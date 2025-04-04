import sys, os, argparse
import udav_align, udav_base
import re

#========================================================================================
curr_version = 2.95
parser = argparse.ArgumentParser(description = 
"This script will remove additional info on sequence range (added by Jalview) and obtain blocks. \
Blocks should be in one of the sequences with the name 'BLOCKS' and marked with B letter. \
Also can filter sequences by their identity and use sequences with the name 'SITE' for this. \
Classes related to alignments are separated to 'udav_align' module. \
Current version is %s" % curr_version 
)
parser.add_argument("-i", help = "Alignment file", required=True, dest = "input_file")
parser.add_argument("-o", help = "Prefix for the output files", required = True, dest = "output")
parser.add_argument("-s", help = "Threshold to do sampling by sequence identity", required = False, dest = "sample_value")
parser.add_argument("-b", help = "Calculate identity in the blocks regions only", action = "store_true", default = False, dest = "blocks_only")
parser.add_argument("-f", help = "Name of file with correct organism names", required = False, dest = "org_file")
parser.add_argument("-l", help = "If names were long, do it other way", action = "store_true", default = False, dest = "long_names")
parser.add_argument("-d", help = "Delete BLOCKS and SITE sequences", action = "store_true", default = False, dest = "delete")
parser.add_argument("-e", help = "Give here the name of file with taxonomy correspondence (Uniprot only!)", required = False, dest="expand")
parser.add_argument("-x", help = "Use this if ids only should be printed to the fixed file", action = "store_true", default = False, dest = "id_only")
parser.add_argument("-r", help = "Motif in the sequences marked by the additional FILTER which will be taken", required = False, dest = "seq_filter")
parser.add_argument("-m", help = "Motifs in the sequence will be colored as separate letters, enter threshold percentage here", required = False, dest = "motif_std")
myargs = parser.parse_args()
#========================================================================================

motif_is_std = False
if myargs.motif_std != None:
    motif_is_std = True
else:
    myargs.motif_std = 0
####
# 1) Reading input file
####
print ("Script <remove_seq_limits.py> is working with %s file" % myargs.input_file)
seq_list = udav_base.read_alignment(myargs.input_file)
####
# 2) Cutting SITE and BLOCKS sequences
####
blocks_seq = None
blocks_string = None
filter_positions = list() # FIX: version 2.7 (list of the position in FILTER sequence)
prev_sym = "-"
site_seq = None
site_positions = list()
mult_site_positions = dict()
output_blocks = open (myargs.output + ".blocks", "w")
a = 0
n = 0
initial_seq_number = len(seq_list)
duplicate_search = dict() # FIX: version 2.6
while a < len(seq_list):
    s = seq_list[a]
    prev_name = s.name
    if not s.ID in duplicate_search:
        duplicate_search[s.ID] = False
    else:
        duplicate_search[s.ID] = True   
    s.remove_limits(myargs.long_names)
    if s.name != prev_name:
        n += 1
    if myargs.org_file == None:
        s.prepare_organism()

    if s.name == "BLOCKS":
        print ("BLOCKS string found!")
        blocks_string = ""
        for i in range(len(s.sequence)): #FIX 2.9: Not only 'B' and 'C' are considered
            if (s.sequence[i] != "-") and (prev_sym == "-"):
               blocks_string += str(i + 1)
               prev_sym = s.sequence[i]
            if (s.sequence[i] == "-") and (prev_sym != "-"):
               blocks_string += ".." + str(i) + ","
               prev_sym = "-"
        blocks_string = blocks_string.strip(",")
        output_blocks.write(blocks_string + "\n")
        blocks_seq = seq_list.pop(a)        
        blocks_seq.name = s.name
        a -= 1  
    if s.name == "SITE":
        print ("SITE string found!")
        site_positions = udav_align.get_positions(s) #-- Difference in these create immunity to fitler
        mult_site_positions = udav_align.get_multiple_positions(s, motif_is_std)
        site_seq = seq_list.pop(a)
        site_seq.name = s.name
        a -= 1
    if s.name == "FILTER":
        print ("FILTER string found!")
        for i in range(len(s.sequence)):
            if s.sequence[i] != "-": # Non-gap symbol found
                filter_positions.append(i)
        seq_list.pop(a) 
        a -= 1
    a += 1
output_blocks.close()

if myargs.seq_filter != None:
    filter_file = open("%s.%s.filter" % (myargs.input_file, myargs.seq_filter), "w")
    myargs.seq_filter = myargs.seq_filter.replace("x", ".")
    print ("Inputed filter: %s" % myargs.seq_filter)
    print ("Found positions: %s" % filter_positions)
    if len(myargs.seq_filter) < len(filter_positions):
        print ("FATAL ERROR: sequence filter inputed does not match FILTER string data!")
        sys.exit()
    a = 0
    while a < len(seq_list):    
        curr_motif = ""
        for p in filter_positions:
            curr_motif += seq_list[a].sequence[p]
        find_matches = re.findall(myargs.seq_filter, curr_motif)
        #print seq_list[a].ID + " " + str(find_matches) + " " + curr_motif
        if len(find_matches) != 0:
            curr_seq = seq_list.pop(a)
            filter_file.write(">%s\n%s\n\n" % (curr_seq.name, curr_seq.sequence))
            a -= 1
        a += 1
    filter_file.close()
        
