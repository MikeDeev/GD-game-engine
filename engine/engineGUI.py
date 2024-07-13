import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import shutil
import uuid
import engine.compiler as compile
from math import cos, sin, radians
from tkinter import colorchooser
import random

scenesNumber = 0

class GameObject:
    def __init__(self, obj_id, x=0, y=0, rotation=0, color_id=None, groups=None, name="", script=""):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.rotation = rotation
        self.color_id = color_id
        self.groups = groups if groups is not None else []
        self.name = name
        self.script = script
    
    def get_position(self):
        return self.x, self.y


class Scene:
    def __init__(self, name):
        global scenesNumber
        scenesNumber += 1
        self.name = name
        self.sceneID = 800 + scenesNumber
        self.objects = []

    
    def to_dict(self):
        return {
            "name": self.name,
            "objects": [obj.__dict__ for obj in self.objects],
            "id": self.sceneID
        }
    
    @classmethod
    def from_dict(cls, data):
        scene = cls(data["name"])
        scene.objects = []
        for obj_data in data["objects"]:
            obj = GameObject(
                obj_id=obj_data["obj_id"],
                x=obj_data["x"],
                y=obj_data["y"],
                rotation=obj_data["rotation"],
                color_id=obj_data["color_id"],
                groups=obj_data["groups"],
                name=obj_data["name"],
                script=obj_data["script"]
            )
            scene.objects.append(obj)
        return scene

class ScriptEditorPopup:
    def __init__(self, parent, script, apply_callback):
        self.parent = parent
        self.script = script
        self.apply_callback = apply_callback
        
        self.popup = tk.Toplevel(parent)
        self.popup.title("Script Editor")
        
        self.text_widget = tk.Text(self.popup, width=60, height=20)
        self.text_widget.pack(padx=10, pady=10)
        self.text_widget.insert(tk.END, script)
        
        ttk.Button(self.popup, text="Apply", command=self.apply_changes).pack(pady=5)
    
    def apply_changes(self):
        self.script = self.text_widget.get("1.0", tk.END).strip()
        self.apply_callback(self.script)
        self.popup.destroy()

