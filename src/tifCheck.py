import rasterio
import numpy as np

def check(file_path):
    with rasterio.open(file_path) as src:
        data = src.read(1)
        mean = np.mean(data)
        min_val = np.min(data)
        max_val = np.max(data)
        print(f"File: {file_path}")
        print(f"Minimum Value: {min_val}")
        print(f"Maximum Value: {max_val}")
        print(f"Mean Value: {mean}")
        print(f"   Bands: {src.count}")
        print(f"   Shape: {src.height} x {src.width}")
        print(f"   Dtype: {src.dtypes[0]}")
        return min_val, max_val
    

def finalCheck(check_directory):
    for path in check_directory.glob("*.tif"):
        check(path)




