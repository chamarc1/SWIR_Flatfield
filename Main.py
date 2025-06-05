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

# #----------------------------------------------------------------------------
# #-- main - main function
# #----------------------------------------------------------------------------
# def main():
#     # crossTrack_dir = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/LEFT_RIGHT/"
#     # alongTrack_dir = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/UP_DOWN/"
#     # metadata = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/gits/AH2_SWIR_metadata_matcher/202502_SWIR_Flatfield_Matched_Metadata.csv"\

#     crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
#     alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])
#     wheel_pos = sys.argv[1]
#     num_sigma = float(sys.argv[2])

#     if not wheel_pos.isdigit:
#         print("Enter correct wheel pos")
#         sys.exit()

#     cross_filter_pos = crossTrack_dict[wheel_pos]
#     cross_dark_pos = crossTrackDark_dict[wheel_pos]
#     along_filter_pos = alongTrack_dict[wheel_pos]
#     along_dark_pos = alongTrackDark_dict[wheel_pos]

#     # take the composite image and take the an along-track row
#     # take the array of counts from the row and graph
#     composite_image = crossTrack_processor.generate_composite(cross_filter_pos, cross_dark_pos) +\
#         alongTrack_processor.generate_composite(along_filter_pos, along_dark_pos)  
#     plot_composite(composite_image)

#     # Plot parabola cores from alongTrack 
#     crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=False, along_track_pos=600)

#     # find flatfiled
#     crossTrack_processor.plot_flatfield(cross_filter_pos, cross_dark_pos, num_sigma, along_track_pos=600)

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
        type=int,
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

        # if not wheel_pos.isdigit:
        #     print("Enter correct wheel pos")
        #     sys.exit()

        cross_filter_pos = crossTrack_dict[args.wheel_pos]
        cross_dark_pos = crossTrackDark_dict[args.wheel_pos]
        along_filter_pos = alongTrack_dict[args.wheel_pos]
        along_dark_pos = alongTrackDark_dict[args.wheel_pos]

        # take the composite image and take the an along-track row
        # take the array of counts from the row and graph
        composite_image = crossTrack_processor.generate_composite(cross_filter_pos, cross_dark_pos) +\
            alongTrack_processor.generate_composite(along_filter_pos, along_dark_pos)  
        plot_composite(composite_image)

        # Plot parabola cores from alongTrack 
        crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=False, along_track_pos=600)

        # find flatfiled
        crossTrack_processor.plot_flatfield(cross_filter_pos, cross_dark_pos, args.num_sigma, along_track_pos=600)
        
    except Exception as e:
        print(f"An error occured during main execution: {e}")
    
    print("-" * 30)
    print("Flatfield Correction script finished.")
    

if __name__ == "__main__":
    main()
