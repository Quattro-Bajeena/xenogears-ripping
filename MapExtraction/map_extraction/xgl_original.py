import sys, struct, array, math, os

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
from pygame.locals import *

def decompressLzs(data, size):
    """Decompress Xenogears-style compressed data. The data must exclude the initial size word"""
    ibuf = array.array("B", data)
    obuf = array.array("B")
   
    iofs = 0
    cmd = 0
    bit = 0
    while iofs < len(ibuf) and len(obuf) < size:
	if bit == 0:
	    cmd = ibuf[iofs]
	    bit = 8
	    iofs += 1
	if cmd & 1:
	    a = ibuf[iofs]
	    iofs += 1
	    b = ibuf[iofs]
	    iofs += 1
	   
	    o = a | ((b & 0x0F) << 8)
	    l = ((b & 0xF0) >> 4) + 3

	    rofs = len(obuf) - o
	    for j in xrange(l):
		if rofs < 0:
		    obuf.append(0)
		else:
		    obuf.append(obuf[rofs])
		rofs += 1
	else:
	    obuf.append(ibuf[iofs])
	    iofs += 1

	cmd >>= 1
	bit -= 1

    return obuf.tostring()

def loadLzs(name):
    """Read a compressed file from disc"""
    f = open(name, "rb")
    buf = f.read()
    f.close()   
    (size,) = struct.unpack_from("<I", buf, 0)
    return decompressLzs(buf[4:], size)

def getData(archiveData, index):
    """Get the compressed data block out of the field map archive"""
    (offset,) = struct.unpack_from("<I", archiveData, 0x0130 + index * 4)
    dataEnd = len(archiveData)
    if index < 8:
	(dataEnd,) = struct.unpack_from("<I", archiveData, 0x0134 + index * 4)

    (size,) = struct.unpack_from("<I", archiveData, 0x010c + index * 4)

    dataStart = offset + 4
    return decompressLzs(archiveData[dataStart:dataEnd], size)
	
class ShaderBuilder:
    def __init__(self):
	self.shaders = {}
	
    def getShader(self, data):
	try:
	    return self.shaders[data]
	except KeyError:
	    i = len(self.shaders)
	    self.shaders[data] = i
	    return i
	   
    def getList(self):
	items = [(val, key) for (key, val) in self.shaders.items()]
	items.sort()
	return [x for _,x in items]

abe_alpha = [128, 0, 0, 64]

