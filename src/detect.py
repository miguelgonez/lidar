import os
import yaml
import json
from PIL import Image
import rasterio
from rasterio.plot import reshape_as_image
import numpy as np
from google import genai
from google.genai import types

# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
#   - do not change this unless explicitly requested by the user
# - Sometimes the google genai SDK has occasional type errors. You might need to run to validate, at time.  
# The SDK was recently renamed from google-generativeai to google-genai. This file reflects the new name and the new APIs.

with open("config.yaml") as f:
    C = yaml.safe_load(f)

os.makedirs("outputs", exist_ok=True)


def create_preview_image(dem_path, output_path, min_val=0.0, max_val=300.0):
    """Create a normalized preview image from a GeoTIFF"""
    try:
        with rasterio.open(dem_path) as src:
            arr = src.read(1)
            
            # Normalize to 0-255 range
            arr_norm = np.clip((arr - min_val) / (max_val - min_val) * 255, 0, 255).astype(np.uint8)
            
            # Create RGB image
            img = Image.fromarray(arr_norm, mode='L').convert('RGB')
            img.save(output_path, 'JPEG')
            print(f"✓ Created preview: {output_path}")
            return True
    except Exception as e:
        print(f"✗ Error creating preview for {dem_path}: {e}")
        return False


def detect_anomalies():
    """Use Gemini AI to detect archaeological anomalies from LiDAR imagery"""
    print("Starting anomaly detection with Gemini AI...")
    
    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("✗ GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key to use anomaly detection")
        return False
    
    # Create client
    client = genai.Client(api_key=api_key)
    
    # Create preview images from GeoTIFFs
    dem_preview = "outputs/dem_preview.jpg"
    hill_preview = "outputs/hill_preview.jpg"
    svf_preview = "outputs/svf_preview.jpg"
    
    if not os.path.exists("data/dem_velez.tif"):
        print("✗ DEM file not found. Please process LAZ files first.")
        return False
    
    create_preview_image("data/dem_velez.tif", dem_preview, 0, 300)
    
    if os.path.exists("data/deriv/hill_45.tif"):
        create_preview_image("data/deriv/hill_45.tif", hill_preview, 0, 255)
    
    if os.path.exists("data/deriv/svf.tif"):
        create_preview_image("data/deriv/svf.tif", svf_preview, 0.5, 1.0)
    
    # Prepare the prompt for archaeological analysis
    prompt = f"""
Eres un arqueólogo experto en análisis LiDAR. Observa las imágenes del terreno de {C['aoi']['name']}.

Imágenes proporcionadas:
1. Modelo Digital del Terreno (DEM) - muestra la elevación
2. Hillshade - resalta la topografía con sombreado
3. Sky View Factor (SVF) - muestra características microtoporáficas

Tu tarea:
1. Identifica hasta 10 anomalías topográficas que podrían ser estructuras arqueológicas ocultas (muros, túmulos, fosas, caminos antiguos)
2. Para cada anomalía, estima las coordenadas aproximadas dentro del área de estudio (bbox: {C['aoi']['bbox']})

Devuelve ÚNICAMENTE un objeto JSON válido (sin markdown, sin texto adicional) con esta estructura exacta:
{{
  "type": "FeatureCollection",
  "features": [
    {{
      "type": "Feature",
      "geometry": {{
        "type": "Point",
        "coordinates": [longitude, latitude]
      }},
      "properties": {{
        "tipo": "muro|túmulo|fossa|camino",
        "score": 0.0-1.0,
        "justificacion": "breve descripción de por qué es una anomalía"
      }}
    }}
  ]
}}
"""
    
    try:
        # Prepare image parts
        content_parts = []
        content_parts.append(types.Part(text=prompt))
        
        # Add images if they exist
        for img_path in [dem_preview, hill_preview, svf_preview]:
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    image_bytes = f.read()
                    content_parts.append(types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    ))
        
        print("Analyzing imagery with Gemini AI...")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=content_parts
        )
        
        # Extract JSON from response
        response_text = response.text if response.text else ""
        
        # Try to extract JSON object
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            geojson_str = response_text[start_idx:end_idx]
            
            # Validate JSON
            geojson_data = json.loads(geojson_str)
            
            # Save to file
            output_path = "outputs/anomalies.geojson"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2, ensure_ascii=False)
            
            num_features = len(geojson_data.get("features", []))
            print(f"✅ Detected {num_features} anomalies")
            print(f"✅ GeoJSON saved to {output_path}")
            return True
        else:
            print("✗ No valid JSON found in Gemini response")
            print("Response:", response_text[:500])
            return False
    
    except Exception as e:
        print(f"✗ Error during anomaly detection: {e}")
        return False


if __name__ == "__main__":
    detect_anomalies()
