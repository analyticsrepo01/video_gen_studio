#!/usr/bin/env python3
"""
Test script for Style Mixing functionality
"""

import os
import sys
import json
import requests
import time

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_style_mixing_api():
    """Test the style mixing API endpoint"""

    # Configuration
    BASE_URL = "http://localhost:5000"

    print("🧪 Testing Style Mixing API")
    print("=" * 50)

    # Step 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Make sure the app is running on localhost:5000")
            return False
        print("✅ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to run: cd app && python app.py")
        return False

    # Step 2: List available images
    try:
        response = requests.get(f"{BASE_URL}/api/list-images")
        if response.status_code != 200:
            print(f"❌ Failed to list images: {response.status_code}")
            return False

        images_data = response.json()
        images = images_data.get('images', [])
        print(f"✅ Found {len(images)} images")

        if len(images) < 2:
            print("❌ Need at least 2 images for style mixing test")
            print("💡 Upload some images first using the web interface")
            return False

        # Show available images
        for i, img in enumerate(images[:5]):
            print(f"   {i+1}. {img['name']} ({img['size']} bytes)")

    except Exception as e:
        print(f"❌ Error listing images: {e}")
        return False

    # Step 3: Test style mixing API call
    try:
        # Use first 2 images for testing
        test_images = [img['path'] for img in images[:2]]

        test_payload = {
            "images": test_images,
            "prompt": "Combine the color palette from the first image with the composition style from the second image",
            "mode": "analyze"
        }

        print(f"\n🔄 Testing style mixing with images:")
        for i, img_path in enumerate(test_images):
            print(f"   Image {i+1}: {os.path.basename(img_path)}")

        print(f"📝 Prompt: {test_payload['prompt']}")
        print(f"🎛️  Mode: {test_payload['mode']}")

        # Make the API call
        print("\n⏳ Making API call...")
        start_time = time.time()

        response = requests.post(
            f"{BASE_URL}/api/mix-image-styles",
            json=test_payload,
            timeout=60  # 60 second timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  API call took {duration:.2f} seconds")

        if response.status_code != 200:
            print(f"❌ API call failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Raw response: {response.text}")
            return False

        # Parse response
        result = response.json()

        if result.get('success'):
            print("✅ Style mixing API call successful!")
            print(f"🎨 Mode: {result.get('mixing_mode')}")
            print(f"📸 Images processed: {result.get('image_count')}")

            # Show analysis if available
            analysis = result.get('analysis', {})
            if isinstance(analysis, dict) and 'individual_styles' in analysis:
                print("\n📊 Analysis Results:")
                individual_styles = analysis.get('individual_styles', [])
                for style in individual_styles[:2]:  # Show first 2
                    print(f"   Image {style.get('image_index', '?')}: {style.get('artistic_style', 'N/A')}")

                recommendations = analysis.get('recommendations', {})
                if recommendations.get('suggested_prompt'):
                    print(f"\n💡 Suggested prompt: {recommendations['suggested_prompt']}")

            elif isinstance(analysis, dict) and 'raw_response' in analysis:
                print(f"\n📄 Raw response preview: {analysis['raw_response'][:200]}...")
            else:
                print(f"\n📄 Analysis type: {type(analysis)}")

            return True
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Style mixing failed: {error_msg}")
            return False

    except requests.exceptions.Timeout:
        print("❌ API call timed out (60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error during style mixing test: {e}")
        return False

def test_path_resolution():
    """Test that the path resolution logic works correctly"""
    print("\n🔍 Testing Path Resolution Logic")
    print("=" * 50)

    # We'll test the logic by making API calls with different path formats
    BASE_URL = "http://localhost:5000"

    try:
        # Get available images
        response = requests.get(f"{BASE_URL}/api/list-images")
        images = response.json().get('images', [])

        if len(images) < 1:
            print("❌ No images available for path testing")
            return False

        # Test with the first image in different path formats
        original_path = images[0]['path']
        image_name = images[0]['name']

        # Different path formats to test
        path_formats = [
            original_path,  # Original format
            f"output/images/{image_name}",  # Output-prefixed format
            f"images/{image_name}",  # Just images folder
            image_name,  # Just filename
        ]

        print(f"🧪 Testing path resolution with image: {image_name}")

        for i, test_path in enumerate(path_formats):
            print(f"\n🔄 Test {i+1}: Path format '{test_path}'")

            test_payload = {
                "images": [test_path],
                "prompt": "Analyze this image style",
                "mode": "analyze"
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/api/mix-image-styles",
                    json=test_payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"   ✅ Path format works!")
                    else:
                        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                else:
                    error = response.json().get('error', 'Unknown error')
                    print(f"   ❌ Failed: {error}")

            except Exception as e:
                print(f"   ❌ Exception: {e}")

        return True

    except Exception as e:
        print(f"❌ Path resolution test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Style Mixing Test Suite")
    print("=" * 60)

    print("\n🔧 Prerequisites:")
    print("1. App should be running: cd app && python app.py")
    print("2. At least 2 images should be uploaded")
    print("3. GEMINI_API_KEY should be set in .env")
    print("\n" + "=" * 60)

    # Run tests
    tests = [
        ("Style Mixing API", test_style_mixing_api),
        ("Path Resolution", test_path_resolution),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if success:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! Style mixing is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)