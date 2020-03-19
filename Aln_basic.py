# -*- coding: utf-8 -*-
import os, sys, platform
import codecs
import Tkinter as tkinter
import tkMessageBox, tkFont

def write_widget_into_file(text_widget, filename, ask_if_exists = False, use_codecs = False):
    """
    Method returns True if the were was written correctly and False if some errors occured
    """
    curr_text = text_widget.get(1.0, tkinter.END)
    if len(curr_text.strip()) == 0: # Text is empty
        return False
    if filename == "": # No filename provided, save was canceled
        return False

    strings = curr_text.split("\n")
    if os.path.isfile(filename) and ask_if_exists:
        answer = tkMessageBox.askyesno("File exists", "File %s exists, are you sure you want to re-write it?" % filename)
        if answer != True:
            return False
    if use_codecs:
        output_file = codecs.open(filename, "w", encoding = "utf_8")
    else:
        output_file = open(filename, "w")
    for string in strings:
        output_file.write("%s\n" % string)
    output_file.close()
    return True

def read_widget_from_file(text_widget, filename, use_codecs = False):
    text_widget.delete(1.0, tkinter.END)
    if use_codecs:
        input_file = codecs.open(filename, "r", encoding = "utf_8")
    else:
        input_file = open(filename, "r")
    for string in input_file:        
        text_widget.insert(tkinter.END, string)
    input_file.close()

    stripped_text = text_widget.get(1.0, tkinter.END).strip()
    text_widget.delete(1.0, tkinter.END)
    text_widget.insert(tkinter.END, stripped_text)

def read_domain_info_file(dom_filename):
    dom_dict = dict()
    dom_file = open(dom_filename)
    for string in dom_file:
        string = string.strip()
        if len(string) == 0:
            continue
        fields = string.split("\t")
        dom_dict[fields[0]] = (fields[1], fields[2])
    dom_file.close()
    return dom_dict

def get_valid_alignment_range(seqs, presence_threshold):
    """
    Method returns <start> and <end> in the sequence alignment <seqs> coordinates,
    where at least <presence_threshold> % of sequences contain letters.
    """
    start = 0
    i = start
    while i < len(seqs[0].sequence):
        j = 0
        presence = 0
        while j < len(seqs):
            curr_letter = seqs[j].sequence[i]
            if curr_letter != "-":
                presence += 1
            j += 1
        presence = 100*float(presence)/float(len(seqs))
        if presence > presence_threshold:
            start = i
            break
        i += 1

    end = len(seqs[0].sequence) - 1
    i = end
    while i >= 0:
        j = 0
        presence = 0
        while j < len(seqs):
            curr_letter = seqs[j].sequence[i]
            if curr_letter != "-":
                presence += 1
            j += 1
        presence = 100*float(presence)/len(seqs)
        if presence > presence_threshold:
            end = i + 1
            break
        i -= 1
    return (start, end)

def read_fasta_from_strings(strings, remove_gaps = False):
    seqs = list()
    import udav_base
    for string in strings:
        string = string.strip()
        if len(string) == 0:
            continue
        if string[0] == ">":             
            seqs.append(udav_base.Sequence(string.strip(">"), ""))
        else:
            if remove_gaps:
                string = string.replace("-", "")
            seqs[-1].sequence += string
    del udav_base    
    return seqs

def export_MEGA_format(text_widget, filename, title):
    strings = text_widget.get(1.0, tkinter.END).split("\n")    
    seqs = read_fasta_from_strings(strings)
    if len(seqs) == 0:
        return
    if filename == "": # No filename provided, save was canceled
        return
  
    mega_file = open(filename, "w")
    mega_file.write("#Mega\n")
    mega_file.write("!Title %s;\n\n" % title)    
    step = 80
    aln_size = len(seqs[0].sequence)
    for s in seqs:
        begin = 0
        end = begin + step
        s.name = s.name.replace("#", "_")
        mega_file.write("#%s\n" % s.name)
        while end < aln_size:
            mega_file.write("%s\n" % s.sequence[begin:end])
            begin = end
            end = begin + step
        if end >= aln_size:        
            mega_file.write("%s\n" % s.sequence[begin:])
    mega_file.close()

