import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from tkinter.scrolledtext import ScrolledText
import shutil
import os
import uuid
import json
from engine.compiler import compile_spwn

class GameObject:
    def __init__(self, obj_id, x=0, y=0, rotation=0, script="", color=None, groups=None):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.rotation = rotation
        self.script = script
        self.color = color if color else "#FFFFFF"  # Default to white if not specified
        self.groups = groups if groups else []
    
    def get_position(self):
        return self.x, self.y
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
    
    def get_rotation(self):
        return self.rotation
    
    def set_rotation(self, rotation):
        self.rotation = rotation
    
    def to_dict(self):
        return {
            "obj_id": self.obj_id,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "script": self.script,
            "color": self.color,
            "groups": self.groups
        }
    
    @staticmethod
    def from_dict(data):
        return GameObject(data["obj_id"], data["x"], data["y"], data["rotation"], data["script"], data.get("color"), data.get("groups", []))

class Scene:
    def __init__(self, name):
        self.name = name
        self.objects = []
    
    def to_dict(self):
        return {
            "name": self.name,
            "objects": [obj.to_dict() for obj in self.objects]
        }
    
    @staticmethod
    def from_dict(data):
        scene = Scene(data["name"])
        scene.objects = [GameObject.from_dict(obj_data) for obj_data in data["objects"]]
        return scene

