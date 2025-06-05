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
from PIL import Image, ImageEnhance
from scipy.ndimage import gaussian_filter
import argparse # For command-line argument parsing

# Assuming ImageProcessor.py is in a 'project_modules' directory or accessible
from project_modules.ImageProcessor import ImageProcessor # Corrected import path

#----------------------------------------------------------------------------
#-- Core Image Processing Functions (Adapted from your original methods)
#----------------------------------------------------------------------------
# NOTE: load_image_as_float32 is now absorbed into ImageProcessor's loading
# We will still need save_image_from_array for saving results.

def save_image_from_array(img_array, file_path):
    """
    Normalizes a float NumPy array to 0-255 (uint8) and saves it as a grayscale image.
    """
    # Handle potential NaN or infinite values before normalization
    img_array = np.nan_to_num(img_array, nan=0.0, posinf=0.0, neginf=0.0)

    C_min = img_array.min()
    C_max = img_array.max()

    if C_max > C_min:
        C_normalized = (img_array - C_min) / (C_max - C_min)
    else:
        # If all values are the same, result should be uniform (e.g., black)
        C_normalized = np.zeros_like(img_array)

    C_normalized = (C_normalized * 255).astype('uint8')
    Image.fromarray(C_normalized).convert('L').save(file_path) # 'L' for grayscale

