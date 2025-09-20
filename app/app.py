from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import asyncio
import os
import time
import datetime
import random
import subprocess
import json
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.cloud import storage
from google import genai
from google.genai import types
import mimetypes
import vertexai
from config_manager import config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration - Auto-detect from gcloud config
def get_project_id():
    """Get project ID from gcloud config or environment variable"""
    try:
        # Try to get from gcloud config first
        result = subprocess.run(['gcloud', 'config', 'get-value', 'core/project'],
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback to environment variable
    return os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')

GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'video-generation-bucket-unique-name')
GCS_FOLDER = "generated-content"
PROJECT_ID = get_project_id()
LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')

# Initialize services
vertexai.init(project=PROJECT_ID, location=LOCATION)
# Initialize both clients
# API Key client for gemini-2.5-flash-image-preview
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

api_client = genai.Client(api_key=api_key)
print("✅ API Key client ready for image preview model")

# Vertex AI client for other models
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
print("✅ Vertex AI client ready for other models")
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# Upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure directories exist
os.makedirs("output/videos", exist_ok=True)
os.makedirs("output/images", exist_ok=True)
os.makedirs("temp", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, file_type):
    if file_type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    data = request.json
    prompt = data.get('prompt')
    aspect_ratio = data.get('aspect_ratio', '9:16')
    negative_prompt = data.get('negative_prompt', '')
    resolution = data.get('resolution', '1080p')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        # Run async function
        result = asyncio.run(generate_video_async(prompt, aspect_ratio, negative_prompt, resolution))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        result = asyncio.run(generate_image_async(prompt))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edit-image', methods=['POST'])
def edit_image():
    data = request.json
    image_path = data.get('image_path')
    edit_prompt = data.get('edit_prompt')
    enable_validation = data.get('enable_validation', False)
    max_retries = data.get('max_retries', 5)

    if not image_path or not edit_prompt:
        return jsonify({'error': 'Image path and edit prompt are required'}), 400

    try:
        if enable_validation:
            result = asyncio.run(edit_image_with_validation_async(image_path, edit_prompt, max_retries))
        else:
            result = asyncio.run(edit_image_async(image_path, edit_prompt))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-video-from-image', methods=['POST'])
def generate_video_from_image():
    data = request.json
    prompt = data.get('prompt')
    image_path = data.get('image_path')
    aspect_ratio = data.get('aspect_ratio', '9:16')
    negative_prompt = data.get('negative_prompt', '')
    resolution = data.get('resolution', '1080p')

    if not prompt or not image_path:
        return jsonify({'error': 'Prompt and image path are required'}), 400

    try:
        result = asyncio.run(generate_video_from_image_async(prompt, image_path, aspect_ratio, negative_prompt, resolution))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refine-prompt', methods=['POST'])
