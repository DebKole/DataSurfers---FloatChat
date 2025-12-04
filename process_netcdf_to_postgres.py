"""
Process all NetCDF files into PostgreSQL-ready format
Handles 31 files with global unique IDs and proper data structure
"""

import os
import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class NetCDFProcessor:
    def __init__(self, data_dir="./data/indian_ocean/2025/01/", db_config=None):
        self.data_dir = data_dir
        self.db_config = db_config
        self.global_profile_counter = self._get_next_profile_id()
        self.processed_files = []
    
    def _get_next_profile_id(self):
        """Get the next available global profile ID from database"""
        if not self.db_config:
            return 1  # Default for non-database usage
        
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get the current maximum global_profile_id
            cursor.execute("SELECT COALESCE(MAX(global_profile_id), 0) + 1 FROM argo_profiles")
            next_id = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"Starting global profile counter from: {next_id}")
            return next_id
            
        except Exception as e:
            print(f"Warning: Could not connect to database to get next ID: {e}")
            return 1  # Fallback to 1 if database connection fails
        
    def get_netcdf_files(self):
        """Get all NetCDF files from the directory"""
        files = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.nc'):
                files.append(filename)
        return sorted(files)
    
    def extract_float_id(self, ds, profile_idx):
        """Safely extract float ID from dataset"""
        try:
            if "PLATFORM_NUMBER" in ds.variables:
                platform_data = ds["PLATFORM_NUMBER"][profile_idx].values
                
                
                # Handle the byte string format we're seeing: b'5906527 '
                if isinstance(platform_data, np.ndarray) and platform_data.dtype == object:
                    # Extract the actual byte string from the numpy array
                    byte_data = platform_data.item()
                    if isinstance(byte_data, bytes):
                        float_id = byte_data.decode('utf-8', errors='ignore').strip()
                    else:
                        float_id = str(byte_data).strip()
                elif hasattr(platform_data, 'dtype'):
                    if platform_data.dtype.kind == 'S':  # Byte string
                        float_id = platform_data.tobytes().decode('utf-8', errors='ignore').strip()
                    elif platform_data.dtype.kind == 'U':  # Unicode string
                        float_id = str(platform_data).strip()
                    else:
                        float_id = str(platform_data).strip()
                else:
                    float_id = str(platform_data).strip()
                
                # Clean up common artifacts but preserve alphanumeric
                float_id = float_id.replace('\x00', '').replace('\n', '').replace('\r', '').strip()
                # Keep only digits (Argo float IDs are numeric)
                float_id = ''.join(c for c in float_id if c.isdigit())
                
                
                # Validate float ID format
                if float_id and len(float_id) >= 4:
                    return float_id
                else:
                    return "unknown"
            return "unknown"
        except Exception as e:
            print(f"Warning: Could not extract float ID for profile {profile_idx}: {e}")
            return "unknown"
    
    def extract_datetime(self, ds, profile_idx):
        """Safely extract datetime from dataset"""
        try:
            if "JULD" in ds.variables:
                juld_val = ds["JULD"][profile_idx].values
                
                
                # Handle numpy.datetime64 objects directly
                if isinstance(juld_val, np.datetime64):
                    # Convert numpy.datetime64 to pandas Timestamp
                    datetime_val = pd.Timestamp(juld_val)
                    
                    
                    # Validate the datetime is reasonable (between 1990 and 2030)
                    if pd.Timestamp('1990-01-01') <= datetime_val <= pd.Timestamp('2030-12-31'):
                        return datetime_val
                    else:
                        if profile_idx < 3:
                            print(f"Debug profile {profile_idx}: datetime out of valid range")
                        return None
                else:
                    # Handle other formats (shouldn't happen with this data)
                    if profile_idx < 3:
                        print(f"Debug profile {profile_idx}: unexpected JULD format")
                    return None
            return None
        except Exception as e:
            print(f"Warning: Could not extract datetime for profile {profile_idx}: {e}")
            return None
    
    def process_single_file(self, filename):
        """Process a single NetCDF file"""
        file_path = os.path.join(self.data_dir, filename)
        print(f"Processing {filename}...")
        
        try:
            ds = xr.open_dataset(file_path)
        except Exception as e:
            print(f"Error opening {filename}: {e}")
            return pd.DataFrame(), pd.DataFrame()
        
        # Get dimensions
        n_prof = ds.sizes.get("N_PROF", 0)
        n_levels = ds.sizes.get("N_LEVELS", 0)
        
        if n_prof == 0 or n_levels == 0:
            print(f"Skipping {filename} - no valid dimensions")
            ds.close()
            return pd.DataFrame(), pd.DataFrame()
        
        # Extract adjusted variables and QC flags
        try:
            # Use adjusted values instead of raw values
            pres = ds["PRES_ADJUSTED"].values if "PRES_ADJUSTED" in ds.variables else np.full((n_prof, n_levels), np.nan)
            temp = ds["TEMP_ADJUSTED"].values if "TEMP_ADJUSTED" in ds.variables else np.full((n_prof, n_levels), np.nan)
            psal = ds["PSAL_ADJUSTED"].values if "PSAL_ADJUSTED" in ds.variables else np.full((n_prof, n_levels), np.nan)
            
            # Extract QC flags
            pres_qc = ds["PRES_ADJUSTED_QC"].values if "PRES_ADJUSTED_QC" in ds.variables else np.full((n_prof, n_levels), np.nan)
            temp_qc = ds["TEMP_ADJUSTED_QC"].values if "TEMP_ADJUSTED_QC" in ds.variables else np.full((n_prof, n_levels), np.nan)
            psal_qc = ds["PSAL_ADJUSTED_QC"].values if "PSAL_ADJUSTED_QC" in ds.variables else np.full((n_prof, n_levels), np.nan)
            
            # Convert QC flags from bytes to integers if needed
            def qc_to_int(qc_array):
                """Convert QC flags to integer values"""
                if qc_array.dtype.kind in ['S', 'U', 'O']:  # String or object type
                    result = np.full(qc_array.shape, np.nan)
                    for i in range(qc_array.shape[0]):
                        for j in range(qc_array.shape[1]):
                            try:
                                val = qc_array[i, j]
                                if isinstance(val, bytes):
                                    val = val.decode('utf-8').strip()
                                elif isinstance(val, str):
                                    val = val.strip()
                                else:
                                    val = str(val).strip()
                                
                                if val and val.isdigit():
                                    result[i, j] = int(val)
                            except:
                                result[i, j] = np.nan
                    return result
                return qc_array.astype(float)
            
            pres_qc = qc_to_int(pres_qc)
            temp_qc = qc_to_int(temp_qc)
            psal_qc = qc_to_int(psal_qc)
            
            lat = ds["LATITUDE"].values if "LATITUDE" in ds.variables else np.full(n_prof, np.nan)
            lon = ds["LONGITUDE"].values if "LONGITUDE" in ds.variables else np.full(n_prof, np.nan)
        except Exception as e:
            print(f"Error extracting variables from {filename}: {e}")
            ds.close()
            return pd.DataFrame(), pd.DataFrame()
        
        profiles_data = []
        measurements_data = []
        
        for local_profile_id in range(n_prof):
            # Generate global unique ID
            global_profile_id = self.global_profile_counter
            self.global_profile_counter += 1
            
            # Extract profile metadata
            float_id = self.extract_float_id(ds, local_profile_id)
            datetime_val = self.extract_datetime(ds, local_profile_id)
            
            cycle_number = None
            try:
                if "CYCLE_NUMBER" in ds.variables:
                    cycle_number = int(ds["CYCLE_NUMBER"][local_profile_id].values)
            except:
                pass
            
            # Calculate pressure range for this profile
            profile_pressures = pres[local_profile_id, :]
            valid_pressures = profile_pressures[~np.isnan(profile_pressures)]
            
            min_pressure = float(np.min(valid_pressures)) if len(valid_pressures) > 0 else None
            max_pressure = float(np.max(valid_pressures)) if len(valid_pressures) > 0 else None
            measurement_count = len(valid_pressures)
            
            # Profile record
            profile_record = {
                'global_profile_id': global_profile_id,
                'source_file': filename,
                'local_profile_id': local_profile_id,
                'float_id': float_id,
                'cycle_number': cycle_number,
                'datetime': datetime_val,
                'latitude': float(lat[local_profile_id]) if not np.isnan(lat[local_profile_id]) else None,
                'longitude': float(lon[local_profile_id]) if not np.isnan(lon[local_profile_id]) else None,
                'min_pressure': min_pressure,
                'max_pressure': max_pressure,
                'measurement_count': measurement_count,
                'project_name': str(ds.attrs.get('project_name', 'ARGO')),
                'institution': str(ds.attrs.get('institution', 'unknown')),
                'data_mode': str(ds.attrs.get('data_mode', 'R'))
            }
            profiles_data.append(profile_record)
            
            # Extract measurements for this profile
            for level in range(n_levels):
                # Get QC values for this measurement
                pres_qc_val = pres_qc[local_profile_id, level]
                temp_qc_val = temp_qc[local_profile_id, level]
                psal_qc_val = psal_qc[local_profile_id, level]
                
                # Only include measurements where:
                # 1. All values are not NaN
                # 2. All QC flags are <= 3 and not NaN
                if (not np.isnan(pres[local_profile_id, level]) and 
                    not np.isnan(temp[local_profile_id, level]) and 
                    not np.isnan(psal[local_profile_id, level]) and
                    not np.isnan(pres_qc_val) and pres_qc_val <= 3 and
                    not np.isnan(temp_qc_val) and temp_qc_val <= 3 and
                    not np.isnan(psal_qc_val) and psal_qc_val <= 3):
                    
                    measurement_record = {
                        'global_profile_id': global_profile_id,
                        'level': level,
                        'pressure_adjusted': float(pres[local_profile_id, level]),
                        'temperature_adjusted': float(temp[local_profile_id, level]),
                        'salinity_adjusted': float(psal[local_profile_id, level]),
                        'pressure_adjusted_qc': int(pres_qc_val),
                        'temperature_adjusted_qc': int(temp_qc_val),
                        'salinity_adjusted_qc': int(psal_qc_val),
                        'latitude': float(lat[local_profile_id]) if not np.isnan(lat[local_profile_id]) else None,
                        'longitude': float(lon[local_profile_id]) if not np.isnan(lon[local_profile_id]) else None,
                        'datetime': datetime_val
                    }
                    measurements_data.append(measurement_record)
        
        ds.close()
        
        profiles_df = pd.DataFrame(profiles_data)
        measurements_df = pd.DataFrame(measurements_data)
        
        print(f"  Extracted {len(profiles_df)} profiles and {len(measurements_df)} measurements")
        
        return profiles_df, measurements_df
    
    def process_all_files(self):
        """Process all NetCDF files in the directory"""
        nc_files = self.get_netcdf_files()
        print(f"Found {len(nc_files)} NetCDF files to process")
        
        all_profiles = []
        all_measurements = []
        
        for filename in nc_files:
            profiles_df, measurements_df = self.process_single_file(filename)
            
            if not profiles_df.empty:
                all_profiles.append(profiles_df)
            if not measurements_df.empty:
                all_measurements.append(measurements_df)
            
            self.processed_files.append({
                'filename': filename,
                'profiles': len(profiles_df),
                'measurements': len(measurements_df)
            })
        
        # Combine all data
        if all_profiles:
            master_profiles = pd.concat(all_profiles, ignore_index=True)
        else:
            master_profiles = pd.DataFrame()
            
        if all_measurements:
            master_measurements = pd.concat(all_measurements, ignore_index=True)
        else:
            master_measurements = pd.DataFrame()
        
        return master_profiles, master_measurements
    
    def save_to_csv(self, profiles_df, measurements_df, output_dir="./processed_data/"):
        """Save processed data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save profiles
        profiles_file = os.path.join(output_dir, "argo_profiles.csv")
        profiles_df.to_csv(profiles_file, index=False)
        
        # Save measurements
        measurements_file = os.path.join(output_dir, "argo_measurements.csv")
        measurements_df.to_csv(measurements_file, index=False)
        
        # Save processing summary
        summary = {
            'processing_date': datetime.now().isoformat(),
            'total_files': len(self.processed_files),
            'total_profiles': len(profiles_df),
            'total_measurements': len(measurements_df),
            'files_processed': self.processed_files
        }
        
        import json
        summary_file = os.path.join(output_dir, "processing_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\nData saved to {output_dir}")
        print(f"Profiles: {len(profiles_df)} records -> {profiles_file}")
        print(f"Measurements: {len(measurements_df)} records -> {measurements_file}")
        print(f"Summary: {summary_file}")
        
        return output_dir

def main():
    """Main processing function"""
    print("Starting NetCDF to PostgreSQL processing...")
    print("=" * 50)
    
    processor = NetCDFProcessor()
    
    # Process all files
    profiles_df, measurements_df = processor.process_all_files()
    
    if profiles_df.empty:
        print("No data processed. Check your NetCDF files.")
        return
    
    # Save to CSV
    output_dir = processor.save_to_csv(profiles_df, measurements_df)
    
    # Print summary
    print("\n" + "=" * 50)
    print("PROCESSING COMPLETE")
    print("=" * 50)
    print(f"Total profiles processed: {len(profiles_df)}")
    print(f"Total measurements processed: {len(measurements_df)}")
    print(f"Files processed: {len(processor.processed_files)}")
    
    print("\nProfile data sample:")
    print(profiles_df.head(3)[['global_profile_id', 'float_id', 'latitude', 'longitude', 'measurement_count']])
    
    print("\nMeasurement data sample:")
    print(measurements_df.head(3)[['global_profile_id', 'level', 'pressure_adjusted', 'temperature_adjusted', 'salinity_adjusted', 'pressure_adjusted_qc', 'temperature_adjusted_qc', 'salinity_adjusted_qc']])
    
    print(f"\nNext step: Import these CSV files into PostgreSQL")
    print(f"Files ready at: {output_dir}")

if __name__ == "__main__":
    main()