#!/usr/bin/env python3
"""
Inspect BGC NetCDF files to see what parameters are available
"""

import os
import xarray as xr
import numpy as np
from collections import defaultdict

def inspect_bgc_file(filepath):
    """Inspect a single BGC NetCDF file"""
    try:
        ds = xr.open_dataset(filepath)
        
        # Look for BGC parameters
        bgc_params = []
        bgc_vars = ['DOXY', 'CHLA', 'NITRATE', 'PH_IN_SITU_TOTAL', 'BBP700', 'CDOM', 
                    'DOWN_IRRADIANCE', 'DOWNWELLING_PAR', 'UP_RADIANCE']
        
        for param in bgc_vars:
            adjusted_var = f"{param}_ADJUSTED"
            if adjusted_var in ds.variables:
                # Check if there's actual data (not all NaN)
                data = ds[adjusted_var].values
                if not np.all(np.isnan(data)):
                    bgc_params.append(param)
        
        # Get basic info
        n_prof = ds.sizes.get("N_PROF", 0)
        n_levels = ds.sizes.get("N_LEVELS", 0)
        
        # Get float ID if available
        float_id = "unknown"
        if "PLATFORM_NUMBER" in ds.variables and n_prof > 0:
            try:
                platform_data = ds["PLATFORM_NUMBER"][0].values
                if isinstance(platform_data, np.ndarray) and platform_data.dtype == object:
                    byte_data = platform_data.item()
                    if isinstance(byte_data, bytes):
                        float_id = byte_data.decode('utf-8', errors='ignore').strip()
                    else:
                        float_id = str(byte_data).strip()
                float_id = ''.join(c for c in float_id if c.isdigit())
            except:
                pass
        
        ds.close()
        
        return {
            'filename': os.path.basename(filepath),
            'float_id': float_id,
            'n_profiles': n_prof,
            'n_levels': n_levels,
            'bgc_params': bgc_params
        }
        
    except Exception as e:
        return {
            'filename': os.path.basename(filepath),
            'error': str(e)
        }

def inspect_bgc_directory(directory="./data/bgc_downloads"):
    """Inspect all BGC files in a directory"""
    print("=" * 80)
    print("BGC NetCDF File Inspector")
    print("=" * 80)
    print(f"\nScanning directory: {directory}\n")
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        print("\nPlease run bgc_download.py first to download BGC files.")
        return
    
    nc_files = [f for f in os.listdir(directory) if f.endswith('.nc')]
    
    if not nc_files:
        print(f"❌ No NetCDF files found in {directory}")
        print("\nPlease run bgc_download.py first to download BGC files.")
        return
    
    print(f"Found {len(nc_files)} NetCDF files\n")
    print("-" * 80)
    
    # Collect statistics
    param_counts = defaultdict(int)
    param_combinations = defaultdict(int)
    file_info = []
    
    for i, filename in enumerate(nc_files[:50], 1):  # Inspect first 50 files
        filepath = os.path.join(directory, filename)
        info = inspect_bgc_file(filepath)
        file_info.append(info)
        
        if 'error' not in info:
            # Count individual parameters
            for param in info['bgc_params']:
                param_counts[param] += 1
            
            # Count parameter combinations
            combo = tuple(sorted(info['bgc_params']))
            param_combinations[combo] += 1
            
            # Print file info
            params_str = ', '.join(info['bgc_params']) if info['bgc_params'] else 'None'
            print(f"{i:3d}. {info['filename'][:40]:40s} | Float: {info['float_id']:8s} | "
                  f"Profiles: {info['n_profiles']:3d} | BGC: {params_str}")
        else:
            print(f"{i:3d}. {info['filename'][:40]:40s} | ERROR: {info['error']}")
        
        if i % 10 == 0:
            print()
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print("\n1. BGC Parameter Frequency:")
    print("-" * 80)
    for param, count in sorted(param_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {param:20s}: {count:4d} files ({100*count/len(file_info):.1f}%)")
    
    print("\n2. Parameter Combinations:")
    print("-" * 80)
    for combo, count in sorted(param_combinations.items(), key=lambda x: x[1], reverse=True)[:10]:
        combo_str = ', '.join(combo) if combo else 'No BGC params'
        print(f"  {combo_str:50s}: {count:4d} files")
    
    print("\n3. Example Data Structures:")
    print("-" * 80)
    
    # Show examples of different combinations
    seen_combos = set()
    for info in file_info:
        if 'error' in info or not info['bgc_params']:
            continue
        
        combo = tuple(sorted(info['bgc_params']))
        if combo not in seen_combos and len(seen_combos) < 5:
            seen_combos.add(combo)
            print(f"\n  Float {info['float_id']} ({info['filename']}):")
            print(f"  JSONB structure will be:")
            print("  {")
            for param in info['bgc_params']:
                print(f'    "{param}": {{"value": <float>, "qc": <int>}},')
            print("  }")
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Run: python bgc_ingest.py")
    print("2. This will process all files and store BGC data in JSONB format")
    print("3. Test with: python test_bgc_integration.py")
    print("4. Query example: 'List floats with oxygen measurements'")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    directory = "./data/bgc_downloads"
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    inspect_bgc_directory(directory)