def loadModel(data):
    shaderBuilder = ShaderBuilder()

    object = {}
    object["parts"] = []

    (partCount,) = struct.unpack_from("<I", data, 0)
    for partIndex in xrange(partCount):
	(partOffset,) = struct.unpack_from("<I", data, 4 + partIndex * 4)

	part = {}
	part["blocks"] = []
	(blockCount,) = struct.unpack_from("<I", data, partOffset)
	for blockIndex in xrange(blockCount):
	    blockOffset = partOffset + 16 + blockIndex * 0x38

	    (vertexCount, meshCount, meshBlockCount, vertexOffset, normalOffset, meshBlockOffset, displayListOffset) = struct.unpack_from("<xxHHHIIII", data, blockOffset)

	    tri_tex = []
	    quad_tex = []
	    tri_mono = []
	    quad_mono = []

	    status = 0
	    clut = 0
	    for meshBlockIndex in xrange(meshBlockCount):
		# init the mesh block
		quad_block, polyCount = struct.unpack_from("<BxH", data, partOffset + meshBlockOffset)
		meshBlockOffset += 4
		
		while polyCount > 0:
	
		    # decode command
		    (cmd,) = struct.unpack_from("<I", data, partOffset + displayListOffset)
		   
		    hp = ((cmd >> 24) & 16) != 0	    # geraud shading
		    quad = ((cmd >> 24) & 8) != 0	    # quad or tri
		    tme = ((cmd >> 24) & 4) != 0	    # texture mapping
		    abe = ((cmd >> 24) & 2) != 0	    # semi transparency
		    fullbright = ((cmd >> 24) & 1) != 0	    # bypass lighting
		    op = (cmd >> 24) & 255		    # operator
		    pop = op & ~(16|2|1)		    # operator, with shading and lighting mask

		    displayListOffset += 4
		    if op == 0xC4: # texture page
			status = cmd & 0xFFFF
		    elif op == 0xC8: # clut
			clut = cmd & 0xFFFF
		    elif pop == 0x24: # triangle with texture	
			(ua, va, ub, vb) = struct.unpack_from("<BBBB", data, partOffset + displayListOffset)
			uc = cmd & 255
			vc = (cmd >> 8) & 255
			displayListOffset += 4
			
			shader = shaderBuilder.getShader((status, clut, abe, True))
			
			vertex = []
			for j in xrange(3):
			    (vtx,) = struct.unpack_from("<H", data, partOffset + meshBlockOffset + j * 2)
			    (x, y, z) = struct.unpack_from("<hhh", data, partOffset + vertexOffset + vtx * 8)
			    if hp:
				(nx, ny, nz) = struct.unpack_from("<hhh", data, partOffset + normalOffset + vtx * 8)
			    else:
				(nx, ny, nz) = (0, 0, 0)
			    vertex.append(((x, y, z), (nx, ny, nz)))
			   
			tri_tex.append((shader, ((vertex[0][0], vertex[0][1], (ua, va)), (vertex[2][0], vertex[2][1], (uc, vc)), (vertex[1][0], vertex[1][1], (ub, vb)))))
			
			meshBlockOffset += 8
			polyCount -= 1
		    elif pop == 0x2C: # quad with texture					
			(ua, va, ub, vb, uc, vc, ud, vd) = struct.unpack_from("<BBBBBBBB", data, partOffset + displayListOffset)
			displayListOffset += 8

			shader = shaderBuilder.getShader((status, clut, abe, True))
			
			vertex = []
			for j in xrange(4):
			    (vtx,) = struct.unpack_from("<H", data, partOffset + meshBlockOffset + j * 2)
			    (x, y, z) = struct.unpack_from("<hhh", data, partOffset + vertexOffset + vtx * 8)
			    if hp:
				(nx, ny, nz) = struct.unpack_from("<hhh", data, partOffset + normalOffset + vtx * 8)
			    else:
				(nx, ny, nz) = (0, 0, 0)
			    vertex.append(((x, y, z), (nx, ny, nz)))
			
			quad_tex.append((shader, ((vertex[1][0], vertex[1][1], (ub, vb)), (vertex[0][0], vertex[0][1], (ua, va)), (vertex[2][0], vertex[2][1], (uc, vc)), (vertex[3][0], vertex[3][1], (ud, vd)))))
			
			meshBlockOffset += 8
			polyCount -= 1
		    elif pop == 0x20: # monochrome triangle
			if abe:
			    abr = (status >> 5) & 3
			    alpha = abe_alpha[abr]
			else:
			    alpha = 255
		   
			col = ((cmd >> 16) & 255, (cmd >> 8) & 255, (cmd) & 255, alpha)

			shader = shaderBuilder.getShader((status, clut, abe, False))

			vertex = []
			for j in xrange(3):
			    (vtx,) = struct.unpack_from("<H", data, partOffset + meshBlockOffset + j * 2)
			    (x, y, z) = struct.unpack_from("<hhh", data, partOffset + vertexOffset + vtx * 8)
			    if hp:
				(nx, ny, nz) = struct.unpack_from("<hhh", data, partOffset + normalOffset + vtx * 8)
			    else:
				(nx, ny, nz) = (0, 0, 0)
			    vertex.append(((x, y, z), (nx, ny, nz)))

			tri_mono.append((shader, ((vertex[0][0], vertex[0][1], col), (vertex[2][0], vertex[2][1], col), (vertex[1][0], vertex[1][1], col))))
			
			meshBlockOffset += 8
			polyCount -= 1
		    elif pop == 0x28: # monochrome quad
			if abe:
			    abr = (status >> 5) & 3
			    alpha = abe_alpha[abr]
			else:
			    alpha = 255

			col = ((cmd >> 16) & 255, (cmd >> 8) & 255, (cmd) & 255, alpha)

			shader = shaderBuilder.getShader((status, clut, abe, False))

			vertex = []
			for j in xrange(4):
			    (vtx,) = struct.unpack_from("<H", data, partOffset + meshBlockOffset + j * 2)
			    (x, y, z) = struct.unpack_from("<hhh", data, partOffset + vertexOffset + vtx * 8)
			    if hp:
				(nx, ny, nz) = struct.unpack_from("<hhh", data, partOffset + normalOffset + vtx * 8)
			    else:
				(nx, ny, nz) = (0, 0, 0)
			    vertex.append(((x, y, z), (nx, ny, nz)))

			quad_mono.append((shader, ((vertex[1][0], vertex[1][1], col), (vertex[0][0], vertex[0][1], col), (vertex[2][0], vertex[2][1], col), (vertex[3][0], vertex[3][1], col))))
			
			meshBlockOffset += 8
			polyCount -= 1
		    else:
			print("unknown cmd: %8.8x\n" % cmd)
	    block = {}
	    block["tri_tex"] = tri_tex
	    block["quad_tex"] = quad_tex
	    block["tri_mono"] = tri_mono
	    block["quad_mono"] = quad_mono
	    part["blocks"].append(block)
	object["parts"].append(part)
    object["shaders"] = shaderBuilder.getList()
   
    return object

def getColour(col, abe, alpha):
    stp = (col & 0x8000) != 0
    r = (((col     ) & 31) * 255 + 15) / 31
    g = (((col >>  5) & 31) * 255 + 15) / 31
    b = (((col >> 10) & 31) * 255 + 15) / 31
    if (col & 0x7FFF) == 0:
	if stp:
	    a = 255
	else:
	    a = 0
    elif stp and abe:
	a = alpha
    else:
	a = 255
    return (r<<24)|(g<<16)|(b<<8)|a
   
