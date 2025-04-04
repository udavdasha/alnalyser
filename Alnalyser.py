#!/usr/bin/env python
"""
This is a main script of the <Alnalyser> program
@ Daria Dibrova aka udavdasha
"""
curr_version = "1.1.1"
import tkinter
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog
import tkinter.ttk as ttk
import sys, os, platform, re, random
import Settings, ColorFrame, Aln_basic, AlnInput, AlnParse, AlnPurify, AlnFeatures, AlnLog, AlnConverter

LOGO_FILENAME = "alnalyser.gif"
ICON_FILENAME = "alnalyser.ico"
INI_FILENAME = "settings.ini"
if platform.system() == "Linux":
    ICON_FILENAME = "@alnalyser.xbm"
if len(sys.argv) > 1: #settings filename was given as an argument
    INI_FILENAME = sys.argv[1]
      
class Alnalyser(tkinter.Frame):
    """
    Main window of the Alnalyser program
    """
    def __init__(self, parent, settings_filename, logo_filename, icon_filename):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)
        self.p = 5 # Padding for internal frames
        self.back = "#D9D9D9"
        self.header = "#37c871"
        self.icon_filename = icon_filename
        self.known_status = {"Ready"     : ("READY", self.header), 
                             "Working"   : ("PLEASE WAIT", "#FF0000"),
                             "Alignment" : ("ALIGNING, PLEASE WAIT", "#FF0000"),
                             "OK"        : ("Everything is OK!", self.header)}
        req_settings = ["script_dir", "muscle_dir", "hmmer_dir", "pfam_profiles", "cog_profiles", "work_dir", "tax_colors_filename", "table_filename"]
        random.seed()
        self.temp_name = "udav_temp_%i" % (random.random() * 1000)
        self.settings = Settings.read_settings_file(settings_filename, req_settings)
        self.check_settings() #FIX (version 1.0.1): existence of required settings is now checked
        sys.path.append(self.settings.script_dir)

        self.check_button = None         # Button for checking of pending results
        self.purify_button = None        # Button from purification
        self.parse_button = None         # Button for the parsing
        self.diagnostics_button = None   # Button for self-diagnostics
        self.status_label = None         # Label to show current program status
        self.project_title_widget = None # Entry for the project title (will be fixed upon input check)  
        self.project_title = None        # Project title
        self.verbose = None              # If information from the scripts which are running should be printed (1 or 0)
        self.tabs = None                 # ttk.Notebook widget
        self.input_tab = None            # Input pab
        self.parse_tab = None            # Parsing pab
        self.purify_tab = None           # Purification pab
        self.features_tab = None         # Features pab
        self.log_tab = None              # Tab for the project log (both auto- and user-generated)
        self.pending_filenames = list()  # List of names of files which should be created by other programs
        self.domain_colors = list()      # List of tuples (domain_name, color) used in the program
        self.domain_to_color = dict()    # Dictionary for the <self.domain_colors>
        self.domain_colors.append(("Enter domain/COG ID", "#FFFFFF"))
        self.domain_colors.append(("TMHMM", "#FF0000"))
        self.domain_to_color["TMHMM"] = "#FF0000"
        self.domain_info = None          # Treeview with the information about domains currently loaded into the feature tab
        self.gi_to_tax = None            # Dictionary of GIs to taxon
        self.tax_to_color = None         # Dictionary of taxa to colors       
          
        self.create_UI(logo_filename)

    def create_UI(self, logo_filename):
        self.grid_columnconfigure(1, weight = 1)
        self.grid_rowconfigure(2, weight = 1)

        logo_image = tkinter.PhotoImage(file = logo_filename)
        logo_image = logo_image.subsample(10, 10)
        self.logo = tkinter.Label(self, image = logo_image)
        self.logo.image = logo_image        
        self.logo.grid(row = 0, column = 0, sticky = "NSEW", padx = self.p, pady = self.p)

        top_panel = tkinter.Frame(self)
        top_panel.grid_columnconfigure (4, weight = 1)
        self.project_title_widget = tkinter.Entry(top_panel, width = 20, font = ("Courier New", 12, "bold"), background = self.header, foreground = "#FFFFFF")
        #self.project_title_widget.insert(tkinter.END, "EnterProjectName")
        self.project_title_widget.grid(row = 0, column = 0, sticky = "NSEW", padx = self.p, pady = self.p)
        tkinter.Button(top_panel, text = "Save project", command = self.save_project).grid(row = 0, column = 1, sticky = "NSEW", padx = self.p, pady = self.p)
        tkinter.Button(top_panel, text = "Load project", command = self.load_project).grid(row = 0, column = 2, sticky = "NSEW", padx = self.p, pady = self.p)
        tkinter.Button(top_panel, text = "Clear all", command = self.clear_all).grid(row = 0, column = 3, sticky = "NSEW", padx = self.p, pady = self.p)
        self.check_button = tkinter.Button(top_panel, text = "Check\npending\nresults", background = self.header, foreground = "#FFFFFF", font = "Arial 12 bold", command = self.check_pending)
        self.disable_check_button()
        self.check_button.grid(row = 1, column = 0, sticky = "NSEW", padx = self.p, pady = self.p)
        self.parse_button = tkinter.Button(top_panel, text = "(1)\nAlignment\nparsing", command = self.parse, state = tkinter.NORMAL)
        self.parse_button.grid(row = 1, column = 1, sticky = "NSEW", padx = self.p, pady = self.p)
        self.purify_button = tkinter.Button(top_panel, text = "(2)\nAlignment\npurification", command = self.purify, state = tkinter.NORMAL)
        self.purify_button.grid(row = 1, column = 2, sticky = "NSEW", padx = self.p, pady = self.p) 
        self.diagnostics_button = tkinter.Button(top_panel, text = "(3)\nWrite current\nstate to log", command = self.diagnostics, state = tkinter.NORMAL)
        self.diagnostics_button.grid(row = 1, column = 3, sticky = "NSEW", padx = self.p, pady = self.p)                      

        base_frame = tkinter.Frame(top_panel)
        base_frame.columnconfigure(0, weight = 1) 
        base_frame.rowconfigure(0, weight = 1)
        y_scrollbar = tkinter.Scrollbar(base_frame)
        y_scrollbar.grid(row = 0, column = 1, sticky = "NS")
        self.domain_info = ttk.Treeview(base_frame, columns = ("domain_id", "occurence", "domain_descr"), selectmode = "extended",
                                        yscrollcommand = y_scrollbar.set, height = 5)
        y_scrollbar.config(command = self.domain_info.yview)
        self.domain_info.grid(row = 0, column = 0, sticky = "NSEW")
        self.domain_info.column("domain_id", width = 50, anchor = "w")
        self.domain_info.heading("domain_id", text = "Domain ID")
        self.domain_info.column("occurence", width = 50, anchor = "w")
        self.domain_info.heading("occurence", text = "Occurence")    
        self.domain_info.column("domain_descr", width = 350, anchor = "w")    
        self.domain_info.heading("domain_descr", text = "Domain description")
        self.domain_info.bind("<Double-Button-1>", self.domain_info_LMB_click)
        self.domain_info.bind("<Double-Button-3>", self.domain_info_RMB_click)
        base_frame.grid(row = 0, column = 4, rowspan = 2, sticky = "NSEW", padx = self.p, pady = self.p)        

        rand_colors = tkinter.Button(top_panel, text = "Random\ncolors", command = self.set_random_colors)
        rand_colors.grid(row = 1, column = 5, sticky ="NSE", padx = self.p, pady = self.p)
        set_colors = tkinter.Button(top_panel, text = "Open\ndomain colors\npanel", command = self.open_color_frame)
        set_colors.grid(row = 1, column = 6, sticky ="NSE", padx = self.p, pady = self.p)

        self.verbose = tkinter.IntVar()
        self.verbose.set(1)
        c = tkinter.Checkbutton(top_panel, text = "Print external logs", variable = self.verbose)
        c.grid(row = 0, column = 5, sticky ="NSE", columnspan = 2, padx = self.p, pady = self.p)

        top_panel.grid(row = 0, column = 1, sticky = "NSEW")

        self.status_label = tkinter.Label(self, text = "", foreground = self.header, font = ("Courier New", 14, "bold"))
        self.set_status("Ready")
        self.status_label.grid(row = 1, column = 0, columnspan = 2, sticky = "NW", padx = self.p, pady = self.p)

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row = 2, column = 0, columnspan = 2, sticky = "NSEW", padx = self.p, pady = self.p)

        self.input_tab = AlnInput.AlnInput(self.tabs, self) 
        self.tabs.add(self.input_tab, text = "Input")
       
        self.parse_tab = AlnParse.AlnParse(self.tabs, self)
        self.tabs.add(self.parse_tab, text = "Parsing")

        self.purify_tab = AlnPurify.AlnPurify(self.tabs, self)
        self.tabs.add(self.purify_tab, text = "Purification")

        self.features_tab = AlnFeatures.AlnFeatures(self.tabs, self)
        self.tabs.add(self.features_tab, text = "Features")

        self.log_tab = AlnLog.AlnLog(self.tabs, self)
        self.tabs.add(self.log_tab, text = "Project log")

        self.converter_tab = AlnConverter.AlnConverter(self.tabs, self)
        self.tabs.add(self.converter_tab, text = "Format converter")

    def load_domain_info(self, domain_dict):
        for value in self.domain_info.get_children(""):
            self.domain_info.delete(value)

        for domain_id in self.domain_to_color.keys():
            self.domain_info.tag_configure(domain_id, background = self.domain_to_color[domain_id])

        domain_occurence = dict() # --------- 1) Calculating number of proteins in which each domain occur at least once
        prot_number = 0
        feature_strings = self.features_tab.features.get_strings()
        for string in feature_strings:
            string = string.strip()
            if len(string) == 0:
                continue
            prot_number += 1
            fields = string.split("\t")
            if len(fields) == 1: # No domains found for this proteins
                continue
            for f in fields[1:]:
                domain_id = f.split(" ", 1)[0].strip("[]")
                if not domain_id in domain_occurence:
                    domain_occurence[domain_id] = 0
                domain_occurence[domain_id] += 1
                                  # --------- 2) Adding information
        sorted_domains = list(domain_occurence.keys())
        sorted_domains.sort(key = lambda k: domain_occurence[k], reverse = True)
        for domain_id in sorted_domains:
            if domain_id == "TMHMM":
                continue  
            curr_domain = domain_dict[domain_id]
            percent_occurence = float(100*domain_occurence[domain_id])/prot_number
            curr_occurence = "%i (%.1f)" % (domain_occurence[domain_id], percent_occurence)
            curr_tag = "no_color"
            if domain_id in self.domain_to_color:
                curr_tag = domain_id 
            self.domain_info.insert("", "end", text = domain_id, values = (curr_domain[0], curr_occurence, curr_domain[1]),
                                    tags = (curr_tag, ))

    def domain_info_LMB_click(self, event):
        curr_id = event.widget.identify_row(event.y)
        try: #FIX: version 0.2.8 (heading clicks are considered)
            curr_domain_id = event.widget.item(curr_id)["text"]
            curr_domain_descr = event.widget.item(curr_id)["values"][2]
            data = "%s (%s)" % (curr_domain_id, curr_domain_descr)
            self.parent.clipboard_clear() 
            self.parent.clipboard_append(data)
        except IndexError:
            print ("Please double-click with LMB at the row, not heading, to get info copied into the clipboard!")

    def domain_info_RMB_click(self, event):
        curr_id = event.widget.identify_row(event.y)        
        try: #FIX: version 0.2.8 (heading clicks are considered)
            curr_domain_ac = event.widget.item(curr_id)["values"][0]
            self.parent.clipboard_clear() 
            self.parent.clipboard_append(curr_domain_ac)
        except IndexError:
            print ("Please double-click with RMB at the row, not heading, to get domain ID copied into the clipboard!")
       
    def parse(self):      
        aligned_filename = os.path.join(self.settings.work_dir, "%s.aln" % self.temp_name)
        Aln_basic.write_widget_into_file(self.input_tab.aln_input_frame.text_widget, aligned_filename)
        remove_seq_limits_path = os.path.join(self.settings.script_dir, "remove_seq_limits.py")

        self.set_status("Working")
        if self.verbose.get():
            os.system("%s -i %s -o %s -d -x" % (remove_seq_limits_path, aligned_filename, os.path.join(self.settings.work_dir, self.temp_name)))
        else:
            os.system("%s -i %s -o %s -d -x 1> nul 2> nul" % (remove_seq_limits_path, aligned_filename, os.path.join(self.settings.work_dir, self.temp_name)))
        self.set_status("Ready")

        try:
            os.remove(os.path.join(self.settings.work_dir, "%s.aln" % self.temp_name))
            os.remove(os.path.join(self.settings.work_dir, "%s.blocks" % self.temp_name))
            os.remove(os.path.join(self.settings.work_dir, "%s.motif" % self.temp_name))
            os.remove(os.path.join(self.settings.work_dir, "%s.motif_var" % self.temp_name))
            os.remove(os.path.join(self.settings.work_dir, "%s.orgs" % self.temp_name))
            os.remove(os.path.join(self.settings.work_dir, "%s.pure.correspond" % self.temp_name))
        except OSError:
            pass

        fixed_filename = os.path.join(self.settings.work_dir, "%s.fixed" % self.temp_name)
        Aln_basic.read_widget_from_file(self.parse_tab.fixed.text_widget, fixed_filename)
        os.remove(fixed_filename)

        pure_filename = os.path.join(self.settings.work_dir, "%s.pure" % self.temp_name)
        Aln_basic.read_widget_from_file(self.parse_tab.pure.text_widget, pure_filename)
        self.parse_tab.enable_pure_analysis()
        os.remove(pure_filename)

        ngphylogeny_filename = os.path.join(self.settings.work_dir, "%s.ngphylogeny" % self.temp_name)
        Aln_basic.read_widget_from_file(self.parse_tab.ngphylogeny.text_widget, ngphylogeny_filename)
        os.remove(ngphylogeny_filename)

        blocks_filename = os.path.join(self.settings.work_dir, "%s.blocks_regions" % self.temp_name)
        if os.path.isfile(blocks_filename):
            Aln_basic.read_widget_from_file(self.parse_tab.blocks.text_widget, blocks_filename)
            os.remove(blocks_filename)

        ids_filename = os.path.join(self.settings.work_dir, "%s.ids" % self.temp_name)
        Aln_basic.read_widget_from_file(self.parse_tab.IDs.text_widget, ids_filename)
        os.remove(ids_filename)

        self.parse_tab.check_numbers()

    def purify(self):
        #seqs = Aln_basic.read_fasta_from_strings(self.input_tab.aln_input_frame.get_strings())
        seqs = Aln_basic.read_fasta_from_strings(self.parse_tab.fixed.get_strings()) 
        if len(seqs) == 0:
            self.set_status("No alignment to purify!")
            return

        for value in self.purify_tab.actions.get_children(""):
            self.purify_tab.actions.delete(value)

        import udav_base
        self.set_status("Working")
        # --------------------------------------- 1) Calculating cut for mainly gappy parts of alignment
        max_name_length = 50
        separator = "  :  "
        presence_threshold = 50
        try:
            presence_threshold = int(self.purify_tab.presence_entry.get())
        except:
            print ("Using default presence threshold value = 50!")
            
        (valid_start, valid_end) = Aln_basic.get_valid_alignment_range(seqs, presence_threshold)
        self.purify_tab.alignment.add_label_data("showing a region [%i; %i]" % (valid_start + 1, valid_end))
        self.purify_tab.alignment.text_widget.delete(1.0, tkinter.END)
 
        # --------------------------------------- 2) Printing alignment into the text widget tab
        self.set_status("Printing alignment", "#FF0000")
        seqs_cut = list() # List of sequences with the mainly gappy parts of alignment cut
        id_to_org_and_seq = dict() # Hash of protein ids to a tuple of (0) their organism name and (1) cut sequences
        id_list = list() # List of protein ids in order of their occurence      
        for i in range(len(seqs)):            
            # Printing to the widget
            fit_name = seqs[i].name[0:max_name_length]
            if len(fit_name) < max_name_length:
                fit_name += (max_name_length - len(fit_name)) * " "         
            seq_part = seqs[i].sequence[valid_start:valid_end]
            seqs_cut.append(udav_base.Sequence(seqs[i].name, seq_part))
            string = fit_name + ("%s%s" % (separator, seq_part))
            self.purify_tab.alignment.text_widget.insert(tkinter.END, "%s\n" % string)            
            # Saving data
            if seqs[i].ID in id_to_org_and_seq:
                print ("    [..WARNING..] Non-unique ID '%s' detected; purification may work unproperly!" % seqs[i].ID)

            curr_org_name = seqs[i].name.replace(seqs[i].ID, "")
            if re.match("^[^\|]+\|[^\|]+\|[^\|]+$", seqs[i].name):
                curr_org_name = seqs[i].name.split("|")[2]
            elif re.match("^[^\|]+\|[^\|]+$", seqs[i].name):
                curr_org_name = seqs[i].name.split("|")[1]
                
            id_to_org_and_seq[seqs[i].ID] = (curr_org_name, seqs[i].sequence)
            id_list.append(seqs[i].ID)

        self.purify_tab.id_to_org_and_seq = id_to_org_and_seq
        self.purify_tab.id_list = id_list
        self.purify_tab.seqs_cut = seqs_cut
        self.purify_tab.id_to_features = None
        self.purify_tab.featured_sequences = None
        self.purify_tab.valid_start = valid_start
        self.purify_tab.valid_end = valid_end
        self.purify_tab.name_length = max_name_length + len(separator)
        self.purify_tab.activate_buttons()
        #FIX: version 0.2.8 (self-hits data is set to default)
        self.purify_tab.evalue_threshold.delete(0, tkinter.END)
        self.purify_tab.evalue_threshold.configure(state = tkinter.DISABLED)
        self.purify_tab.sigma_num_self.delete(0, tkinter.END)
        self.purify_tab.sigma_num_self.configure(state = tkinter.DISABLED)

        del udav_base
        self.set_status("Ready")

    def check_settings(self):
        """
        This method checks if all required settings are correctly set. That is:
        1) there should be settings for work_dir, hmmer_dir, muscle_dir, script_dir, pfam_profiles 
           and cog_profiles attributes of <self.settings>;
        2) directories <self.settings.work_dir> and <self.settings.script_dir> must exist, files 
           <self.settings.pfam_profiles> and <self.settings.cog_profiles> must exist;
        3) programs 'muscle' and 'hmmbuild', 'hmmsearch' must exist in respective directories.
        """
        results = list()
        results.append(Aln_basic.exists(self.settings, "muscle_dir", os.path.isdir, "Muscle directory"))
        results.append(Aln_basic.exists(self.settings, "hmmer_dir", os.path.isdir, "HMMer directory"))
        results.append(Aln_basic.exists(self.settings, "work_dir", os.path.isdir, "Working directory"))
        results.append(Aln_basic.exists(self.settings, "cog_profiles", os.path.isfile, "Database of COG profiles"))
        results.append(Aln_basic.exists(self.settings, "pfam_profiles", os.path.isfile, "Database of Pfam profiles"))
        extension = ""
        if platform.system() == "Windows":
            extension = ".exe"
        results.append(Aln_basic.exists(self.settings, "muscle_dir", os.path.isfile, "Muscle program", "muscle" + extension))
        results.append(Aln_basic.exists(self.settings, "hmmer_dir", os.path.isfile, "HMMbuild program", "hmmbuild" + extension))
        results.append(Aln_basic.exists(self.settings, "hmmer_dir", os.path.isfile, "HMMsearch program", "hmmsearch" + extension))
        results.append(Aln_basic.exists(self.settings, "hmmer_dir", os.path.isfile, "HMMscan program", "hmmscan" + extension))

        if False in results:
            sys.exit()

    def diagnostics(self):
        self.log_tab.get_current_project_state()
    
    def set_status(self, curr_status, curr_color = "#888800"):        
        if curr_status in self.known_status:
            curr_color = self.known_status[curr_status][1]
            curr_status = self.known_status[curr_status][0]
        self.status_label.configure(text = "[..%s..]" % curr_status, foreground = curr_color)
        self.update()

    def enable_check_button(self):
        self.check_button.configure(state = tkinter.NORMAL, background = self.header)

    def disable_check_button(self):
        self.check_button.configure(state = tkinter.DISABLED, background = "light grey")

    def check_pending(self):                 
        files_ready = list()
        i = 0
        while i < len(self.pending_filenames):
            filename = self.pending_filenames[i]
            if os.path.isfile(filename):
                file_to_check = open(filename)
                strings = file_to_check.readlines()
                file_to_check.close()
                try:
                    if strings[-1].strip() == "# [ok]":
                        files_ready.append(filename)
                        self.pending_filenames.pop(i)
                        i -= 1
                except IndexError:
                    print ("File '%s' is not yet ready..." % filename) 
            i += 1
        if len(self.pending_filenames) == 0:
            self.disable_check_button()

        ready_and_required = list()
        for curr_file in files_ready:
            base_name = os.path.basename(curr_file)
            name_parts = base_name.split(".")
            if len(name_parts) != 2: # Files without extension or with multiple dots are not considered
                continue 
            project_name = name_parts[0]
            extension = name_parts[1]
            if project_name == self.get_project_name():
                if extension == "Pfam_table":
                    Aln_basic.read_widget_from_file(self.features_tab.hmmresults_Pfam.text_widget, curr_file)
                    ready_and_required.append(extension)
                if extension == "COG_table":
                    Aln_basic.read_widget_from_file(self.features_tab.hmmresults_COG.text_widget, curr_file)
                    ready_and_required.append(extension)
          
        if len(ready_and_required) == 0: # No files are ready
            self.set_status("Sorry, no file delivered!")
        else:
            self.set_status("These files were ready and loaded: %s" % ",".join(ready_and_required))
        
    def save_project(self):
        #answer = tkMessageBox.askyesno("Please confirm saving", "Are you sure you want to save %s project? Existing files, if any, will be re-writed!" % self.get_project_name())
        #if answer != True:
        #   return
        if self.get_project_name().count(".") != 0: # Dots in the project name are not allowed
            name_answer = tkMessageBox.askyesno("Please change project name", "Currently selected project name is: '%s'. This name contain dot(s), and thus it would not be possible to read project files from it afterwards. Please change the name to, e.g., '%s' before saving. Are you sure you want to continue anyway?" % (self.get_project_name(), self.get_project_name().replace(".", "_")))
            if name_answer != True:
               return
        if self.get_project_name() == "": # No project name specified
            return
        curr_project_dir = os.path.join(self.settings.work_dir, self.get_project_name())
        if not os.path.isdir(curr_project_dir): # Directory for the project was not yet created
            print ("    Creating project directory de novo: '%s'" % curr_project_dir)
            os.mkdir(curr_project_dir)

        self.save_colors()
        self.input_tab.save_alignment()
        self.input_tab.save_sequence_sample()
        self.input_tab.save_taxonomy_data()
        #self.purify_tab.save_actions()
        self.parse_tab.save_fixed(False)
        self.parse_tab.save_pure(False)
        self.parse_tab.save_blocks(False)
        self.parse_tab.save_IDs(False)
        self.features_tab.save_TMHMM(False)
        #self.features_tab.save_features(False) #FIX: version 0.2.8 (features should not be saved)
        self.log_tab.save_logs(False)

    def clear_all(self):
        print ("------------- Erasing all data -------------")   
        self.input_tab.clear()
        self.parse_tab.clear()
        self.purify_tab.clear()
        self.features_tab.clear()
        self.log_tab.clear()

        self.parse_tab.disable_pure_analysis()
        self.purify_tab.disable_buttons()

        self.domain_colors = list()
        self.domain_to_colors = dict()
        self.gi_to_tax = None
        self.domain_colors.append(("Enter domain/COG ID", "#FFFFFF"))
        self.domain_colors.append(("TMHMM", "#FF0000"))
        self.domain_to_color["TMHMM"] = "#FF0000"
        
        for i in self.domain_info.get_children():
            self.domain_info.delete(i)

        self.project_title_widget.delete(0, tkinter.END)
        self.clear_temp_files()
        
    def load_project(self):
        project_dir = os.path.join(self.settings.work_dir, self.get_project_name())
        if self.get_project_name() == "": # No project name was entered
            project_dir = tkFileDialog.askdirectory(initialdir = self.settings.work_dir, title = "Please select a folder with the project:")
            if project_dir == "": # Cancel
                return
        if not os.path.isdir(project_dir):
            self.set_status("This project does not exist, please check its name again!", "#FF0000")
            return
        #answer = tkMessageBox.askyesno("Please confirm loading", "Are you sure you want to load %s project? All existing data in the frames, if any, will be re-writed!" % self.get_project_name())
        #if answer != True:
        #   return
        self.clear_all()
        self.project_title_widget.insert(tkinter.END, os.path.basename(project_dir))
 
        self.set_status("Working")
        print ("-------- Project %s is now loading! --------" % self.get_project_name())

        project_files = os.listdir(project_dir)
        extension_to_widget = {"aln"            : self.input_tab.aln_input_frame.text_widget,
                               "sample"         : self.input_tab.seq_input_frame.text_widget,
                               "tax"            : self.input_tab.tax_input_frame.text_widget,
                               "fixed"          : self.parse_tab.fixed.text_widget,
                               "pure"           : self.parse_tab.pure.text_widget,
                               "ngphylogeny"    : self.parse_tab.ngphylogeny.text_widget,
                               "blocks_regions" : self.parse_tab.blocks.text_widget,
                               "ids"            : self.parse_tab.IDs.text_widget,
                               "COG_table"      : self.features_tab.hmmresults_COG.text_widget,
                               "Pfam_table"     : self.features_tab.hmmresults_Pfam.text_widget,
                               "TMHMM"          : self.features_tab.TMHMM_results.text_widget,
                              #"features"       : self.features_tab.features.text_widget, #FIX: version 0.2.8 (features should not be loaded)
                               "auto_log"       : self.log_tab.auto_log.text_widget,
                               "rem_log"       : self.log_tab.remove_log.text_widget,
                               "man_log"        : self.log_tab.manual_log.text_widget}

        for curr_file in project_files:
            name_parts = curr_file.split(".")
            if len(name_parts) != 2: # Files without extension or with multiple dots are not considered
                continue 
            project_name = name_parts[0]
            extension = name_parts[1]
            full_filename = os.path.join(project_dir, curr_file)
            if project_name == self.get_project_name():
                if extension in extension_to_widget:                    
                    Aln_basic.read_widget_from_file(extension_to_widget[extension], full_filename)
                if extension == "pure":
                    self.parse_tab.enable_pure_analysis()
                #if extension == "actions":
                #    self.purify_tab.load_actions(full_filename)
                if extension == "colors":
                    self.load_colors_from_file(full_filename)

        self.parse_tab.check_numbers()
        self.log_tab.color_important()
        self.set_status("Ready")   

    def get_project_name(self):
        return self.project_title_widget.get().strip()

    def load_colors_from_file(self, filename):
        color_file = open(filename)
        for string in color_file:
            string = string.strip()
            if len(string) == 0:
                continue
            fields = string.split("\t")
            if fields[0] != "Enter domain/COG ID":
                if not fields[1] in self.domain_to_color:                   
                    self.domain_colors.append((fields[1], fields[0]))
                    self.domain_to_color[fields[1]] = fields[0]
        color_file.close()

    def save_colors(self):
        domain_color_file = os.path.join(self.settings.work_dir, self.get_project_name(), "%s.colors" % self.get_project_name())
        color_file = open(domain_color_file, "w")
        for pair in self.domain_colors:
            if pair[0] != "Enter domain/COG ID":
                color_file.write("%s\t%s\n" % (pair[1], pair[0]))
        color_file.close()

    def palette_is_saved(self, colors, data_type, names):
        """
        Method for interaction between the <ColorFrame.ColorWind> and this program:
        it is called to compare current color/name set with the one in
        the <ColorFrame.ColorWind> window. Returns True or False
        """
        curr_colors = list()
        curr_names = list()
        for pair in self.domain_colors:
            curr_colors.append(pair[1])
            curr_names.append(pair[0])
        same_colors = Aln_basic.compare_sets(colors, curr_colors)
        same_names = Aln_basic.compare_sets(names, curr_names)
        return same_colors and same_names

    def open_color_frame(self):  
        colors = list()
        names = list()
        for pair in self.domain_colors:
            colors.append(pair[1])
            names.append(pair[0])
        domain_color_file = os.path.join(self.settings.work_dir, self.get_project_name(), "%s.colors" % self.get_project_name())
        ColorFrame.ColorWind(self, "", "Domain color scheme", colors, names, self.header, "#808080", self.icon_filename, domain_color_file)

    def set_random_colors(self):
        if self.domain_info != None:
            RGB_range = range(0,255)
            self.domain_to_color = dict()
            self.domain_colors = list()
            self.domain_to_color["TMHMM"] = "#FF0000"
            for value in self.domain_info.get_children(""):
                #curr_domain_id = self.domain_info.item(value)["values"][0]
                curr_domain_id = self.domain_info.item(value)["text"] #FIX: version 0.2.8 (Pfam data like 'Cytochrome_B' is used instead of 'PF00033')
                rand_color = "#%02x%02x%02x" % (random.choice(RGB_range), random.choice(RGB_range), random.choice(RGB_range))
                self.domain_to_color[curr_domain_id] = rand_color
                self.domain_colors.append((curr_domain_id, rand_color))
                # Actual coloring: FIX: version 0.2.8 (frustrating non-coloring on pressing the button fixed)
                self.domain_info.tag_configure(curr_domain_id, background = rand_color)
                self.domain_info.item(value, tags=(curr_domain_id, ))
            self.domain_colors.append(("TMHMM", "#FF0000"))

    def import_colors(self, colors, data_type, color_names):
        print ("    Importing colors from the color panel...")
        self.domain_colors = list()
        self.domain_to_color = dict()
        for i in range(len(colors)):
            self.domain_colors.append((color_names[i], colors[i]))          
            if color_names[i] in self.domain_to_color:
                print ("    [..WARNING..] Duplicate COG name found: %s; latest color will be used!" % color_names[i])
            self.domain_to_color[color_names[i]] = colors[i]
        print ("    [..DONE..]")

    def clear_temp_files(self):
        for curr_file in os.listdir(self.settings.work_dir):
            file_prefix = curr_file.split(".")[0]
            if file_prefix == self.temp_name:
                os.remove(os.path.join(self.settings.work_dir, curr_file))

    def on_close(self):
        self.clear_temp_files()
        tkinter.Tk.destroy(self.parent)

