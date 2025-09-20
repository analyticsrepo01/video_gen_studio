#!/usr/bin/env python3

import os
import glob
import csv
import datetime
from google.cloud import storage

# GCS configuration
GCS_BUCKET_NAME = "tennis-360-myproject002-464908"
GCS_FOLDER = "important"

def upload_all_videos():
    """Upload all videos from output/videos to GCS important folder and create CSV mapping"""
    try:
        # Initialize the GCS client
        storage_client = storage.Client(project='my-project-0004-346516')
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # Read prompts from prompts.txt
        with open("prompts.txt", "r") as f:
            prompts = [line.strip() for line in f.readlines() if line.strip()]
        
        # Find all MP4 files in output/videos
        video_files = glob.glob("output/videos/*.mp4")
        
        if not video_files:
            print("No video files found in output/videos/")
            return
        
        print(f"Found {len(video_files)} video files to upload")
        
        uploaded_count = 0
        failed_count = 0
        csv_data = []
        
        for video_file in video_files:
            try:
                # Get just the filename without path
                filename = os.path.basename(video_file)
                blob_path = f"{GCS_FOLDER}/{filename}"
                blob = bucket.blob(blob_path)
                
                print(f"Uploading {filename} to gs://{GCS_BUCKET_NAME}/{blob_path}")
                blob.upload_from_filename(video_file)
                print(f"✅ Uploaded: {filename}")
                uploaded_count += 1
                
                # Match filename to prompt (first 6 chars + timestamp)
                file_prefix = filename.split('_')[0]
                matched_prompt = None
                for prompt in prompts:
                    if prompt[:6] == file_prefix:
                        matched_prompt = prompt
                        break
                
                if not matched_prompt:
                    matched_prompt = f"Unknown prompt for {file_prefix}"
                
                csv_data.append([matched_prompt, f"gs://{GCS_BUCKET_NAME}/{blob_path}"])
                
            except Exception as e:
                print(f"❌ Failed to upload {filename}: {e}")
                failed_count += 1
        
        # Create CSV mapping file
        csv_filename = f"video_mapping_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Prompt', 'GCS_File_Path'])
            writer.writerows(csv_data)
        
        # Upload CSV to GCS
        csv_blob_path = f"{GCS_FOLDER}/{csv_filename}"
        csv_blob = bucket.blob(csv_blob_path)
        csv_blob.upload_from_filename(csv_filename)
        
        print(f"\n📊 Upload Summary:")
        print(f"✅ Successfully uploaded: {uploaded_count} videos")
        print(f"❌ Failed uploads: {failed_count} videos")
        print(f"✅ CSV mapping uploaded: gs://{GCS_BUCKET_NAME}/{csv_blob_path}")
        print(f"📍 GCS location: gs://{GCS_BUCKET_NAME}/{GCS_FOLDER}/")
        
        # Clean up local CSV
        os.remove(csv_filename)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Video upload failed")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    upload_all_videos()