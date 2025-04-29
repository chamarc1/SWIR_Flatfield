#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
import os                             # Needed for locating images/files
import numpy as np                    # Images converted to NumPy arrays for data manipulation
import matplotlib as mpl              # Needed for plotting
import matplotlib.pyplot as plt       # Needed for plotting
from PIL import Image                 # Needed for opening images

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
BIT_SHIFT = 2**14 
mpl.use("Qt5Agg")

#----------------------------------------------------------------------------
#-- ImageProcessor - class for opening images
#----------------------------------------------------------------------------
class ImageProcessor:
    def __init__(self, base_directory):
        """
        Initializes the processor with a list of images from the specified directory.

        :param base_directory: str, path to the base directory containing subdirectories of images
        """
        self.base_directory = base_directory
        self.image_data = self.load_images()  # Load images on initialization

    def is_valid_directory(self, path):
        """
        Check if a given path is a valid directory.

        :param path: str, path to check for validity
        :return: bool, True if path is a valid directory, False otherwise
        """
        return os.path.isdir(path)
    
    def process_image(self, image_path):
        """
        Process an individual image: Apply SWIR correction by converting it into a NumPy array 
        and performing a bit shift operation.

        :param image_path: str, path to the image file to process
        :return: np.ndarray or None, processed image as a NumPy array or None if an error occurs
        """
        try:
            return BIT_SHIFT - np.asarray(Image.open(image_path))
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None
        
    def load_images_from_directory(self, degree_path):
        """
        Load images from a specific degree directory, process them, and store them.

        :param degree_path: str, path to the directory containing images for a specific degree position
        :return: list of np.ndarray, list of processed images as NumPy arrays
        """
        images = []
        for filename in os.listdir(degree_path):
            if filename.lower().endswith((".tif", ".tiff")):
                image_path = os.path.join(degree_path, filename)
                processed_image = self.process_image(image_path)
                if processed_image is not None:
                    images.append(processed_image)
        return images
    
    def load_filter_data(self, filter_path):
        """
        Load degree positions and images for a specific filter position.

        :param filter_path: str, path to the filter position directory
        :return: dict, dictionary mapping degree positions to their corresponding processed images
        """
        filter_data = {}
        for degree_pos in os.listdir(filter_path):
            degree_path = os.path.join(filter_path, degree_pos)
            if self.is_valid_directory(degree_path):
                filter_data[degree_pos] = self.load_images_from_directory(degree_path)
        return filter_data
    
    def load_images(self):
        """
        Load all images from the base directory, processing them by filter and degree position.

        :return: dict, dictionary mapping filter positions to dictionaries of degree positions and their corresponding images
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
        Display all images for a given filter and degree position in a grid.

        :param filter_pos: str, filter position to display images for
        :param degree_pos: str, degree position to display images for
        """
        images = self.get_images(filter_pos, degree_pos)
        if not images:
            print(f"No images found for {filter_pos} at {degree_pos}")
            return
        
        fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 5))
        if len(images) == 1:
            axes = [axes]  # Ensure iterable
        for ax, image in zip(axes, images):
            ax.imshow(image)
            ax.axis("off")
        plt.show()

    def get_images(self, filter_pos, degree_pos):
        """
        Return a list of images for the specified filter and degree position.

        :param filter_pos: str, filter position to get images for
        :param degree_pos: str, degree position to get images for
        :return: list of np.ndarray, list of images for the given filter and degree position, 
                or an empty list if no data is found
        """
        if filter_pos not in self.image_data or degree_pos not in self.image_data[filter_pos]:
            print(f"No data found for filter position: {filter_pos} or degree position: {degree_pos}")
            return []
        return self.image_data[filter_pos][degree_pos]
