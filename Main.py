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
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.CompositeProcessor import plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict
from scipy.ndimage import gaussian_filter
import sys 
import argparse
import numpy as np

#----------------------------------------------------------------------------
#-- main - main function
#----------------------------------------------------------------------------
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
    
    # Optional arguemnt for guassian sigma
    parser.add_argument(
        "--num_sigma",
        type=float,
        default=1.0,
        help="Standard deviation for Gaussian smoothing applied to all loaded/generated images"
             "(raw, dark). Set to 0 to disable smoothing. Default: 1.0",
    )
    
    args = parser.parse_args()
    
    try:
        crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
        alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])

        if not args.wheel_pos.isdigit(): # Added parentheses to call .isdigit()
            print("Enter correct wheel pos")
            raise ValueError("Invalid input value")

        cross_filter_pos = crossTrack_dict[args.wheel_pos]
        cross_dark_pos = crossTrackDark_dict[args.wheel_pos]
        along_filter_pos = alongTrack_dict[args.wheel_pos]
        along_dark_pos = alongTrackDark_dict[args.wheel_pos]

        # Generate full-image flatfield
        print("\n--- Generating Full-Image Flatfield ---")
        # For flatfield generation, we'll assume a 'flat' filter position for demonstration.
        # You might need to adjust 'flat_filter_pos' and 'flat_dark_pos' based on your actual data.
        # Using cross_filter_pos and cross_dark_pos for simplicity here, assuming they represent flatfield data.
        full_image_flatfield_cross = crossTrack_processor.generate_full_image(cross_filter_pos, cross_dark_pos)
        full_image_flatfield_along = alongTrack_processor.generate_full_image(along_filter_pos, along_dark_pos)

        # Combine the flatfields if both exist
        full_image_flatfield = None
        if full_image_flatfield_cross is not None and full_image_flatfield_along is not None:
            # Simple average for combination, adjust as needed for your specific application
            full_image_flatfield = (full_image_flatfield_cross + full_image_flatfield_along) / 2
            print("Combined full-image flatfield generated.")
        elif full_image_flatfield_cross is not None:
            full_image_flatfield = full_image_flatfield_cross
        elif full_image_flatfield_along is not None:
            full_image_flatfield = full_image_flatfield_along
        else:
            print("No full-image flatfield could be generated from either track.")


        # take the composite image and take the an along-track row
        # take the array of counts from the row and graph
        print("\n--- Generating Composite Image ---")
        composite_image_cross = crossTrack_processor.generate_composite(cross_filter_pos, cross_dark_pos)
        composite_image_along = alongTrack_processor.generate_composite(along_filter_pos, along_dark_pos)
        
        composite_image = None
        if composite_image_cross is not None and composite_image_along is not None:
            composite_image = composite_image_cross + composite_image_along
        elif composite_image_cross is not None:
            composite_image = composite_image_cross
        elif composite_image_along is not None:
            composite_image = composite_image_along

        # Apply flatfield correction to the composite image if a flatfield was generated
        if composite_image is not None and full_image_flatfield is not None:
            print("Applying full-image flatfield correction to composite image.")
            # Ensure flatfield is not zero to avoid division by zero
            full_image_flatfield[full_image_flatfield == 0] = 1 # Prevent division by zero
            composite_image_corrected = composite_image / full_image_flatfield
            plot_composite(composite_image_corrected)
            print("Composite image with flatfield correction displayed.")
        elif composite_image is not None:
            plot_composite(composite_image)
            print("Composite image (uncorrected) displayed as no flatfield was generated or applicable.")
        else:
            print("No composite image to display.")


        # Plot parabola cores from alongTrack 
        print("\n--- Plotting Parabola Cores ---")
        crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=False, along_track_pos=600)
        
        # find flatfiled profile for a single row
        print("\n--- Plotting Flatfield Profile ---")
        crossTrack_processor.plot_flatfield(cross_filter_pos, cross_dark_pos, args.num_sigma, along_track_pos=600)
        
    except Exception as e:
        print(f"An error occured during main execution: {e}")
    
    print("-" * 30)
    print("Flatfield Correction script finished.")
    

if __name__ == "__main__":
    main()