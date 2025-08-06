#!/usr/bin/env python3
"""
Test script for the updated extract_profile methods with new return values.

This script demonstrates how to use the updated profile extraction methods that now
return 6 values instead of 3, providing access to all stages of processing.

Usage:
    python test_updated_profiles.py

Author: Charlemagne Marc
"""

from project_modules.FlatfieldProcessor import FlatfieldProcessor

def test_updated_extract_methods():
    """
    Test the updated extract_row_profile and extract_column_profile methods.
    """
    print("Testing updated profile extraction methods...")
    
    try:
        # Create a flatfield processor for position 1
        processor = FlatfieldProcessor("pos1")
        
        print("\n" + "="*60)
        print("Testing extract_row_profile with new return values:")
        print("="*60)
        
        # Extract row profile - now returns 6 values
        x_vals, combined_profile, x_vals_filtered, profile_filtered, profile_smoothed, envelope = processor.extract_row_profile(
            avg_window=10,        # Window size for averaging around optical center
            num_sigma=2.0,        # Sigma threshold for outlier rejection
            window_length=61,     # Window length for Savitzky-Golay smoothing
            polyorder=3           # Polynomial order for smoothing
        )
        
        if x_vals is not None:
            print(f"✅ Cross-track profile extracted successfully:")
            print(f"  - Raw profile length: {len(x_vals)} points")
            print(f"  - Filtered profile length: {len(x_vals_filtered)} points")
            print(f"  - Raw signal range: {combined_profile.min():.2f} - {combined_profile.max():.2f} DN")
            print(f"  - Smoothed signal range: {profile_smoothed.min():.2f} - {profile_smoothed.max():.2f} DN")
            print(f"  - Envelope range: {envelope.min():.2f} - {envelope.max():.2f} DN")
        else:
            print("❌ Cross-track profile extraction failed")
        
        print("\n" + "="*60)
        print("Testing extract_column_profile with new return values:")
        print("="*60)
        
        # Extract column profile - now returns 6 values
        x_vals_col, combined_profile_col, x_vals_filtered_col, profile_filtered_col, profile_smoothed_col, envelope_col = processor.extract_column_profile(
            avg_window=10, num_sigma=2.0, window_length=61, polyorder=3
        )
        
        if x_vals_col is not None:
            print(f"✅ Along-track profile extracted successfully:")
            print(f"  - Raw profile length: {len(x_vals_col)} points")
            print(f"  - Filtered profile length: {len(x_vals_filtered_col)} points")
            print(f"  - Raw signal range: {combined_profile_col.min():.2f} - {combined_profile_col.max():.2f} DN")
            print(f"  - Smoothed signal range: {profile_smoothed_col.min():.2f} - {profile_smoothed_col.max():.2f} DN")
            print(f"  - Envelope range: {envelope_col.min():.2f} - {envelope_col.max():.2f} DN")
        else:
            print("❌ Along-track profile extraction failed")
        
        print("\n✅ Updated profile extraction test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise

def test_combined_plotting():
    """
    Test the new combined plotting functionality.
    """
    print("\n" + "="*60)
    print("Testing combined profile plotting:")
    print("="*60)
    
    try:
        # Create a flatfield processor for position 2
        processor = FlatfieldProcessor("pos2")
        
        print("\nExtracting and plotting combined profiles...")
        
        # Use the new combined plotting method
        row_data, col_data = processor.plot_combined_profiles(
            avg_window=10,        # Window size for averaging around optical center
            num_sigma=2.0,        # Sigma threshold for outlier rejection
            window_length=61,     # Window length for Savitzky-Golay smoothing
            polyorder=3           # Polynomial order for smoothing
        )
        
        # Unpack the returned data
        (x_vals_row, combined_profile_row, x_vals_filtered_row, 
         profile_filtered_row, profile_smoothed_row, envelope_row) = row_data
        
        (x_vals_col, combined_profile_col, x_vals_filtered_col, 
         profile_filtered_col, profile_smoothed_col, envelope_col) = col_data
        
        print(f"\n✅ Combined plotting completed successfully!")
        print(f"Row data: {len(x_vals_row) if x_vals_row is not None else 0} raw points, {len(x_vals_filtered_row) if x_vals_filtered_row is not None else 0} filtered points")
        print(f"Column data: {len(x_vals_col) if x_vals_col is not None else 0} raw points, {len(x_vals_filtered_col) if x_vals_filtered_col is not None else 0} filtered points")
        
    except Exception as e:
        print(f"\n❌ Error during combined plotting test: {e}")
        raise

if __name__ == "__main__":
    print("SWIR Flatfield - Updated Profile Extraction Test")
    print("=" * 60)
    
    # Test the updated individual extraction methods
    test_updated_extract_methods()
    
    # Test the new combined plotting functionality
    test_combined_plotting()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)
    print("\nSummary of updated functionality:")
    print("• extract_profile() now returns 6 values:")
    print("  1. x_vals: Original x-coordinates")
    print("  2. combined_profile: Raw combined profile") 
    print("  3. x_vals_filtered: Sigma-filtered x-coordinates")
    print("  4. profile_filtered: Sigma-filtered profile")
    print("  5. profile_smoothed: Savitzky-Golay smoothed profile")
    print("  6. envelope: Quadratic envelope fit")
    print("• extract_row_profile() and extract_column_profile() return same 6 values")
    print("• plot_combined_profiles() shows both profiles with all processing stages")
    print("• generate_quadratic_envelope_flatfield() uses the updated return values")
