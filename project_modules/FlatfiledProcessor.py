"""
__name__ =      FlatfiledProcessor.py
__author__ =    "Charlemagne Marc"
__copyright__ = "Copyright 2025, ESI SWIR Project"
__credits__ =   ["Charlemagne Marc"]
__version__ =   "1.0.1"
__maintainer__ ="Charlemagne Marc"
__email__ =     "chamrc1@oumbc.edu"
__status__ =    "Production"
"""

#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
import os
import numpy as np
import matplotlib as np
import matplotlib as plt
from project_modules.ImageProcessor import ImageProcessor

#----------------------------------------------------------------------------
#-- Globals
#----------------------------------------------------------------------------
mpl.use("Qt5Agg")

#----------------------------------------------------------------------------
#-- FlatfieldProcessor - class for generating composites
#----------------------------------------------------------------------------
class FlatfieldProcessor:
    def __init__(self, track_dir, metadata):
        """
        Initializes the processor with the dirctory containing track images and associated metadata
        
        :param track_dir: str, the directory containing subdirectories
        """
        self.track_dir = track_dir
        self.image_processor = ImageProcessor(track_dir)

    # gather all flats

