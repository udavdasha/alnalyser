# -*- coding: utf-8 -*-
import os, re, time
import Tkinter as tkinter
import ttk
import Aln_basic

class AlnLog(tkinter.Frame):
    def __init__(self, parent, host):
        tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.host = host
        self.p = self.host.p
        self.auto_log = None     # Frame for the automatically generated log
        self.manual_log = None   # Frame for the user-generated log
        self.wrap_auto = None    # tkinter boolean value for the wrapping of the text in the <self.auto_log>
        self.wrap_manual = None  # tkinter boolean value for the wrapping of the text in the <self.manual_log>

        self.create_UI()

    def create_UI(self):
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        central_panel = tkinter.PanedWindow(self, orient = tkinter.HORIZONTAL, sashwidth = self.p * 2, sashrelief = tkinter.RIDGE, background = self.host.back)
        central_panel.grid(row = 0, column = 0, sticky = "NSEW")

        self.auto_log = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                        "Automatically generated log:", "")
        self.auto_log.button.grid_forget()
        self.auto_log.text_widget.tag_configure("important", background = "#FFFF00")
        self.wrap_auto = tkinter.BooleanVar()
        c = tkinter.Checkbutton(self.auto_log.panel, text = "Wrap text", variable = self.wrap_auto, command = self.wrap_configure)
        c.grid(row = 0, column = 1, sticky ="NSE", padx = self.p, pady = self.p)
        central_panel.add(self.auto_log)

        self.manual_log = Aln_basic.TextFrameWithLabelAndButton(central_panel, self.p, None, None, 
                        "Manually generated log:", "")
        self.manual_log.button.grid_forget()
        self.wrap_manual = tkinter.BooleanVar()
        c = tkinter.Checkbutton(self.manual_log.panel, text = "Wrap text", variable = self.wrap_manual, command = self.wrap_configure)
        c.grid(row = 0, column = 1, sticky ="NSE", padx = self.p, pady = self.p)
        central_panel.add(self.manual_log)

    def write_to_log(self, message, is_important = False):
        self.auto_log.text_widget.insert(tkinter.END, "\n\n")   
        t = time.localtime()
        time_string = "%02i.%02i.%i\t%02i:%02i:%02i" % (t.tm_mday, t.tm_mon, t.tm_year, t.tm_hour, t.tm_min, t.tm_sec)
        if is_important:
            time_string += " [IMPORTANT]"
        self.auto_log.text_widget.insert(tkinter.END, "%s\n" % time_string)
        if is_important:            
            start = self.auto_log.text_widget.search(time_string, 1.0, stopindex = tkinter.END)
            end = '%s+%dc' % (start, len(time_string))
            self.auto_log.text_widget.tag_add("important", start, end)
        self.auto_log.text_widget.insert(tkinter.END, "%s\n" % message)       

    def color_important(self):
        start = "1.0"
        while True:
            hit_position = self.auto_log.text_widget.search("[IMPORTANT]", start, stopindex = tkinter.END)
            if not hit_position:
                break
            end_position = '%s+%dc' % (hit_position, len("[IMPORTANT]"))
            self.auto_log.text_widget.tag_add("important", hit_position, end_position)                               
            start = end_position

    def get_current_project_state(self):
        seq_n = self.host.input_tab.seq_input_frame.count_fasta()
        aln_n = self.host.input_tab.aln_input_frame.count_fasta()
        aln_length = self.host.parse_tab.fixed.count_seq_length()
        final_num = self.host.parse_tab.pure.count_fasta()
        blocks_length = self.host.parse_tab.blocks.count_seq_length()
        curr_message = "Number of unaligned input sequences: %i\n" % seq_n
        curr_message += "Number of aligned input sequences: %i\n" % aln_n
        curr_message += "Number of positions in the alignment: %s\n" % aln_length
        curr_message += "------------------------------------\n"
        curr_message += "Number of positions in the blocks: %s\n" % blocks_length
        curr_message += "Number of informative sequences for tree construction: %s\n" % final_num
        self.write_to_log(curr_message, True)

    def write_histogram(self, values, info_string, begin, step, nsteps):        
        pos = begin
        result = list()
        n = 0      
        for v in values:
            if v < begin:
                n += 1
        result.append((n, "< %s" % begin))
        while pos < begin + (step * nsteps):
              part_begin = pos
              part_end = pos + step
              n = 0
              for v in values:
                  if (v >= part_begin) and (v < part_end):
                      n += 1
              result.append((n, "[%s; %s)" % (part_begin, part_end)))              
              pos += step
        n = 0
        for v in values:
            if v >= (begin + (step * nsteps)):
                n += 1
        result.append((n, ">= %s" % (begin + (step * nsteps))))

        curr_message = "%s\n" % info_string
        check = 0        
        for r in result:
            curr_message += "%i\t%s\n" % (r[0], r[1])
            check += r[0]
        if check != len(values):
            curr_message += "[..WARNING..] Number of given values: %i; summ of histogram: %i\n" % (len(values), check)
        self.write_to_log(curr_message)
          
    def wrap_configure(self):
        if self.wrap_auto.get() == False:
            self.auto_log.text_widget.configure(wrap = tkinter.NONE)
        else:
            self.auto_log.text_widget.configure(wrap = tkinter.WORD)

        if self.wrap_manual.get() == False:
            self.manual_log.text_widget.configure(wrap = tkinter.NONE)
        else:
            self.manual_log.text_widget.configure(wrap = tkinter.WORD)

    def save_logs(self, ask_if_exists = True):
        auto_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.auto_log" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.auto_log.text_widget, auto_filename, ask_if_exists, True)

        man_filename = os.path.join(self.host.settings.work_dir, self.host.get_project_name(), "%s.man_log" % self.host.get_project_name())
        Aln_basic.write_widget_into_file(self.manual_log.text_widget, man_filename, ask_if_exists, True)

    def clear(self):
        self.auto_log.text_widget.delete(1.0, tkinter.END)
        self.manual_log.text_widget.delete(1.0, tkinter.END)