import torch
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch import ToTensorV2
import rasterio
import numpy as np
import os
from pathlib import Path

# --- Configuration ---
# A minimal config for inference
class Config:
    BACKBONE = 'efficientnet-b3'
    NUM_CLASSES = 1
    IMAGE_SIZE = 256
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    CHECKPOINT_DIR = "./lake_checkpoints"

config = Config()

# --- Model Definition ---
def create_model(num_classes=config.NUM_CLASSES, backbone=config.BACKBONE):
    """Recreates the model architecture."""
    model = smp.Unet(
        encoder_name=backbone,
        encoder_weights='imagenet',
        in_channels=1,
        classes=num_classes,
    )
    return model

# --- Model Loading ---
def load_model_for_inference(checkpoint_path, device):
    """Loads the model from a checkpoint for inference."""
    model = create_model()
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval() # Set model to evaluation mode
    print(f"✅ Model loaded from {checkpoint_path} and set to evaluation mode.")
    return model

# --- Preprocessing and Prediction ---
def get_prediction_transform():
    """Get transformation for a single image prediction."""
    return A.Compose([
        A.Resize(config.IMAGE_SIZE, config.IMAGE_SIZE),
        ToTensorV2(),
    ], is_check_shapes=False)

def predict_one_image(model, image_path, device):
    """
    Predicts a mask for a single image, returning the original image and the predicted mask.
    """
    # 1. Load image using rasterio to keep georeferencing info
    with rasterio.open(image_path) as src:
        image_data = src.read(1).copy()  # Read single-channel image
        transform_meta = src.transform # Get georeferencing transform
        crs_meta = src.crs # Get coordinate reference system

    original_image = image_data.copy()

    # 2. Preprocess for the model
    if image_data.ndim == 2:
        image_data = image_data[..., np.newaxis]
    
    image_data = image_data.astype(np.float32) / 255.0
    patch_mean = image_data.mean()
    patch_std = image_data.std()
    epsilon = 1e-6
    image_data = (image_data - patch_mean) / (patch_std + epsilon)

    # 3. Apply transformations
    transform = get_prediction_transform()
    augmented = transform(image=image_data)
    image_tensor = augmented['image'].to(device).unsqueeze(0)  # Add batch dimension

    # 4. Predict
    with torch.no_grad():
        outputs = model(image_tensor)
        preds = torch.sigmoid(outputs).squeeze()
        pred_mask = (preds > 0.5).cpu().numpy().astype(np.uint8)

    return original_image, pred_mask, transform_meta, crs_meta

# --- Mask Saving ---
def save_mask_as_tif(mask_array, original_image_path, output_dir):
    """
    Saves the predicted mask as a .tif file with georeferencing.
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define output filename
    original_filename = Path(original_image_path).stem
    output_filepath = output_path / f"{original_filename}_mask.tif"

    # Get georeferencing from original image
    with rasterio.open(original_image_path) as src:
        profile = src.profile
    
    # Update profile for the new mask file
    profile.update(
        dtype=rasterio.uint8,
        count=1,
        compress='lzw'
    )

    # Write the mask
    with rasterio.open(output_filepath, 'w', **profile) as dst:
        dst.write(mask_array, 1)
        
    print(f"✅ Mask saved to: {output_filepath}")
    return output_filepath
