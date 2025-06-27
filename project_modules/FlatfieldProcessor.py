"""
__name__ =      FlatfieldProcessor.py
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
import os
import datetime
import json
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.ndimage import median_filter
from scipy.optimize import curve_fit  # Provides functions to use non-linear least squares to fit a function (like a parabola) to data.
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.CompositeProcessor import plot_composite
from project_modules.Constants import flatfield_save_path
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict

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
    
    def generate_quadratic_envelope_flatfield(self, smoothing_sigma=None):
        """
        Generate a 2D flatfield correction array based on the quadratic envelope fit
        to the mean cross-track profile of the composite image.
        """
        composite_image = self.crossTrack_processor.generate_composite(self.cross_filter_pos, self.cross_dark_pos) +\
            self.alongTrack_processor.generate_composite(self.along_filter_pos, self.along_dark_pos)
            
        if composite_image is None:
            print("No composite image available.")
            return None
        
        # Applies Gaussian smoothing to the composite_image if a positive sigma is provided.
        if smoothing_sigma is not None and smoothing_sigma > 0:
            composite_image = gaussian_filter(composite_image, sigma=smoothing_sigma)
            
        # Compute the mean cross-track profile (average over rows)
        mean_profile = np.mean(composite_image, axis=0)
        x_vals = np.arange(mean_profile.size)
        
        # Fit quadratic envelope
        _, _, popt_coeffs = self.quadratic_fit(x_vals, mean_profile)
        envelope_1d = self.parabola_func(x_vals, *popt_coeffs) # Calculate the envelope using the fitted coefficients.
        
        # Expand to 2D by repeating the envelope for each row
        envelope_2d = np.tile(envelope_1d, (composite_image.shape[0], 1)) # Creates a 2D array by repeating the 1D envelope across all rows of the composite image.
        
        # Normalize the envelope to mean 1 for proper correction
        envelope_2d /= np.mean(envelope_2d)
        
        # plot the envelope flatfield
        plot_composite(envelope_2d)
        
        return envelope_2d # Returns the 2D composite_image correction array
    
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