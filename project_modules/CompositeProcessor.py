"""
__name__ =      CompositeProcessor.py
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
        """Correct images by subtracting the average dark frame from each image.

        This step aims to reduce the impact of sensor noise and biases present in the dark frame on the actual data images.
        Clipping the result to the valid data range (0 to 16383 for a 14-bit sensor) ensures that pixel values remain within the sensor's capabilities.

        :param images: list of np.ndarray, a list of images (as NumPy arrays) to be corrected.
        :param dark_frame: np.ndarray or None, the average dark frame to subtract. If None, no correction is applied.
        :return: list of np.ndarray, a list of dark frame corrected images as NumPy arrays.
        """
        corrected_images = []
        for image in images: # Iterates through each image in the input list.
            if dark_frame is not None:
                # Converts both the image and the dark frame to 32-bit integers to prevent overflow during subtraction.
                # Subtracts the dark frame from the image. Clips the resulting pixel values to the range [0, 16383] (for a 14-bit sensor: 2^14 - 1).
                # Converts the clipped result back to 16-bit unsigned integers (uint16) to maintain a common data type,
                # If dark_frame is None, the original image is kept without correction.
                corrected_image = np.clip(image.astype(np.int32) - dark_frame.astype(np.int32), 0, 2**14 - 1).astype(np.uint16)
            else:
                corrected_image = image # If dark_frame is None, no correction is applied.
            corrected_images.append(corrected_image) # Appends the corrected image to the list.

        return corrected_images

    def generate_images(self, filter_pos, dark_pos):
        """Generate corrected images for a filter position using a dark frame,
        ensuring that each degree position contributes the same number of images,
        equal to the degree position with the least number of images.

        :param filter_pos: str, the filter position for which to generate corrected images.
        :param dark_pos: str, the filter position used to compute the average dark frame.
        :return: list of np.ndarray, a list of dark frame corrected images for the specified filter position,
                 with an equal number of images contributed from each degree position.
                 Returns an empty list if no images are found for the filter position.
        """
        if filter_pos not in self.track_processor.image_data:
            print(f"No images found for filter position: {filter_pos}")
            return []

        dark_frame = self.compute_average_dark_frame(dark_pos)
        all_images = []
        min_images = float('inf')

        # Find the minimum number of images across all degree positions
        for degree_pos, images in self.track_processor.image_data[filter_pos].items():
            min_images = min(min_images, len(images))

        if min_images == float('inf') or min_images == 0: # Added check for min_images == 0
            print(f"Warning: No images found for filter position '{filter_pos}'.")
            return []

        # Collect an equal number of corrected images from each degree position
        for degree_pos, images in self.track_processor.image_data[filter_pos].items():
            # Take only the first 'min_images' from each degree position
            images_to_use = images[:min_images]
            corrected_images = self.correct_images_with_dark_frame(images_to_use, dark_frame)
            all_images.extend(corrected_images)

        print(f"Info: Using {min_images} images from each degree position for filter '{filter_pos}'.")
        return all_images

    def generate_composite(self, filter_pos, dark_pos):
        """Generate a composite image by averaging all the dark frame corrected images for a given filter position.

        This process effectively combines multiple images to reduce noise and highlight common features.

        :param filter_pos: str, the filter position for which to generate the composite image.
        :param dark_pos: str, the filter position used to compute the average dark frame for correction.
        :return: np.ndarray or None, the composite image as a NumPy array (the average of the corrected images). Returns None if no corrected images are available.
        """
        images = self.generate_images(filter_pos, dark_pos)
        # If the list of corrected images is not empty, it converts it to a NumPy array and calculates the mean along the first axis (averaging all images pixel-wise) to create the composite image. If the list is empty, it returns None.
        return np.mean(np.asarray(images), axis=0) if images else None

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
        plt.grid(True, linestyle="--", alpha=0.5)
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

    def plot_flatfield(self, filter_pos, dark_pos, num_sigma, along_track_pos, window_length=61, polyorder=3):
        """
        Combines all images for a given filter, performs some initial filtering based on a fraction of the maximum,
        averages the resulting cross-track signals, applies a sigma filter for outlier removal, smooths the data,
        fits a quadratic curve to the smoothed data, and plots the original data, filtered data, smoothed data,
        and the quadratic fit. This function aims to generate and visualize a "flatfield" profile for a specific filter.

        :param filter_pos: str, the filter position to analyze.
        :param dark_pos: str, the dark frame filter position used for correction.
        :param num_sigma: float, the number of standard deviations to use for the sigma filter to remove outliers.
        :param along_track_pos: int, the along-track row index around which to average for extracting the cross-track signal from each image.
        :param window_length: int, the window length for the Savitzky-Golay filter used for smoothing (must be odd and greater than polyorder, default: 61).
        :param polyorder: int, the polynomial order for the Savitzky-Golay filter (default: 3).
        """
        images = self.generate_images(filter_pos, dark_pos) # Gets the list of dark frame corrected images for the specified filter.
        if not images: # Checks if there are any images to process.
            print("No images to process for plotting.")
            return # Exits if no images are found.

        avg_rows = None # Initializes a variable to store the averaged cross-track rows from each image.
        for idx, image in enumerate(images): # Iterates through each corrected image.
            # Determine bounds for averaging along-track rows
            row_start = max(along_track_pos - 10, 0) # Calculates the starting row index for averaging, ensuring it's not below 0.
            row_end = min(along_track_pos + 10 + 1, image.shape[0])  # Calculates the ending row index for averaging, ensuring it's not beyond the image height and adding 1 to include the upper bound.

            # Safety check
            if row_start >= row_end: # Checks if the averaging range is valid.
                print(f"Invalid range for image {idx}. Skipping.")
                continue # Skips to the next image if the range is invalid.

            averaged_row = np.mean(image[row_start:row_end, :], axis=0) # Averages the pixel values across the selected along-track rows to get a 1D cross-track signal.
            for col in range(averaged_row.shape[0]): # Iterates through each pixel (column) in the averaged row.
                #-- filter out any data that is less than the maximum value of the current averaged row. assign to NaN to help with np.nanmean later on
                if averaged_row[col] < np.nanmax(averaged_row) / 2.0:#2: # If the pixel value is less than half of the maximum value in the current averaged row...
                    averaged_row[col] = np.nan # ...it's set to NaN. This is a preliminary filtering step to remove low-signal regions.

            if avg_rows is None: # If this is the first averaged row.
                avg_rows = averaged_row # Initialize avg_rows with the current averaged row.
            else: # For subsequent averaged rows.
                avg_rows = np.vstack((avg_rows, averaged_row)) # Stacks the current averaged row vertically with the previously accumulated averaged rows.

        combined_row = np.nanmean(avg_rows, axis = 0) # Calculates the mean of all the stacked averaged rows, ignoring NaN values. This gives a single, combined cross-track profile.
        if combined_row is None or np.all(np.isnan(combined_row)):  # No valid data to plot
            print("No valid data to combine for flatfield plot.")
            return # Exits if there's no valid data to combine and plot.

        x_vals = np.arange(len(combined_row)) # Creates an array of x-axis values (pixel indices) for the combined cross-track signal.

        # Plot the combined data
        fig,ax2 = plt.subplots(1,1,num=2) # Creates a new Matplotlib figure and a subplot.
        ax2.plot(x_vals, combined_row, 'x', color='red', label="Rejected Points", linewidth=1.5, markersize=2.75) # Plots the combined row with 'x' markers in red, representing points that were likely filtered out as low signal (NaNs).

        # num_sigma = 1.0
        x_vals_filtered, combined_row_filtered = self.sigma_filter(x_vals, combined_row, num_sigma) # Applies the sigma filter to remove outliers from the combined row.
        ax2.plot(x_vals_filtered, combined_row_filtered, '.', color='green', label=f"Filtered Signal at {num_sigma}-sigma", linewidth=1.5) # Plots the sigma-filtered signal with '.' markers in green.

        if len(combined_row_filtered) < window_length:  # Adjust if row is too short
            window_length_adj = len(combined_row_filtered) - 1
            if window_length_adj % 2 == 0:
                window_length_adj -= 1
            if window_length_adj <= polyorder:
                window_length_adj = polyorder + 2 if (polyorder + 2) % 2 != 0 else polyorder + 3
            window_length = window_length_adj
            if window_length <= 0: # Ensure window_length is positive
                print("Window length for smoothing is too small for filtered data, skipping smoothing.")
                combined_row_smoothed_filtered = combined_row_filtered
            else:
                combined_row_smoothed_filtered = savgol_filter(combined_row_filtered, window_length=window_length, polyorder=polyorder)
        else:
            combined_row_smoothed_filtered = savgol_filter(combined_row_filtered, window_length=window_length, polyorder=polyorder)

        if len(combined_row) < window_length:  # Adjust if row is too short for original combined_row
             window_length_adj_orig = len(combined_row) - 1
             if window_length_adj_orig % 2 == 0:
                 window_length_adj_orig -= 1
             if window_length_adj_orig <= polyorder:
                 window_length_adj_orig = polyorder + 2 if (polyorder + 2) % 2 != 0 else polyorder + 3
             window_length_orig = window_length_adj_orig
             if window_length_orig <= 0: # Ensure window_length is positive
                 print("Window length for smoothing is too small for original data, skipping smoothing.")
                 combined_row_smoothed_orig = combined_row
             else:
                 combined_row_smoothed_orig = savgol_filter(combined_row, window_length=window_length_orig, polyorder=polyorder)
        else:
            combined_row_smoothed_orig = savgol_filter(combined_row, window_length=window_length, polyorder=polyorder)


        ax2.plot(x_vals, combined_row_smoothed_orig, color='orange', label="Smoothed Signal With Noise", linewidth=1.5, linestyle='--') # Plots the smoothed signal with potential noise (from NaNs) with a dashed orange line.
        ax2.plot(x_vals_filtered, combined_row_smoothed_filtered, color='black', label="Smoothed Signal", linewidth=1.5) # Plots the smoothed, sigma-filtered signal with a solid black line.

        _, _, popt_coeffs = self.quadratic_fit(x_vals_filtered, combined_row_smoothed_filtered) # Fits a quadratic curve to the smoothed, sigma-filtered data.
        ax2.plot(x_vals_filtered, self.parabola_func(x_vals_filtered, *popt_coeffs), color='red', label="Envelope, O(x^2)", linewidth=1.5) # Plots the quadratic fit with a solid red line, labeled as the envelope.

        ax2.set_title(f"Flatfield Plot: Filter {filter_pos}, Row {row_start}-{row_end-1}") # Sets the title of the plot.
        ax2.set_xlabel("Cross-Track Pixel Index") # Labels the x-axis.
        ax2.set_ylabel("Digital Numbers (DN)") # Labels the y-axis.
        ax2.grid(True, linestyle="--", alpha=0.5) # Adds a grid to the plot.
        ax2.legend() # Displays the legend to identify the different plotted lines.
        ax2.set_ylim(ymin=0) # Sets the lower limit of the y-axis to 0.
        os.makedirs(os.path.dirname(flatfield_plot_save_path), exist_ok=True) # Create the directory if it doesn't exist
        plt.savefig(flatfield_plot_save_path) # Saves the generated plot to the specified path.
        plt.show() # Displays the plot.
