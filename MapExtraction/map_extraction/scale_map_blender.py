import bpy, sys
from math import radians
from pathlib import Path

def import_map(map_id, maps_folder:Path):
    bpy.ops.import_scene.gltf(filepath= str(maps_folder / f"Converted/level{map_id}.glb"))
    
def scale_map():
    bpy.ops.object.select_all(action='SELECT')

    bpy.ops.transform.resize(
        value=(0.04, 0.04, 0.04), orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1 , 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
        constraint_axis=(True, False, False),
        center_override=(0,0,0)
    )



def export_map(map_id, maps_folder:Path):
    bpy.ops.export_scene.gltf(
        filepath= str(maps_folder / f"Scaled/level{map_id}.glb"),
        export_format = 'GLB',
        export_image_format = 'AUTO',
        export_texcoords = True,
        export_normals = True,
        export_materials = 'EXPORT',
        export_colors = True
    )
    
def delete_all():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete() 

if __name__ == '__main__':
    maps_folder = Path(sys.argv[-2])
    #maps_folder = Path("F:\Programowanie\XenogearsRipping\Maps")
    map_id = sys.argv[-1]
    #map_id = 1
    
    #delete_all()
    import_map(map_id, maps_folder)
    scale_map()
    export_map(map_id, maps_folder)
    
    
