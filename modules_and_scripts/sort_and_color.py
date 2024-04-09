#!/usr/bin/env python
import sys, os, argparse, re
import udav_fasta, udav_base, udav_tree_svg, udav_soft

#========================================================================================
curr_version = 4.6
parser = argparse.ArgumentParser(description = 
"This script will kill two rabbits: it (1) color tree according to the coloring rules and \
(2) sorts input alignment file by the order of the given tree. Can also identify and mark isoforms. \
Current version is %s" % curr_version 
)
parser.add_argument("-i", help = "Name of the alignment file", required = False, dest = "input_align")
parser.add_argument("-y", help = "   Toggle this to work not with the alignment but with URef format sequences", action = "store_true", dest = "yes_sample")
parser.add_argument("-t", help = "Name of the tree file (svg format)", required = True, dest = "input_tree")
parser.add_argument("-o", help = "Prefix for the output files", required = True, dest ="output")
parser.add_argument("-c", help = "-- For coloring: File with the coloring", required = False, dest ="colors")
parser.add_argument("-a", help = "-- For coloring: name of the id to taxonomy assignment (fasta file or table)", required = False, dest = "assign")
parser.add_argument("-f", help = "-- For coloring: Format (URef or My_Ref) if fasta file is given", required = False, dest = "format")
parser.add_argument("--add_assign", help = "-- Additional id to taxonomy assignment file (URef)", required = False, dest = "add_assign")
parser.add_argument("-u", help = "Use this option if SwissProt sequence names should be enlarged", action = "store_true", dest = "uniprot")
parser.add_argument("-m", help = "Chouse if alignment contains more sequences then tree and they should be added", action = "store_true", dest = "more")
parser.add_argument("-n", help = "Chouse if 'no-name' tree file should be printed", action = "store_true", dest = "no_names")
parser.add_argument("-s", help = "If 'no-name' tree file is printed, give here new stroke size (OPTIONAL)", required = False, dest = "stroke")
parser.add_argument("-b", help = "If search and marking of isoforms should be done, give here URef format file", required = False, dest = "bank_isoform")
parser.add_argument("-g", help = "File with classification of IDs into groups", required = False, dest = "group")
parser.add_argument("-j", help = "If -g option is used, this is required. Give color scheme for groups", required = False, dest = "group_color")
parser.add_argument("-l", help = "Use this option if no legend should be printed", action = "store_false", dest = "legend_draw")
parser.add_argument("-r", help = "To remove bootstraps give 'remove'; to replace with circles give here a string in format 'g_p_s', where <g> is a limit value for bootstrap to print filled circle, <p> to print opened circles in [p; g] and <s> for a size of the circle", required = False, dest = "remove_bootstrap")
parser.add_argument("-x", help = "Mark proteins with given mark (e.g., 'COG0001') with bold", required = False, dest = "mark_bold")
parser.add_argument("-p", help = "Print plain id list as found on the tree", action = "store_true", required = False, dest = "plain_list")
parser.add_argument("-z", help = "If tree contains gi, give here file with the assignment gi->id (.table format)", required = False, dest = "gi_to_id_filename")
myargs = parser.parse_args()
color_file_path = "D:\\UdavBackup\\_Complete_genomes\\_scripts\\udav_color_taxonomy.txt"
if myargs.colors != None:
    color_file_path = myargs.colors
if myargs.remove_bootstrap == None:
    myargs.remove_bootstrap = False
elif myargs.remove_bootstrap == "remove":    
    myargs.remove_bootstrap = True
#========================================================================================

def read_direct_tax_assignment(assign_filename, id_to_taxonomy, short_id_to_taxonomy):
    """
    Reads <assign_filename> and fills <id_to_taxonomy> and <short_id_to_taxonomy>
    with values from it
    """
    assign_file = open(assign_filename, "r")
    for string in assign_file:
        string = string.strip()
        if len(string) == 0:
            continue
        if string[0] == "#":
            continue
        fields = string.split("\t", 1)
        if len (fields) < 2:
            print ("WARNING: Error in the taxonomy assignment file!")
            print (string)
            print (fields)
        else:
            id_to_taxonomy[fields[0]] = fields[1].split("\t") # FIX version 3.85
            fields[0] = fields[0].split(".", 1)[0] # FIX version 1.4: protein_ids are operated normally
            id_to_taxonomy[fields[0]] = fields[1].split("\t") 
            first_id_part = fields[0].split("_", 1)[0]
            if (first_id_part != fields[0]) and (len(first_id_part) > 4): # Not the same and not SwissProt (e.g. CRP_ECOLI)
                short_id_to_taxonomy[first_id_part] = fields[1].split("\t") 
    assign_file.close()  

