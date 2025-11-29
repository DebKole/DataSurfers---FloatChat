"""
Analysis Tools Wrapper for FloatChat
Provides unified interface between orchestrator and MCP analysis tools
Handles data normalization, validation, and error translation
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class AnalysisToolsWrapper:
    """Wrapper for MCP analysis tools with data normalization and validation"""
    
    def __init__(self):
        """Initialize wrapper and import MCP analysis tools"""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Import analysis tools from MCP server
            from float_chat_mcp.analysis_tools import server
            
            # Store references to tool functions
            self.temp_trend = server.argo_temp_trend.fn
            self.sal_trend = server.argo_salinity_trend.fn
            self.pressure_trend = server.argo_pressure_trend.fn
            self.ts_curve = server.argo_ts_curve.fn
            self.td_curve = server.argo_td_curve.fn
            self.comparison = server.argo_comparison_tool.fn
            self.statistics = server.argo_stat_summary.fn
            
            self.logger.info("✅ Analysis tools wrapper initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize analysis tools: {e}")
            raise
        
        # Column name mappings for normalization
        self.column_mappings = {
            # Uppercase mappings
            'TEMP': 'temperature',
            'SAL': 'salinity',
            'PRES': 'pressure',
            'DATETIME': 'datetime',
            'LEVEL': 'level',
            'DEPTH': 'depth',
            # Database-specific mappings (lowercase)
            'profile_datetime': 'datetime',
            'measurement_datetime': 'datetime',
            'profile_latitude': 'latitude',
            'profile_longitude': 'longitude'
        }
        
        # Minimum data requirements for each analysis type
        self.min_data_requirements = {
            'temp_trend': {'columns': ['datetime', 'temperature'], 'min_rows': 3},
            'sal_trend': {'columns': ['datetime', 'salinity'], 'min_rows': 3},
            'pressure_trend': {'columns': ['datetime', 'pressure'], 'min_rows': 3},
            'ts_curve': {'columns': ['temperature', 'salinity'], 'min_rows': 2},
            'td_curve': {'columns': ['temperature', 'level'], 'min_rows': 2},
            'comparison': {'columns': ['temperature'], 'min_rows': 1},  # Per dataset
            'statistics': {'columns': ['temperature', 'salinity', 'pressure'], 'min_rows': 1}
        }
    
    def execute_analysis(
        self,
        analysis_type: str,
        data: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute analysis on provided data
        
        Args:
            analysis_type: Type of analysis (temp_trend, sal_trend, ts_curve, etc.)
            data: List of measurement dictionaries
            parameters: Optional parameters (window, axis_var, labels, etc.)
        
        Returns:
            Analysis results or error dict
        """
        if parameters is None:
            parameters = {}
        
        self.logger.info(f"📊 Executing {analysis_type} analysis on {len(data)} data points")
        
        try:
            # Step 1: Normalize data
            normalized_data = self._normalize_data(data)
            
            # Step 2: Validate data
            is_valid, error_msg = self._validate_data(
                normalized_data,
                analysis_type
            )
            
            if not is_valid:
                return {
                    "status": "error",
                    "error": error_msg,
                    "analysis_type": analysis_type
                }
            
            # Step 3: Route to appropriate analysis tool
            result = self._route_to_tool(analysis_type, normalized_data, parameters)
            
            self.logger.info(f"✅ {analysis_type} analysis complete")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {str(e)}")
            return self._handle_error(e, analysis_type)
    
    def _normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize column names to lowercase and map alternatives
        
        Args:
            data: Raw data from database
            
        Returns:
            Normalized data with consistent column names
        """
        normalized = []
        
        for row in data:
            normalized_row = {}
            
            for key, value in row.items():
                # Start with lowercase version
                lower_key = key.lower()
                
                # Check mappings in order of priority:
                # 1. Exact match (case-sensitive)
                if key in self.column_mappings:
                    lower_key = self.column_mappings[key]
                # 2. Lowercase match
                elif lower_key in self.column_mappings:
                    lower_key = self.column_mappings[lower_key]
                # 3. Uppercase match
                elif key.upper() in self.column_mappings:
                    lower_key = self.column_mappings[key.upper()]
                
                normalized_row[lower_key] = value
            
            normalized.append(normalized_row)
        
        return normalized
    
    def _validate_data(
        self,
        data: List[Dict[str, Any]],
        analysis_type: str
    ) -> Tuple[bool, str]:
        """
        Validate data has required columns and minimum rows
        
        Args:
            data: Normalized data
            analysis_type: Type of analysis to validate for
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not data:
            return False, "No data available for analysis"
        
        # Get requirements for this analysis type
        requirements = self.min_data_requirements.get(analysis_type)
        
        if not requirements:
            return False, f"Unknown analysis type: {analysis_type}"
        
        # Check minimum rows
        if len(data) < requirements['min_rows']:
            return False, f"Insufficient data for {analysis_type} (minimum {requirements['min_rows']} points required, got {len(data)})"
        
        # Check required columns
        sample_row = data[0]
        missing_columns = []
        
        for required_col in requirements['columns']:
            if required_col not in sample_row:
                missing_columns.append(required_col)
        
        if missing_columns:
            return False, f"Missing required columns for {analysis_type}: {', '.join(missing_columns)}"
        
        return True, ""
    
    def _route_to_tool(
        self,
        analysis_type: str,
        data: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route to appropriate analysis tool based on type
        
        Args:
            analysis_type: Type of analysis
            data: Normalized and validated data
            parameters: Analysis parameters
            
        Returns:
            Analysis results
        """
        # Extract common parameters
        window = parameters.get('window', 20)
        axis_var = parameters.get('axis_var', None)
        labels = parameters.get('labels', [])
        datasets = parameters.get('datasets', [])
        
        # Route to appropriate tool
        if analysis_type == 'temp_trend':
            return self.temp_trend(data, show_plot=False, window=window)
        
        elif analysis_type == 'sal_trend':
            return self.sal_trend(data, show_plot=False, window=window)
        
        elif analysis_type == 'pressure_trend':
            return self.pressure_trend(data, show_plot=False, window=window)
        
        elif analysis_type == 'ts_curve':
            return self.ts_curve(data, show_plot=False)
        
        elif analysis_type == 'td_curve':
            return self.td_curve(data, show_plot=False)
        
        elif analysis_type == 'comparison':
            # Comparison requires multiple datasets
            if not datasets or len(datasets) < 2:
                return {
                    "status": "error",
                    "error": "Comparison requires at least 2 datasets"
                }
            
            # Determine variable to compare
            variable = parameters.get('variable', 'temperature')
            
            return self.comparison(
                datasets=datasets,
                labels=labels,
                variable=variable,
                axis_var=axis_var
            )
        
        elif analysis_type == 'statistics':
            return self.statistics(data)
        
        else:
            return {
                "status": "error",
                "error": f"Unknown analysis type: {analysis_type}"
            }
    
    def _handle_error(self, error: Exception, analysis_type: str) -> Dict[str, Any]:
        """
        Convert technical errors to user-friendly messages
        
        Args:
            error: Exception that occurred
            analysis_type: Type of analysis that failed
            
        Returns:
            Standardized error response
        """
        error_type = type(error).__name__
        
        # Define user-friendly error messages
        error_messages = {
            "temp_trend": {
                "ValueError": "Unable to generate temperature trend. Please ensure the data contains valid datetime and temperature values.",
                "KeyError": "Missing required data columns for temperature trend analysis.",
                "default": "Temperature trend analysis failed. Please try a different query."
            },
            "sal_trend": {
                "ValueError": "Unable to generate salinity trend. Please ensure the data contains valid datetime and salinity values.",
                "KeyError": "Missing required data columns for salinity trend analysis.",
                "default": "Salinity trend analysis failed. Please try a different query."
            },
            "pressure_trend": {
                "ValueError": "Unable to generate pressure trend. Please ensure the data contains valid datetime and pressure values.",
                "KeyError": "Missing required data columns for pressure trend analysis.",
                "default": "Pressure trend analysis failed. Please try a different query."
            },
            "ts_curve": {
                "ValueError": "Unable to generate T-S curve. Please ensure the data contains valid temperature and salinity values.",
                "KeyError": "Missing required columns 'temperature' and 'salinity' for T-S curve.",
                "default": "T-S curve generation failed."
            },
            "td_curve": {
                "ValueError": "Unable to generate T-D profile. Please ensure the data contains valid temperature and level/depth values.",
                "KeyError": "Missing required columns 'temperature' and 'level' for T-D profile.",
                "default": "T-D profile generation failed."
            },
            "comparison": {
                "ValueError": "Unable to compare datasets. Please ensure all datasets contain the comparison variable.",
                "default": "Dataset comparison failed."
            },
            "statistics": {
                "ValueError": "Unable to compute statistics. Please ensure the data contains valid numeric values.",
                "KeyError": "Missing required columns for statistical analysis.",
                "default": "Statistical analysis failed."
            }
        }
        
        # Get appropriate message
        messages = error_messages.get(analysis_type, {})
        user_message = messages.get(error_type, messages.get("default", str(error)))
        
        return {
            "status": "error",
            "error": user_message,
            "technical_error": str(error),
            "analysis_type": analysis_type
        }


# Test function
def test_analysis_wrapper():
    """Test the analysis tools wrapper"""
    print("🧪 Testing Analysis Tools Wrapper\n")
    
    wrapper = AnalysisToolsWrapper()
    
    # Test data
    test_data = [
        {"datetime": "2025-01-01T00:00:00", "temperature": 25.5, "salinity": 35.2, "pressure": 10.0, "level": 0},
        {"datetime": "2025-01-02T00:00:00", "temperature": 25.3, "salinity": 35.1, "pressure": 10.5, "level": 1},
        {"datetime": "2025-01-03T00:00:00", "temperature": 25.1, "salinity": 35.0, "pressure": 11.0, "level": 2},
    ]
    
    # Test 1: Temperature trend
    print("1. Testing temperature trend...")
    result = wrapper.execute_analysis("temp_trend", test_data)
    print(f"   Status: {result.get('status', 'unknown')}")
    if result.get('profiles'):
        print(f"   Measurements: {len(result['profiles'][0]['measurements'])}")
    
    # Test 2: T-S curve
    print("\n2. Testing T-S curve...")
    result = wrapper.execute_analysis("ts_curve", test_data)
    print(f"   Status: {result.get('status', 'unknown')}")
    
    # Test 3: Statistics
    print("\n3. Testing statistics...")
    result = wrapper.execute_analysis("statistics", test_data)
    print(f"   Status: {result.get('status', 'unknown')}")
    
    # Test 4: Insufficient data
    print("\n4. Testing error handling (insufficient data)...")
    result = wrapper.execute_analysis("temp_trend", [test_data[0]])
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Error: {result.get('error', 'N/A')}")
    
    print("\n✅ Analysis Tools Wrapper testing complete!")


if __name__ == "__main__":
    test_analysis_wrapper()
