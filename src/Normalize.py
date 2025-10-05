import rasterio
import numpy as np
from pathlib import Path


def normalize_and_save_geotiff_hist_equalization(input_path, output_path):
    try:
        with rasterio.open(input_path) as src:
            # Read the data from the first band
            data = src.read(1)

            # Get the original nodata value
            nodata_val = src.nodata

            # Create a mask for valid data pixels
            if nodata_val is not None:
                valid_mask = data != nodata_val
                valid_pixels = data[valid_mask]
            else:
                valid_pixels = data

            # Get the minimum and maximum values from the valid data for the histogram range
            min_val = np.min(valid_pixels)
            max_val = np.max(valid_pixels)

            # Create a histogram of the valid pixels
            hist, bins = np.histogram(valid_pixels, bins=256, range=(min_val, max_val))
            
            # Calculate the cumulative distribution function (CDF)
            cdf = hist.cumsum()
            
            # Normalize the CDF to the full 0-255 range, ignoring pixels at the very beginning
            # This avoids crushing the data if there's a big spike in the lowest values
            cdf_normalized = (cdf - cdf.min()) * 255 / (cdf.max() - cdf.min())

            # Use the CDF to map the original data to the new range
            equalized_data = np.interp(data, bins[:-1], cdf_normalized)

            # Ensure nodata values are set to 0 in the new data
            if nodata_val is not None:
                equalized_data[~valid_mask] = 0
            
            # Get the original metadata
            profile = src.profile

            # Update the profile for the new 8-bit output
            profile.update(
                dtype=rasterio.uint8,
                nodata=0,
                count=1,
            )

            # Save the equalized data to the new file
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(equalized_data.astype(rasterio.uint8), 1)

        print(f"✅ Successfully processed '{input_path}' using Histogram Equalization and saved to '{output_path}'.")

    except rasterio.RasterioIOError as e:
        print(f"❌ Rasterio error: Could not open or process '{input_path}'. Error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


def normalize(input_directory = Path('../before_norm'),
              output_directory = Path('../after_norm')):

    Path(output_directory).mkdir(exist_ok=True)
    for path in Path(input_directory).glob("*.tif"):
        output_path = Path(output_directory) / path.name
        normalize_and_save_geotiff_hist_equalization(path, output_path)
    return Path(output_directory)