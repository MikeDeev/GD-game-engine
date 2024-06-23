import os
import shutil
import uuid
import random
import string

def copy_files(src_folder, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    for item in os.listdir(src_folder):
        src_item = os.path.join(src_folder, item)
        dest_item = os.path.join(dest_folder, item)
        if os.path.isfile(src_item):
            shutil.copy(src_item, dest_item)
            print(f"Copied {src_item} to {dest_item}")

def random_string(length):
    randomchars = string.ascii_letters + string.digits
    random_str = ''.join(random.choice(randomchars) for _ in range(length))
    return random_str

def compile_spwn(scenes, filename, compiled_level_name):
    uid_folder = f"builds/{uuid.uuid4()}"
    os.makedirs(uid_folder, exist_ok=True)
    print(f"Created temporary folder: {uid_folder}")

    try:
        utils_folder = "engine/utils"
        engine_func_folder = "engine/engine_func"

        if os.path.exists(utils_folder):
            copy_files(utils_folder, uid_folder)
            print(f"Copied {utils_folder} to {uid_folder}/utils")
        else:
            print(f"Warning: {utils_folder} not found")

        if os.path.exists(engine_func_folder):
            copy_files(engine_func_folder, uid_folder)
            print(f"Copied {engine_func_folder} to {uid_folder}/engine_func")
        else:
            print(f"Warning: {engine_func_folder} not found")

        spwn_code = """
extract obj_props;
//GENERATED WITH GEOMETRY DASH GAME ENGINE//
let engineeVrsion = "1.0";
let engineName = "GD game engine";

//Libs
import "collection.spwn";
let spwngen = import "spwngen.spwn";
let game = import "engine.spwn";
//let xor = import "xor.spwn";

        
        """

        group = 1
        for scene in scenes:
            spwn_code += f"// Scene: {scene.name}\n"
            for obj in scene.objects:
                objId = random_string(10)
                spwn_code += f"""
                $.add(obj{{
                    OBJ_ID: {obj.obj_id},
                    X: {obj.x}+100,
                    Y: {obj.y}+100,
                    //rotation: {obj.rotation},
                    //COLOR: "{obj.color_id}",
                    GROUPS: {obj.groups if obj.groups else []}
                }});
                """
                if obj.script:
                    spwn_code += f"""
                    // Script for object {obj.obj_id}
                    {obj.script}
                    """
            group += 1

        spwn_file_path = os.path.join(uid_folder, filename)
        with open(spwn_file_path, 'w') as file:
            file.write(spwn_code)
        print(f'SPWN file generated at: {spwn_file_path}')

        os.chdir(uid_folder)
        
        os.system(f'spwn build {filename} --level-name "{compiled_level_name}"')
    finally:
        print("Project compiled!")