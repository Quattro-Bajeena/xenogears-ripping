from .xgl import sloppy_open, getData, loadModel, loadTextures, getNodes, saveModel
from pathlib import Path

#MAP_FOLDER = Path(__file__).absolute().parent.parent / "Maps" / "Extracted"

def load_and_save_map(file_no, rip_archive : Path, map_folder : Path):
    print("loading archive...")
    diskIndex = 1 # there are disk 1 and disk 2
    dirIndex = 11 # 0-based index
    #fileIndex = int(argv[0]) # 0-based index
    fileIndex = file_no # 1 to 729
    #archivePath = os.path.join("STRIPCD%i" % diskIndex, "%i" % dirIndex, "%04d" % (fileIndex * 2))
    #archivePath = ROOT / f"STRIPCD{diskIndex}" / str(dirIndex) / f"{fileIndex*2:04d}"
    archivePath = rip_archive / f"STRIPCD{diskIndex}" / str(dirIndex) / f"{fileIndex*2:04d}"

    f = sloppy_open(archivePath)
    archiveData = f.read()
    f.close()

    if archiveData[:4] == "It's":
    # file was removed from disk image
        print("This file was removed from the disk image. Most likely it is a room that is not reachable any more.")
        return 0

    modelData = getData(archiveData, 2)

    print("loading texture...")
    #texturePath = os.path.join("STRIPCD%i" % diskIndex, "%i" % dirIndex, "%04d" % (fileIndex * 2 + 1))
    texturePath = rip_archive / f"STRIPCD{diskIndex}" / str(dirIndex) / f"{fileIndex*2+1:04d}"
    print(texturePath)

    f = sloppy_open(texturePath)
    textureData = f.read()
    f.close()

    print("converting meshes...")
    model = loadModel(modelData)

    print("converting textures...")
    model["textures"] = loadTextures(textureData, model["shaders"])

    print("getting nodes...")
    model["nodes"] = getNodes(archiveData)

    print("saving model")
    target_folder = map_folder / str(fileIndex)
    target_folder.mkdir(exist_ok=True)
    saveModel(target_folder / f"level{fileIndex}.dae", model)