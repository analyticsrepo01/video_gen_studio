#!/usr/bin/env python3
"""
Test which models are available with API key vs Service Account
"""

import os
import sys
from google import genai
from google.genai import types

def test_api_key_models():
    """Test what models are available with API key"""
    print("🔑 Testing API Key Models...")

    try:
        client = genai.Client(api_key="AIzaSyBNTqcP3lFVKn_zCEig3EqvQYC38vh-Kpg")
        print("✅ API Key client created successfully")

        # Test basic model
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Hello, test message"
            )
            print("✅ Basic text generation works with API key")
        except Exception as e:
            print(f"❌ Basic model failed: {e}")

        # Test image preview model
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents="Generate a simple image",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )
            print("✅ Image preview model works with API key!")
        except Exception as e:
            print(f"❌ Image preview model failed: {e}")
            if "401" in str(e):
                print("   💡 This confirms: API keys not supported for this model")
            elif "404" in str(e):
                print("   💡 Model not found - might need different name")

    except Exception as e:
        print(f"❌ API Key client creation failed: {e}")

def test_vertex_models():
    """Test what models are available with Vertex AI"""
    print("\n🏢 Testing Vertex AI Models...")

    try:
        # Get project from environment or use default
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0492208227")
        location = "us-central1"

        client = genai.Client(vertexai=True, project=project_id, location=location)
        print("✅ Vertex AI client created successfully")

        # Test image preview model
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents="Generate a simple image",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )
            print("✅ Image preview model works with Vertex AI!")
        except Exception as e:
            print(f"❌ Image preview model failed: {e}")
            if "404" in str(e):
                print("   💡 Model not available in this project/location")
            elif "403" in str(e):
                print("   💡 Permission denied - need model access")

    except Exception as e:
        print(f"❌ Vertex AI client creation failed: {e}")

def test_environment_setup():
    """Test environment setup"""
    print("\n🔧 Testing Environment Setup...")

    # Check environment variables
    api_key = os.environ.get("GEMINI_API_KEY")
    gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")

    print(f"GEMINI_API_KEY: {'Set' if api_key else 'Not set'}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {'Set' if gcp_creds else 'Not set'}")
    print(f"GOOGLE_CLOUD_PROJECT: {gcp_project or 'Not set'}")

    if not api_key and not gcp_creds:
        print("⚠️  No authentication method configured")

    if gcp_creds and os.path.exists(gcp_creds):
        print("✅ Service account file exists")
    elif gcp_creds:
        print("❌ Service account file path set but file doesn't exist")

def main():
    """Run all tests"""
    print("🧪 Model Availability Testing")
    print("="*50)

    test_environment_setup()
    test_api_key_models()
    test_vertex_models()

    print("\n" + "="*50)
    print("📋 Summary:")
    print("1. If API key works: Use Google AI Studio endpoint")
    print("2. If Vertex AI works: Use service account authentication")
    print("3. Check model names might differ between services")
    print("4. Some models may be exclusive to Vertex AI")

if __name__ == "__main__":
    main()