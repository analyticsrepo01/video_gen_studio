# 🎬 Video Generation Studio

A comprehensive web application for generating videos and images using Google's latest AI models including **Veo 3.0**, **Imagen 3.0**, and **Gemini 2.5 Flash**.

![Video Generation Studio](https://img.shields.io/badge/AI-Video%20Generation-blue) ![Google AI](https://img.shields.io/badge/Powered%20by-Google%20AI-green) ![Flask](https://img.shields.io/badge/Built%20with-Flask-red)

## ✨ Features

### 🎥 **Video Generation**
- **Text-to-Video**: Generate videos from text descriptions using Veo 3.0
- **Image-to-Video**: Animate static images into dynamic videos
- **Advanced Controls**: Resolution, aspect ratio, negative prompts
- **High Quality**: Up to 1080p resolution with 8-second duration

### 🖼️ **Image Generation & Editing**
- **Text-to-Image**: Create images from text using Imagen 3.0
- **AI Image Editing**: Edit images with natural language using Gemini 2.5 Flash Image Preview
- **Style Mixing**: Combine styles from multiple reference images
- **Text Overlay**: Add text and decorative elements to images

### 🛠️ **Video Tools**
- **Frame Extraction**: Extract specific frames or sequences
- **Video Joining**: Combine multiple videos
- **Format Support**: MP4, AVI, MOV, MKV, WebM, and more

### 🎨 **Creative Features**
- **Prompt Refinement**: AI-powered prompt enhancement
- **Style Analysis**: Analyze and combine visual styles
- **Batch Processing**: Process multiple files
- **Real-time Preview**: Live preview of edits and overlays

### 📁 **File Management**
- **Cloud Storage**: Automatic upload to Google Cloud Storage
- **Local Storage**: Organized output directories
- **File Browser**: Built-in file management
- **Format Support**: Extensive image and video format support

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Google Cloud Account** with billing enabled
3. **FFmpeg** (for video processing)
4. **Google AI Studio API Key** (for image editing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/video-generation-studio.git
   cd video-generation-studio
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install -y ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

4. **Set up Google Cloud**
   ```bash
   # Install gcloud CLI
   # Download from: https://cloud.google.com/sdk/docs/install

   # Authenticate
   gcloud auth login
   gcloud auth application-default login

   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

6. **Create output directories**
   ```bash
   mkdir -p app/output/videos app/output/images app/temp
   ```

### Configuration

#### 1. Google AI Studio API Key
Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

```bash
# Add to .env file
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

#### 2. Google Cloud Setup
```bash
# Create a service account
gcloud iam service-accounts create video-gen-service \
    --display-name="Video Generation Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:video-gen-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:video-gen-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=video-gen-service@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

#### 3. Enable Required APIs
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable vertexai.googleapis.com
```

#### 4. Create GCS Bucket
```bash
gsutil mb gs://your-unique-bucket-name
```

### Running the Application

1. **Start the server**
   ```bash
   cd app
   python app.py
   ```

2. **Access the application**
   - Open your browser to `http://localhost:5000`
   - The app will automatically detect available ports

3. **Or use the startup script**
   ```bash
   chmod +x app/run.sh
   ./app/run.sh
   ```

## 🎯 What This App Can Do

### 🎥 **Video Generation Capabilities**

| Feature | Description | Model Used |
|---------|-------------|------------|
| **Text-to-Video** | Generate 8-second videos from text descriptions | Veo 3.0 |
| **Image-to-Video** | Animate static images with motion prompts | Veo 3.0 |
| **Style Control** | Control artistic style, mood, and aesthetics | Veo 3.0 |
| **Quality Options** | 720p, 1080p resolution with 16:9 or 9:16 aspect ratios | Veo 3.0 |

### 🖼️ **Image Generation & Editing**

| Feature | Description | Model Used |
|---------|-------------|------------|
| **Text-to-Image** | Create high-quality images from descriptions | Imagen 3.0 |
| **AI Image Editing** | Edit existing images with natural language | Gemini 2.5 Flash Image Preview |
| **Style Transfer** | Apply artistic styles to existing images | Gemini 2.5 Flash Image Preview |
| **Multi-Style Mixing** | Combine visual elements from multiple images | Gemini 2.5 Flash Image Preview |

### 🔧 **Advanced Features**

- **Prompt Enhancement**: AI automatically improves your prompts for better results
- **Validation System**: AI validates edits and suggests improvements
- **Batch Processing**: Process multiple files simultaneously
- **Cloud Integration**: Automatic backup to Google Cloud Storage
- **Format Conversion**: Support for 15+ image and video formats
- **Real-time Preview**: See edits before processing

### 🎨 **Creative Workflows**

1. **Content Creation Pipeline**:
   Text Prompt → Image Generation → Image Editing → Video Animation

2. **Style Exploration**:
   Reference Images → Style Analysis → Style Mixing → New Creations

3. **Video Production**:
   Concept → Storyboard Images → Video Generation → Post-processing

## 📁 Project Structure

```
video-generation-studio/
├── app/
│   ├── app.py                 # Main Flask application
│   ├── config.json           # Configuration settings
│   ├── config_manager.py     # Configuration management
│   ├── run.sh               # Startup script
│   ├── templates/
│   │   └── index.html       # Web interface
│   └── output/              # Generated content
│       ├── videos/          # Generated videos
│       └── images/          # Generated images
├── test/                     # Test files and validation
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ⚙️ Configuration

The app uses `config.json` for centralized configuration:

```json
{
  "models": {
    "video_generation": {
      "model_id": "veo-3.0-generate-001",
      "max_duration_seconds": 8
    },
    "image_generation": {
      "model_id": "imagen-3.0-generate-001"
    },
    "image_editing": {
      "model_id": "gemini-2.5-flash-image-preview"
    }
  }
}
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Test basic functionality
python test/test_image_editing.py

# Test API key implementation
python test/test_api_key_implementation.py

# Test model availability
python test/test_model_availability.py
```

## 🔧 Troubleshooting

### Common Issues

1. **"API keys are not supported"**
   - Solution: Ensure you're using the correct authentication method for each model

2. **"Model not found"**
   - Solution: Check model availability in your Google Cloud project and region

3. **FFmpeg not found**
   - Solution: Install FFmpeg using your system's package manager

4. **Permission denied**
   - Solution: Verify Google Cloud service account permissions

5. **Quota exceeded**
   - Solution: Check your Google Cloud quotas and billing

### Getting Help

- Check the [Google AI Documentation](https://ai.google.dev/)
- Review [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- File issues on our [GitHub repository](https://github.com/yourusername/video-generation-studio/issues)

## 🔒 Security Notes

- Never commit API keys or credentials to version control
- Use environment variables for sensitive configuration
- Regularly rotate your API keys and service account keys
- Review and limit Google Cloud IAM permissions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⭐ Acknowledgments

- Google AI Team for the amazing Veo, Imagen, and Gemini models
- Google Cloud Platform for the infrastructure
- Flask community for the excellent web framework

---

**Built with ❤️ using Google's latest AI models**