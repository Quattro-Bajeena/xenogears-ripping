import time
from pathlib import Path

from map_extraction import scale_map_launch

ROOT = Path(__file__).parent.parent
rip_archive = ROOT / "ISOExtraction"
map_folder = ROOT / "Maps"

START_ID = 1
END_ID = 729 + 1

processing_start = time.time()


for map_id in range(START_ID, END_ID):  
    start = time.time()  
    scale_map_launch(map_id, map_folder, True)
    end = time.time()
    print(f"Scaled map {map_id} in {round(end-start, 2)}s")

processing_end = time.time()

print(f"Scaled all maps in {round(processing_end - processing_start, 2)}s")