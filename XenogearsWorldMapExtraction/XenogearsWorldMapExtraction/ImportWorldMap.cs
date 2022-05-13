using System;
using System.IO;
using System.Collections.Generic;
using System.Numerics;
using System.Drawing;

public static class ImportWorldMap
{

	static byte[] decompressLzs(byte[] ibuf, uint ofs, uint size)
	{
		byte[] obuf = new byte[size];
		uint iofs = ofs;
		uint oofs = 0;
		uint cmd = 0;
		uint bit = 0;
		while (iofs < ibuf.Length && oofs < obuf.Length)
		{
			if (bit == 0)
			{
				cmd = ibuf[iofs++];
				bit = 8;
			}
			if ((cmd & 1) != 0)
			{
				byte a = ibuf[iofs++];
				byte b = ibuf[iofs++];
				uint o = (uint)a | ((uint)(b & 0x0F) << 8);
				uint l = (((uint)b & 0xF0) >> 4) + 3;
				int rofs = (int)oofs - (int)o;
				// UnityEngine.Debug.Log("oofs:"+oofs+" iofs:"+iofs+" rofs:"+rofs+" l:"+l+" o:"+o+" size:"+size+" a:"+a+" b:"+b);
				for (int j = 0; j < l; j++)
				{
					if (rofs < 0)
					{
						obuf[oofs++] = 0;
					}
					else
					{
						obuf[oofs++] = obuf[rofs];
					}
					rofs++;
				}
			}
			else if (oofs < obuf.Length)
			{
				// UnityEngine.Debug.Log("oofs:"+oofs+" iofs:"+iofs);
				obuf[oofs++] = ibuf[iofs++];
			}
			cmd >>= 1;
			bit -= 1;
		}
		return obuf;
	}

	static byte[] loadLzs(string path)
	{
		byte[] buf = File.ReadAllBytes(path);
		uint length = getUInt32LE(buf, 0);
		return decompressLzs(buf, 4, length);
	}

	static ushort getUInt16LE(byte[] buf, uint ofs)
	{
		return (ushort)(((ushort)buf[ofs + 1] << 8) | (ushort)buf[ofs + 0]);
	}

	static uint getUInt32LE(byte[] buf, uint ofs)
	{
		return ((uint)buf[ofs + 3] << 24) | ((uint)buf[ofs + 2] << 16) | ((uint)buf[ofs + 1] << 8) | (uint)buf[ofs + 0];
	}


	public struct MapTile
	{
		public Bitmap bitmap;
		public Vector2 offset;
	}

	static MapTile[,] ImportTextures(byte[] data, byte[] textureData)
	{
		var mapTiles = new MapTile[4, 4];

		for (uint ytex = 0; ytex < 4; ytex++)
		{
			for (uint xtex = 0; xtex < 4; xtex++)
			{
				//Color[] image = new Color[1024 * 1024];
				var bitmap = new Bitmap(1024, 1024);
				for (uint i = 0; i < 4; i++)
				{
					for (uint j = 0; j < 4; j++)
					{
						uint terrainOffset = ((i + ytex * 4) * 16 + (j + xtex * 4)) * 2048;
						for (int y = 0; y < 16; y++)
						{
							for (int x = 0; x < 16; x++)
							{
								// Debug.Log ("i:"+i+" j:"+j+" y:"+y+" x:"+x);
								int xt = x / 8;
								int yt = y / 8;
								int xp = x % 8;
								int yp = y % 8;
								uint adr = (uint)(terrainOffset + ((yt * 2 + xt) * 9 * 9 + yp * 9 + xp) * 4);

								byte attr = data[adr + 1];
								bool water = (attr & 0x10) != 0;
								bool flipU = (attr & 0x20) != 0;
								bool flipV = (attr & 0x40) != 0;
								uint textureIdx = (uint)(attr & 0x7);

								byte uv = data[adr + 2];
								int v = (uv >> 4) * 16;
								int u = (uv & 0xF) * 16;
								uint textureOffset = getUInt32LE(textureData, 4 + textureIdx * 4);
								for (int yy = 0; yy < 16; yy++)
								{
									for (int xx = 0; xx < 16; xx++)
									{
										int yf = flipV ? 15 - yy : yy;
										int xf = flipU ? 15 - xx : xx;
										int index = textureData[textureOffset + 0x220 + (v + yf) * 256 + (u + xf)];
										ushort col = getUInt16LE(textureData, (uint)(textureOffset + 0x14 + index * 2));
										float r = (float)((col) & 31) / 31.0f;
										float g = (float)((col >> 5) & 31) / 31.0f;
										float b = (float)((col >> 10) & 31) / 31.0f;

										var color = Color.FromArgb(255, (int)Math.Round(r * 255), (int)Math.Round(g * 255), (int)Math.Round(b * 255));

										//image[((j * 16 + x) * 16 + xx) * 1024 + ((i * 16 + y) * 16 + yy)] = new Color(r, g, b, 1.0f);

										bitmap.SetPixel((int)((i * 16 + y) * 16 + yy), (int)((j * 16 + x) * 16 + xx), color);

									}
								}
							}
						}
					}
				}

				//Texture2D texture = new Texture2D(1024, 1024);
				//texture.name = "texture" + (ytex * 4 + xtex);
				//texture.wrapMode = TextureWrapMode.Clamp;
				//texture.SetPixels(image);
				//texture.Apply();
				//AssetDatabase.AddObjectToAsset(texture, prefab);

				//SplatPrototype splatPrototype = new SplatPrototype();
				//splatPrototype.texture = texture;
				//splatPrototype.tileOffset = new Vector2(-ytex * 64, -xtex * 64);
				//splatPrototype.tileSize = new Vector2(64, 64);
				//splatPrototypes[ytex * 4 + xtex] = splatPrototype;

				var tile = new MapTile();
				tile.bitmap = bitmap;
				tile.offset = new Vector2(-ytex * 64, -xtex * 64);
				mapTiles[xtex, ytex] = tile;

			}
		}
		return mapTiles;
	}

