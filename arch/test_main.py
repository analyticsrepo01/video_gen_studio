
import asyncio
import datetime
import os

# GCS configuration
GCS_BUCKET_NAME = "veo3"
PROJECT_ID = "my-project-0004-346516"

async def generate_and_upload(prompt):
    """
    Generates a video from a prompt and uploads it to GCS.
    """
    print(f"Starting video generation for prompt: {prompt}")
    # Mock video generation
    print("Mocking video generation...")
    await asyncio.sleep(2)
    print("Mock video generation complete.")

    # Mock video download
    video_filename_temp = "temp_video.mp4"
    print(f"Mocking download to {video_filename_temp}")
    with open(video_filename_temp, "w") as f:
        f.write("This is a dummy video file.")

    # Mock GCS upload
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    video_filename_gcs = f"{prompt[:6]}_{timestamp}.mp4"
    print(f"Mocking upload to gs://{GCS_BUCKET_NAME}/{video_filename_gcs}")
    print("Mock upload complete.")
    os.remove(video_filename_temp)

async def main():
    """
    Reads prompts from a file and starts the video generation for each.
    """
    # Create a dummy prompts.txt for testing
    with open("prompts.txt", "w") as f:
        f.write("A cinematic shot of a majestic lion in the savannah.\n")
        f.write("A futuristic cityscape with flying cars and neon lights.\n")

    with open("prompts.txt", "r") as f:
        prompts = [line.strip() for line in f.readlines() if line.strip()]

    tasks = [generate_and_upload(prompt) for prompt in prompts]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
