from pathlib import Path

from map_extraction import load_and_save_map


ROOT = Path(__file__).parent.parent
rip_archive = ROOT / "ISOExtraction"
map_folder = ROOT / "Maps" / "Extracted"

load_and_save_map(729, rip_archive, map_folder)