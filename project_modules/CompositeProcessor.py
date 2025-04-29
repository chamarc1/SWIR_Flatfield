#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
import os                             # Needed for locating images/files
import numpy as np                    # Images converted to NumPy arrays for data manipulation
import matplotlib as mpl              # Needed for plotting
import matplotlib.pyplot as plt       # Needed for plotting
from scipy.signal import savgol_filter# Needed for curve fitting
from scipy.optimize import curve_fit  # Needed for curve fitting
from project_modules.ImageProcessor import ImageProcessor
from project_modules.Constants import composite_save_path, parabola_save_path, flatfield_save_path

#----------------------------------------------------------------------------
#-- GLOBALS
#----------------------------------------------------------------------------
mpl.use("Qt5Agg")

#----------------------------------------------------------------------------
#-- plot_composite
#----------------------------------------------------------------------------
def plot_composite(composite_image):
    """plots the composite image from data from both cross and along tracks"""
    if composite_image is not None:
        plt.imshow(composite_image)
        plt.axis("on")  # Turn on axis to see labels

        # Set title and labels
        plt.title("Composite")
        plt.xlabel('Cross-Track Pixels')
        plt.ylabel('Along-Track Pixels')
        os.makedirs(os.path.dirname(composite_save_path), exist_ok=True)  # Create the directory if it doesn't exist
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
        Initializes the processor with list of images

        :param track_dir: track directory
        :param metadata: meta data of temperatures of sensor during imaging
        """
        self.track_dir = track_dir
        self.metadata = metadata
        self.track_processor = ImageProcessor(track_dir)

    def compute_average_dark_frame(self, dark_pos):
        """Compute the average dark frame from all images"""
        dark_images = []
        for degree_pos, images in self.track_processor.image_data.get(dark_pos, {}).items():
            dark_images.extend(images)
        return np.mean(np.asarray(dark_images), axis=0) if dark_images else None
    
    def correct_images_with_dark_frame(self, images, dark_frame):
        """Correct images by subtracting the dark frame."""
        corrected_images = []
        for image in images:
            corrected_images.append(np.clip(image - dark_frame, 0, None) if dark_frame is not None else image)
        return corrected_images

    def generate_images(self, filter_pos, dark_pos):
        """Generate corrected images for a filter position using a dark frame."""
        if filter_pos not in self.track_processor.image_data:
            print(f"No images found for filter position: {filter_pos}")
            return []

        dark_frame = self.compute_average_dark_frame(dark_pos)
        all_images = []
        for images in self.track_processor.image_data[filter_pos].values():
            corrected_images = self.correct_images_with_dark_frame(images, dark_frame)
            all_images.extend(corrected_images)
        return all_images

    def generate_composite(self, filter_pos, dark_pos):
        """Generate a composite image by averaging corrected images."""
        images = self.generate_images(filter_pos, dark_pos)
        return np.mean(np.asarray(images), axis=0) if images else None
    
    def plotComposite(self, filter_pos, dark_pos):
        """
        Generates and plots the composite image.

        :param filter_pos: filter position of desired composite plot
        """
        composite_image = self.generate_composite(filter_pos, dark_pos)
        if composite_image is not None:
            plt.imshow(composite_image)
            plt.axis("off")
            plt.show()
        else:
            print("No composite image to display.")

    def find_parabola_core(self, signal):
        peak_val = np.max(signal)
        half_max = peak_val / 1.2
        peak_idx = np.argmax(signal)

        # search to the left for the first point below half max
        left_idx = np.copy(peak_idx)
        while left_idx > 0 and signal[left_idx] > half_max:
            left_idx -= 1
        
        # search to the right for the first point below half max
        right_idx = np.copy(peak_idx)
        while right_idx < len(signal) - 1 and signal[right_idx] > half_max:
            right_idx += 1

        core_width = right_idx - left_idx
        core_signal = signal[left_idx:right_idx + 1]
        core_x = np.arange(left_idx, right_idx + 1)

        return {
            "peak_value": peak_val,
            "peak_index": peak_idx,
            "left_index": left_idx,
            "right_index": right_idx,
            "core_signal": core_signal,
            "core_x": core_x,
            "core_width": core_width
        }

    def plot_parabola_cores(self, filter_pos, dark_pos, along_track_pos, smooth=True, core=True, window_length=61, polyorder=3):
        """
        Generates and plots the core (parabola) of each image at a specified Along-Track row.
        
        :param filter_pos: Filter position to analyze
        :param dark_pos: Dark frame filter position
        :param along_track_pos: The along-track row index to extract from each image
        :param smooth: Whether to apply Savitzky-Golay smoothing
        :param window_length: Window length for smoothing (must be odd and > polyorder)
        :param polyorder: Polynomial order for smoothing
        """
        images = self.generate_images(filter_pos, dark_pos)
        if not images:
            print("No images to process for plotting.")
            return

        plt.figure(figsize=(14, 6))

        for idx, image in enumerate(images):
            # Determine bounds for averaging
            row_start = max(along_track_pos - 10, 0)
            row_end = min(along_track_pos + 10 + 1, image.shape[0]) # +1 to include upper bound

            # saftey check
            if row_start >= row_end:
                print(f"Invalid range for image {idx}. Skipping")
                continue

            averaged_row = np.mean(image[row_start:row_end, :], axis=0)
            x_vals = np.arange(len(averaged_row))

            if smooth:
                if window_length >= len(averaged_row): # Adjust if row is too short
                    window_length = len(averaged_row) - 1 if len(averaged_row) % 2 == 0 else len(averaged_row)
                averaged_row = savgol_filter(averaged_row, window_length=window_length, polyorder=polyorder)

            if core:
                core_data = self.find_parabola_core(averaged_row)
                plt.plot(core_data["core_x"], core_data["core_signal"], linewidth=2, label=f"Core Image data {idx+1}")
            else:
                plt.plot(x_vals, averaged_row, label=f"Image {idx+1}", linewidth=1.5)


        plt.title(f"Averaged Along-Track Row {along_track_pos-10} to {along_track_pos+10}")
        plt.xlabel("Cross-Track Pixel Index")
        plt.ylabel("Digital Numbers (DN)")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.ylim(ymin=0)
        os.makedirs(os.path.dirname(parabola_save_path), exist_ok=True)  # Create the directory if it doesn't exist
        plt.savefig(parabola_save_path)
        plt.show()

    def parabola_func(self, x, constant, linear, quadratic):
        return constant + linear * x + quadratic * (x**2)

    def quadratic_fit_temp(self, x_vals, y_vals):
        """temp quadratic fit"""
        # Remove NaN values from x_vals and y_vals
        valid_indices = ~np.isnan(y_vals)
        x_vals = x_vals[valid_indices]
        y_vals = y_vals[valid_indices]

        # Perform the least-squares fitting
        popt, pcov = curve_fit(self.parabola_func, x_vals, y_vals)
        constant = popt[0]
        linear = popt[1]
        quadratic = popt[2]
        constant_err = np.sqrt(pcov[0][0])
        linear_err = np.sqrt(pcov[1][1])
        quadratic_err = np.sqrt(pcov[2][2])

        y_fit = constant + (linear * x_vals) + (quadratic * (x_vals**2))

        # Report values to shell
        print(f"constant = {constant:.7f} ohm")
        print(f"constant std. error = {constant_err:.7f} ohm")
        print(f"linear = {linear:.2E} ohm/T")
        print(f"linear std. error = {linear_err:.2E} ohm/T")
        print(f"quadratic = {quadratic:.4E} ohm/T^2")
        print(f"quadratic std. error = {quadratic_err:.2E} ohm/T^2")

        return x_vals, y_fit

    def quadratic_fit(self, x_vals, y_vals):
        """
        Fits a quadratic curve (parabola) to the given x and y values, ignoring NaN values.

        :param x_vals: Array of x values
        :param y_vals: Array of y values
        :return: x_fit, y_fit representing the fitted curve
        """
        # Remove NaN values from x_vals and y_vals
        valid_indices = ~np.isnan(y_vals)
        x_vals_clean = x_vals[valid_indices]
        y_vals_clean = y_vals[valid_indices]

        if len(x_vals_clean) < 3:  # Need at least three points for quadratic fitting
            print("Not enough valid data for quadratic fitting.")
            return x_vals, y_vals

        # Fit a quadratic polynomial (degree 2)
        coeffs = np.polyfit(x_vals_clean, y_vals_clean, deg=2)

        # Generate fitted y values using the polynomial
        x_fit = np.linspace(min(x_vals_clean), max(x_vals_clean), num=300)
        y_fit = np.polyval(coeffs, x_fit)

        print(np.poly1d(coeffs))

        return x_fit, y_fit
    
    def sigma_filter(self, x_vals, y_vals, n_sigma):
        """Removes data points where y_vals deviate from the mean by more than n_sigma std deviation"""
        # Remove NaN values from x_vals and y_vals
        valid_indices = ~np.isnan(y_vals)
        x_vals_clean = x_vals[valid_indices]
        y_vals_clean = y_vals[valid_indices]

        mean_y = np.mean(y_vals_clean)
        std_y = np.std(y_vals_clean, mean=mean_y)

        # mask = np.abs(y_vals_clean - mean_y) <= n_sigma * std_y
        mask = (y_vals_clean >= mean_y - n_sigma * std_y) & (y_vals_clean <= mean_y + n_sigma * std_y) 

        return x_vals_clean[mask], y_vals_clean[mask]

    def plot_flatfield(self, filter_pos, dark_pos, num_sigma, along_track_pos, window_length=61, polyorder=3):
        """
        Combines all images for a given filter and plots averaged along-track signal data.
        
        :param filter_pos: Filter position to analyze
        :param dark_pos: Dark frame filter position
        :param along_track_pos: The along-track row index to extract from each image
        :param smooth: Whether to apply Savitzky-Golay smoothing
        :param core: Whether to plot just the parabola core
        :param window_length: Window length for smoothing (must be odd and > polyorder)
        :param polyorder: Polynomial order for smoothing
        """
        images = self.generate_images(filter_pos, dark_pos)
        if not images:
            print("No images to process for plotting.")
            return

        avg_rows = None
        for idx, image in enumerate(images):
            # Determine bounds for averaging
            row_start = max(along_track_pos - 10, 0)
            row_end = min(along_track_pos + 10 + 1, image.shape[0])  # +1 to include upper bound

            # Safety check
            if row_start >= row_end:
                print(f"Invalid range for image {idx}. Skipping.")
                continue

            averaged_row = np.mean(image[row_start:row_end, :], axis=0)
            for col in range(averaged_row.shape[0]):
                #-- filter out any data that is less than the maximum value of the current averaged row. assign to NaN to help with np.nanmean later on
                if averaged_row[col] < np.nanmax(averaged_row) / 2:
                    averaged_row[col] = np.nan
            
            if avg_rows is None:
                avg_rows = averaged_row
            else:
                avg_rows = np.vstack((avg_rows, averaged_row))
            
        combined_row = np.nanmean(avg_rows, axis = 0)
        if combined_row is None:  # No valid data to plot
            print("No valid data to combine.")
            return

        x_vals = np.arange(len(combined_row))

        # Plot the combined data
        fig,ax2 = plt.subplots(1,1,num=2)
        ax2.plot(x_vals, combined_row, 'x', color='red', label="Rejected Points", linewidth=1.5, markersize=2.75)

        # num_sigma = 1.0
        x_vals_filtered, combined_row_filtered = self.sigma_filter(x_vals, combined_row, num_sigma)
        ax2.plot(x_vals_filtered, combined_row_filtered, '.', color='green', label=f"Filtered Signal at {num_sigma}-sigma", linewidth=1.5)
        
        if window_length >= len(combined_row_filtered):  # Adjust if row is too short
            window_length = len(combined_row_filtered) - 1 if len(combined_row_filtered) % 2 == 0 else len(combined_row_filtered)
        combined_row_filtered = savgol_filter(combined_row_filtered, window_length=window_length, polyorder=polyorder)
        if window_length >= len(combined_row):  # Adjust if row is too short
            window_length = len(combined_row) - 1 if len(combined_row) % 2 == 0 else len(combined_row)
        combined_row = savgol_filter(combined_row, window_length=window_length, polyorder=polyorder)
        ax2.plot(x_vals, combined_row, color='orange', label="Smoothed Signal With Noise", linewidth=1.5, linestyle='--')
        ax2.plot(x_vals_filtered, combined_row_filtered, color='black', label="Smoothed Signal", linewidth=1.5)

        # quadratic_fit_x, quadratic_fit_y = self.quadratic_fit(x_vals_filtered, combined_row_filtered)
        quadratic_fit_x, quadratic_fit_y = self.quadratic_fit_temp(x_vals_filtered, combined_row_filtered)
        ax2.plot(quadratic_fit_x, quadratic_fit_y, color='red', label="Envelope, O(x^2)", linewidth=1.5)

        ax2.set_title(f"Flatfield Plot: Filter {filter_pos}, Row {row_start}-{row_end-1}")
        ax2.set_xlabel("Cross-Track Pixel Index")
        ax2.set_ylabel("Digital Numbers (DN)")
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend()
        ax2.set_ylim(ymin=0)
        os.makedirs(os.path.dirname(parabola_save_path), exist_ok=True)  # Create the directory if it doesn't exist
        plt.savefig(flatfield_save_path)
        plt.show()