####
# 3) Filtering sequences by their identity (under -s option)
####
if myargs.sample_value != None:
    matrix_filename = myargs.output + ".id_matrix"
    if myargs.blocks_only == True:
        vertex_list = udav_align.Identity_graph (seq_list, float(myargs.sample_value), blocks_string, matrix_filename)
    else:
        vertex_list = udav_align.Identity_graph (seq_list, float(myargs.sample_value), None, matrix_filename)

    vertex_list.print_graph(myargs.output + ".graph")
    vertex_list.proceed_graph(seq_list, myargs.output + ".report", site_positions)
                                           
####
# 4) Creating organism list (under -f option)
####
correct_orgs = None
if myargs.org_file != None:
    correct_orgs = dict()
    org_file = open (myargs.org_file)
    print ("The following organism name replacements will take place:")
    for string in org_file:
        string = string.strip()
        string = string.replace(" ", "_")
        if string.count("/") != 0:
           correct_orgs[string.split("/", 1)[0]] = string
           print ("%s\t=>\t%s" % (string.split("/", 1)[0], string))
    org_file.close()

####
# 5) Reading organism expansion file (under -e option)
####
expanded_orgs = None
if myargs.expand != None:
    expanded_orgs = dict()
    expansion = open (myargs.expand, "r")
    for string in expansion:
         string = string.strip()
         if len(string) == 0:
             continue
         if string[0] != "#":
             fields = string.split("\t")
             if len(fields) != 2:
                 print ("FATAL ERROR: number of fields is wrong (%i), expecting 2!" % len(fields))
                 sys.exit()
             fields[0] = fields[0].strip()
             fields[1] = fields[1].strip()
             expanded_orgs[fields[0]] = fields[1]
    expansion.close()

####
# 6) Printing output
####
output_file = open (myargs.output + ".fixed", "w")
if myargs.delete == False:
    if blocks_seq != None:
        output_file.write(">%s\n%s\n\n" % (blocks_seq.name, blocks_seq.sequence))   
    if site_seq != None:
        output_file.write(">%s\n%s\n\n" % (site_seq.name, site_seq.sequence))   

o = 0
output_ids = open(myargs.output + ".ids", "w")
output_ngphylogeny = open(myargs.output + ".ngphylogeny", "w")
output_orgs = open(myargs.output + ".orgs", "w")
for s in seq_list:
    req_name = s.correct_organism (correct_orgs, expanded_orgs)
    output_ids.write ("%s\n" % s.ID)
    if len (req_name.split("|", 1)) != 1:
        org_name = req_name.split("|", 1)[1]
        org_name = org_name.replace("_", " ")
        output_orgs.write("%s\n" % org_name)
    #if myargs.id_only == True:
    #    req_name = s.ID
    output_file.write(">%s\n%s\n\n" % (req_name, s.sequence))
    id_part = req_name.split("|", 1)[0] # FIX: version 2.95 (NGPhylogeny stupid replacement tracked)
    ngphylogeny_name = re.sub("[^A-Za-z0-9\-_]", "-", req_name)
    output_ngphylogeny.write("%s\t%s\t%s\n" % (id_part, req_name, ngphylogeny_name))
    if s.name != req_name:
        o += 1
output_file.close()
output_ids.close()
output_ngphylogeny.close()
output_orgs.close()

udav_base.print_pure_sequences(seq_list, myargs.output + ".pure", myargs.id_only, True)
udav_align.print_multiple_positions(mult_site_positions, myargs.output + ".motif")
udav_align.print_motif_variants(seq_list, mult_site_positions, myargs.output + ".motif_var", motif_is_std, float(myargs.motif_std))
if blocks_seq != None:
    udav_align.print_blocks_regions(seq_list, blocks_string, myargs.output + ".blocks_regions")

print ("DONE! %i cases of JalView bugs fixed (out of total %i sequences)" % (n, initial_seq_number))
print ("Also %i cases of organism names fixed (out of resulting %i sequences)" % (o, len(seq_list)))

####
# 7) Warining about names duplicates - FIX: version 2.6
####
n = 0
for protein_ID in duplicate_search.keys():
    if duplicate_search[protein_ID] == True:
        n += 1
if n != 0:
    print ("\nIMPORTANT WARNING: your alignment contains %i protein_ids which are duplicated.\n\
                                 This will likely cause problems afterwards, please remove them\n\
                                 prior to further analysis and re-run this script!" % n)
    for protein_ID in duplicate_search.keys():
        if duplicate_search[protein_ID] == True:
            print (protein_ID)
