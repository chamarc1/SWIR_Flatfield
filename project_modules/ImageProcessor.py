"""
ImageProcessor.py
Author: Charlemagne Marc
"""

#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
import os                             # Provides functions for interacting with the operating system, such as file path manipulation and directory listing.
import numpy as np                    # A fundamental library for numerical computation in Python, essential for working with multi-dimensional arrays representing images.
import matplotlib as mpl              # A comprehensive library for creating static, interactive, and animated visualizations in Python. Used here to set the backend for plotting.
import matplotlib.pyplot as plt       # A module within Matplotlib that provides a MATLAB-like interface for plotting. Used for displaying images.
from PIL import Image                 # The Python Imaging Library (PIL), used here for opening and manipulating image files.

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
BIT_SHIFT = 2**14                     # A constant defining a bit shift value (2 raised to the power of 14). This is likely used for a specific image correction or data scaling operation, possibly related to the dynamic range of the sensor.
mpl.use("Qt5Agg")                     # Sets the Matplotlib backend to Qt5Agg, which is an interactive backend using the Qt 5 framework. This allows for displaying plots in a separate window.

#----------------------------------------------------------------------------
#-- ImageProcessor - class for opening images
#----------------------------------------------------------------------------
class ImageProcessor:
    def __init__(self, base_directory):
        """
        Initializes the ImageProcessor object with the base directory containing image data.

        The constructor takes the path to the base directory as input and immediately calls
        the `load_images` method to populate the `image_data` attribute upon object creation.

        :param base_directory: str, path to the base directory. It is expected that this directory
                                 contains subdirectories organized by filter positions, which in turn
                                 contain subdirectories organized by degree positions, and finally the
                                 image files within the degree position directories.
        """
        self.base_directory = base_directory
        self.image_data = self.load_images()

    def is_valid_directory(self, path):
        """
        Checks if the given path exists and is a valid directory.

        :param path: str, the path to be checked.
        :return: bool, True if the path is a valid directory, False otherwise.
        """
        return os.path.isdir(path)

    def process_image(self, image_path):
        """
        Processes a single image file. Currently, the processing involves opening the image using PIL,
        converting it to a NumPy array, and then applying a bit shift correction by subtracting the
        array from the `BIT_SHIFT` global constant. This operation is likely specific to the type
        of image data being processed (e.g., SWIR imagery).

        :param image_path: str, the full path to the image file to be processed.
        :return: np.ndarray or None, the processed image as a NumPy array. Returns None if an error
                                  occurs during image loading.
        """
        try:
            image = Image.open(image_path)
            numpy_array = np.asarray(image)
            processed_array = BIT_SHIFT - numpy_array  # Applies the bit shift correction by subtracting the NumPy array from the global BIT_SHIFT value.
            return processed_array
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None

    def load_images_from_directory(self, degree_path):
        """
        Loads and processes all TIFF (.tif or .tiff) image files found within a specified degree directory.

        It iterates through the files in the given directory, checks if they are TIFF images (case-insensitive),
        constructs the full path to each image, calls the `process_image` method to process it, and appends
        the processed image (as a NumPy array) to a list.

        :param degree_path: str, the path to the directory containing image files for a specific degree position.
        :return: list of np.ndarray, a list containing the processed images as NumPy arrays.
        """
        images = []
        for filename in os.listdir(degree_path):  # Iterates through each item (files and subdirectories) within the specified degree directory.
            if filename.lower().endswith((".tif", ".tiff")):  # Checks if the filename (converted to lowercase) ends with either ".tif" or ".tiff", indicating it's a TIFF image.
                image_path = os.path.join(degree_path, filename)  # Creates the full path to the image file by joining the degree path and the filename.
                processed_image = self.process_image(image_path)  # Calls the process_image method to load and apply the bit shift correction to the current image.
                if processed_image is not None:  # Checks if the image was processed successfully (i.e., no error occurred during loading).
                    images.append(processed_image)  # If processing was successful, the resulting NumPy array is added to the list of images.
        return images

    def load_filter_data(self, filter_path):
        """
        Loads image data for a specific filter position. It iterates through the subdirectories within the filter directory,
        assumes each subdirectory represents a degree position, and then calls `load_images_from_directory` to get the
        processed images for that degree position. The results are stored in a dictionary where keys are degree positions
        and values are lists of processed images for that degree.

        :param filter_path: str, the path to the directory containing subdirectories for different degree positions under a specific filter.
        :return: dict, a dictionary where keys are degree position directory names (str) and values are lists of
                      corresponding processed images (list of np.ndarray).
        """
        filter_data = {}  # Initializes an empty dictionary to store the image data for the current filter.
        for degree_pos in os.listdir(filter_path):  # Iterates through each item (subdirectories) within the specified filter directory. It's assumed these are degree position directories.
            degree_path = os.path.join(filter_path, degree_pos)  # Creates the full path to the degree position directory.
            if self.is_valid_directory(degree_path):  # Checks if the constructed path is a valid directory.
                filter_data[degree_pos] = self.load_images_from_directory(degree_path)  # If it's a valid directory, it calls load_images_from_directory to get the processed images for this degree position and stores the list of images in the filter_data dictionary with the degree position as the key.
        return filter_data  # Returns the dictionary containing degree positions and their corresponding processed images for the current filter.

    def load_images(self):
        """
        Loads all images from the base directory. It assumes the base directory is organized into subdirectories
        representing different filter positions. For each filter directory, it calls `load_filter_data` to load
        the images organized by degree positions. The final result is a nested dictionary where the outer keys are
        filter positions and the inner keys are degree positions, with values being lists of processed images.

        :return: dict, a nested dictionary where the outer keys are filter position directory names (str),
                      the inner keys are degree position directory names (str), and the values are lists of
                      corresponding processed images (list of np.ndarray).
        """
        image_data = {}
        if not self.is_valid_directory(self.base_directory):
            print(f"Error: Directory not found at {self.base_directory}")
            return image_data

        for filter_pos in os.listdir(self.base_directory):  # Iterates through each item (subdirectories) within the base directory. It's assumed these are filter position directories.
            filter_path = os.path.join(self.base_directory, filter_pos)  # Creates the full path to the filter position directory.
            if self.is_valid_directory(filter_path):  # Checks if the constructed path is a valid directory.
                image_data[filter_pos] = self.load_filter_data(filter_path)  # If it's a valid directory, it calls load_filter_data to get the processed images for this filter position (organized by degree) and stores the resulting dictionary in the image_data dictionary with the filter position as the key.
        return image_data

    def show_images(self, filter_pos, degree_pos):
        """
        Displays all processed images for a given filter and degree position in a single Matplotlib figure.
        If multiple images exist for the specified filter and degree, they are displayed in a horizontal grid.

        :param filter_pos: str, the name of the filter position directory.
        :param degree_pos: str, the name of the degree position directory.
        """
        images = self.get_images(filter_pos, degree_pos)  # Retrieves the list of processed images for the specified filter and degree.
        if not images:
            print(f"No images found for {filter_pos} at {degree_pos}")
            return  # Exits the function if no images are found.

        num_images = len(images)  # Gets the number of images to be displayed.
        fig, axes = plt.subplots(1, num_images, figsize=(5 * num_images, 5))  # Creates a Matplotlib figure and a set of subplots in a 1xN grid, where N is the number of images. The figsize is adjusted based on the number of images to provide reasonable spacing.
        if num_images == 1:
            axes = [axes]  # If there's only one image, the 'axes' object is not a list, so we wrap it in a list to allow consistent iteration.
        for ax, image in zip(axes, images):
            ax.imshow(image)
            ax.axis("off")
        plt.show()

    def get_images(self, filter_pos, degree_pos):
        """
        Retrieves the list of processed images for a specific filter and degree position from the stored `image_data`.

        :param filter_pos: str, the name of the filter position directory.
        :param degree_pos: str, the name of the degree position directory.
        :return: list of np.ndarray, a list of processed images for the given filter and degree position.
                Returns an empty list if no data is found for the specified filter or degree.
        """
        if filter_pos not in self.image_data or degree_pos not in self.image_data[filter_pos]:
            print(f"No data found for filter position: {filter_pos} or degree position: {degree_pos}")
            return []
        return self.image_data[filter_pos][degree_pos]  # If the filter and degree positions exist in the data, it returns the list of processed images associated with that filter and degree.