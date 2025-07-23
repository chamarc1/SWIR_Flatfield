# SWIR Image Processing Pipeline for Scientific Data

This project provides a Python-based pipeline for processing scientific SWIR image data, specifically designed for handling multi-frame acquisitions across different experimental conditions. The core functionality includes dark frame correction, flatfield generation and application, composite image creation, flatfiled generation and tools for analyzing cross-track signal profiles.

## Project Structure

The project is organized into the following key Python modules:

* **`Main.py`**: This script is intended as the entry point for running the image processing pipeline. It will import and utilize the classes and functions defined in the other modules to load data, perform processing, and save results.
* **`CompositeProcessor.py`**: Contains the `CompositeProcessor` class, which handles the core image processing tasks. This includes:
    * Loading and managing image data organized by filter and degree.
    * Calculating average dark frames.
    * Correcting images for dark frames.
    * Generating composite images by averaging corrected frames.
    * Generating and applying flatfield corrections.
    * Analyzing and plotting cross-track signal profiles, including core identification and FWHM calculation.
    * Fitting quadratic curves to data.
    * Applying sigma filtering for outlier removal.
* **`ImageProcessor.py`**: Contains the `ImageProcessor` class, responsible for the initial loading and organization of image data from a specified directory structure. It reads image files and stores them in a structured dictionary format based on the directory hierarchy (filter and degree).
* **`Constants.py`**: Defines various constants used throughout the project, such as default file paths for saving generated plots (e.g., composite images, parabola plots, flatfield images).

## Functionality

The project offers the following functionalities:

* **Data Loading and Organization**: Efficiently loads image data from a directory structure, organizing it by experimental parameters like filter position and degree.
* **Dark Frame Correction**: Calculates an average dark frame from specified dark exposures and subtracts it from the science and flatfield images to reduce sensor noise and bias.
* **Flatfield Correction**: Generates a full-image flatfield from dedicated flatfield exposures to correct for pixel sensitivity variations and uneven illumination. This flatfield can then be applied to science images.
* **Composite Image Generation**: Creates high signal-to-noise ratio composite images by averaging multiple dark and flatfield corrected frames acquired under the same experimental conditions.
* **Cross-Track Signal Analysis**: Provides tools to extract and analyze 1D signal profiles (e.g., along a specific row or averaged rows) from the 2D images. This includes:
    * Identifying the "core" region of a signal peak.
    * Calculating the Full Width at Half Maximum (FWHM).
    * Plotting the signal and its core/FWHM.
* **Curve Fitting**: Implements quadratic (parabolic) fitting to analyze trends in the data.
* **Outlier Removal**: Utilizes sigma filtering to identify and remove data points that deviate significantly from the mean.
* **Visualization**: Includes plotting functions to display composite images, cross-track signal profiles, and flatfield images.

## Flatfield Characterization and Application

### Flatfield Characterization

The pipeline now supports robust pixel-by-pixel flatfield characterization, following best practices from the AirHARP2 SWIR calibration protocol:

- **Composite Generation:** Uses both cross-track and along-track uniform-illumination images to generate composite images.
- **Averaging and Smoothing:** Combines and optionally smooths these composites to create a high-SNR flatfield reference.
- **Normalization:** The flatfield is normalized to a mean of 1, ensuring that only pixel-to-pixel sensitivity variations are corrected.
- **Defective Pixel Handling:** Pixels with abnormally high or low response (beyond 3 standard deviations from the mean) are automatically replaced with the local median value.
- **Metadata Logging:** Each flatfield characterization saves a metadata dictionary (including date, filter positions, smoothing parameters, and statistics) alongside the flatfield array for full reproducibility.
- **Saving:** The flatfield and its metadata are saved as a `.npy` or `.npz` file for future use.

### Applying Flatfield Correction

- **Correction Workflow:** When raw science images are available, the pipeline can load the saved flatfield and metadata, subtract the appropriate dark frame, and apply the flatfield correction pixel-by-pixel.
- **Reproducibility:** The correction step logs which flatfield was used and its parameters, ensuring traceability for all processed data.

### Example Usage

```python
from project_modules.FlatfieldProcessor import FlatfieldProcessor

# Characterize and save flatfield (run once per calibration session)
flatfield_processor = FlatfieldProcessor(wheel_pos="050")
flatfield = flatfield_processor.characterize_pixel_response(smoothing_sigma=1.0, save_path="flatfield_050.npy")

# Later, apply flatfield to raw images
corrected_image, metadata = flatfield_processor.apply_flatfield_to_raw(raw_image, "flatfield_050.npy", dark_frame)
```

### Logging and Metadata

- All major processing steps print informative log messages to the console.
- Flatfield files include metadata such as creation date, filter positions, smoothing parameters, and summary statistics.

---

**These improvements ensure your pipeline is fully aligned with current best practices for SWIR sensor calibration and is ready for reproducible, quantitative scientific analysis.**

## Quick Start Guide

### What is Flatfield Correction?

A flatfield correction removes spatial variations in sensor response, making your images more uniform and improving data quality. Think of it like correcting for uneven lighting in a photograph - some parts of the sensor might be slightly more or less sensitive than others, and this tool creates a correction to even that out.

### Basic Usage

To process images for a specific filter position:

```bash
python Main.py --wheel_pos pos1
```

With custom smoothing:

```bash
python Main.py --wheel_pos pos1 --num_sigma 2.0    # More smoothing
python Main.py --wheel_pos pos1 --num_sigma 0.5    # Less smoothing  
python Main.py --wheel_pos pos1 --num_sigma 0      # No smoothing
```

### Understanding the Parameters

