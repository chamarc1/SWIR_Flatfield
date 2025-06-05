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
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.CompositeProcessor import plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict, flatfield_save_path
from scipy.ndimage import gaussian_filter

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
    
    # Corrected: Changed type from int to float for num_sigma
    parser.add_argument(
        "--num_sigma",
        type=float, # Changed to float to accept values like 2.0
        default=1.0, # Default also changed to float
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

        # take the composite image and take the an along-track row
        # take the array of counts from the row and graph
        composite_image = crossTrack_processor.generate_composite(cross_filter_pos, cross_dark_pos) + \
            alongTrack_processor.generate_composite(along_filter_pos, along_dark_pos)  
        plot_composite(composite_image)

        # Plot parabola cores from alongTrack 
        crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=False, along_track_pos=600)

        # find flatfiled (existing row-wise flatfield plotting)
        crossTrack_processor.plot_flatfield(cross_filter_pos, cross_dark_pos, args.num_sigma, along_track_pos=600)
        
        # New: Generate and optionally save the full-image flatfield
        print("\n--- Generating Full-Image Flatfield ---")
        full_flatfield = crossTrack_processor.generate_full_image_flatfield(
            filter_pos=cross_filter_pos, 
            dark_pos=cross_dark_pos, 
            num_sigma=args.num_sigma,
            plot_path=os.path.join(os.path.dirname(flatfield_save_path), f"full_flatfield_{args.wheel_pos}.png")
        )

        if full_flatfield is not None:
            print(f"Full-image flatfield generated successfully with shape {full_flatfield.shape} and dtype {full_flatfield.dtype}")
        else:
            print("Failed to generate full-image flatfield.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()