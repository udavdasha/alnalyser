# -*- coding: utf-8 -*-
import os, re
import tkinter
import tkinter.messagebox as tkMessageBox
import tkinter.ttk as ttk
import Aln_basic, Settings

class ActionMenu(tkinter.Menu):
    def __init__(self, parent, host):
        tkinter.Menu.__init__(self, parent, tearoff = 0)
        self.parent = parent          # Root window object
        self.host = host              # Alnalyser main window
        self.selection = None         # List of IDs of elements from actions Treeview
        self.normal_color = "#AAFFAA"      
        self.removal_color = "#FFAAAA"
        self.fix_color = "#FFE680"
        self.host.purify_tab.actions.tag_configure("normal", background = self.normal_color)
        self.host.purify_tab.actions.tag_configure("removal", background = self.removal_color)
        self.host.purify_tab.actions.tag_configure("fix", background = self.fix_color)
        self.create_menu()            
        
    def create_menu(self):    
        self.add_command(label="Mark as normal", background = self.normal_color, command = self._normal)
        self.add_command(label="Mark for removal", background = self.removal_color, command = self._removal)
        self.add_command(label="Mark for N-term fix", state = tkinter.DISABLED, background = self.fix_color, command = self._fix)
        self.add_separator()       
        self.add_command(label="Remove mark", command = self._unmark)   

    def _normal(self):
        for item_id in self.selection:
            self.host.purify_tab.actions.item(item_id, tags = ("normal",))

    def _removal(self):
        for item_id in self.selection:
            self.host.purify_tab.actions.item(item_id, tags = ("removal",))

    def _fix(self):
        for item_id in self.selection:
            self.host.purify_tab.actions.item(item_id, tags = ("fix",))

    def _unmark(self):
        for item_id in self.selection:
            self.host.purify_tab.actions.item(item_id, tags = ())
        
    def show_menu(self, event):       
        try:
            if len(event.widget.selection()) == 0:
                curr_id = event.widget.identify_row(event.y)     
                event.widget.selection_set(curr_id)
            self.selection = event.widget.selection()
            a = event.widget.menu_available # Checking if this is not the TreeView in the main window
            self.post(event.x_root, event.y_root)
        except AttributeError:
            pass

class TextMenu(tkinter.Menu):
    def __init__(self, parent, host):
        tkinter.Menu.__init__(self, parent, tearoff = 0)
        self.parent = parent          # Root window object
        self.host = host              # Alnalyser main window
        self.selection = None         # List of IDs of elements from actions Treeview  
        self.removal_color = "#FFAAAA"
        self.fix_color = "#FFE680"
        self.host.purify_tab.actions.tag_configure("removal", background = self.removal_color)
        self.host.purify_tab.actions.tag_configure("fix", background = self.fix_color)
        self.create_menu()            
        
    def create_menu(self):    
        self.add_command(label="Mark for removal", background = self.removal_color, command = self._removal)
        self.add_command(label="Mark for N-term fix", state = tkinter.DISABLED, background = self.fix_color, command = self._fix)

    def _removal(self):
        for protein_id in self.selection:
            curr_org = self.host.purify_tab.id_to_org_and_seq[protein_id][0]
            curr_reason = "manual"
            self.host.purify_tab.add_to_actions(protein_id, (curr_reason, curr_org), ("removal",))            

    def _fix(self):
        for protein_id in self.selection:
            curr_org = self.host.purify_tab.id_to_org_and_seq[protein_id][0]
            curr_reason = "manual"
            self.host.purify_tab.add_to_actions(protein_id, (curr_reason, curr_org), ("fix",))   
      
    def show_menu(self, event):
        self.selection = list()
        try:
            a = event.widget.purify_text_widget # Checking if this is a text widget in "Purify" tab
            if event.widget.tag_ranges("sel"):
                start = "%s linestart" % tkinter.SEL_FIRST               
                first_id = event.widget.get(start, "%s+%ic" % (start, self.host.purify_tab.name_length))
                first_id = first_id.split("|")[0]
                end = "%s linestart" % tkinter.SEL_LAST
                last_id = event.widget.get(end, "%s+%ic" % (end, self.host.purify_tab.name_length))
                last_id = last_id.split("|")[0]

                adding = False
                for protein_id in self.host.purify_tab.id_list:
                    if protein_id == first_id:
                        adding = True
                    if adding == True:
                        self.selection.append(protein_id)
                    if protein_id == last_id:
                        adding = False                   
            self.post(event.x_root, event.y_root)
        except AttributeError:
            pass

