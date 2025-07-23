"""
__name__ =      FlatfieldProcessor.py
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
import os
import datetime
import json
import numpy as np
from scipy.ndimage import gaussian_filter, median_filter
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.Constants import flatfield_save_path, composite_save_path, parabola_func
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
# OPTICAL_CENTER_X = 526
# OPTICAL_CENTER_Y = 685
# OPTICAL_CENTER_X = 685
# OPTICAL_CENTER_Y = 526
OPTICAL_CENTER_X = 675
OPTICAL_CENTER_Y = 560

#----------------------------------------------------------------------------
def plot_composite(composite_image):
    """Plot and save the composite image."""
    if composite_image is not None:
        plt.imshow(composite_image)
        plt.axis("on")
        plt.title("Composite")
        plt.xlabel('Cross-Track Pixels')
        plt.ylabel('Along-Track Pixels')
        os.makedirs(os.path.dirname(composite_save_path), exist_ok=True)
        plt.savefig(composite_save_path)
        plt.show()
    else:
        print("No composite image to display.")

#----------------------------------------------------------------------------
class FlatfieldProcessor:
    def __init__(self, wheel_pos):
        """
        Initializes the FlatfieldProcessor and sets up filter/dark positions.
        """
        self.crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
        self.alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])

        if not wheel_pos.isdigit:
            print("Enter correct wheel pos")
            raise ValueError("Invalid input value")

        self.cross_filter_pos = crossTrack_dict[wheel_pos]
        self.cross_dark_pos = crossTrackDark_dict[wheel_pos]
        self.along_filter_pos = alongTrack_dict[wheel_pos]
        self.along_dark_pos = alongTrackDark_dict[wheel_pos]
        
    def quadratic_fit(self, x_vals, y_vals):
        """
        Fit a quadratic curve (parabola) to x and y values using non-linear least squares.
        Returns fitted y-values and optimal parameters.
        """
        valid_indices = ~np.isnan(y_vals)
        x_vals_clean = x_vals[valid_indices]
        y_vals_clean = y_vals[valid_indices]

        if len(x_vals_clean) < 3:
            print("Not enough valid data for quadratic fitting. Returning default coefficients.")
            return x_vals_clean, np.zeros_like(x_vals_clean), np.array([0.0, 0.0, 0.0])

        popt, pcov = curve_fit(parabola_func, x_vals_clean, y_vals_clean)
        self.constant = popt[0]
        self.linear = popt[1]
        self.quadratic = popt[2]
        self.constant_err = np.sqrt(pcov[0][0])
        self.linear_err = np.sqrt(pcov[1][1])
        self.quadratic_err = np.sqrt(pcov[2][2])

        y_fit = parabola_func(x_vals_clean, *popt)
        return x_vals_clean, y_fit, popt
    
    def sigma_filter(self, x_vals, y_vals, n_sigma):
        """
        Remove data points where y_vals deviate from the mean by more than n_sigma standard deviations.
        """
        valid_indices = ~np.isnan(y_vals)
        x_vals_clean = x_vals[valid_indices]
        y_vals_clean = y_vals[valid_indices]

        if len(y_vals_clean) == 0:
            return np.array([]), np.array([])

        mean_y = np.mean(y_vals_clean)
        std_y = np.std(y_vals_clean, mean=mean_y)
        mask = (y_vals_clean >= mean_y - n_sigma * std_y) & (y_vals_clean <= mean_y + n_sigma * std_y)
        return x_vals_clean[mask], y_vals_clean[mask]
    
    def extract_profile(self, profile_type, avg_window=10, num_sigma=2.0, window_length=61, polyorder=3):
        """
        Extract and process either a row or column profile from images.
        
        Args:
            profile_type (str): Either 'row' for cross-track profile or 'column' for along-track profile
            avg_window (int): Window size for averaging around optical center
            num_sigma (float): Sigma threshold for outlier rejection
            window_length (int): Window length for Savitzky-Golay smoothing
            polyorder (int): Polynomial order for Savitzky-Golay smoothing
            
        Returns:
            tuple: (x_vals_filtered, profile_smoothed, envelope)
        """
        # Configuration mapping for profile types
        config = {
            'row': {
                'processor': self.crossTrack_processor,
                'filter_pos': self.cross_filter_pos,
                'dark_pos': self.cross_dark_pos,
                'optical_center': OPTICAL_CENTER_Y,
                'slice_axis': 0,  # rows
                'mean_axis': 0,   # average along rows
                'title': f"Along-track row Y={OPTICAL_CENTER_Y}",
                'xlabel': "Cross-Track Pixel Index"
            },
            'column': {
                'processor': self.alongTrack_processor,
                'filter_pos': self.along_filter_pos,
                'dark_pos': self.along_dark_pos,
                'optical_center': OPTICAL_CENTER_X,
                'slice_axis': 1,  # columns
                'mean_axis': 1,   # average along columns
                'title': f"Cross-track column X={OPTICAL_CENTER_X}",
                'xlabel': "Along-Track Pixel Index"
            }
        }
        
        if profile_type not in config:
            raise ValueError("profile_type must be either 'row' or 'column'")
        
        cfg = config[profile_type]
        
        # Get images from the appropriate processor
        images = cfg['processor'].generate_images(cfg['filter_pos'], cfg['dark_pos'])
        
        avg_profiles = []
        for img in images:
            # Extract image array (handle both dict and array formats)
            image = img["image"] if isinstance(img, dict) else img
            
            # Calculate slice indices
            start_idx = max(cfg['optical_center'] - avg_window, 0)
            end_idx = min(cfg['optical_center'] + avg_window + 1, image.shape[cfg['slice_axis']])
            if start_idx >= end_idx:
                continue
            
            # Extract profile using dynamic slicing
            if cfg['slice_axis'] == 0:  # row profile
                profile = np.mean(image[start_idx:end_idx, :], axis=cfg['mean_axis'])
            else:  # column profile
                profile = np.mean(image[:, start_idx:end_idx], axis=cfg['mean_axis'])
            
            # Mask low-signal regions
            profile[profile < np.nanmax(profile) / 2.0] = np.nan
            avg_profiles.append(profile)
            
        if not avg_profiles:
            return None, None, None
        
        # Process combined profile
        combined_profile = np.nanmean(np.stack(avg_profiles), axis=0)
        x_vals = np.arange(len(combined_profile))
        
        # Outlier rejection and smoothing
        x_vals_filtered, profile_filtered = self.sigma_filter(x_vals, combined_profile, num_sigma)
        
        if len(profile_filtered) < window_length:
            window_length = max(polyorder + 2 if (polyorder + 2) % 2 != 0 else polyorder + 3, 3)
        profile_smoothed = savgol_filter(profile_filtered, window_length=window_length, polyorder=polyorder)
        
        # Quadratic envelope fit
        _, _, popt_coeffs = self.quadratic_fit(x_vals_filtered, profile_smoothed)
        envelope = parabola_func(x_vals_filtered, *popt_coeffs)
        
        # # Plotting
        # fig, ax = plt.subplots(figsize=(10, 5))
        # ax.plot(x_vals, combined_profile, 'x', color='red', label="Combined Profile (raw)", linewidth=1.5, markersize=2.75)
        # ax.plot(x_vals_filtered, profile_filtered, '.', color='green', label=f"Filtered ({num_sigma}-sigma)", linewidth=1.5)
        # ax.plot(x_vals_filtered, profile_smoothed, color='black', label="Smoothed", linewidth=1.5)
        # ax.plot(x_vals_filtered, envelope, color='red', label="Envelope, O(x^2)", linewidth=1.5)

        # ax.set_title(cfg['title'])
        # ax.set_xlabel(cfg['xlabel'])
        # ax.set_ylabel("Signal (DN)")
        # ax.grid(True, linestyle="--", alpha=0.5)
        # ax.legend()
        # plt.show()

        return x_vals_filtered, profile_smoothed, envelope
    
    def extract_row_profile(self, avg_window=10, num_sigma=2.0, window_length=61, polyorder=3):
        """Extract cross-track profile (along-track row cut) at optical center Y."""
        return self.extract_profile('row', avg_window, num_sigma, window_length, polyorder)
    
    def extract_column_profile(self, avg_window=10, num_sigma=2.0, window_length=61, polyorder=3):
        """Extract along-track profile (cross-track column cut) at optical center X."""
        return self.extract_profile('column', avg_window, num_sigma, window_length, polyorder)

    def generate_quadratic_envelope_flatfield(self, avg_window=10, num_sigma=2.0, window_length=61, polyorder=3, smoothing_sigma=None):
        """
        Generate a 2D flatfield correction array based on quadratic envelope fits to mean profiles.
        Models large-scale illumination gradients (e.g., vignetting).
        """
        # Cross-track envelope using crossTrack_processor
        x_vals_cross, profile_cross, envelope_cross = self.extract_row_profile(
            avg_window=avg_window, num_sigma=num_sigma, 
            window_length=window_length, polyorder=polyorder
        )
        # Get shape from one of the crosstrack images for envelope creation
        images_cross = self.crossTrack_processor.generate_images(self.cross_filter_pos, self.cross_dark_pos)
        cross_arrays = [img["image"] if isinstance(img, dict) else img for img in images_cross]
        # Create full envelope using the fitted parameters
        _, _, popt_cross = self.quadratic_fit(x_vals_cross, profile_cross)
        envelope_cross_full = parabola_func(np.arange(cross_arrays[0].shape[1]), *popt_cross)
        envelope_cross_2d = np.tile(envelope_cross_full, (cross_arrays[0].shape[0], 1))

        # Along-track envelope using alongTrack_processor
        x_vals_along, profile_along, envelope_along = self.extract_column_profile(
            avg_window=avg_window, num_sigma=num_sigma,
            window_length=window_length, polyorder=polyorder
        )

        # Create 3D plot of the profiles only
        self.plot_3d_envelope(x_vals_cross, profile_cross, envelope_cross, x_vals_along, profile_along, envelope_along)
    
    def plot_3d_envelope(self, x_vals_cross, profile_cross, envelope_cross, x_vals_along, profile_along, envelope_along):
        """
        Create a 3D plot of the individual profiles and their envelopes.
        X-axis: Cross-track pixel count
        Y-axis: Along-track pixel count  
        Z-axis: Signal (DN)
        """
        from mpl_toolkits.mplot3d import Axes3D
        
        # Create 3D plot
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot cross-track profile (row profile) at optical center Y
        if x_vals_cross is not None and profile_cross is not None:
            y_cross_line = np.full_like(x_vals_cross, OPTICAL_CENTER_X)  # Fixed Y position
            ax.plot(x_vals_cross, y_cross_line, profile_cross, 
                   color='red', linewidth=3, label='Cross-track Profile (smoothed)', alpha=0.9)
            
            # Plot cross-track envelope
            if envelope_cross is not None:
                ax.plot(x_vals_cross, y_cross_line, envelope_cross, 
                       color='darkred', linewidth=2, linestyle='--', 
                       label='Cross-track Envelope', alpha=0.9)
        
        # Plot along-track profile (column profile) at optical center X  
        if x_vals_along is not None and profile_along is not None:
            x_along_line = np.full_like(x_vals_along, OPTICAL_CENTER_Y)  # Fixed X position
            ax.plot(x_along_line, x_vals_along, profile_along, 
                   color='blue', linewidth=3, label='Along-track Profile (smoothed)', alpha=0.9)
            
            # Plot along-track envelope
            if envelope_along is not None:
                ax.plot(x_along_line, x_vals_along, envelope_along, 
                       color='darkblue', linewidth=2, linestyle='--', 
                       label='Along-track Envelope', alpha=0.9)
        
        # Mark optical center point (using a reasonable z-value)
        if profile_cross is not None and len(profile_cross) > 0:
            # Use the signal value from cross-track profile at optical center as reference
            optical_center_z = np.nanmean(profile_cross) if len(profile_cross) > 0 else 1.0
        else:
            optical_center_z = 1.0
            
        ax.scatter([OPTICAL_CENTER_Y], [OPTICAL_CENTER_X], [optical_center_z], 
                  color='yellow', s=100, marker='*', 
                  label=f'Optical Center ({OPTICAL_CENTER_Y}, {OPTICAL_CENTER_X})')
        
        # Labels and title
        ax.set_xlabel('Cross-Track Pixel Count')
        ax.set_ylabel('Along-Track Pixel Count')
        ax.set_zlabel('Signal (DN)')
        ax.set_title('3D Profile Cuts and Quadratic Envelopes')
        
        # Add legend
        ax.legend(loc='upper left', bbox_to_anchor=(0.05, 0.95))
        
        # Set viewing angle for better visualization
        ax.view_init(elev=25, azim=45)
        
        plt.tight_layout()
        plt.show()
        
    def characterize_pixel_response(self, smoothing_sigma=None, save_path=flatfield_save_path):
        """
        Characterize pixel-to-pixel relative response (flatfield) using composite images.
        """
        cross_composite = self.crossTrack_processor.generate_composite(self.cross_filter_pos, self.cross_dark_pos)
        along_composite = self.alongTrack_processor.generate_composite(self.along_filter_pos, self.along_dark_pos)
        if cross_composite is None or along_composite is None:
            print("Could not generate composite images for flatfield characterization.")
            return None

        flatfield = (cross_composite + along_composite) / 2.0
        print("[Flatfield] Composite images combined.")
        plot_composite(flatfield)

        if smoothing_sigma is not None and smoothing_sigma > 0:
            flatfield = gaussian_filter(flatfield, sigma=smoothing_sigma)
            print(f"[Flatfield] Applied Gaussian smoothing (sigma={smoothing_sigma}).")

        flatfield /= np.mean(flatfield)
        print("[Flatfield] Normalized flatfield to mean 1.")
        
        # Defective Pixel Handling
        mean = np.mean(flatfield)
        std = np.std(flatfield)
        defect_mask = (flatfield < mean - 3*std) | (flatfield > mean + 3*std)
        flatfield[defect_mask] = median_filter(flatfield, size=3)[defect_mask]
        print(f"[Flatfield] Defective pixels replaced: {np.sum(defect_mask)}")
        
        # Metadata
        metadata = {
            "date": datetime.datetime.now().isoformat(),
            "cross_filter_pos": self.cross_filter_pos,
            "cross_dark_pos": self.cross_dark_pos,
            "along_filter_pos": self.along_filter_pos,
            "along_dark_pos": self.along_dark_pos,
            "smoothing_sigma": smoothing_sigma,
            "shape": flatfield.shape,
            "mean": float(np.mean(flatfield)),
            "std": float(np.std(flatfield)),
        }

        np.save(save_path, flatfield)
        print(f"Flatfield characterization saved to {save_path}")
        plot_composite(flatfield)
        return flatfield
    
    # def apply_flatfield_to_raw(self, raw_image, flatfield_path, dark_frame):
    #     """
    #     Apply saved flatfield correction to a raw image.
    #     Returns corrected image and metadata.
    #     """
    #     data = np.load(flatfield_path)
    #     flatfield = data['flatfield']
    #     metadata = json.loads(data['metadata'].item())

    #     print(f"[Flatfield] Applying flatfield correction using file: {flatfield_path}")
    #     print(f"[Flatfield] Flatfield metadata: {metadata}")

    #     corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
    #     flatfield = np.where(flatfield == 0, 1, flatfield)
    #     corrected /= flatfield
    #     corrected = np.clip(corrected, 0, 2**14 - 1)
    #     return corrected.astype(np.uint16), metadata
    
    # def apply_quadratic_envelope_to_raw(self, raw_image, envelope_path, dark_frame):
    #     """
    #     Apply a saved quadratic envelope flatfield correction to a raw image.
    #     Returns corrected image.
    #     """
    #     envelope_2d = np.load(envelope_path)
    #     print(f"[Flatfield] Applying quadratic envelope correction using file: {envelope_path}")

    #     corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
    #     envelope_2d = np.where(envelope_2d == 0, 1, envelope_2d)
    #     corrected /= envelope_2d
    #     corrected = np.clip(corrected, 0, 2**14 - 1)
    #     return corrected.astype(np.uint16)