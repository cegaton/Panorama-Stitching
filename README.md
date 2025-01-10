# Panorama-Stitching
Utilities in python and bash to automate multirow panorama stitching from different images arranged in rows a and columns.

1A 1B 1C 1D

2A 2B 2C 2D

3A 3B 3C 3D

4A 4B 4C 4D

The script will open windows to select images and ask for number of rows and columns.

These scripts are designed to create control points in adjacent overlapping pictures orgainized in rows and colums.
Rows and columns are created in different .pto projects and combined into a final one at the end.

The idea is avoiding trying to find control points in all images (to avoid false matches or too much distortion)
Each image will only be stitched to the immediatlely adjacent images (up to eight), but if more images overlap that information will be ignored
and no control points will be created. For example: even if 4D and 2C have overlapping information, no control points will be created.

The script assumes that the images are shot in sequence and the numbering of the images corresponds to rows or columns.
If the images do not match a regular grid the sript will not work and images will need to be renamed to be arranged a coherent pattern.

