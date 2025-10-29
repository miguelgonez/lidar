import asyncio
import aiohttp
import aiofiles
import geopandas as gpd
from shapely.geometry import box
import yaml
import os

with open("config.yaml") as f:
    C = yaml.safe_load(f)

BBOX = C["aoi"]["bbox"]
OUT = "data/laz"
os.makedirs(OUT, exist_ok=True)

INDEX_URL = ("https://centrodedescargas.cnig.es/CentroDescargas/"
             "documentos/PDT_LIDAR3_2025.zip")


async def download_laz(session, sem, url, path):
    """Download a single LAZ file with semaphore for concurrency control"""
    async with sem:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as r:
                if r.status == 200:
                    async with aiofiles.open(path, "wb") as f:
                        async for chunk in r.content.iter_chunked(1024 * 64):
                            await f.write(chunk)
                    print(f"✓ Downloaded {os.path.basename(path)}")
                else:
                    print(f"✗ Failed to download {os.path.basename(path)}: HTTP {r.status}")
        except Exception as e:
            print(f"✗ Error downloading {os.path.basename(path)}: {e}")


async def main():
    """Download LAZ tiles from CNIG for the configured bounding box"""
    print(f"Downloading PNOA-LiDAR tiles for {C['aoi']['name']}...")
    print(f"Bounding box: {BBOX}")
    
    try:
        # Read the index of available tiles
        idx = gpd.read_file(INDEX_URL).to_crs(4326)
        
        # Filter tiles that intersect with our AOI
        tiles = idx[idx.intersects(box(*BBOX))].head(C["aoi"]["max_downloads"])
        
        if len(tiles) == 0:
            print("⚠ No tiles found for the specified bounding box")
            return
        
        print(f"Found {len(tiles)} tiles to download")
        
        # Download tiles with concurrency control
        sem = asyncio.Semaphore(6)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _, row in tiles.iterrows():
                url = row.URL_DESCARGA
                fname = f"{row.HOJA}.laz"
                tasks.append(download_laz(session, sem, url, f"{OUT}/{fname}"))
            await asyncio.gather(*tasks)
        
        print(f"✅ Download complete: {len(tasks)} LAZ files")
    
    except Exception as e:
        print(f"✗ Error during download process: {e}")


if __name__ == "__main__":
    asyncio.run(main())
