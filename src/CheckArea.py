import rasterio
import numpy as np
from pathlib import Path

def getArea(mask_path):
    mask_path = Path(mask_path)
    if not mask_path.exists():
        print(f"Error: Mask file not found at {mask_path}")
        return

    with rasterio.open(str(mask_path)) as src_mask:
        # Resolution (pixel size in meters)
        pixel_size_x, pixel_size_y = src_mask.res
        # Area of a single pixel in square meters
        pixel_area_sq_m = abs(pixel_size_x * pixel_size_y)
        
        mask_data = src_mask.read(1)

    # Count the number of pixels with value 1 (lake)
    lake_pixels = np.count_nonzero(mask_data == 1)

    # Calculate total area in square meters and square kilometers
    total_area_sq_m = lake_pixels * pixel_area_sq_m
    total_area_sq_km = total_area_sq_m / 1_000_000

    print(f"Analysis for: {mask_path.name}")
    print(f"  - Pixel Resolution: {abs(pixel_size_x):.2f}m x {abs(pixel_size_y):.2f}m")
    print(f"  - Detected Lake Pixels: {lake_pixels}")
    print(f"  - Total Lake Area: {total_area_sq_km:.4f} sq. km")
    
    return total_area_sq_km

