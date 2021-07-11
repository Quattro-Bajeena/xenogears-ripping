import subprocess
from pathlib import Path

def convert_map_blender(id, map_folder, disable_output):
    blender_script = Path(__file__).absolute().parent / "convert_map_blender.py"
    args = ["blender", "--background", "--python", blender_script, "--", map_folder, str(id)]
    process = subprocess.run(args, capture_output=True, text=True)

    if not disable_output:
        print(process.stdout)
        print(process.stderr)
        print("Conversion return code:", process.returncode)
