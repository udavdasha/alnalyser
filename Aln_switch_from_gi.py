#!/usr/bin/env python
import sys, os, shutil, re, argparse, platform
if platform.system() == "Windows":
    sys.path.append("D:\\UdavBackup\\_Complete_genomes\\_scripts")
else:
    sys.path.append("/media/udavdasha/Data/scripts")
import udav_base, udav_soft, udav_convert

#========================================================================================
curr_version = 1.0
parser = argparse.ArgumentParser(description = 
"This script will change IDs in the files produced by Alnalyser based on the assignment \
of GI to ID and locus. Namely, the following files will be changed: \
 * FASTA files: \
    <prefix>.aln \
    <prefix>.fixed \
    <prefix>.pure \
    <prefix>.sample \
    <prefix>.blocks_regions \
    <prefix>_fixed.meg (almost fasta) \
    <prefix>_blocks.meg (almost fasta) \
 * Text & table files: \
    <prefix>.actions \
    <prefix>.features \
    <prefix>.ids \
    <prefix>.TMHMM \
 * Other files: \
    <prefix>.auto_log \
    <prefix>.man_log \
    <prefix>.COG_out \
    <prefix>.COG_table \
Current version is %s" % curr_version 
)
parser.add_argument("-i", help = "Name of the Alnalyser project directory (must exist)", required = True, dest = "input_dir")
parser.add_argument("-w", help = "Name of working directory (use . to work where you run script)", required = True, dest = "work_dir")
parser.add_argument("-o", help = "Name of the new Alnalyser project directory (must not exist)", required = True, dest = "output_dir")
parser.add_argument("-a", help = "Name of the assignment between GI and protein ID/locus (.table)", required = True, dest = "gi_to_id_and_locus_filename")
parser.add_argument("-t", help = "Type if ID to switch to: 'ID' (DEFAULT) or 'locus'", required = False, dest = 'type_of_id')
myargs = parser.parse_args()
[myargs.work_dir, myargs.input_dir, myargs.output_dir, myargs.gi_to_id_and_locus_filename] = udav_base.proceed_params([myargs.work_dir, myargs.input_dir, myargs.output_dir, myargs.gi_to_id_and_locus_filename])
if myargs.type_of_id == None:
    myargs.type_of_id = "ID"
#========================================================================================

if not os.path.isdir(myargs.input_dir):
    print ("FATAL ERROR: input directory '%s' does not exists!" % myargs.input_dir)
    sys.exit()
if os.path.isdir(myargs.output_dir):
    print ("FATAL ERROR: output directory '%s' exists!" % myargs.output_dir)
    sys.exit()

(GI_to_ID, GI_to_locus, gi_dupl, non_unique) = udav_soft.read_protein_table_info(myargs.gi_to_id_and_locus_filename)

if len(non_unique) != 0:
    print ("WARNING: non-unique locus/ID detected; total %i cases" % len(non_unique))

GI_not_found = dict()
GI_to_proper_id = None
if myargs.type_of_id == "ID":
    GI_to_proper_id = GI_to_ID
if myargs.type_of_id == "locus":
    GI_to_proper_id = GI_to_locus

os.makedirs(myargs.output_dir)
files = os.listdir(myargs.input_dir)
for f in files:
    old_file_path = os.path.join(myargs.input_dir, f)
    new_file_path = os.path.join(myargs.output_dir, f)
    if os.path.isdir(old_file_path): # This is a directory
        shutil.copytree(old_file_path, new_file_path)
        continue

    corrected = False
    curr_extension = f.split(".")[-1]
    if curr_extension in ["aln", "pure", "sample", "fixed", "blocks_regions"]: # This is one of FASTA-format files
        udav_convert.correct_fasta(old_file_path, new_file_path, GI_to_proper_id, GI_not_found)
        corrected = True
    if curr_extension in ["actions", "features", "ids", "TMHMM"]: # This is one of table-format files
        udav_convert.correct_table(old_file_path, new_file_path, GI_to_proper_id, GI_not_found)
        corrected = True
    if curr_extension == "meg":
        udav_convert.correct_fasta(old_file_path, new_file_path, GI_to_proper_id, GI_not_found, "#")
        corrected = True
    if curr_extension == "auto_log":
        udav_convert.correct_log(old_file_path, new_file_path, GI_to_proper_id, GI_not_found)
        corrected = True      

    extension_to_re = {"COG_out" : "^Query:\s+(\d+)", "COG_table" : "\s+(\d{6,9})\s+"}
    if curr_extension in extension_to_re:
        udav_convert.correct_re(old_file_path, new_file_path, GI_to_proper_id, GI_not_found, extension_to_re[curr_extension])
        corrected = True
    if not corrected: # Should not be corrected
        shutil.copy(old_file_path, myargs.output_dir)
        print ("NOTE: file '%s' was not corrected!" % f)
print ("Number of GI's not found: %i" % len(GI_not_found.keys()))
for gi in GI_not_found.keys():
    print ("NOT FOUND: '%s'" % gi)