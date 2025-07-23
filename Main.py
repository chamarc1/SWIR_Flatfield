"""
SWIR Flatfield Processing - Main Entry Point

This script processes Short-Wave Infrared (SWIR) images to create flatfield corrections.
A flatfield correction removes spatial variations in sensor response, making images
more uniform and improving data quality.

Usage:
    python Main.py --wheel_pos <position> [--num_sigma <value>]
    
Example:
    python Main.py --wheel_pos 1 --num_sigma 1.0

__author__ =    "Charlemagne Marc"
__copyright__ = "Copyright 2025, ESI SWIR Project"
__version__ =   "1.1.1"
__email__ =     "chamrc1@oumbc.edu"
"""

#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.FlatfieldProcessor import FlatfieldProcessor, plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict
import argparse

#----------------------------------------------------------------------------
#-- MAIN FUNCTION
#----------------------------------------------------------------------------
def main():
    """
    Main function that processes SWIR images for flatfield correction.
    
    This function:
    1. Parses command line arguments
    2. Creates flatfield processors for the specified filter position
    3. Generates quadratic envelope flatfield corrections
    4. Optionally characterizes pixel response
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Create flatfield corrections for SWIR images.\n\n"
                   "This tool processes multiple SWIR images to create a flatfield\n"
                   "correction that removes spatial variations in sensor response.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--wheel_pos",
        required=True,
        type=str,
        help="Filter wheel position to process (e.g., '1', '2', '3')\n"
             "This determines which filter data to use for processing."
    )
    
    parser.add_argument(
        "--num_sigma",
        type=float,
        default=1.0,
        help="Standard deviation for Gaussian smoothing (default: 1.0)\n"
             "Higher values = more smoothing\n"
             "Set to 0 to disable smoothing"
    )
    
    # Parse the command line arguments
    args = parser.parse_args()
    
    # composite
    process_composite_images(args.wheel_pos)
    
    # flatfield
    process_flatfield(args.wheel_pos, args.num_sigma)

# flatfield 2d and 3d
def process_flatfield(wheel_pos, num_sigma):
    print(f"Starting flatfield processing for filter position: {wheel_pos}")
    print(f"Using smoothing sigma: {num_sigma}")
    
    try:
        # STEP 1: Create the flatfield processor
        # This handles loading images and creating the correction
        flatfield_processor = FlatfieldProcessor(wheel_pos)
        
        # STEP 2: Generate the main flatfield correction
        # This creates a 2D correction based on quadratic envelope fitting
        print("\nGenerating quadratic envelope flatfield...")
        flatfield_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=num_sigma)
        
        # STEP 3: Optional pixel response characterization
        # Uncomment the line below to also generate pixel response analysis
        # print("\nCharacterizing pixel response...")
        # flatfield_processor.characterize_pixel_response(smoothing_sigma=num_sigma)
        
        print("\nFlatfield processing completed successfully!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        print("Please check your input parameters and try again.")

# composite image processing options
def process_composite_images(wheel_pos):
    """
    Alternative processing method that creates composite images from multiple tracks.
    This method combines cross-track and along-track images before flatfield processing.
    
    Args:
        wheel_pos (str): Filter wheel position to process
    """
    try:
        # Create processors for both imaging directions
        crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
        alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])

        # Get filter positions for this wheel position
        cross_filter_pos = crossTrack_dict[wheel_pos]
        cross_dark_pos = crossTrackDark_dict[wheel_pos]
        along_filter_pos = alongTrack_dict[wheel_pos]
        along_dark_pos = alongTrackDark_dict[wheel_pos]

        # Choose correction method: "average" or "pairwise"
        correction_mode = "pairwise"

        # Generate composite images for both tracks
        cross_composite = crossTrack_processor.generate_composite(
            cross_filter_pos, cross_dark_pos, correction_mode=correction_mode
        )
        along_composite = alongTrack_processor.generate_composite(
            along_filter_pos, along_dark_pos, correction_mode=correction_mode
        )

        # Combine composites and display
        if cross_composite is not None and along_composite is not None:
            composite_image = cross_composite + along_composite
            plot_composite(composite_image)
        
    except Exception as e:
        print(f"Error during composite processing: {e}")


if __name__ == "__main__":
    """
    This block runs when the script is executed directly (not imported).
    It calls the main() function to start processing.
    """
    exit_code = main()
    exit(exit_code)
