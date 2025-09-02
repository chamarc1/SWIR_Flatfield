#!/usr/bin/env python3
"""
Enhanced Flatfield Effectiveness Analysis

This script performs a deep analysis of why the flatfield correction
is not providing substantial improvements and suggests potential solutions.

Usage:
    python analyze_flatfield_effectiveness.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from project_modules.FlatfieldProcessor import FlatfieldProcessor

# Import optical center constants from FlatfieldProcessor
from project_modules.FlatfieldProcessor import OPTICAL_CENTER_X, OPTICAL_CENTER_Y

def analyze_flatfield_effectiveness():
    """Perform comprehensive analysis of flatfield effectiveness."""
    
    print("=" * 80)
    print("ENHANCED FLATFIELD EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    
    # Create output directory
    output_dir = "/data/home/cmarc/SWIR_Projects/Flatfield/Images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test multiple positions
    positions = ["pos1", "pos2", "pos3", "pos4"]
    wavelengths = {"pos1": "1.57μm", "pos2": "1.55μm", "pos3": "1.38μm", "pos4": "Open"}
    
    for position in positions:
        print(f"\n{'=' * 60}")
        print(f"ANALYZING FILTER POSITION {position.upper()} ({wavelengths[position]})")
        print(f"{'=' * 60}")
        
        try:
            analyze_position(position, wavelengths[position], output_dir)
        except Exception as e:
            print(f"❌ Error analyzing {position}: {str(e)}")
            continue
    
    print(f"\n{'=' * 80}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 80}")

def analyze_position(position, wavelength, output_dir):
    """Analyze flatfield effectiveness for a specific position."""
    
    # Create processor
    processor = FlatfieldProcessor(position)
    
    # Generate flatfield map
    print("1. Generating flatfield map...")
    flatfield_map = processor.generate_flatfield_map()
    
    if flatfield_map is None:
        print(f"❌ Failed to generate flatfield map for {position}")
        return
    
    print(f"   ✓ Flatfield map generated")
    print(f"   Shape: {flatfield_map.shape}")
    print(f"   Range: [{np.min(flatfield_map):.4f}, {np.max(flatfield_map):.4f}]")
    print(f"   Mean: {np.mean(flatfield_map):.4f}")
    print(f"   Std: {np.std(flatfield_map):.4f}")
    
    # Get sample images
    print("\n2. Loading sample images...")
    sample_images = processor.get_sample_images(n_samples=10)
    
    if not sample_images:
        print(f"❌ No sample images found for {position}")
        return
    
    print(f"   ✓ Loaded {len(sample_images)} sample images")
    
    # Analyze flatfield characteristics
    print("\n3. Analyzing flatfield characteristics...")
    analyze_flatfield_characteristics(flatfield_map, position, wavelength, output_dir)
    
    # Analyze sphere vs background regions
    print("\n4. Analyzing sphere vs background regions...")
    analyze_sphere_background_regions(sample_images, flatfield_map, position, wavelength, output_dir)
    
    # Test different correction strategies
    print("\n5. Testing different correction strategies...")
    test_correction_strategies(sample_images[0], flatfield_map, position, wavelength, output_dir)
    
    # Analyze spatial frequency content
    print("\n6. Analyzing spatial frequency content...")
    analyze_spatial_frequencies(sample_images[0], flatfield_map, position, wavelength, output_dir)

def analyze_flatfield_characteristics(flatfield_map, position, wavelength, output_dir):
    """Analyze the characteristics of the flatfield map."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Flatfield map visualization
    im1 = axes[0, 0].imshow(flatfield_map, cmap='viridis', origin='lower')
    axes[0, 0].set_title(f'Flatfield Map\n{position} ({wavelength})')
    axes[0, 0].add_patch(Circle((OPTICAL_CENTER_X, OPTICAL_CENTER_Y), 50, 
                               fill=False, color='red', linewidth=2))
    plt.colorbar(im1, ax=axes[0, 0], label='Correction Factor')
    
    # 2. Flatfield map histogram
    axes[0, 1].hist(flatfield_map.flatten(), bins=50, alpha=0.7, color='blue')
    axes[0, 1].axvline(np.mean(flatfield_map), color='red', linestyle='--', 
                      label=f'Mean: {np.mean(flatfield_map):.4f}')
    axes[0, 1].axvline(np.median(flatfield_map), color='orange', linestyle='--', 
                      label=f'Median: {np.median(flatfield_map):.4f}')
    axes[0, 1].set_xlabel('Correction Factor')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Flatfield Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Cross-track profile through center
    center_row = flatfield_map[OPTICAL_CENTER_Y, :]
    axes[0, 2].plot(center_row, 'b-', linewidth=2, label='Cross-track')
    axes[0, 2].axhline(1.0, color='red', linestyle='--', alpha=0.7, label='Perfect correction')
    axes[0, 2].set_xlabel('Pixel Position')
    axes[0, 2].set_ylabel('Correction Factor')
    axes[0, 2].set_title('Cross-track Profile (Center Row)')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. Along-track profile through center
    center_col = flatfield_map[:, OPTICAL_CENTER_X]
    axes[1, 0].plot(center_col, 'g-', linewidth=2, label='Along-track')
    axes[1, 0].axhline(1.0, color='red', linestyle='--', alpha=0.7, label='Perfect correction')
    axes[1, 0].set_xlabel('Pixel Position')
    axes[1, 0].set_ylabel('Correction Factor')
    axes[1, 0].set_title('Along-track Profile (Center Col)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. Deviation from unity
    deviation_map = flatfield_map - 1.0
    im2 = axes[1, 1].imshow(deviation_map, cmap='RdBu_r', origin='lower', 
                           vmin=-np.max(np.abs(deviation_map)), 
                           vmax=np.max(np.abs(deviation_map)))
    axes[1, 1].set_title('Deviation from Unity\n(Flatfield - 1.0)')
    axes[1, 1].add_patch(Circle((OPTICAL_CENTER_X, OPTICAL_CENTER_Y), 50, 
                               fill=False, color='black', linewidth=2))
    plt.colorbar(im2, ax=axes[1, 1], label='Deviation')
    
    # 6. Statistics summary
    axes[1, 2].axis('off')
    stats_text = f"""
Flatfield Map Statistics
{position} ({wavelength})

Shape: {flatfield_map.shape}
Data Type: {flatfield_map.dtype}

Value Range:
  Min: {np.min(flatfield_map):.6f}
  Max: {np.max(flatfield_map):.6f}
  Range: {np.max(flatfield_map) - np.min(flatfield_map):.6f}

Central Tendency:
  Mean: {np.mean(flatfield_map):.6f}
  Median: {np.median(flatfield_map):.6f}
  Mode region: {np.percentile(flatfield_map, [45, 55])}

Variability:
  Std Dev: {np.std(flatfield_map):.6f}
  Variance: {np.var(flatfield_map):.8f}
  Coeff. of Var: {100*np.std(flatfield_map)/np.mean(flatfield_map):.3f}%

Deviation from Unity:
  Mean Abs Dev: {np.mean(np.abs(deviation_map)):.6f}
  Max Abs Dev: {np.max(np.abs(deviation_map)):.6f}
  RMS Dev: {np.sqrt(np.mean(deviation_map**2)):.6f}

Spatial Characteristics:
  Center Value: {flatfield_map[OPTICAL_CENTER_Y, OPTICAL_CENTER_X]:.6f}
    """
    
    axes[1, 2].text(0.05, 0.95, stats_text, transform=axes[1, 2].transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.1))
    
    plt.suptitle(f'Flatfield Map Analysis - {position} ({wavelength})', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f'flatfield_analysis_{position}.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Flatfield analysis saved to: {save_path}")

def analyze_sphere_background_regions(sample_images, flatfield_map, position, wavelength, output_dir):
    """Analyze correction effectiveness in sphere vs background regions."""
    
    # Define sphere region (rough estimate)
    y_center, x_center = OPTICAL_CENTER_Y, OPTICAL_CENTER_X
    sphere_radius = 200  # Adjust based on your data
    
    # Create masks
    y, x = np.ogrid[:flatfield_map.shape[0], :flatfield_map.shape[1]]
    sphere_mask = (x - x_center)**2 + (y - y_center)**2 <= sphere_radius**2
    background_mask = ~sphere_mask
    
    # Analyze first sample image
    sample_image = sample_images[0]
    corrected_image = sample_image * flatfield_map
    
    # Calculate statistics for different regions
    regions = {
        'Entire Image': (slice(None), slice(None)),
        'Sphere Region': sphere_mask,
        'Background': background_mask
    }
    
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    
    # Show original and corrected images
    im1 = axes[0, 0].imshow(sample_image, cmap='gray', origin='lower')
    axes[0, 0].set_title('Original Image')
    axes[0, 0].add_patch(Circle((x_center, y_center), sphere_radius, 
                               fill=False, color='red', linewidth=2))
    plt.colorbar(im1, ax=axes[0, 0])
    
    im2 = axes[0, 1].imshow(corrected_image, cmap='gray', origin='lower')
    axes[0, 1].set_title('Corrected Image')
    axes[0, 1].add_patch(Circle((x_center, y_center), sphere_radius, 
                               fill=False, color='red', linewidth=2))
    plt.colorbar(im2, ax=axes[0, 1])
    
    # Show difference
    diff_image = corrected_image - sample_image
    im3 = axes[0, 2].imshow(diff_image, cmap='RdBu_r', origin='lower',
                           vmin=-np.max(np.abs(diff_image)), vmax=np.max(np.abs(diff_image)))
    axes[0, 2].set_title('Difference (Corrected - Original)')
    axes[0, 2].add_patch(Circle((x_center, y_center), sphere_radius, 
                               fill=False, color='black', linewidth=2))
    plt.colorbar(im3, ax=axes[0, 2])
    
    # Show masks
    mask_display = np.zeros_like(sample_image)
    mask_display[sphere_mask] = 1
    mask_display[background_mask] = 0.5
    axes[0, 3].imshow(mask_display, cmap='viridis', origin='lower')
    axes[0, 3].set_title('Region Masks\n(1=Sphere, 0.5=Background)')
    
    # Regional analysis
    stats_data = []
    colors = ['blue', 'red', 'green']
    
    for i, (region_name, mask) in enumerate(regions.items()):
        if isinstance(mask, tuple):  # slice objects
            orig_region = sample_image[mask]
            corr_region = corrected_image[mask]
        else:  # boolean mask
            orig_region = sample_image[mask]
            corr_region = corrected_image[mask]
        
        orig_std = np.std(orig_region)
        corr_std = np.std(corr_region)
        improvement = 100 * (orig_std - corr_std) / orig_std
        
        stats_data.append({
            'region': region_name,
            'orig_mean': np.mean(orig_region),
            'orig_std': orig_std,
            'corr_mean': np.mean(corr_region),
            'corr_std': corr_std,
            'improvement': improvement
        })
        
        # Plot histograms
        axes[1, i].hist(orig_region.flatten(), bins=50, alpha=0.7, 
                       color=colors[i], label=f'Original (σ={orig_std:.1f})')
        axes[1, i].hist(corr_region.flatten(), bins=50, alpha=0.7, 
                       color=colors[i], linestyle='--', histtype='step', linewidth=2,
                       label=f'Corrected (σ={corr_std:.1f})')
        axes[1, i].set_xlabel('Pixel Value')
        axes[1, i].set_ylabel('Frequency')
        axes[1, i].set_title(f'{region_name}\nImprovement: {improvement:.2f}%')
        axes[1, i].legend()
        axes[1, i].grid(True, alpha=0.3)
    
    # Summary statistics
    axes[1, 3].axis('off')
    summary_text = f"""
Regional Analysis Summary
{position} ({wavelength})

Sphere Region:
  Original σ: {stats_data[1]['orig_std']:.2f}
  Corrected σ: {stats_data[1]['corr_std']:.2f}
  Improvement: {stats_data[1]['improvement']:.2f}%

Background Region:
  Original σ: {stats_data[2]['orig_std']:.2f}
  Corrected σ: {stats_data[2]['corr_std']:.2f}
  Improvement: {stats_data[2]['improvement']:.2f}%

Entire Image:
  Original σ: {stats_data[0]['orig_std']:.2f}
  Corrected σ: {stats_data[0]['corr_std']:.2f}
  Improvement: {stats_data[0]['improvement']:.2f}%

Analysis:
"""
    
    # Add analysis
    if stats_data[1]['improvement'] > stats_data[2]['improvement']:
        analysis = "Correction works better\nin sphere region"
    elif stats_data[2]['improvement'] > stats_data[1]['improvement']:
        analysis = "Correction works better\nin background region"
    else:
        analysis = "Correction effectiveness\nis similar across regions"
    
    summary_text += analysis
    
    axes[1, 3].text(0.05, 0.95, summary_text, transform=axes[1, 3].transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.1))
    
    plt.suptitle(f'Regional Correction Analysis - {position} ({wavelength})', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f'regional_analysis_{position}.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Regional analysis saved to: {save_path}")

def test_correction_strategies(sample_image, flatfield_map, position, wavelength, output_dir):
    """Test different correction strategies."""
    
    strategies = {
        'Multiply': lambda img, ff: img * ff,
        'Divide': lambda img, ff: img / ff,
        'Subtract': lambda img, ff: img - (ff - 1.0) * np.mean(img),
        'Add': lambda img, ff: img + (ff - 1.0) * np.mean(img),
        'Hybrid': lambda img, ff: img * ff + 0.1 * (img - img * ff)
    }
    
    original_std = np.std(sample_image)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    results = []
    
    # Original image
    axes[0].imshow(sample_image, cmap='gray', origin='lower')
    axes[0].set_title(f'Original Image\nσ = {original_std:.2f}')
    axes[0].add_patch(Circle((OPTICAL_CENTER_X, OPTICAL_CENTER_Y), 50, 
                            fill=False, color='red', linewidth=2))
    
    for i, (strategy_name, strategy_func) in enumerate(strategies.items(), 1):
        try:
            corrected = strategy_func(sample_image, flatfield_map)
            corrected_std = np.std(corrected)
            improvement = 100 * (original_std - corrected_std) / original_std
            
            results.append({
                'strategy': strategy_name,
                'std': corrected_std,
                'improvement': improvement
            })
            
            axes[i].imshow(corrected, cmap='gray', origin='lower')
            axes[i].set_title(f'{strategy_name}\nσ = {corrected_std:.2f}\nΔ = {improvement:+.2f}%')
            axes[i].add_patch(Circle((OPTICAL_CENTER_X, OPTICAL_CENTER_Y), 50, 
                                    fill=False, color='red', linewidth=2))
            
        except Exception as e:
            axes[i].text(0.5, 0.5, f'Error in {strategy_name}:\n{str(e)}', 
                        transform=axes[i].transAxes, ha='center', va='center')
            axes[i].set_title(f'{strategy_name} - Error')
    
    plt.suptitle(f'Correction Strategy Comparison - {position} ({wavelength})', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f'strategy_comparison_{position}.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Strategy comparison saved to: {save_path}")
    
    # Print results
    print("   Strategy Results:")
    for result in sorted(results, key=lambda x: x['improvement'], reverse=True):
        print(f"     {result['strategy']:10s}: {result['improvement']:+6.2f}% improvement")

def analyze_spatial_frequencies(sample_image, flatfield_map, position, wavelength, output_dir):
    """Analyze spatial frequency content to understand flatfield effectiveness."""
    
    # Apply correction
    corrected_image = sample_image * flatfield_map
    
    # Compute 2D FFT
    fft_orig = np.fft.fft2(sample_image)
    fft_corr = np.fft.fft2(corrected_image)
    fft_flatfield = np.fft.fft2(flatfield_map)
    
    # Power spectra
    power_orig = np.abs(fft_orig)**2
    power_corr = np.abs(fft_corr)**2
    power_flatfield = np.abs(fft_flatfield)**2
    
    # Shift zero frequency to center
    power_orig_shifted = np.fft.fftshift(power_orig)
    power_corr_shifted = np.fft.fftshift(power_corr)
    power_flatfield_shifted = np.fft.fftshift(power_flatfield)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Power spectra (log scale)
    im1 = axes[0, 0].imshow(np.log10(power_orig_shifted + 1), cmap='hot', origin='lower')
    axes[0, 0].set_title('Original Image\nPower Spectrum')
    plt.colorbar(im1, ax=axes[0, 0], label='Log10(Power)')
    
    im2 = axes[0, 1].imshow(np.log10(power_corr_shifted + 1), cmap='hot', origin='lower')
    axes[0, 1].set_title('Corrected Image\nPower Spectrum')
    plt.colorbar(im2, ax=axes[0, 1], label='Log10(Power)')
    
    im3 = axes[0, 2].imshow(np.log10(power_flatfield_shifted + 1), cmap='hot', origin='lower')
    axes[0, 2].set_title('Flatfield Map\nPower Spectrum')
    plt.colorbar(im3, ax=axes[0, 2], label='Log10(Power)')
    
    # Radial power spectra
    center_y, center_x = np.array(power_orig_shifted.shape) // 2
    y, x = np.ogrid[:power_orig_shifted.shape[0], :power_orig_shifted.shape[1]]
    r = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Compute radially averaged power spectra
    max_r = int(min(center_x, center_y))
    radial_orig = []
    radial_corr = []
    radial_flatfield = []
    radii = []
    
    for radius in range(1, max_r, 5):
        mask = (r >= radius - 2.5) & (r < radius + 2.5)
        if np.sum(mask) > 0:
            radial_orig.append(np.mean(power_orig_shifted[mask]))
            radial_corr.append(np.mean(power_corr_shifted[mask]))
            radial_flatfield.append(np.mean(power_flatfield_shifted[mask]))
            radii.append(radius)
    
    axes[1, 0].loglog(radii, radial_orig, 'b-', label='Original', linewidth=2)
    axes[1, 0].loglog(radii, radial_corr, 'r-', label='Corrected', linewidth=2)
    axes[1, 0].set_xlabel('Spatial Frequency (cycles/image)')
    axes[1, 0].set_ylabel('Power')
    axes[1, 0].set_title('Radial Power Spectra')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].loglog(radii, radial_flatfield, 'g-', linewidth=2)
    axes[1, 1].set_xlabel('Spatial Frequency (cycles/image)')
    axes[1, 1].set_ylabel('Power')
    axes[1, 1].set_title('Flatfield Power Spectrum')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Power ratio
    power_ratio = np.array(radial_corr) / np.array(radial_orig)
    axes[1, 2].semilogx(radii, power_ratio, 'purple', linewidth=2)
    axes[1, 2].axhline(1.0, color='black', linestyle='--', alpha=0.7)
    axes[1, 2].set_xlabel('Spatial Frequency (cycles/image)')
    axes[1, 2].set_ylabel('Power Ratio (Corrected/Original)')
    axes[1, 2].set_title('Frequency Response')
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.suptitle(f'Spatial Frequency Analysis - {position} ({wavelength})', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f'frequency_analysis_{position}.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Frequency analysis saved to: {save_path}")

if __name__ == "__main__":
    try:
        analyze_flatfield_effectiveness()
        print("\n🎉 Enhanced analysis completed!")
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        raise
