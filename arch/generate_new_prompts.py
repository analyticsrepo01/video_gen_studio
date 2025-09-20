#!/usr/bin/env python3

import os
import csv
import json
import datetime
import vertexai
from google import genai
from google.cloud import storage

# Configuration
GCS_BUCKET_NAME = "tennis-360-myproject002-464908"
GCS_FOLDER = "important"

# Initialize Gemini client
vertexai.init(project='my-project-0004-346516', location='us-central1')
client = genai.Client(vertexai=True, project='my-project-0004-346516', location='us-central1')

def get_processed_prompts_from_gcs():
    """Download and read the latest CSV mapping file from GCS"""
    try:
        storage_client = storage.Client(project='my-project-0004-346516')
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # List all CSV files in the important folder
        blobs = bucket.list_blobs(prefix=f"{GCS_FOLDER}/video_mapping_")
        csv_blobs = [blob for blob in blobs if blob.name.endswith('.csv')]
        
        if not csv_blobs:
            print("No CSV mapping files found in GCS")
            return []
        
        # Get the latest CSV file
        latest_csv = max(csv_blobs, key=lambda x: x.time_created)
        print(f"Found latest CSV: {latest_csv.name}")
        
        # Download and read the CSV
        csv_content = latest_csv.download_as_text()
        processed_prompts = []
        
        for row in csv.reader(csv_content.strip().split('\n')):
            if row[0] != 'Prompt':  # Skip header
                processed_prompts.append(row[0])
        
        print(f"Found {len(processed_prompts)} processed prompts in GCS")
        return processed_prompts
        
    except Exception as e:
        print(f"Error reading GCS CSV: {e}")
        return []

def get_current_prompts():
    """Read current prompts.txt file"""
    try:
        with open("prompts.txt", "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("prompts.txt not found")
        return []

def generate_prompts_with_gemini():
    """Use Gemini to generate trending, funny prompts for shorts"""
    try:
        prompt = """Generate 15 creative, funny, and trending video prompts perfect for viral shorts. Focus on:
- Current internet trends and memes
- Funny scenarios that would work well as short videos
- Popular culture references
- Absurd but entertaining situations
- Things that would make people laugh and share

Each prompt should be 1-2 sentences, cinematic, and perfect for 30-60 second videos.
Return only the prompts, one per line, without numbering."""

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={
                "temperature": 0.9,
                "max_output_tokens": 1000
            }
        )
        
        content = response.text
        prompts = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        # Clean up any numbered prompts
        cleaned_prompts = []
        for p in prompts:
            # Remove numbers at start like "1. " or "1) "
            cleaned = p.strip()
            if cleaned and (cleaned[0].isdigit() or cleaned.startswith('-')):
                # Find where the actual prompt starts
                for i, char in enumerate(cleaned):
                    if char.isalpha():
                        cleaned = cleaned[i:]
                        break
            if cleaned and len(cleaned) > 10:
                cleaned_prompts.append(cleaned)
        
        return cleaned_prompts[:15]  # Return max 15 prompts
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return []

def main():
    """Main function to check processed prompts and generate new ones if needed"""
    print("🔍 Checking processed prompts from GCS...")
    processed_prompts = get_processed_prompts_from_gcs()
    
    print("📖 Reading current prompts.txt...")
    current_prompts = get_current_prompts()
    
    # Find unprocessed prompts
    unprocessed = [p for p in current_prompts if p not in processed_prompts]
    
    if unprocessed:
        print(f"⏳ Found {len(unprocessed)} unprocessed prompts:")
        for prompt in unprocessed:
            print(f"  - {prompt[:50]}...")
        print("No need to generate new prompts yet.")
        return
    
    print("✅ All prompts have been processed!")
    
    # Backup current prompts.txt
    if current_prompts:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"prompts_{timestamp}.txt"
        os.rename("prompts.txt", backup_filename)
        print(f"📁 Backed up current prompts to: {backup_filename}")
    
    # Generate new prompts using Gemini
    print("🤖 Generating new trending funny prompts with Gemini...")
    new_prompts = generate_prompts_with_gemini()
    
    if new_prompts:
        # Write new prompts.txt
        with open("prompts.txt", "w") as f:
            for prompt in new_prompts:
                f.write(f"{prompt}\n")
        
        print(f"✅ Generated {len(new_prompts)} new prompts in prompts.txt")
        print("📄 New prompts:")
        for i, prompt in enumerate(new_prompts, 1):
            print(f"  {i:2d}. {prompt}")
    else:
        print("❌ Failed to generate new prompts")
        print("💡 You can manually create new prompts in prompts.txt")

if __name__ == "__main__":
    main()