	static Bitmap ImportHeightMap(byte[] data)
	{
		//var heights = new float[256, 256];
		var heightsBitmap = new Bitmap(256, 256);
		for (uint i = 0; i < 16; i++)
		{
			for (uint j = 0; j < 16; j++)
			{
				uint terrainOffset = (i * 16 + j) * 2048;
				for (int y = 0; y < 16; y++)
				{
					for (int x = 0; x < 16; x++)
					{
						int xt = x / 8;
						int yt = y / 8;
						int xp = x % 8;
						int yp = y % 8;
						uint adr = (uint)(terrainOffset + ((yt * 2 + xt) * 9 * 9 + yp * 9 + xp) * 4);

						byte attr = data[adr + 1];
						bool water = (attr & 0x10) != 0; // ?
						bool flipU = (attr & 0x20) != 0;
						bool flipV = (attr & 0x40) != 0;

						byte uv = data[adr + 2];
						int v = (uv >> 4) * 16;
						int u = (uv & 0xF) * 16;
						int h = -((sbyte)data[adr + 0]);

						//heights[j * 16 + x, i * 16 + y] = ((float)h) / 128.0f;

						var grayScale = (int)Math.Round((h / 128.0f + 1) * 255 / 2);
						heightsBitmap.SetPixel((int)((j * 16) + x), (int)((i * 16) + y), Color.FromArgb(255, grayScale, grayScale, grayScale));
					}
				}
			}
		}



		//TerrainData terrainData = new TerrainData();
		//terrainData.name = "terrain";
		//terrainData.heightmapResolution = 256;
		//terrainData.size = new Vector3(256, 16, 256);
		//terrainData.SetHeights(0, 0, heights);
		//terrainData.alphamapResolution = 64;
		//terrainData.splatPrototypes = splatPrototypes;

		return heightsBitmap;
	}

	static Bitmap GenerateAlpha()
	{
		// Blend the textures
		int alphaRes = 64;
		int alphaLayers = 16;


		var alphaMapBitmap = new Bitmap(alphaRes, alphaRes);
		float[,,] alphaData = new float[alphaRes, alphaRes, alphaLayers];
		int dw = 64 / 4;
		int dh = 64 / 4;
		for (int i = 0; i < alphaRes; i++)
		{
			for (int j = 0; j < alphaRes; j++)
			{
				int idx = (i / dw) + (j / dh) * 4;
				for (int k = 0; k < alphaLayers; k++)
				{
					var alphaValue = k != idx ? 0.0f : 1.0f;
					alphaData[i, j, k] = alphaValue;


					var prevCol = alphaMapBitmap.GetPixel(i, j);

					var value = 255 / (k + 1);

					if(prevCol.A == 0)
					{
						var color = Color.FromArgb((int)(alphaValue * 255), value, value, value);
						alphaMapBitmap.SetPixel(i, j, color);
					}
						
					//alphaMapBitmap.SetPixel(i + alphaRes * col, j + alphaRes * row, color);
				}
			}
		}

		return alphaMapBitmap;
	}

	static void ImportTerrain(uint fileIndex)
	{
		uint diskIndex = 1; // there are disk 1 and disk 2
		uint dirIndex = 26 + fileIndex; // 0-based index

		var projectDir = AppDomain.CurrentDomain.BaseDirectory;

		string dataPath = "Data";
		string terrainPath = Path.Combine(dataPath, Path.Combine("disk" + diskIndex, "dir" + dirIndex));
		string filePath = Path.Combine(terrainPath, "file" + 8 + ".bin");
		string texturePath = Path.Combine(terrainPath, "file" + 1 + ".bin");




		byte[] data = File.ReadAllBytes(filePath);
		byte[] textureData = loadLzs(texturePath);


		//var alphaMapBitmap = GenerateAlpha();
		//alphaMapBitmap.Save("alphaMap.bmp");


		//var heightsBitmap = ImportHeightMap(data);
		//heightsBitmap.Save("heightmap.bmp");

		var mapTiles = ImportTextures(data, textureData);
		var mapRes = 4;
		var worldBitmap = new Bitmap(1024 * mapRes, 1024 * mapRes);
		var tileSize = 1024;
		for (int i = 0; i < mapRes; i++)
		{
			for (int j = 0; j < mapRes; j++)
			{
				var tile = mapTiles[i, j];
				Console.WriteLine(tile.offset);
				//tile.bitmap.Save($"MapTile_{i}_{j}_{tile.offset.X}_{tile.offset.Y}.bmp");

				tile.bitmap.RotateFlip(RotateFlipType.Rotate270FlipY);

				for (int x = 0; x < tileSize; x++)
				{
					for (int y = 0; y < tileSize; y++)
					{
						var sampleX = x;
						var sampleY = y;
					
						worldBitmap.SetPixel(x + i * tileSize, y + j * tileSize, tile.bitmap.GetPixel(sampleX, sampleY));
					}
				}

			}
		}

		worldBitmap.Save("World.bmp");


	}

	public static void Main()
	{
		ImportWorldMap.ImportTerrain(0);
	}

}

