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
OPTICAL_CENTER_X = 526
OPTICAL_CENTER_Y = 685

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
    
    def extract_profile(self, images, pos, direction="cross", avg_window=10, num_sigma=2.0, window_length=61, polyorder=3):
        """
        Extract and process a 1D profile (cross-track or along-track) from a list of images.
        Returns the filtered and smoothed profile and the corresponding x values.
        """
        avg_profiles = []
        # Accepts either a list of dicts (with "image" key) or a list of arrays
        for img in images:
            # If img is a dict, extract the array
            image = img["image"] if isinstance(img, dict) else img
            if direction == "cross":
                row_start = max(pos - avg_window, 0)
                row_end = min(pos + avg_window + 1, image.shape[0])
                if row_start >= row_end:
                    continue
                profile = np.mean(image[row_start:row_end, :], axis=0)
            elif direction == "along":
                col_start = max(pos - avg_window, 0)
                col_end = min(pos + avg_window + 1, image.shape[1])
                if col_start >= col_end:
                    continue
                profile = np.mean(image[:, col_start:col_end], axis=1)
            else:
                raise ValueError("direction must be 'cross' or 'along'")
            
            # Mask low-signal regions below half max
            profile[profile < np.nanmax(profile) / 2.0] = np.nan
            avg_profiles.append(profile)
            
        if not avg_profiles:
            return None, None
        
        combined_profile = np.nanmean(np.stack(avg_profiles), axis=0)
        x_vals = np.arange(len(combined_profile))
        
        # Outlier rejection
        x_vals_filtered, profile_filtered = self.sigma_filter(x_vals, combined_profile, num_sigma)
        
        # Smoothing
        if len(profile_filtered) < window_length:
            window_length = max(polyorder + 2 if (polyorder + 2) % 2 != 0 else polyorder + 3, 3)
        profile_smoothed = savgol_filter(profile_filtered, window_length=window_length, polyorder=polyorder)
        
        # Plotting
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x_vals, combined_profile, 'x', color='red', label="Combined Profile (raw)", linewidth=1.5, markersize=2.75)
        ax.plot(x_vals_filtered, profile_filtered, '.', color='green', label=f"Filtered ({num_sigma}-sigma)", linewidth=1.5)
        ax.plot(x_vals_filtered, profile_smoothed, color='black', label="Smoothed", linewidth=1.5)

        # Quadratic envelope fit and plot
        _, _, popt_coeffs = self.quadratic_fit(x_vals_filtered, profile_smoothed)
        envelope = parabola_func(x_vals_filtered, *popt_coeffs)
        ax.plot(x_vals_filtered, envelope, color='red', label="Envelope, O(x^2)", linewidth=1.5)

        ax.set_title(f"Extracted Profile ({direction}-track line cut) at pos={pos}")
        ax.set_xlabel("Pixel Index")
        ax.set_ylabel("Signal (DN)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        plt.show()

        return x_vals_filtered, profile_smoothed

    def generate_quadratic_envelope_flatfield(self, pos_cross=526, pos_along=685, avg_window=10, num_sigma=2.0, window_length=61, polyorder=3, smoothing_sigma=None):
        """
        Generate a 2D flatfield correction array based on quadratic envelope fits to mean profiles.
        Models large-scale illumination gradients (e.g., vignetting).
        """
        # Cross-track envelope
        images_cross = self.crossTrack_processor.generate_images(self.cross_filter_pos, self.cross_dark_pos)
        # Extract arrays for profile calculation, robust to both dicts and arrays
        cross_arrays = [img["image"] if isinstance(img, dict) else img for img in images_cross]
        x_vals_cross, profile_cross = self.extract_profile(
            cross_arrays, pos_cross, direction="cross", avg_window=avg_window,
            num_sigma=num_sigma, window_length=window_length, polyorder=polyorder
        )
        _, _, popt_cross = self.quadratic_fit(x_vals_cross, profile_cross)
        envelope_cross = parabola_func(np.arange(cross_arrays[0].shape[1]), *popt_cross)
        envelope_cross_2d = np.tile(envelope_cross, (cross_arrays[0].shape[0], 1))

        # Along-track envelope
        images_along = self.alongTrack_processor.generate_images(self.along_filter_pos, self.along_dark_pos)
        along_arrays = [img["image"] if isinstance(img, dict) else img for img in images_along]
        x_vals_along, profile_along = self.extract_profile(
            along_arrays, pos_along, direction="along", avg_window=avg_window,
            num_sigma=num_sigma, window_length=window_length, polyorder=polyorder
        )
        _, _, popt_along = self.quadratic_fit(x_vals_along, profile_along)
        envelope_along = parabola_func(np.arange(along_arrays[0].shape[0]), *popt_along)
        envelope_along_2d = np.tile(envelope_along[:, np.newaxis], (1, along_arrays[0].shape[1]))

        # Combine and normalize by optical center
        envelope_2d = (envelope_cross_2d + envelope_along_2d) / 2.0
        center_row = min(max(OPTICAL_CENTER_X, 0), envelope_2d.shape[0] - 1)
        center_col = min(max(OPTICAL_CENTER_Y, 0), envelope_2d.shape[1] - 1)
        optical_center_value = envelope_2d[center_row, center_col]
        if optical_center_value == 0:
            optical_center_value = 1
        envelope_2d /= optical_center_value

        # Optional smoothing
        if smoothing_sigma is not None and smoothing_sigma > 0:
            envelope_2d = gaussian_filter(envelope_2d, sigma=smoothing_sigma)

        # for visual inspection
        # plot_composite(envelope_2d)
        return envelope_2d

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
    
    def apply_flatfield_to_raw(self, raw_image, flatfield_path, dark_frame):
        """
        Apply saved flatfield correction to a raw image.
        Returns corrected image and metadata.
        """
        data = np.load(flatfield_path)
        flatfield = data['flatfield']
        metadata = json.loads(data['metadata'].item())

        print(f"[Flatfield] Applying flatfield correction using file: {flatfield_path}")
        print(f"[Flatfield] Flatfield metadata: {metadata}")

        corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
        flatfield = np.where(flatfield == 0, 1, flatfield)
        corrected /= flatfield
        corrected = np.clip(corrected, 0, 2**14 - 1)
        return corrected.astype(np.uint16), metadata
    
    def apply_quadratic_envelope_to_raw(self, raw_image, envelope_path, dark_frame):
        """
        Apply a saved quadratic envelope flatfield correction to a raw image.
        Returns corrected image.
        """
        envelope_2d = np.load(envelope_path)
        print(f"[Flatfield] Applying quadratic envelope correction using file: {envelope_path}")

        corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
        envelope_2d = np.where(envelope_2d == 0, 1, envelope_2d)
        corrected /= envelope_2d
        corrected = np.clip(corrected, 0, 2**14 - 1)
        return corrected.astype(np.uint16)
