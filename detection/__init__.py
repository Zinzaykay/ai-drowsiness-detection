"""
Package detection chứa các module xử lý Camera, Face Detection và Feature Extraction.
"""

from .camera import Camera
from .face_detector import Face_Detector
from .feature_extractor import Ear

__all__ = [
    "Camera",
    "Face_Detector",
    "Ear",
]
