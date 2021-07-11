import bpy, sys
from math import radians
from pathlib import Path

def import_map(map_id, maps_folder:Path):
	print(f"Importing map {map_id}")
	bpy.ops.wm.collada_import(filepath= str(maps_folder / f"Extracted/{map_id}/level{map_id}.dae"))
	print("Imported")
	
def rotate_map():
	print("Rotating map")
	bpy.ops.object.select_all(action='SELECT')

	# Hack to fix a bug https://stackoverflow.com/q/67659621/15990870
	ov = bpy.context.copy()
	ov['area']=[a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]

	bpy.ops.transform.rotate(ov,
		value=radians(-90), orient_axis='X', orient_type='GLOBAL',
	 	orient_matrix=((1, 0, 0), (0, 1 , 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
	 	constraint_axis=(True, False, False)
	)

def change_tex_filtering():
	print("Changing texture filtering")
	for mat in bpy.data.materials:
	    if mat.node_tree:
	        for node in mat.node_tree.nodes:
	            if node.type == 'TEX_IMAGE':
	                node.interpolation = 'Closest'
	


def export_map(map_id, maps_folder:Path):
	print(f"Exporting map {map_id}")
	bpy.ops.export_scene.gltf(
		filepath= str(maps_folder / f"Converted/level{map_id}.glb"),
		export_format = 'GLB',
		export_image_format = 'AUTO',
		export_texcoords = True,
		export_normals = True,
		export_materials = 'EXPORT',
		export_colors = True
	)
	print("Exported")
	
def delete_all():
	print("Deleting objects")
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete() 

if __name__ == '__main__':
	maps_folder = Path(sys.argv[-2])
	map_id = sys.argv[-1]
	import_map(map_id, maps_folder)
	rotate_map()
	change_tex_filtering()
	export_map(map_id, maps_folder)
	#delete_all()
