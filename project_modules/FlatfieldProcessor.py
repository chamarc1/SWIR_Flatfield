"""
__name__ =      FlatfieldProcessor.py
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
import argparse
import sdt-python

# Corrected import path for ImageProcessor, assuming it's in the same directory
from ImageProcessor import ImageProcessor
from Constants import directory_dict 

#----------------------------------------------------------------------------
#-- Core Image Processing Functions for Flatfielding
#----------------------------------------------------------------------------

def save_image_from_array(img_array, file_path):
    """
    Normalizes a float NumPy array to 0-255 (uint8) and saves it as a grayscale image.
    This function handles potential NaN or infinite values by converting them to 0.0
    before normalization and clipping.
    """
    # Handle potential NaN or infinite values before normalization
    img_array = np.nan_to_num(img_array, nan=0.0, posinf=0.0, neginf=0.0)

    C_min = img_array.min()
    C_max = img_array.max()

    if C_max > C_min:
        C_normalized = (img_array - C_min) / (C_max - C_min)
    else:
        # If all values are the same (e.g., a completely black image), result should be uniform (e.g., black)
        C_normalized = np.zeros_like(img_array)

    C_normalized = (C_normalized * 255).astype('uint8')
    Image.fromarray(C_normalized).convert('L').save(file_path) # 'L' for grayscale

def generate_synthetic_dark_flat_fields_np(image_shape, sigma_dark_flat=1.0):
    """
    Generates synthetic dark and flat field images as NumPy arrays based on a
    reference image shape. This is useful for testing when actual dark/flat fields
    are not available.

    :param image_shape: tuple, the desired (height, width) shape for the synthetic images.
    :param sigma_dark_flat: float, standard deviation for Gaussian smoothing applied.
    :return: tuple of (smoothed_dark, flat_array_smoothed), the synthetic dark and flat fields.
    """
    # Create a dummy raw image array for synthetic generation logic's initial PIL conversion
    # Assume a grayscale image for PIL conversion for consistency.
    # A non-zero value is added to simulate some signal for the dark field generation.
    dummy_raw_image_array = np.zeros(image_shape, dtype=np.uint8)
    dummy_raw_image_array[image_shape[0]//2, image_shape[1]//2] = 100 # Simple spot to make it not completely black initially

    # Generate Synthetic Dark Field (D)
    # Convert dummy raw to PIL Image (L mode for grayscale) for brightness enhancement
    raw_pil_L = Image.fromarray(dummy_raw_image_array).convert('L')
    enhancer = ImageEnhance.Brightness(raw_pil_L)
    # Reduce brightness to simulate a dark field (e.g., reduce to 20% of original brightness)
    dark_image_pil = enhancer.enhance(0.2)
    dark_array = np.array(dark_image_pil).astype('float32')

    # Apply Gaussian smoothing to synthetic dark field
    if sigma_dark_flat > 0:
        smoothed_dark = gaussian_filter(dark_array, sigma=sigma_dark_flat)
    else:
        smoothed_dark = dark_array

    # Generate Synthetic Flat Field (F) by creating a uniform image with noise
    # Desired brightness level for flat field (less than 255 to avoid clipping on noise)
    flat_brightness_value = 200
    flat_array = np.full(image_shape, flat_brightness_value, dtype='float32')
    noise = np.random.normal(0, 5, flat_array.shape).astype('float32') # Add Gaussian noise
    flat_array = flat_array + noise
    flat_array = np.clip(flat_array, 0, 255).astype('float32') # Clip values to valid range

    # Apply Gaussian smoothing to synthetic flat field
    if sigma_dark_flat > 0:
        flat_array_smoothed = gaussian_filter(flat_array, sigma=sigma_dark_flat)
    else:
        flat_array_smoothed = flat_array

    return smoothed_dark, flat_array_smoothed

def perform_correction_np(R, D_avg, F_avg):
    """
    Performs flat field correction on NumPy arrays following the formula:
    I_ij = (R_ij - D_ij) * (mean(F_kl - D_kl) / (F_ij - D_ij))
    (Adapted from Equation 1 in AMT paper: https://amt.copernicus.org/articles/17/5709/2024/)

    :param R: Raw image array (R_ij).
    :param D_avg: Averaged Dark Field image array (D_ij).
    :param F_avg: Averaged Flat Field image array (F_ij).
    :return: Corrected image array (I_ij).
    :raises ValueError: If input image dimensions are not consistent.
    """
    if R.shape != D_avg.shape or R.shape != F_avg.shape:
        raise ValueError("All input images (Raw, Dark Average, Flat Average) must have the same dimensions for correction.")

    # Calculate (F_avg - D_avg), which is F_corr (dark-corrected flat-field image) in the paper
    F_corr = F_avg - D_avg

    # Calculate mean(F_kl - D_kl)
    m = np.mean(F_corr)

    # Avoid division by zero: replace zeros or near-zeros in F_corr with a small constant (epsilon)
    epsilon = 1e-6
    denominator = F_corr.copy()
    denominator[np.abs(denominator) < epsilon] = epsilon

    # Calculate gain factor: G_ij = mean(F_corr) / F_corr
    G = m / denominator

    # Calculate (R_ij - D_ij), which is R_corr (dark-corrected raw image)
    R_corr = R - D_avg

    # Apply gain to the dark-corrected raw image to get the final corrected image
    C = R_corr * G

    # Handle any potential NaN or infinite values resulting from calculation
    C = np.nan_to_num(C, nan=0.0, posinf=0.0, neginf=0.0)

    return C

class FlatfieldStd:
    def __init__(self, image_data, gaussian_fit=True, shape=None, density_weight=false)

#----------------------------------------------------------------------------
#-- FlatfieldProcessor Class
#----------------------------------------------------------------------------
class FlatfieldProcessor:
    def __init__(self, image_data_root_dir, sigma=1.0):
        """
        Initializes the FlatfieldProcessor. This class coordinates the loading of
        images via ImageProcessor and applies flat field correction.

        :param image_data_root_dir: The root directory containing all image data (raw, dark, flat).
                                    Expected structure: root_dir/[filter_pos]/[degree_pos]/image.tif
        :param sigma: Standard deviation for Gaussian smoothing applied to images during loading/averaging.
                      Set to 0 to disable smoothing.
        """
        self.image_processor = ImageProcessor(image_data_root_dir)
        self.sigma = sigma
        print(f"FlatfieldProcessor initialized with root directory: {image_data_root_dir}")
        print(f"Default smoothing sigma: {self.sigma}")

        # Trigger ImageProcessor to load all data when FlatfieldProcessor is initialized.
        # This will populate self.image_processor.image_data for subsequent access.
        _ = self.image_processor.image_data # Accessing the property triggers loading if it's lazy.
        print("All image data loaded by ImageProcessor.")

    def _get_averaged_image_array(self, filter_position):
        """
        Helper method to retrieve and average all images for a given filter position
        from ImageProcessor's loaded data. Applies Gaussian smoothing during aggregation.

        :param filter_position: str, the filter position string (e.g., 'dark', 'flat').
        :return: np.ndarray, the averaged image array (float32), or None if no images are found.
        """
        images = []
        # Access image_data property of ImageProcessor, which triggers loading if not already done.
        # Iterates through all degree positions within the specified filter position.
        for degree_pos_data in self.image_processor.image_data.get(filter_position, {}).values():
            for img_array in degree_pos_data:
                # Convert raw image (uint16) to float32 before smoothing
                img_float = img_array.astype(np.float32)
                if self.sigma > 0:
                    smoothed_array = gaussian_filter(img_float, sigma=self.sigma)
                else:
                    smoothed_array = img_float
                images.append(smoothed_array)

        if not images:
            return None
        # Average all collected and smoothed images pixel-wise
        return np.mean(np.asarray(images), axis=0)

    def process_flatfield_correction(self, raw_filter_pos, dark_filter_pos, flat_filter_pos):
        """
        Coordinates the full flat field correction process for a specified raw image
        filter position using averaged dark and flat fields.

        The process involves:
        1. Loading a raw image to be corrected (currently takes the first available).
        2. Computing the average dark frame from all images in `dark_filter_pos`.
        3. Computing the average flat frame from all images in `flat_filter_pos`.
        4. Applying the combined dark and flat field correction formula to the raw image.

        :param raw_filter_pos: The filter position string for the raw images to be corrected.
        :param dark_filter_pos: The filter position string for the dark images used to compute the average dark frame.
        :param flat_filter_pos: The filter position string for the flat images used to compute the average flat frame.
        :return: np.ndarray, the corrected image array (float32), or None if an error occurs.
        """
        print(f"\n--- Starting Flat Field Correction ---")
        print(f"Raw Image Filter: '{raw_filter_pos}'")
        print(f"Dark Image Filter: '{dark_filter_pos}'")
        print(f"Flat Image Filter: '{flat_filter_pos}'")
        print(f"Smoothing Sigma: {self.sigma}")
        print("-" * 30)

        try:
            # 1. Load Raw Image to be corrected (R_ij)
            # For simplicity in this CLI, we take the first raw image found from the first degree position.
            raw_data_for_pos = self.image_processor.image_data.get(raw_filter_pos)
            if not raw_data_for_pos:
                raise ValueError(f"No raw images found for filter position '{raw_filter_pos}'. Cannot proceed.")

            first_degree_pos_raw = next(iter(raw_data_for_pos))
            # Convert to float32 and apply smoothing to the raw image before correction
            raw_image_to_correct = raw_data_for_pos[first_degree_pos_raw][0].astype(np.float32)
            if self.sigma > 0:
                raw_image_to_correct = gaussian_filter(raw_image_to_correct, sigma=self.sigma)
            print("Raw image selected and pre-processed successfully.")

            # 2. Compute Averaged Dark Frame (D_ij)
            print(f"Retrieving/averaging dark field from filter position '{dark_filter_pos}'...")
            dark_average_frame = self._get_averaged_image_array(dark_filter_pos)
            if dark_average_frame is None:
                print(f"No valid dark images found for '{dark_filter_pos}'. Generating synthetic dark field...")
                synthetic_dark, _ = generate_synthetic_dark_flat_fields_np(raw_image_to_correct.shape, self.sigma)
                dark_average_frame = synthetic_dark
                print("Synthetic Dark Field generated.")
            else:
                print("Dark field average retrieved successfully.")

            # 3. Compute Averaged Flat Frame (F_ij)
            print(f"Retrieving/averaging flat field from filter position '{flat_filter_pos}'...")
            flat_average_frame = self._get_averaged_image_array(flat_filter_pos)
            if flat_average_frame is None:
                print(f"No valid flat images found for '{flat_filter_pos}'. Generating synthetic flat field...")
                _, synthetic_flat = generate_synthetic_dark_flat_fields_np(raw_image_to_correct.shape, self.sigma)
                flat_average_frame = synthetic_flat
                print("Synthetic Flat Field generated.")
            else:
                print("Flat field average retrieved successfully.")

            # Ensure all relevant arrays are float32 for consistent calculations
            dark_average_frame = dark_average_frame.astype(np.float32)
            flat_average_frame = flat_average_frame.astype(np.float32)

            # 4. Perform the combined dark and flat field correction
            print("Performing flat field correction using combined formula...")
            corrected_image_array = perform_correction_np(
                R=raw_image_to_correct,
                D_avg=dark_average_frame,
                F_avg=flat_average_frame
            )
            print("Flat field correction complete.")

            return corrected_image_array

        except ValueError as e:
            print(f"Error during processing: {e}")
            print("Please check filter positions and ensure image data exists in the specified directories.")
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
        description="Perform Flat Field Correction on images using ImageProcessor for data loading.\n\n"
                    "This script implements the combined dark current and flat field correction\n"
                    "as described in Equation 1 of the provided AMT paper.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Change image_data_root_dir to be an optional argument, with a default from Constants.py
    parser.add_argument(
        "--image_data_root_dir", # Changed from positional to optional argument (with '--' prefix)
        default=directory_dict["crossTrack"], # Default to 'crossTrack' directory from Constants.py
        help="Root directory containing all image data (raw, dark, flat).\n"
             "Defaults to the 'crossTrack' path defined in Constants.py if not provided.\n"
             "Expected structure: root_dir/[filter_pos]/[degree_pos]/image.tif"
    )

    # Required arguments for filter positions (these still need to be explicitly provided
    # unless you want to map them via Constants.py 'wheel_pos' keys like in Main.py)
    parser.add_argument(
        "--raw_filter_pos",
        required=True,
        help="Filter position for the Raw Image(s) to be corrected (R).\n"
             "The script will use the first image found in the first degree position."
    )
    parser.add_argument(
        "--dark_filter_pos",
        required=True,
        help="Filter position for the Dark Field Image(s) (D).\n"
             "All images found here will be averaged to create the D_avg frame."
    )
    parser.add_argument(
        "--flat_filter_pos",
        required=True,
        help="Filter position for the Flat Field Image(s) (F).\n"
             "All images found here will be averaged to create the F_avg frame."
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
        help="Standard deviation for Gaussian smoothing applied to all loaded/generated images\n"
             "(raw, dark, flat). Set to 0 to disable smoothing. Default: 1.0",
    )

    args = parser.parse_args()

    try:
        # Initialize the FlatfieldProcessor, which in turn initializes ImageProcessor
        # and triggers the initial loading of all image data.
        processor = FlatfieldProcessor(args.image_data_root_dir, args.sigma)

        # Perform correction using the new class instance
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
            
        corrected_image = processor.process_flatfield_correction(
            raw_filter_pos=args.raw_filter_pos,
            dark_filter_pos=args.dark_filter_pos,
            flat_filter_pos=args.flat_filter_pos
        )
        
        if corrected_img is not None:
            print(f"Saving corrected image to {args.output_path}...")
            save_image_from_array(corrected_img, args.output_path)
            print(f"Corrected image saved successfully to {args.output_path}")

    except Exception as e:
        print(f"An error occurred during main execution: {e}")

    print("-" * 30)
    print("Flat Field Correction script finished.")