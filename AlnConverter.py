# -*- coding: utf-8 -*-
import os, re
import Tkinter as tkinter
import Aln_basic

class AlnConverter(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.host = host
        self.p = self.host.p
        self.input_frame = None
        self.input_format = None
        self.output_format = None
        self.output_frame = None
        self.replace_spaces = None  # Replace spaces in the organism name?
        self.id_mode = None         # Specify if GI or protein_ID is used as an identifier at the end
        self.unalign = None         # If alignment should be removed

        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")
        self.input_frame = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF", 
                           "Insert FASTA-format sequences:", "=> Convert =>")
        self.input_frame.button.configure(command = self.convert)
        tkinter.Label(self.input_frame.panel, text = "Input format:").grid(row = 0, column = 2, sticky = "NSW")
        self.input_format = tkinter.StringVar()
        self.input_format.set("Basic")
        #input_format = tkinter.OptionMenu(self.input_frame.panel, self.input_format, "URef", "NCBI", "NCBI_2016", "Uniprot", "PDB", "COGcollator", "Basic", "COG", "OldRef", "My_Ref", "My", "Olesya", "German") 
        input_format = tkinter.OptionMenu(self.input_frame.panel, self.input_format, "Basic", "NCBI", "NCBI_2016-", "Uniprot", "PDB", "COGcollator", "URef", "My")
        input_format.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)      
        help_button = tkinter.Button(self.input_frame.panel, state = tkinter.DISABLED, text = "Format help", command = self.show_help)
        help_button.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)   
        central_panel.add(self.input_frame)

        self.output_frame = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF", 
                           "Your result will be shown here:", "")
        self.output_frame.button.grid_forget()
        tkinter.Label(self.output_frame.panel, text = "Output format:").grid(row = 0, column = 1, sticky = "NSW")   

        self.output_format = tkinter.StringVar()
        self.output_format.set("My")
        output_format = tkinter.OptionMenu(self.output_frame.panel, self.output_format, "My", "Basic", "NCBI", "ID", "Table", "Same but fixed") 
        output_format.grid(row = 0, column = 2, sticky = "NSW", padx = self.p, pady = self.p)
        tkinter.Label(self.output_frame.panel, text = "Group label (optional):").grid(row = 0, column = 3, sticky = "NSW")  
        self.output_class = tkinter.Entry(self.output_frame.panel, width = 15)
        self.output_class.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)

        self.replace_spaces = tkinter.BooleanVar()
        self.replace_spaces.set(True)
        c = tkinter.Checkbutton(self.output_frame.panel, text = "Replace spaces", variable = self.replace_spaces)
        c.grid(row = 0, column = 5, sticky ="NSW", padx = self.p, pady = self.p)
        self.id_mode = tkinter.StringVar()
        self.id_mode.set("GI")
        radio = tkinter.Radiobutton(self.output_frame.panel, text = "GI", variable = self.id_mode, value = "GI")
        radio.grid(row = 0, column = 6, sticky = "NSW", padx = self.p, pady = self.p)
        radio = tkinter.Radiobutton(self.output_frame.panel, text = "protein_id", variable = self.id_mode, value = "ID")
        radio.grid(row = 0, column = 7, sticky = "NSW", padx = self.p, pady = self.p)
        radio = tkinter.Radiobutton(self.output_frame.panel, text = "locus", variable = self.id_mode, value = "locus")
        radio.grid(row = 0, column = 8, sticky = "NSW", padx = self.p, pady = self.p)
        self.unalign = tkinter.BooleanVar()
        self.unalign.set(False)
        c = tkinter.Checkbutton(self.output_frame.panel, text = "Unalign", variable = self.unalign)
        c.grid(row = 0, column = 9, sticky ="NSW", padx = self.p, pady = self.p)
        
        central_panel.add(self.output_frame)

    def convert(self):        
        self.output_frame.text_widget.delete(1.0, tkinter.END)
        seqs = list()
        import udav_fasta      
        try: #------------------------------------ 1) Input
            for string in self.input_frame.get_strings():
                string = string.strip()
                if len(string) == 0:
                    continue
                if string[0] == ">":               
                    new_seq = udav_fasta.get_sequence_data(string, self.input_format.get()) 
                    seqs.append(new_seq)
                else:
                    seqs[-1].sequence += string 
            self.host.set_status("Successful convertion!", self.host.header)   
        except udav_fasta.FastaException:
            self.host.set_status("Wrong input fasta format, check that it matches your selecton!", "#FF0000")            
        del udav_fasta

        prot_type = self.output_class.get()
        if prot_type == "":
            prot_type = None
        for s in seqs: #-------------------------- 2) Output
            curr_seq_name = s.get_name_in_format(self.id_mode.get(), self.output_format.get(), self.replace_spaces.get(), prot_type)
            self.output_frame.text_widget.insert(tkinter.END, curr_seq_name)
            if self.output_format.get() != "Table":
                if self.unalign.get() == True:                    
                    s.sequence = s.sequence.replace("-", "")
                self.output_frame.text_widget.insert(tkinter.END, s.sequence + "\n\n")

            non_letter_match = re.search("[^A-Za-z\-]", s.sequence)
            if non_letter_match != None: # Non-letter or gap found
                print ("    [..WARNING..] Sequence with id %s contains non-letter char: '%s'" % (s.gi, non_letter_match.group(0)))

    def show_help(self):
        print ("Showing info!")