#----------- 1) Tree reading
print ("Reading tree file from .svg picture...")
(file_strings, text_tags, path_tags) = udav_tree_svg.read_svg_file(myargs.input_tree)
#text_tags_keys = list(text_tags.keys())
#text_tags_keys = sorted(text_tags_keys, key=lambda k:float(text_tags[k].features["y"])) #FIX: version 4.5
print ("\tDONE! Found %i text tags" % len(text_tags.keys()))

leaves = 0
for key in text_tags.keys():
    if text_tags[key].is_leaf():
        leaves += 1
print ("Number of tree leaves: %i" % leaves)

if myargs.gi_to_id_filename != None: #FIX 4.1: another mode (not coloring, but replacing of GIs)
    GI_to_ID = None
    GI_to_locus = None
    print ("Changing type of ID in .svg...")
    (GI_to_ID, GI_to_locus, gi_dupl, non_unique) = udav_soft.read_protein_table_info(myargs.gi_to_id_filename)
    n = 0
    for key in text_tags.keys():
        curr_id = text_tags[key].get_seq_id(False)        
        if curr_id in GI_to_locus:
            n += 1
            text_tags[key].content = text_tags[key].content.replace(curr_id, GI_to_locus[curr_id])
    print ("Total %i replacements made!" % n)
    udav_tree_svg.print_svg_file(myargs.output + "_replaced.svg", file_strings, text_tags, path_tags, None, None, None, myargs.remove_bootstrap)

