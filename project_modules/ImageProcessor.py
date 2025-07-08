"""
__name__ =      ImageProcessor.py
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
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
BIT_SHIFT = 2**14
mpl.use("Qt5Agg")

#----------------------------------------------------------------------------
#-- ImageProcessor - class for opening images
#----------------------------------------------------------------------------
class ImageProcessor:
    def __init__(self, base_directory, metadata_csv=None):
        """
        Initializes the ImageProcessor with the base directory and loads all images.
        Optionally loads TEC metadata if a CSV is provided.
        :param base_directory: str, path to the base directory containing image data.
        :param metadata_csv: str, path to the CSV file with metadata.
        """
        self.base_directory = base_directory
        self.tec_map = {}
        if metadata_csv:
            df = pd.read_csv(metadata_csv)
            self.tec_map = dict(zip(df['FILEPATH'], df['TEC_READING(CELCIUS)']))
        self.image_data = self.load_images()

    def is_valid_directory(self, path):
        """Returns True if the path is a valid directory."""
        return os.path.isdir(path)

    def process_image(self, image_path):
        """
        Loads an image, converts to NumPy array, and applies bit shift correction.
        :param image_path: str, full path to the image file.
        :return: dict with processed image and TEC value or None if loading fails.
        """
        try:
            image = Image.open(image_path)
            numpy_array = np.asarray(image)
            processed_array = BIT_SHIFT - numpy_array
            tec_value = self.tec_map.get(image_path)
            return {"image": processed_array, "tec": tec_value}
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None

    def load_images_from_directory(self, degree_path):
        """
        Loads and processes all TIFF images in a directory.
        :param degree_path: str, path to directory with images for a degree position.
        :return: list of dicts with processed images and TEC values
        """
        images = []
        for filename in os.listdir(degree_path):
            if filename.lower().endswith((".tif", ".tiff")):
                image_path = os.path.join(degree_path, filename)
                processed = self.process_image(image_path)
                if processed is not None:
                    images.append(processed)
        return images

    def load_filter_data(self, filter_path):
        """
        Loads image data for a filter position, organized by degree position.
        :param filter_path: str, path to filter directory.
        :return: dict mapping degree position to list of images.
        """
        filter_data = {}
        for degree_pos in os.listdir(filter_path):
            degree_path = os.path.join(filter_path, degree_pos)
            if self.is_valid_directory(degree_path):
                filter_data[degree_pos] = self.load_images_from_directory(degree_path)
        return filter_data

    def load_images(self):
        """
        Loads all images from the base directory, organized by filter and degree position.
        :return: nested dict: filter position -> degree position -> list of images
        """
        image_data = {}
        if not self.is_valid_directory(self.base_directory):
            print(f"Error: Directory not found at {self.base_directory}")
            return image_data

        for filter_pos in os.listdir(self.base_directory):
            filter_path = os.path.join(self.base_directory, filter_pos)
            if self.is_valid_directory(filter_path):
                image_data[filter_pos] = self.load_filter_data(filter_path)
        return image_data

    def show_images(self, filter_pos, degree_pos):
        """
        Displays all images for a given filter and degree position.
        :param filter_pos: str
        :param degree_pos: str
        """
        images = self.get_images(filter_pos, degree_pos)
        if not images:
            print(f"No images found for {filter_pos} at {degree_pos}")
            return

        num_images = len(images)
        fig, axes = plt.subplots(1, num_images, figsize=(5 * num_images, 5))
        if num_images == 1:
            axes = [axes]
        for ax, image in zip(axes, images):
            ax.imshow(image)
            ax.axis("off")
        plt.show()

    def get_images(self, filter_pos, degree_pos):
        """
        Returns list of images for a specific filter and degree position.
        :param filter_pos: str
        :param degree_pos: str
        :return: list of np.ndarray
        """
        if filter_pos not in self.image_data or degree_pos not in self.image_data[filter_pos]:
            print(f"No data found for filter position: {filter_pos} or degree position: {degree_pos}")
            return []
        return self.image_data[filter_pos][degree_pos]