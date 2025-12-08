
import os
import requests
from bs4 import BeautifulSoup
import xarray as xr
import numpy as np
from vector_db_manager import FloatChatVectorDB
import shutil
import time

BASE_URL = "https://data-argo.ifremer.fr/dac/incois/"
DOWNLOAD_DIR = "./temp_meta_downloads"

def get_float_urls():
    """Crawl the base URL to find all float directories"""
    print(f"Crawling {BASE_URL}...")
    try:
        response = requests.get(BASE_URL, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch {BASE_URL}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        float_urls = []
        
        for link in soup.find_all('a'):
            href = link.get('href')
            # Float directories are usually numeric, e.g., "1900045/"
            if href and href.endswith('/') and href[:-1].isdigit():
                float_urls.append(BASE_URL + href)
                
        print(f"Found {len(float_urls)} float directories.")
        return float_urls
    except Exception as e:
        print(f"Error crawling: {e}")
        return []

def download_meta_nc(float_url, float_id, max_retries=3):
    """Download meta.nc for a specific float with retries"""
    meta_url = float_url + f"{float_id}_meta.nc"
    target_path = os.path.join(DOWNLOAD_DIR, f"{float_id}_meta.nc")
    
    for attempt in range(max_retries):
        try:
            # Check if file exists on server
            r = requests.head(meta_url, timeout=10)
            if r.status_code != 200:
                # Try generic meta.nc
                meta_url = float_url + "meta.nc"
                
            print(f"Downloading {meta_url} (Attempt {attempt+1}/{max_retries})...")
            r = requests.get(meta_url, timeout=30)
            
            if r.status_code == 200:
                with open(target_path, 'wb') as f:
                    f.write(r.content)
                return target_path
            elif r.status_code == 404:
                print(f"File not found: {meta_url}")
                return None
            else:
                print(f"Failed to download {meta_url}: {r.status_code}")
                
        except Exception as e:
            print(f"Error downloading {meta_url}: {e}")
            
        # Wait before retrying
        time.sleep(2 ** attempt)
        
    print(f"Giving up on {float_id} after {max_retries} attempts.")
    return None

def extract_metadata(nc_path):
    """Extract ALL metadata from NetCDF file"""
    try:
        ds = xr.open_dataset(nc_path)
        metadata = {}
        
        # Helper to decode bytes/strings
        def decode_val(val):
            if isinstance(val, bytes):
                return val.decode('utf-8', errors='ignore').strip()
            elif isinstance(val, str):
                return val.strip()
            elif isinstance(val, (int, float, np.integer, np.floating)):
                return val
            elif isinstance(val, np.ndarray):
                if val.ndim == 0:
                    return decode_val(val.item())
                elif val.dtype.kind in ['S', 'U']:
                    # Join character arrays
                    return "".join([x.decode('utf-8') if isinstance(x, bytes) else str(x) for x in val.flatten()]).strip()
                elif val.dtype.kind == 'O':
                    # Object arrays (mixed types)
                    parts = []
                    for x in val.flatten():
                        parts.append(str(decode_val(x)))
                    return " ".join(parts).strip()
                else:
                    # Numeric arrays - convert to list
                    return val.tolist()
            return str(val).strip()

        # Iterate over ALL variables
        for var_name in ds.variables:
            try:
                val = ds[var_name].values
                decoded = decode_val(val)
                metadata[var_name] = decoded
            except Exception as e:
                print(f"Warning: Failed to extract {var_name}: {e}")
                metadata[var_name] = str(val)

        # Also get global attributes
        for attr_name, attr_val in ds.attrs.items():
            metadata[f"GLOBAL_{attr_name}"] = str(attr_val)

        ds.close()
        
        # Create a rich document content
        import json
        
        # 1. Create a readable summary for the top of the document
        summary_parts = []
        summary_parts.append(f"Argo Float {metadata.get('PLATFORM_NUMBER', 'Unknown')}")
        if 'PROJECT_NAME' in metadata:
            summary_parts.append(f"Project: {metadata['PROJECT_NAME']}")
        if 'PI_NAME' in metadata:
            summary_parts.append(f"PI: {metadata['PI_NAME']}")
        if 'PLATFORM_TYPE' in metadata:
            summary_parts.append(f"Type: {metadata['PLATFORM_TYPE']}")
        if 'LAUNCH_DATE' in metadata:
            summary_parts.append(f"Launched: {metadata['LAUNCH_DATE']}")
        
        # 2. Dump the ENTIRE metadata dictionary as a JSON string at the end
        # This ensures "don't leave anything out" is satisfied and searchable
        full_json = json.dumps(metadata, default=str, indent=2)
        
        document_content = "\n".join(summary_parts) + "\n\nFULL METADATA:\n" + full_json
        
        # Add special fields for vector DB manager
        metadata['document_content'] = document_content
        metadata['float_id'] = str(metadata.get('PLATFORM_NUMBER', '')).strip()
        
        return metadata
        
    except Exception as e:
        print(f"Error parsing {nc_path}: {e}")
        return None

def main():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    vector_db = FloatChatVectorDB()
    
    float_urls = get_float_urls()
    # Limit for testing/demo purposes if needed, or process all
    # float_urls = float_urls[:10] 
    
    all_metadata = []
    
    for url in float_urls:
        float_id = url.split('/')[-2]
        
        # Check if already exists
        if vector_db.check_float_exists(float_id):
            print(f"Skipping {float_id} (already exists)")
            continue
            
        nc_path = download_meta_nc(url, float_id)
        
        if nc_path:
            meta = extract_metadata(nc_path)
            if meta:
                # Clean up float_id (remove extra chars if any)
                if 'PLATFORM_NUMBER' in meta:
                    meta['float_id'] = ''.join(filter(str.isdigit, str(meta['PLATFORM_NUMBER'])))
                
                print(f"Extracted metadata for {float_id}: {meta.get('PI_NAME')}, {meta.get('PROJECT_NAME')}")
                # Add immediately to save progress
                vector_db.add_float_metadata_to_collection([meta])
            
            # Remove file to save space
            os.remove(nc_path)
            
        # Be nice to the server
        time.sleep(0.5)
        
    print("Ingestion complete!")
        
    # Cleanup
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

if __name__ == "__main__":
    main()
