import tkinter as tk
from tkinter import ttk, scrolledtext
import pyperclip
import math
import time

class SVGPathBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG Path Builder")
        self.root.geometry("1200x800")
        
        self.points = []
        self.current_point = None
        self.dragging = False
        self.selected_point_index = None
        
        self.create_ui()
        
        self.canvas_width = 800
        self.canvas_height = 600
        self.animation_speed = 10
        self.animation_duration = 10
        self.is_animating = False
        
    def create_ui(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        ttk.Label(control_frame, text="SVG Path Builder", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.mode_var = tk.StringVar(value="add_points")
        ttk.Radiobutton(control_frame, text="Add Points", variable=self.mode_var, 
                      value="add_points").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(control_frame, text="Edit Points", variable=self.mode_var, 
                      value="edit_points").pack(anchor=tk.W, pady=2)
        
        ttk.Label(control_frame, text="Text to display:").pack(anchor=tk.W, pady=(20, 5))
        self.text_var = tk.StringVar(value="Your text here")
        ttk.Entry(control_frame, textvariable=self.text_var, width=30).pack(fill=tk.X, pady=(0, 10))
        self.text_var.trace_add("write", self.update_preview)
        
        ttk.Label(control_frame, text="Font Size:").pack(anchor=tk.W, pady=(10, 5))
        self.font_size_var = tk.StringVar(value="36")
        ttk.Entry(control_frame, textvariable=self.font_size_var, width=10).pack(anchor=tk.W, pady=(0, 10))
        self.font_size_var.trace_add("write", self.update_preview)
        
        ttk.Label(control_frame, text="Text Color:").pack(anchor=tk.W, pady=(10, 5))
        self.text_color_var = tk.StringVar(value="black")
        ttk.Entry(control_frame, textvariable=self.text_color_var, width=10).pack(anchor=tk.W, pady=(0, 10))
        self.text_color_var.trace_add("write", self.update_preview)
        
        ttk.Label(control_frame, text="Letter Spacing:").pack(anchor=tk.W, pady=(10, 5))
        self.letter_spacing_var = tk.IntVar(value=0)
        ttk.Scale(control_frame, from_=-20, to=50, variable=self.letter_spacing_var,
                 command=lambda e: self.update_preview()).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Start Offset (%):").pack(anchor=tk.W, pady=(10, 5))
        self.start_offset_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.start_offset_var, width=10).pack(anchor=tk.W, pady=(0, 10))
        self.start_offset_var.trace_add("write", self.update_preview)
        
        ttk.Label(control_frame, text="Animation Duration (seconds):").pack(anchor=tk.W, pady=(20, 5))
        self.duration_var = tk.StringVar(value="10")
        ttk.Entry(control_frame, textvariable=self.duration_var, width=10).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Button(control_frame, text="Clear Canvas", command=self.clear_canvas).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Preview Animation", command=self.toggle_animation).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Generate SVG", command=self.generate_svg).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Copy SVG Code", command=self.copy_svg_code).pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="SVG Code:").pack(anchor=tk.W, pady=(20, 5))
        self.svg_code_text = scrolledtext.ScrolledText(control_frame, width=40, height=20)
        self.svg_code_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        
        if self.mode_var.get() == "add_points":
            if len(self.points) == 0:
                self.points.append(('M', x, y))
            else:
                last_x, last_y = self.points[-1][1], self.points[-1][2]
                if self.points[-1][0] == 'C':
                    last_x, last_y = self.points[-1][5], self.points[-1][6]
                
                cp1_x, cp1_y = last_x + (x - last_x) // 3, last_y + (y - last_y) // 3
                cp2_x, cp2_y = last_x + 2 * (x - last_x) // 3, last_y + 2 * (y - last_y) // 3
                self.points.append(('C', cp1_x, cp1_y, cp2_x, cp2_y, x, y))
            
            self.draw_path()
            
        elif self.mode_var.get() == "edit_points":
            for i, point in enumerate(self.points):
                if point[0] == 'M':
                    px, py = point[1], point[2]
                    if math.hypot(x - px, y - py) < 10:
                        self.selected_point_index = (i, 0)
                        self.dragging = True
                        return
                elif point[0] == 'C':
                    for j in range(3):
                        px, py = point[1 + j*2], point[2 + j*2]
                        if math.hypot(x - px, y - py) < 10:
                            self.selected_point_index = (i, j)
                            self.dragging = True
                            return

    def on_canvas_drag(self, event):
        if self.dragging and self.selected_point_index is not None:
            x, y = event.x, event.y
            idx, point_type = self.selected_point_index
            
            if idx < len(self.points):
                if self.points[idx][0] == 'M':
                    self.points[idx] = ('M', x, y)
                elif self.points[idx][0] == 'C' and point_type < 3:
                    old_point = list(self.points[idx])
                    old_point[1 + point_type*2] = x
                    old_point[2 + point_type*2] = y
                    self.points[idx] = tuple(old_point)
                
                self.draw_path()

    def on_canvas_release(self, event):
        self.dragging = False
        
    def clear_canvas(self):
        self.points = []
        self.selected_point_index = None
        self.canvas.delete("all")
        self.is_animating = False
        
    def draw_path(self):
        self.canvas.delete("all")
        
        if len(self.points) > 0:
            path_coords = []
            if self.points[0][0] == 'M':
                path_coords.extend([self.points[0][1], self.points[0][2]])
            
            for point in self.points[1:]:
                if point[0] == 'C':
                    prev_x, prev_y = path_coords[-2], path_coords[-1]
                    cp1_x, cp1_y = point[1], point[2]
                    cp2_x, cp2_y = point[3], point[4]
                    end_x, end_y = point[5], point[6]
                    
                    segments = 10
                    for i in range(1, segments + 1):
                        t = i / segments
                        x = (1-t)**3 * prev_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * end_x
                        y = (1-t)**3 * prev_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * end_y
                        path_coords.extend([x, y])
            
            if len(path_coords) >= 4:
                self.canvas.create_line(path_coords, fill="black", width=2, smooth=True, tags="path")
            
            for i, point in enumerate(self.points):
                if point[0] == 'M':
                    x, y = point[1], point[2]
                    self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue", tags=f"point_{i}")
                    self.canvas.create_text(x, y-15, text=f"M{i}", tags=f"label_{i}")
                elif point[0] == 'C':
                    cp1_x, cp1_y = point[1], point[2]
                    cp2_x, cp2_y = point[3], point[4]
                    x, y = point[5], point[6]
                    
                    self.canvas.create_oval(cp1_x-4, cp1_y-4, cp1_x+4, cp1_y+4, fill="red", tags=f"cp1_{i}")
                    self.canvas.create_oval(cp2_x-4, cp2_y-4, cp2_x+4, cp2_y+4, fill="green", tags=f"cp2_{i}")
                    self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue", tags=f"point_{i}")
                    
                    if i > 0:
                        prev_x, prev_y = self.get_previous_endpoint(i)
                        self.canvas.create_line(prev_x, prev_y, cp1_x, cp1_y, fill="red", dash=(2, 2), tags=f"handle_cp1_{i}")
                        self.canvas.create_line(x, y, cp2_x, cp2_y, fill="green", dash=(2, 2), tags=f"handle_cp2_{i}")
                    
                    self.canvas.create_text(cp1_x, cp1_y-10, text=f"CP1.{i}", tags=f"label_cp1_{i}")
                    self.canvas.create_text(cp2_x, cp2_y-10, text=f"CP2.{i}", tags=f"label_cp2_{i}")
                    self.canvas.create_text(x, y-15, text=f"P{i}", tags=f"label_point_{i}")
        
        self.update_preview()
    
    def get_previous_endpoint(self, index):
        if index <= 0: return 0, 0
        prev = self.points[index-1]
        return (prev[1], prev[2]) if prev[0] == 'M' else (prev[5], prev[6])
        
    def get_path_string(self):
        return " ".join([
            f"M{p[1]},{p[2]}" if p[0] == 'M' else 
            f"C {p[1]},{p[2]}, {p[3]},{p[4]}, {p[5]},{p[6]}"
            for p in self.points
        ])
        
    def update_preview(self, *args):
        self.canvas.delete("text_preview")
        if not self.points or not self.text_var.get():
            return
            
        try:
            font_size = int(self.font_size_var.get())
            start_offset_percent = float(self.start_offset_var.get())
        except ValueError:
            return
            
        text_color = self.text_color_var.get()
        letter_spacing = self.letter_spacing_var.get()
        path_points = self.sample_path_points(100)
        start_offset_idx = max(0, min(int(len(path_points) * start_offset_percent / 100), len(path_points)-1))
        
        char_width = font_size * 0.6
        current_pos = start_offset_idx
        
        for char in self.text_var.get():
            if current_pos >= len(path_points):
                break
            x, y = path_points[current_pos]
            self.canvas.create_text(x, y, text=char, fill=text_color, 
                                   font=("Arial", font_size), angle=0, 
                                   anchor="center", tags="text_preview")
            current_pos += int(char_width) + letter_spacing
        
        self.generate_svg()
    
    def sample_path_points(self, num_points):
        path_points = []
        if not self.points:
            return path_points
            
        if self.points[0][0] == 'M':
            path_points.append((self.points[0][1], self.points[0][2]))
        
        for i in range(1, len(self.points)):
            if self.points[i][0] == 'C':
                prev_x, prev_y = self.get_previous_endpoint(i)
                cp1_x, cp1_y = self.points[i][1], self.points[i][2]
                cp2_x, cp2_y = self.points[i][3], self.points[i][4]
                end_x, end_y = self.points[i][5], self.points[i][6]
                
                points_per_segment = num_points // max(1, len(self.points)-1)
                for j in range(1, points_per_segment + 1):
                    t = j / points_per_segment
                    x = (1-t)**3 * prev_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * end_x
                    y = (1-t)**3 * prev_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * end_y
                    path_points.append((x, y))
        return path_points
            
    def generate_svg(self):
        try:
            if not self.points:
                self.svg_code_text.delete(1.0, tk.END)
                self.svg_code_text.insert(tk.END, "No path defined yet. Add points to create a path.")
                return

            # Generate proper path data
            path_data = []
            for point in self.points:
                if point[0] == 'M':
                    path_data.append(f"M{point[1]},{point[2]}")
                elif point[0] == 'C':
                    path_data.append(f"C{point[1]},{point[2]} {point[3]},{point[4]} {point[5]},{point[6]}")

            # Calculate viewBox based on actual points
            all_x = [p[1] for p in self.points if p[0] == 'M'] + \
                    [p[i] for p in self.points if p[0] == 'C' for i in [1,3,5]]
            all_y = [p[2] for p in self.points if p[0] == 'M'] + \
                    [p[i] for p in self.points if p[0] == 'C' for i in [2,4,6]]
                    
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            viewbox = f"{min_x-50} {min_y-50} {max_x-min_x+100} {max_y-min_y+100}"

            svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" 
                viewBox="{viewbox}" 
                width="100%" 
                height="100%">
                <path id="curve" 
                    d="{' '.join(path_data)}" 
                    fill="none" 
                    stroke="black" 
                    stroke-width="2"/>
                <text font-size="{self.font_size_var.get()}" 
                    fill="{self.text_color_var.get()}" 
                    letter-spacing="{self.letter_spacing_var.get()}px">
                    <textPath href="#curve" 
                        startOffset="{self.start_offset_var.get()}%">
                        {self.text_var.get()}
                        <animate 
                            attributeName="startOffset" 
                            from="100%" 
                            to="-100%" 
                            dur="{self.duration_var.get()}s" 
                            repeatCount="indefinite"/>
                    </textPath>
                </text>
            </svg>'''

            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, svg_code)
        
        except Exception as e:
            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, f"Error generating SVG: {str(e)}")

    def get_path_string(self):
        path = []
        for p in self.points:
            if p[0] == 'M':
                path.append(f'M{p[1]},{p[2]}')
            elif p[0] == 'C':
                # Format: C x1,y1 x2,y2 x,y
                path.append(f'C{p[1]},{p[2]} {p[3]},{p[4]} {p[5]},{p[6]}')
        return ' '.join(path)

        
    def copy_svg_code(self):
        pyperclip.copy(self.svg_code_text.get(1.0, tk.END))
        status_label = ttk.Label(self.root, text="SVG code copied to clipboard!", foreground="green")
        status_label.place(relx=0.5, rely=0.9, anchor="center")
        self.root.after(2000, status_label.destroy)
    
    def toggle_animation(self):
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.animate_text()
        
    def animate_text(self):  # Now properly indented inside the class
        if not self.is_animating:
            return

        self.canvas.delete("text_preview")
        text = self.text_var.get()
        if not text:
            self.root.after(50, self.animate_text)
            return

        try:
            font_size = int(self.font_size_var.get())
            letter_spacing = self.letter_spacing_var.get()
            duration = float(self.duration_var.get())
        except ValueError:
            self.root.after(50, self.animate_text)
            return

        path_points = self.sample_path_points(200)
        if not path_points:
            self.root.after(50, self.animate_text)
            return

        current_time = time.time()
        progress = (current_time % duration) / duration
        
        start_offset = int(len(path_points) * (1 - progress))
        char_width = font_size * 0.6
        
        current_pos = start_offset
        for char in text:
            if current_pos >= len(path_points) or current_pos < 0:
                continue
            x, y = path_points[current_pos]
            self.canvas.create_text(x, y, 
                                  text=char, 
                                  fill=self.text_color_var.get(), 
                                  font=("Arial", font_size), 
                                  angle=0, 
                                  anchor="center", 
                                  tags="text_preview")
            current_pos += int(char_width) + letter_spacing
        
        self.root.after(50, self.animate_text)

def main():
    root = tk.Tk()
    app = SVGPathBuilder(root)
    root.mainloop()

if __name__ == "__main__":
    main()