class AlnPurify(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.host = host
        self.p = self.host.p
        self.alignment = None                # Main widget
        self.actions = None                  # Treeview widget with possible actions to take
        self.evalue_threshold = None         # Entry for the e-value threshold
        self.sigma_num_self = None           # Entry for the number of sigma-values for proteins 'normal' with hit length (sigma = sqrt(dispersion))
        self.self_hits_button = None         # Button to start searching of self hits
        self.min_length = None               # Entry for the minimal protein length
        self.max_length = None               # Entry for the maximal protein length
        self.white_crow_button = None        # Button to run analysis
        self.show_features = None            # Button to show domains
        self.hide_features = None            # Button to hide domains
        self.load_taxonomy = None            # Button to load taxonomy
        self.act = None                      # Button to apply actions
        self.presence_entry = None           # Entry for the presence threshold (for Aln_basic.get_valid_alignment_range())

        self.featured_sequences = None       # Featured sequences
        self.valid_start = None              # Position in the alignment where showing region is starting (configured in <Alnalyser.purify()> method)
        self.valid_end = None                # Position in the alignment where showing region is ending (configured in <Alnalyser.purify()> method)
        self.name_length = None              # Sequence name length (with separator)
        self.id_to_features = None           # Hash of protein IDs to features created by a self-hmmer search during purification
        self.id_to_org_and_seq = None        # Hash of protein IDs to their (organism name, sequence)
        self.id_list = None                  # List of protein IDs in order of their occurence in the widget
        self.seqs_cut = None                 # List of cutted sequences (as present in the widget tab)
        
        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")

        base_frame = tkinter.Frame(central_panel)
        base_frame.columnconfigure(0, weight = 1) 
        base_frame.rowconfigure(1, weight = 1)

        top_frame = tkinter.Frame(base_frame)
        tkinter.Label(top_frame, text = "Max e-value:").grid(row = 0, column = 0, sticky = "NSW")
        self.evalue_threshold = tkinter.Entry(top_frame, state = tkinter.DISABLED, width = 8)
        self.evalue_threshold.grid(row = 0, column = 1, sticky = "NSW", padx = self.p, pady = self.p)
        tkinter.Label(top_frame, text = "# of σ (hit):").grid(row = 0, column = 2, sticky = "NSW")
        self.sigma_num_self = tkinter.Entry(top_frame, state = tkinter.DISABLED, width = 4)
        self.sigma_num_self.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)
        self.self_hits_button = tkinter.Button(top_frame, state = tkinter.DISABLED, text = "Find self-hits", command = self.find_self_hits)
        self.self_hits_button.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)
        self.white_crow_button = tkinter.Button(top_frame, state = tkinter.DISABLED, text = "Apply options", command = self.apply_purification_options)
        self.white_crow_button.grid(row = 1, column = 4, sticky = "NSW", padx = self.p, pady = self.p)         
        tkinter.Label(top_frame, text = "Min length:").grid(row = 1, column = 0, sticky = "NSW")
        self.min_length = tkinter.Entry(top_frame, width = 6)
        self.min_length.insert(tkinter.END, "0")
        self.min_length.grid(row = 1, column = 1, sticky = "NSW", padx = self.p, pady = self.p)
        tkinter.Label(top_frame, text = "Max length:").grid(row = 1, column = 2, sticky = "NSW")
        self.max_length = tkinter.Entry(top_frame, width = 6)
        self.max_length.insert(tkinter.END, "10000")
        self.max_length.grid(row = 1, column = 3, sticky = "NSW", padx = self.p, pady = self.p)

        top_frame.grid(row = 0, column = 0, columnspan = 2, sticky = "NSEW")

        y_scrollbar = tkinter.Scrollbar(base_frame)
        y_scrollbar.grid(row = 1, column = 1, sticky = "NS")
        actions = ttk.Treeview(base_frame, columns = ("action", "organism"), selectmode = "extended",
                               yscrollcommand = y_scrollbar.set)
        y_scrollbar.config(command = actions.yview)
        actions.grid(row = 1, column = 0, sticky = "NSEW")
        actions.column("action", width = 50, anchor = "w")
        actions.heading("action", text = "Action")
        actions.column("organism", width = 50, anchor = "w")
        actions.heading("organism", text = "Organism")
        actions.bind("<Double-Button-1>", self.get_click)
        self.actions = actions
        self.actions.menu_available = True # To show <ActionMenu> only at this widget    
        central_panel.add(base_frame)

        self.alignment = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF", "Suggested changes in alignment:", "Load domains")   
        self.alignment.button.configure(state = tkinter.DISABLED, command = self.create_domain_tags)
        self.alignment.text_widget.purify_text_widget = True # To show <TextMenu> only at this widget    
        self.show_features = tkinter.Button(self.alignment.panel, state = tkinter.DISABLED, text = "Show domains", command = self.show_domains)
        self.show_features.grid(row = 0, column = 2, sticky = "NSW", padx = self.p, pady = self.p) 
        self.hide_features = tkinter.Button(self.alignment.panel, state = tkinter.DISABLED, text = "Hide domains", command = self.hide_domains)
        self.hide_features.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)
        self.load_taxonomy = tkinter.Button(self.alignment.panel, state = tkinter.DISABLED, text = "Color taxonomy", command = self.color_taxonomy)
        self.load_taxonomy.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)
        self.act = tkinter.Button(self.alignment.panel, state = tkinter.DISABLED, text = "Apply actions", background = self.host.header, foreground = "#FFFFFF", command = self.apply_actions)
        self.act.grid(row = 0, column = 5, sticky = "NSW", padx = self.p * 3, pady = self.p)
        tkinter.Label(self.alignment.panel, text = "Presence required (%):").grid(row = 0, column = 6)
        self.presence_entry = tkinter.Entry(self.alignment.panel, width = 3)
        self.presence_entry.insert(tkinter.END, "0")
        self.presence_entry.grid(row = 0, column = 7, padx = self.p, pady = self.p)
        
        central_panel.add(self.alignment)

        self.update_idletasks()
        central_panel.sash_place(0, base_frame.winfo_reqwidth(), 1)

    def get_click(self, event):
        curr_id = event.widget.identify_row(event.y)
        curr_text_id = self.host.purify_tab.actions.item(curr_id)["text"]
        id_start = self.alignment.text_widget.search(curr_text_id, 1.0, stopindex = tkinter.END)
        id_end = '%s+%dc' % (id_start, len(curr_text_id))
        self.alignment.text_widget.focus()
        self.alignment.text_widget.tag_remove("sel", 1.0, tkinter.END)
        self.alignment.text_widget.tag_add("sel", id_start, id_end)
        self.alignment.text_widget.see(id_start)        

    def find_self_hits(self):
        import udav_base, udav_soft
        # --------------------------------------- 1) HMMbuild
        aligned_filename = os.path.join(self.host.settings.work_dir, "%s.aln" % self.host.temp_name)
        pure_filename = os.path.join(self.host.settings.work_dir, "%s.pure" % self.host.temp_name)
        udav_base.print_pure_sequences(self.seqs_cut, pure_filename, True, True)
        alnfile = open(aligned_filename, "w")
        for s in self.seqs_cut:
            s.print_fasta(alnfile)
        alnfile.close()
        (hmmbuild_name, hmmbuild_path) = Settings.get_program_name(self.host.settings.hmmer_dir, "hmmbuild")
        (hmmsearch_name, hmmsearch_path) = Settings.get_program_name(self.host.settings.hmmer_dir, "hmmsearch")
        hmm_filename = os.path.join(self.host.settings.work_dir, "%s.hmm" % self.host.temp_name)
        result_filename = os.path.join(self.host.settings.work_dir, "%s.self_out" % self.host.temp_name)
        domtable_filename = os.path.join(self.host.settings.work_dir, "%s.self_domtable" % self.host.temp_name)
        table_filename = os.path.join(self.host.settings.work_dir, "%s.self_table" % self.host.temp_name)

        self.host.set_status("Running HMMbuild", "#FF0000")
        print ("    Running HMMbuild for the cutted alignment...")
        #FIX: version 0.2.8 (--wnone option suppresses weightening of sequences in hmmbuild thus poor sequences do not alter profile that much)
        if self.host.verbose.get():        
            os.system("%s --wnone --informat=afa %s %s" % (hmmbuild_path, hmm_filename, aligned_filename))
        else:
            os.system("%s --wnone --informat=afa %s %s 1> nul 2> nul" % (hmmbuild_path, hmm_filename, aligned_filename))
        # --------------------------------------- 2) HMMsearch
        self.host.set_status("Running HMMsearch", "#FF0000")   
        print ("    Running HMMsearch to search for the self-hits...")     
        if self.host.verbose.get():
            os.system("%s --tblout %s --domtblout %s -o %s %s %s" % (hmmsearch_path, table_filename, domtable_filename, result_filename, hmm_filename, pure_filename))
        else:
            os.system("%s --tblout %s --domtblout %s -o %s %s %s 1> nul 2> nul" % (hmmsearch_path, table_filename, domtable_filename, result_filename, hmm_filename, pure_filename))        

        # --------------------------------------- 3) Obtaining features
        self.host.set_status("Obtaining self-hit features", "#FF0000")
        print ("    Obtaining self-hit features...")           
        (self.id_to_features, domains) = udav_soft.read_Pfam_output(domtable_filename, "1.0", False, None, add_score = True, hmmsearch_output = True)
        del udav_base, udav_soft
        #os.remove(result_filename)
        #os.remove(domtable_filename)
        #os.remove(table_filename)

        self.evalue_threshold.configure(state = tkinter.NORMAL)
        self.evalue_threshold.delete(0, tkinter.END) #FIX: version 0.2.8 (removing values before appending)
        self.evalue_threshold.insert(tkinter.END, "1e-5")
        self.sigma_num_self.configure(state = tkinter.NORMAL)
        self.sigma_num_self.delete(0, tkinter.END) #FIX: version 0.2.8 (removing values before appending)
        self.sigma_num_self.insert(tkinter.END, "2")
        self.self_hits_button.configure(state = tkinter.DISABLED)

        self.host.set_status("Ready")

    def show_blocks_regions(self, blocks_string):
        if blocks_string == None: # No string was found
            return
        blocks = list() #---------------------- 1) Reading <blocks_string> into a list of regions
        reading_block = False
        for i in range(len(blocks_string)):
            letter = blocks_string[i]
            if not reading_block:
               if letter != "-": # No gap symbol; block started!
                   suggested_start = i - self.valid_start
                   real_start = max(0, suggested_start)
                   start_end = {"start" : real_start, "end" : None}

                   blocks.append(start_end)
                   reading_block = True 
            if reading_block:
                if letter == "-": # Gap symbol; block ended!
                   suggested_end = i - (self.valid_start + 1)
                   real_end = min(self.valid_end - self.valid_start + 1, suggested_end)
                   blocks[-1]["end"] = real_end
                   reading_block = False

        strings = self.alignment.get_strings()
        for i in range(len(strings)): #-------- 2) Adding <blocks> tag
            for b in blocks:
                tag_start = "%i.%i" % (i + 1, b["start"] + self.name_length)
                tag_end = "%i.%i" % (i + 1, b["end"] + self.name_length + 1)
                self.alignment.text_widget.tag_add("blocks", tag_start, tag_end)

    def add_tag_to_text(self, strings_to_search, tag_name, fore = None, back = None):
        for string in strings_to_search:
            start = "1.0"
            while True:
                hit_position = self.alignment.text_widget.search(string, start, stopindex = tkinter.END)
                if not hit_position:
                    break
                end_position = '%s+%dc' % (hit_position, len(string))
                self.alignment.text_widget.tag_add(tag_name, hit_position, end_position)                               
                start = end_position
        if fore != None:
            self.alignment.text_widget.tag_config(tag_name, foreground = fore)
        if back != None:  
            self.alignment.text_widget.tag_config(tag_name, background = back)               

    def add_to_actions(self, protein_id, column_values, curr_tags = ()):
        should_add = True
        for a in self.actions.get_children(""):
            a_id = self.actions.item(a)["text"]
            if a_id == protein_id: # This protein id is already in the actions list
                should_add = False
                curr_values = self.actions.item(a)["values"]
                if not column_values[0] in curr_values[0]: # Different reason
                    self.actions.item(a, values = ("%s, %s" % (curr_values[0], column_values[0]), curr_values[1]))
                break
        if should_add:
            self.actions.insert("", "end", text = protein_id, values = column_values, tags = curr_tags)

    def get_self_hit_info(self, evalue_threshold, sigma_num, no_hit, poor_hit, partial_hit):
        hit_positions = dict()        
        print ("    List of self-hits (<from-to..e-value..Score>):")
        for protein_id in self.id_to_org_and_seq.keys():
            (curr_org, curr_seq) = self.id_to_org_and_seq[protein_id]
            if not protein_id in self.id_to_features: # No hit found at all
                self.add_to_actions(protein_id, ("no hit", curr_org))
                no_hit.append(protein_id)
            else:
                #[profile name] 1..456..1e-56..256.7 <...>
                lowest_evalue = 100
                best_start = -1
                best_end = -1
                curr_features = self.id_to_features[protein_id].split(" ")[1:]             
                print ("    %s\t%s" % (protein_id, curr_features))
                for feature in curr_features:
                    values = feature.strip("\t").split("..")
                    evalue = float(values[2])
                    if evalue < lowest_evalue:
                        lowest_evalue = evalue
                        best_start = values[0]
                        best_end = values[1]
                if lowest_evalue > evalue_threshold:
                    poor_hit.append(protein_id)
                    self.add_to_actions(protein_id, ("poor hit", curr_org))
                hit_positions[protein_id] = (int(best_start), int(best_end))
       
        mean_length = 0
        values = list()
        for protein_id in hit_positions.keys():
            curr_length = hit_positions[protein_id][1] - hit_positions[protein_id][0] + 1
            values.append(curr_length)
            mean_length += curr_length
        mean_length = float(mean_length)/len(hit_positions.keys())
        dispersion = 0
        for protein_id in hit_positions.keys():
            curr_length = hit_positions[protein_id][1] - hit_positions[protein_id][0] + 1
            dispersion += (curr_length - mean_length) ** 2
        dispersion = dispersion/len(hit_positions.keys())
        std_deviation = dispersion ** 0.5
        #print ("Mean is: %s" % mean_length)
        #print ("Dispersion is: %s" % dispersion)
        #print ("Std deviation is: %s" % std_deviation)
        #print ("------------------------------------")         
        for protein_id in hit_positions.keys():
            curr_length = hit_positions[protein_id][1] - hit_positions[protein_id][0] + 1
            if mean_length - curr_length > sigma_num * std_deviation: # Oh-o
                #print ("BAD\tID = %s, curr length = %s" % (protein_id, curr_length))
                partial_hit.append(protein_id)
                self.add_to_actions(protein_id, ("partial hit", self.id_to_org_and_seq[protein_id][0]))
            #else:
                #print ("GOOD\tID = %s, curr length = %s" % (protein_id, curr_length))
        
        info_string = "Length of hit part to a profile created from the alignment\n"
        info_string += "M(x): %.3f; D(x): %.3f; std. deviation = %.3f\n" % (mean_length, dispersion, std_deviation)
        info_string += "Number of std. deviations allowed: %s" % sigma_num

        begin = int(mean_length - (sigma_num * std_deviation))
        end = int(mean_length + (sigma_num * std_deviation))
        nsteps = 20
        step = (float(end - begin))/nsteps
        step = int(step)
        self.host.log_tab.write_histogram(values, info_string, begin, step, nsteps)  
  
    def get_length_info(self, short_seq, long_seq):
        min_length = None
        max_length = None
        try:
            min_length = float(self.min_length.get())
        except ValueError:
            print ("    [..WARNING..] Minimal protein length will not be considered")
        try:
            max_length = float(self.max_length.get())
        except ValueError:
            print ("    [..WARNING..] Maximal protein length will not be considered")

        for protein_id in self.id_to_org_and_seq.keys():
            curr_seq = self.id_to_org_and_seq[protein_id][1].replace("-", "")
            if (min_length != None) and (len(curr_seq) < min_length):
                self.add_to_actions(protein_id, ("short hit", self.id_to_org_and_seq[protein_id][0]))
                short_seq.append(protein_id) 
            if (max_length != None) and (len(curr_seq) > max_length):
                self.add_to_actions(protein_id, ("long hit", self.id_to_org_and_seq[protein_id][0]))
                long_seq.append(protein_id) 

    def apply_purification_options(self):
        print ("    Applying purification options!")
        tag_info = {"no_hit"      : ("#FF0000", "#000000"), # No hit found at any e-value threshold
                    "poor_hit"    : ("#000000", "#FFFF00"), # Weak hit found (with e-value higher than current threshold)                    
                    "partial_hit" : ("#FF0000", "#FFFFFF"), # Possible N-terminal flaw or organism join (id marked by fore and sequence region by back)
                    "org_join"    : ("#000000", "#FF00FF"),
                    "short_seq"   : (None, None),
                    "long_seq"    : (None, None)}
        for name in self.alignment.text_widget.tag_names():            
            if (name in tag_info) or (name == "bold") or (name == "italic"):
                self.alignment.text_widget.tag_remove(name, 1.0, tkinter.END)           
        for value in self.actions.get_children(""):
            curr_tags = self.actions.item(value)["tags"]
            if len(curr_tags) == 0: # No decision is made about this protein
                self.actions.delete(value) 

        no_hit = list()
        poor_hit = list()
        partial_hit = list()        
        short_seq = list()
        long_seq = list()
        if self.id_to_features != None:
            curr_evalue_threshold = 1e-5
            try:
                curr_evalue_threshold = float(self.evalue_threshold.get())
            except ValueError:
                print ("    [..WARNING..] Bad value entered as an e-value threshold; default %s is used!" % curr_evalue_threshold)

            sigma_num_self = 2        
            try:
                sigma_num_self = float(self.sigma_num_self.get())
            except ValueError:
                print ("    [..WARNING..] Bad value entered as sigma number; default %s is used!" % sigma_num_self)
            self.get_self_hit_info(curr_evalue_threshold, sigma_num_self, no_hit, poor_hit, partial_hit)

        self.get_length_info(short_seq, long_seq)

        self.add_tag_to_text(no_hit, "no_hit", tag_info["no_hit"][0], tag_info["no_hit"][1])
        self.add_tag_to_text(poor_hit, "poor_hit", None, tag_info["poor_hit"][1])
        self.add_tag_to_text(partial_hit, "partial_hit", tag_info["partial_hit"][0], None)
        self.add_tag_to_text(short_seq, "italic", None, None)
        self.add_tag_to_text(long_seq, "bold", None, None)

        print ("    [..DONE..]")

    def load_featured_sequences(self):
        """
        Method maps data from the Features tab (if it is not blank) on the alignment.
        """
        if self.host.features_tab.features.text_is_empty(): # No features obtained
            self.host.set_status("Cannot show domains; check that features in the 'Features' tab are obtained", "#888800")        
            tkMessageBox.showinfo("Obtain features first", "Before purification analysis please obtain features in the 'Features' tab!")            
            raise ValueError

        import udav_base
        self.host.set_status("Obtaining sequence features, check the console for progress", "#FF0000")
        aligned_filename = os.path.join(self.host.settings.work_dir, "%s.aln" % self.host.temp_name)
        Aln_basic.write_widget_into_file(self.host.input_tab.aln_input_frame.text_widget, aligned_filename, False)        
        features_filename = os.path.join(self.host.settings.work_dir, "%s.features" % self.host.temp_name)
        Aln_basic.write_widget_into_file(self.host.features_tab.features.text_widget, features_filename, False)  
        self.featured_sequences = udav_base.get_featured(aligned_filename, None, features_filename, dict(), dict(), False)
        del udav_base
        self.host.set_status("Ready")
        print ("    [..DONE..]")

    def create_domain_tags(self):
        """
        COGs or other domains are mapped in the order specified in the <self.host.domain_colors> list
        """        
        for tag_name in self.alignment.text_widget.tag_names():
            if (tag_name[0] == tag_name[0].upper()) and (tag_name[0] != "["): # This is not a technical or taxonomy tag, but domain/COG name
                self.alignment.text_widget.tag_delete(tag_name)

        if self.featured_sequences == None: # No features were obtained previously
            try:
                self.load_featured_sequences()
            except ValueError:
                return
                 
        req_domain_to_color = self.host.domain_to_color
        id_to_req_features = dict()
        blocks_seq = None
        for s in self.featured_sequences:
            if s.ID == "BLOCKS":
                blocks_seq = s.sequence
                continue
            if s.ID == "SITE":
                continue
            id_to_req_features[s.ID] = list()
            for feature in s.features:                           
                if feature.name in req_domain_to_color: # This domain has a certain color and should be drawn             
                    for region in feature.regions:                        
                        suggested_start = feature.get_begin(region) - (self.valid_start + 1)
                        suggested_end = feature.get_end(region) - (self.valid_start + 1)
                        real_start = max(0, suggested_start)
                        real_end = min(self.valid_end - self.valid_start + 1, suggested_end)
                        #print ("feature = %s: region = '%s', REAL start = '%s', REAL end = '%s'" % (feature.name, region, real_start, real_end))
                        if real_end > 0: # Thus it is in the showing range 
                            id_to_req_features[s.ID].append((feature.name, real_start, real_end))

        # --------------------------------------- 2) Adding tags to a widget
        proper_color_order = self.host.domain_colors
        for i in range(len(proper_color_order)):        
            if proper_color_order[i][0] == "TMHMM": # FIX 0.2.7 TMHMM tag should be added last, despite it is listed first
                proper_color_order.append(proper_color_order.pop(i))
                break
        
            
        for pair in proper_color_order: # FIX 0.2.3 Tags are now added in a proper order, as listed in color scheme
            for i in range(len(self.id_list)):
                protein_id = self.id_list[i]
                if protein_id in id_to_req_features:
                    for feature in id_to_req_features[protein_id]:
                        if pair[0] == feature[0]:
                            tag_start = "%i.%i" % (i + 1, feature[1] + self.name_length)
                            tag_end = "%i.%i" % (i + 1, feature[2] + self.name_length + 1)                                              
                            #print ("id = %s, domain = %s, start = %s, end = %s" % (protein_id, feature[0], tag_start, tag_end))
                            self.alignment.text_widget.tag_add(feature[0], tag_start, tag_end)
        self.show_features.configure(state = tkinter.NORMAL)
        self.hide_features.configure(state = tkinter.NORMAL)
        self.show_domains()

        self.show_blocks_regions(blocks_seq)

    def show_domains(self):
        for pair in self.host.domain_colors: # FIX 0.2.3 These domain names should be colored in a proper order
            tag_name = pair[0]
            if tag_name in self.alignment.text_widget.tag_names():
                if (tag_name[0] == tag_name[0].upper()) and (tag_name[0] != "["): # This is not a technical or taxonomy tag, but domain/COG name              
                    self.alignment.text_widget.tag_config(tag_name, background = self.host.domain_to_color[tag_name]) 

    def hide_domains(self):
        for tag_name in self.alignment.text_widget.tag_names():
            if (tag_name[0] == tag_name[0].upper()) and (tag_name[0] != "["): # This is not a technical or taxonomy tag, but domain/COG name
                self.alignment.text_widget.tag_config(tag_name, background = "#FFFFFF") 

    def apply_actions(self):
        ids_to_remove = dict() #---------------------- 1) Finding IDs to remove
        for action_id in self.actions.get_children():   
            curr_tags = self.actions.item(action_id)["tags"]
            if "removal" in curr_tags:
                curr_protein_id = self.actions.item(action_id)["text"]
                reason = self.actions.item(action_id)["values"][0]
                ids_to_remove[curr_protein_id] = [reason, None]
        ids_to_fix = dict() #---------------------- 2) Fixing N-terminal truncation (not available)

                            #---------------------- 3) Getting organism information
        p = 0
        for protein_id in ids_to_remove.keys():
            organism_remains = False
            if not protein_id in self.id_to_org_and_seq: # This protein was likely removed already
                #ids_to_remove.pop(protein_id)
                p += 1
                continue
            curr_org = self.id_to_org_and_seq[protein_id][0]
            for protein_jd in self.id_to_org_and_seq.keys():
                if not protein_jd in ids_to_remove:
                    remaining_org = self.id_to_org_and_seq[protein_jd][0]
                    if remaining_org == curr_org: # Organism for this protein ID remains in the sample
                        organism_remains = True
                        break
            ids_to_remove[protein_id][1] = organism_remains
        print ("    Previously removed proteins: %i" % p)
        self.host.input_tab.apply_actions(ids_to_remove, ids_to_fix)

    def color_taxonomy(self):
        error = False
        import udav_base, udav_tree_svg
        if self.host.gi_to_tax == None:
            self.host.set_status("Reading assignment of gi to taxonomy", "#FF0000")            
            curr_tax_text = self.host.input_tab.tax_input_frame.text_widget.get(1.0, tkinter.END).strip()
            strings = curr_tax_text.split("\n")
            first_symbol = None
            try:
                first_symbol = strings[0][0]
            except IndexError:
                print ("    [ERROR]: Taxonomy data is empty, please insert it into the 'Input' tab")
                self.host.set_status("Assignment of protein id to taxonomy was not loaded", "#888800")
                error = True

            if first_symbol == ">": # URef format input
                self.host.gi_to_tax = dict()
                for string in strings:
                    string = string.strip()
                    if len(string) == 0:
                        continue
                    if string[0] == ">":
                        try:
                            #                          [0]                         [1]                                                [2]                                         [3]                    [4]     [5]   [6]                                [7]                                   
                            #>gi|Unk|ref|BAF59926.1 PTH_1745|3-oxoacyl-(acyl-carrier-protein) synthase III|Pelotomaculum thermopropionicum SI DNA, complete genome.|Pelotomaculum thermopropionicum SI|1827707|1828699|-1|Bacteria; Firmicutes; Clostridia; Clostridiales; Peptococcaceae; Pelotomaculum|AP009389 BAAC01000000 BAAC01000001-BAAC01000195 @ GCA_000010565.1_ASM1056v1
                            protein_id = string.split(" ", 1)[0].split("|")[3]
                            fields = string.split(" ", 1)[1].split("|")
                            locus = fields[0]
                            taxonomy_field = fields[7]
                            taxons = taxonomy_field.split(";")
                            if len(taxons) == 1:
                                self.host.gi_to_tax[protein_id] = taxons[0]
                                self.host.gi_to_tax[locus] = taxons[0]
                            else:
                                self.host.gi_to_tax[protein_id] = taxons[1].strip()
                                self.host.gi_to_tax[locus] = taxons[1].strip()
                        except IndexError as e:
                            print ("    [ERROR]: URef format is wrong in the following line, not enought fields:")
                            print ("             '%s'" % string)
                            self.host.set_status("Assignment of protein id to taxonomy was not loaded", "#888800")
                            error = True                             
            else:
                self.host.gi_to_tax = udav_base.read_gi_to_tax(strings, True)

        if self.host.tax_to_color == None:
            try: 
                (self.host.tax_to_color, tax_order) = udav_tree_svg.read_taxonomy_colors(self.host.settings.tax_colors_filename)
            except AttributeError:
                print ("    [ERROR]: File with color code for taxons was not given to the script!")
                print ("             Please check 'tax_colors_filename' option in the <settings.ini> file")                   
                self.host.set_status("Color code for taxonomy coloring was not loaded", "#888800")
                error = True
            except FileNotFoundError:
                print ("    [ERROR]: File with color code for taxons '%s' not found!" % self.host.settings.tax_colors_filename) 
                self.host.set_status("Color code for taxonomy coloring was not loaded", "#888800")
                error = True
        del udav_base, udav_tree_svg
        if error == True:
            return    
        
        self.host.set_status("Coloring alignment", "#FF0000")
        for tag_name in self.alignment.text_widget.tag_names(): #--- 1) Removing previous marking, if any
            if tag_name[0] == "[": # This is taxonomy tag
                self.alignment.text_widget.tag_delete(tag_name)

        for tax_name in self.host.tax_to_color.keys(): #------------------- 2) Loading new taxonomy tags
            tag_name = "[%s]" % tax_name
            self.alignment.text_widget.tag_configure(tag_name, background = self.host.tax_to_color[tax_name], foreground = "#FFFFFF")

        for i in range(len(self.id_list)): #------------------------ 3) New marking
            protein_id = self.id_list[i]
            if protein_id.count("_") != 0: # e.g., it is YP_12345678.9 or 123456789_1-99 or CRP_ECOLI
                match = re.match("(.+)\_\d+\-d+$", protein_id)
                if match != None: # 123456789_1-99                
                    protein_id = match.group(1)
                    print (protein_id)
                else: # CRP_ECOLI or YP_12345678.9 or Nther_1492
                    pass

            curr_tag = "[Unknown]"
            if protein_id in self.host.gi_to_tax:
                curr_tag = "[%s]" % self.host.gi_to_tax[protein_id]                
            tag_start = "%i.%i" % (i + 1, self.name_length - 4)
            tag_end = "%i.%i" % (i + 1, self.name_length - 1)                                                                                     
            self.alignment.text_widget.tag_add(curr_tag, tag_start, tag_end)

        self.host.set_status("READY", self.host.header)

    def get_curr_options(self):
        result = "Options in the purify tab are currently these:\n"
        result += "Threshold e-value for the poor self-hits: %s\n" % self.evalue_threshold.get()
        result += "Number of std. deviations allowed in self-hit length: %s\n" % self.sigma_num_self.get()
        result += "Minimal protein length: %s\n" % self.min_length.get()
        result += "Maximal protein length: %s\n" % self.max_length.get()
        return result

    def save_actions(self):
        actions_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.actions" % self.host.get_project_name())
        actions_file = open(actions_filename, "w")
        actions_file.write("#protein_id\ttag\tvalues\n")
        for action_id in self.actions.get_children():   
            curr_tags = self.actions.item(action_id)["tags"]
            if len(curr_tags) != 0: # There was a decision about this protein
                curr_protein_id = self.actions.item(action_id)["text"]
                curr_values = self.actions.item(action_id)["values"]
                curr_tag = curr_tags[0]
                string = "%s\t%s" % (curr_protein_id, curr_tag)
                for value in curr_values:
                    string += "\t%s" % value
                actions_file.write("%s\n" % string)
        actions_file.close()

    def load_actions(self, filename):
        actions_file = open(filename, "r")
        for string in actions_file:
            string = string.strip()
            if len(string) == 0:
                continue
            if string[0] == "#":
                continue
            fields = string.split("\t")
            curr_protein_id = fields.pop(0)
            curr_tag = fields.pop(0)
            self.add_to_actions(curr_protein_id, fields, (curr_tag, ))
        actions_file.close()

    def activate_buttons(self):
        self.alignment.button.configure(state = tkinter.NORMAL)
        self.load_taxonomy.configure(state = tkinter.NORMAL)
        self.act.configure(state = tkinter.NORMAL)
        self.self_hits_button.configure(state = tkinter.NORMAL)
        self.white_crow_button.configure(state = tkinter.NORMAL)

    def disable_buttons(self):
        self.alignment.button.configure(state = tkinter.DISABLED)
        self.load_taxonomy.configure(state = tkinter.DISABLED)
        self.act.configure(state = tkinter.DISABLED)
        self.self_hits_button.configure(state = tkinter.DISABLED)
        self.white_crow_button.configure(state = tkinter.DISABLED)
        self.show_features.configure(state = tkinter.DISABLED)
        self.hide_features.configure(state = tkinter.DISABLED)

    def clear(self):
        self.alignment.text_widget.delete(1.0, tkinter.END)
        for value in self.actions.get_children(""):
            self.actions.delete(value)