def loadTextures(textureData, shaderList):
    vram = array.array("B", [0] * (2048 * 1024))

    # unpack MIM data into "VRAM"
    offset = 0
    while offset < len(textureData):
	header = offset
	(type, pos_x, pos_y, move_x, move_y, width, height, chunks) = struct.unpack_from("<IHHHHHHxxH", textureData, header)
	# print (type, pos_x, pos_y, move_x, move_y, width, height, chunks)
	blockSize = 0x1C + chunks * 2
	offset += (blockSize + 2047) & ~2047
	for i in xrange(chunks):
	    (height,) = struct.unpack_from("<H", textureData, header + 0x1C)
	    for j in xrange(height):
		vramAddr = (pos_y + move_y + j) * 2048 + (pos_x + move_x) * 2
		texAddr = offset + j * width * 2
		for k in xrange(width * 2):
		    vram[vramAddr] = ord(textureData[texAddr])
		    vramAddr += 1
		    texAddr += 1
	    pos_y += height
	    blockSize = width * height * 2
	    offset += (blockSize + 2047) & ~2047
    if False:
	f = open("vram.bin", "wb")
	vram.tofile(f)
	f.close()
   
    # convert textures with their palette
    textures = []
    for shader in shaderList:
	(status, clut, abe, tme) = shader
	if tme:
	    tx = (status & 0xF) * 64 * 2
	    ty = ((status >> 4) & 1) * 256
	    abr = (status >> 5) & 3
	    tp = (status >> 7) & 3
	    px = (clut & 63) * 16
	    py = clut >> 6
	   
	    if abe:
		alpha = abe_alpha[abr]
	    else:
		alpha = 0
	   
	    image = array.array("I")
	    if tp == 0: # 4-bit
		pal = array.array("I")
		for idx in xrange(16):
		    vaddr = py * 2048 + idx * 2 + px * 2
		    col = vram[vaddr] + vram[vaddr+1] * 256
		    pal.append(getColour(col, abe, alpha))
		for y in xrange(256):
		    for x in xrange(256):
			val = vram[(y + ty) * 2048 + (x/2) + tx]
			if x & 1:
			    idx = val >> 4
			else:
			    idx = val & 0xF
			image.append(pal[idx])
		del pal
	    elif tp == 1:
		pal = array.array("I")
		for idx in xrange(256):
		    vaddr = py * 2048 + idx * 2 + px * 2
		    col = vram[vaddr] + vram[vaddr+1] * 256
		    pal.append(getColour(col, abe, alpha))
		for y in xrange(256):
		    for x in xrange(256):
			idx = vram[(y + ty) * 2048 + x + tx];
			image.append(pal[idx])
		del pal
	    elif tp == 2:
		for y in xrange(256):
		    for x in xrange(256):
			vaddr = (y + ty) * 2048 + x * 2 + tx
			col = vram[vaddr] + vram[vaddr+1] * 256
			image.append(getColour(col, abe, alpha))
	    	
	    textures.append(image.tostring())
	    del image
	else:
	    textures.append(None)

    del vram
    return textures

