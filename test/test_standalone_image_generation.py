#!/usr/bin/env python3
"""
Test standalone image generation exactly matching your code
"""

import base64
import mimetypes
import os
from google import genai
from google.genai import types

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to: {file_name}")

def test_image_edit():
    """Test your exact pattern with an actual image"""

    client = genai.Client(
        api_key="AIzaSyBNTqcP3lFVKn_zCEig3EqvQYC38vh-Kpg",
    )

    # Find test image
    test_image_path = "output/images/20250919154027_building_21.jpeg"

    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False

    # Read image
    with open(test_image_path, 'rb') as f:
        image_data = f.read()

    # Detect mime type
    mime_type, _ = mimetypes.guess_type(test_image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    model = "gemini-2.5-flash-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                types.Part.from_text(text="Create a vibrant artistic version of this image with enhanced colors"),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    file_index = 0

    print("🎨 Starting image generation...")

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                file_name = f"test_output_{file_index}"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                save_binary_file(f"{file_name}{file_extension}", data_buffer)
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    print(f"Text: {chunk.text}")

        if file_index > 0:
            print(f"✅ Generated {file_index} images successfully!")
            return True
        else:
            print("❌ No images generated")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Change to app directory
    os.chdir("/home/jupyter/GenAI10/veo3/app")
    test_image_edit()