if myargs.assign != None: #----------- 1a) Changing text tags (coloring)    
    print ("Reading taxonomy colors...")
    (taxonomy_colors, taxa_order) = udav_tree_svg.read_taxonomy_colors(color_file_path)
    if myargs.legend_draw:
        udav_tree_svg.print_simple_legend(taxonomy_colors, taxa_order, myargs.output + ".tax_legend")
    print ("\tDONE!")
    id_to_taxonomy = dict()
    short_id_to_taxonomy = dict() #FIX 3.3: considering case of non-complete IDs: not W9Y1V1_9EURO, but W9Y1V1 (Uniprot only)
    if myargs.format != None:
        print ("Reading fasta file with long names...")
        (long_names, l_not_found) = udav_fasta.read_fasta(myargs.assign, None, None, dict(),
                                           100, False, None, None, None, None, myargs.format)
        print ("\tDONE; %i sequences found!" % len(long_names))
        for s in long_names:
            prot_id = s.get_proper_protein_id()            
                
            #id_hash_long[prot_id.split(".")[0]] = s
            #gi_hash_long[s.gi] = s
            curr_taxonomy = s.taxonomy.split("; ")

            id_to_taxonomy[s.locus] = curr_taxonomy
            id_to_taxonomy[prot_id.split(".")[0]] = curr_taxonomy
            id_to_taxonomy[s.gi] = curr_taxonomy
    else:
        print ("Reading direct assignment of id to taxonomy (at least domain and phylum depth)...")
        #FIX: 4.0 <myargs.assign> could be either file or a directory with a number of files
        if os.path.isfile(myargs.assign):
            read_direct_tax_assignment(myargs.assign, id_to_taxonomy, short_id_to_taxonomy)
        elif os.path.isdir(myargs.assign):
            files = os.listdir(myargs.assign)
            f_n = 0
            for f in files:
                f_n += 1
                filename = os.path.join(myargs.assign, f)
                print ("File %s (%i out of %i)" % (f, f_n, len(files)))
                read_direct_tax_assignment(filename, id_to_taxonomy, short_id_to_taxonomy)
        else:
            print ("FATAL ERROR: '%s' is not a file or directory!" % myargs.assign)
            sys.exit()
    if myargs.add_assign != None: # FIX: version 4.5
        (add_long_names, add_l_not_found) = udav_fasta.read_fasta(myargs.add_assign, None, None, dict(),
                                           100, False, None, None, None, None, "URef")
        for s in add_long_names:
            prot_id = s.get_proper_protein_id()
            curr_taxonomy = s.taxonomy.split("; ")
            if not s.locus in id_to_taxonomy:
                id_to_taxonomy[s.locus] = curr_taxonomy
            if not prot_id.split(".")[0] in id_to_taxonomy:
                id_to_taxonomy[prot_id.split(".")[0]] = curr_taxonomy
            if not s.gi in id_to_taxonomy:
                id_to_taxonomy[s.gi] = curr_taxonomy

    isoforms = dict() # Dictionary of protein ID to an isoform label # FIX version 3.0
    if myargs.bank_isoform != None:
        req_proteins = dict()
        for text_id in text_tags.keys():
            if text_tags[text_id].is_leaf:
                protein_id = text_tags[text_id].get_seq_id(False)
                req_proteins[protein_id] = True
        print ("Obtaining isoform data...")
        isoforms = udav_fasta.get_isoform_data(myargs.bank_isoform, req_proteins, "GI", "%s.isoforms" % myargs.output)
        print ("DONE; %i proteins assigned to isoform groups" % len(isoforms.keys()))

    print ("Changing colors in .svg...")
    n = 0
    m = 0
    for key in text_tags.keys():
        text_tags[key].stroke_off() # FIX 3.4: stroke should be turned off
        curr_id = text_tags[key].get_seq_id(False)
        before_version_part = curr_id.split(".", 1)[0] # FIX 4.0: if version (xxxx.1) is omitted in taxonomy data
        first_part = curr_id.split("_", 1)[0]
        curr_id = curr_id.split("-", 1)[0]        
        if (curr_id in id_to_taxonomy) or (first_part in short_id_to_taxonomy) or (before_version_part in id_to_taxonomy):
            if curr_id in id_to_taxonomy:
                curr_taxonomy = id_to_taxonomy[curr_id]
                #id_to_taxonomy.pop(curr_id)   
            elif first_part in short_id_to_taxonomy:
                curr_taxonomy = short_id_to_taxonomy[first_part] #FIX 3.3: case of non-complete IDs: not W9Y1V1_9EURO, but W9Y1V1 (Uniprot only?)
                #short_id_to_taxonomy.pop(first_part)   
            else:
                curr_taxonomy = id_to_taxonomy[before_version_part] #FIX 4.0
                #id_to_taxonomy.pop(before_version_part)   

            if (curr_taxonomy[0] == "Viruses"):
                phylum = curr_taxonomy[0]
            else:
                if len(curr_taxonomy) < 2:
                    phylum = curr_taxonomy[0] # Nothing but domain is specified
                else:    
                    phylum = curr_taxonomy[1] # Trying to use phylum info
                    if not phylum in taxonomy_colors:
                        phylum = curr_taxonomy[0]

            if phylum in taxonomy_colors:
                new_color = taxonomy_colors[phylum]
                text_tags[key].change_text_color(new_color)                

                if myargs.uniprot: # Only works with Uniprot!
                    first_part = curr_id.split("_", 1)[0]
                    first_part_len = len(first_part)
                    first_part_is_numeric = False #FIX 3.2: 123 is not counted as "unusual"
                    try:
                        first_part = int(first_part)
                        first_part_is_numeric = True
                    except:
                        pass
                    curr_id_in_caps = (curr_id == curr_id.upper())            
                    if (first_part_len < 5) and (first_part_len != 2) and not("scale" in curr_id) and not(first_part_is_numeric) and curr_id_in_caps: #FIX 1.3: YP_... is not colored; changing for SwissProt; FIX: 4.4 iTOL Tree_scale considered
                        text_tags[key].change_font("Arial", 10, True)                
                #text_tags[key].change_font("Courier New", 12)                
                #text_tags[key].content = curr_id + " " + seq_long.organism
                n += 1
            else:
                print ("WARNING: no color found for phylum '%s'!" % phylum)
        else:
            if text_tags[key].content.strip() in taxonomy_colors:
                print ("Found taxonomy name in the file (%s), not changing..." % text_tags[key].content.strip())
            elif "Tree_scale" in curr_id: #FIX 4.4: iTOL output considered too
                print ("Label '%s' is technical and will not be considered" % curr_id)
            elif len(text_tags[key].content) > 5:
                new_color = taxonomy_colors["Unknown"]
                text_tags[key].change_text_color(new_color)
                try: #FIX 3.6: This is to detect PDB identifiers like '2cgp_A|Escherichia coli'
                    first_part = curr_id.split("_", 1)[0]
                    second_part = curr_id.split("_")[1].split("|", 1)[0]                    
                    if (len(first_part) == 4) and (len(second_part) == 1):
                        text_tags[key].change_font("Arial", 12, True)
                except:
                    pass                   
                print ("WARNING: no color info found for id '%s'; default color using!" % curr_id)
                print ("         Possible cause of error: duplicate IDs in the input file!")
                m += 1

        if isoforms != None: # Isoform data will be added, if any, to the content
            if curr_id in isoforms:
                isoform_data = "[%s]" % isoforms[curr_id]
                text_tags[key].content = "%s %s" % (isoform_data, text_tags[key].content)

        if myargs.mark_bold != None: # Marking with bold
           if re.search("\|%s\|" % myargs.mark_bold, text_tags[key].content) != None:
               text_tags[key].change_font(None, None, True)
           

    print ("\tDONE!")
    print ("Made %i replacements (%i missing)" % (n, m))

    group = None
    group_color = None
    if myargs.group != None:
        group = udav_soft.read_group_file(myargs.group)
        (group_color, group_list) = udav_soft.read_color_file(myargs.group_color, False)
        print ("Group file red; total %i proteins assigned to some group" % len(group.keys()))
        for c in group_color.keys():
            colors = group_color[c].replace("rgb", "").strip("()").split(",")
            group_color[c] = (int(colors[0]), int(colors[1]), int(colors[2]))
    udav_tree_svg.print_svg_file(myargs.output + "_colored.svg", file_strings, text_tags, path_tags, None, group, group_color, myargs.remove_bootstrap)
    if myargs.no_names:
        print ("'No-name' file will be created now! Setting new stroke size: %s" % myargs.stroke)
        print ("Building graph...")
        graph = udav_tree_svg.Graph_path_svg(path_tags, 1.5)
        print ("Coloring branches of the leaves...")
        graph.color_leaves(text_tags, 10.0)
        print ("Coloring other part of the tree...")
        graph.color_parents()
        if myargs.stroke != None:
            graph.set_size(float(myargs.stroke))
        udav_tree_svg.print_svg_file(myargs.output + "_noname.svg", file_strings, text_tags, path_tags, myargs.no_names, group, group_color, myargs.remove_bootstrap)