class WindowCommands:
    """
    This is a class of basic commands which tune all <tkinter.Text> widgets
    to the russian commands. It is shared among three programs:
    COGalyser, Alnalyser and NyanTranslate
    """
    def __init__(self, host):
        self.host = host

    def rus_copy(self, event):
        #print ("Crtl + C (russian) pressed in '%s' widget" % event.widget.winfo_class())
        if event.widget.winfo_class() == "Text":
            if event.widget.tag_ranges("sel"):
                content = event.widget.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
                self.host.parent.clipboard_clear() 
                self.host.parent.clipboard_append(content)
   
    def rus_paste(self, event):
        #print ("Crtl + V (russian) pressed in '%s' widget" % event.widget.winfo_class())
        if event.widget.winfo_class() == "Text":
            if event.widget.tag_ranges("sel"):
                event.widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
            event.widget.insert("insert", event.widget.selection_get(selection='CLIPBOARD'))

    def rus_cut(self, event):
        #print ("Crtl + X (russian) pressed in '%s' widget" % event.widget.winfo_class())
        if event.widget.winfo_class() == "Text":
            if event.widget.tag_ranges("sel"):
                self.rus_copy(event)
                event.widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)

    def select_all(self, event):
        if event.widget.winfo_class() == "Text":
            event.widget.tag_add("sel", 1.0, "%s-%dc" % (tkinter.END, 1))

