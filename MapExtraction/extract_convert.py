import time
from pathlib import Path

from map_extraction import load_and_save_map, convert_map_blender


ROOT = Path(__file__).parent.parent
rip_archive = ROOT / "ISOExtraction"
map_folder = ROOT / "Maps"

START_ID = 1
END_ID = 729 + 1

processing_start = time.time()


for map_id in range(START_ID, END_ID):  
    start = time.time()  
    load_and_save_map(map_id, rip_archive, map_folder / "Extracted", True)
    convert_map_blender(map_id, map_folder, True)
    end = time.time()
    print(f"Converted map {map_id} in {round(end-start, 2)}s")

processing_end = time.time()

print(f"Ripped and converted all maps in {round(processing_end - processing_start, 2)}s")