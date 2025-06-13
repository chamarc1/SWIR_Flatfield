"""
__name__ =      Main.py
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
import sys
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.CompositeProcessor import plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict, flatfield_save_path
from scipy.ndimage import gaussian_filter


# Define additional save paths for the 2D flat field and corrected images in Main.py
FITTED_FLATFIELD_SAVE_PATH = 'plots/fitted_flatfield_main_script.png'
CORRECTED_IMAGE_SAVE_PATH = 'plots/corrected_image_main_script.png'
RESIDUALS_IMAGE_SAVE_PATH = 'plots/residuals_image_main_script.png'


def main():
    parser = argparse.ArgumentParser(
        description="Perform Flatfield Correction on images using ImageProcessor for data loading.\n\n"
                    "This script implements the combined dark current and flat field correction\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--wheel_pos",
        required=True,
        help="Images at SWIR Filter Wheel postion desired"
    )
    
    parser.add_argument(
        "--num_sigma",
        type=float,
        default=1.0,
        help="Number of sigma for outlier rejection in flatfield calculation (default: 3.0)"
    )
    
    try:
        args = parser.parse_args()

        crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
        alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])

        if not args.wheel_pos.isdigit():
            print("Enter correct wheel pos")
            raise ValueError("Invalid input value")

        cross_filter_pos = crossTrack_dict[args.wheel_pos]
        cross_dark_pos = crossTrackDark_dict[args.wheel_pos]
        along_filter_pos = alongTrack_dict[args.wheel_pos]
        along_dark_pos = alongTrackDark_dict[args.wheel_pos]

        # Generate the full-image flatfield
        print("\n--- Generating Full-Image Flatfield ---")
        
        fitted_flat = crossTrack_processor.generate_flatfield(cross_filter_pos, cross_dark_pos)
        
        print(f"Generated fitted flat field mean: {np.mean(fitted_flat):.2f}")

        # --- Retrieve raw_image and dark_image from the ImageProcessor ---
        raw_image = None
        # Find the first available raw image for the specified filter position
        if cross_filter_pos in crossTrack_processor.track_processor.image_data:
            for degree_pos_key in crossTrack_processor.track_processor.image_data[cross_filter_pos]:
                if crossTrack_processor.track_processor.image_data[cross_filter_pos][degree_pos_key]:
                    raw_image = crossTrack_processor.track_processor.image_data[cross_filter_pos][degree_pos_key][0]
                    break # Found the first image, use it for correction
        
        dark_image = crossTrack_processor.compute_average_dark_frame(cross_dark_pos)
        
        if raw_image is None:
            raise ValueError(f"No raw images found for filter position: {cross_filter_pos} in ImageProcessor data.")
        if dark_image is None:
            print("Warning: No dark images found to compute average dark frame. Correction will proceed without dark subtraction for the raw image.")
            # Create a zero-filled dark_image of the same shape if no dark frames are found
            dark_image = np.zeros_like(raw_image)

        # Ensure dark_image matches the raw_image shape if it's an average dark frame
        if raw_image.shape != dark_image.shape:
             print("Warning: Raw image and dark image shapes do not match. Attempting to resize dark_image.")
             # This simple resizing might not be appropriate for all cases.
             # A more robust solution involves ensuring loaded dark frames match sensor dimensions.
             if dark_image.shape[0] < raw_image.shape[0] or dark_image.shape[1] < raw_image.shape[1]:
                 temp_dark = np.zeros_like(raw_image)
                 temp_dark[:dark_image.shape[0], :dark_image.shape[1]] = dark_image
                 dark_image = temp_dark
             elif dark_image.shape[0] > raw_image.shape[0] or dark_image.shape[1] > raw_image.shape[1]:
                 dark_image = dark_image[:raw_image.shape[0], :raw_image.shape[1]]


        # Now, apply the 2D flat field correction
        corrected_image = crossTrack_processor.apply_2d_flatfield_correction(raw_image, dark_image)
        
        print(f"Corrected image mean: {np.mean(corrected_image):.2f}")

        # --- Saving images ---
        # Ensure the 'plots' directory exists
        os.makedirs(os.path.dirname(FITTED_FLATFIELD_SAVE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(CORRECTED_IMAGE_SAVE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(RESIDUALS_IMAGE_SAVE_PATH), exist_ok=True)

        # Save the fitted flat field image
        plt.imsave(FITTED_FLATFIELD_SAVE_PATH, fitted_flat, cmap='viridis')
        print(f"Saved fitted flat field to: {FITTED_FLATFIELD_SAVE_PATH}")

        # Save the corrected image
        plt.imsave(CORRECTED_IMAGE_SAVE_PATH, corrected_image, cmap='viridis')
        print(f"Saved corrected image to: {CORRECTED_IMAGE_SAVE_PATH}")

        # Calculate and save residuals for verification (difference between a master flat and the fit)
        master_flat_for_residuals_raw_list = crossTrack_processor.generate_images(cross_filter_pos, cross_dark_pos)
        if not master_flat_for_residuals_raw_list:
            print("Could not generate master flat for residuals. Skipping residuals plot.")
        else:
            master_flat_for_residuals = np.mean(np.asarray(master_flat_for_residuals_raw_list).astype(np.float64), axis=0)
            master_flat_for_residuals[master_flat_for_residuals < 1.0] = 1.0 # Clamp to avoid issues

            # Reconstruct the fitted flat field using stored coefficients
            height, width = raw_image.shape # Use the dimensions of your actual images
            X_grid_res, Y_grid_res = np.meshgrid(np.arange(width), np.arange(height))
            x_norm_res = (X_grid_res - (width - 1) / 2) / (width / 2)
            y_norm_res = (Y_grid_res - (height - 1) / 2) / (height / 2)
            
            popt_reconstructed_res = (
                crossTrack_processor.quadratic[0], crossTrack_processor.quadratic[1], crossTrack_processor.quadratic[2],
                crossTrack_processor.linear[0], crossTrack_processor.linear[1], crossTrack_processor.constant
            )
            reconstructed_fitted_flat = crossTrack_processor.quadratic_surface_2d((x_norm_res, y_norm_res), *popt_reconstructed_res)

            residuals = master_flat_for_residuals - reconstructed_fitted_flat
            max_abs_res = np.max(np.abs(residuals))
            plt.imsave(RESIDUALS_IMAGE_SAVE_PATH, residuals, cmap='RdBu', vmin=-max_abs_res, vmax=max_abs_res)
            print(f"Saved residuals image to: {RESIDUALS_IMAGE_SAVE_PATH}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()