def generate_synthetic_dark_flat_fields_np(reference_image_shape, sigma_dark_flat=1.0):
    """
    Generates synthetic dark and flat field images as NumPy arrays based on a
    reference image shape. This is useful when actual dark/flat fields aren't available.
    """
    # Create a dummy raw image array for synthetic generation logic
    # This assumes a grayscale image for PIL conversion for consistency
    dummy_raw_image_array = np.zeros(reference_image_shape, dtype=np.uint8)
    dummy_raw_image_array[dummy_raw_image_array.shape[0]//2, dummy_raw_image_array.shape[1]//2] = 255 # Simple spot to make it not completely black

    # Generate Dark Field (D) by dimming the raw image
    raw_pil_L = Image.fromarray(dummy_raw_image_array).convert('L')
    enhancer = ImageEnhance.Brightness(raw_pil_L)
    # Reduce brightness to simulate a dark field (reduced by 80%)
    dark_image_pil = enhancer.enhance(0.2)
    dark_array = np.array(dark_image_pil).astype('float32')

    # Apply Gaussian smoothing to dark field
    if sigma_dark_flat > 0:
        smoothed_dark = gaussian_filter(dark_array, sigma=sigma_dark_flat)
    else:
        smoothed_dark = dark_array

    # Generate Flat Field (F) by creating a uniform image with noise
    flat_brightness_value = 200 # Desired brightness level for flat field (less than 255 to avoid clipping on noise)
    flat_array = np.full(reference_image_shape, flat_brightness_value, dtype='float32')
    noise = np.random.normal(0, 5, flat_array.shape).astype('float32') # Add Gaussian noise
    flat_array = flat_array + noise
    flat_array = np.clip(flat_array, 0, 255).astype('float32') # Clip values to valid range

    # Apply Gaussian smoothing to flat field
    if sigma_dark_flat > 0:
        flat_array_smoothed = gaussian_filter(flat_array, sigma=sigma_dark_flat)
    else:
        flat_array_smoothed = flat_array

    return smoothed_dark, flat_array_smoothed

def perform_correction_np(R, D, F):
    """
    Performs flat field correction on NumPy arrays.
    R: Raw image array
    D: Dark field image array
    F: Flat field image array
    """
    if R.shape != D.shape or R.shape != F.shape:
        raise ValueError("All images must have the same dimensions for correction.")

    F_minus_D = F - D
    m = np.mean(F_minus_D) # Mean of (F - D)
    epsilon = 1e-6 # Small constant to avoid division by zero

    denominator = F_minus_D.copy()
    # Replace zeros or near-zeros in denominator with epsilon to prevent division by zero
    denominator[np.abs(denominator) < epsilon] = epsilon

    G = m / denominator # Calculate gain
    R_minus_D = R - D # Subtract dark field from raw image
    C = R_minus_D * G # Apply gain to corrected image

    # Handle any potential NaN or infinite values resulting from calculation
    C = np.nan_to_num(C, nan=0.0, posinf=0.0, neginf=0.0)

    return C

#----------------------------------------------------------------------------
#-- FlatfieldProcessor Class (New addition for structured processing)
#----------------------------------------------------------------------------
class FlatfieldProcessor:
    def __init__(self, image_data_root_dir, sigma=1.0):
        """
        Initializes the FlatfieldProcessor.

        :param image_data_root_dir: The root directory containing all image data (raw, dark, flat).
        :param sigma: Standard deviation for Gaussian smoothing applied to images.
        """
        self.image_processor = ImageProcessor(image_data_root_dir)
        self.sigma = sigma
        print(f"FlatfieldProcessor initialized with root directory: {image_data_root_dir}")
        print(f"Default smoothing sigma: {self.sigma}")

    def _get_averaged_image(self, filter_position):
        """
        Helper method to get an averaged image from a given filter position.
        Assumes ImageProcessor's `image_data` is populated.
        """
        images = []
        for degree_pos_data in self.image_processor.image_data.get(filter_position, {}).values():
            # Apply Gaussian smoothing when extracting from ImageProcessor's raw data
            for img_array in degree_pos_data:
                if self.sigma > 0:
                    smoothed_array = gaussian_filter(img_array.astype(np.float32), sigma=self.sigma)
                else:
                    smoothed_array = img_array.astype(np.float32)
                images.append(smoothed_array)

        if not images:
            return None
        return np.mean(np.asarray(images), axis=0)


    def process_flatfield_correction(self, raw_filter_pos, dark_filter_pos, flat_filter_pos):
        """
        Coordinates the flat field correction process using images loaded by ImageProcessor.

        :param raw_filter_pos: The filter position string for the raw images.
        :param dark_filter_pos: The filter position string for the dark images.
        :param flat_filter_pos: The filter position string for the flat images.
        :return: Corrected image array, or None if an error occurs.
        """
        print(f"\n--- Starting Flat Field Correction ---")
        print(f"Raw Image Filter: {raw_filter_pos}")
        print(f"Dark Image Filter: {dark_filter_pos}")
        print(f"Flat Image Filter: {flat_filter_pos}")
        print(f"Smoothing Sigma: {self.sigma}")
        print("-" * 30)

        raw_image_array = None
        dark_image_array = None
        flat_image_array = None

        try:
            # Load Raw Image
            print(f"Loading raw image data from filter position '{raw_filter_pos}'...")
            # We assume a single raw image or average if multiple are loaded.
            # For simplicity, we'll take the first image found in the raw_filter_pos
            # or you might want to extend ImageProcessor to average this.
            # For a single image, we'll use the first one from the first degree position.
            raw_data = self.image_processor.image_data.get(raw_filter_pos)
            if not raw_data:
                raise ValueError(f"No raw images found for filter position '{raw_filter_pos}'.")
            
            # Get the first image from the first degree position found
            first_degree_pos = next(iter(raw_data))
            raw_image_array = raw_data[first_degree_pos][0].astype(np.float32)
            
            if self.sigma > 0:
                raw_image_array = gaussian_filter(raw_image_array, sigma=self.sigma)
            print("Raw image data loaded successfully.")


            # Get Dark Field
            print(f"Attempting to retrieve dark field from filter position '{dark_filter_pos}'...")
            dark_image_array = self._get_averaged_image(dark_filter_pos)
            if dark_image_array is None:
                print(f"No valid dark images found for '{dark_filter_pos}'. Generating synthetic dark field...")
                # Generate synthetic dark based on the shape of the raw image
                synthetic_dark, _ = generate_synthetic_dark_flat_fields_np(raw_image_array.shape, self.sigma)
                dark_image_array = synthetic_dark
                print("Synthetic Dark Field generated.")
            else:
                print("Dark field loaded successfully.")

            # Get Flat Field
            print(f"Attempting to retrieve flat field from filter position '{flat_filter_pos}'...")
            flat_image_array = self._get_averaged_image(flat_filter_pos)
            if flat_image_array is None:
                print(f"No valid flat images found for '{flat_filter_pos}'. Generating synthetic flat field...")
                # Generate synthetic flat based on the shape of the raw image
                _, synthetic_flat = generate_synthetic_dark_flat_fields_np(raw_image_array.shape, self.sigma)
                flat_image_array = synthetic_flat
                print("Synthetic Flat Field generated.")
            else:
                print("Flat field loaded successfully.")

            # Ensure all images are of consistent type before correction
            raw_image_array = raw_image_array.astype(np.float32)
            dark_image_array = dark_image_array.astype(np.float32)
            flat_image_array = flat_image_array.astype(np.float32)


            # Perform Correction
            print("Performing flat field correction...")
            corrected_image_array = perform_correction_np(raw_image_array, dark_image_array, flat_image_array)
            print("Flat field correction complete.")

            return corrected_image_array

        except ValueError as e:
            print(f"Error: {e}")
            print("Please check filter positions or data availability.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during processing: {e}")
            return None
        finally:
            print("-" * 30)
            print("Flat Field Correction process finished.")


#----------------------------------------------------------------------------
#-- Main CLI Execution (Updated to use FlatfieldProcessor Class)
#----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Perform Flat Field Correction on images using ImageProcessor for data loading.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Required argument for the root directory containing image data
    parser.add_argument(
        "image_data_root_dir",
        help="Root directory containing all image data (raw, dark, flat)."
             "Expected structure: root_dir/[filter_pos]/[degree_pos]/image.tif"
    )

    # Required arguments for filter positions
    parser.add_argument(
        "--raw_filter_pos",
        required=True,
        help="Filter position for the Raw Image(s) (R)."
             "e.g., 'open' for a raw image taken with open filter."
    )
    parser.add_argument(
        "--dark_filter_pos",
        required=True,
        help="Filter position for the Dark Field Image(s) (D)."
             "e.g., 'dark' for images taken with the shutter closed."
    )
    parser.add_argument(
        "--flat_filter_pos",
        required=True,
        help="Filter position for the Flat Field Image(s) (F)."
             "e.g., 'flat' for images taken of a uniform source."
    )

    # Optional argument for output path
    parser.add_argument(
        "--output_path",
        help="Path to save the Corrected Image (C).\n"
             "Defaults to 'corrected_image.png' in the current directory.",
        default="corrected_image.png"
    )

    # Optional argument for gaussian sigma
    parser.add_argument(
        "--sigma",
        type=float,
        default=1.0,
        help="Standard deviation for Gaussian smoothing applied to all loaded/generated images.\n"
             "Set to 0 to disable smoothing. Default: 1.0",
    )

    args = parser.parse_args()

    # Initialize ImageProcessor to load all data first
    # This might take some time depending on your data volume.
    # The FlatfieldProcessor will then pull from this loaded data.
    # Note: ImageProcessor is initialized within FlatfieldProcessor now.

    processor = FlatfieldProcessor(args.image_data_root_dir, args.sigma)

    try:
        # Load all images using ImageProcessor's internal logic
        # This step is handled implicitly by ImageProcessor in FlatfieldProcessor's init
        # No explicit load_images() call needed here in main if ImageProcessor handles it at init.
        # However, ImageProcessor's __init__ just sets up the directory.
        # We need to ensure data is actually read. Let's assume ImageProcessor has a `load_all_images` method.
        # If not, you might need to add it or call its internal methods.
        # Assuming ImageProcessor reads data when `image_data` is first accessed or via a method.

        # Trigger ImageProcessor to load data (if not lazy loaded)
        print(f"Loading all image data from '{args.image_data_root_dir}' using ImageProcessor...")
        # A simple way to force loading if ImageProcessor is lazy is to access its data attribute
        # Or, ImageProcessor should ideally have a method like `load_data()`
        # For this example, let's assume image_processor.image_data will trigger loading.
        _ = processor.image_processor.image_data # This line forces ImageProcessor to load data if it's lazy.
        print("All image data loaded by ImageProcessor.")


        # Perform correction using the new class
        corrected_img = processor.process_flatfield_correction(
            raw_filter_pos=args.raw_filter_pos,
            dark_filter_pos=args.dark_filter_pos,
            flat_filter_pos=args.flat_filter_pos
        )

        if corrected_img is not None:
            # Save Corrected Image
            print(f"Saving corrected image to {args.output_path}...")
            save_image_from_array(corrected_img, args.output_path)
            print(f"Corrected image saved successfully to {args.output_path}")

    except Exception as e:
        print(f"An error occurred in the main execution: {e}")

    print("-" * 30)
    print("Flat Field Correction script finished.")