class ScriptEditorPopup:
    def __init__(self, parent, initial_script, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback
        
        self.popup = tk.Toplevel(parent)
        self.popup.title("Script Editor")
        
        self.script_text = ScrolledText(self.popup, wrap=tk.WORD, width=30, height=10)
        self.script_text.pack(expand=True, fill=tk.BOTH)
        
        self.script_text.insert(tk.END, initial_script)  # Display previous script
        
        ttk.Button(self.popup, text="Apply Script", command=self.apply_script).pack(pady=5)
    
    def apply_script(self):
        script = self.script_text.get(1.0, tk.END)
        self.apply_callback(script)
        self.popup.destroy()

class ProjectSettingsPopup:
    def __init__(self, parent, project_settings, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback
        self.project_settings = project_settings.copy()  # Create a copy to work with
        
        self.popup = tk.Toplevel(parent)
        self.popup.title("Project Settings")
        
        self.create_widgets()
    
    def create_widgets(self):
        notebook = ttk.Notebook(self.popup)
        notebook.pack(expand=True, fill=tk.BOTH)
        
        general_frame = ttk.Frame(notebook)
        self.create_general_settings(general_frame)
        notebook.add(general_frame, text="General")
        
        color_frame = ttk.Frame(notebook)
        self.create_color_settings(color_frame)
        notebook.add(color_frame, text="Colors")
        
        ttk.Button(self.popup, text="Apply", command=self.apply_settings).pack(pady=5)
    
    def create_general_settings(self, frame):
        ttk.Label(frame, text="General Settings", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        # Add general settings fields here if needed
        
    def create_color_settings(self, frame):
        ttk.Label(frame, text="Color Settings", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        self.color_listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        self.color_listbox.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.color_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.color_listbox.config(yscrollcommand=scrollbar.set)
        
        self.color_square = tk.Canvas(frame, width=30, height=30, bg="#FFFFFF", highlightthickness=0)
        self.color_square.pack(pady=10)
        
        ttk.Button(frame, text="Edit Color", command=self.edit_color).pack()
        
        # Add initial colors (all white)
        self.color_ids = []
        for i in range(1000):
            color_id = f"Color {i + 1}"
            self.color_listbox.insert(tk.END, color_id)
            self.color_ids.append(color_id)
        
        self.color_listbox.bind("<ButtonRelease-1>", self.select_color)
    
    def select_color(self, event):
        selected_index = self.color_listbox.curselection()
        if selected_index:
            color_id = self.color_ids[selected_index[0]]
            color = self.project_settings.get(color_id, "#FFFFFF")
            self.color_square.config(bg=color)
    
    def edit_color(self):
        selected_index = self.color_listbox.curselection()
        if selected_index:
            color_id = self.color_ids[selected_index[0]]
            color = self.project_settings.get(color_id, "#FFFFFF")
            new_color = colorchooser.askcolor(color=color)[1]
            if new_color:
                self.project_settings[color_id] = new_color
                self.color_square.config(bg=new_color)
    
    def apply_settings(self):
        self.apply_callback(self.project_settings)
        self.popup.destroy()

class EngineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Geometry Dash Game Engine")
        
        # icon_path = 'icon.ico'
        # self.root.iconbitmap(icon_path)
        
        self.scenes = []
        self.current_scene_index = -1
        self.selected_object_index = -1
        
        # Project settings
        self.project_settings = {
            "Color 1": "#FFFFFF",
        }
        
        self.create_menu()
        self.create_toolbar()
        self.create_scene_panel()
        self.create_canvas()
        self.create_object_panel()
        self.create_property_panel()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="Project Settings", command=self.open_project_settings)
        menubar.add_cascade(label="Project", menu=project_menu)
        
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
        self.script_editor_button = ttk.Button(object_panel, text="Edit Script", state=tk.DISABLED, command=self.open_script_editor)
        self.script_editor_button.pack(pady=5)
    
    def create_property_panel(self):
        property_panel = ttk.Frame(self.root)
        property_panel.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(property_panel, text="Properties", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.property_text = ScrolledText(property_panel, wrap=tk.WORD, width=30, height=10)
        self.property_text.pack(expand=True, fill=tk.BOTH)
    
    def update_object_listbox(self):
        self.object_listbox.delete(0, tk.END)
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                self.object_listbox.insert(tk.END, f"Object {obj.obj_id}")
    
    def clear_object_listbox(self):
        self.object_listbox.delete(0, tk.END)
    
    def update_properties_text(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            self.property_text.delete(1.0, tk.END)
            self.property_text.insert(tk.END, f"Position: {obj.x}, {obj.y}\n")
            self.property_text.insert(tk.END, f"Rotation: {obj.rotation}\n")
            self.property_text.insert(tk.END, f"Script:\n{obj.script}")
    
    def clear_property_text(self):
        self.property_text.delete(1.0, tk.END)
    
    def save_project(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filename:
            data = {
                "scenes": [scene.to_dict() for scene in self.scenes],
                "project_settings": self.project_settings
            }
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)
            messagebox.showinfo("Save Project", "Project saved successfully.")
    
    def load_project(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            self.scenes.clear()
            self.scene_listbox.delete(0, tk.END)
            with open(filename, 'r') as file:
                data = json.load(file)
                for scene_data in data["scenes"]:
                    scene = Scene.from_dict(scene_data)
                    self.scenes.append(scene)
                    self.scene_listbox.insert(tk.END, scene.name)
                if "project_settings" in data:
                    self.project_settings = data["project_settings"]
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
    
    def add_object(self):
        if self.current_scene_index != -1:
            obj_id = len(self.scenes[self.current_scene_index].objects) + 1
            new_object = GameObject(obj_id)
            self.scenes[self.current_scene_index].objects.append(new_object)
            self.update_object_listbox()
            self.draw_scene()
    
    def new_scene(self):
        scene_name = f"Scene {len(self.scenes) + 1}"
        self.scenes.append(Scene(scene_name))
        self.scene_listbox.insert(tk.END, scene_name)
        self.clear_object_listbox()
        self.clear_property_text()
    
    def delete_scene(self):
        if self.current_scene_index != -1:
            del self.scenes[self.current_scene_index]
            self.scene_listbox.delete(self.current_scene_index)
            self.current_scene_index = -1
            self.clear_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def open_script_editor(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            editor = ScriptEditorPopup(self.root, obj.script, self.apply_script_editor)
    
    def apply_script_editor(self, script):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            self.scenes[self.current_scene_index].objects[self.selected_object_index].script = script
            self.update_properties_text()
    
    def open_project_settings(self):
        settings_popup = ProjectSettingsPopup(self.root, self.project_settings, self.apply_project_settings)
    
    def apply_project_settings(self, settings):
        self.project_settings = settings
    
    def select_scene(self, event):
        selected_index = self.scene_listbox.curselection()
        if selected_index:
            self.current_scene_index = selected_index[0]
            self.clear_object_listbox()
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def select_object(self, event):
        selected_index = self.object_listbox.curselection()
        if selected_index:
            self.selected_object_index = selected_index[0]
            self.update_properties_text()
            self.script_editor_button.config(state=tk.NORMAL)  # Enable script editor button
    
    def draw_scene(self):
        self.canvas.delete("all")
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                x, y = obj.get_position()
                self.canvas.create_rectangle(x - 10, y - 10, x + 10, y + 10, fill=obj.color, tags="object")
    
    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
    
    def on_canvas_click(self, event):
        if self.current_scene_index != -1:
            x, y = event.x, event.y
            scene = self.scenes[self.current_scene_index]
            for i, obj in enumerate(scene.objects):
                obj_x, obj_y = obj.get_position()
                if abs(x - obj_x) <= 10 and abs(y - obj_y) <= 10:
                    self.selected_object_index = i
                    self.update_object_listbox()
                    self.object_listbox.selection_set(i)
                    self.select_object(None)
                    break
    
    def on_canvas_drag(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            x, y = event.x, event.y
            self.scenes[self.current_scene_index].objects[self.selected_object_index].set_position(x, y)
            self.update_object_listbox()
            self.draw_scene()

if __name__ == "__main__":
    root = tk.Tk()
    app = EngineGUI(root)
    root.mainloop()
