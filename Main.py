#----------------------------------------------------------------------------
#-- IMPORT STATEMENTS
#----------------------------------------------------------------------------
from project_modules.CompositeProcessor import CompositeProcessor
from project_modules.CompositeProcessor import plot_composite
from project_modules.Constants import directory_dict, crossTrack_dict, crossTrackDark_dict, alongTrack_dict, alongTrackDark_dict
import sys 

#----------------------------------------------------------------------------
#-- main - main function
#----------------------------------------------------------------------------
def main():
    # crossTrack_dir = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/LEFT_RIGHT/"
    # alongTrack_dir = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/raw_data/2025_SWIR_Flatfield/UP_DOWN/"
    # metadata = r"/data/home/cjescobar/Projects/AirHARP2/SWIR/gits/AH2_SWIR_metadata_matcher/202502_SWIR_Flatfield_Matched_Metadata.csv"\

    crossTrack_processor = CompositeProcessor(directory_dict["crossTrack"], directory_dict["metadata"])
    alongTrack_processor = CompositeProcessor(directory_dict["alongTrack"], directory_dict["metadata"])
    wheel_pos = sys.argv[1]
    num_sigma = float(sys.argv[2])

    if not wheel_pos.isdigit:
        print("Enter correct wheel pos")
        sys.exit()

    cross_filter_pos = crossTrack_dict[wheel_pos]
    cross_dark_pos = crossTrackDark_dict[wheel_pos]
    along_filter_pos = alongTrack_dict[wheel_pos]
    along_dark_pos = alongTrackDark_dict[wheel_pos]

    # take the composite image and take the an along-track row
    # take the array of counts from the row and graph
    composite_image = crossTrack_processor.generate_composite(cross_filter_pos, cross_dark_pos) +\
        alongTrack_processor.generate_composite(along_filter_pos, along_dark_pos)  
    plot_composite(composite_image)

    # Plot parabola cores from alongTrack 
    crossTrack_processor.plot_parabola_cores(cross_filter_pos, cross_dark_pos, core=True, along_track_pos=600)

    # find flatfiled
    crossTrack_processor.plot_flatfield(cross_filter_pos, cross_dark_pos, num_sigma, along_track_pos=600)

if __name__ == "__main__":
    main()