def refine_prompt():
    data = request.json
    original_prompt = data.get('original_prompt')
    focus = data.get('focus', 'general')

    if not original_prompt:
        return jsonify({'error': 'Original prompt is required'}), 400

    try:
        result = asyncio.run(refine_prompt_with_gemini(original_prompt, focus))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        # Return safe configuration data (no secrets)
        safe_config = {
            'app_info': config.get('app_info'),
            'models': config.get('models'),
            'generation_settings': config.get('generation_settings'),
            'ui_settings': config.get('ui_settings'),
            'features': config.get('features'),
            'file_handling': {
                'upload': config.get('file_handling.upload'),
                'storage': {
                    'local_output_dir': config.get('file_handling.storage.local_output_dir'),
                    'temp_dir': config.get('file_handling.storage.temp_dir'),
                    'auto_cleanup_temp': config.get('file_handling.storage.auto_cleanup_temp')
                }
            }
        }
        return jsonify(safe_config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration settings"""
    try:
        data = request.json

        # Only allow updates to safe configuration sections
        allowed_sections = [
            'generation_settings',
            'ui_settings',
            'features.ai_features',
            'features.video_tools'
        ]

        for key, value in data.items():
            if any(key.startswith(section) for section in allowed_sections):
                config.set(key, value)

        # Save the updated configuration
        config.save_config()

        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-text-overlay', methods=['POST'])
def add_text_overlay():
    """Add text overlay to an existing image"""
    try:
        data = request.json

        # Extract parameters
        image_path = data.get('image_path')
        text = data.get('text')
        position = data.get('position', {'x': 50, 'y': 50})
        font_family = data.get('font_family', 'Arial')
        font_size = data.get('font_size', 24)
        font_color = data.get('font_color', '#ffffff')
        font_weight = data.get('font_weight', 'normal')
        background = data.get('background', {'enabled': False})
        shadow = data.get('shadow', {'enabled': False})
        image_dimensions = data.get('image_dimensions', {})

        if not image_path or not text:
            return jsonify({'error': 'Image path and text are required'}), 400

        # Open the original image
        image = Image.open(image_path)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Create a transparent overlay for text
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load a system font
        try:
            # Map font families to system fonts
            font_map = {
                'Arial, sans-serif': ['arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf'],
                'Georgia, serif': ['georgia.ttf', 'Georgia.ttf', 'DejaVuSerif.ttf'],
                "'Times New Roman', serif": ['times.ttf', 'Times.ttf', 'DejaVuSerif.ttf'],
                "'Courier New', monospace": ['cour.ttf', 'Courier.ttf', 'DejaVuSansMono.ttf'],
                'Helvetica, sans-serif': ['helvetica.ttf', 'Helvetica.ttf', 'DejaVuSans.ttf'],
                'Impact, sans-serif': ['impact.ttf', 'Impact.ttf', 'DejaVuSans-Bold.ttf'],
                "'Comic Sans MS', cursive": ['comic.ttf', 'ComicSans.ttf', 'DejaVuSans.ttf']
            }

            font = None
            font_files = font_map.get(font_family, ['DejaVuSans.ttf'])

            # Try to find and load the font
            for font_file in font_files:
                try:
                    # Try different common font paths
                    font_paths = [
                        f'/usr/share/fonts/truetype/dejavu/{font_file}',
                        f'/usr/share/fonts/truetype/liberation/{font_file}',
                        f'/System/Library/Fonts/{font_file}',
                        f'/Windows/Fonts/{font_file}',
                        font_file
                    ]

                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            break

                    if font:
                        break
                except:
                    continue

            # Fallback to default font if no TrueType font found
            if not font:
                font = ImageFont.load_default()

        except Exception as e:
            font = ImageFont.load_default()

        # Calculate text position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Convert percentage positions to pixel coordinates
        x = int((position['x'] / 100.0) * image.width)
        y = int((position['y'] / 100.0) * image.height)

        # Adjust position based on text size (center the text on the position)
        x = max(0, min(image.width - text_width, x - text_width // 2))
        y = max(0, min(image.height - text_height, y - text_height // 2))

        # Add background box if enabled
        if background.get('enabled', False):
            # Parse background color
            bg_color = background.get('color', '#000000')
            bg_opacity = background.get('opacity', 70)

            # Convert hex to RGB
            bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
            bg_rgba = bg_rgb + (int(255 * bg_opacity / 100),)

            # Add padding around text
            padding = 10
            bg_bbox = (
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            )

            draw.rectangle(bg_bbox, fill=bg_rgba)

        # Parse text color
        text_rgb = tuple(int(font_color[i:i+2], 16) for i in (1, 3, 5))
        text_rgba = text_rgb + (255,)

        # Add text shadow if enabled
        if shadow.get('enabled', False):
            shadow_color = shadow.get('color', '#000000')
            shadow_blur = shadow.get('blur', 2)

            # Parse shadow color
            shadow_rgb = tuple(int(shadow_color[i:i+2], 16) for i in (1, 3, 5))
            shadow_rgba = shadow_rgb + (128,)  # Semi-transparent shadow

            # Draw shadow (offset by shadow_blur pixels)
            for offset_x in range(-shadow_blur, shadow_blur + 1):
                for offset_y in range(-shadow_blur, shadow_blur + 1):
                    if offset_x != 0 or offset_y != 0:
                        draw.text((x + offset_x, y + offset_y), text, font=font, fill=shadow_rgba)

        # Draw the main text
        draw.text((x, y), text, font=font, fill=text_rgba)

        # Composite the overlay onto the original image
        final_image = Image.alpha_composite(image, overlay)

        # Convert back to RGB for saving as JPEG (if needed)
        if final_image.mode == 'RGBA':
            # Create white background for RGBA images
            rgb_image = Image.new('RGB', final_image.size, (255, 255, 255))
            rgb_image.paste(final_image, mask=final_image.split()[-1])  # Use alpha channel as mask
            final_image = rgb_image

        # Save the result
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"{config.local_output_dir}/images/text_overlay_{timestamp}.png"
        final_image.save(output_filename, 'PNG', quality=95)

        # Optional: Upload to GCS if file is large enough
        gcs_url = None
        file_size_mb = os.path.getsize(output_filename) / (1024 * 1024)
        if file_size_mb >= config.gcs_upload_threshold_mb:
            try:
                gcs_path = f"text_overlays/overlay_{timestamp}.png"
                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(output_filename)
                gcs_url = f"gs://{config.gcs_bucket_name}/{gcs_path}"
            except Exception as e:
                print(f"GCS upload failed: {e}")

        return jsonify({
            'success': True,
            'message': 'Text overlay applied successfully',
            'output_path': output_filename,
            'original_path': image_path,
            'text_applied': text,
            'position': position,
            'gcs_url': gcs_url,
            'file_size': os.path.getsize(output_filename)
        })

    except FileNotFoundError:
        return jsonify({'error': 'Image file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to add text overlay: {str(e)}'}), 500

@app.route('/api/join-videos', methods=['POST'])
def join_videos():
    data = request.json
    video_paths = data.get('video_paths', [])

    if len(video_paths) < 2:
        return jsonify({'error': 'At least 2 videos are required'}), 400

    try:
        result = join_videos_ffmpeg(video_paths)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-frames', methods=['POST'])
def extract_frames():
    data = request.json
    video_path = data.get('video_path')

    if not video_path:
        return jsonify({'error': 'Video path is required'}), 400

    try:
        result = extract_frames_ffmpeg(video_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-first-frame', methods=['POST'])
def extract_first_frame():
    data = request.json
    video_path = data.get('video_path')

    if not video_path:
        return jsonify({'error': 'Video path is required'}), 400

    try:
        result = extract_first_frame_ffmpeg(video_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-last-frame', methods=['POST'])
def extract_last_frame():
    data = request.json
    video_path = data.get('video_path')

    if not video_path:
        return jsonify({'error': 'Video path is required'}), 400

    try:
        result = extract_last_frame_ffmpeg(video_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-videos')
def list_videos():
    try:
        videos = []
        for file in os.listdir("output/videos"):
            if file.endswith('.mp4'):
                file_path = os.path.join("output/videos", file)
                file_size = os.path.getsize(file_path)
                videos.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'created': os.path.getctime(file_path)
                })
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename, 'image'):
            # Secure the filename
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{filename}"

            # Save to output/images directory
            file_path = os.path.join("output/images", filename)
            file.save(file_path)

            # Optional: Upload to GCS
            gcs_url = None
            try:
                gcs_path = f"{GCS_FOLDER}/uploaded_{filename}"
                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(file_path)
                gcs_url = f"gs://{config.gcs_bucket_name}/{gcs_path}"
            except Exception as e:
                print(f"GCS upload failed: {e}")

            return jsonify({
                'success': True,
                'filename': filename,
                'local_path': file_path,
                'gcs_url': gcs_url,
                'size': os.path.getsize(file_path)
            })
        else:
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, webp'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename, 'video'):
            # Secure the filename
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{filename}"

            # Save to output/videos directory
            file_path = os.path.join("output/videos", filename)
            file.save(file_path)

            # Optional: Upload to GCS
            gcs_url = None
            try:
                gcs_path = f"{GCS_FOLDER}/uploaded_{filename}"
                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(file_path)
                gcs_url = f"gs://{config.gcs_bucket_name}/{gcs_path}"
            except Exception as e:
                print(f"GCS upload failed: {e}")

            return jsonify({
                'success': True,
                'filename': filename,
                'local_path': file_path,
                'gcs_url': gcs_url,
                'size': os.path.getsize(file_path)
            })
        else:
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv, wmv, flv, webm'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-images')
def list_images():
    try:
        images = []
        for file in os.listdir("output/images"):
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                file_path = os.path.join("output/images", file)
                file_size = os.path.getsize(file_path)
                images.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'created': os.path.getctime(file_path)
                })
        return jsonify({'images': images})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview/image/<path:filename>')
def preview_image(filename):
    try:
        return send_file(os.path.join("output/images", filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/preview/video/<path:filename>')
def preview_video(filename):
    try:
        return send_file(os.path.join("output/videos", filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/delete-file', methods=['DELETE'])
def delete_file():
    try:
        data = request.json
        file_path = data.get('file_path')
        file_type = data.get('file_type')  # 'image' or 'video'

        if not file_path or not file_type:
            return jsonify({'error': 'File path and file type are required'}), 400

        # Security check - ensure the file is in the correct directory
        if file_type == 'image':
            allowed_dir = os.path.abspath("output/images")
            full_path = os.path.abspath(file_path)
        elif file_type == 'video':
            allowed_dir = os.path.abspath("output/videos")
            full_path = os.path.abspath(file_path)
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        # Check if file is in allowed directory
        if not full_path.startswith(allowed_dir):
            return jsonify({'error': 'Invalid file path'}), 400

        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404

        # Delete the file
        os.remove(full_path)

        # Try to delete from GCS if it exists there
        try:
            filename = os.path.basename(full_path)
            # Check common GCS paths where the file might be
            possible_gcs_paths = [
                f"{GCS_FOLDER}/{filename}",
                f"{GCS_FOLDER}/uploaded_{filename}",
            ]

            for gcs_path in possible_gcs_paths:
                blob = bucket.blob(gcs_path)
                if blob.exists():
                    blob.delete()
                    break
        except Exception as e:
            print(f"GCS deletion failed (non-critical): {e}")

        return jsonify({
            'success': True,
            'message': f'File {os.path.basename(full_path)} deleted successfully',
            'deleted_path': file_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def generate_video_async(prompt, aspect_ratio, negative_prompt='', resolution='1080p'):
    max_retries = 5
    base_wait_time = 60

    for attempt in range(max_retries):
        try:
            # Build video generation config
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                number_of_videos=1,
                duration_seconds=8,
                person_generation="allow_all",
            )

            # Add negative prompt if provided
            if negative_prompt.strip():
                video_config.negative_prompt = negative_prompt.strip()

            operation = client.models.generate_videos(
                model=config.video_model_id,
                prompt=prompt,
                config=video_config,
            )
            break

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    wait_time = base_wait_time * (2 ** attempt) + random.uniform(0, 30)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {'error': f'Max retries reached for prompt: {prompt}'}
            else:
                raise e

    # Wait for completion
    while not operation.done:
        await asyncio.sleep(10)
        try:
            operation = client.operations.get(operation)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                await asyncio.sleep(60)
                continue
            else:
                raise e

    if not operation.response or not operation.response.generated_videos:
        return {'error': 'No videos were generated'}

    generated_video = operation.response.generated_videos[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Save locally
    video_filename = f"{config.local_output_dir}/videos/{prompt[:10]}_{timestamp}.mp4"
    with open(video_filename, 'wb') as f:
        f.write(generated_video.video.video_bytes)

    # Upload to GCS
    gcs_path = f"{GCS_FOLDER}/{prompt[:10]}_{timestamp}.mp4"
    blob = bucket.blob(gcs_path)

    try:
        blob.upload_from_filename(video_filename)
        gcs_url = f"gs://{config.gcs_bucket_name}/{gcs_path}"
    except Exception as e:
        gcs_url = None

    return {
        'success': True,
        'local_path': video_filename,
        'gcs_url': gcs_url,
        'prompt': prompt
    }

async def generate_image_async(prompt):
    try:
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
        )

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f"{config.local_output_dir}/images/{prompt[:10]}_{timestamp}.png"

        # Save the image
        result.generated_images[0].image.save(image_filename)

        return {
            'success': True,
            'local_path': image_filename,
            'prompt': prompt
        }
    except Exception as e:
        return {'error': str(e)}

async def edit_image_async(image_path, edit_prompt):
    try:
        # Read the image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        # Detect mime type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = "image/png"

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Create content following your exact pattern
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text=edit_prompt),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        # Use streaming following your exact pattern
        edited_images = []
        description = ""
        file_index = 0

        # Use API client for gemini-2.5-flash-image-preview
        active_client = api_client if config.image_edit_model_id == "gemini-2.5-flash-image-preview" else client

        for chunk in active_client.models.generate_content_stream(
            model=config.image_edit_model_id,
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
                file_name = f"edited_{timestamp}_{file_index}"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)

                # Save to output directory
                edited_image_filename = f"{config.local_output_dir}/images/{file_name}{file_extension}"

                with open(edited_image_filename, 'wb') as f:
                    f.write(data_buffer)

                edited_images.append(edited_image_filename)
                print(f"Image saved to: {edited_image_filename}")
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    description += chunk.text
                    print(chunk.text)

        return {
            'success': True,
            'description': description or "Image editing completed",
            'edited_images': edited_images,
            'image_count': len(edited_images),
            'original_path': image_path
        }

    except Exception as e:
        return {'error': str(e)}

async def validate_image_edit_async(original_image_path, edited_description, edit_prompt):
    """
    Validate if the image edit matches the requested prompt using Gemini
    """
    try:
        # Read the original image
        with open(original_image_path, 'rb') as f:
            image_bytes = f.read()

        validation_prompt = f"""
You are an expert at analyzing image editing results. Please analyze the following:

ORIGINAL EDIT REQUEST: "{edit_prompt}"
EDIT RESULT DESCRIPTION: "{edited_description}"

Please provide a JSON response with the following format:
{{
    "validation_passed": true/false,
    "confidence_score": 0.0-1.0,
    "analysis": "Brief explanation of whether the edit matches the request",
    "suggested_improvements": "If validation failed, suggest specific improvements to the prompt",
    "enhanced_prompt": "If validation failed, provide an improved version of the original prompt"
}}

Focus on whether the described changes actually address what was requested in the original edit prompt.
"""

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=validation_prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ]
            )
        ]

        response = client.models.generate_content(
            model=config.image_edit_model_id,
            contents=contents
        )

        # Try to parse JSON response
        try:
            import json
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured response
            return {
                'validation_passed': False,
                'confidence_score': 0.5,
                'analysis': 'Could not parse validation response',
                'suggested_improvements': 'Try being more specific in your edit request',
                'enhanced_prompt': edit_prompt,
                'raw_response': response.text
            }

    except Exception as e:
        return {
            'validation_passed': False,
            'confidence_score': 0.0,
            'analysis': f'Validation failed: {str(e)}',
            'suggested_improvements': 'Try a different approach',
            'enhanced_prompt': edit_prompt
        }

async def enhance_edit_prompt_async(original_prompt, failure_reason=""):
    """
    Enhance an image edit prompt using Gemini to make it more effective
    """
    try:
        enhancement_prompt = f"""
You are an expert at writing effective image editing prompts. Please improve the following prompt to make it more specific, clear, and actionable for AI image editing.

ORIGINAL PROMPT: "{original_prompt}"
{f"PREVIOUS FAILURE REASON: {failure_reason}" if failure_reason else ""}

Guidelines for improvement:
1. Be specific about what changes to make
2. Describe the desired visual outcome clearly
3. Include details about style, colors, objects to add/remove
4. Avoid ambiguous language
5. Make the request technically feasible

Please provide a JSON response with:
{{
    "enhanced_prompt": "improved version of the prompt",
    "explanation": "brief explanation of what was improved",
    "key_changes": ["list", "of", "main", "improvements"]
}}
"""

        response = client.models.generate_content(
            model=config.prompt_refine_model_id,
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=enhancement_prompt)]
            )]
        )

        try:
            import json
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            return {
                'enhanced_prompt': original_prompt + " (please be more specific)",
                'explanation': 'Could not parse enhancement response',
                'key_changes': ['Made prompt more specific']
            }

    except Exception as e:
        return {
            'enhanced_prompt': original_prompt,
            'explanation': f'Enhancement failed: {str(e)}',
            'key_changes': []
        }

async def edit_image_with_validation_async(image_path, edit_prompt, max_retries=5):
    """
    Edit image with AI validation and automatic retry with enhanced prompts
    """
    attempts = []
    current_prompt = edit_prompt

    for attempt in range(max_retries):
        try:
            print(f"🔄 Image edit attempt {attempt + 1}/{max_retries}")
            print(f"📝 Using prompt: {current_prompt}")

            # Try to edit the image
            edit_result = await edit_image_async(image_path, current_prompt)

            if edit_result.get('error'):
                # If edit failed, enhance the prompt and try again
                failure_reason = edit_result['error']
                print(f"❌ Edit failed: {failure_reason}")

                enhancement_result = await enhance_edit_prompt_async(current_prompt, failure_reason)
                current_prompt = enhancement_result.get('enhanced_prompt', current_prompt)

                attempts.append({
                    'attempt': attempt + 1,
                    'prompt': current_prompt,
                    'result': 'failed',
                    'error': failure_reason,
                    'enhancement': enhancement_result
                })

                continue

            # If edit succeeded, validate the result
            print("✅ Edit succeeded, validating result...")
            validation_result = await validate_image_edit_async(
                image_path,
                edit_result.get('description', ''),
                edit_prompt
            )

            # Store attempt information
            attempts.append({
                'attempt': attempt + 1,
                'prompt': current_prompt,
                'result': 'success',
                'edit_result': edit_result,
                'validation': validation_result
            })

            # Check if validation passed
            if validation_result.get('validation_passed', False) and validation_result.get('confidence_score', 0) > 0.7:
                print("🎉 Validation passed!")
                return {
                    'success': True,
                    'final_result': edit_result,
                    'validation': validation_result,
                    'attempts': attempts,
                    'total_attempts': attempt + 1,
                    'final_prompt': current_prompt
                }

            # If validation failed but we have retries left, enhance prompt
            if attempt < max_retries - 1:
                print("⚠️ Validation failed, enhancing prompt...")
                enhancement_result = await enhance_edit_prompt_async(
                    current_prompt,
                    validation_result.get('analysis', 'Validation failed')
                )
                current_prompt = enhancement_result.get('enhanced_prompt', current_prompt)
                attempts[-1]['enhancement'] = enhancement_result

        except Exception as e:
            attempts.append({
                'attempt': attempt + 1,
                'prompt': current_prompt,
                'result': 'error',
                'error': str(e)
            })

    # If we've exhausted all retries
    return {
        'success': False,
        'error': 'Failed to achieve satisfactory edit result after maximum retries',
        'attempts': attempts,
        'total_attempts': max_retries,
        'final_prompt': current_prompt,
        'suggestion': 'Try a different editing approach or more specific prompt'
    }

async def generate_video_from_image_async(prompt, image_path, aspect_ratio, negative_prompt='', resolution='1080p'):
    try:
        # Read the image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        image_data = types.Image(
            image_bytes=image_bytes,
            mime_type="image/png"
        )

        # Build video generation config
        video_config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            number_of_videos=1,
            duration_seconds=8,
            person_generation="allow_adult",
        )

        # Add negative prompt if provided
        if negative_prompt.strip():
            video_config.negative_prompt = negative_prompt.strip()

        operation = client.models.generate_videos(
            model=config.video_model_id,
            prompt=prompt,
            image=image_data,
            config=video_config,
        )

        # Wait for completion
        while not operation.done:
            await asyncio.sleep(10)
            operation = client.operations.get(operation)

        if not operation.response or not operation.response.generated_videos:
            return {'error': 'No videos were generated'}

        generated_video = operation.response.generated_videos[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        video_filename = f"{config.local_output_dir}/videos/from_image_{timestamp}.mp4"
        with open(video_filename, 'wb') as f:
            f.write(generated_video.video.video_bytes)

        # Upload to GCS
        gcs_path = f"{GCS_FOLDER}/from_image_{timestamp}.mp4"
        blob = bucket.blob(gcs_path)

        try:
            blob.upload_from_filename(video_filename)
            gcs_url = f"gs://{config.gcs_bucket_name}/{gcs_path}"
        except:
            gcs_url = None

        return {
            'success': True,
            'local_path': video_filename,
            'gcs_url': gcs_url,
            'prompt': prompt,
            'source_image': image_path
        }

    except Exception as e:
        return {'error': str(e)}

async def refine_prompt_with_gemini(original_prompt, focus='general'):
    try:
        # Create focus-specific instructions
        focus_instructions = {
            'general': 'Improve overall clarity, detail, and structure.',
            'cinematic': 'Focus on camera movements, lighting, and cinematic techniques.',
            'detailed': 'Add more specific visual details, textures, and descriptive elements.',
            'technical': 'Emphasize technical camera work, film techniques, and production quality.',
            'creative': 'Enhance artistic elements, unique perspectives, and creative styles.'
        }

        focus_instruction = focus_instructions.get(focus, focus_instructions['general'])

        # Create the refinement prompt for Gemini
        refinement_prompt = f"""
You are an expert in writing high-quality prompts for Veo video generation. Your task is to refine and improve the given prompt based on best practices.

REFINEMENT FOCUS: {focus_instruction}

Best Practices for Veo Video Generation Prompts:

Key Elements to Include:
1. Subject: The main object, person, or scene
2. Context: Background or setting
3. Action: What the subject is doing
4. Style: Specific aesthetic or film style
5. Camera Motion: Optional camera perspective
6. Composition: How the shot is framed
7. Ambiance: Color tones and lighting

Guidelines:
- Use descriptive, clear language
- Include specific details
- Reference specific artistic styles
- Provide context for the model
- Use adjectives and adverbs to paint a clear picture
- Specify camera movements if desired
- Include color palette descriptions
- Be explicit about desired details

Structure: "[Camera motion] shot of a [subject] [doing action] in [context], with [style] and [ambiance]."

Original Prompt: "{original_prompt}"

Please refine this prompt to make it more effective for video generation. Provide:
1. The refined prompt
2. A brief explanation of what you improved
3. Alternative variations (2-3 options)

Format your response as JSON:
{{
    "refined_prompt": "improved prompt here",
    "explanation": "explanation of improvements",
    "alternatives": [
        "alternative 1",
        "alternative 2",
        "alternative 3"
    ]
}}
"""

        # Use Gemini to refine the prompt
        response = client.models.generate_content(
            model=config.prompt_refine_model_id,
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=refinement_prompt)]
            )]
        )

        # Try to parse JSON response
        import json
        try:
            result = json.loads(response.text)
            return {
                'success': True,
                'original_prompt': original_prompt,
                'refined_prompt': result.get('refined_prompt', ''),
                'explanation': result.get('explanation', ''),
                'alternatives': result.get('alternatives', [])
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw response
            return {
                'success': True,
                'original_prompt': original_prompt,
                'refined_prompt': response.text,
                'explanation': 'Raw response from Gemini (JSON parsing failed)',
                'alternatives': []
            }

    except Exception as e:
        return {'error': str(e)}

def join_videos_ffmpeg(video_paths):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = f"output/videos/joined_{timestamp}.mp4"

        # Create file list for ffmpeg
        list_file = f"temp/video_list_{timestamp}.txt"
        with open(list_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{os.path.abspath(video_path)}'\n")

        # Run ffmpeg command
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file, '-c', 'copy', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temp file
        os.remove(list_file)

        if result.returncode == 0:
            return {
                'success': True,
                'output_path': output_path,
                'input_videos': video_paths
            }
        else:
            return {'error': f'FFmpeg error: {result.stderr}'}

    except Exception as e:
        return {'error': str(e)}

def extract_frames_ffmpeg(video_path):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        frames_dir = f"output/frames_{timestamp}"
        os.makedirs(frames_dir, exist_ok=True)

        # Extract frames (1 per second)
        cmd = [
            'ffmpeg', '-i', video_path, '-vf', 'fps=1',
            f'{frames_dir}/frame_%03d.png'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.png')]
            return {
                'success': True,
                'frames_dir': frames_dir,
                'frame_count': len(frame_files),
                'frames': [os.path.join(frames_dir, f) for f in frame_files]
            }
        else:
            return {'error': f'FFmpeg error: {result.stderr}'}

    except Exception as e:
        return {'error': str(e)}

def extract_first_frame_ffmpeg(video_path):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        frame_filename = f"{config.local_output_dir}/images/first_frame_{timestamp}.png"

        # Extract first frame
        cmd = [
            'ffmpeg', '-i', video_path, '-vframes', '1', '-q:v', '2',
            frame_filename
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {
                'success': True,
                'frame_path': frame_filename,
                'frame_type': 'first'
            }
        else:
            return {'error': f'FFmpeg error: {result.stderr}'}

    except Exception as e:
        return {'error': str(e)}

def extract_last_frame_ffmpeg(video_path):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        frame_filename = f"{config.local_output_dir}/images/last_frame_{timestamp}.png"

        # Get video duration first
        duration_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]

        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)

        if duration_result.returncode != 0:
            return {'error': 'Could not get video duration'}

        try:
            duration = float(duration_result.stdout.strip())
            # Extract frame from 1 second before the end
            seek_time = max(0, duration - 1)
        except ValueError:
            return {'error': 'Invalid video duration'}

        # Extract last frame
        cmd = [
            'ffmpeg', '-ss', str(seek_time), '-i', video_path,
            '-vframes', '1', '-q:v', '2', frame_filename
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {
                'success': True,
                'frame_path': frame_filename,
                'frame_type': 'last'
            }
        else:
            return {'error': f'FFmpeg error: {result.stderr}'}

    except Exception as e:
        return {'error': str(e)}

@app.route('/api/mix-image-styles', methods=['POST'])
def mix_image_styles():
    """Mix styles from multiple images using Gemini"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Support both 'image_paths' and 'images' for compatibility
        image_paths = data.get('image_paths', data.get('images', []))
        style_prompt = data.get('style_prompt', data.get('prompt', ''))
        mixing_mode = data.get('mixing_mode', data.get('mode', 'analyze'))

        if not image_paths:
            return jsonify({'error': 'No images provided'}), 400

        if len(image_paths) > 5:
            return jsonify({'error': 'Maximum 5 images allowed'}), 400

        # Validate that all image files exist
        for image_path in image_paths:
            # Try multiple possible paths with fallback
            possible_paths = [
                image_path,  # Use as-is (for absolute paths or correct relative paths)
                os.path.join(config.local_output_dir, image_path),  # Join with output dir
                os.path.join(os.getcwd(), image_path),  # Join with current working directory
                os.path.join(os.getcwd(), config.local_output_dir, image_path),  # Full path from cwd
            ]

            # If path starts with output/, also try without the output prefix
            if image_path.startswith('output/'):
                relative_path = image_path[7:]  # Remove 'output/' prefix
                possible_paths.extend([
                    relative_path,
                    os.path.join(config.local_output_dir, relative_path),
                    os.path.join(os.getcwd(), config.local_output_dir, relative_path),
                ])

            # Find the first path that exists
            full_path = None
            for try_path in possible_paths:
                if os.path.exists(try_path):
                    full_path = try_path
                    print(f"✅ Found image at: {full_path}")
                    break

            if not full_path:
                # Debug: show all attempted paths
                print(f"❌ Could not find image: {image_path}")
                print(f"❌ Tried paths: {possible_paths}")
                return jsonify({'error': f'Image not found: {image_path}. Tried: {possible_paths}'}), 404

        # Prepare content for Gemini
        contents = []

        # Add images to the content
        for i, image_path in enumerate(image_paths):
            # Try multiple possible paths with fallback (same logic as validation)
            possible_paths = [
                image_path,  # Use as-is
                os.path.join(config.local_output_dir, image_path),  # Join with output dir
                os.path.join(os.getcwd(), image_path),  # Join with current working directory
                os.path.join(os.getcwd(), config.local_output_dir, image_path),  # Full path from cwd
            ]

            # If path starts with output/, also try without the output prefix
            if image_path.startswith('output/'):
                relative_path = image_path[7:]  # Remove 'output/' prefix
                possible_paths.extend([
                    relative_path,
                    os.path.join(config.local_output_dir, relative_path),
                    os.path.join(os.getcwd(), config.local_output_dir, relative_path),
                ])

            # Find the first path that exists
            full_path = None
            for try_path in possible_paths:
                if os.path.exists(try_path):
                    full_path = try_path
                    break

            if not full_path:
                # This shouldn't happen since we validated earlier, but just in case
                raise FileNotFoundError(f"Image not found: {image_path}")

            with open(full_path, 'rb') as f:
                image_data = f.read()

            # Get file extension from the actual file path
            file_extension = full_path.split('.')[-1].lower()
            mime_type = f"image/{file_extension}"
            if file_extension == 'jpg':
                mime_type = "image/jpeg"

            contents.append(types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            ))

        # Create the analysis prompt based on mixing mode
        if mixing_mode == 'analyze':
            prompt = f"""
Please analyze these {len(image_paths)} images and identify their key visual styles, including:

1. **Color Palette**: Dominant colors, color harmony, saturation levels
2. **Artistic Style**: Art movement, technique, brush strokes, texture
3. **Composition**: Layout, balance, focal points, perspective
4. **Mood & Atmosphere**: Emotional tone, lighting, ambiance
5. **Subject Matter**: Objects, themes, content focus

User Request: "{style_prompt}"

Please provide a detailed analysis in JSON format:
{{
    "individual_styles": [
        {{
            "image_index": 1,
            "color_palette": "description of colors",
            "artistic_style": "style description",
            "composition": "composition analysis",
            "mood": "mood description",
            "key_elements": ["element1", "element2"]
        }}
    ],
    "style_combinations": {{
        "dominant_colors": ["color1", "color2"],
        "mixed_techniques": ["technique1", "technique2"],
        "unified_mood": "overall mood when combined",
        "style_harmony": "how well styles work together"
    }},
    "recommendations": {{
        "best_combination": "which images work best together",
        "suggested_prompt": "improved prompt for style mixing",
        "creative_directions": ["direction1", "direction2"]
    }}
}}
"""
        elif mixing_mode == 'generate':
            prompt = f"""
Based on these {len(image_paths)} reference images, please provide detailed instructions for creating a new image that combines their styles.

User Request: "{style_prompt}"

Please provide comprehensive generation guidance in JSON format:
{{
    "style_synthesis": {{
        "color_scheme": "how to blend the color palettes",
        "technique_fusion": "how to merge artistic techniques",
        "composition_guide": "how to arrange elements",
        "texture_blending": "how to combine textures"
    }},
    "generation_prompt": "detailed prompt for creating new image with combined styles",
    "technical_settings": {{
        "recommended_style": "overall style direction",
        "key_descriptors": ["descriptor1", "descriptor2"],
        "avoid_elements": ["what not to include"]
    }},
    "variation_ideas": [
        "variation 1 description",
        "variation 2 description"
    ]
}}
"""
        else:  # guide mode
            prompt = f"""
Please provide step-by-step guidance for manually combining the styles from these {len(image_paths)} images.

User Request: "{style_prompt}"

Please provide detailed guidance in JSON format:
{{
    "step_by_step_guide": [
        {{
            "step": 1,
            "action": "what to do",
            "focus_image": "which reference image to focus on",
            "technique": "specific technique to use"
        }}
    ],
    "style_extraction": {{
        "from_image_1": "what to take from first image",
        "from_image_2": "what to take from second image",
        "blending_method": "how to combine elements"
    }},
    "practical_tips": [
        "tip 1",
        "tip 2"
    ],
    "common_pitfalls": [
        "what to avoid",
        "potential issues"
    ]
}}
"""

        # Add the text prompt (following official examples)
        contents.append(prompt)

        # Call Gemini API with config
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["TEXT"],
            candidate_count=1,
            safety_settings=[
                {
                    "method": "PROBABILITY",
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )

        # Use API client for gemini-2.5-flash-image-preview
        active_client = api_client if config.image_edit_model_id == "gemini-2.5-flash-image-preview" else client

        response = active_client.models.generate_content(
            model=config.image_edit_model_id,
            contents=contents,
            config=generate_content_config
        )

        # Try to parse JSON response
        try:
            import json
            result = json.loads(response.text)

            return jsonify({
                'success': True,
                'mixing_mode': mixing_mode,
                'image_count': len(image_paths),
                'analysis': result,
                'user_prompt': style_prompt
            })

        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            return jsonify({
                'success': True,
                'mixing_mode': mixing_mode,
                'image_count': len(image_paths),
                'analysis': {
                    'raw_response': response.text,
                    'note': 'Could not parse as JSON, showing raw response'
                },
                'user_prompt': style_prompt
            })

    except Exception as e:
        print(f"❌ Style mixing error: {str(e)}")
        return jsonify({
            'error': f'Style mixing failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    import socket

    # Get external IP address
    def get_external_ip():
        try:
            # Connect to a remote address to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

    # Get hostname
    hostname = socket.gethostname()
    external_ip = get_external_ip()
    port = 5000

    # Check configured ports for availability
    available_ports = []
    for test_port in config.server_ports:
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind(('', test_port))
            test_socket.close()
            available_ports.append(test_port)
        except:
            pass

    if available_ports:
        port = available_ports[0]

    print("🎬" + "="*60)
    print("🚀 Video Generation Studio is starting...")
    print("="*62)
    print(f"🔌 Using port {port} (available ports: {available_ports})")
    print(f"📍 Local access:    http://localhost:{port}")
    print(f"🌐 Network access:  http://{external_ip}:{port}")
    print(f"🖥️  Hostname:       http://{hostname}:{port}")
    print("="*62)
    print("🌍 External IP confirmed: 34.70.186.61")
    print(f"🔗 External access: http://34.70.186.61:{port}")
    print("="*62)
    print("✅ Server is ready! Open any of the above URLs in your browser.")
    print("🔄 Press Ctrl+C to stop the server")
    print("="*62)

    app.run(debug=config.server_debug, host=config.server_host, port=port)