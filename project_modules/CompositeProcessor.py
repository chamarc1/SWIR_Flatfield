"""
__name__ =      CompositeProcessor.py
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
import os                             # Provides functions for interacting with the operating system, such as file path manipulation and directory listing.
import numpy as np                    # A fundamental library for numerical computation in Python, essential for working with multi-dimensional arrays representing images.
import matplotlib as mpl              # A comprehensive library for creating static, interactive, and animated visualizations in Python. Used here to set the backend for plotting.
import matplotlib.pyplot as plt       # A module within Matplotlib that provides a MATLAB-like interface for plotting. Used for displaying images and other plots.
from scipy.signal import savgol_filter# A signal processing tool for smoothing data using the Savitzky-Golay filter, which fits successive sub-sets of adjacent data points with a low-degree polynomial by linear least squares.
from scipy.optimize import curve_fit  # Provides functions to use non-linear least squares to fit a function (like a parabola) to data.
from scipy.ndimage import gaussian_filter # Needed for flat field composite generation
from project_modules.ImageProcessor import ImageProcessor # Imports the ImageProcessor class from a local module, likely used for loading and basic processing of individual images.
from project_modules.Constants import composite_save_path, parabola_save_path, flatfield_save_path, flatfield_plot_save_path # Imports predefined file paths for saving generated plots from a local Constants module.
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
mpl.use("Qt5Agg")                     # Sets the Matplotlib backend to Qt5Agg, which is an interactive backend using the Qt 5 framework. This allows for displaying plots in a separate window.

#----------------------------------------------------------------------------
#-- CompositeProcessor - class for generating composites
#----------------------------------------------------------------------------
class CompositeProcessor:
    def __init__(self, track_dir, metadata):
        """
        Initializes the processor with the directory containing track images and associated metadata.

        :param track_dir: str, the directory containing subdirectories of images (likely organized by filter and degree).
        :param metadata: dict, metadata associated with the image acquisition, such as sensor temperatures during imaging.
        """
        self.track_dir = track_dir
        self.metadata = metadata
        self.track_processor = ImageProcessor(track_dir)
        self.constant = 0.0
        self. linear = 0.0
        self.quadratic = 0.0
        self.constant_err = 0.0
        self.linear_err = 0.0
        self.quadratic_err = 0.0

    def compute_average_dark_frame(self, dark_pos):
        """Compute the average dark frame from all images taken at the specified dark position.

        A dark frame is typically an image taken with the sensor's shutter closed, capturing sensor noise and biases. Averaging multiple dark frames reduces random noise.

        :param dark_pos: str, the filter position that corresponds to the dark frame images.
        :return: np.ndarray or None, the average dark frame as a NumPy array. Returns None if no dark images are found.
        """
        dark_images = []
        for degree_pos, images in self.track_processor.image_data.get(dark_pos, {}).items(): # Iterates through the images associated with each degree position within the specified dark filter position. The .get(dark_pos, {}) ensures that an empty dictionary is returned if the dark_pos is not found, preventing errors.
            dark_images.extend(images) # Extends the dark_images list with the list of images found at the current degree position.
        return np.mean(np.asarray(dark_images), axis=0) if dark_images else None # If dark_images is not empty, it converts the list of dark frame images to a NumPy array and calculates the mean along the first axis (averaging all images pixel-wise). If dark_images is empty, it returns None.

    def correct_images_with_dark_frame(self, images, dark_frame):
        """Correct images by subtracting the average dark frame from each image, using absolute difference.

        For each image, subtract the dark frame, take the absolute value, and return the list of results.

        :param images: list of np.ndarray, a list of images (as NumPy arrays) to be corrected.
        :param dark_frame: np.ndarray or None, the average dark frame to subtract. If None, no correction is applied.
        :return: list of np.ndarray, a list of dark frame corrected images as NumPy arrays.
        """
        corrected_images = []
        for image in images:
            if dark_frame is not None:
                # Subtract dark frame, take absolute value, clip to valid range, and cast to uint16
                corrected_image = np.abs(image.astype(np.int32) - dark_frame.astype(np.int32))
                corrected_image = np.clip(corrected_image, 0, 2**14 - 1).astype(np.uint16)
            else:
                corrected_image = image
            corrected_images.append(corrected_image)
        return corrected_images

    def correct_images_pairwise(self, filter_images, dark_images):
        """
        Corrects images by subtracting each filter image with its paired dark image.
        Only pairs up to the minimum number of images available.
        """
        n_images = min(len(filter_images), len(dark_images))
        corrected = []
        for i in range(n_images):
            img = filter_images[i]
            dark = dark_images[i]
            diff = np.abs(img.astype(np.int32) - dark.astype(np.int32))
            diff = np.clip(diff, 0, 2**14 - 1).astype(np.uint16)
            corrected.append(diff)
        return corrected

    def correct_images_with_average_dark(self, images, dark_frame):
        """
        Corrects images by subtracting the average dark frame from each image.
        """
        corrected = []
        for img in images:
            diff = np.abs(img.astype(np.int32) - dark_frame.astype(np.int32))
            diff = np.clip(diff, 0, 2**14 - 1).astype(np.uint16)
            corrected.append(diff)
        return corrected

    def generate_images(self, filter_pos, dark_pos, correction_mode="average"):
        """
        Loads and corrects images for a filter position using the specified dark correction mode.
        correction_mode: "average" (default) or "pairwise"
        """
        if filter_pos not in self.track_processor.image_data or dark_pos not in self.track_processor.image_data:
            print(f"No images found for filter position: {filter_pos} or dark position: {dark_pos}")
            return []

        # Flatten all images across degree positions for both filter and dark
        filter_images = []
        for images in self.track_processor.image_data[filter_pos].values():
            filter_images.extend(images)
        dark_images = []
        for images in self.track_processor.image_data[dark_pos].values():
            dark_images.extend(images)

        if correction_mode == "pairwise":
            corrected = self.correct_images_pairwise(filter_images, dark_images)
            print(f"Info: Using {len(corrected)} pairwise-corrected images for filter '{filter_pos}' and dark '{dark_pos}'.")
            return corrected
        else:
            if not dark_images:
                print("No dark images found for average dark subtraction.")
                return []
            dark_frame = np.mean(np.stack(dark_images), axis=0)
            corrected = self.correct_images_with_average_dark(filter_images, dark_frame)
            print(f"Info: Using {len(corrected)} images with average dark subtraction for filter '{filter_pos}'.")
            return corrected

    def generate_composite(self, filter_pos, dark_pos, correction_mode="average"):
        """
        Generates a composite image using the specified dark correction mode.
        """
        images = self.generate_images(filter_pos, dark_pos, correction_mode=correction_mode)
        if not images:
            return None
        composite = np.mean(np.stack(images), axis=0)
        return composite

    def plotComposite(self, filter_pos, dark_pos):
        """
        Generates and plots the composite image for a specified filter position.

        :param filter_pos: str, the filter position of the desired composite plot.
        :param dark_pos: str, the filter position used for dark frame correction.
        """
        composite_image = self.generate_composite(filter_pos, dark_pos)
        if composite_image is not None: # Checks if a valid composite image was generated.
            plt.imshow(composite_image)
            plt.axis("off")
            plt.show()
        else:
            print("No composite image to display.")

    def find_parabola_core(self, signal):
        """
        Calculates and plots the plateaus of each parabola of each core image

        This function identifies a central "core" region of a signal by finding the region around the peak where
        the signal is above a certain fraction of the peak value.

        :param signal: numpy array of values, the 1-D signal to analyze (e.g., a row or averaged rows of an image).
        Return: returns dictionary of related info of plateaus, containing:
            "peak_value": The maximum value in the signal.
            "peak_index": The index of the maximum value.
            "left_index": The index of the left boundary of the core region.
            "right_index": The index of the right boundary of the core region.
            "core_signal": The signal values within the core region.
            "core_x": The x-axis indices corresponding to the core region.
            "core_width": The width (number of points) of the core region.
        """
        peak_val = np.max(signal)
        half_max = peak_val / 1.15       # Calculates a threshold slightly below the peak to define the core (adjusted from 2 for a wider region).
        peak_idx = np.argmax(signal)

        # search to the left for the first point below half max
        left_idx = np.copy(peak_idx)
        while left_idx > 0 and signal[left_idx] > half_max: # Moves left as long as the index is within bounds and the signal is above the threshold.
            left_idx -= 1

        # search to the right for the first point below half max
        right_idx = np.copy(peak_idx)
        while right_idx < len(signal) - 1 and signal[right_idx] > half_max: # Moves right as long as the index is within bounds and the signal is above the threshold.
            right_idx += 1

        core_width = right_idx - left_idx # Calculates the width of the core region.
        core_signal = signal[left_idx:right_idx + 1] # Extracts the signal values within the identified core region.
        core_x = np.arange(left_idx, right_idx + 1) # Creates an array of x-axis indices corresponding to the core region.

        return { # Dictionary containing the calculated information about the core region.
            "peak_value": peak_val,
            "peak_index": peak_idx,
            "left_index": left_idx,
            "right_index": right_idx,
            "core_signal": core_signal,
            "core_x": core_x,
            "core_width": core_width
        }

    def calculate_FWHM(self, x_vals, y_vals):
        """
        Calculates the Full Width Half Max (FWHM)

        This function determines the width of a signal at half of its maximum value.

        :param x_vals: 1-D np array containing x-values over which FWHM should be calculated.
        :param y_vals: 1-D np array containing y-values over which FWHM should be calculated.

        :return fwhm_idx:   1-D np array containing the x-values where the y-values are greater than or equal to half of the maximum y-value. This effectively represents the width at half max.
        :return fwhm_y_vals: 1-D np array containing the y-values where the y-values are greater than or equal to half of the maximum y-value.
        """
        peak = np.max(y_vals)          # Finds the maximum value of the y-values.
        half_max = peak / 1.15        # Calculates half of the maximum value (adjusted for a broader region).
        fwhm_indices = np.argwhere(y_vals >= half_max).flatten() # Finds the indices where the y-values are greater than or equal to half the maximum and flattens the resulting array.

        return x_vals[fwhm_indices], y_vals[fwhm_indices] # Returns the x-values and corresponding y-values at or above half the maximum.

    def plot_parabola_cores(self, filter_pos, dark_pos, along_track_pos, smooth=True, core=True, window_length=61, polyorder=3):
        """
        Generates and plots the core (or FWHM region) of the cross-track signal for each image at a specified Along-Track row.

        This function extracts a cross-track profile (a row or an average of rows) from each corrected image then plots either
        the identified core or the full profile.

        :param filter_pos: str, the filter position to analyze.
        :param dark_pos: str, the dark frame filter position used for correction.
        :param along_track_pos: int, the along-track row index to extract the cross-track signal from each image (averaging a few rows around this index for better signal).
        :param smooth: bool, whether to apply Savitzky-Golay smoothing to the cross-track signal (default: True).
        :param core: bool, whether to plot only the identified "core" region (using FWHM calculation here) or the full signal (default: True, plotting the core).
        :param window_length: int, the window length for the Savitzky-Golay filter (must be odd and greater than polyorder, default: 61).
        :param polyorder: int, the polynomial order for the Savitzky-Golay filter (default: 3).
        """
        images = self.generate_images(filter_pos, dark_pos)
        if not images:
            print("No images to process for plotting.")
            return

        plt.figure(figsize=(14, 6))

        for idx, image in enumerate(images): # Iterates through each corrected image.
            # Determine bounds for averaging along-track rows
            row_start = max(along_track_pos - 10, 0) # Calculates the starting row index for averaging, ensuring it's not below 0.
            row_end = min(along_track_pos + 10 + 1, image.shape[0]) # Calculates the ending row index for averaging, ensuring it's not beyond the image height and adding 1 to include the upper bound.

            # saftey check
            if row_start >= row_end: # Checks if the averaging range is valid.
                print(f"Invalid range for image {idx}. Skipping")
                continue

            averaged_row = np.mean(image[row_start:row_end, :], axis=0) # Averages the pixel values across the selected along-track rows to get a 1D cross-track signal.
            x_vals = np.arange(len(averaged_row)) # Creates an array of x-axis values (pixel indices) for the cross-track signal.

            if smooth: # Checks if smoothing is enabled.
                if window_length >= len(averaged_row): # Adjust if row is too short for the specified window length.
                    window_length = len(averaged_row) - 1 if len(averaged_row) % 2 == 0 else len(averaged_row)
                averaged_row = savgol_filter(averaged_row, window_length=window_length, polyorder=polyorder) # Applies the Savitzky-Golay filter to smooth the cross-track signal.

            if core: # Checks if only the "core" region should be plotted.
                fwhm_x, fwhm_y = self.calculate_FWHM(x_vals, averaged_row)
                plt.plot(fwhm_x, fwhm_y, linewidth=2, label=f"Core Image data {idx+1}") # Plots the FWHM region.
            else: # If the full signal should be plotted.
                plt.plot(x_vals, averaged_row, label=f"Image {idx+1}", linewidth=1.5)


        plt.title(f"Averaged Along-Track Row {along_track_pos-10} to {along_track_pos+10}")
        plt.xlabel("Cross-Track Pixel Index")
        plt.ylabel("Digital Numbers (DN)")
        plt.grid(True, linestyle="dotted", alpha=0.5)
        plt.ylim(ymin=0)
        os.makedirs(os.path.dirname(parabola_save_path), exist_ok=True)
        plt.savefig(parabola_save_path)
        plt.show()

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
        """Removes data points where y_vals deviate from the mean by more than n_sigma standard deviations.

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