class OpenGLObject:
    def __init__(self, model):
	self.model = model
	self.drawNormals = False
	self.list = None
	self.abe = None
	self.abr = None
	self.texture = None

	self.textureList = []
	for t in model["textures"]:
	    if t is not None:
		texIndex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texIndex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8, t)
		if True:
		    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		else:
		    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
		self.textureList.append(texIndex)
	    else:
		self.textureList.append(None)
	
    def setBlend(self, status, abe):
	if abe:
	    if self.abe != abe:
		self.abe = abe
		glEnable(GL_BLEND)
		glDisable(GL_ALPHA_TEST)
	    abr = (status >> 3) & 3
	    if self.abr != abr:
		self.abr = abr
		if abr == 0:
		    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		    glBlendEquation(GL_FUNC_ADD);
		elif abr == 1:
		    glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
		    glBlendEquation(GL_FUNC_ADD);
		elif abr == 2:
		    glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
		    glBlendEquation(GL_FUNC_SUBTRACT);
		elif abr == 3:
		    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		    glBlendEquation(GL_FUNC_ADD);
	else:
	    if self.abe != abe:
		self.abe = abe
		glDisable(GL_BLEND)
		glEnable(GL_ALPHA_TEST)
		glAlphaFunc(GL_GREATER, 0.0)
   
    def setTexture(self, texture):
	if self.texture != texture:
	    self.texture = texture
	    glBindTexture(GL_TEXTURE_2D, texture)
   
    def drawPart(self, part, trans):
	for block in part["blocks"]:
	    glDisable(GL_TEXTURE_2D);
	    # glColor4ub(255,255,255,255)
	    if len(block["tri_mono"]) > 0:
		for tri_mono in block["tri_mono"]:
		    (status, _, abe, tme) = self.model["shaders"][tri_mono[0]]
		    if (abe and trans) or (not abe and not trans):
			self.setBlend(status, abe)
			glBegin(GL_TRIANGLES)
			for j in xrange(3):
			    pos, normal, colour = tri_mono[1][j]
			    glColor4ub(colour[0], colour[1], colour[2], colour[3])
			    glNormal3f(normal[0] / 4096.0, normal[1] / 4096.0, normal[2] / 4096.0)
			    glVertex3i(pos[0], pos[1], pos[2])
			glEnd()
	    if len(block["quad_mono"]) > 0:
		for quad_mono in block["quad_mono"]:
		    (status, _, abe, tme) = self.model["shaders"][quad_mono[0]]
		    if (abe and trans) or (not abe and not trans):
			self.setBlend(status, abe)
			glBegin(GL_QUADS)
			for j in xrange(4):
			    pos, normal, colour = quad_mono[1][j]
			    glColor4ub(colour[0], colour[1], colour[2], colour[3])
			    glNormal3f(normal[0] / 4096.0, normal[1] / 4096.0, normal[2] / 4096.0)
			    glVertex3i(pos[0], pos[1], pos[2])
			glEnd()

	    # glColor4ub(255,255,255,255)
	    if True:
		glEnable(GL_TEXTURE_2D)
		if len(block["tri_tex"]) > 0:
		    for tri_tex in block["tri_tex"]:
			(status, _, abe, tme) = self.model["shaders"][tri_tex[0]]
			if (abe and trans) or (not abe and not trans):
			    self.setBlend(status, abe)
			    self.setTexture(self.textureList[tri_tex[0]])
			    glBegin(GL_TRIANGLES)
			    for j in xrange(3):
				pos, normal, uv = tri_tex[1][j]
				glTexCoord2i(uv[0], uv[1])
				glNormal3f(normal[0] / 4096.0, normal[1] / 4096.0, normal[2] / 4096.0)
				glVertex3i(pos[0], pos[1], pos[2])
			    glEnd()

		if len(block["quad_tex"]) > 0:
		    for quad_tex in block["quad_tex"]:
			(status, _, abe, tme) = self.model["shaders"][quad_tex[0]]
			if (abe and trans) or (not abe and not trans):
			    self.setBlend(status, abe)
			    self.setTexture(self.textureList[quad_tex[0]])
			    glBegin(GL_QUADS)
			    for j in xrange(4):
				pos, normal, uv = quad_tex[1][j]
				glTexCoord2i(uv[0], uv[1])
				glNormal3f(normal[0] / 4096.0, normal[1] / 4096.0, normal[2] / 4096.0)
				glVertex3i(pos[0], pos[1], pos[2])
			    glEnd()
   
    def draw(self):
	glMatrixMode(GL_TEXTURE)
	glLoadIdentity()
	glScalef(1.0/256.0, 1.0/256.0, 0)
	glTranslatef(0.5, 0.5, 0.0)
   
	glMatrixMode(GL_MODELVIEW)
	glRotatef(180, 1, 0, 0)
	
	if self.list is None:
	    self.list = glGenLists(1)
	    glNewList(self.list, GL_COMPILE_AND_EXECUTE)

	    # render opaque objects
	    glDepthMask(GL_TRUE)
	    for item in self.model["nodes"]:
		(flags, index, pos, rot) = item
		if flags != 480:
		    glPushMatrix()
		    glTranslatef(pos[0], pos[1], pos[2])
		    glRotatef(rot[0] * 90.0 / 1024.0, 1, 0, 0)
		    glRotatef(rot[1] * 90.0 / 1024.0, 0, 1, 0)
		    glRotatef(rot[2] * 90.0 / 1024.0, 0, 0, 1)

		    self.drawPart(self.model["parts"][index], False)

		    glPopMatrix()
	   
	    # render transparent objects
	    glDepthMask(GL_FALSE)
	    for item in self.model["nodes"]:
		(flags, index, pos, rot) = item
		if flags != 480:
		    glPushMatrix()
		    glTranslatef(pos[0], pos[1], pos[2])
		    glRotatef(rot[0] * 90.0 / 1024.0, 1, 0, 0)
		    glRotatef(rot[1] * 90.0 / 1024.0, 0, 1, 0)
		    glRotatef(rot[2] * 90.0 / 1024.0, 0, 0, 1)

		    self.drawPart(self.model["parts"][index], True)

		    glPopMatrix()
	    glDepthMask(GL_TRUE)
	    glEndList()
	else:
	    glCallList(self.list)
	   
    def clearList(self):
	glDeleteLists(self.list, 1)
	self.list = None

def getNodes(archiveData):
    nodes = []
    (itemCount,) = struct.unpack_from("<I", archiveData, 0x018C)
    for itemIndex in xrange(itemCount):
	(flags, rot_x, rot_y, rot_z, pos_x, pos_y, pos_z, index) = struct.unpack_from("<HHHHhhhH", archiveData, 0x0190 + itemIndex * 16)
	nodes.append((flags, index, (pos_x, pos_y, pos_z), (rot_x, rot_y, rot_z)))
    return nodes

