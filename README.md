# SWIR Flatfield Processing Pipeline

This project provides a comprehensive Python-based pipeline for processing Short-Wave Infrared (SWIR) images to generate high-quality flatfield corrections. The pipeline is specifically designed for the AirHARP2 SWIR sensor calibration, implementing advanced quadratic envelope fitting techniques to model and correct illumination variations.

## What This Tool Does

The pipeline automatically processes SWIR images from all four filter wheel positions and creates detailed flatfield corrections that remove spatial variations in sensor response. It uses sophisticated analysis techniques including:

- **Quadratic envelope fitting** to model illumination patterns
- **Cross-track and along-track profile extraction** at the optical center
- **Sigma filtering** for robust outlier removal
- **Savitzky-Golay smoothing** for noise reduction
- **2D flatfield map generation** with normalization to the optical center

## Project Structure

The project consists of four main Python modules:

### Core Processing Modules

* **`Main.py`**: Entry point that processes all filter positions (pos1-pos4) automatically. Run this script to generate flatfield corrections for all positions with a single command.

* **`FlatfieldProcessor.py`**: The heart of the pipeline containing the `FlatfieldProcessor` class with methods for:
    - Extracting brightness profiles from cross-track and along-track directions
    - Fitting quadratic envelopes to model illumination gradients
    - Generating 2D flatfield correction maps
    - Creating comprehensive visualization plots
    - Applying flatfield corrections to raw images

* **`CompositeProcessor.py`**: Contains the `CompositeProcessor` class for:
    - Loading and organizing image data by filter position and degree
    - Computing average dark frames for noise correction
    - Generating composite images from multiple exposures
    - Managing dark frame subtraction workflows

* **`ImageProcessor.py`**: Handles low-level image operations:
    - Loading images from directory structures
    - Reading metadata from CSV files
    - Converting between image formats
    - Managing file paths and organization

### Configuration

* **`Constants.py`**: Defines system configuration including:
    - File paths for input data and output plots
    - Filter position mappings for different wavelengths
    - Dark frame position associations
    - Optical center coordinates
    - Mathematical functions for curve fitting

## Current Filter Configuration

The pipeline is configured for four filter positions:

- **pos1**: 1.57μm filter (FILTPOS_050)
- **pos2**: 1.55μm filter (FILTPOS_090) 
- **pos3**: 1.38μm filter (FILTPOS_130)
- **pos4**: Open position (FILTPOS_169)

Each position has associated dark frames and specific integration times optimized for the target wavelength.

## Quick Start Guide

### What This Tool Does

The flatfield processing pipeline:

1. **Analyzes Images**: Loads SWIR images from all four filter positions automatically
2. **Extracts Profiles**: Analyzes brightness variations in cross-track and along-track directions
3. **Fits Quadratic Envelopes**: Creates smooth mathematical models of illumination patterns
4. **Generates Corrections**: Creates 2D flatfield maps to correct sensor variations
5. **Produces Visualizations**: Generates comprehensive plots showing analysis results

### Basic Usage

**Process all filter positions with default settings:**
```bash
python Main.py
```

**Adjust smoothing for more or less aggressive correction:**
```bash
python Main.py --num_sigma 2.0    # More smoothing (gentler correction)
python Main.py --num_sigma 0.5    # Less smoothing (preserves more detail)
python Main.py --num_sigma 0      # No smoothing
```

### Understanding the Parameters

#### --num_sigma (Optional)
- **Default**: 1.0
- **What it controls**: Amount of smoothing applied during profile extraction and envelope fitting
- **Higher values**: Create smoother, more gradual corrections
- **Lower values**: Preserve fine details but may include more noise
- **Value of 0**: Disables smoothing entirely

## How the Algorithm Works

### 1. Profile Extraction

The pipeline extracts 1D brightness profiles from 2D images:

- **Cross-track profiles**: Cut through the image horizontally at the optical center Y position
- **Along-track profiles**: Cut through the image vertically at the optical center X position
- **Averaging window**: Profiles are averaged over a small window around the optical center for noise reduction

### 2. Data Cleaning

Each profile undergoes robust cleaning:

- **Sigma filtering**: Removes outliers beyond a specified threshold (default: 2σ)
- **Low-signal masking**: Excludes pixels with signal less than half the maximum
- **Validity checks**: Ensures sufficient data points remain for reliable fitting

### 3. Envelope Fitting

The cleaned profiles are fitted with quadratic functions:

- **Savitzky-Golay smoothing**: Applied first to reduce noise while preserving shape
- **Quadratic fitting**: Models illumination as f(x) = ax² + bx + c
- **Fallback options**: Linear or constant fits if quadratic fails

### 4. 2D Map Generation

Individual 1D fits are combined into a full 2D correction:

- **Additive combination**: Cross-track and along-track corrections are combined
- **Optical center normalization**: Map is normalized so the optical center has value 1.0
- **Quality assurance**: Bad pixels are identified and replaced with median values

## Output Files and Plots

The pipeline generates several types of output in the `Images/` directory:

### Individual Position Analysis
- **Combined profile plots**: Shows raw data, filtered data, smoothed profiles, and quadratic envelopes for each position
- **3D envelope visualizations**: Three-dimensional plots showing profile cuts and their fitted envelopes

### Generated Flatfield Maps
- **2D flatfield maps**: Visual representation of the correction with statistics
- **Cross-sections**: Profiles through the optical center showing correction behavior
- **Saved correction data**: `.npz` files containing flatfield arrays and metadata for later use