#### --wheel_pos (Required)
- **What it is**: The filter wheel position you want to process
- **Example values**: "pos1", "pos2", "pos3", "pos4" (based on your Constants.py setup)
- **Why needed**: Different filters may need different corrections

#### --num_sigma (Optional)
- **What it is**: Controls how much smoothing is applied to the correction
- **Default**: 1.0
- **Higher values** (e.g., 2.0): More smoothing, gentler correction
- **Lower values** (e.g., 0.5): Less smoothing, preserves more detail
- **Zero**: No smoothing at all

## Detailed Setup and Usage

### 1. Installation

* Ensure you have Python 3.x installed on your system.
* Install the required Python libraries:
    ```bash
    pip install numpy matplotlib scipy pillow pandas
    ```
* Place the `CompositeProcessor.py`, `FlatfieldProcessor.py`, `ImageProcessor.py`, and `Constants.py` files in your project directory.

### 2. Data Organization

* Organize your image data in a directory structure that the `ImageProcessor` can understand. Typically, this involves a main directory containing subdirectories for each filter position, and within each filter directory, subdirectories for different degree settings. Ensure your dark frames and flatfield frames are placed in appropriately named filter positions (e.g., "dark", "flat"). This structure may be updated with files from NASA testing.

### 3. Configuration (`Constants.py`)

* Review and modify the paths defined in `Constants.py` to specify where you want the generated plots and flatfield files to be saved.

### 4. Running the Pipeline (`Main.py`)

* The main script is run from the command line and accepts arguments for the filter wheel position and optional Gaussian smoothing:
    ```bash
    python Main.py --wheel_pos <FILTER_WHEEL_POSITION> [--num_sigma <SMOOTHING_SIGMA>]
    ```

* Examples:
    ```bash
    python Main.py --wheel_pos pos1 --num_sigma 1.5
    python Main.py --wheel_pos pos2
    python Main.py --wheel_pos pos3 --num_sigma 0    # No smoothing
    ```

* The script will:
    - Instantiate a `FlatfieldProcessor` for the specified wheel position.
    - Characterize the pixel-to-pixel flatfield response using composite images from both cross-track and along-track directions.
    - Apply optional smoothing and handle defective pixels.
    - Save the resulting flatfield and metadata for future use.

### 5. Applying Flatfield to Raw Images

* Once you have raw images and a saved flatfield, you can use the `apply_flatfield_to_raw` method in `FlatfieldProcessor` to correct your data (see the "Flatfield Characterization and Application" section above for an example).

## What the Tool Does

1. **Loads Images**: Reads in multiple SWIR images from the specified filter position
2. **Extracts Profiles**: Analyzes how brightness varies across the image
3. **Fits Envelopes**: Creates smooth curves that follow the brightness patterns
4. **Creates Correction**: Generates a 2D flatfield correction
5. **Shows Results**: Displays plots showing the correction and analysis

## Output Files

The tool creates several output files in the `Images/` directory:

- **flatfield.png**: The final flatfield correction image
- **flatfield_plot.png**: Analysis plots showing how the correction was created
- **along_track.png**: Profile analysis in the along-track direction
- **along_track_core.png**: Core region analysis for along-track
- **composite.png**: Combined image analysis

## Understanding the Plots

### Profile Plots
- Show how brightness varies across the image
- Blue lines: Cross-track direction (left-to-right across the image)
- Red lines: Along-track direction (top-to-bottom of the image)

### 3D Plots
- Show the overall shape of the flatfield correction
- Higher areas appear brighter in the final correction

### Envelope Plots
- Show the smooth curves fitted to the brightness profiles
- These curves are used to create the final correction

## Troubleshooting

### "No images found for filter position"
- Check that your filter position exists in the data
- Verify the Constants.py file has the correct mappings
- Ensure your data directory structure matches what the code expects

### "Error during processing"
- Try different smoothing values (--num_sigma)
- Check that input images are readable and in the correct format
- Ensure you have write permissions in the output directory
- Verify that all required dependencies are installed

### Plots look wrong
- Try adjusting the smoothing parameter
- Check that input images are properly calibrated
- Verify dark frame corrections are working
- Make sure optical center coordinates are correct for your data

### Processing Multiple Positions
```bash
python Main.py --wheel_pos pos1
python Main.py --wheel_pos pos2  
python Main.py --wheel_pos pos3
python Main.py --wheel_pos pos4
```

## Tips for Best Results

1. **Start with default settings** - Try `--num_sigma 1.0` first
2. **Examine the plots** - Look at the generated images to understand your data
3. **Adjust smoothing** - If correction looks too rough, increase num_sigma; if too smooth, decrease it
4. **Check input data** - Make sure your images are properly dark-corrected
5. **Verify output** - Always examine the flatfield correction before applying to science data
6. **Use consistent parameters** - Keep the same processing parameters for related datasets

## For Developers

- The main processing happens in `FlatfieldProcessor.py`
- Image loading and dark correction in `CompositeProcessor.py`
- Configuration settings in `Constants.py`
- Individual image processing in `ImageProcessor.py`
- All methods include comprehensive docstrings and beginner-friendly comments

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above first
2. Look at the generated plots to understand what's happening
3. Try different parameter values (especially --num_sigma)
4. Verify your data organization matches the expected structure
5. Check that all file paths in Constants.py are correct
6. Ensure you have all required Python packages installed

## Contributing

This tool is designed to be accessible to users with varying levels of coding experience. Don't hesitate to experiment with different settings to understand how they affect your results!

Contact Charlemagne Marc (email: chamrc1@umbc.edu) for any contribution inquiries, bug reports, or feature requests.