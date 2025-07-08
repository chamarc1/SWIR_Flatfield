"""
__name__ =      Main.py
__author__ =    "Charlemagne Marc"
__copyright__ = "Copyright 2025, ESI SWIR Project"
__credits__ =   ["Charlemagne Marc"]
__version__ =   "1.1.1"
__maintainer__ ="Charlemagne Marc"
__email__ =     "chamrc1@oumbc.edu"
__status__ =    "Production"
"""

#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.FlatfieldProcessor import FlatfieldProcessor, plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict
import argparse

#----------------------------------------------------------------------------
#-- main - main function
#----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Perform Flatfield Correction on SWIR images.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--wheel_pos",
        required=True,
        help="SWIR Filter Wheel position."
    )
    parser.add_argument(
        "--num_sigma",
        type=float,
        default=1.0,
        help="Std. deviation for Gaussian smoothing (set 0 to disable, default: 1.0)."
    )
    
    args = parser.parse_args()
    
    # try:
    #     # Comment/Uncomment to run/not run track wise processing
    #     # crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
    #     # alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])

    #     # cross_filter_pos = crossTrack_dict[args.wheel_pos]
    #     # cross_dark_pos = crossTrackDark_dict[args.wheel_pos]
    #     # along_filter_pos = alongTrack_dict[args.wheel_pos]
    #     # along_dark_pos = alongTrackDark_dict[args.wheel_pos]

    #     # # Correction mode: "average" or "pairwise"
    #     # correction_mode = "pairwise"

    #     # cross_composite = crossTrack_processor.generate_composite(
    #     #     cross_filter_pos, cross_dark_pos, correction_mode=correction_mode
    #     # )
    #     # crossTrack_processor.plotComposite(cross_filter_pos, cross_dark_pos)
        
        
    #     # along_composite = alongTrack_processor.generate_composite(
    #     #     along_filter_pos, along_dark_pos, correction_mode=correction_mode
    #     # )
    #     # alongTrack_processor.plotComposite(along_filter_pos, along_dark_pos)

    #     # composite_image = cross_composite + along_composite
    #     # # plot_composite(composite_image)

    #     # # Plot parabola cores from both tracks
    #     # crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=True, along_track_pos=526)
    #     # alongTrack_processor.plot_parabola_cores(along_filter_pos, along_dark_pos, core=True, along_track_pos=685)
        
    #     # # Comment/Uncomment to run/not run flatfield processing
    #     flatfield_processor = FlatfieldProcessor(args.wheel_pos)
    #     flatfield_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=args.num_sigma)
    #     flatfield_processor.characterize_pixel_response(smoothing_sigma=args.num_sigma)
        
    # except Exception as e:
    #     print(f"Error during main execution: {e}")
        
    flatfield_processor = FlatfieldProcessor(args.wheel_pos)
    flatfield_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=args.num_sigma)
    flatfield_processor.characterize_pixel_response(smoothing_sigma=args.num_sigma)
    

if __name__ == "__main__":
    main()
