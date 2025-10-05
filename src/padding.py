import numpy as np
import rasterio
from rasterio.transform import Affine

def pad_and_save_tif(input_path, output_path, target_size=(256, 256)):
    """
    Pads a single-band GeoTIFF to the target size with zero padding and updates georeference.
    
    Parameters:
        input_path (str): Path to the input GeoTIFF.
        output_path (str): Path to save the padded GeoTIFF.
        target_size (tuple): (height, width) of the desired output size.
    """
    try:
        with rasterio.open(input_path) as src:
            img_array = src.read(1)  # Read first band
            profile = src.profile

        current_h, current_w = img_array.shape

        # Calculate padding for top/bottom and left/right (handles odd differences)
        pad_h_top = (target_size[0] - current_h) // 2
        pad_h_bottom = target_size[0] - current_h - pad_h_top
        pad_w_left = (target_size[1] - current_w) // 2
        pad_w_right = target_size[1] - current_w - pad_w_left

        # Apply zero-padding
        padded_img_array = np.pad(
            img_array,
            ((pad_h_top, pad_h_bottom), (pad_w_left, pad_w_right)),
            mode='constant',
            constant_values=0
        )

        # Update metadata with new size and transform
        profile.update(
            width=padded_img_array.shape[1],
            height=padded_img_array.shape[0],
            transform=Affine(
                profile['transform'].a,  # x-pixel size
                profile['transform'].b,  # rotation
                profile['transform'].c - pad_w_left * profile['transform'].a,  # x-offset
                profile['transform'].d,  # rotation
                profile['transform'].e,  # y-pixel size (negative)
                profile['transform'].f - pad_h_top * profile['transform'].e  # y-offset
            )
        )

        # Save the padded image
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(padded_img_array, 1)

        print(f"Padded GeoTIFF saved successfully to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
