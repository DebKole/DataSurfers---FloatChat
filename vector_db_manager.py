"""
Vector Database Manager for FloatChat
Handles Chroma DB operations for Argo float profile data
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import json
from datetime import datetime
import logging

class FloatChatVectorDB:
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize Chroma DB for FloatChat profiles"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Collection names
        self.january_collection_name = "floatchat_january_profiles"
        self.live_collection_name = "floatchat_live_profiles"
        
        # Initialize collections
        self.january_collection = self._get_or_create_collection(self.january_collection_name)
        self.live_collection = self._get_or_create_collection(self.live_collection_name)
        
        self.logger = logging.getLogger(__name__)
    
    def _get_or_create_collection(self, collection_name: str):
        """Get or create a Chroma collection"""
        try:
            collection = self.client.get_collection(collection_name)
            print(f"✅ Connected to existing collection: {collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"FloatChat Argo profiles - {collection_name}"}
            )
            print(f"✅ Created new collection: {collection_name}")
        
        return collection
    
    def create_profile_document(self, profile_row: Dict[str, Any]) -> str:
        """Create a rich text document from profile data"""
        
        # Extract key information
        float_id = profile_row.get('float_id', 'unknown')
        institution = profile_row.get('institution', 'unknown')
        latitude = profile_row.get('latitude')
        longitude = profile_row.get('longitude')
        datetime_val = profile_row.get('datetime')
        min_pressure = profile_row.get('min_pressure', 0)
        max_pressure = profile_row.get('max_pressure', 0)
        measurement_count = profile_row.get('measurement_count', 0)
        cycle_number = profile_row.get('cycle_number')
        
        # Determine geographic region
        region = self._determine_region(latitude, longitude)
        
        # Determine season and year
        season, year = self._determine_season_year(datetime_val)
        
        # Create depth description
        depth_desc = self._create_depth_description(min_pressure, max_pressure)
        
        # Create rich document text
        document = f"""Argo float {float_id}"""
        
        if institution and institution != 'unknown':
            document += f" deployed by {institution}"
        
        if cycle_number:
            document += f" (cycle {cycle_number})"
        
        if season and year:
            document += f" in {season} {year}"
        
        if region:
            document += f" in the {region}"
        
        if latitude is not None and longitude is not None:
            document += f" at coordinates {latitude:.2f}°N, {longitude:.2f}°E"
        
        document += f". This oceanographic profile collected {measurement_count} measurements"
        
        if depth_desc:
            document += f" {depth_desc}"
        
        document += ". The deployment provides valuable oceanographic data for climate monitoring and marine research"
        
        if region:
            document += f" in the {region} region"
        
        document += "."
        
        return document
    
    def _determine_region(self, lat: float, lng: float) -> str:
        """Determine ocean region from coordinates"""
        if lat is None or lng is None or pd.isna(lat) or pd.isna(lng):
            return "unknown region"
        
        # Indian Ocean regions
        if 20 <= lng <= 120:
            if 0 <= lat <= 30:
                if 50 <= lng <= 80:
                    return "Arabian Sea"
                elif 80 <= lng <= 100:
                    return "Bay of Bengal"
                else:
                    return "Northern Indian Ocean"
            elif -40 <= lat < 0:
                return "Southern Indian Ocean"
            elif lat > 30:
                return "Northern Indian Ocean"
        
        # Pacific Ocean
        elif lng > 120 or lng < -80:
            if lat > 0:
                return "North Pacific Ocean"
            else:
                return "South Pacific Ocean"
        
        # Atlantic Ocean
        elif -80 <= lng < 20:
            if lat > 0:
                return "North Atlantic Ocean"
            else:
                return "South Atlantic Ocean"
        
        return "Indian Ocean"
    
    def _determine_season_year(self, datetime_val) -> tuple:
        """Determine season and year from datetime"""
        if datetime_val is None:
            return None, None
        
        try:
            if isinstance(datetime_val, str):
                dt = pd.to_datetime(datetime_val)
            else:
                dt = datetime_val
            
            year = dt.year
            month = dt.month
            
            # Determine season (Northern Hemisphere)
            if month in [12, 1, 2]:
                season = "winter"
            elif month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            elif month in [9, 10, 11]:
                season = "autumn"
            else:
                season = None
            
            return season, year
            
        except Exception:
            return None, None
    
    def _create_depth_description(self, min_pressure: float, max_pressure: float) -> str:
        """Create depth description from pressure values"""
        if min_pressure is None or max_pressure is None or pd.isna(min_pressure) or pd.isna(max_pressure):
            return ""
        
        try:
            max_depth = int(float(max_pressure))  # Pressure ≈ depth in meters
        except (ValueError, TypeError):
            return ""
        
        if max_depth < 100:
            return f"down to {max_depth}m depth, focusing on surface waters"
        elif max_depth < 500:
            return f"down to {max_depth}m depth, capturing upper ocean structure"
        elif max_depth < 1000:
            return f"down to {max_depth}m depth, reaching intermediate waters"
        elif max_depth < 2000:
            return f"down to {max_depth}m depth, sampling deep ocean layers"
        else:
            return f"down to {max_depth}m depth, providing full-depth ocean profiling"
    
    def create_profile_metadata(self, profile_row: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for vector search filtering"""
        latitude = profile_row.get('latitude')
        longitude = profile_row.get('longitude')
        datetime_val = profile_row.get('datetime')
        
        # Helper function to safely convert to int, handling NaN
        def safe_int(value, default=0):
            if pd.isna(value) or value is None:
                return default
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default
        
        # Helper function to safely convert to float, handling NaN
        def safe_float(value):
            if pd.isna(value) or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        metadata = {
            'global_profile_id': str(profile_row.get('global_profile_id', '')),
            'float_id': str(profile_row.get('float_id', 'unknown')),
            'institution': str(profile_row.get('institution', 'unknown')),
            'cycle_number': str(profile_row.get('cycle_number', '')),
            'measurement_count': safe_int(profile_row.get('measurement_count'), 0),
            'region': self._determine_region(latitude, longitude)
        }
        
        # Add coordinates if available and not NaN
        lat_safe = safe_float(latitude)
        lng_safe = safe_float(longitude)
        if lat_safe is not None:
            metadata['latitude'] = lat_safe
        if lng_safe is not None:
            metadata['longitude'] = lng_safe
        
        # Add temporal information
        season, year = self._determine_season_year(datetime_val)
        if season:
            metadata['season'] = season
        if year:
            metadata['year'] = safe_int(year, 0)
        
        # Add depth categories
        max_pressure = safe_float(profile_row.get('max_pressure'))
        if max_pressure and max_pressure > 0:
            if max_pressure < 100:
                metadata['depth_category'] = 'surface'
            elif max_pressure < 500:
                metadata['depth_category'] = 'shallow'
            elif max_pressure < 1000:
                metadata['depth_category'] = 'intermediate'
            else:
                metadata['depth_category'] = 'deep'
        
        return metadata
    
    def add_profiles_to_collection(self, profiles_df: pd.DataFrame, collection_name: str = "live") -> int:
        """Add profiles to specified collection"""
        
        collection = self.live_collection if collection_name == "live" else self.january_collection
        
        documents = []
        metadatas = []
        ids = []
        
        for _, profile_row in profiles_df.iterrows():
            # Create document and metadata
            document = self.create_profile_document(profile_row.to_dict())
            metadata = self.create_profile_metadata(profile_row.to_dict())
            profile_id = f"profile_{profile_row['global_profile_id']}"
            
            documents.append(document)
            metadatas.append(metadata)
            ids.append(profile_id)
        
        # Add to collection
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(documents)} profiles to {collection_name} vector collection")
            return len(documents)
            
        except Exception as e:
            print(f"❌ Error adding profiles to vector DB: {e}")
            return 0
    
    def search_profiles(self, query: str, collection_name: str = "live", n_results: int = 10, 
                       filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search profiles using semantic similarity"""
        
        collection = self.live_collection if collection_name == "live" else self.january_collection
        
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        where_clause[key] = value
            
            # Perform search
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching vector DB: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about both collections"""
        try:
            january_count = self.january_collection.count()
            live_count = self.live_collection.count()
            
            return {
                'january_profiles': january_count,
                'live_profiles': live_count,
                'total_profiles': january_count + live_count,
                'collections': {
                    'january': self.january_collection_name,
                    'live': self.live_collection_name
                }
            }
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self, collection_name: str):
        """Clear all data from a collection"""
        try:
            if collection_name == "live":
                self.client.delete_collection(self.live_collection_name)
                self.live_collection = self._get_or_create_collection(self.live_collection_name)
            elif collection_name == "january":
                self.client.delete_collection(self.january_collection_name)
                self.january_collection = self._get_or_create_collection(self.january_collection_name)
            
            print(f"✅ Cleared {collection_name} collection")
            
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")

def test_vector_db():
    """Test the vector database functionality"""
    print("🧪 Testing FloatChat Vector Database...")
    
    # Initialize
    vector_db = FloatChatVectorDB()
    
    # Get stats
    stats = vector_db.get_collection_stats()
    print(f"📊 Collection Stats: {stats}")
    
    # Test search (if data exists)
    if stats.get('total_profiles', 0) > 0:
        results = vector_db.search_profiles("INCOIS floats in Arabian Sea", "january", 3)
        print(f"🔍 Search Results: Found {len(results)} matches")
        for result in results[:2]:
            print(f"  - {result['document'][:100]}...")

if __name__ == "__main__":
    test_vector_db()