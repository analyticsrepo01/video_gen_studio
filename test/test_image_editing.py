#!/usr/bin/env python3
"""
Test script for image editing functionality
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_image_editing_api():
    """Test the image editing API endpoint"""

    # Test configuration
    BASE_URL = "http://localhost:5000"
    TEST_IMAGE_PATH = "output/images"  # Relative to app directory

    print("🧪 Testing Image Editing API...")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print("✅ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not running: {e}")
        return False

    # Check if there are any images to test with
    app_dir = os.path.join(os.path.dirname(__file__), '..', 'app')
    images_dir = os.path.join(app_dir, TEST_IMAGE_PATH)

    if not os.path.exists(images_dir):
        print(f"❌ Images directory not found: {images_dir}")
        return False

    # Find a test image
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        print(f"❌ No images found in {images_dir}")
        print("💡 Generate an image first using the Image Generation tab")
        return False

    test_image = image_files[0]
    test_image_path = f"output/images/{test_image}"

    print(f"📷 Using test image: {test_image}")

    # Test 1: Basic image editing
    print("\n🔄 Test 1: Basic image editing...")

    edit_data = {
        "image_path": test_image_path,
        "edit_prompt": "Add a red border around the image"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/edit-image", json=edit_data, timeout=30)
        result = response.json()

        if response.status_code == 200 and not result.get('error'):
            print("✅ Basic image editing request successful")
            print(f"   Response: {result.get('description', 'No description')[:100]}...")
        else:
            print(f"❌ Basic image editing failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Basic image editing error: {e}")
        return False

    # Test 2: Image editing with validation
    print("\n🔄 Test 2: Image editing with validation...")

    validation_data = {
        "image_path": test_image_path,
        "edit_prompt": "Make the image brighter and more colorful",
        "enable_validation": True,
        "max_retries": 2
    }

    try:
        response = requests.post(f"{BASE_URL}/api/edit-image-with-validation", json=validation_data, timeout=60)
        result = response.json()

        if response.status_code == 200 and result.get('success'):
            print("✅ Image editing with validation successful")
            print(f"   Attempts: {len(result.get('attempts', []))}")
            print(f"   Final result: {result.get('final_result', {}).get('description', 'No description')[:100]}...")
        else:
            print(f"❌ Image editing with validation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Image editing with validation error: {e}")

    return True

def test_style_mixing_api():
    """Test the style mixing API endpoint"""

    BASE_URL = "http://localhost:5000"
    TEST_IMAGE_PATH = "output/images"

    print("\n🎨 Testing Style Mixing API...")

    # Find test images
    app_dir = os.path.join(os.path.dirname(__file__), '..', 'app')
    images_dir = os.path.join(app_dir, TEST_IMAGE_PATH)

    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(image_files) < 2:
        print(f"❌ Need at least 2 images for style mixing, found {len(image_files)}")
        print("💡 Generate more images first using the Image Generation tab")
        return False

    # Use first 2-3 images for testing
    test_images = [f"images/{img}" for img in image_files[:min(3, len(image_files))]]

    print(f"🖼️  Using {len(test_images)} test images: {[img.split('/')[-1] for img in test_images]}")

    # Test 1: Analyze mode
    print("\n🔄 Test 1: Style mixing - Analyze mode...")

    analyze_data = {
        "image_paths": test_images,
        "style_prompt": "Analyze and compare the artistic styles of these images",
        "mixing_mode": "analyze"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/mix-image-styles", json=analyze_data, timeout=60)
        result = response.json()

        if response.status_code == 200 and result.get('success'):
            print("✅ Style mixing (analyze) successful")
            print(f"   Analyzed {result.get('image_count')} images")
            analysis = result.get('analysis', {})
            if isinstance(analysis, dict) and 'individual_styles' in analysis:
                print(f"   Found {len(analysis.get('individual_styles', []))} individual style analyses")
            else:
                print(f"   Raw analysis provided")
        else:
            print(f"❌ Style mixing (analyze) failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Style mixing (analyze) error: {e}")

    # Test 2: Generate mode
    print("\n🔄 Test 2: Style mixing - Generate mode...")

    generate_data = {
        "image_paths": test_images[:2],  # Use only 2 images for generate mode
        "style_prompt": "Create a new image that combines the best elements of these two styles",
        "mixing_mode": "generate"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/mix-image-styles", json=generate_data, timeout=60)
        result = response.json()

        if response.status_code == 200 and result.get('success'):
            print("✅ Style mixing (generate) successful")
            print(f"   Generated guidance for {result.get('image_count')} images")
        else:
            print(f"❌ Style mixing (generate) failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Style mixing (generate) error: {e}")

    return True

def main():
    """Run all tests"""
    print("🚀 Starting API Tests for Video Generation Studio")
    print("="*60)

    # Test image editing
    image_editing_success = test_image_editing_api()

    time.sleep(2)  # Brief pause between test suites

    # Test style mixing
    style_mixing_success = test_style_mixing_api()

    print("\n" + "="*60)
    print("📊 Test Summary:")
    print(f"   Image Editing: {'✅ PASS' if image_editing_success else '❌ FAIL'}")
    print(f"   Style Mixing: {'✅ PASS' if style_mixing_success else '❌ FAIL'}")

    if image_editing_success and style_mixing_success:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)