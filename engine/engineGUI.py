import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import shutil
import os
import uuid
from engine.compiler import compile_spwn

class GameObject:
    def __init__(self, obj_id, x=0, y=0, script=""):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.script = script
    
    def get_position(self):
        return self.x, self.y
    
    def set_position(self, x, y):
        self.x = x
        self.y = y

class Scene:
    def __init__(self, name):
        self.name = name
        self.objects = []

class ScriptEditorPopup:
    def __init__(self, parent, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback
        
        self.popup = tk.Toplevel(parent)
        self.popup.title("Script Editor")
        
        self.script_text = ScrolledText(self.popup, wrap=tk.WORD, width=30, height=10)
        self.script_text.pack(expand=True, fill=tk.BOTH)
        
        ttk.Button(self.popup, text="Apply Script", command=self.apply_script).pack(pady=5)
        
    def apply_script(self):
        script = self.script_text.get(1.0, tk.END)
        self.apply_callback(script)
        self.popup.destroy()

class EngineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Engine for Geometry Dash (SPWN)")
        
        self.scenes = []
        self.current_scene_index = -1
        self.selected_object_index = -1
        
        self.create_menu()
        self.create_toolbar()
        self.create_scene_panel()
        self.create_canvas()
        self.create_object_panel()
        self.create_property_panel()
        self.create_buttons_panel()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="New Scene", command=self.new_scene).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Delete Scene", command=self.delete_scene).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Compile SPWN", command=self.compile_spwn).pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_scene_panel(self):
        scene_panel = ttk.Frame(self.root)
        scene_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(scene_panel, text="Scenes").pack(pady=5)
        
        self.scene_listbox = tk.Listbox(scene_panel, selectmode=tk.SINGLE)
        self.scene_listbox.pack(expand=True, fill=tk.BOTH)
        self.scene_listbox.bind("<ButtonRelease-1>", self.select_scene)
        
        scrollbar = ttk.Scrollbar(scene_panel, orient=tk.VERTICAL, command=self.scene_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scene_listbox.config(yscrollcommand=scrollbar.set)
    
    def create_object_panel(self):
        object_panel = ttk.Frame(self.root)
        object_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(object_panel, text="Objects").pack(pady=5)
        
        self.object_listbox = tk.Listbox(object_panel, selectmode=tk.SINGLE)
        self.object_listbox.pack(expand=True, fill=tk.BOTH)
        self.object_listbox.bind("<ButtonRelease-1>", self.select_object)
        
        scrollbar = ttk.Scrollbar(object_panel, orient=tk.VERTICAL, command=self.object_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.object_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(object_panel, text="Add Object", command=self.add_object).pack(pady=5)
        
        ttk.Label(object_panel, text="Script Editor", font=('Helvetica', 12, 'bold')).pack(pady=5)
        self.script_editor_button = ttk.Button(object_panel, text="Open Script Editor", command=self.open_script_editor)
        self.script_editor_button.pack(pady=5)
        
    def open_script_editor(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            popup = ScriptEditorPopup(self.root, lambda script: self.apply_script_to_object(script))
    
    def apply_script_to_object(self, script):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            self.scenes[self.current_scene_index].objects[self.selected_object_index].script = script
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def add_object(self):
        if self.current_scene_index != -1:
            obj_id = self.get_available_object_id()
            new_object = GameObject(obj_id)
            self.scenes[self.current_scene_index].objects.append(new_object)
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def get_available_object_id(self):
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            max_id = 0
            for obj in scene.objects:
                if obj.obj_id > max_id:
                    max_id = obj.obj_id
            return max_id + 1
        return 1
    
    def create_property_panel(self):
        property_panel = ttk.Frame(self.root)
        property_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(property_panel, text="Properties", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.property_text = ScrolledText(property_panel, wrap=tk.WORD, width=30, height=10)
        self.property_text.pack(expand=True, fill=tk.BOTH)
        self.property_text.bind("<FocusOut>", self.update_properties)
    
    def update_properties(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            properties_text = self.property_text.get(1.0, tk.END)
            lines = properties_text.splitlines()
            for line in lines:
                if line.startswith("Position:"):
                    x, y = line.split(": ")[1].split(",")
                    self.scenes[self.current_scene_index].objects[self.selected_object_index].set_position(int(x), int(y))
                    break
    
    def new_scene(self):
        scene_name = f"Scene {len(self.scenes) + 1}"
        self.scenes.append(Scene(scene_name))
        self.scene_listbox.insert(tk.END, scene_name)
    
    def delete_scene(self):
        selected_index = self.scene_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            del self.scenes[index]
            self.scene_listbox.delete(index)
            self.clear_object_listbox()
            self.clear_property_text()
    
    def select_scene(self, event):
        selected_index = self.scene_listbox.curselection()
        if selected_index:
            self.current_scene_index = selected_index[0]
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def update_object_listbox(self):
        self.clear_object_listbox()
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                self.object_listbox.insert(tk.END, f"Object {obj.obj_id}")
    
    def clear_object_listbox(self):
        self.object_listbox.delete(0, tk.END)
    
    def select_object(self, event):
        selected_index = self.object_listbox.curselection()
        if selected_index and self.current_scene_index != -1:
            self.selected_object_index = selected_index[0]
            scene = self.scenes[self.current_scene_index]
            obj = scene.objects[self.selected_object_index]
            self.property_text.delete(1.0, tk.END)
            self.property_text.insert(tk.END, f"Object ID: {obj.obj_id}\n")
            self.property_text.insert(tk.END, f"Position: ({obj.x}, {obj.y})")
            self.script_editor_button.config(state=tk.NORMAL)
        else:
            self.selected_object_index = -1
            self.clear_property_text()
            self.script_editor_button.config(state=tk.DISABLED)
    
    def clear_property_text(self):
        self.property_text.delete(1.0, tk.END)
    
    def save_project(self):
        filename = filedialog.asksaveasfilename(defaultextension=".proj", filetypes=[("Project Files", "*.proj")])
        if filename:
            with open(filename, 'w') as file:
                for scene in self.scenes:
                    file.write(f"Scene: {scene.name}\n")
                    for obj in scene.objects:
                        file.write(f"Object {obj.obj_id}: ({obj.x}, {obj.y})\n")
                        if obj.script:
                            file.write(f"Script: {obj.script}\n")
                    file.write("\n")
            messagebox.showinfo("Save Project", "Project saved successfully.")
    
    def load_project(self):
        filename = filedialog.askopenfilename(filetypes=[("Project Files", "*.proj")])
        if filename:
            self.scenes.clear()
            self.scene_listbox.delete(0, tk.END)
            with open(filename, 'r') as file:
                current_scene = None
                for line in file:
                    line = line.strip()
                    if line.startswith("Scene: "):
                        scene_name = line.split("Scene: ")[1]
                        current_scene = Scene(scene_name)
                        self.scenes.append(current_scene)
                        self.scene_listbox.insert(tk.END, scene_name)
                    elif line.startswith("Object "):
                        obj_info = line.split(": ")[1]
                        obj_id = int(obj_info.split(",")[0])
                        pos = obj_info.split("(")[1].split(")")[0].split(",")
                        x = int(pos[0])
                        y = int(pos[1])
                        script = None
                        if "Script: " in line:
                            script = line.split("Script: ")[1]
                        current_scene.objects.append(GameObject(obj_id, x, y, script))
            messagebox.showinfo("Load Project", "Project loaded successfully.")
            self.clear_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def compile_spwn(self):
        if self.scenes:
            temp_dir = os.path.join("/tmp", str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copy utils files
            utils_dir = os.path.join(os.path.dirname(__file__), "utils")
            for filename in os.listdir(utils_dir):
                shutil.copy(os.path.join(utils_dir, filename), temp_dir)
            
            filename = os.path.join(temp_dir, "compiled.spwn")
            compile_spwn(self.scenes, filename)
            
            messagebox.showinfo("Compile SPWN", f"SPWN file compiled successfully. Saved in temporary directory: {temp_dir}")
        else:
            messagebox.showwarning("Compile SPWN", "No scenes to compile.")
    
    def on_canvas_click(self, event):
        if self.current_scene_index != -1:
            x, y = event.x, event.y
            scene = self.scenes[self.current_scene_index]
            for i, obj in enumerate(scene.objects):
                obj_x, obj_y = obj.get_position()
                if abs(x - obj_x) <= 10 and abs(y - obj_y) <= 10:
                    self.selected_object_index = i
                    self.select_object(None)
                    return
            self.selected_object_index = -1
            self.select_object(None)
    
    def on_canvas_drag(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            x, y = event.x, event.y
            self.scenes[self.current_scene_index].objects[self.selected_object_index].set_position(x, y)
            self.update_object_listbox()
            self.draw_scene()
    
    def draw_scene(self):
        self.canvas.delete("all")
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                x, y = obj.get_position()
                self.canvas.create_rectangle(x - 10, y - 10, x + 10, y + 10, fill="blue", tags="object")
    
    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
    
    def create_buttons_panel(self):
        buttons_panel = ttk.Frame(self.root)
        buttons_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(buttons_panel, text="Apply Script", command=self.open_script_editor).pack(pady=5)
        ttk.Button(buttons_panel, text="Save Project", command=self.save_project).pack(pady=5)
        ttk.Button(buttons_panel, text="Load Project", command=self.load_project).pack(pady=5)
