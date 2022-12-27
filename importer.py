#  ╭─────────────────────────────────────────╮
#  │ UDump to Blender                        │
#  │                                         │
#  │ M4X4#6494, zwei#0001 • discord.gg/gator │
#  ╰─────────────────────────────────────────╯

#  ╶─────────────────────────────────────────── #

#  ╭──────────╮
#  │ Settings │
#  ╰──────────╯

DumpDirectory = "D:\\C_Docs\\ResilioSync\\Imports\\UE\\Tools\\udump-new\\Dump\\"
DeleteObjects = True
ConvertTextures = True
OldTextureExtension = "tga"
NewTextureExtension = "png"

#  ╶─────────────────────────────────────────╴ #

#  ╭─────────╮
#  │ Imports │
#  ╰─────────╯

import os
import cv2
import bpy
import json
import shutil
from bpy import *
from math import *
from PIL import Image
from pathlib import Path
from io_import_scene_unreal_psa_psk_280 import pskimport

#  ╶─────────────────────────────────────────╴ #

#  ╭───────────╮
#  │ Variables │
#  ╰───────────╯
successfulObjects = 0
failedObjects = 0
nonImportedObjects = []
pskObjectCache = {}
CWD = os.getcwd()

#  ╶─────────────────────────────────────────╴ #

#  ╭───────────╮
#  │ Functions │
#  ╰───────────╯

# Tied to DeleteObjects
def removeAll():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    main()

# Main Import Funtion, Used in createObject()
def importMesh(filePath):
    return pskimport(filePath,bpy.context,bReorientBones=True)

# Fixes NaN Values in mesh
def fixNan(value):
    if(value=="NaN"):
        return 0
    else:
        return value
def convert(root, file):
    path = os.path.join(root,file)

    path = path.replace('\\', r'\\')
    root2 = root.replace('\\', r'\\') + r'\\'
    base = os.path.splitext(file)[0]

    os.chdir(root2)

    text = Image.open(file)
    text.save(f'{root2}{base}.{NewTextureExtension}')
    os.remove(path)

    print(f' --> <-- Converted {file}!')

    os.chdir(CWD)

def moveTex(root, file):
    path = os.path.join(root,file)

    path = path.replace('\\', r'\\')
    base = os.path.splitext(file)[0]
    
    dest = f"{DumpDirectory}Textures\\{base}.tga"
    try:
        shutil.copyfile(path, dest)
    except Exception:
        try:
            path = path.replace('\\\\', r'\\')
            shutil.copyfile(path,dest)
        except Exception:
            print(f'!!! --> Error in moving textures to folder: {e}')

def splitORM(root, file):
    fname = ((file.split(".tga"))[0]) + ".png"
    path = os.path.join(root,fname)
    path = path.replace('\\', r'\\')
    base = os.path.splitext(fname)[0]

    img = cv2.imread(f'{path}')

    blue,green,red = cv2.split(img)
    del blue

    name = (base.split("OcclusionRoughnessMetallic"))[0]

    cv2.imwrite(f"{root}{name}Roughness.png", red)
    cv2.imwrite(f"{root}{name}Metallic.png", green)
    os.remove(path)
    
    print(f" <-- --> Split {fname} into Roughness and Metallic textures!")

# Actual Import
def createObject(jsonData):
    objectType = jsonData["type"]
    if(objectType=="mesh"):
        path = jsonData["path"]

        path = path.split('.')[0]

        path = DumpDirectory+"UmodelExport"+path

        if(Path(path + ".pskx").is_file()):
            path = path + ".pskx"
        elif(Path(path + ".psk").is_file()):
            path = path + ".psk"
        if path != DumpDirectory+"UmodelExportNone":
            importMesh(path)

            imported = bpy.context.active_object

            location = jsonData["position"]
            rotation = jsonData["rotation"]

            scale = jsonData["scale"]

            imported.location = (fixNan(location["X"])/100,fixNan(location["Y"])/100*-1,fixNan(location["Z"]/100))
            imported.rotation_euler = (radians(fixNan(rotation["Z"])),radians(fixNan(rotation["X"])*-1),radians(fixNan(rotation["Y"])*-1))
            imported.scale = (fixNan(scale["X"]),fixNan(scale["Y"]),fixNan(scale["Z"]))

