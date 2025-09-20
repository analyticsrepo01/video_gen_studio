# Video Generation Studio

A comprehensive web application for generating videos and images using Google's AI models (Veo 3 and Imagen).

## Features

- **Video Generation from Text**: Generate videos in 9:16 or 16:9 aspect ratios
- **Image Generation from Text**: Create images using Imagen 3
- **Image Editing**: Edit images with AI using Gemini 2.5 Flash
- **Video from Image**: Generate videos using existing images as reference
- **Video Tools**: Join multiple videos and extract frames using FFmpeg
- **File Management**: Browse and manage generated videos and images
- **GCS Integration**: Automatic upload to Google Cloud Storage

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (for video operations):
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

3. Configure Google Cloud credentials:
   - Set up a service account with appropriate permissions
   - Download the service account key file
   - Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

4. Update configuration in `app.py`:
   - Change `GCS_BUCKET_NAME` to your bucket name
   - Update `PROJECT_ID` and `LOCATION` to match your setup

## Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Video Generation
1. Go to the "Video Generation" tab
2. Enter a text prompt describing your video
3. Select aspect ratio (9:16 for vertical, 16:9 for horizontal)
4. Click "Generate Video"

### Image Generation
1. Go to the "Image Generation" tab
2. Enter a text prompt describing your image
3. Click "Generate Image"

### Image Editing
1. Go to the "Image Editing" tab
2. Enter the path to your image file
3. Describe how you want to edit the image
4. Click "Edit Image"

### Video from Image
1. Go to the "Video from Image" tab
2. Enter the path to your image file
3. Describe the motion/animation you want
4. Select aspect ratio
5. Click "Generate Video"

### Video Tools
1. **Join Videos**: Select multiple videos from the list and join them
2. **Extract Frames**: Extract frames from a video at 1 frame per second

### Browse Files
View all generated videos and images with file details and easy path copying.

## Directory Structure

```
app/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Web interface
├── output/
│   ├── videos/         # Generated videos
│   └── images/         # Generated images
├── temp/               # Temporary files
└── requirements.txt    # Python dependencies
```

## API Endpoints

- `POST /api/generate-video` - Generate video from text
- `POST /api/generate-image` - Generate image from text
- `POST /api/edit-image` - Edit image with AI
- `POST /api/generate-video-from-image` - Generate video from image
- `POST /api/join-videos` - Join multiple videos
- `POST /api/extract-frames` - Extract frames from video
- `GET /api/list-videos` - List all videos
- `GET /api/list-images` - List all images

## Notes

- Video generation can take several minutes
- Large files are automatically uploaded to Google Cloud Storage
- FFmpeg is required for video joining and frame extraction
- The app includes retry logic for quota limits and rate limiting