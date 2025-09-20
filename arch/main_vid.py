
import time
import asyncio
from google.cloud import storage
from google import genai
from google.genai import types
import datetime
import vertexai
import random

# GCS configuration
GCS_BUCKET_NAME = "tennis-360-myproject002-464908"
GCS_FOLDER = "important"


# Initialize Vertex AI and GenAI client
vertexai.init(project='my-project-0004-346516', location='us-central1')
client = genai.Client(vertexai=True, project='my-project-0004-346516', location='us-central1')

# Initialize the GCS client
storage_client = storage.Client(project='my-project-0004-346516')
bucket = storage_client.bucket(GCS_BUCKET_NAME)

async def generate_and_upload(prompt):
    """
    Generates a video from a prompt with exponential backoff retry.
    """
    max_retries = 5
    base_wait_time = 60  # Start with 1 minute
    
    for attempt in range(max_retries):
        try:
            print(f"Starting video generation for prompt: {prompt} (attempt {attempt + 1}/{max_retries})")
            operation = client.models.generate_videos(
                # model='veo-3.0-fast-generate-preview', #"veo-3.0-generate-preview",
                model="veo-3.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    number_of_videos=1,
                    duration_seconds=8,
                    person_generation="allow_all", #        "personGeneration": "allow_all"
                ),                
            )
            break  # Success, exit retry loop
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = base_wait_time * (2 ** attempt) + random.uniform(0, 30)
                    print(f"Resource exhausted for '{prompt}'. Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"Max retries reached for '{prompt}'. Skipping.")
                    return
            else:
                # Non-quota error, re-raise
                raise e

    print(f"Waiting for operation {operation.name} to complete...")
    while not operation.done:
        await asyncio.sleep(10)
        try:
            operation = client.operations.get(operation)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Rate limited while checking operation status. Waiting 60 seconds...")
                await asyncio.sleep(60)
                continue
            else:
                raise e

    print(f"Operation {operation.name} completed.")
    
    # Check if operation has a valid response
    if not operation.response:
        print(f"Operation completed but has no response. This might indicate an error.")
        
        # Check for error details
        if hasattr(operation, 'error') and operation.error:
            print(f"Operation error: {operation.error}")
            print(f"Error code: {operation.error.code if hasattr(operation.error, 'code') else 'N/A'}")
            print(f"Error message: {operation.error.message if hasattr(operation.error, 'message') else 'N/A'}")
        
        # Print all available attributes for debugging
        print(f"Operation attributes: {dir(operation)}")
        print(f"Operation metadata: {getattr(operation, 'metadata', 'N/A')}")
        print(f"Operation done: {operation.done}")
        
        return
    
    if not operation.response.generated_videos:
        print(f"Operation completed but no videos were generated.")
        return
    
    generated_video = operation.response.generated_videos[0]
    
    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Save video data to file in output/videos folder
    import os
    os.makedirs("output/videos", exist_ok=True)
    video_filename_temp = f"output/videos/temp_video_{timestamp}.mp4"
    
    with open(video_filename_temp, 'wb') as f:
        f.write(generated_video.video.video_bytes)
    
    # Try to upload to GCS
    video_filename_gcs = f"{GCS_FOLDER}/{prompt[:6]}_{timestamp}.mp4"
    blob = bucket.blob(video_filename_gcs)
    
    try:
        print(f"Uploading video to gs://{GCS_BUCKET_NAME}/{video_filename_gcs}")
        blob.upload_from_filename(video_filename_temp)
        print(f"Video uploaded to GCS: gs://{GCS_BUCKET_NAME}/{video_filename_gcs}")
    except Exception as e:
        print(f"GCS upload failed: {e}")
        print("Continuing with local storage only...")
    
    # Keep local copy and clean up temp file
    video_filename_final = f"output/videos/{prompt[:6]}_{timestamp}.mp4"
    import os
    os.rename(video_filename_temp, video_filename_final)
    
    print(f"Video saved locally as: {video_filename_final}")
    print(f"Generation complete for: {prompt}")

async def upload_prompts_file():
    """
    Uploads the prompts.txt file to GCS bucket.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        prompts_filename_gcs = f"{GCS_FOLDER}/prompts_{timestamp}.txt"
        blob = bucket.blob(prompts_filename_gcs)
        
        print(f"Uploading prompts.txt to gs://{GCS_BUCKET_NAME}/{prompts_filename_gcs}")
        blob.upload_from_filename("prompts.txt")
        print(f"Prompts file uploaded to GCS: gs://{GCS_BUCKET_NAME}/{prompts_filename_gcs}")
    except Exception as e:
        print(f"Failed to upload prompts.txt to GCS: {e}")

async def main():
    """
    Reads prompts from a file and starts the video generation for each.
    """
    with open("prompts.txt", "r") as f:
        prompts = [line.strip() for line in f.readlines() if line.strip()]

    # Upload prompts file to GCS
    await upload_prompts_file()

    # Process prompts sequentially with delay to avoid quota issues
    for i, prompt in enumerate(prompts):
        if i > 0:
            # Add delay between requests to avoid overwhelming the quota
            print(f"Waiting 30 seconds before next request...")
            await asyncio.sleep(30)
        
        await generate_and_upload(prompt)

if __name__ == "__main__":
    asyncio.run(main())
