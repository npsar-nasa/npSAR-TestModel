from osgeo import gdal
from pathlib import Path

def crop(input_tif, wkt, outDir, lakeName):
    """
    Crops a raster to a given WKT polygon and saves it.
    This version explicitly tells GDAL the coordinate system of the WKT.
    """
    output_tif_name = f"{Path(input_tif).stem}_clipped_to_{lakeName}AOI.tif"
    output_tif = Path(outDir) / output_tif_name

    # Set up the options for gdal.Warp.
    # This tells GDAL to use the WKT string as the cutline and to
    # assume the WKT is in WGS84 (EPSG:4326). GDAL will then reproject
    # the cutline to match the raster before cropping.
    warp_options = gdal.WarpOptions(
        format='GTiff',
        cutlineWKT=wkt,
        cutlineSRS='EPSG:4326',  # Explicitly define the cutline's CRS
        cropToCutline=True,
        dstNodata=0,
        multithread=True,
        xRes=20,
        yRes=20,
        targetAlignedPixels=True
    )

    # Perform the crop operation
    try:
        gdal.Warp(
            destNameOrDestDS=str(output_tif),
            srcDSOrSrcDSTab=str(input_tif),
            options=warp_options
        )
        print(f"✅ Cropped raster saved to: {output_tif}")
        return output_tif
    except Exception as e:
        print(f"❌ Failed to crop {input_tif}. Error: {e}")
        return None