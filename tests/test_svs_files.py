import py_wsi
import py_wsi.imagepy_toolkit as tk


file_dir = "//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/Pathology Data/P01/Beebe Data/H_E Slices/Original Scans/"
db_location = "h:/data"
xml_dir = file_dir
patch_size = 256
level = 17
db_name = "patch_db"
overlap = 0

# All possible labels mapped to integer ids in order of increasing severity.
label_map = {'Normal': 0,
             'Benign': 1,
             'Carcinoma in situ': 2,
             'In situ carcinoma': 2,
             'Carcinoma invasive': 3,
             'Invasive carcinoma': 3,
            }

turtle = py_wsi.Turtle(file_dir, db_location, db_name, xml_dir=xml_dir, label_map=label_map)
print("Total WSI images:    " + str(turtle.num_files))
print("LMDB name:           " + str(turtle.db_name))
print("File names:          " + str(turtle.files))
print("XML files found:     " + str(turtle.get_xml_files()))

file_name = '17009-1-Slice 1-001.svs'
level_count, level_tiles, level_dims = turtle.retrieve_tile_dimensions(file_name, patch_size=128)
print("Level count:         " + str(level_count))
print("Level tiles:         " + str(level_tiles))
print("Level dimensions:    " + str(level_dims))

patch_6 = turtle.retrieve_sample_patch(file_name, 1024*64, 16, overlap=12)

tk.show_images([patch_6], 1, 1)
