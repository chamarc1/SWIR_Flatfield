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
from scipy.ndimage import gaussian_filter
from scipy.ndimage import median_filter
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit  # Provides functions to use non-linear least squares to fit a function (like a parabola) to data.
import matplotlib.pyplot as plt
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.Constants import flatfield_save_path, composite_save_path
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict

#----------------------------------------------------------------------------
#-- plot_composite
#----------------------------------------------------------------------------
def plot_composite(composite_image):
    """plots the composite image from data from both cross and along tracks"""
    if composite_image is not None:  # Checks if a valid composite image (NumPy array) was provided.
        plt.imshow(composite_image)
        plt.axis("on")

        # Set title and labels
        plt.title("Composite")
        plt.xlabel('Cross-Track Pixels')
        plt.ylabel('Along-Track Pixels')
        os.makedirs(os.path.dirname(composite_save_path), exist_ok=True)
        plt.savefig(composite_save_path)

        plt.show()
    else:
        print("No composite image to display.")

#----------------------------------------------------------------------------
#-- FlatfieldProcessor Class
#----------------------------------------------------------------------------
class FlatfieldProcessor:
    def __init__(self, wheel_pos):
        """
        Initializes the FlatfieldProcessor. This class coordinates the loading of
        images via ImageProcessor and applies flat field correction.
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
    
    def parabola_func(self, x, constant, linear, quadratic):
        """
        Defines a parabolic function (quadratic polynomial).

        This function is used as the model for fitting a parabola to data points.

        :param x: float or np.ndarray, the independent variable(s) at which to evaluate the parabola.
        :param constant: float, the y-intercept (constant term) of the parabola.
        :param linear: float, the coefficient of the linear term (the slope at x=0 if quadratic is zero).
        :param quadratic: float, the coefficient of the quadratic term (determines the curvature of the parabola).
        :return: float or np.ndarray, the calculated y-value(s) of the parabola for the given x value(s).
        """
        return constant + linear * x + quadratic * (x**2)
        
    def quadratic_fit(self, x_vals, y_vals):
        """
        Fits a quadratic curve (parabola) to the given x and y values using non-linear least squares,
        specifically using the `parabola_func` as the model. It also calculates and prints the
        standard errors of the fitted parameters

        :param x_vals: np.ndarray, the array of independent variable (x) values.
        :param y_vals: np.ndarray, the array of dependent variable (y) values to which the parabola will be fitted.
        :return: tuple of (x_vals, y_fit, popt), where x_vals are the original x-values (after removing NaNs), y_fit
                 are the corresponding y-values of the fitted parabolic curve, and popt are the optimal parameters.
        """
        # Remove NaN values from x_vals and y_vals
        valid_indices = ~np.isnan(y_vals) # Creates a boolean array indicating indices where y_vals are not NaN.
        x_vals_clean = x_vals[valid_indices] # Filters x_vals to keep only values at valid indices.
        y_vals_clean = y_vals[valid_indices] # Filters y_vals to remove NaN values.

        if len(x_vals_clean) < 3:  # Need at least three points for quadratic fitting
            print("Not enough valid data for quadratic fitting. Returning default coefficients.")
            # Return x_vals_clean, a placeholder for y_fit, and default popt
            return x_vals_clean, np.zeros_like(x_vals_clean), np.array([0.0, 0.0, 0.0])

        # Perform the least-squares fitting
        popt, pcov = curve_fit(self.parabola_func, x_vals_clean, y_vals_clean) # Uses the `curve_fit` function from scipy.optimize to find the optimal parameters (constant, linear, quadratic) that minimize the sum of the squares of the residuals between y_vals and the parabola defined by parabola_func. `popt` contains the fitted parameters, and `pcov` contains the estimated covariance of popt.
        self.constant = popt[0] # Extracts the fitted constant term.
        self.linear = popt[1] # Extracts the fitted linear term.
        self.quadratic = popt[2] # Extracts the fitted quadratic term.
        self.constant_err = np.sqrt(pcov[0][0]) # Calculates the standard error of the constant term from the covariance matrix.
        self.linear_err = np.sqrt(pcov[1][1]) # Calculates the standard error of the linear term.
        self.quadratic_err = np.sqrt(pcov[2][2]) # Calculates the standard error of the quadratic term.

        y_fit = self.parabola_func(x_vals_clean, *popt) # Calculates the y-values of the fitted parabola using the original (cleaned) x_vals and the fitted parameters.

        # # Report values to shell
        # print(f"constant = {self.constant:.7f} ohm") # Prints the fitted constant value with 7 decimal places and its unit.
        # print(f"constant std. error = {self.constant_err:.7f} ohm") # Prints the standard error of the constant term.
        # print(f"linear = {self.linear:.2E} ohm/T") # Prints the fitted linear coefficient in scientific notation with 2 decimal places and its unit.
        # print(f"linear std. error = {self.linear_err:.2E} ohm/T") # Prints the standard error of the linear term.
        # print(f"quadratic = {self.quadratic:.4E} ohm/T^2") # Prints the fitted quadratic coefficient in scientific notation with 4 decimal places and its unit.
        # print(f"quadratic std. error = {self.quadratic_err:.2E} ohm/T^2") # Prints the standard error of the quadratic term.

        return x_vals_clean, y_fit, popt # Returns the original x-values (cleaned) and the corresponding fitted y-values, and popt.
    
    def sigma_filter(self, x_vals, y_vals, n_sigma):
        """"Removes data points where y_vals deviate from the mean by more than n_sigma standard deviations.

        This is a simple outlier removal technique used to filter noisy data before further analysis or fitting.

        :param x_vals: np.ndarray, the array of independent variable (x) values corresponding to the y values.
        :param y_vals: np.ndarray, the array of dependent variable (y) values to be filtered for outliers.
        :param n_sigma: float, the number of standard deviations away from the mean that a data point can be to be considered an inlier. Data points beyond this threshold are considered outliers and removed.
        :return: tuple of (x_vals_filtered, y_vals_filtered), containing the x and y values after the outlier removal process.
        """
        # Remove NaN values from x_vals and y_vals
        valid_indices = ~np.isnan(y_vals) # Creates a boolean array indicating indices where y_vals are not NaN.
        x_vals_clean = x_vals[valid_indices] # Filters x_vals to keep only values at valid indices.
        y_vals_clean = y_vals[valid_indices] # Filters y_vals to remove NaN values.

        if len(y_vals_clean) == 0:
            return np.array([]), np.array([]) # Return empty arrays if no valid data

        mean_y = np.mean(y_vals_clean) # Calculates the mean of the cleaned y-values.
        std_y = np.std(y_vals_clean, mean=mean_y) # Calculates the standard deviation of the cleaned y-values.

        # mask = np.abs(y_vals_clean - mean_y) <= n_sigma * std_y
        mask = (y_vals_clean >= mean_y - n_sigma * std_y) & (y_vals_clean <= mean_y + n_sigma * std_y) # Creates a boolean mask that is True for data points whose y-value is within `n_sigma` standard deviations of the mean, and False otherwise (outliers).

        return x_vals_clean[mask], y_vals_clean[mask] # Returns the x and y values corresponding to the True values in the mask (i.e., the filtered data without outliers).
    
    def extract_profile(self, images, pos, direction="cross", avg_window=10, num_sigma=2.0, window_length=61, polyorder=3):
        """
        Extracts and processes a 1D profile (cross-track or along-track) from a list of images.
        Returns the filtered and smoothed profile and the corresponding x values.
        """
        avg_profiles = []
        for image in images:
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
            
            # Filter out low-signal regions below Half_Max
            # for i in range(profile.shape[0]):
            #     if profile[i] < np.nanmax(profile) / 2.0:
            #         profile[i] = np.nan
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
        
        # Plotting section
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x_vals, combined_profile, 'x', color='red', label="Combined Profile (raw)", linewidth=1.5, markersize=2.75)
        ax.plot(x_vals_filtered, profile_filtered, '.', color='green', label=f"Filtered ({num_sigma}-sigma)", linewidth=1.5)
        ax.plot(x_vals_filtered, profile_smoothed, color='black', label="Smoothed", linewidth=1.5)

        # Quadratic envelope fit and plot
        _, _, popt_coeffs = self.quadratic_fit(x_vals_filtered, profile_smoothed)
        envelope = self.parabola_func(x_vals_filtered, *popt_coeffs)
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
        Generate a 2D flatfield correction array based on the quadratic envelope fit
        to the mean profile of the composite image, using both cross-track and along-track directions.

        This method models large-scale illumination gradients (such as vignetting) by:
        - Extracting 1D signal profiles in both cross-track and along-track directions.
        - Fitting a quadratic (parabolic) curve to each profile.
        - Expanding each 1D quadratic fit into a 2D array (one for cross, one for along).
        - Combining the two 2D arrays (by averaging) to form the final envelope.
        - Normalizing the envelope so its mean is 1.
        - Optionally smoothing the envelope to suppress noise.
        - Returning the 2D envelope, which can be used as a flatfield correction surface.
        """

        # Cross-track envelope
        images_cross = self.crossTrack_processor.generate_images(self.cross_filter_pos, self.cross_dark_pos)
        # Extract a 1D profile by averaging over a window of rows centered at pos_cross.
        x_vals_cross, profile_cross = self.extract_profile(
            images_cross, pos_cross, direction="cross", avg_window=avg_window,
            num_sigma=num_sigma, window_length=window_length, polyorder=polyorder
        )
        # Fit a quadratic curve to the cross-track profile.
        _, _, popt_cross = self.quadratic_fit(x_vals_cross, profile_cross)
        # Evaluate the fitted quadratic across the full cross-track axis (width of image).
        envelope_cross = self.parabola_func(np.arange(images_cross[0].shape[1]), *popt_cross)
        # Tile the 1D envelope across all rows to create a 2D array.
        envelope_cross_2d = np.tile(envelope_cross, (images_cross[0].shape[0], 1))

        # Along-track envelope
        images_along = self.alongTrack_processor.generate_images(self.along_filter_pos, self.along_dark_pos)
        # Extract a 1D profile by averaging over a window of columns centered at pos_along.
        x_vals_along, profile_along = self.extract_profile(
            images_along, pos_along, direction="along", avg_window=avg_window,
            num_sigma=num_sigma, window_length=window_length, polyorder=polyorder
        )
        # Fit a quadratic curve to the along-track profile.
        _, _, popt_along = self.quadratic_fit(x_vals_along, profile_along)
        # Evaluate the fitted quadratic across the full along-track axis (height of image).
        envelope_along = self.parabola_func(np.arange(images_along[0].shape[0]), *popt_along)
        # Tile the 1D envelope across all columns to create a 2D array.
        envelope_along_2d = np.tile(envelope_along[:, np.newaxis], (1, images_along[0].shape[1]))

        # Combine the two 2D envelopes
        envelope_2d = (envelope_cross_2d + envelope_along_2d) / 2.0

        # Normalize the envelope by the optical center (x=685, y=526)
        center_row = 526
        center_col = 685
        # Ensure indices are within bounds
        center_row = min(max(center_row, 0), envelope_2d.shape[0] - 1)
        center_col = min(max(center_col, 0), envelope_2d.shape[1] - 1)
        optical_center_value = envelope_2d[center_row, center_col]
        if optical_center_value == 0:
            optical_center_value = 1  # Prevent division by zero
        envelope_2d /= optical_center_value  # Normalize by optical center

        # Apply a Gaussian filter to further suppress noise.
        if smoothing_sigma is not None and smoothing_sigma > 0:
            envelope_2d = gaussian_filter(envelope_2d, sigma=smoothing_sigma)

        # for visual inspection
        plot_composite(envelope_2d)
        return envelope_2d

    def characterize_pixel_response(self, smoothing_sigma=None, save_path=flatfield_save_path):
        """
        Characterize the pixel-to-pixel relative response (flatfield) using composite images.
        This can be applied to raw images in the future.
        """
        # Generate composite images for both directions
        cross_composite = self.crossTrack_processor.generate_composite(self.cross_filter_pos, self.cross_dark_pos)
        along_composite = self.alongTrack_processor.generate_composite(self.along_filter_pos, self.along_dark_pos)
        if cross_composite is None or along_composite is None:
            print("Could not generate composite images for flatfield characterization.")
            return None

        # Combine (mean or sum) the composites
        flatfield = (cross_composite + along_composite) / 2.0
        print("[Flatfield] Composite images combined.")
        plot_composite(flatfield)

        # Optional smoothing
        if smoothing_sigma is not None and smoothing_sigma > 0:
            flatfield = gaussian_filter(flatfield, sigma=smoothing_sigma)
            print(f"[Flatfield] Applied Gaussian smoothing (sigma={smoothing_sigma}).")

        # Normalize to mean 1
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

        # Save for future use
        np.save(save_path, flatfield)
        print(f"Flatfield characterization saved to {save_path}")

        # Optionally plot
        plot_composite(flatfield)

        return flatfield
    
    def apply_flatfield_to_raw(self, raw_image, flatfield_path, dark_frame):
        """
        Apply saved flatfield correction to a raw image.
        Args:
            raw_image: 2D np.ndarray, the raw image to correct
            flatfield_path: str, path to .npz file with flatfield and metadata
            dark_frame: 2D np.ndarray, dark frame to subtract
        Returns:
            corrected_image: 2D np.ndarray, flatfield-corrected image
            metadata: dict, metadata loaded from flatfield file
        """
        data = np.load(flatfield_path)
        flatfield = data['flatfield']
        metadata = json.loads(data['metadata'].item())

        print(f"[Flatfield] Applying flatfield correction using file: {flatfield_path}")
        print(f"[Flatfield] Flatfield metadata: {metadata}")

        # Subtract dark frame
        corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
        # Avoid division by zero
        flatfield = np.where(flatfield == 0, 1, flatfield)
        # Apply correction
        corrected /= flatfield
        # Clip to valid range if needed
        corrected = np.clip(corrected, 0, 2**14 - 1)
        return corrected.astype(np.uint16), metadata
    
    def apply_quadratic_envelope_to_raw(self, raw_image, envelope_path, dark_frame):
        """
        Apply a saved quadratic envelope flatfield correction to a raw image.
        Args:
            raw_image: 2D np.ndarray, the raw image to correct
            envelope_path: str, path to .npy file with the quadratic envelope flatfield
            dark_frame: 2D np.ndarray, dark frame to subtract
        Returns:
            corrected_image: 2D np.ndarray, envelope-corrected image
        """
        envelope_2d = np.load(envelope_path)
        print(f"[Flatfield] Applying quadratic envelope correction using file: {envelope_path}")

        # Subtract dark frame
        corrected = raw_image.astype(np.float32) - dark_frame.astype(np.float32)
        # Avoid division by zero
        envelope_2d = np.where(envelope_2d == 0, 1, envelope_2d)
        # Apply envelope correction
        corrected /= envelope_2d
        # Clip to valid range if needed (e.g., 14-bit data)
        corrected = np.clip(corrected, 0, 2**14 - 1)
        return corrected.astype(np.uint16)