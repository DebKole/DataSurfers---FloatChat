"""
Oceanographic feature computation using GSW (Gibbs SeaWater) library.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
import logging

try:
    import gsw
    GSW_AVAILABLE = True
except ImportError:
    GSW_AVAILABLE = False
    logging.warning("GSW library not available. Oceanographic features will be limited.")

logger = logging.getLogger(__name__)


class OceanographicFeatures:
    """Compute oceanographic features from T/S/P profiles."""
    
    @staticmethod
    def compute_density(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        latitude: float,
        longitude: float
    ) -> np.ndarray:
        """
        Compute potential density using GSW.
        
        Args:
            temperature: Temperature in °C
            salinity: Practical salinity (PSU)
            pressure: Pressure in dbar
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            
        Returns:
            Potential density (sigma0) in kg/m³
        """
        if not GSW_AVAILABLE:
            # Fallback: simple approximation
            return 1000 + 0.8 * salinity - 0.2 * temperature
        
        # Convert to absolute salinity
        SA = gsw.SA_from_SP(salinity, pressure, longitude, latitude)
        
        # Convert to conservative temperature
        CT = gsw.CT_from_t(SA, temperature, pressure)
        
        # Compute potential density referenced to 0 dbar
        sigma0 = gsw.sigma0(SA, CT)
        
        return sigma0
    
    @staticmethod
    def compute_spice(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        latitude: float,
        longitude: float
    ) -> np.ndarray:
        """
        Compute spice (orthogonal to density in T-S space).
        
        Args:
            temperature: Temperature in °C
            salinity: Practical salinity (PSU)
            pressure: Pressure in dbar
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            
        Returns:
            Spice in kg/m³
        """
        if not GSW_AVAILABLE:
            # Simple approximation
            return 0.5 * salinity - 0.1 * temperature
        
        SA = gsw.SA_from_SP(salinity, pressure, longitude, latitude)
        CT = gsw.CT_from_t(SA, temperature, pressure)
        
        # Spice at reference pressure 0
        spice = gsw.spiciness0(SA, CT)
        
        return spice
    
    @staticmethod
    def compute_mld(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        latitude: float,
        longitude: float,
        threshold: float = 0.03
    ) -> float:
        """
        Compute mixed layer depth using density threshold criterion.
        
        Args:
            temperature: Temperature profile
            salinity: Salinity profile
            pressure: Pressure profile
            latitude: Latitude
            longitude: Longitude
            threshold: Density difference threshold (kg/m³)
            
        Returns:
            Mixed layer depth in meters (pressure)
        """
        if len(pressure) < 2:
            return np.nan
        
        # Compute density
        density = OceanographicFeatures.compute_density(
            temperature, salinity, pressure, latitude, longitude
        )
        
        # Reference density at 10m (or shallowest available)
        ref_idx = np.argmin(np.abs(pressure - 10.0))
        ref_density = density[ref_idx]
        
        # Find where density exceeds threshold
        density_diff = np.abs(density - ref_density)
        mld_idx = np.where(density_diff > threshold)[0]
        
        if len(mld_idx) == 0:
            # MLD deeper than profile
            return pressure[-1]
        
        return pressure[mld_idx[0]]
    
    @staticmethod
    def compute_thermocline_depth(
        temperature: np.ndarray,
        pressure: np.ndarray
    ) -> float:
        """
        Compute thermocline depth as depth of maximum temperature gradient.
        
        Args:
            temperature: Temperature profile
            pressure: Pressure profile
            
        Returns:
            Thermocline depth in meters (pressure)
        """
        if len(pressure) < 3:
            return np.nan
        
        # Compute temperature gradient
        dT_dz = np.gradient(temperature, pressure)
        
        # Find maximum gradient (most negative)
        therm_idx = np.argmin(dT_dz)
        
        return pressure[therm_idx]
    
    @staticmethod
    def compute_buoyancy_frequency(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        latitude: float,
        longitude: float
    ) -> np.ndarray:
        """
        Compute buoyancy frequency (N²).
        
        Args:
            temperature: Temperature profile
            salinity: Salinity profile
            pressure: Pressure profile
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            N² in s⁻²
        """
        if not GSW_AVAILABLE or len(pressure) < 2:
            return np.full_like(pressure, np.nan)
        
        SA = gsw.SA_from_SP(salinity, pressure, longitude, latitude)
        CT = gsw.CT_from_t(SA, temperature, pressure)
        
        # Compute N²
        N2, p_mid = gsw.Nsquared(SA, CT, pressure, latitude)
        
        # Interpolate back to original pressure levels
        N2_interp = np.interp(pressure, p_mid, N2, left=np.nan, right=np.nan)
        
        return N2_interp
    
    @staticmethod
    def compute_vertical_gradients(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute vertical gradients of temperature and salinity.
        
        Args:
            temperature: Temperature profile
            salinity: Salinity profile
            pressure: Pressure profile
            
        Returns:
            Tuple of (dT/dz, dS/dz)
        """
        if len(pressure) < 2:
            return np.full_like(pressure, np.nan), np.full_like(pressure, np.nan)
        
        dT_dz = np.gradient(temperature, pressure)
        dS_dz = np.gradient(salinity, pressure)
        
        return dT_dz, dS_dz
    
    @staticmethod
    def interpolate_to_standard_depths(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        standard_depths: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Interpolate profiles to standard depth levels.
        
        Args:
            temperature: Temperature profile
            salinity: Salinity profile
            pressure: Pressure profile
            standard_depths: Target depth levels
            
        Returns:
            Tuple of (temp_interp, sal_interp, valid_mask)
        """
        # Use monotonic interpolation
        temp_interp = np.interp(
            standard_depths, pressure, temperature,
            left=np.nan, right=np.nan
        )
        
        sal_interp = np.interp(
            standard_depths, pressure, salinity,
            left=np.nan, right=np.nan
        )
        
        # Mask for valid interpolated values
        valid_mask = ~(np.isnan(temp_interp) | np.isnan(sal_interp))
        
        return temp_interp, sal_interp, valid_mask
    
    @staticmethod
    def extract_surface_values(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pressure: np.ndarray,
        target_depth: float = 0.0
    ) -> Tuple[float, float]:
        """
        Extract temperature and salinity at target depth.
        
        Args:
            temperature: Temperature profile
            salinity: Salinity profile
            pressure: Pressure profile
            target_depth: Target depth in dbar
            
        Returns:
            Tuple of (temperature, salinity) at target depth
        """
        if len(pressure) == 0:
            return np.nan, np.nan
        
        # Find closest depth
        idx = np.argmin(np.abs(pressure - target_depth))
        
        # If too far, interpolate
        if np.abs(pressure[idx] - target_depth) > 20.0:
            temp = np.interp(target_depth, pressure, temperature)
            sal = np.interp(target_depth, pressure, salinity)
        else:
            temp = temperature[idx]
            sal = salinity[idx]
        
        return temp, sal
