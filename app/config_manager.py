"""
Configuration Manager for Video Generation Studio

This module handles loading and managing configuration from config.json
"""

import json
import os
from typing import Dict, Any, List, Optional

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_path} not found!")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {self.config_path}: {e}")
            raise

    def save_config(self) -> None:
        """Save current configuration to JSON file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            raise

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('models.video_generation.model_id')
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        Example: config.set('models.video_generation.model_id', 'veo-3-1')
        """
        keys = key_path.split('.')
        target = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Set the final value
        target[keys[-1]] = value

    # App Info
    @property
    def app_name(self) -> str:
        return self.get('app_info.name', 'Video Generation Studio')

    @property
    def app_version(self) -> str:
        return self.get('app_info.version', '1.0.0')

    # Server Configuration
    @property
    def server_host(self) -> str:
        return self.get('server.host', '0.0.0.0')

    @property
    def server_ports(self) -> List[int]:
        return self.get('server.ports', [8088, 8089, 5000])

    @property
    def server_debug(self) -> bool:
        return self.get('server.debug', True)

    # Google Cloud Configuration
    @property
    def gcp_project_id(self) -> str:
        return self.get('google_cloud.project_id', 'your-project-id')

    @property
    def gcp_location(self) -> str:
        return self.get('google_cloud.location', 'us-central1')

    @property
    def gcs_bucket_name(self) -> str:
        return self.get('google_cloud.gcs_bucket_name', 'your-bucket-name')

    # Model Configuration
    @property
    def video_model_id(self) -> str:
        return self.get('models.video_generation.model_id', 'veo-3-0')

    @property
    def image_model_id(self) -> str:
        return self.get('models.image_generation.model_id', 'imagen-3.0-generate-001')

    @property
    def image_edit_model_id(self) -> str:
        return self.get('models.image_editing.model_id', 'gemini-2.5-flash-image-preview')

    @property
    def prompt_refine_model_id(self) -> str:
        return self.get('models.prompt_refinement.model_id', 'gemini-2.0-flash-exp')

    # Generation Settings
    @property
    def default_video_resolution(self) -> str:
        return self.get('generation_settings.video.default_resolution', '1080p')

    @property
    def default_video_aspect_ratio(self) -> str:
        return self.get('generation_settings.video.default_aspect_ratio', '16:9')

    @property
    def video_timeout(self) -> int:
        return self.get('generation_settings.video.timeout_seconds', 300)

    @property
    def video_retry_attempts(self) -> int:
        return self.get('generation_settings.video.retry_attempts', 3)

    @property
    def image_timeout(self) -> int:
        return self.get('generation_settings.image.timeout_seconds', 60)

    @property
    def image_retry_attempts(self) -> int:
        return self.get('generation_settings.image.retry_attempts', 3)

    # File Handling
    @property
    def max_file_size_mb(self) -> int:
        return self.get('file_handling.upload.max_file_size_mb', 500)

    @property
    def allowed_image_formats(self) -> List[str]:
        return self.get('file_handling.upload.allowed_image_formats',
                       ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'])

    @property
    def allowed_video_formats(self) -> List[str]:
        return self.get('file_handling.upload.allowed_video_formats',
                       ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'])

    @property
    def local_output_dir(self) -> str:
        return self.get('file_handling.storage.local_output_dir', 'output')

    @property
    def temp_dir(self) -> str:
        return self.get('file_handling.storage.temp_dir', 'temp')

    @property
    def gcs_upload_threshold_mb(self) -> int:
        return self.get('file_handling.storage.gcs_upload_threshold_mb', 100)

    # Features
    @property
    def ffmpeg_enabled(self) -> bool:
        return self.get('features.video_tools.ffmpeg_enabled', True)

    @property
    def prompt_refinement_enabled(self) -> bool:
        return self.get('features.ai_features.prompt_refinement_enabled', True)

    @property
    def negative_prompts_enabled(self) -> bool:
        return self.get('features.ai_features.negative_prompts_enabled', True)

    # UI Settings
    @property
    def primary_color(self) -> str:
        return self.get('ui_settings.theme.primary_color', '#667eea')

    @property
    def enabled_tabs(self) -> List[str]:
        return self.get('ui_settings.tabs.enabled_tabs', [
            'video-gen', 'image-gen', 'image-edit', 'video-from-image',
            'video-tools', 'upload', 'browse', 'guidelines', 'prompt-refine'
        ])

    @property
    def default_tab(self) -> str:
        return self.get('ui_settings.tabs.default_tab', 'video-gen')

    # Rate Limiting
    def get_rate_limit(self, service: str, period: str) -> int:
        """Get rate limit for a specific service and time period"""
        return self.get(f'rate_limiting.{service}.requests_per_{period}', 999)

    # Validation Methods
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Check required fields
        required_fields = [
            'google_cloud.project_id',
            'google_cloud.gcs_bucket_name',
            'models.video_generation.model_id',
            'models.image_generation.model_id'
        ]

        for field in required_fields:
            if not self.get(field):
                errors.append(f"Missing required configuration: {field}")

        # Check if directories exist and create them if needed
        output_dir = self.local_output_dir
        temp_dir = self.temp_dir

        try:
            os.makedirs(f"{output_dir}/videos", exist_ok=True)
            os.makedirs(f"{output_dir}/images", exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Failed to create directories: {e}")

        return errors

    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get complete model information for a specific type"""
        return self.get(f'models.{model_type}', {})

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all configured models"""
        return self.get('models', {})

    def print_config_summary(self) -> None:
        """Print a summary of current configuration"""
        print("\n" + "="*60)
        print(f"📋 {self.app_name} v{self.app_version} - Configuration Summary")
        print("="*60)
        print(f"🔧 Project ID: {self.gcp_project_id}")
        print(f"🪣 GCS Bucket: {self.gcs_bucket_name}")
        print(f"🎬 Video Model: {self.video_model_id}")
        print(f"🖼️  Image Model: {self.image_model_id}")
        print(f"✏️  Edit Model: {self.image_edit_model_id}")
        print(f"🚀 Refine Model: {self.prompt_refine_model_id}")
        print(f"📁 Output Dir: {self.local_output_dir}")
        print(f"🌐 Server: {self.server_host}:{self.server_ports}")
        print("="*60)

        # Validate and show any errors
        errors = self.validate_config()
        if errors:
            print("⚠️  Configuration Issues:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Configuration is valid!")
        print("="*60 + "\n")

# Create global config instance
config = ConfigManager()