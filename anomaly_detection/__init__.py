"""
Argo Ocean Data Anomaly Detection System

A geographically-aware anomaly detection system for Argo float ocean profile data.
"""

__version__ = "0.1.0"
__author__ = "Argo Anomaly Detection Team"

from . import data
from . import features
from . import clustering
from . import geo
from . import models
from . import anomaly

__all__ = [
    "data",
    "features",
    "clustering",
    "geo",
    "models",
    "anomaly",
]