class TextFrameWithLabelAndButton(tkinter.Frame):
    def __init__(self, parent, padding, background, text_color, label_text, button_text):
        tkinter.Frame.__init__(self, parent)
        self.p = padding
        self.back = background
        self.text_color = text_color
        self.panel = None
        self.label = None
        self.text_widget = None       
        self.button = None
        self.font_size = 8
        self.normal_font = None   # tkFont for the text
        self.bold_font = None     # tkFont for the "bold" tag
        self.italic_font = None   # tkFont for the "italic" tag
        self.create_UI(label_text, button_text)

    def create_UI(self, label_text, button_text):
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        self.panel = tkinter.Frame(self)
        self.panel.grid_columnconfigure(0, weight = 1)
        self.panel.grid_rowconfigure(0, weight = 1)
        self.label = tkinter.Label(self.panel, text = label_text)
        self.label.grid(row = 0, column = 0, sticky = "NSW", padx = self.p, pady = self.p)        
        if (self.back == None) or (self.text_color == None):
            self.button = tkinter.Button(self.panel, state = tkinter.NORMAL, text = button_text, command = self.button_action)
        else: 
            self.button = tkinter.Button(self.panel, state = tkinter.NORMAL, text = button_text, background = self.back, foreground = self.text_color, command = self.button_action)
        self.button.grid(row = 0, column = 1, sticky = "NSW", padx = self.p, pady = self.p)
        self.panel.grid(row = 0, column = 0, columnspan = 2, sticky = "NSEW")
        text_scr_y = tkinter.Scrollbar(self, orient = tkinter.VERTICAL)
        text_scr_y.grid(row = 1, column = 1, sticky = "NSEW")
        text_scr_x = tkinter.Scrollbar(self, orient = tkinter.HORIZONTAL)
        text_scr_x.grid(row = 2, column = 0, sticky = "NSEW")
        self.normal_font = tkFont.Font(self.text_widget, ("Courier New", self.font_size))
        self.text_widget = tkinter.Text(self, state = tkinter.NORMAL, font = self.normal_font,
                                        yscrollcommand = text_scr_y.set, xscrollcommand = text_scr_x.set, wrap = tkinter.NONE)
        self.text_widget.grid(row = 1, column = 0, sticky = "NSEW")
        text_scr_y.configure(command = self.text_widget.yview)
        text_scr_x.configure(command = self.text_widget.xview)
        self.bold_font = tkFont.Font(self.text_widget, self.text_widget.cget("font"))
        self.bold_font.configure(weight = "bold")
        self.text_widget.tag_configure("bold", font = self.bold_font)
        self.italic_font = tkFont.Font(self.text_widget, self.text_widget.cget("font"))
        self.italic_font.configure(slant = "italic")
        self.text_widget.tag_configure("italic", font = self.italic_font)
        self.text_widget.tag_configure("blocks", font = self.bold_font, foreground = "#0000FF")

        if platform.system() == "Linux":
            self.text_widget.bind("<Control-Button-4>", self.change_font) 
            self.text_widget.bind("<Control-Button-5>", self.change_font)
        else: 
            self.text_widget.bind("<Control-MouseWheel>", self.change_font) 

    def change_font(self, event):
        change = 0
        if platform.system() == "Linux":
            if event.num == 4: # Scroll up
                change = 1
            if event.num == 5: # Scroll down
                change = -1
        else:
            if event.delta > 0: # Scroll up
                change = 1
            else:
                change = -1
        if (change < 0) and (self.font_size == 1):
            return

        self.font_size += change
        self.normal_font.configure(size = self.font_size)
        self.bold_font.configure(size = self.font_size)
        self.italic_font.configure(size = self.font_size)

    def text_is_empty(self):
        curr_text = self.text_widget.get(1.0, tkinter.END).strip()
        if len(curr_text) == 0: # No text is in current frame's text widget
            return True
        else:
            return False

    def button_action(self):
        print ("[..WARNING..] Unassigned action with the button!")

    def get_strings(self):
        return self.text_widget.get(1.0, tkinter.END).strip().split("\n")

    def count_fasta(self):
        seqs = read_fasta_from_strings(self.get_strings())
        n = len(seqs)
        self.add_label_data("%i sequences" % n)
        return n

    def add_label_data(self, text):
        if text != "":
            curr_label_text = self.label.cget("text").split(" (", 1)[0].strip(":")        
            self.label.configure(text = "%s (%s):" % (curr_label_text, text))

    def count_seq_length(self):        
        result = None
        lengths = dict()        
        seqs = read_fasta_from_strings(self.get_strings())
        for s in seqs:           
            lengths[len(s.sequence)] = True
        if len(lengths.keys()) == 0: # No sequences found
           result = ""
        elif(len(lengths.keys())) == 1: # All sequences have the same length
           result = lengths.keys()[0]
        else:
           result = "different lengths"
        self.add_label_data(result)   
        return result

def is_negative_float(string, name):
    result = False
    try:
        f = float(string) # Checking floatable
        (-f) ** 0.5 # Checking negative number
        result = True
    except TypeError:
        print ("Option %s is not a floating point value; it will be ignored!" % name)
    except ValueError:
        print ("Option %s is not negative value; it will be ignored!" % name)
    return result

def compare_sets(set1, set2):
    the_same = True
    if len(set1) != len(set2):
        the_same = False    
    else:
        for i in range(len(set1)):
            if set1[i] != set2[i]:
                the_same = False
    return the_same

"""
        aa_sets_to_colors = {"KHR"   : ("#000000", "#0000FF"),
                             "ED"    : ("#000000", "#FF0000"),
                             "QN"    : ("#000000", "#FF6600"),
                             "STC"   : ("#000000", "#FFFF00"),
                             "FYW"   : ("#000000", "#800080")}
        aa_to_colors = dict()
        for aa_set in aa_sets_to_colors.keys():
            for aa in aa_set:
                aa_to_colors[aa] = aa_sets_to_colors[aa_set]

        aminoacids = aa_to_colors.keys()
        for i in range(len(aminoacids)):
            aa = aminoacids[i]
            print ("Working with aminoacid '%s' (%i out of %i)" % (aa, i, len(aminoacids)))
            start = "1.0"
            while True:
                hit_position = self.purify_tab.text_widget.search(aa, start, stopindex = tkinter.END)
                if not hit_position:
                    break
                end_position = '%s+%dc' % (hit_position, 1)
                column = int(hit_position.split(".")[1].split("+")[0])                
                if column > max_name_length: # Not coloring sequence names
                    self.purify_tab.text_widget.tag_add(aa, hit_position, end_position)                
                start = end_position            
            self.purify_tab.text_widget.tag_config(aa, foreground = aa_to_colors[aa][0], background = aa_to_colors[aa][1])
""" 