ordered_ids = udav_tree_svg.get_id_order(file_strings, text_tags, not myargs.yes_sample) # If this is sequence sample, IDs should be correct!

if myargs.plain_list == True: #FIX: version 3.8
    plain_id_file = open("%s.plain.ids" % myargs.output, "w")
    for curr_id in ordered_ids:
        plain_id_file.write("%s\n" % curr_id)
    plain_id_file.close()        

#----------- 2) Alignment sorting
if myargs.input_align == None:
    print ("Alignment file is missing, sorting will not be done")
    sys.exit()

alignment = None
id_hash_align = dict()
if myargs.yes_sample: #FIX: version 4.2
    print ("Sorting sequence sample started...")
    (alignment, found) = udav_fasta.read_fasta (myargs.input_align, None, None, dict(), 10000, False, None, None, None, None, "URef")
    for s in alignment:
        id_hash_align[s.ID] = s
        id_hash_align[s.locus] = s
else:
    print ("Sorting alignment started...")
    alignment = udav_base.read_alignment(myargs.input_align, False) # FIX: False = do not recover 'proper' ID!
    for s in alignment:
        #id_hash_align[s.ID.split(".")[0]] = s
        id_hash_align[s.ID] = s
    
sorted_seq = list()
a = 0
print ("Number of elements in <ordered_ids> list: %i" % len(ordered_ids))
for curr_id in ordered_ids:
    no_match = True
    if len(str(curr_id)) < 4: # This is likely a bootstrap support
        continue   
    if re.match("^0\.\d+$", curr_id): # FIX: version 4.3 (scale bar value was treated as a regex, e.g. '0.20' matches 'RHA1_ro01202')
        continue
    part_of_curr_id = curr_id.split("-")[0]
    for aln_id in id_hash_align.keys():
        if (re.search(curr_id, aln_id) != None) or (re.search(part_of_curr_id, aln_id) != None): #FIX: version 4.2 (re.search instead of re.match), version 4.6 (iTOL lame output considered)
            #seq_aligned = id_hash_align.pop(aln_id) #FIX: version 4.2
            seq_aligned = id_hash_align[aln_id]
            sorted_seq.append(seq_aligned)
            a += 1
            no_match = False
            break
    if no_match: 
        print ("WARNING: Cannot find aligned sequence with id '%s'" % curr_id)
        sorted_seq.append(udav_base.Sequence(curr_id, "---"))

print ("\tDONE!")
if myargs.more == True:
    unsorted = id_hash_align.keys()
    for curr_id in unsorted:
        curr_sequence = id_hash_align[curr_id].sequence
        best_identity = 0
        best_i = 0
        for i in range(len(sorted_seq)):
            new_sequence = sorted_seq[i].sequence
            curr_identity = 0
            for l in range(len(new_sequence)): # or len(curr_sequence), they are equal
                if curr_sequence[l] == new_sequence[l]:
                    curr_identity += 1
            if curr_identity > best_identity:
                best_identity = curr_identity
                best_i = i
        sorted_seq.insert(best_i, id_hash_align[curr_id])
    print ("Printed %i sorted sequences (and %i unsorted added near the best match)" % (a, len(id_hash_align.keys())))
else:
    print ("Printed %i sorted sequences (unsorted were not added)" % len(sorted_seq))
udav_base.print_pure_sequences(sorted_seq, myargs.output + ".tree_sorted", False, False)