class ProjectSettingsPopup:
    def __init__(self, parent, project_settings, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback
        self.project_settings = project_settings.copy() 
        
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
        self.root.title("Engine GUI")
        self.root.geometry("800x600")
        self.root.iconbitmap("icon.ico")
        
        self.scenes = []
        self.current_scene_index = -1
        self.selected_object_index = -1
        self.project_settings = {
            "Color1": "#FFFFFF"
        }
        
        self.create_menu()
        self.create_scene_panel()
        self.create_object_panel()
        self.create_property_panel()
        self.create_canvas()
        
        self.draw_scene()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Scene", command=self.new_scene)
        file_menu.add_command(label="Delete Scene", command=self.delete_scene)
        file_menu.add_separator()
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="Project Settings", command=self.open_project_settings)
        
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Project", menu=project_menu)
        
        menubar.add_command(label="Compile Project", command=self.compile_project)

        self.root.config(menu=menubar)
    
    def create_scene_panel(self):
        scene_panel = ttk.Frame(self.root)
        scene_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(scene_panel, text="Scenes", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.scene_listbox = tk.Listbox(scene_panel, selectmode=tk.SINGLE)
        self.scene_listbox.pack(expand=True, fill=tk.BOTH)
        self.scene_listbox.bind("<ButtonRelease-1>", self.select_scene)
        
        scrollbar = ttk.Scrollbar(scene_panel, orient=tk.VERTICAL, command=self.scene_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scene_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(scene_panel, text="New Scene", command=self.new_scene).pack(pady=5)
    
    def create_object_panel(self):
        object_panel = ttk.Frame(self.root)
        object_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(object_panel, text="Objects", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.object_listbox = tk.Listbox(object_panel, selectmode=tk.SINGLE)
        self.object_listbox.pack(expand=True, fill=tk.BOTH)
        self.object_listbox.bind("<ButtonRelease-1>", self.select_object)
        self.object_listbox.bind("<B1-Motion>", self.move_object)
        
        scrollbar = ttk.Scrollbar(object_panel, orient=tk.VERTICAL, command=self.object_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.object_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(object_panel, text="Add Object", command=self.add_object).pack(pady=5)
        #ttk.Button(object_panel, text="Rename Object", command=self.rename_object).pack(pady=5)
    
    def create_property_panel(self):
        property_panel = ttk.Frame(self.root)
        property_panel.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(property_panel, text="Properties", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.property_frame = ttk.Frame(property_panel)
        self.property_frame.pack(expand=True, fill=tk.BOTH)
        
    def update_property_panel(self):
        for widget in self.property_frame.winfo_children():
            widget.destroy()
        
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            
            ttk.Label(self.property_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5)
            self.name_entry = ttk.Entry(self.property_frame)
            self.name_entry.grid(row=0, column=1, padx=5)
            self.name_entry.insert(0, obj.name)
            self.name_entry.bind("<Return>", self.update_object_name)
            
            ttk.Label(self.property_frame, text="Position:").grid(row=1, column=0, sticky=tk.W, padx=5)
            self.position_x_entry = ttk.Entry(self.property_frame, width=5)
            self.position_x_entry.grid(row=1, column=1, padx=5)
            self.position_x_entry.insert(0, obj.x)
            self.position_x_entry.bind("<Return>", self.update_object_position)
            self.position_y_entry = ttk.Entry(self.property_frame, width=5)
            self.position_y_entry.grid(row=1, column=2, padx=5)
            self.position_y_entry.insert(0, obj.y)
            self.position_y_entry.bind("<Return>", self.update_object_position)
            
            ttk.Label(self.property_frame, text="Rotation:").grid(row=2, column=0, sticky=tk.W, padx=5)
            self.rotation_entry = ttk.Entry(self.property_frame, width=10)
            self.rotation_entry.grid(row=2, column=1, columnspan=2, padx=5)
            self.rotation_entry.insert(0, obj.rotation)
            self.rotation_entry.bind("<Return>", self.update_object_rotation)
            
            ttk.Label(self.property_frame, text="Color:").grid(row=3, column=0, sticky=tk.W, padx=5)
            self.color_var = tk.StringVar()
            self.color_var.set(obj.color_id if obj.color_id else "")
            self.color_optionmenu = ttk.OptionMenu(self.property_frame, self.color_var, *list(self.project_settings.keys()))
            self.color_optionmenu.grid(row=3, column=1, columnspan=2, padx=5)
            ttk.Button(self.property_frame, text="Apply Color", command=self.apply_object_color).grid(row=3, column=3, padx=5)
            
            ttk.Label(self.property_frame, text="Groups:").grid(row=4, column=0, sticky=tk.W, padx=5)
            self.groups_text = tk.Text(self.property_frame, height=4, width=20)
            self.groups_text.grid(row=4, column=1, columnspan=2, padx=5)
            self.groups_text.insert(tk.END, "\n".join(obj.groups))
            self.groups_text.bind("<Return>", self.update_object_groups)
            
            ttk.Button(self.property_frame, text="Add Group", command=self.add_group).grid(row=5, column=1, padx=5, pady=5)
            ttk.Button(self.property_frame, text="Remove Group", command=self.remove_group).grid(row=5, column=2, padx=5, pady=5)
            
            ttk.Button(self.property_frame, text="Edit Script", command=self.edit_script).grid(row=6, column=0, columnspan=3, padx=5, pady=5)
    
    def edit_script(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            ScriptEditorPopup(self.root, obj.script, self.apply_script_changes)

    def apply_script_changes(self, script):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            self.scenes[self.current_scene_index].objects[self.selected_object_index].script = script

    def update_object_name(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            new_name = self.name_entry.get().strip()
            if new_name:
                self.scenes[self.current_scene_index].objects[self.selected_object_index].name = new_name
                self.update_object_listbox()
    
    def update_object_position(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            try:
                new_x = float(self.position_x_entry.get())
                new_y = float(self.position_y_entry.get())
                self.scenes[self.current_scene_index].objects[self.selected_object_index].x = new_x
                self.scenes[self.current_scene_index].objects[self.selected_object_index].y = new_y
                self.draw_scene()
            except ValueError:
                pass
    
    def update_object_rotation(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            try:
                new_rotation = float(self.rotation_entry.get())
                self.scenes[self.current_scene_index].objects[self.selected_object_index].rotation = new_rotation
                self.draw_scene()
            except ValueError:
                pass
    
    def apply_object_color(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            color_id = self.color_var.get()
            if color_id in self.project_settings:
                self.scenes[self.current_scene_index].objects[self.selected_object_index].color_id = color_id
                self.draw_scene()
    
    def update_object_groups(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            groups_text = self.groups_text.get("1.0", tk.END).strip()
            groups = [group.strip() for group in groups_text.split("\n") if group.strip()]
            self.scenes[self.current_scene_index].objects[self.selected_object_index].groups = groups
    
    def add_group(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            new_group = simpledialog.askstring("Add Group", "Enter group name:")
            if new_group:
                self.scenes[self.current_scene_index].objects[self.selected_object_index].groups.append(new_group)
                self.update_properties_text()
    
    def remove_group(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            selected_text = self.groups_text.tag_ranges(tk.SEL)
            if selected_text:
                start = int(selected_text[0])
                end = int(selected_text[1])
                self.groups_text.delete(start, end)
                self.update_properties_text()
    
    def new_scene(self):
        scene_name = simpledialog.askstring("New Scene", "Enter scene name:")
        if scene_name:
            self.scenes.append(Scene(scene_name))
            self.update_scene_listbox()
            self.update_object_listbox()

    
    def delete_scene(self):
        if self.current_scene_index != -1:
            del self.scenes[self.current_scene_index]
            self.current_scene_index = -1
            self.update_scene_listbox()
            self.update_object_listbox()
            self.draw_scene()
    
    def rename_object(self):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            new_name = simpledialog.askstring("Rename Object", "Enter new object name:")
            if new_name:
                self.scenes[self.current_scene_index].objects[self.selected_object_index].name = new_name
                self.update_object_listbox()
                self.draw_scene()
    
    def move_object(self, event):
        if self.selected_object_index != -1 and self.current_scene_index != -1:
            obj = self.scenes[self.current_scene_index].objects[self.selected_object_index]
            x = event.x
            y = event.y
            obj.x = x
            obj.y = y
            self.draw_scene()
    
    def open_project_settings(self):
        ProjectSettingsPopup(self.root, self.project_settings, self.apply_project_settings)
    
    def apply_project_settings(self, settings):
        self.project_settings = settings
    
    def select_scene(self, event):
        selection = self.scene_listbox.curselection()
        if selection:
            self.current_scene_index = selection[0]
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()
        else:
            self.current_scene_index = -1
            self.clear_object_listbox()
            self.clear_property_text()
            self.draw_scene()
    
    def select_object(self, event):
        selection = self.object_listbox.curselection()
        if selection:
            self.selected_object_index = selection[0]
            self.update_properties_text()
        else:
            self.selected_object_index = -1
            self.clear_property_text()
    
    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="#333333")
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.bind("<Button-1>", self.select_object)
        self.canvas.bind("<B1-Motion>", self.move_object)
    
    def draw_scene(self):
        self.canvas.delete("all")
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                x, y = obj.get_position()
                self.canvas.create_rectangle(x - 10, y - 10, x + 10, y + 10, fill=self.project_settings.get(obj.color_id, "#FFFFFF"))
                self.canvas.create_text(x, y, text=str(obj.name), fill="#000000")
                if obj.rotation != 0:
                    self.canvas.create_line(x, y, x + 20 * cos(radians(obj.rotation)), y + 20 * sin(radians(obj.rotation)), fill="#FF0000")
    
    def update_scene_listbox(self):
        self.scene_listbox.delete(0, tk.END)
        for scene in self.scenes:
            self.scene_listbox.insert(tk.END, scene.name)
    
    def update_object_listbox(self):
        self.object_listbox.delete(0, tk.END)
        if self.current_scene_index != -1:
            scene = self.scenes[self.current_scene_index]
            for obj in scene.objects:
                self.object_listbox.insert(tk.END, obj.name)
    
    def clear_object_listbox(self):
        self.object_listbox.delete(0, tk.END)
    
    def update_properties_text(self):
        self.update_property_panel()
    
    def clear_property_text(self):
        for widget in self.property_frame.winfo_children():
            widget.destroy()
    
    def save_project(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            data = {
                "scenesNumber": scenesNumber,
                "scenes": [scene.to_dict() for scene in self.scenes]
                }
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
    
    def load_project(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                scenesNumber = data["scenesNumber"]
                self.scenes = [Scene.from_dict(scene_data) for scene_data in data["scenes"]]
                self.update_scene_listbox()
                self.current_scene_index = -1
                self.update_object_listbox()
                self.clear_property_text()
                self.draw_scene()

    def add_object(self):
        if self.current_scene_index != -1:
            obj_id = 1
            new_object = GameObject(obj_id,32,32,0,None,[],"object","")
            self.scenes[self.current_scene_index].objects.append(new_object)
            self.update_object_listbox()
            self.clear_property_text()
            self.draw_scene()

    def compile_project(self):
        game_name = simpledialog.askstring("Compile", "Whats the name of the lvl in gd you want to replace with the compiled game?")
        if game_name:
            compile.compile_spwn(self.scenes,"PROJ_" + game_name + ".compiled.spwn",game_name)
            
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    gui = EngineGUI(root)
    gui.run()