# -*- coding: utf-8 -*-
import os, re
import Tkinter as tkinter
import Aln_basic

class AlnFilter(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.host = host
        self.p = self.host.p
        self.input_format = None
        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.input_frame = Aln_basic.TextFrameWithLabelAndButton(self, self.p, self.host.header, "#FFFFFF", 
                           "Insert sequences in FASTA format:", "Obtain taxonomy units")
        self.input_frame.grid(row = 0, column = 0, sticky = "NSEW", padx = self.p, pady = self.p)
        self.input_frame.button.configure(command = self.filter)
        tkinter.Label(self.input_frame.panel, text = "Input format:").grid(row = 0, column = 2, sticky = "NSW")
        self.input_format = tkinter.StringVar()
        self.input_format.set("My")
        input_format = tkinter.OptionMenu(self.input_frame.panel, self.input_format, "URef", "NCBI", "Uniprot", "PDB", "COGalyser", "Basic", "COG", "OldRef", "My_Ref", "My", "Olesya", "German") 
        input_format.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)      
        help_button = tkinter.Button(self.input_frame.panel, state = tkinter.DISABLED, text = "Format help", command = self.show_help)
        help_button.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)   

        self.configure_frame = 
