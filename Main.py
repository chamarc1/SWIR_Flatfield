"""
SWIR Flatfield Processing - Main Entry Point

This script processes Short-Wave Infrared (SWIR) images to create flatfield corrections.
A flatfield correction removes spatial variations in sensor response, making images
more uniform and improving data quality.

The script now automatically processes ALL filter wheel positions (pos1-pos4) and creates
combined visualizations showing all positions together.

Usage:
    python Main.py [--num_sigma <value>]
    
Example:
    python Main.py --num_sigma 1.0

__author__ =    "Charlemagne Marc"
__copyright__ = "Copyright 2025, ESI SWIR Project"
__version__ =   "2.0.0"
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
    2. Creates flatfield processors for all filter positions
    3. Generates combined plots for all positions
    4. Creates both 2D composite and 3D envelope visualizations
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Create flatfield corrections for SWIR images.\n\n"
                   "This tool processes multiple SWIR images for ALL filter positions\n"
                   "and creates combined visualizations showing all positions together.",
        formatter_class=argparse.RawTextHelpFormatter
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
    
    # Process all positions
    process_all_positions(args.num_sigma)

def process_all_positions(num_sigma):
    """
    Process all filter wheel positions and create combined visualizations.
    
    Args:
        num_sigma (float): Standard deviation for Gaussian smoothing
    """
    print("Starting SWIR flatfield processing for ALL filter positions...")
    print(f"Using smoothing sigma: {num_sigma}")
    
    try:
        # Create the flatfield processor (now handles all positions)
        pos1_processor = FlatfieldProcessor("pos1")
        pos2_processor = FlatfieldProcessor("pos2")
        pos3_processor = FlatfieldProcessor("pos3")
        pos4_processor = FlatfieldProcessor("pos4")
        
        # Process all positions and create combined plots and Generate detailed analysis for each position
        print("\n" + "="*70)
        print("Generating detailed flatfield analysis...")
        print("="*70)
        print("\n" + "="*70)
        print("Filter Position 1:")
        print("="*70)
        pos1_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=num_sigma)
        print("\n" + "="*70)
        print("Filter Position 2:")
        print("="*70)
        pos2_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=num_sigma)
        print("\n" + "="*70)
        print("Filter Position 3:")
        print("="*70)
        pos3_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=num_sigma)
        print("\n" + "="*70)
        print("Filter Position 4:")
        print("="*70)
        pos4_processor.generate_quadratic_envelope_flatfield(smoothing_sigma=num_sigma)
        
        print("\n" + "="*70)
        print("PROCESSING COMPLETE!")
        print("="*70)
        # print("Generated visualizations:")
        # print("• Combined 2D composites (2x2 grid)")
        # print("• Combined 3D envelopes (single plot)")
        # print("• Individual 2D composites (4 separate plots)")
        # print("• Individual 3D envelopes (4 separate plots)") 
        # print("• Individual profile comparisons (4 separate plots)")
        # print("• Individual flatfield corrections for each position")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        print("Please check your input parameters and try again.")
        raise

if __name__ == "__main__":
    main()