def set_proper_size (main_window):
    main_window.update_idletasks()
    w = main_window.winfo_width()
    h = main_window.winfo_height()
    screen_w = main_window.parent.winfo_screenwidth()
    screen_h = main_window.parent.winfo_screenheight()
    main_window.parent.geometry("%dx%d+%d+%d" % (w, screen_h - 100, (screen_w - w)/2, 0))

root = tkinter.Tk()
root.title("Alnalyser (version %s)" % curr_version)
root.iconbitmap(ICON_FILENAME)

root.grid_rowconfigure(0, weight = 1)
root.grid_columnconfigure(0, weight = 1)

main_window = Alnalyser(root, INI_FILENAME, LOGO_FILENAME, ICON_FILENAME)
main_window.grid(row = 0, column = 0, sticky = "NSEW")
commands = WindowCommands(main_window)
root.bind("<Control-ntilde>", commands.rus_copy)
root.bind("<Control-igrave>", commands.rus_paste)
root.bind("<Control-division>", commands.rus_cut)
root.bind("<Control-ocircumflex>", commands.select_all)
root.bind("<Control-a>", commands.select_all)

actions_menu = AlnPurify.ActionMenu(root, main_window)
text_menu = AlnPurify.TextMenu(root, main_window)
def post_menu(event):
    actions_menu.show_menu(event)
    text_menu.show_menu(event)
root.bind("<Button-3>", post_menu) 

set_proper_size(main_window)
if platform.system() == "Windows":
    root.wm_state("zoomed")
root.mainloop()