def writeData(f, node):
    f.write("<%s" % node[0])
    items = node[1].items()
    items.sort()
    for key, value in items:
	f.write(" %s=\"%s\"" % (key, value))
    if len(node[2]) > 0:
	f.write(">")
	x = []
	for item in node[2]:
	    if type(item) == tuple:
		if len(x) > 0:
		    f.write(" ".join(x))
		    x = []
		writeData(f, item)
	    else:
		x.append(str(item))
	if len(x) > 0:
	    f.write(" ".join(x))
	    x = []
	f.write("</%s>" % node[0])
    else:
	f.write("/>\n")

def flattenBuffer(buffer):
    l = [(value,key) for key,value in buffer.items()]
    l.sort()
    v = []
    for x in [list(key) for _,key in l]:
	v.extend(x)
    return v

def saveModel(name, model):
    basename = os.path.splitext(name)[0]
    print("saving textures...")
    for index,t in enumerate(model["textures"]):
	if t is not None:
	    n = "%s_%i.tga" % (basename, index)
	    image = pygame.image.fromstring(t, (256, 256), "RGBA", True)
	    pygame.image.save(image, n)
	    del image

    print "saving model..."
    collada = ("COLLADA", {"xmlns":"http://www.collada.org/2005/11/COLLADASchema", "version":"1.4.0"}, [])

    library_visual_scenes = ("library_visual_scenes", {}, [])
    visual_scene = ("visual_scene", {"id":"scene", "name":"level"}, [])
    for i,n in enumerate(model["nodes"]):
	(flags, partIndex, pos, rot) = n
	nodeName = "node%i_%4.4x_%i" % (i, flags, partIndex)
	node = ("node", {"name":nodeName, "id":nodeName}, [])
	if pos[0] != 0 or pos[1] != 0 or pos[2] != 0:
	    translate = ("translate", {}, [pos[0], pos[1], pos[2]])
	    node[2].append(translate)
	if rot[0] != 0:
	    rotate = ("rotate", {}, [1,0,0,rot[0] * 90.0 / 1024.0])
	    node[2].append(rotate)
	if rot[1] != 0:
	    rotate = ("rotate", {}, [0,1,0,rot[1] * 90.0 / 1024.0])
	    node[2].append(rotate)
	if rot[2] != 0:
	    rotate = ("rotate", {}, [0,0,1,rot[2] * 90.0 / 1024.0])
	    node[2].append(rotate)
	if flags != 480:
	    for blockIndex, block in enumerate(model["parts"][partIndex]["blocks"]):
		shaders = set([shader for shader,_ in block["tri_tex"]]+[shader for shader,_ in block["quad_tex"]]+[shader for shader,_ in block["tri_mono"]]+[shader for shader,_ in block["quad_mono"]])
		for s in shaders:
		    meshName = "#mesh%i_%i_%i" % (partIndex, blockIndex,s)
		    instance_geometry = ("instance_geometry", {"url":meshName}, [])
		    bind_material = ("bind_material", {}, [])
		    technique_common = ("technique_common", {}, [])

		    shader = model["shaders"][s]
		    instance_material = ("instance_material", {"symbol":"slot%i" % s, "target":"#material%i" % s}, [])
		    if shader[3]:
			bind_vertex_input = ("bind_vertex_input", {"semantic":"UVSET0", "input_semantic":"TEXCOORD", "input_set":0}, [])
			instance_material[2].append(bind_vertex_input)
		    else:
			bind_vertex_input = ("bind_vertex_input", {"semantic":"DIFFUSE", "input_semantic":"COLOUR", "input_set":0}, [])
			instance_material[2].append(bind_vertex_input)
		    technique_common[2].append(instance_material)
		    bind_material[2].append(technique_common)
		    instance_geometry[2].append(bind_material)
		    node[2].append(instance_geometry)
	visual_scene[2].append(node)
    library_visual_scenes[2].append(visual_scene)
    collada[2].append(library_visual_scenes)

    library_images = ("library_images", {}, [])
    for index,t in enumerate(model["textures"]):
	if t is not None:
	    n = "%s_%i.tga" % (basename, index)
	    image = ("image", {"id":"image%i" % index}, [
		("init_from", {}, [n])
	    ])
	    library_images[2].append(image)
    collada[2].append(library_images)

    library_geometries = ("library_geometries", {}, [])
    for partIndex, part in enumerate(model["parts"]):
	for blockIndex, block in enumerate(part["blocks"]):   
	    # create separate mesh for each shader and for textured and untextured geometry
	    meshlist = {}   
	    for tri_tex in block["tri_tex"]:
		(shader, prim) = tri_tex
		try:
		    d = meshlist[shader]
		except KeyError:
		    d = {"poly":[], "position":{}, "normal":{}, "colour":{}, "uv":{}}
		    meshlist[shader] = d
		poly = []
		for vtx in prim:
		    try:
			p = d["position"][vtx[0]]
		    except KeyError:
			p = len(d["position"])
			d["position"][vtx[0]] = p
		    try:
			n = d["normal"][vtx[1]]
		    except KeyError:
			n = len(d["normal"])
			d["normal"][vtx[1]] = n
		    try:
			t = d["uv"][vtx[2]]
		    except KeyError:
			t = len(d["uv"])
			d["uv"][vtx[2]] = t
		    poly.append((p,n,t))
		d["poly"].append(poly)

	    for quad_tex in block["quad_tex"]:
		(shader, prim) = quad_tex
		try:
		    d = meshlist[shader]
		except KeyError:
		    d = {"poly":[], "position":{}, "normal":{}, "colour":{}, "uv":{}}
		    meshlist[shader] = d
		poly = []
		for vtx in prim:
		    try:
			p = d["position"][vtx[0]]
		    except KeyError:
			p = len(d["position"])
			d["position"][vtx[0]] = p
		    try:
			n = d["normal"][vtx[1]]
		    except KeyError:
			n = len(d["normal"])
			d["normal"][vtx[1]] = n
		    try:
			t = d["uv"][vtx[2]]
		    except KeyError:
			t = len(d["uv"])
			d["uv"][vtx[2]] = t
		    poly.append((p,n,t))
		d["poly"].append(poly)
	   
	    for tri_mono in block["tri_mono"]:
		(shader, prim) = tri_mono
		try:
		    d = meshlist[shader]
		except KeyError:
		    d = {"poly":[], "position":{}, "normal":{}, "colour":{}, "uv":{}}
		    meshlist[shader] = d
		poly = []
		for vtx in prim:
		    try:
			p = d["position"][vtx[0]]
		    except KeyError:
			p = len(d["position"])
			d["position"][vtx[0]] = p
		    try:
			n = d["normal"][vtx[1]]
		    except KeyError:
			n = len(d["normal"])
			d["normal"][vtx[1]] = n
		    try:
			c = d["colour"][vtx[2]]
		    except KeyError:
			c = len(d["colour"])
			d["colour"][vtx[2]] = c
		    poly.append((p,n,c))
		d["poly"].append(poly)
	   
	    for quad_mono in block["quad_mono"]:
		(shader, prim) = quad_mono
		try:
		    d = meshlist[shader]
		except KeyError:
		    d = {"poly":[], "position":{}, "normal":{}, "colour":{}, "uv":{}}
		    meshlist[shader] = d
		poly = []
		for vtx in prim:
		    try:
			p = d["position"][vtx[0]]
		    except KeyError:
			p = len(d["position"])
			d["position"][vtx[0]] = p
		    try:
			n = d["normal"][vtx[1]]
		    except KeyError:
			n = len(d["normal"])
			d["normal"][vtx[1]] = n
		    try:
			c = d["colour"][vtx[2]]
		    except KeyError:
			c = len(d["colour"])
			d["colour"][vtx[2]] = c
		    poly.append((p,n,c))
		d["poly"].append(poly)

	    for shader, meshdata in meshlist.items():
		meshName = "mesh%i_%i_%i" % (partIndex, blockIndex, shader)
		geometry = ("geometry", {"id":meshName}, [])
		mesh = ("mesh", {}, [])
		
		position = meshdata["position"]
		if len(position) > 0:
		    source = ("source", {"id":"%s-position" % meshName}, [])
		    float_array = ("float_array", {"id":"%s-position-array" % meshName, "count":(len(position) * 3)}, [float(x) for x in flattenBuffer(position)])
		    source[2].append(float_array)
		    technique_common = ("technique_common", {}, [
			("accessor", {"count":len(position), "source":"%s-position-array" % meshName, "stride":3}, [
			    ("param", {"name":"X", "type":"float"}, []),
			    ("param", {"name":"Y", "type":"float"}, []),
			    ("param", {"name":"Z", "type":"float"}, [])
			])
		    ])
		    source[2].append(technique_common)
		    mesh[2].append(source)

		normal = meshdata["normal"]
		if len(normal) > 0:
		    source = ("source", {"id":"%s-normal" % meshName}, [])
		    float_array = ("float_array", {"id":"%s-normal-array" % meshName, "count":(len(normal) * 3)}, [float(x) / 4096.0 for x in flattenBuffer(normal)])
		    source[2].append(float_array)
		    technique_common = ("technique_common", {}, [
			("accessor", {"count":len(normal), "source":"%s-normal-array" % meshName, "stride":3}, [
			    ("param", {"name":"X", "type":"float"}, []),
			    ("param", {"name":"Y", "type":"float"}, []),
			    ("param", {"name":"Z", "type":"float"}, [])
			])
		    ])
		    source[2].append(technique_common)
		    mesh[2].append(source)

		uv = meshdata["uv"]
		if len(uv) > 0:
		    source = ("source", {"id":"%s-uv" % meshName}, [])
		    float_array = ("float_array", {"id":"%s-uv-array" % meshName, "count":(len(uv) * 2)}, [(float(x) + 0.5) / 256.0 for x in flattenBuffer(uv)])
		    source[2].append(float_array)
		    technique_common = ("technique_common", {}, [
			("accessor", {"count":len(uv), "source":"%s-uv-array" % meshName, "stride":2}, [
			    ("param", {"name":"U", "type":"float"}, []),
			    ("param", {"name":"V", "type":"float"}, [])
			])
		    ])
		    source[2].append(technique_common)
		    mesh[2].append(source)

		colour = meshdata["colour"]
		if len(colour) > 0:
		    source = ("source", {"id":"%s-colour" % meshName}, [])
		    float_array = ("float_array", {"id":"%s-colour-array" % meshName, "count":(len(colour) * 4)}, [float(x) / 255.0 for x in flattenBuffer(colour)])
		    source[2].append(float_array)
		    technique_common = ("technique_common", {}, [
			("accessor", {"count":len(colour), "source":"%s-colour-array" % meshName, "stride":4}, [
			    ("param", {"name":"R", "type":"float"}, []),
			    ("param", {"name":"G", "type":"float"}, []),
			    ("param", {"name":"B", "type":"float"}, []),
			    ("param", {"name":"A", "type":"float"}, [])
			])
		    ])
		    source[2].append(technique_common)
		    mesh[2].append(source)

		vertices = ("vertices", {"id":"%s-vertex" % meshName}, [
		    ("input", {"semantic":"POSITION", "source":"#%s-position" % meshName}, [])
		])
		mesh[2].append(vertices)
	       
		primitives = meshdata["poly"]
		polylist = ("polylist", {"count":len(primitives), "material":"slot%i" % shader}, [])
		input = ("input", {"semantic":"VERTEX", "source":"#%s-vertex" % meshName, "offset":0}, [])
		polylist[2].append(input)
		input = ("input", {"semantic":"NORMAL", "source":"#%s-normal" % meshName, "offset":1}, [])
		polylist[2].append(input)
		if len(uv) > 0:
		    input = ("input", {"semantic":"TEXCOORD", "source":"#%s-uv" % meshName, "offset":2}, [])
		    polylist[2].append(input)
		if len(colour) > 0:
		    input = ("input", {"semantic":"COLOUR", "source":"#%s-colour" % meshName, "offset":2}, [])
		    polylist[2].append(input)
		vcount = ("vcount", {}, [len(poly) for poly in primitives])
		polylist[2].append(vcount)
		p = ("p", {}, [])
		for poly in primitives:
		    for vtx in poly:
			p[2].extend(list(vtx))
		polylist[2].append(p)
		mesh[2].append(polylist)

		geometry[2].append(mesh)
		library_geometries[2].append(geometry)
    collada[2].append(library_geometries)

    library_materials = ("library_materials", {}, [])
    for shaderIndex,shader in enumerate(model["shaders"]):
	matName = "material%i" % shaderIndex
	effName = "effect%i" % shaderIndex
	material = ("material", {"id":matName}, [
	    ("instance_effect", {"url":"#%s" % effName}, [])
	])
	library_materials[2].append(material)
    collada[2].append(library_materials)
   
    library_effects = ("library_effects", {}, [])
    for shaderIndex,shader in enumerate(model["shaders"]):
	matName = "material%i" % shaderIndex
	effName = "effect%i" % shaderIndex
	effect = ("effect", {"id":effName}, [])
	profile_COMMON = ("profile_COMMON", {}, [])

	if shader[3]:
	    newparam = ("newparam", {"sid":"surface%i" % shaderIndex}, [
		("surface", {"type":"2D"}, [
		    ("init_from", {}, ["image%i" % shaderIndex])
		])
	    ])
	    profile_COMMON[2].append(newparam)
	    newparam = ("newparam", {"sid":"sampler%i" % shaderIndex}, [
		("sampler2D", {}, [
		    ("source", {}, ["surface%i" % shaderIndex])
		])
	    ])
	    profile_COMMON[2].append(newparam)
	else:
	    newparam = ("newparam", {"sid":"colour"}, [
		("semantic", {}, ["DIFFUSE"]),
		("modifier", {}, ["VARYING"])
	    ])
	    profile_COMMON[2].append(newparam)

	technique = ("technique", {"sid":"COMMON"}, [])
	lambert = ("lambert", {}, [])
	if shader[3]:
	    # textured
	    diffuse = ("diffuse", {}, [
		("texture", {"texture":"sampler%i" % shaderIndex, "texcoord":"UVSET0"}, [])
	    ])
	    lambert[2].append(diffuse)
	else:
	    # vertex colour
	    diffuse = ("diffuse", {}, [
		("param", {"ref":"colour"}, [])
	    ])
	    lambert[2].append(diffuse)
	
	technique[2].append(lambert)
	profile_COMMON[2].append(technique)
	effect[2].append(profile_COMMON)

	library_effects[2].append(effect)
    collada[2].append(library_effects)
   
    scene = ("scene", {}, [
	("instance_visual_scene", {"url":"#scene"}, [])
    ])
    collada[2].append(scene)
   
    f = open(name, "wt")
    writeData(f, collada)
    f.close()
   
    print "done..."

