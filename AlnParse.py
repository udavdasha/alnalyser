# -*- coding: utf-8 -*-
import os, platform
import Tkinter as tkinter
import tkMessageBox, tkFileDialog
import Aln_basic, Settings
import subprocess

class AlnParse(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.host = host
        self.p = self.host.p
        self.fixed = None
        self.pure = None
        self.run_hmmsearch_Pfam = None # Button to run HMM search with the Pfam database
        self.run_hmmsearch_COG = None  # Button to run HMM search with the COG database
        self.run_TMHMM = None          # Button to run TMHMM program (only works under Linux)
        self.begin_entry = None
        self.step_entry = None
        self.nsteps_entry = None        
        self.length_histo = None       # Button to print to log histogram of protein lengths
        self.blocks = None
        self.IDs = None
        self.ID_save_mode = None       # String variable with the mode of ID saving
        
        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")
        
        self.fixed = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "'Fixed' alignment:", "Save to file")
        self.fixed.button.configure(command = self.save_fixed)
        sort_by_tree = tkinter.Button(self.fixed.panel, background = self.host.header, foreground = "#FFFFFF", text = "Sort by tree", command = self.sort_by_tree)
        sort_by_tree.grid(row = 0, column = 2, sticky = "NSW", padx = self.p, pady = self.p)  
        central_panel.add(self.fixed)

        self.pure = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None,  
                               "'Pure names':", "Save to file")
        self.pure.button.configure(command = self.save_pure)
        self.run_hmmsearch_Pfam = tkinter.Button(self.pure.panel, state = tkinter.DISABLED, text = "HMM search (Pfam)", command = self.hmmsearch_Pfam)
        self.run_hmmsearch_Pfam.grid(row = 0, column = 2, sticky = "NSW", padx = self.p, pady = self.p)  
        self.run_hmmsearch_COG = tkinter.Button(self.pure.panel, state = tkinter.DISABLED, text = "HMM search (COG)", command = self.hmmsearch_COG)
        self.run_hmmsearch_COG.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)  
        self.run_TMHMM = tkinter.Button(self.pure.panel, state = tkinter.DISABLED, text = "TMHMM", command = self.TMHMM)
        self.run_TMHMM.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)  

        tkinter.Label(self.pure.panel, text = "Enter begin, step and nsteps:").grid(row = 1, column = 0, sticky = "NSW")
        self.begin_entry = tkinter.Entry(self.pure.panel, width = 8)
        self.begin_entry.grid(row = 1, column = 1, sticky = "NSW", padx = self.p, pady = self.p)
        self.begin_entry.insert(tkinter.END, 200)
        self.step_entry = tkinter.Entry(self.pure.panel, width = 8)
        self.step_entry.grid(row = 1, column = 2, sticky = "NSW", padx = self.p, pady = self.p)
        self.step_entry.insert(tkinter.END, 50)
        self.nsteps_entry = tkinter.Entry(self.pure.panel, width = 8)
        self.nsteps_entry.grid(row = 1, column = 3, sticky = "NSW", padx = self.p, pady = self.p)
        self.nsteps_entry.insert(tkinter.END, 10)
        self.length_histo = tkinter.Button(self.pure.panel, text = "To log", state = tkinter.DISABLED, command = self.histo_to_log)
        self.length_histo.grid(row = 1, column = 4, sticky = "NSW", padx = self.p, pady = self.p)
        central_panel.add(self.pure)

        self.blocks = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "Blocks regions:", "Save to file")
        self.blocks.button.configure(command = self.save_blocks)
        central_panel.add(self.blocks)  

        self.IDs = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "List of IDs:", "Save to file")
        self.IDs.button.configure(command = self.save_IDs)
        self.ID_save_mode = tkinter.StringVar()
        self.ID_save_mode.set("No change")
        ID_save_mode = tkinter.OptionMenu(self.IDs.panel, self.ID_save_mode, "No change", "  -> gi  ", "fix gi-gi", "fix & ->") 
        ID_save_mode.grid(row = 0, column = 2, sticky = "NW", padx = self.p, pady = self.p)         
        try: #FIX: version 1.0.0 (if no assignment between gi and id/locus was given, conversion options are disabled)
            curr_table = self.host.settings.table_filename
        except AttributeError:
            ID_save_mode.configure(state = tkinter.DISABLED)
        
        central_panel.add(self.IDs)
        self.update_idletasks()
        central_panel.sash_place(0, 300, 1)
        central_panel.sash_place(1, 1100, 1)
        central_panel.sash_place(2, 1500, 1)

    def sort_by_tree(self):
        tree_filename = tkFileDialog.askopenfilename(initialdir = self.host.settings.work_dir, filetypes = (("Inkscape vector file", "*.svg"), ))
        if tree_filename == "": # Cancel
            return
        old_order_seqs = Aln_basic.read_fasta_from_strings(self.fixed.get_strings())

        sort_and_color_path = os.path.join(self.host.settings.script_dir, "sort_and_color.py")
        fixed_filename = os.path.join(self.host.settings.work_dir, "%s.fixed" % self.host.temp_name)
        Aln_basic.write_widget_into_file(self.fixed.text_widget, fixed_filename)

        if self.host.verbose.get():
            os.system("%s -i %s -w %s -o %s -t %s" % (sort_and_color_path, os.path.basename(fixed_filename), self.host.settings.work_dir, 
                                                      self.host.temp_name, tree_filename))
        else:
            os.system("%s -i %s -w %s -o %s -t %s 1> nul 2> nul" % (sort_and_color_path, os.path.basename(fixed_filename), 
                                                                    self.host.settings.work_dir, self.host.temp_name, tree_filename))

        temp_sorted_filename = os.path.join(self.host.settings.work_dir, "%s.tree_sorted" % self.host.temp_name)
        Aln_basic.read_widget_from_file(self.fixed.text_widget, temp_sorted_filename)
                
        self.IDs.text_widget.delete(1.0, tkinter.END)
        new_order_seqs = Aln_basic.read_fasta_from_strings(self.fixed.get_strings())
        new_ids = ""
        for s in new_order_seqs:
            new_ids += "%s\n" % s.ID            
        self.IDs.text_widget.insert(tkinter.END, new_ids)

        print ("    Alignment was sorted according to the %s tree file!" % tree_filename)
        self.host.log_tab.write_to_log("Alignment was sorted according to the tree file:\n%s" % tree_filename, True)
        if len(new_order_seqs) != len(old_order_seqs):
            print ("    Number of sequences reduced from %i to %i! Possibly IDs in the tree file was interpreted badly" % (len(old_order_seqs), len(new_order_seqs)))
            self.host.set_status("Number of sequences reduced from %i to %i!" % (len(old_order_seqs), len(new_order_seqs)))
        
    def save_fixed(self, ask_filename = True):
        name_prefix = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), self.host.get_project_name())
        if ask_filename:
            name_prefix = tkFileDialog.asksaveasfilename(filetypes = (("Prefix for fixed (fasta) and MEGA", "*.*"), ))
        fixed_filename = name_prefix + ".fixed"
        mega_filename = name_prefix + "_fixed.meg"
        Aln_basic.write_widget_into_file(self.fixed.text_widget, fixed_filename, ask_filename)
        Aln_basic.export_MEGA_format(self.fixed.text_widget, mega_filename, os.path.basename(fixed_filename))

    def save_pure(self, ask_filename = True):
        pure_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.pure" % self.host.get_project_name())
        if ask_filename:
            pure_filename = tkFileDialog.asksaveasfilename(filetypes = (("Non-aligned sequences with pure names (fasta)", "*.pure"), ("All", "*.*")))
        Aln_basic.write_widget_into_file(self.pure.text_widget, pure_filename, ask_filename)

    def save_blocks(self, ask_filename = True):
        name_prefix = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), self.host.get_project_name())
        if ask_filename:
            name_prefix = tkFileDialog.asksaveasfilename(filetypes = (("Prefix for blocks and MEGA files", "*.*"),))
        blocks_filename = name_prefix + ".blocks_regions"
        mega_filename = name_prefix + "_blocks.meg"
        Aln_basic.write_widget_into_file(self.blocks.text_widget, blocks_filename, ask_filename)
        Aln_basic.export_MEGA_format(self.blocks.text_widget, mega_filename, os.path.basename(blocks_filename))

    def save_IDs(self, ask_filename = True):
        ids_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.ids" % self.host.get_project_name())
        if ask_filename:
            ids_filename = tkFileDialog.asksaveasfilename(filetypes = (("List of protein IDs", "*.ids"), ("All", "*.*")))       

        curr_ID_save_mode = self.ID_save_mode.get()
        curr_text = self.IDs.text_widget.get(1.0, tkinter.END).strip()
        if curr_ID_save_mode != "No change":
            print ("    IDs will be converted before writing!")
            to_gi = False
            fix = False
            if (curr_ID_save_mode == "  -> gi  ") or (curr_ID_save_mode == "fix & ->"):
                to_gi = True
            if (curr_ID_save_mode == "fix gi-gi") or (curr_ID_save_mode == "fix & ->"):
                fix = True
            
            locus_to_gi = dict()
            id_to_gi = dict()
            if to_gi:
                self.host.set_status("Working")
                import udav_soft
                try: #FIX: (version 1.0) if <settings.table_filename> is not given, nothing bad will happen
                    (locus_to_gi, id_to_gi, a, b) = udav_soft.read_protein_table_info(self.host.settings.table_filename, True)
                except AttributeError: 
                    print ("    [ERROR]: Table with assignment of GI to other types of IDs was not given to the script!")
                    print ("             Please check 'table_filename' option in the <settings.ini> file")                   
                except OSError:
                    print ("    [ERROR]: Table with assignment of GI to other types of IDs '%s' not found!" % self.host.settings.table_filename) 
                del udav_soft             
                self.host.set_status("Ready")
                
            strings = curr_text.split("\n")
            i = 0
            while i < len(strings):
                curr_id = strings[i].strip()
                if fix:
                    curr_id = curr_id.split("-", 1)[0]
                new_id = curr_id
                if to_gi:
                    if curr_id in locus_to_gi:
                        new_id = locus_to_gi[curr_id]                 
                    if curr_id in id_to_gi:
                        new_id = id_to_gi[curr_id]
                strings[i] = new_id
                i += 1
            self.IDs.text_widget.delete(1.0, tkinter.END)
            self.IDs.text_widget.insert(tkinter.END, "\n".join(strings).strip())

        Aln_basic.write_widget_into_file(self.IDs.text_widget, ids_filename, ask_filename)
        self.IDs.text_widget.delete(1.0, tkinter.END)     
        self.IDs.text_widget.insert(tkinter.END, curr_text)            

    def enable_pure_analysis(self):
        print ("    Enabling analysis buttons...")
        try:
           a = self.host.settings.pfam_profiles
           self.run_hmmsearch_Pfam.configure(state = tkinter.NORMAL)
        except AttributeError:
           print ("    Pfam profile database is not set; Pfam database analysis is not possible")

        try:
           a = self.host.settings.cog_profiles
           self.run_hmmsearch_COG.configure(state = tkinter.NORMAL)
        except AttributeError:
           print ("    COG profile database is not set; Pfam database analysis is not possible")

        try:
           a = self.host.settings.tmhmm_dir
           if platform.system() == "Linux":
               self.run_TMHMM.configure(state = tkinter.NORMAL)
           else:
               print ("    Operation system is not Linux and thus TMHMM cannot be executed!")
        except AttributeError:
           print ("    Path to TMHMM is not set; transmembrane helix search is not possible")

        self.length_histo.configure(state = tkinter.NORMAL)
        print ("    [..DONE..]")

    def disable_pure_analysis(self):
        self.run_hmmsearch_Pfam.configure(state = tkinter.DISABLED)
        self.run_hmmsearch_COG.configure(state = tkinter.DISABLED)
        self.run_TMHMM.configure(state = tkinter.DISABLED)

    def hmmsearch_Pfam(self):
        self.hmmsearch_profile_database(self.host.settings.pfam_profiles, "Pfam")
       
    def hmmsearch_COG(self):
        self.hmmsearch_profile_database(self.host.settings.cog_profiles, "COG")

    def hmmsearch_profile_database(self, profile_database, database_type):
        curr_project_dir = os.path.join(self.host.settings.work_dir, self.host.get_project_name())
        if not os.path.isdir(curr_project_dir):
            dir_answer = tkMessageBox.askyesno("Create directory and start analysis?", "This type of analysis cannot be done if the project directory is not created. Do you want to create the following directory and continue?\n%s" % curr_project_dir)
            if dir_answer != True:
               return
            print ("    Creating project directory de novo: '%s'" % curr_project_dir)
            os.mkdir(curr_project_dir)

        (hmmscan_name, hmmscan_path) = Settings.get_program_name(self.host.settings.hmmer_dir, "hmmscan")
        pure_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.pure" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.pure.text_widget, pure_filename)
        result_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.%s_out" % (self.host.get_project_name(), database_type))
        table_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.%s_table" % (self.host.get_project_name(), database_type))
        args = [hmmscan_path, "--domtblout", table_filename, "-o", result_filename, profile_database, pure_filename]
        subprocess.Popen(args, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
        self.host.pending_filenames.append(result_filename)
        self.host.pending_filenames.append(table_filename)
        self.host.enable_check_button()

    def TMHMM(self):
        print ("Currently this cannot be done; please use TMHMM web server instead!")

    def check_numbers(self):
        """
        Method will modify labels according to the number of entries found inside
        """
        self.fixed.count_seq_length()
        self.pure.count_fasta()
        self.blocks.count_seq_length()

    def clear(self):
        self.fixed.text_widget.delete(1.0, tkinter.END)
        self.pure.text_widget.delete(1.0, tkinter.END)
        self.blocks.text_widget.delete(1.0, tkinter.END)
        self.IDs.text_widget.delete(1.0, tkinter.END)       

    def histo_to_log(self):
        values = list()
        seqs = Aln_basic.read_fasta_from_strings(self.pure.get_strings())
        for s in seqs:            
            values.append(len(s.sequence))
        info_string = "Length of proteins in the alignment"        
        begin = 0
        step = 0
        nsteps = 0
        try:
            begin = int(self.begin_entry.get())
            step = int(self.step_entry.get())
            nsteps = int(self.nsteps_entry.get())
        except ValueError:
            print ("    [..WARNING..] Enter proper begin, step and number of steps before printing!")
            return
        self.host.log_tab.write_histogram(values, info_string, begin, step, nsteps)