# Main data handler
def main():
    
    # Create Textures Folder
    if not os.path.exists(f"{DumpDirectory}\\Textures\\"):
        os.mkdir(f"{DumpDirectory}\\Textures\\")
    
    jsonFileData = json.loads((open(DumpDirectory+"dump.json","r").read())) 
    listLen = len(jsonFileData)
    for i in range(0,listLen):
        createObject(jsonFileData[i])
        print("Imported object "+str(i)+"/"+str(listLen))

    textfile = open(DumpDirectory+"brokenObjects.txt", "w")
    for element in nonImportedObjects:
        textfile.write(element + "\n")
    textfile.close()

    # Delete SkySphere
    try:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['SM_SkySphere.mo'].select_set(True)
        bpy.ops.object.delete()
        print(" --> Found and deleted SkySphere")
    except Exception:
        print(f" --> SkySphere Not Found, Trying InvertedSphere.")

    # Delete InvertedSphere
    try:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['MOD_InvertedSphere.mo'].select_set(True)
        bpy.ops.object.delete()
        print(" --> Found and deleted InvertedSphere")
    except Exception:
        print(f" --> InvertedSphere Not Found, Continuing.")

    # Shade Smooth / Delete VCOLS / Nodes
    print(" --> Enabling nodes, shade smoothing, and deleting V-Colors")
    bpy.ops.object.select_all(action='SELECT')
    for ob in bpy.context.selected_objects:
        ob.active_material.use_nodes = True
        bpy.context.view_layer.objects.active = ob
        while len(ob.data.vertex_colors) > 0:
            try:
                bpy.ops.geometry.color_attribute_remove()
            except Exception:
                bpy.ops.mesh.vertex_color_remove()
        bpy.ops.object.shade_smooth()

    #Start Convertion
    if ConvertTextures:
        print(" --> Starting texture conversion process")
        for root, dirs, files in os.walk(DumpDirectory):
            for file in files:
                if(file.endswith(f".{OldTextureExtension}")):
                    moveTex(root, file)
        for root, dirs, files in os.walk(f'{DumpDirectory}Textures\\'):
            for file in files:
                if(file.endswith(f".{OldTextureExtension}")):
                    convert(root, file)
                    if "OcclusionRoughnessMetallic" in file:
                        splitORM(root, file)
        print(" --> Finished texture conversion process")

    # AutoTexture
    print(" --> Starting auto-texturing")
    for i in bpy.data.materials:
        mat = str(i)
        mat = mat.split('<bpy_struct, Material("')
        mat = mat[1].split('") at ')
        mat = mat[0]

    for root, dirs, files in os.walk(DumpDirectory):
        for file in files:

            if(file.endswith(f".mat")):

                path = os.path.join(root,file)
                path = path.replace('\\', r'\\')

                if not os.path.exists(f'{DumpDirectory}\\Materials\\'):
                    os.mkdir(f'{DumpDirectory}\\Materials\\')

                dest = f"{DumpDirectory}\\Materials\\{file}"

                try:
                    shutil.copyfile(path,dest)
                except Exception:
                    continue

    texlist = {}

    for root, dirs, files in os.walk(f"{DumpDirectory}\\Materials\\"):
        for file in files:
            os.chdir(root)

            path = os.path.join(root,file)
            path = path.replace('\\', r'\\')
            base = os.path.splitext(file)[0]

            with open(file) as f:
                for line in f.readlines():
                    if 'Diffuse=' in line:
                        texPath = line.split('Diffuse=')
                        texPath = texPath[1]
                        texlist["Diffuse"] = texPath
                    if 'Normal=' in line:
                        texPath = line.split('Normal=')
                        texPath = texPath[1]
                        texlist["Normal"] = texPath
                    if 'Roughness=' in line:
                        texPath = line.split('Roughness=')
                        texPath = texPath[1]
                        if "OcclusionRoughnessMetallic" in texPath:
                            texPath = (texPath.split("OcclusionRoughnessMetallic"))[0]
                            texPath = f"{texPath}Roughness"
                        texlist['Roughness'] = texPath
                    if 'Metallic=' in line:
                        texPath = line.split('Metallic=')
                        texPath = texPath[1]
                        if "OcclusionRoughnessMetallic" in texPath:
                            texPath = (texPath.split("OcclusionRoughnessMetallic"))[0]
                            texPath = f"{texPath}Roughness"
                        texlist['Metallic'] = texPath
                    if 'Other[0]=' in line:
                        if 'OcclusionRoughnessMetallic' in line:
                            split = line.split("Other[0]=")[1]
                            texPath = split.split("OcclusionRoughness")
                            texPath = texPath[0] + texPath[1]
                            texlist['Metallic'] = texPath
                            texPath = split.split("Occlusion")
                            texPath = texPath[0] + "Roughness"
                            texlist['Roughness'] = texPath
                        elif '_Metallic' in line:
                            texPath = line.split("Other[0]=")[1]
                            texlist['Metallic'] = texPath
                        elif '_Roughness' in line:
                            texPath = line.split("Other[0]=")[1]
                            texlist['Roughness'] = texPath
                    if 'Other[1]=' in line:
                        if 'OcclusionRoughnessMetallic' in line:
                            split = line.split("Other[1]=")[1]
                            texPath = split.split("OcclusionRoughness")
                            texPath = texPath[0] + texPath[1]
                            texlist['Metallic'] = texPath
                            texPath = split.split("Occlusion")
                            texPath = texPath[0] + "Roughness"
                            texlist['Roughness'] = texPath
                        elif '_Metallic' in line:
                            texPath = line.split("Other[1]=")[1]
                            texlist['Metallic'] = texPath
                        elif '_Roughness' in line:
                            texPath = line.split("Other[1]=")[1]
                            texlist['Roughness'] = texPath

            for mat in bpy.data.materials:
                if mat.name == base:
                        mat.use_nodes = True
                        mat_nodes = mat.node_tree.nodes
                        mat_links = mat.node_tree.links
                        
                        try:
                            ColorNode = mat_nodes.new('ShaderNodeTexImage')
                            textPath = DumpDirectory.replace('\\', '/')
                            ColorNode.image = bpy.data.images.load(filepath = "".join(f"{textPath}Textures/{texlist['Diffuse']}.png".split()))
                            ColorNode.location = (-400,500)
                            mat_links.new(ColorNode.outputs["Color"], mat_nodes.get("Principled BSDF").inputs["Base Color"])
                        except Exception as e:
                            print(e)
                        
                        try:
                            NormalMap = mat_nodes.new("ShaderNodeNormalMap")
                            NormalNode = mat_nodes.new('ShaderNodeTexImage')
                            textPath = DumpDirectory.replace('\\', '/')
                            NormalNode.image = bpy.data.images.load(filepath = "".join(f"{textPath}Textures/{texlist['Normal']}.png".split()))
                            NormalNode.image.colorspace_settings.name = "Non-Color"
                            NormalNode.location = (-475,-375)
                            NormalMap.location = (-175,-275)
                            mat_links.new(NormalNode.outputs["Color"], NormalMap.inputs["Color"])
                            mat_links.new(NormalMap.outputs["Normal"], mat_nodes.get("Principled BSDF").inputs["Normal"])
                        except Exception as e:
                            print(e)
                        if "Roughness" in texlist.keys():
                            RoughNode = mat_nodes.new('ShaderNodeTexImage')
                            textPath = DumpDirectory.replace('\\', '/')
                            RoughNode.image = bpy.data.images.load(filepath = "".join(f"{textPath}Textures/{texlist['Roughness']}.png".split()))
                            RoughNode.image.colorspace_settings.name = "Non-Color"
                            RoughNode.location = (-300,0)
                            mat_links.new(RoughNode.outputs["Color"], mat_nodes.get("Principled BSDF").inputs["Roughness"])
                        if "Metallic" in texlist.keys():
                            MetalNode = mat_nodes.new('ShaderNodeTexImage')
                            textPath = DumpDirectory.replace('\\', '/')
                            MetalNode.image = bpy.data.images.load(filepath = "".join(f"{textPath}Textures/{texlist['Metallic']}.png".split()))
                            MetalNode.image.colorspace_settings.name = "Non-Color"
                            MetalNode.location = (-600,200)
                            mat_links.new(MetalNode.outputs["Color"], mat_nodes.get("Principled BSDF").inputs["Metallic"])
    print(" --> Done!")
#  ╭───────╮
#  │ Start │
#  ╰───────╯
if __name__ == '__main__':
    if DeleteObjects:
        removeAll()
    else:
        main()
