# -*- coding: utf-8 -*-
import os
import tkinter
import tkinter.filedialog as tkFileDialog
import Aln_basic

class AlnFeatures(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.host = host
        self.p = self.host.p
        self.hmmresults_COG = None
        self.hmmresults_Pfam = None
        self.TMHMM_results = None 
        self.features = None

        self.evalue_threshold = None  # Entry for the -e option of <obtain_features.py>
        self.overlap_threshold = None # Entry for the -f option of <obtain_features.py>
        self.feature_mode = None      # Variable for the 'COG' or 'Pfam' mode
        self.unite_domains = None     # Variable for the boolean option to apply domain unite or not
        self.max_distance = None      # Entry for the parameter of domain uniting
        self.max_hmm_overlap = None   # Entry for the parameter of domain uniting
        
        self.create_UI()    

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")
        
        self.hmmresults_COG = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "HMMer (COG):", "")
        self.hmmresults_COG.button.grid_forget()
        central_panel.add(self.hmmresults_COG)

        self.hmmresults_Pfam = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "HMMer (Pfam):", "")
        self.hmmresults_Pfam.button.grid_forget()
        central_panel.add(self.hmmresults_Pfam)

        self.TMHMM_results = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "DeepTMHMM (.gff3):", "")
        self.TMHMM_results.button.grid_forget()
        central_panel.add(self.TMHMM_results)

        self.features = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                               "Resulting features:", "Save to file")
        self.features.button.configure(command = self.save_features)

        tkinter.Label(self.features.panel, text = "E-value threshold:").grid(row = 0, column = 2, sticky = "NSW")
        self.evalue_threshold = tkinter.Entry(self.features.panel, width = 8)
        self.evalue_threshold.insert(tkinter.END, "1e-5")
        self.evalue_threshold.grid(row = 0, column = 3, sticky = "NSW", padx = self.p, pady = self.p)           

        tkinter.Label(self.features.panel, text = "Overlap threshold (%):").grid(row = 0, column = 4, sticky = "NSW")
        self.overlap_threshold = tkinter.Entry(self.features.panel, width = 3)
        self.overlap_threshold.insert(tkinter.END, "5")
        self.overlap_threshold.grid(row = 0, column = 5, sticky = "NSW", padx = self.p, pady = self.p)

        self.unite_domains = tkinter.BooleanVar()
        c = tkinter.Checkbutton(self.features.panel, text = "Unite domains", variable = self.unite_domains)
        c.select()
        c.grid(row = 0, column = 6, sticky ="NSE", padx = self.p, pady = self.p)

        tkinter.Label(self.features.panel, text = "Max distance (aa):").grid(row = 0, column = 7, sticky = "NSW")
        self.max_distance = tkinter.Entry(self.features.panel, width = 5)
        self.max_distance.insert(tkinter.END, "50")
        self.max_distance.grid(row = 0, column = 8, sticky = "NSW", padx = self.p, pady = self.p)

        tkinter.Label(self.features.panel, text = "Max HMM overlap (%):").grid(row = 0, column = 9, sticky = "NSW")
        self.max_hmm_overlap = tkinter.Entry(self.features.panel, width = 3)
        self.max_hmm_overlap.insert(tkinter.END, "30")
        self.max_hmm_overlap.grid(row = 0, column = 10, sticky = "NSW", padx = self.p, pady = self.p)

        self.feature_mode = tkinter.StringVar()
        self.feature_mode.set("COG")
        radio = tkinter.Radiobutton(self.features.panel, text = "COG", variable = self.feature_mode, value = "COG")
        radio.grid(row = 0, column = 11, sticky = "NSW", padx = self.p, pady = self.p)
        radio = tkinter.Radiobutton(self.features.panel, text = "Pfam", variable = self.feature_mode, value = "Pfam")
        radio.grid(row = 0, column = 12, sticky = "NSW", padx = self.p, pady = self.p)

        obtain = tkinter.Button(self.features.panel, text = "Obtain", background = self.host.header, foreground = "#FFFFFF", command = self.obtain_features)
        obtain.grid(row = 0, column = 13, sticky = "NSW", padx = self.p, pady = self.p)
        central_panel.add(self.features)

        self.update_idletasks()
        central_panel.sash_place(0, 200, 1)
        central_panel.sash_place(1, 400, 1)
        central_panel.sash_place(2, 600, 1)

    def save_TMHMM(self, ask_filename = True):
        TMHMM_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.TMHMM" % self.host.get_project_name())
        if ask_filename:
            TMHMM_filename = tkFileDialog.asksaveasfilename(filetypes = (("Plain output of the TMHMM", "*.TMHMM"), ("All", "*.*")))
        Aln_basic.write_widget_into_file(self.TMHMM_results.text_widget, TMHMM_filename, ask_filename)

    def save_features(self, ask_filename = True):
        features_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.features" % self.host.get_project_name())
        if ask_filename:
            features_filename = tkFileDialog.asksaveasfilename(filetypes = (("Sequence features", "*.features"), ("All", "*.*")))
        Aln_basic.write_widget_into_file(self.features.text_widget, features_filename, ask_filename)    

    def obtain_features(self):
        print ("    Obtaining features...")
        curr_mode = self.feature_mode.get()
        domain_filename = os.path.join(self.host.settings.work_dir, "%s.domain_table" % self.host.temp_name)
        domain_not_empty = None
        if curr_mode == "COG":
            domain_not_empty = Aln_basic.write_widget_into_file(self.hmmresults_COG.text_widget, domain_filename)                
        else:
            domain_not_empty = Aln_basic.write_widget_into_file(self.hmmresults_Pfam.text_widget, domain_filename)
        fixed_filename = os.path.join(self.host.settings.work_dir, "%s.fixed" % self.host.temp_name)
        dom_filename = os.path.join(self.host.settings.work_dir, "%s.domain_info" % self.host.temp_name)
        Aln_basic.write_widget_into_file(self.host.parse_tab.fixed.text_widget, fixed_filename)

        obtain_features_path = os.path.join(self.host.settings.script_dir, "obtain_features.py")

        data_for_features = ""
        if domain_not_empty:
            data_for_features += "-p %s" % domain_filename
        if not self.TMHMM_results.text_is_empty():
            TM_filename = os.path.join(self.host.settings.work_dir, "%s.TMHMM" % self.host.temp_name)           
            Aln_basic.write_widget_into_file(self.TMHMM_results.text_widget, TM_filename)
            data_for_features += " -t %s" % TM_filename
        self.host.set_status("Working")
        features_filename = os.path.join(self.host.settings.work_dir, "%s.features" % self.host.temp_name)
        command = "%s -i %s -o %s %s -e %s -f %s --max_dist %s --max_hmm_overlap %s -d %s" % (obtain_features_path, 
                                                       fixed_filename, features_filename, data_for_features, 
                                                       self.evalue_threshold.get(), self.overlap_threshold.get(),
                                                       self.max_distance.get(), self.max_hmm_overlap.get(), dom_filename)        
        if self.unite_domains.get():
            command += " --unite"
        if not self.host.verbose.get():
            command += " 1> nul 2> nul"
        print ("Executing command: '%s'" % command)
        os.system(command)

        self.host.set_status("Ready")
        Aln_basic.read_widget_from_file(self.features.text_widget, os.path.join(self.host.settings.work_dir, "%s.features" % self.host.temp_name))
        
        if os.path.isfile(dom_filename): # File was created (non-empty domains)
            domain_dict = Aln_basic.read_domain_info_file(dom_filename)
            self.host.load_domain_info(domain_dict) # Loading domain info into the info tab
        print ("    [..DONE..]")  

    def clear(self):
        self.hmmresults_COG.text_widget.delete(1.0, tkinter.END)
        self.hmmresults_Pfam.text_widget.delete(1.0, tkinter.END)
        self.TMHMM_results.text_widget.delete(1.0, tkinter.END)
        self.features.text_widget.delete(1.0, tkinter.END)