import os
import sys
import json
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from core.config import settings

def main():
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return

    client = genai.Client(api_key=api_key)
    
    # Load coordinates
    toado_path = Path(__file__).resolve().parents[1] / "toado.md"
    with open(toado_path, "r", encoding="utf-8") as f:
        toado_content = f.read()

    # Load image
    map_image_path = Path(__file__).resolve().parents[1] / "map.png"
    if not map_image_path.exists():
        print(f"Error: {map_image_path} does not exist.")
        return

    print("Analyzing map.png with Gemini...")
    image = Image.open(map_image_path)
    print(f"Image format: {image.format}, size: {image.size}")

    prompt = f"""
You are an expert cartographer and geographic analyst.
We have an image file `map.png` which is a map of the Imperial City of Hue (Hoàng thành Huế / Đại Nội Huế).
We also have a list of historical locations/buildings with their real GPS coordinates (latitude, longitude) from `toado.md`:

{toado_content}

Your task:
1. Examine the image `map.png`. Identify what area of Hoàng thành Huế it covers.
2. Determine the coordinates of the Southwest (bottom-left) and Northeast (top-right) corners of the map image `map.png` so that when we use Leaflet's `ImageOverlay` with bounds `[ [SW_lat, SW_lng], [NE_lat, NE_lng] ]`, the GPS coordinates of the 16 monuments in the list will align exactly with their corresponding visual locations in the image.
   Note: Imperial City of Hue is oriented such that its main axis is tilted by about 45 degrees (facing Southeast). Ensure you inspect the image orientation. In the image, is North pointing straight up, or is the Citadel aligned straight (which means North is tilted)?
   If the Citadel is aligned straight in the image, then North is tilted about 45 degrees to the left or right, and standard Leaflet bounding box might need adjustment, or the image bounds must cover the full area containing all these points when projected.
3. If the image itself is oriented with North pointing up (as standard maps), please calculate the SW and NE coordinates of the boundary of the image.
4. Provide the exact coordinates of the SW corner and NE corner of the image in JSON format:
{{
  "analysis": "Your analysis of the image orientation and location alignment",
  "sw": [latitude, longitude],
  "ne": [latitude, longitude],
  "alignments": [
     {{"id": 1, "name": "Cửa Hòa Bình", "gps": [16.4721279, 107.5762716], "description_of_position_on_image": "e.g., center top edge, or center, etc."}}
  ]
}}
"""

    response = client.models.generate_content(
        model=settings.GEMINI_VISION_MODEL,
        contents=[prompt, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    print("Analysis complete. Writing to map_analysis_result.json...")
    with open("map_analysis_result.json", "w", encoding="utf-8") as out:
        out.write(response.text)
    print("Saved response to map_analysis_result.json successfully.")

if __name__ == "__main__":
    main()
