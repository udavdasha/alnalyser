# -*- coding: utf-8 -*-
import os, re
import tkinter
import tkinter.messagebox as tkMessageBox
import Aln_basic, Settings

class AlnInput(tkinter.Frame):
    """
    Frame which manages the input: alignment and unaligned proteins
    """
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.host = host
        self.p = self.host.p
        self.aln_input_frame = None  # Frame with the text widget for the alignment
        self.seq_input_frame = None  # Frame with the text widget for the unaligned sequences
        self.tax_input_frame = None  # Frame with the text widget for taxonomy-related data
        self.maxiters = None         # Entry for muscle parameter maxiters (leave blank for default)
        self.gapopen = None          # Entry for muscle parameter gapopen (leave blank for default)
        self.gapextend = None        # Entry for muscle parameter gapextend (leave blank for default)
        self.insert_blocks = None    # Boolean value to insert BLOCKS and SITE sequences after alignment
        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")
        self.aln_input_frame = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF", 
                               "Insert multiple alignment or generate it from the left panel:", "Check input")
        self.aln_input_frame.button.configure(command = self.check_input)
        central_panel.add(self.aln_input_frame)
        
        self.seq_input_frame = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF",
                               "Insert unaligned sequences:", "Align now!")
        self.seq_input_frame.button.configure(command = self.align)
        central_panel.add(self.seq_input_frame)         

        self.insert_blocks = tkinter.BooleanVar()
        self.insert_blocks.set(False)
        c = tkinter.Checkbutton(self.seq_input_frame.panel, text = "Insert BLOCKS & SITE", variable = self.insert_blocks)
        c.grid(row = 0, column = 2, sticky ="NSW", padx = self.p, pady = self.p)

        tkinter.Label(self.seq_input_frame.panel, text = "maxiters").grid(row = 0, column = 3, sticky = "NSW")
        self.maxiters = tkinter.Entry(self.seq_input_frame.panel, width = 2)
        self.maxiters.insert(tkinter.END, "2")
        self.maxiters.grid(row = 0, column = 4, sticky = "NSW", padx = self.p, pady = self.p)

        tkinter.Label(self.seq_input_frame.panel, text = "gapopen").grid(row = 0, column = 5, sticky = "NSW")
        self.gapopen = tkinter.Entry(self.seq_input_frame.panel, width = 3)
        self.gapopen.insert(tkinter.END, "")
        self.gapopen.grid(row = 0, column = 6, sticky = "NSW", padx = self.p, pady = self.p)

        tkinter.Label(self.seq_input_frame.panel, text = "gapextend").grid(row = 0, column = 7, sticky = "NSW")
        self.gapextend = tkinter.Entry(self.seq_input_frame.panel, width = 3)
        self.gapextend.insert(tkinter.END, "")
        self.gapextend.grid(row = 0, column = 8, sticky = "NSW", padx = self.p, pady = self.p)

        filter_identical = tkinter.Button(self.seq_input_frame.panel, text = "Filter identical", command = self.filter_seq)
        filter_identical.grid(row = 0, column = 9, sticky = "NSW", padx = self.p, pady = self.p)

        self.tax_input_frame = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, self.host.header, "#FFFFFF",
                               "Taxonomy data (sequences in URef format or tab-separated values):", "")
        self.tax_input_frame.button.grid_forget()
        central_panel.add(self.tax_input_frame)

        self.update_idletasks()
        central_panel.sash_place(0, 480, 1)
        central_panel.sash_place(1, 1440, 1)

    def filter_seq(self):
        """
        This method filters sequences in the input frame which have the same ID.
        Also could filter identical protein sequences.
        """
        seqs = Aln_basic.read_fasta_from_strings(self.seq_input_frame.get_strings())
        seq_ids_unique = dict()
        seqs_unique = dict()        
        i = 0
        r = 0
        s = 0
        seq_size = len(seqs)
        bad_ids = list()
        identical_seq_ids = dict()
        smooth = True        
        while i < len(seqs):
            if not seqs[i].ID in seq_ids_unique: # This is normal sequence            
                seq_ids_unique[seqs[i].ID] = seqs[i].sequence

            else:
                if seqs[i].sequence != seq_ids_unique[seqs[i].ID]: # Sequences differs
                    smooth = False
                    bad_ids.append(seqs[i].ID)                    
                else:
                    seqs.pop(i)
                    i -= 1
                    r += 1
            if not seqs[i].sequence in seqs_unique:
                seqs_unique[seqs[i].sequence] = True
            else:
                s += 1
                identical_seq_ids[seqs[i].ID] = True
            i += 1

        if len(identical_seq_ids) != 0:
            answer = tkMessageBox.askyesno("Filter identical sequences?", "We found %i sequences which are identical with some other sequence in alignment. Do you want to remove them?" % len(identical_seq_ids), icon = "question", parent = self)
            if answer == True:
                i = 0
                while i < len(seqs):
                    if seqs[i].ID in identical_seq_ids:
                        seqs.pop(i)
                        i -= 1
                        r += 1
                    i += 1                   

        self.seq_input_frame.text_widget.delete(1.0, tkinter.END)
        for s in seqs:
            self.seq_input_frame.text_widget.insert(tkinter.END, ">%s\n%s\n\n" % (s.name, s.sequence))

        curr_message = "Filtering of %i input sequences; %i sequences removed; %i remained\n" % (seq_size, r, len(seqs))
        if smooth:           
            self.host.set_status("Filtering gained success; %i sequences removed!" % r, self.host.header)
            curr_message += "Filtering gained success, all non-unique IDs removed\n"
        else:
            self.host.set_status("Filtering NOT gained success; see console for details!")
            print ("These sequences have duplicate IDs '%s' but different sequences; NOT removed:")
            curr_message += "Filtering NOT gained success, NOT all non-unique IDs removed; these remains:"
            for bad in bad_ids:
                print (bad)
                curr_message += "%s\n" % bad
        self.host.log_tab.write_to_log(curr_message, True)

    def align(self):        
        if self.seq_input_frame.text_is_empty(): # No sequences were provided
            self.host.set_status("No sequences were provided to align!", "#FF0000")
            return
        print ("    Alignment construction started...")
        (muscle_name, muscle_path) = Settings.get_program_name(self.host.settings.muscle_dir, "muscle")
        unaligned_filename = os.path.join(self.host.settings.work_dir, "%s.fasta" % self.host.temp_name)
        Aln_basic.write_widget_into_file(self.seq_input_frame.text_widget, unaligned_filename)
        aligned_filename = os.path.join(self.host.settings.work_dir, "%s.aln" % self.host.temp_name)

        self.host.set_status("Alignment")
        maxiters_option = ""
        if self.maxiters.get() != "":
            try:
                maxiters_option = "-maxiters %i" % int(self.maxiters.get())
            except TypeError:
                print ("Option -maxiters is not an integer and is ignored!")
        gapopen_option = ""
        if self.gapopen.get() != "":
            if Aln_basic.is_negative_float(self.gapopen.get(), "-gapopen"):
                gapopen_option = "-gapopen %s" % self.gapopen.get()
        gapextend_option = ""
        if self.gapextend.get() != "":
            if Aln_basic.is_negative_float(self.gapextend.get(), "-gapextend"):
                gapextend_option = "-gapextend %s" % self.gapextend.get()
        muscle_command = "%s -in %s -out %s %s %s %s" % (muscle_path, unaligned_filename, aligned_filename, maxiters_option, gapopen_option, gapextend_option)
        print ("Muscle command to be ran:")
        print (muscle_command)        
        if self.host.verbose.get():                     
            os.system(muscle_command)
        else:
            os.system("%s 1> nul 2> nul" % muscle_command)

        Aln_basic.read_widget_from_file(self.aln_input_frame.text_widget, aligned_filename)
        if self.insert_blocks.get(): # Empty sequence >BLOCKS should be added
            curr_seqs = Aln_basic.read_fasta_from_strings(self.aln_input_frame.get_strings())
            self.aln_input_frame.text_widget.delete(1.0, tkinter.END)
            upd_aln_file = open(aligned_filename, "w")            
            upd_aln_file.write(">BLOCKS\n")
            upd_aln_file.write("%s\n\n" % ("-" * len(curr_seqs[0].sequence)))
            upd_aln_file.write(">SITE\n")
            upd_aln_file.write("%s\n\n" % ("-" * len(curr_seqs[0].sequence)))
            for s in curr_seqs:
                s.print_fasta(upd_aln_file, 60)
            upd_aln_file.close()
            Aln_basic.read_widget_from_file(self.aln_input_frame.text_widget, aligned_filename)            
                    
        self.host.set_status("Ready")

        os.remove(unaligned_filename)
        os.remove(aligned_filename)
        print ("    [..DONE..]")

    def check_input(self):
        print ("    Checking input alignment...")
        if self.aln_input_frame.text_is_empty(): # No alignment is provided
            self.host.set_status("No alignment is provided!", "#FF0000")
        else:
            aligned_filename = os.path.join(self.host.settings.work_dir, "%s.aln" % self.host.temp_name)  
            Aln_basic.write_widget_into_file(self.aln_input_frame.text_widget, aligned_filename)    
            import udav_base
            try:
                seq_list = udav_base.read_alignment(aligned_filename)
                if type(seq_list) == type(""): # This means that at least one sequence in alignment differs in length from other
                    self.host.set_status(seq_list, "#FF0000")
                else:
                    status_OK = True
                    id_to_name = dict()
                    for s in seq_list:
                        s.remove_limits(False, False)                   
                        if s.ID in id_to_name: # Identical protein IDs detected
                            status_OK = False
                            print ("    [..WARNING..] Identical protein ID detected: '%s'" % s.ID)
                        id_to_name[s.ID] = s.name

                        my_format = re.match("^[^\|]+\|[^\|]+\|[^\|]+$", s.name)
                        my_format_simple = re.match("^[^\|]+\|[^\|]+$", s.name)
                        if not (my_format or my_format_simple) and not ((s.name == "BLOCKS") or (s.name == "SITE")):
                            status_OK = False
                            print ("    [..WARNING..] This name can fail a purification step. Consider 'My' format instead")
                            print ("    Current name: '%s'" % s.name)
                            print ("    'My' format example: 'ID|smth|organism' or 'ID|organism'")                           
                    if status_OK:
                        self.host.set_status("OK")
                    else:
                        self.host.set_status("Alignment has problems with names format, check console for details", "#888800")
            except IndexError:
                self.host.set_status("Alignment is corrupted; check that it is in FASTA format!", "#888800")
            del udav_base
            os.remove(aligned_filename)
        print ("    [..DONE..]")

    def save_alignment(self):
        aligned_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.aln" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.aln_input_frame.text_widget, aligned_filename, False)
  
    def save_sequence_sample(self):
        sequence_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.sample" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.seq_input_frame.text_widget, sequence_filename, False)

    def save_taxonomy_data(self):
        tax_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.tax" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.tax_input_frame.text_widget, tax_filename, False)

    def clear(self):
        self.seq_input_frame.text_widget.delete(1.0, tkinter.END)
        self.aln_input_frame.text_widget.delete(1.0, tkinter.END)
        self.tax_input_frame.text_widget.delete(1.0, tkinter.END)

    def apply_actions(self, ids_to_remove, ids_to_fix):
        print ("    Removement started...")
        seqs = None
        if self.seq_input_frame.text_is_empty():
            tkMessageBox.showwarning("Unaligned sequences are not provided", "Alnalyser cannot find unaligned sequences. They will be loaded from the alignment panel and unaligned. Consider building new alignment after this step!")
            seqs = Aln_basic.read_fasta_from_strings(self.aln_input_frame.get_strings(), True)
        else:
            seqs = Aln_basic.read_fasta_from_strings(self.seq_input_frame.get_strings())
            self.seq_input_frame.text_widget.delete(1.0, tkinter.END)
        reason_to_id = dict()
        r = 0

        no_org_remains = list()
        for s in seqs:
            if s.ID in ids_to_remove:
                curr_reason = ids_to_remove[s.ID][0]
                org_remains = ids_to_remove[s.ID][1]
                if not curr_reason in reason_to_id:
                    reason_to_id[curr_reason] = list()
                reason_to_id[curr_reason].append(s.ID)
                r += 1
                if not org_remains:
                    no_org_remains.append((s.ID, s.organism))
                self.host.log_tab.remove_log.text_widget.insert(tkinter.END, ">%s\n" % s.name)
                self.host.log_tab.remove_log.text_widget.insert(tkinter.END, s.sequence + "\n\n")
                continue
            self.seq_input_frame.text_widget.insert(tkinter.END, ">%s\n" % s.name)
            self.seq_input_frame.text_widget.insert(tkinter.END, s.sequence + "\n\n")

        curr_message = "Removement log: %i sequences removed from %i (%i remained)\n" % (r, len(seqs), len(seqs) - r)
        curr_message += self.host.purify_tab.get_curr_options()
        for reason in reason_to_id:
            curr_message += "Reason(s) - %s:\n" % reason
            for protein_id in reason_to_id[reason]:
                curr_message += "%s, " % protein_id
            curr_message = "%s\n" % (curr_message.strip(", "))
        curr_message += "\n"
        curr_message += "For %i removements no protein from this organism remained in the sample\n" % len(no_org_remains)
        for pair in no_org_remains:
            curr_message += "%s\t%s\n" % (pair[0], pair[1])
        self.host.log_tab.write_to_log(curr_message, True)

        print ("    [..DONE..] Total %i removes done (%i possible)" % (r, len(ids_to_remove.keys())))