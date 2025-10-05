# npSAR-TestModel: Automated Glacial Lake Monitoring

A deep learning-based system for automated glacial lake detection and monitoring in Nepal using Sentinel-1 Synthetic Aperture Radar (SAR) satellite imagery.

This project provides an end-to-end pipeline to:
1.  **Download** and preprocess Sentinel-1 data for a specified region and time.
2.  **Predict** glacial lake boundaries using a pre-trained U-Net deep learning model.
3.  **Analyze** the results by visualizing the output masks and calculating the lake surface area.

---

## How to Use This Project

Follow these steps to set up the environment, configure the parameters, and run the full pipeline.

### 1. Setup and Installation

First, set up your local environment.

**A. Create a Virtual Environment**

It is highly recommended to use a Python virtual environment to manage dependencies.

```bash
# Navigate to the project directory
cd npSAR-TestModel

# Create a virtual environment
python3 -m venv .venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

**B. Install Dependencies**

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 2. Configuration

All parameters for the project are managed in the `src/config.ini` file. Before running the scripts, you must update this file.

Open `src/config.ini` and set the following:

-   **`[Login]`**:
    -   `user`: Your NASA Earthdata username.
    -   `password`: Your NASA Earthdata password.
-   **`[Other]`**:
    -   `wkt`: The Well-Known Text (WKT) polygon defining your area of interest (AOI).
    -   `lakeNames`: A comma-separated list of names for the lakes in your AOI.
    -   `years`: The years you want to search for satellite data.
    -   `job_name`: A unique name for the data processing job on HyP3.
    -   `start_date` / `end_date`: The month and day for the search period within each year (e.g., `07-01` to `08-31`).

For wkt, you can first create a geojson from http://geojson.io and then convert it to wkt from https://geojson-to-wkt-converter.onrender.com.

### 3. Running the Pipeline

The workflow is a two-step process: first download and process the data, then run the prediction.

**Step 1: Download and Process SAR Data**

This script searches for relevant SAR images, submits a processing job to ASF HyP3, downloads the results, and prepares them for the model.

```bash
python src/DownloadProcessing.py
```

What this script does:
- Searches for Sentinel-1 data based on your `config.ini` parameters.
- If a HyP3 job with the same `job_name` exists, it will ask if you want to re-use it.
- Submits a new processing job if required.
- Watches the job until it completes, then downloads the `.zip` files to the location specified in `store_location`.
- Unzips, crops, pads, and normalizes the images, saving the final processed files into the `after_norm/` directory.

**Step 2: Predict Lake Masks and Analyze Results**

Once the data is processed, run the orchestrator script to perform inference. This script uses the pre-trained model included in the project (`./lake_checkpoints/best_lake_model.pth`).

```bash
python src/Orchestrator.py
```

What this script does:
- Loads the pre-trained U-Net model.
- Processes each image from the `after_norm/` directory.
- For each image:
    - Predicts the water mask.
    - Saves the mask as a new `.tif` file in the `Output/` directory.
    - Displays a plot showing the original image, the predicted mask, and an overlay.
    - Calculates and prints the lake surface area in square kilometers.

---

### Model Training (Optional)

The project includes a pre-trained model, but you can train your own using the `TrainTest.ipynb` Jupyter notebook.

1.  **Prepare Data**: Place your raw training images in `SAR_model_data/Prelabelled/` and your corresponding binary masks in `SAR_model_data/Labelled/`.
2.  **Run Notebook**: Launch and run the cells in `TrainTest.ipynb` to start the training process. The best-performing model will be saved to the `lake_checkpoints/` directory.

### Project Structure

```
npSAR-TestModel/
├── src/                      # Core processing scripts
│   ├── DownloadProcessing.py   # Step 1: Download and process data
│   ├── Orchestrator.py       # Step 2: Predict and analyze
│   ├── predictor.py          # Helper functions for model inference
│   ├── Crop_Product.py         # Image cropping utility
│   ├── Normalize.py            # Image normalization utility
│   └── config.ini              # Main configuration file
├── lake_checkpoints/         # Stores trained model files
│   └── best_lake_model.pth   # The pre-trained model
├── after_norm/               # Output of the data processing step
├── Output/                   # Output of the prediction step
├── TrainTest.ipynb           # Notebook for model training
├── requirements.txt          # Project dependencies
└── README.md                 # This documentation
```


