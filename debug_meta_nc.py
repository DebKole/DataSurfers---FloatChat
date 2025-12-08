
import requests
import xarray as xr
import os
import numpy as np

url = "https://data-argo.ifremer.fr/dac/incois/1900121/1900121_meta.nc"
filename = "debug_meta.nc"

def debug_meta():
    print(f"Downloading {url}...")
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)
        
    ds = xr.open_dataset(filename)
    
    print(f"Global Attributes: {ds.attrs}")
    
    print("\nVariables:")
    for var_name in ds.variables:
        data = ds[var_name]
        print(f"  - {var_name}: {data.dtype} {data.shape}")
        # print(f"    Values: {data.values}")

    ds.close()
    # os.remove(filename)

if __name__ == "__main__":
    debug_meta()
