"""
__name__ =      Constants.py
__author__ =    "Charlemagne Marc"
__copyright__ = "Copyright 2025, ESI SWIR Project"
__credits__ =   ["Charlemagne Marc"]
__version__ =   "1.0.1"
__maintainer__ ="Charlemagne Marc"
__email__ =     "chamrc1@oumbc.edu"
__status__ =    "Production"
"""

#----------------------------------------------------------------------------
#-- CONSTANTS
#----------------------------------------------------------------------------
composite_save_path = r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/composite.png"
parabola_save_path = r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/along_track.png"
flatfield_save_path = r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/flatfield.png"
flatfield_plot_save_path = r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/flatfield_plot.png"
corrected_composite_save_path = r"/data/home/cmarc/SWIR_Projects/Flatfield/Images/corrected_composite.png"


directory_dict = {
    "crossTrack":  r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/LEFT_RIGHT/",
    "alongTrack" : r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/UP_DOWN/",
    "metadata" : r"/data/home/cjescobar/Projects/AirHARP2/SWIR/gits/AH2_SWIR_metadata_matcher/202502_SWIR_Flatfield_Matched_Metadata.csv"
    }

crossTrack_dict = {
    "050" : "20250206_FILTPOS_050_INTTIME_02p0",
    "090" : "20250206_FILTPOS_090_INTTIME_01p5",
    "130" : "20250206_FILTPOS_130_INTTIME_02p0",
    "169" : "20250206_FILTPOS_169_INTTIME_00p2"
}

crossTrackDark_dict = {
    "050" : "20250206_FILTPOS_010_INTTIME_02p0",
    "090" : "20250206_FILTPOS_010_INTTIME_01p5",
    "130" : "20250206_FILTPOS_130_INTTIME_02p0",
    "169" : "20250206_FILTPOS_010_INTTIME_00p2"
}

alongTrack_dict = {
    "050" : "20250205_FILTPOS_050_INTTIME_02p0",
    "090" : "20250205_FILTPOS_090_INTTIME_01p5",
    "130" : "20250205_FILTPOS_130_INTTIME_02p0" ,
    "169" : "20250205_FILTPOS_169_INTTIME_00p2",
    "02p0" : "20250205_FILTPOS_010_INTTIME_02p0",
    "01p5" : "20250205_FILTPOS_010_INTTIME_01p5",
    "00p2" : "20250205_FILTPOS_010_INTTIME_00p2"
}

alongTrackDark_dict = {
    "050" : "20250205_FILTPOS_010_INTTIME_02p0",
    "090" : "20250205_FILTPOS_010_INTTIME_01p5",
    "130" : "20250205_FILTPOS_010_INTTIME_02p0",
    "169" : "20250205_FILTPOS_010_INTTIME_00p2"
}