### Example Output Interpretation

**Profile Plots**: 
- Raw data points show the measured brightness
- Filtered data (green) shows outlier-removed points
- Smoothed profile (black) shows noise-reduced signal
- Envelope (red) shows the fitted quadratic model

**3D Plots**:
- Show the spatial relationship between cross-track and along-track profiles
- Envelope surfaces demonstrate the mathematical model of illumination patterns

**Flatfield Maps**:
- Bright regions indicate areas where the sensor is less sensitive (needs more correction)
- Dark regions indicate areas where the sensor is more sensitive (needs less correction)
- Values around 1.0 indicate areas needing minimal correction

## Advanced Usage

### Applying Corrections to Science Data

Once flatfield maps are generated, you can apply them to raw science images:

```python
from project_modules.FlatfieldProcessor import FlatfieldProcessor

# Initialize processor for specific filter position
processor = FlatfieldProcessor("pos1")

# Apply correction to a raw image
corrected_image, flatfield_map, metadata = processor.apply_flatfield_correction(
    raw_image=your_raw_image,
    show_comparison=True  # Display before/after plots
)
```

### Custom Processing Parameters

```python
# Generate flatfield with custom parameters
processor.generate_quadratic_envelope_flatfield(
    avg_window=15,        # Larger averaging window for more stable profiles
    num_sigma=1.5,        # Custom outlier threshold
    window_length=81,     # Longer smoothing window
    polyorder=3           # Higher polynomial order for smoothing
)
```

### Working with Saved Flatfields

```python
# Load a previously saved flatfield
import numpy as np
data = np.load("flatfield_map_pos1.npz")
flatfield_map = data['flatfield_map']
metadata = data['metadata'].item()  # Convert back to dict
cross_coeffs = data['cross_track_coeffs']
along_coeffs = data['along_track_coeffs']
```

## Installation and Dependencies

### Required Python Packages

```bash
pip install numpy matplotlib scipy pillow pandas
```

### System Requirements

- **Python**: 3.7 or later
- **Memory**: At least 4GB RAM for processing large image sets
- **Storage**: Sufficient space for input images and generated outputs
- **Display**: GUI backend for matplotlib plots (Qt5 recommended)

### File Structure Requirements

Ensure your data follows this structure:
```
data_directory/
├── LEFT_RIGHT/          # Cross-track illumination images
├── UP_DOWN/             # Along-track illumination images  
└── metadata.csv         # Image metadata and TEC readings
```

## Troubleshooting

### Common Issues

**"No images found for filter position"**
- Verify filter position mappings in `Constants.py`
- Check that data directories contain expected image files
- Ensure file naming conventions match the expected patterns

**"Failed to extract profiles"**
- Try adjusting the `avg_window` parameter (start with 5-15)
- Check that optical center coordinates are correct for your data
- Verify that images have sufficient signal levels

**"Quadratic fitting failed"**
- The algorithm automatically falls back to linear or constant fits
- Consider increasing `num_sigma` to be less strict about outliers
- Check that profiles have sufficient valid data points

**Memory errors**
- Process one filter position at a time if needed
- Reduce the number of images being processed simultaneously
- Ensure sufficient RAM is available

### Performance Optimization

**Faster processing:**
- Use smaller averaging windows when possible
- Reduce the number of images per position if signal allows
- Process filter positions sequentially rather than in parallel

**Better results:**
- Use larger averaging windows for noisier data
- Increase smoothing parameters for unstable fits
- Verify optical center coordinates are accurate

## Technical Details

### Optical Center Configuration

The pipeline uses fixed optical center coordinates defined in `Constants.py`:
```python
OPTICAL_CENTER_X = 640  # Cross-track center
OPTICAL_CENTER_Y = 510  # Along-track center
```

These coordinates should be verified and adjusted based on your specific sensor and optical system.

### Mathematical Model

The quadratic envelope model assumes illumination follows:
```
I(x) = a·x² + b·x + c
```

Where:
- `a` captures curvature (vignetting effects)
- `b` captures linear gradients (alignment effects)  
- `c` captures the baseline illumination level

### Data Processing Pipeline

1. **Image Loading**: Multi-threaded loading with metadata association
2. **Dark Correction**: Robust averaging and subtraction with overflow protection
3. **Profile Extraction**: Windowed averaging with comprehensive validity checking
4. **Outlier Removal**: Statistical filtering with configurable thresholds
5. **Smoothing**: Savitzky-Golay filtering with automatic parameter adjustment
6. **Envelope Fitting**: Hierarchical fitting (quadratic → linear → constant)
7. **Map Generation**: 2D interpolation with normalization and quality control

## Contributing

This pipeline is designed for scientific reproducibility and extensibility. When modifying the code:

1. **Maintain logging**: All major steps should include informative print statements
2. **Preserve metadata**: Include processing parameters in all output files
3. **Add error handling**: Gracefully handle edge cases and provide helpful error messages
4. **Update documentation**: Modify this README when changing functionality

## Getting Help

For questions, bug reports, or feature requests:

1. **Check this documentation** for parameter explanations and troubleshooting
2. **Examine the generated plots** to understand what the algorithm is doing
3. **Try different parameter values** to see their effects on results
4. **Contact**: Charlemagne Marc (chamrc1@umbc.edu)

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