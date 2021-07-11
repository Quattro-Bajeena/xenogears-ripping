import bpy, sys
from pathlib import Path

if __name__ == '__main__':
    maps_folder = Path(sys.argv[-2])
    map_id = sys.argv[-1]
    print(sys.argv)
    print(maps_folder / f"Converted/level{map_id}.glb")