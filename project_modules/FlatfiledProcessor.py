"""
FlatfiledProcessor.py
Author: Charlemagne Marc
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

