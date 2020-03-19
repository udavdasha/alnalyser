#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a module for color picking management
@ Daria Dibrova aka udavdasha
"""
curr_version = "0.7"
import sys, platform, os
if sys.version_info < (3, 0): # Python 2.x
    import Tkinter as tkinter
    import tkMessageBox
else:                         # Python 3.x
    import tkinter
    import tkinter.messagebox as tkMessageBox

def get_gradient_canvas(parent, value, channel_name, order, canvas_w, canvas_h):
    """
    Method create a canvas attributed to a <parent> with width as in <canvas_w>
    and height as in <canvas_h>. This canvas will be filled with a gradient image
    of one of three channels: <channel_name> should be 'red', green' or 'blue'.
    Value of selected color which remains the same is specified by <value>.
    Orientation of gradient is set by <order> option: 1 is 'from white to color'
    and -1 is 'from color to white'.

    Returns: tkinter.Canvas
    """
    result = tkinter.Canvas(parent)
    img = tkinter.PhotoImage(width = canvas_w, height = canvas_h)
    result.img = img
    all_lines = list()
    vary_range = None
    if order == 1:
        vary_range = range(0, 256)
    if order == -1:
        vary_range = range(255, -1, -1)

    for i in vary_range: 
        the_color = None
        if channel_name == "blue":
            the_color = "#%02x%02x%02x" % (i, i, value)
        if channel_name == "green":
            the_color = "#%02x%02x%02x" % (i, value, i)
        if channel_name == "red":
            the_color = "#%02x%02x%02x" % (value, i, i)
        horizontal_line = "{" + " ".join([the_color]*canvas_w) + "}" 
        all_lines.append(horizontal_line)
    img.put(" ".join(all_lines))
    result.create_image((1, 1), image = img, anchor = "nw", state = "normal")
    return result

class ColorRow:
    """
    This class binds together all objects of a single color row 
    """
    def __init__(self, label, hex_entry, name_entry, pick_button, delete_button, up_button, down_button):
       self.label = label
       self.hex_entry = hex_entry
       self.name_entry = name_entry
       self.pick_button = pick_button
       self.delete_button = delete_button
       self.up_button = up_button
       self.down_button = down_button

class CustomClick:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class ButtonExe(tkinter.Button):
    """
    This class inherits tkinter.Button and is required to execute an action
    on a certain row of colors   
    """
    def __init__(self, parent, host, mode, index, text_on_top):
        tkinter.Button.__init__(self, parent, text = text_on_top)
        self.host = host
        self.mode = mode
        self.index = index

    def action(self):
        if self.mode == "DELETE":
            self.host.delete_color(self.index)
        if self.mode == "PICK":
            self.host.pick_color(self.index)
        if self.mode == "UP":
            self.host.row_move(self.index, -1)
        if self.mode == "DOWN":
            self.host.row_move(self.index, 1)

class ColorFrame(tkinter.Frame):
    """
    This class inherits <tkinter.Frame> as represent a frame with the options to select colors manually
    and/or load them manually from a file.
    Current colors are stored in the <self.colors> list is a hex representation
    Current list names are stored in the <self.names> list
    """
    def __init__(self, parent, background_color, initial_colors, initial_names, label_color, color_filename = None):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        if platform.system() == "Linux":
            self.parent.bind("<Button-4>", self.mouse_wheel)
            self.parent.bind("<Button-5>", self.mouse_wheel)
        else:
            self.parent.bind("<MouseWheel>", self.mouse_wheel)

        self.colors = initial_colors
        self.names = initial_names
        self.color_rows = list()       
        self.back = background_color
        self.label_color = label_color
        self.p = 5
        self.main_canvas = None
        self.file_mode = None       # Variable with the mode to read/write file
        self.wheel_img = None       # This should contain a wheel image, or it will disapear        
        self.frame_id = None       
        self.color_wheel = None
        self.check_canvas = None
        self.check_circle = None        
        self.select_position = None # Oval and other widgets showing the selection  
        self.picked_color = "#000000"
        self.blue_scale = None
        self.curr_blue = 150   
        self.filename_entry = None
        self.y_scrollbar = None
        self.canvas_panel = None
        self.file_panel = None

        self.create_UI(color_filename)

    def create_UI(self, color_filename):
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        file_panel = tkinter.Frame(self)
        file_panel.grid(row = 0, column = 0, columnspan = 4, padx = self.p, pady = self.p, sticky = "NEW")
        file_panel.grid_columnconfigure(6, weight = 1) 
        self.file_mode = tkinter.StringVar()
        self.file_mode.set("Replace")
        radio = tkinter.Radiobutton(file_panel, text = "Replace", variable = self.file_mode, value = "Replace")
        radio.grid(row = 0, column = 0, sticky = "NSW")
        radio = tkinter.Radiobutton(file_panel, text = "Append", variable = self.file_mode, value = "Append")
        radio.grid(row = 0, column = 1, sticky = "NSW")
        
        self.filename_entry = tkinter.Entry(file_panel, width = 40)
        if color_filename == None:
            self.filename_entry.insert(tkinter.END, "default_colors.txt")
        else:
            self.filename_entry.insert(tkinter.END, color_filename)
        self.filename_entry.grid(row = 0, column = 2, padx = 1, pady = 1, sticky = "NSW")
        load_button = tkinter.Button(file_panel, text = "Load", command = self.load_file)
        load_button.grid(row = 0, column = 3, padx = 1, pady = 1, sticky = "NSW")
        save_button = tkinter.Button(file_panel, text = "Save", command = self.save_file)
        save_button.grid(row = 0, column = 4, padx = 1, pady = 1, sticky = "NSW")
        add_button = tkinter.Button(file_panel, text = "+", command = self.add_color)
        add_button.grid(row = 0, column = 5, padx = 1, pady = 1, sticky = "NSW")
        self.file_panel = file_panel

        self.canvas_panel = tkinter.Frame(self, background = self.back)        
        self.canvas_panel.grid(row = 1, column = 0, rowspan = 2, padx = self.p, pady = self.p, sticky = "NSEW")
        self.canvas_panel.grid_rowconfigure(0, weight = 1)
        self.canvas_panel.grid_columnconfigure(0, weight = 1)
        self.fill_color_panel()

        self.draw_wheel()

        canvas_w = 20
        canvas_h = 256
        blue_canvas = get_gradient_canvas(self, 255, "blue", -1, canvas_w, canvas_h)
        blue_canvas.grid(row = 1, column = 2, pady = self.p, sticky = "NSEW")        
        blue_canvas.configure(width = canvas_w, height = canvas_h) 

        blue_scale = tkinter.Scale(self, from_ = 0, to = 255, orient = tkinter.VERTICAL, troughcolor = self.cget("background"), 
                                   relief = "flat", showvalue = 0, length = 255, width = 10)
        blue_scale.grid(row = 1, column = 3, pady = self.p, sticky = "N")
        blue_scale.bind("<ButtonRelease-1>", self.set_blue)
        blue_scale.bind("<B1-Motion>", self.pick_blue)        
        blue_scale.set(self.curr_blue)
        self.blue_scale = blue_scale 

        self.check_canvas = tkinter.Canvas(self) 
        self.check_canvas.grid(row = 2, column = 1, columnspan = 3, padx = self.p, pady = self.p, sticky = "NEW")
        center = (self.color_wheel.winfo_reqwidth() + self.blue_scale.winfo_reqwidth() + blue_canvas.winfo_reqwidth())/2
        self.check_circle = self.check_canvas.create_oval(center - 50, 10, center + 50, 110, fill = "#000000", outline = "#000000")
        self.check_canvas.configure(width = center * 2, height = 120)       

    def mouse_wheel(self, event):
        self.main_canvas.yview_scroll(-1*(event.delta/120), "units")

    def fill_color_panel(self):
        #self.canvas_panel.grid_forget()
        self.canvas_panel.destroy()
        self.canvas_panel = tkinter.Frame(self, background = self.back)        
        self.canvas_panel.grid(row = 1, column = 0, rowspan = 2, padx = self.p, pady = self.p, sticky = "NSEW")
        self.canvas_panel.grid_rowconfigure(0, weight = 1)
        self.canvas_panel.grid_columnconfigure(0, weight = 1)
        self.color_rows = list()

        canvas = tkinter.Canvas(self.canvas_panel, background = self.back)
        canvas.grid(row = 0, column = 0, sticky = "NSEW")
        self.y_scrollbar = tkinter.Scrollbar(self.canvas_panel, orient = tkinter.VERTICAL)
        self.y_scrollbar.grid(row = 0, column = 1, padx = 1, pady = 1, sticky = "NS")
        self.y_scrollbar.configure(command = canvas.yview)
        canvas.configure(yscrollcommand = self.y_scrollbar.set)
        
        color_frame = tkinter.Frame(canvas, background = self.back)
        color_frame.grid_columnconfigure(1, weight = 1)
        for i in range(len(self.colors)):
            curr_color = self.colors[i]
            label = tkinter.Label(color_frame, text = "%i" % (i + 1), background = curr_color, foreground = self.label_color)
            label.grid(row = i, column = 0, padx = 1, pady = 1, sticky = "NEW")
            hex_color = tkinter.Entry(color_frame, width = 10)
            hex_color.insert(tkinter.END, curr_color)
            hex_color.grid(row = i, column = 1, padx = 1, pady = 1, sticky = "NEW")
            hex_color.number = i
            hex_color.bind("<Return>", self.enter_press)
            color_name = tkinter.Entry(color_frame, width = 30) 
            color_name.grid(row = i, column = 2, padx = 1, pady = 1, sticky = "NEW")
            if i < len(self.names):
                color_name.insert(tkinter.END, self.names[i])
            else:
                self.names.append("<COLOR>")
            up_button = ButtonExe(color_frame, self, "UP", i, "↑")
            up_button.grid(row = i, column = 3, padx = 1, pady = 1, sticky = "NEW")
            up_button.configure(command = up_button.action)
            down_button = ButtonExe(color_frame, self, "DOWN", i, "↓")
            down_button.grid(row = i, column = 4, padx = 1, pady = 1, sticky = "NEW")
            down_button.configure(command = down_button.action)
            delete_button = ButtonExe(color_frame, self, "DELETE", i, "Delete")
            delete_button.configure(command = delete_button.action)
            delete_button.grid(row = i, column = 5, padx = 1, pady = 1, sticky = "NEW")
            pick_button = ButtonExe(color_frame, self, "PICK", i, "Pick...")
            pick_button.configure(command = pick_button.action)
            pick_button.grid(row = i, column = 6, padx = 1, pady = 1, sticky = "NEW")
            
            self.color_rows.append(ColorRow(label, hex_color, color_name, pick_button, delete_button, up_button, down_button))
            
        frame_id = canvas.create_window(0, 0, anchor = "nw", window = color_frame) 
        color_frame.update_idletasks()
        canvas.config(scrollregion = canvas.bbox(frame_id))
        #canvas.bind("<Configure>", self.resize_frame)
        canvas.itemconfig(frame_id, height = color_frame.winfo_height())
        canvas.configure(width = color_frame.winfo_width() + self.p, height = color_frame.winfo_height() + self.p)         
        self.frame_id = frame_id
        self.main_canvas = canvas

    def enter_press(self, event):
        color_num = event.widget.number
        new_color = event.widget.get()
        try:
            (r, g, b) = self.parent.winfo_rgb(new_color)
        except:
            tkMessageBox.showinfo("Invalid color", "Inputed color '%s' is not a valid hex color representation!" % new_color)
            return
        self.colors[color_num] = new_color.upper()
        self.save_and_redraw()

    def add_color(self):        
        self.colors.append("#FFFFFF")        
        self.names = self.get_color_names()
        self.names.append("<COLOR>")
        self.fill_color_panel()
        self.main_canvas.yview_moveto(1.0)

    def delete_color(self, color_num):
        self.colors.pop(color_num)
        self.names.pop(color_num)
        self.save_and_redraw()

    def save_and_redraw(self):
        """
        Method saves current names and redraws color panel; it also returns
        canvas position to the same place
        """
        #self.names = self.get_color_names()
        (begin, end) = self.y_scrollbar.get()
        self.fill_color_panel()
        self.main_canvas.yview_moveto(begin)

    def pick_color(self, color_num):
        """
        Method is used to modify color of the clicked row with the <self.picked_color>
        """        
        self.colors[color_num] = self.picked_color.upper()
        self.names = self.get_color_names()
        self.save_and_redraw()

    def get_color_names(self):
        """
        Method returns a list of color names specified; if no color is specified, it will be '<COLOR>'
        """
        result = list()
        for row in self.color_rows:
            curr_color = row.name_entry.get().strip()
            if len(curr_color) == 0: # empty field
                curr_color = "<COLOR>"
            result.append(curr_color)
        return result

    def row_move(self, color_num, direction):
        if (direction == -1) and (color_num == 0): # It is already on top
            return
        if (direction == 1) and (color_num == len(self.colors) - 1): # It is already on bottom
            return
        self.names = self.get_color_names()
        neighbor_color = self.colors[color_num + direction]
        neighbor_name = self.names[color_num + direction]
        self.colors[color_num + direction] = self.colors[color_num]
        self.names[color_num + direction] = self.names[color_num]
        self.colors[color_num] = neighbor_color
        self.names[color_num] = neighbor_name
        self.save_and_redraw()
               
    def draw_wheel(self):
        if self.color_wheel != None:
            self.color_wheel.delete("all")
            self.color_wheel.grid_forget()

        self.color_wheel = tkinter.Canvas(self, background = "#FFFFFF", cursor = "crosshair") 
        self.color_wheel.grid(row = 1, column = 1, padx = self.p, pady = self.p, sticky = "N")
        img = tkinter.PhotoImage(width = 256, height = 256)
        self.wheel_img = img # Required to save!
        all_lines = list()
        for g in range (0, 256):            
            pixels = list()
            for r in range (0, 256):
                the_color = "#%02x%02x%02x" % (r, g, self.curr_blue)
                pixels.append(the_color)                
            horizontal_line = "{" + " ".join(pixels) + "}"
            all_lines.append(horizontal_line)
        img.put(" ".join(all_lines))
        self.color_wheel.create_image((1, 1), image = img, anchor = "nw", state = "normal")

        self.color_wheel.bind("<B1-Motion>", self.wheel_click)
        self.color_wheel.bind("<Button-1>", self.wheel_click)
        self.color_wheel.bind("<Button-3>", self.wheel_pick)
        self.color_wheel.configure(width = 255, height = 255)

    def set_blue(self, event):
        self.curr_blue = self.blue_scale.get()
        self.draw_wheel()
        self.pick_blue(event)

    def pick_blue(self, event):
        self.curr_blue = self.blue_scale.get()
        (x, y) = self.draw_selection_cursor(7)
        custom_event = CustomClick(x, y)
        self.wheel_click(custom_event)
            
    def draw_selection_cursor(self, size = 5):
        if self.select_position != None:
            for figure in self.select_position: 
                self.color_wheel.delete(figure)
        x = int(self.picked_color[1:3], 16)
        y = int(self.picked_color[3:5], 16)       
        self.select_position = list()
        self.select_position.append(self.color_wheel.create_rectangle(x - size, y - size, x + size, y + size, fill = "", outline = "#FFFFFF"))
        self.select_position.append(self.color_wheel.create_oval(x - 1, y - 1, x + 1, y + 1, fill = "#FFFFFF", outline = ""))
        return (x, y)        

    def wheel_click(self, event):
        """
        Method activated on LMB click on a color palette or while dragging LMB.        
        """
        if (event.x <= 255) and (event.y <= 255) and (event.x >= 0) and (event.y >= 0):
            the_color = "#%02x%02x%02x" % (event.x, event.y, self.curr_blue)
            self.check_canvas.itemconfigure(self.check_circle, fill = the_color, outline = the_color)
            self.picked_color = the_color
            self.draw_selection_cursor(7)

    def wheel_pick(self, event):
        """
        Method activated on RMB click on a color palette. In contrast with the
        <self.wheel_click> method, it will try to pick current color for the top
        white color found in a palette
        """
        if (event.x <= 255) and (event.y <= 255)and(event.x >= 0) and (event.y >= 0):
            self.wheel_click(event)            
            for i in range(len(self.colors)):
                if (self.colors[i] == "#FFFFFF") and (self.names[i] == "<COLOR>"): # white and fresh
                    self.colors[i] = self.picked_color.upper()                   
                    self.save_and_redraw()
                    break

    def get_names_and_colors(self, filename):
        """
        Method is used by <self.load_file> method and <self.save_file> method (under appending option)
        """
        file_colors = list()
        file_names = list()
        scheme_file = open(filename)
        for string in scheme_file:
            string = string.strip()
            if len(string) == 0:
                continue
            fields = string.split("\t")
            if len(fields) == 1: # No name information specified                        
                file_colors.append(fields[0])
                file_names.append("<COLOR>")
            else:
                file_colors.append(fields[0])
                file_names.append(fields[1])
        scheme_file.close()
        return (file_colors, file_names)

    def get_names_to_colors(self, color_list, names_list):
        names_to_color = dict()
        not_unique = list()            
        for i in range(len(names_list)):
            if names_list[i] in names_to_color:
                not_unique.append(names_list[i])                    
            names_to_color[names_list[i]] = color_list[i]
        return (names_to_color, not_unique)

    def load_file(self):
        self.names = self.get_color_names()
        file_colors = list()
        file_names = list()
        filename = self.filename_entry.get()
        # ----------------------------------- 1) Reading file
        try:
            (file_colors, file_names) = self.get_names_and_colors(filename)
        except:
            tkMessageBox.showinfo("Error in opening a file", "File '%s' cannot be opened, check file name correctness!" % filename, parent = self.parent)
            return
        # ----------------------------------- 2) Checking colors        
        for i in range(len(file_colors)):
            try:
                (r, g, b) = self.parent.winfo_rgb(file_colors[i])
            except:
                tkMessageBox.showinfo("Invalid color", "Color in a string %i '%s' is not a valid hex color representation!" % (i, file_colors[i]), parent = self.parent)
                return

        if self.file_mode.get() == "Replace":
            self.colors = file_colors
            self.names = file_names            
        if self.file_mode.get() == "Append":
            (file_names_to_color, file_not_unique) = self.get_names_to_colors(file_colors, file_names)
            if len(file_not_unique) != 0:
               tkMessageBox.showinfo("Error in loading file in append mode", "File has the following names associated with the colors which are not unique: %s." % ", ".join(file_not_unique), parent = self.parent)
               return
            else:
                for i in range(len(self.names)): 
                    if self.names[i] in file_names_to_color: # Color for this name was already specified
                        self.colors[i] = file_names_to_color[self.names[i]]
        self.fill_color_panel()              
                             
    def save_file(self):
        self.names = self.get_color_names()
        filename = self.filename_entry.get()
        colors_to_write = list()
        names_to_write = list()
        if (self.file_mode.get() == "Replace") or (not os.path.isfile(filename)): # File does not exist, appending is impossible
            colors_to_write = self.colors
            names_to_write = self.names
        if self.file_mode.get() == "Append":                       
            (names_to_color, not_unique) = self.get_names_to_colors(self.colors, self.names)
            if len(not_unique) != 0:
                tkMessageBox.showinfo("Error in appending to file", "Appending is impossible; the following names associated with the colors in current scheme are not unique: %s." % ", ".join(not_unique), parent = self.parent)
                return
            
            (file_colors, file_names) = self.get_names_and_colors(filename)
            (file_names_to_color, file_not_unique) = self.get_names_to_colors(file_colors, file_names)
            if len(file_not_unique) != 0:
                tkMessageBox.showinfo("Error in appending to file", "Appending is impossible; the following names associated with the colors in the file are not unique: %s." % ", ".join(file_not_unique), parent = self.parent)
                return

            for name in file_names: # In this case <file_names> should be the same as <file_names_to_color.keys()>                 
                if name in names_to_color: # Replacing file value with current value
                    colors_to_write.append(names_to_color[name])
                    names_to_color.pop(name)
                else:                      # Adding original file value  
                    colors_to_write.append(file_names_to_color[name])
                names_to_write.append(name)
            for name in names_to_color.keys(): # Appending
                colors_to_write.append(names_to_color[name])
                names_to_write.append(name)            

        scheme_file = open(self.filename_entry.get(), "w")
        for i in range(len(colors_to_write)):
            scheme_file.write("%s\t%s\n" % (colors_to_write[i], names_to_write[i]))
        scheme_file.close()

class ColorWind (tkinter.Toplevel):
    """
    This class is a <tkinter.Toplevel> which incapsulates <ColorFrame> frame.
    Method <self.get_colors> is used to obtain current colors from the frame

    !IMPORTANT! Method <self.export_colors> is activated when the button is pressed:
                it will execute <self.host.import_colors> method, which should be created
                by the user in its host object.
                This method is excepted to obtain the following arguments:
                1) List of colors in hex representation;
                2) Type of data (useful if several different color wheels are to be used);
                3) List of color names.

                Method of a host <self.host.palette_is_saved> will be activated if a user
                closes window. This method should obtain the same parameters as given above
                and return a boolean value, telling if current window can be safely closed or not
    """
    def __init__(self, host, data_type, window_title, colors, color_names, button_color, label_color, icon = None, color_filename = None):
        tkinter.Toplevel.__init__(self)
        self.host = host
        self.data_type = data_type
        self.title(window_title)       
        self.button_color = button_color
        self.main_frame = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)        
        if icon != None:
            self.iconbitmap(icon)
        self.create_UI(colors, label_color, color_names, color_filename)
    
    def create_UI(self, colors, label_color, color_names, color_filename):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        self.main_frame = ColorFrame(self, "#D9D9D9", colors, color_names, label_color, color_filename)
        self.main_frame.grid(row = 0, column = 0, sticky = "NSEW")
        self.main_frame.update_idletasks() # This could be done because the frame should be drawn and arranged

        load_colors = tkinter.Button(self.main_frame.file_panel, text = "Save current color scheme", command = self.export_colors, foreground = "#FFFFFF", background = self.button_color)
        load_colors.grid(row = 0, column = 6, padx = 1, pady = 1, sticky = "NSE")
         
        w = self.winfo_width()
        h = 500
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - w)/2
        y = (screen_h - h)/2
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.resizable(0,0)
        self.wm_attributes("-topmost", 1)

    def export_colors(self):
        self.host.import_colors(self.get_colors(), self.data_type, self.main_frame.get_color_names())

    def get_colors(self):
        return self.main_frame.colors

    def on_close(self):
        data_saved = self.host.palette_is_saved(self.get_colors(), self.data_type, self.main_frame.get_color_names())
        if data_saved == False:            
            answer = tkMessageBox.askyesnocancel("Save data before closing?", "You have unsaved changes; do you want to save them?", icon = "question", parent = self)
            if answer == None: # Cancel, do nothing
                return
            if answer == True:
                self.export_colors()
        tkinter.Toplevel.destroy(self)

if __name__ == "__main__":    
    root = tkinter.Tk()
    root.title("Test window for the ColorFrame ")
    root.grid_rowconfigure(0, weight = 1)
    root.grid_columnconfigure(0, weight = 1)

    colors = ["#FF0000", "#00FF00", "#0000FF"]
    names = ["red", "green", "blue"]
    main_window = ColorFrame(root, "#D9D9D9", colors, names, "#000000")
    main_window.grid(row = 0, column = 0, sticky = "NSEW")
    main_window.update_idletasks() # This could be done because the frame should be drawn and arranged

    w = root.winfo_width()
    h = root.winfo_height()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - w)/2
    y = (screen_h - h)/2
    root.geometry("%dx%d+%d+%d" % (w, h, x, y))
    root.resizable(0,0)
    root.mainloop()