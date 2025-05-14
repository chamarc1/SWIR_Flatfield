# test_dark_subtraction.py
from PIL import Image                 # Needed for opening images
import numpy as np
import os

img = np.array(Image.open(r"/data/ESI/User/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/LEFT_RIGHT/20250206_FILTPOS_010_INTTIME_01p5/DEG_0/cfc_capture_1719354333877.tiff"))
dark = np.array(Image.open(r"/data/ESI/User/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/LEFT_RIGHT/20250206_FILTPOS_090_INTTIME_01p5/DEG_0/cfc_capture_1719353022833.tiff"))
print(img.shape)  # Will show (H, W) for grayscale or (H, W, C) for color

corrected = img.astype(np.int32) - dark.astype(np.int32)
corrected = np.clip(corrected, 0, 65535).astype(np.uint16)

corrected_image = Image.fromarray(corrected)
corrected_image.save(r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/corrected_test.png")
