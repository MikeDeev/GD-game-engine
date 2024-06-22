import os

#TODO: Make it work 

def compile_spwn(scenes, filename,CompiledlevelName):

    spwn_code = """
    //libs
    let isNumber = import 'is-number';
    let spwngen = import "spwngen.spwn";
    let gameoflife = import "gameoflife.spwn";
    let spwngen = import "spwngen.spwn";
    let collection = import "collection.spwn";
    let xor = import "xor.spwn";
    """
    group = 1
    for scene in scenes:
        spwn_code += f"// Scene: {scene.name}\n"
        for obj in scene.objects:
            spwn_code += f"""
            let block = {{
                id: {obj.obj_id},
                x: {obj.x},
                y: {obj.y},
                group: {group}
            }};
            """
            if obj.script:
                spwn_code += f"""
                {{
                    {obj.script}
                }}
                """
        group += 1
    with open(filename, 'w') as file:
        file.write(spwn_code)
    print(f'building {filename}')
    os.system(f'spwn build {filename} --level-name "{CompiledlevelName}"')
