#if UNITY_EDITOR
using UnityEngine;
using System.Collections;
using UnityEditor;
using System.Text;
using System.Collections.Generic;
using UnityEngine.SceneManagement;
using UnityEditor.SceneManagement;
using System.Linq;
using System.IO;

public class ExportXenogears : ScriptableWizard
{


    [MenuItem("File/Export/Xenogears OBJ")]
    static void CreateWizard()
    {
        ScriptableWizard.DisplayWizard("Export Xenogears", typeof(ExportXenogears), "Export");
    }


    void OnWizardCreate()
	{
		string lastPath = EditorPrefs.GetString("a4_XenogearsExport_lastPath", "");
		string expFolder = EditorUtility.SaveFolderPanel("Export OBJ", lastPath, "");
		if (expFolder.Length <= 0)
		{
			return;
		}
		EditorPrefs.SetString("a4_XenogearsExport_lastPath", expFolder);

		Debug.Log(expFolder);

		var exporter = ScriptableObject.CreateInstance<OBJExporter>();

        string[] scene_assets = AssetDatabase.FindAssets("*", new[] { "Assets/SceneModel/Scene" });
        string[] scene_paths = scene_assets.Select( scene_guid => AssetDatabase.GUIDToAssetPath(scene_guid)).ToArray();

		foreach (string scene_path in scene_paths)
		{
			string fileName = Path.GetFileNameWithoutExtension(scene_path);
			Directory.CreateDirectory(Path.Combine(expFolder, fileName));
			
			EditorSceneManager.OpenScene(scene_path);
			exporter.Export(Path.Combine(new string[] { expFolder, fileName, fileName + ".obj" }));
        }

	}
}
#endif