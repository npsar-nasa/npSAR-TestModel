import predictor
import DownloadProcessing as DP
import CheckArea
from pathlib import Path
import matplotlib.pyplot as plt


# 1. Define the input directory for prediction
input_image_dir = DP.getFinalPatchDir()
print(input_image_dir)
if not input_image_dir.exists():
    raise FileNotFoundError(f"Input directory not found: {input_image_dir}")

# 2. Define the output directory for the masks
output_mask_dir = Path("./Output")
output_mask_dir.mkdir(exist_ok=True)

# 3. Load the trained model
best_model_path = f'{predictor.config.CHECKPOINT_DIR}/best_lake_model.pth'
inference_model = predictor.load_model_for_inference(best_model_path, predictor.config.DEVICE)

# 4. Process each image in the input directory
for image_path in input_image_dir.glob('*.tif'):
    print("-" * 50)
    print(f"Processing: {image_path.name}")

    # a. Get the prediction
    original_image, pred_mask, _, _ = predictor.predict_one_image(
        inference_model, 
        image_path, 
        predictor.config.DEVICE
    )

    # b. Save the predicted mask to a new .tif file
    saved_mask_path = predictor.save_mask_as_tif(
        pred_mask, 
        image_path, 
        output_mask_dir
    )

    # c. Visualize the results
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    axes[0].imshow(original_image, cmap='gray')
    axes[0].set_title("Original SAR Image")
    axes[0].axis('off')

    axes[1].imshow(pred_mask, cmap='Reds', vmin=0, vmax=1)
    axes[1].set_title("Predicted Mask")
    axes[1].axis('off')

    axes[2].imshow(original_image, cmap='gray')
    axes[2].imshow(pred_mask, cmap='Reds', alpha=0.5, vmin=0, vmax=1)
    axes[2].set_title("Overlay")
    axes[2].axis('off')
    
    plt.suptitle(f"Prediction for {image_path.name}", fontsize=16)
    plt.tight_layout()
    plt.show()

    # d. Calculate and print the area from the new mask file
    print(f"Calculating area for: {saved_mask_path.name}")
    CheckArea.getArea(saved_mask_path)
    print("-" * 50)



