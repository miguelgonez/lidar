import subprocess
import os
import rasterio
from scipy.ndimage import maximum_filter
import numpy as np

os.makedirs("data/deriv", exist_ok=True)


def hill_multi(dem):
    """Generate multiple hillshade images from different azimuth angles"""
    print("Generating hillshade derivatives...")
    for az in (45, 90, 135, 180, 225, 270, 315, 360):
        out = f"data/deriv/hill_{az}.tif"
        try:
            subprocess.run(
                ["gdaldem", "hillshade", "-az", str(az), "-alt", "45", 
                 "-compute_edges", dem, out],
                check=True,
                capture_output=True
            )
            print(f"✓ Generated hillshade azimuth {az}°")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error generating hillshade {az}°: {e.stderr.decode()}")
        except FileNotFoundError:
            print("✗ Error: gdaldem command not found. Make sure GDAL is installed.")
            break


def svf(dem):
    """Calculate Sky View Factor (SVF) from DEM"""
    print("Calculating Sky View Factor...")
    try:
        with rasterio.open(dem) as src:
            arr = src.read(1)
            meta = src.meta.copy()
        
        # Apply maximum filter to simulate sky visibility
        rad = 25
        maxf = maximum_filter(arr, size=rad)
        
        # Calculate SVF
        svf_arr = 1 - (maxf - arr) / (arr + 30)
        
        # Update metadata for output
        meta.update(dtype="float32")
        
        with rasterio.open("data/deriv/svf.tif", "w", **meta) as dst:
            dst.write(svf_arr.astype("float32"), 1)
        
        print("✓ Sky View Factor calculated")
    
    except Exception as e:
        print(f"✗ Error calculating SVF: {e}")


if __name__ == "__main__":
    dem_path = "data/dem_velez.tif"
    
    if not os.path.exists(dem_path):
        print(f"✗ DEM file not found: {dem_path}")
        print("Please run the PDAL pipeline first to generate the DEM.")
    else:
        hill_multi(dem_path)
        svf(dem_path)
        print("✅ Processing complete")
