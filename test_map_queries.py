#!/usr/bin/env python3
"""
Test script for map visualization queries.
"""

from data_processor import ArgoDataProcessor
from query_interpreter import QueryInterpreter
from map_data_provider import MapDataProvider

def test_map_queries():
    """Test map-related queries."""
    
    print("🗺️ Testing Map Visualization System\n")
    
    # Initialize components
    processor = ArgoDataProcessor("argo_demo.csv")
    interpreter = QueryInterpreter(processor)
    
    # Test map queries
    map_queries = [
        "Show me a map of temperature distribution",
        "Display temperature heatmap",
        "Where is the temperature highest?",
        "Show salinity map",
        "Visualize temperature in the Indian Ocean",
        "Map view of surface conditions",
        "Plot temperature data on map",
        "Show me the ocean temperature map"
    ]
    
    for i, query in enumerate(map_queries, 1):
        print(f"{'='*60}")
        print(f"Map Test {i}: {query}")
        print(f"{'='*60}")
        
        result = interpreter.interpret_query(query)
        print(f"Query Type: {result['query_type']}")
        print(f"Show Map: {result.get('show_map', False)}")
        
        if result.get('show_map'):
            map_data = result.get('map_data', [])
            parameter = result.get('map_parameter', 'unknown')
            region = result.get('map_region', 'current location')
            
            print(f"Map Parameter: {parameter}")
            print(f"Map Region: {region}")
            print(f"Data Points: {len(map_data)}")
            
            if map_data:
                print("Sample Data Points:")
                for j, point in enumerate(map_data[:3]):  # Show first 3 points
                    print(f"  Point {j+1}: Lat {point['lat']:.4f}, Lng {point['lng']:.4f}, Value {point['value']}")
        
        print(f"Response:\n{result['response']}")
        print()

if __name__ == "__main__":
    test_map_queries()