def main(*argv):
    print "loading archive..."
    diskIndex = 1 # there are disk 1 and disk 2
    dirIndex = 11 # 0-based index
    fileIndex = int(argv[0]) # 0-based index

    archivePath = os.path.join("disk%i" % diskIndex, "dir%i" % dirIndex, "file%i.bin" % (fileIndex * 2))
   
    f = open(archivePath, "rb")
    archiveData = f.read()
    f.close()
   
    if archiveData[:4] == "It's":
	# file was removed from disk image
	print "This file was removed from the disk image. Most likely it is a room that is not reachable any more."
	return 0

    modelData = getData(archiveData, 2)

    print "loading texture..."
    texturePath = os.path.join("disk%i" % diskIndex, "dir%i" % dirIndex, "file%i.bin" % (fileIndex * 2 + 1))
   
    f = open(texturePath, "rb")
    textureData = f.read()
    f.close()

    print "converting meshes..."
    model = loadModel(modelData)
   
    print "converting textures..."
    model["textures"] = loadTextures(textureData, model["shaders"])
   
    print "getting nodes..."
    model["nodes"] = getNodes(archiveData)

    print "starting OpenGL..."
    pygame.init()
   
    screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF|OPENGL)

    glViewport(0, 0, 640, 480)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    kFOVy = 0.57735
    kZNear = 10.0
    kZFar = 10000.0
    aspect = (640.0 / 480.0) * kZNear * kFOVy
    glFrustum(-aspect, aspect, -(kZNear * kFOVy), (kZNear * kFOVy), kZNear, kZFar)

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glDisable(GL_CULL_FACE)
    glDisable(GL_LIGHTING)
    glDisable(GL_BLEND)
    glPolygonMode(GL_FRONT, GL_FILL)
    glPolygonMode(GL_BACK, GL_LINE)

    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    wireframe = False
   
    clock = pygame.time.Clock()
    key_up = key_down = key_left = key_right = key_front = key_back = False
    rot_x = 0.0
    rot_y = 0.0
    pos_x = 0.0
    pos_y = 0
    pos_z = -2000
    object = OpenGLObject(model)
    while True:
	for event in pygame.event.get():
	    if event.type == QUIT:
		exit()
	    elif event.type == KEYDOWN:
		if event.key == pygame.K_UP:
		    key_up = True
		elif event.key == pygame.K_DOWN:
		    key_down = True
		elif event.key == pygame.K_LEFT:
		    key_left = True
		elif event.key == pygame.K_RIGHT:
		    key_right = True
		elif event.key == pygame.K_w:
		    key_front = True
		elif event.key == pygame.K_s:
		    key_back = True
		elif event.key == pygame.K_ESCAPE:
		    exit()
		elif event.key == pygame.K_d:
		    wireframe = not wireframe
		    if wireframe:
		        glPolygonMode(GL_FRONT, GL_LINE)
		    else:
		        glPolygonMode(GL_FRONT, GL_FILL)
		elif event.key == pygame.K_c:
		    saveModel("level%i.dae" % fileIndex, model)
	    elif event.type == KEYUP:
		if event.key == pygame.K_UP:
		    key_up = False
		elif event.key == pygame.K_DOWN:
		    key_down = False
		elif event.key == pygame.K_LEFT:
		    key_left = False
		elif event.key == pygame.K_RIGHT:
		    key_right = False
		elif event.key == pygame.K_w:
		    key_front = False
		elif event.key == pygame.K_s:
		    key_back = False
		   
	if key_up:
	    rot_x -= 1.0
	elif key_down:
	    rot_x += 1.0
	   
	if key_left:
	    rot_y -= 1.0
	elif key_right:
	    rot_y += 1.0
	   
	if key_front:
	    sx = math.sin(rot_x * math.pi * 2.0 / 256.0)
	    cx = -math.cos(rot_x * math.pi * 2.0 / 256.0)
	    sy = math.sin(rot_y * math.pi * 2.0 / 256.0)
	    cy = -math.cos(rot_y * math.pi * 2.0 / 256.0)
	    pos_x += sy * cx * 16
	    pos_y += sx * 16
	    pos_z += cy * cx * 16
	elif key_back:
	    sx = math.sin(rot_x * math.pi * 2.0 / 256.0)
	    cx = -math.cos(rot_x * math.pi * 2.0 / 256.0)
	    sy = math.sin(rot_y * math.pi * 2.0 / 256.0)
	    cy = -math.cos(rot_y * math.pi * 2.0 / 256.0)
	    pos_x -= sy * cx * 16
	    pos_y -= sx * 16
	    pos_z -= cy * cx * 16

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)	

	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	glFrustum(-aspect, aspect, -(kZNear * kFOVy), (kZNear * kFOVy), kZNear, kZFar)
	if False:
	    glTranslatef(0, 0, -2000)
	    glRotatef(rot_y * 360.0 / 256.0, 0.0, 1.0, 0.0)
	    glRotatef(rot_x * 360.0 / 256.0, 1.0, 0.0, 0.0)
	else:
	    glRotatef(rot_x * 360.0 / 256.0, 1.0, 0.0, 0.0)
	    glRotatef(rot_y * 360.0 / 256.0, 0.0, 1.0, 0.0)
	    glTranslatef(pos_x, pos_y, pos_z)

	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	   
	object.draw()
   
	clock.tick(60)
	pygame.display.flip()

if __name__ == "__main__":
    main(*sys.argv[1:])
