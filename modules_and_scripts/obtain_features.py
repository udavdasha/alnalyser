#!/usr/bin/env python
import sys, os, argparse
import udav_align, udav_base, udav_soft

#========================================================================================
curr_version = 1.6
parser = argparse.ArgumentParser(description = 
"This script will obtain features file for given alignment (Pfam + TMHMM in this version) \
Current version is %s" % curr_version 
)
parser.add_argument("-i", help = "Name of the alignment (name = ID is expected)", required = True, dest = "input_file")
parser.add_argument("-w", help = "Name of working directory (use . to work where you run script)", required=True, dest = "work_dir")
parser.add_argument("-o", help = "Name of the output feature file", required = True, dest ="output_file")
parser.add_argument("-t", help = "Name of TMHMM result for given file (one line per protein)", required = False, dest = "TMHMM")
parser.add_argument("-l", help = "Letters of amino acids which should be added as features (string)", required = False, dest = "letters")
parser.add_argument("-p", help = "Name of HMMer output for Pfam database (result of -domtblout option)", required = False, dest = "Pfam")
parser.add_argument("-e", help = "Give here global domain e-value threshold (DEFAULT = 1.0)", required = False, dest = "evalue")
parser.add_argument("-f", help = "If domain filtering required, give here threshold for overlap in percent", required = False, dest = "filter_thresh")
parser.add_argument("-c", help = "Give here file with name correspondence to replace and sort input file", required = False, dest = "correspond")
parser.add_argument("-s", help = "File with color scheme (required if -c is used)", required = False, dest = "scheme")
parser.add_argument("-r", help = "If names in the input should not be changed, enter this option", required = False, action = "store_false", dest = "replace")
parser.add_argument("-d", help = "Name of output file with information about the domains found (if required)", required = False, dest = "domain_filename")
                                                                                                                                       
myargs = parser.parse_args()
[myargs.work_dir, myargs.input_file, myargs.output_file, myargs.TMHMM, myargs.Pfam, myargs.correspond, myargs.scheme, myargs.domain_filename] = udav_base.proceed_params([myargs.work_dir, myargs.input_file, myargs.output_file, myargs.TMHMM, myargs.Pfam, myargs.correspond, myargs.scheme, myargs.domain_filename])
if myargs.evalue == None:
    myargs.evalue = 1.0
myargs.evalue = float(myargs.evalue)
filter_on = False
if myargs.filter_thresh != None:
    myargs.filter_thresh = float(myargs.filter_thresh)
    filter_on = True
#========================================================================================
def get_letter_features(sequence, letters):
    no_gaps = sequence.replace("-", "")
    letter_features = ""
    for l in letters:
        addition = ""
        for i in range(len(no_gaps)):
            if no_gaps[i] == l:
                addition += "%s," % (i + 1)
        addition = addition.strip(",")
        if addition != "":
            letter_features += "[%s] " % l        
            letter_features += addition
            letter_features += "\t"
    letter_features = letter_features.strip("\t")
    return letter_features
    
alignment = udav_base.read_alignment(myargs.input_file)

TMHMM_result = None
if myargs.TMHMM != None:
    TMHMM_result = udav_soft.read_TMHMM_output(myargs.TMHMM)

Pfam_result = None
if myargs.Pfam != None:
    (Pfam_result, domains) = udav_soft.read_Pfam_output(myargs.Pfam, myargs.evalue, filter_on, myargs.filter_thresh)
    if myargs.domain_filename != None:
        domain_file = open(myargs.domain_filename, "w")
        for domain in domains.keys():
            curr_domain = domains[domain]
            domain_file.write("%s\t%s\t%s\n" % (curr_domain.name, curr_domain.ac, curr_domain.description))
        domain_file.close()

output = open(myargs.output_file, "w")
for s in alignment:  
    s.remove_limits(False, myargs.replace)
    output.write("%s" % s.ID)
    if TMHMM_result != None:
        if s.ID in TMHMM_result:
            output.write("\t%s" % TMHMM_result[s.ID])
    if Pfam_result != None:
        if s.ID in Pfam_result:
            output.write("\t%s" % Pfam_result[s.ID])
    if myargs.letters != None:
        letters_result = get_letter_features(s.sequence, myargs.letters)
        output.write("\t%s" % letters_result)
    output.write("\n")
output.close()
    
if myargs.correspond != None:  
    color_scheme = udav_soft.read_color_file(myargs.scheme)
    complete_alignment = udav_base.get_featured (myargs.input_file, myargs.correspond, myargs.output_file, dict(), color_scheme, True)
    sorted_alignment = udav_base.sort_by_features(complete_alignment)
    debug = open("_SORT_DEBUG.txt", "w")
    for s in sorted_alignment:
        curr_domains = s.get_features_order()
        debug.write(curr_domains + "\n")
    debug.close()
    udav_base.print_pure_sequences(sorted_alignment, myargs.input_file, False, False)
