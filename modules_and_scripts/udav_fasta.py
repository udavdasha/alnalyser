"""
Module for working with the FASTA-formatted sequences produced from complete genomes
Currently the following formats are accepted: My_Ref, My (v1.3), Uniprot (v1.4), PDB (v1.5)
                                              Basic (v1.7), URef(v2.0), OldRef(v.2.4), 
                                              NCBI (v.2.4), Olesya (v.2.10), COGcollator (v.2.11),
                                              German (v.2.12)
Now exceptions are considered: FIX: version 2.12
------- Version: 2.22
Methods included in this module:
        1) dict unredun_org (input_filename, output_filename)
           a)  Reads <input_filename> which is expected to be *.org file produces with the 
               <read_Genome_release.py> script
           b)  Prints to the file with <output_filename> an unredundant list of species
           c)  Returns a hash with required organisms names as keys and True as values
        2) dict read_req_list (input_filename, mode, req_code)
           FIX: (version 1.2)
           a)  Reads <input_filename> which is expected to be a list of entries to be written
               into hash (organism names, protein IDs etc). 
           b)  Depending on the <mode>, only first column (\t as separator) will be used or
               only records with <req_code> ("1" by default) in second column will be taken.
               Modes could be: "all" (default) or "sample" or "pdb" (FIX: (version 1.3) in 
               this mode second column is considered as a chain and merged with the first)
               or "exact" or "cog" (in FIX: version 2.3)
           c)  Returns a hash with these entry names as keys and True as values
        3) str  get_id (seq, id_type)
        4) list read_fasta (filename, sample_filename, occurrence_filename, protein_occur, 
                            verbose_limit, big_file, required_id, required_org, min_len, max_len,
                            format = URef):

Classes included in this module:
	1) Annotated_sequence (<- Sequence)
           ~ Variables: ~
        -> str  name          - string with initial description line
        -> str  ID            - part of the name before 1st space (as considered by fasta format)
        -> str  sequence      
	   str  gi
           str  protein_id
           str  locus
           str  product
           str  organism
           int  gene_begin
           int  gene_end
           int  gene_direction
           str  source_record
           list operon        - list with objects of chromosome tables as values
           int  position      - position of current gene in operon list

           ~ Methods: ~
        -> void print_fasta(fasta_file)           - print fasta format sequence into given file        
        -> bool length_in_range(min_len, max_len) - checks if sequence length is into the given range
           void print_short(fasta_file)           - print short format ('My') into file
           str  get_data()                        - returns a string for the table
 
        2) Organism
           ~ Variables: ~
           str  name
           str  taxonomy
           int  protein_num
           int  records_num
           str  full_data
"""
import re, sys
import copy
from udav_base import Sequence

class FastaException(BaseException):   
    def __init__(self):
        BaseException(self)

def get_id (seq, id_type):
    result = None
    if id_type == "GI":
        result = seq.gi
    if id_type == "ID":
        result = seq.protein_id
    if id_type == "Basic":
        result = seq.ID
    if id_type == "locus": # FIX: version 2.15
        result = seq.locus
    if result == None:
        print "FATAL ERROR: no record of type %s found in record %s" % (id_type, seq.full_fasta)
        sys.exit()
    return result
    
class Annotated_sequence(Sequence):
    def __init__(self, gi, protein_id, locus, product, organism, gene_begin, gene_end,
                       gene_direction, taxonomy, source_record, full_fasta, source_name = None):
        Sequence.__init__(self, full_fasta, "")
        self.gi = gi
        self.protein_id = protein_id
        self.locus = locus
        self.product = product
        self.organism = organism
        self.gene_begin = int(gene_begin)
        self.gene_end = int(gene_end)
        self.gene_direction = int(gene_direction)
        self.source_record = source_record
        self.source_name = source_name # FIX: version 2.12 - full name of the source record
        self.taxonomy = taxonomy
        self.operon = list()        
        self.position = 0
        self.COG = None

    def get_start_from_id(self):
        '''
        In case of complex protein ids, returns start position written in it (like for
        'ABC_ECOLI_456-676' will return int 456), for simple IDs will return 1
        '''
        result = 1
        start_match = re.search("\_(\d+)\-\d+$", self.protein_id)
        if start_match != None:
            result = int(start_match.group(1))
        return result

    def get_proper_protein_id(self):
        proper_id = re.search("\w+_*\d+\.\d+", self.protein_id)
        return proper_id.group(0)

    def print_short (self, id_type, fasta_file, prot_type = None, mode = "normal"):
        req_id = get_id(self, id_type)
        if self.COG != None:
            prot_type = self.COG
        if prot_type == None:
            if mode == "normal":
                fasta_file.write(">%s|%s\n" % (req_id, self.organism))
                #fasta_file.write(">" + req_id + "\n")
            if mode == "underline": # FIX: version 2.8
                fasta_file.write(">%s|%s\n" % (req_id, self.organism.replace(" ", "_")))
        else:
            if mode == "normal":
                fasta_file.write(">%s|%s|%s\n" % (req_id, prot_type, self.organism))
            if mode == "cog": # FIX: version 2.6
                fasta_file.write(">%s|%s %s\n" % (req_id, prot_type, self.organism))
        fasta_file.write(self.sequence + "\n\n")

    def get_name_in_format(self, id_type, format, no_spaces = False, prot_type = None):
        """
        Returns sequence name in fasta format of selected flavor
        FIX: version 2.11
        """
        supported = {"My" : True, "Basic" : True, "NCBI" : True, "ID" : True, "Table" : True, "My & unaligned" : True, "Same but fixed" : True}
        if not format in supported:
            print ("FATAL ERROR: format '%s' is not supported by AnnotatedSequence class!" % format)
            print ("Supported formats are: %s" % supported.keys())
            raise FastaException
        result = ""
        req_id = get_id(self, id_type)
        org = self.organism
        if no_spaces:
            org = org.replace(" ", "_")

        if (format == "My") or (format == "My & unaligned"):
            if prot_type == None:
                result = ">%s|%s\n" % (req_id, org)
            else:
                result = ">%s|%s|%s\n" % (req_id, prot_type, org)
        if format == "Basic":
           result = ">%s %s\n" % (req_id, org)
        if format == "NCBI":
           result = ">gi|%s|ref|%s %s [%s]\n" % (self.gi, self.protein_id, self.product, self.organism)            
        if format == "ID":
           result = ">%s\n" % req_id
        if format == "Table":
           result = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (self.gi, self.protein_id, self.organism, 
                                                          self.gene_begin, self.gene_end, self.gene_direction,
                                                          self.source_record, self.source_name)        
        if format == "Same but fixed":   
           result = ">" + re.sub("\/\d+\-\d+$", "", self.name) + "\n"
        return result

    def get_data(self):
        data_string = "%s\t%s\t%s\t%i..%i\n" % (self.protein_id, self.organism,
                                              self.source_record, 
                                              self.gene_begin, self.gene_end)
        return data_string

class Organism:
    def __init__(self, name, taxonomy, records_num, protein_num, full_data):
        self.name = name
        self.taxonomy = taxonomy
        self.protein_num = protein_num
        self.records_num = records_num
        self.full_data = full_data 

def unredun_org (input_filename, output_filename):
    print "List of organisms inside the %s file will become unredundant" % input_filename
    print "Strains with larger proteomes are preferred!"
    org_list = list()
    unredun_org = dict()
    exceptional_org = {"Bacillus subtilis subsp. subtilis str. 168" : True,
                       "Escherichia coli str. K-12 substr. MG1655"  : True}
    header = list()
    #----------------------------------------------------------------------------------
    input_list = open (input_filename, "r")
    for string in input_list:
        string = string.strip()
        if len(string) == 0:
           continue
        if string[0] == "#":
           header.append(string)
           continue
        data = string.split("\t")
        if len(data) < 4:
           print 
        curr_name = data.pop(0)
        curr_record_num = data.pop(0)
        curr_protein_num = data.pop(0)
        org_list.append(Organism(curr_name, data, curr_record_num, curr_protein_num, string))
    input_list.close()
    #----------------------------------------------------------------------------------
    match_num = 0
    for org in org_list:      
        name_parts = org.name.split(" ")               # Staphylothermus hellenicus DSM 12710
        species = name_parts[0] + " " + name_parts[1]  # Staphylothermus hellenicus
        if name_parts[0] == "Candidatus":              # Candidatus Methanomethylophilus alvus Mx1201
            species += name_parts[2]
        if species in unredun_org:
            if unredun_org[species].name in exceptional_org: # Exceptional organism is already taken
                continue
            if org.name in exceptional_org:                  # This organism is exceptional
                unredun_org[species] = org 
            else:
                if unredun_org[species].protein_num == org.protein_num:                    
                    header.insert(0, "# Exact proteome size match: fst = %s, snd = %s" % (unredun_org[species].name, org.name))
                    match_num += 1
                if unredun_org[species].protein_num < org.protein_num:
                    unredun_org[species] = org
        else:
            unredun_org[species] = org 
    #----------------------------------------------------------------------------------    
    output_list = open (output_filename, "w")
    output_list.write("# Unrerundant list of species produced by script <get_operon.py>\n")
    output_list.write("# Strains with larger proteomes were preferred\n")
    output_list.write("# The following organisms were preferred over any other:\n")
    for e in exceptional_org.keys():
        output_list.write("# " + e + "\n")
    output_list.write("# Total %i exact matches were observed\n" % match_num)
    for h in header:
        output_list.write(h + "\n")
    for key in unredun_org.keys():
        output_list.write(unredun_org[key].full_data + "\n")
    output_list.close()

    print "List of unredundant organisms was written to the %s file!" % input_filename
    print "Species in the original list: %i" % len(org_list) 
    print "Species in the unredundant list: %i" % len(unredun_org.keys())
    #----------------------------------------------------------------------------------    
    required_org = dict()
    for key in unredun_org.keys():
        required_org[unredun_org[key].name] = True 
    return required_org

def read_req_list (input_filename, mode = "all", req_code = "1"):      
    print "List of entries inside the %s file will be red; mode = %s" % (input_filename, mode)
    required = dict()
    input_list = open (input_filename, "r") 
    for string in input_list:
        string = string.strip()
        if len(string) > 0:
            if string[0] != "#":
                values = string.split("\t")
                if mode == "all":   
                    required[values[0]] = True
                    required[values[0].upper()] = True # FIX: version 2.1
                    required[values[0].lower()] = True
                if mode == "exact":
                    required[values[0]] = True
                if mode == "sample":
                    if len(values) > 1:
                        if values[1] == req_code:
                            required[values[0]] = True
                if mode == "pdb":
                    if len(values) > 1:
                        full_code = "_".join((values[0], values[1]))
                        required[full_code] = True
                    else:
                        required[values[0]] = True # FIX: version 2.2 (normal ID could be provided)
                if mode == "cog":
                    gi = values.pop(0)                     
                    values.pop(0) # Removing organism data
                    COG_data = "_".join(values)
                    required[gi] = COG_data
                if type(mode) == type(1.0): # FIX: version 2.14 (this is BLAST results)                    
                    gi = values[1]
                    e_value = float(values[10])
                    if e_value < mode:
                        required[gi] = True
    input_list.close()
    print "DONE. Total %i entries names were obtained" % len(required.keys())
    return required

def get_sequence_data (string, format):
    result_seq = None
    string = string.strip(">")    
    if format == "My_Ref":
        fields = string.split("|")
        if len(fields) != 13: 
            print "FATAL ERROR: Unexpected file format. Check that recent version of"
            print "             'My_Ref' format was used!"
            print "Number of fields: %i" % len(fields)
            print "String = %s" % string
            print fields
            raise FastaException
        result_seq = Annotated_sequence(fields[1], fields[3], fields[4], fields[5], fields[7],
                              fields[8], fields[9], fields[10], fields[11], fields[12], string) 
    if format == "My": #FIX: version 1.3
        fields = string.split("|")
        if len(fields) == 3:
            result_seq = Annotated_sequence(fields[0], fields[0], "Unk", fields[1], fields[2], 
                                  -1, -1, 0, "Unk", "Unk", string)
        if len(fields) == 2:
            result_seq = Annotated_sequence(fields[0], fields[0], "Unk", "Unk", fields[1], 
                                  -1, -1, 0, "Unk", "Unk", string)
    
    if format == "Uniprot": #FIX: version 1.4
        # gi = AC; protein_id = ID; locus = "Unk"; product = DE; organism = OS;
        # gene_begin = -1; gene_end = -1; gene_direction = 0; source_record = sw or tr
        # >sp|Q6GZX4|001R_FRG3G Putative transcription factor 001R OS=Frog virus 3 (isolate Goorha) GN=FV3-001R PE=4 SV=1
        curr_id = string.split(" ", 1)[0]
        curr_descr = string.split(" ", 1)[1]
        fields = curr_id.split("|")
        if len (fields) != 3:
            print "FATAL ERROR: Unexpected file format in Uniprot!"
            print "Number of fields: %i" % len(fields)
            print "String = %s" % string
            raise FastaException        
        source = fields[0]
        AC = fields[1]
        ID = fields[2]
        match = re.match("([^=]+)=([^=]+)", curr_descr.split(" ", 1)[1])
        DE = "Unk"
        OS = "Unk"
        if match != None:
            DE = match.groups()[0].replace(" OS", "")
            OS = match.groups()[1].replace(" GN", "").replace(" OX", "") #FIX: version 2.22 (Uniprot format could be: >... OS=Streptomyces sp. BK022 OX=2512123)
        else:
            print "Match here was None: %s" % string
        result_seq = Annotated_sequence(AC, ID, "Unk", DE, OS, -1, -1, 0, "Unk", source, string) 
        #print "source = %s, AC = %s, ID = %s, OS = %s" % (source, AC, ID, OS)

    if format == "PDB": #FIX: version 1.5
        #gi = pdbid; protein_id = pdbid (no chain); locus = "Unk"; product = <name>; organism = "Unk";
        # gene_begin = -1; gene_end = -1; gene_direction = 0; source_record = na or protein
        #>101m_A mol:protein length:154  MYOGLOBIN
        fields = string.split("  ", 1)
        pdbid = fields[0].split(" ")[0].strip(">")
        mol_type = fields[0].split(" ")[1].split(":")[1]
        product = "Unk"
        if len(fields) == 2:
            product = fields[1]
        possible_id = pdbid.split("_", 1)[0] # FIX: now truncated id (without chain) is not considered
        result_seq = Annotated_sequence(pdbid, possible_id, "Unk", product, "Unk", -1, -1, 0, "Unk", mol_type, string) 
    
    if format == "OldRef": #FIX: version 2.4
        #>gi|42761457|ref|NP_976267.1|pML_02|hypothetical protein|Methanohalophilus mahii plasmid pML, complete sequence.|Methanohalophilus mahii
        fields = string.split("|")
        if len(fields) != 8:
            print "WARNING: Unexpected file format. Check that 'OldRef' format was used!"
            print "Number of fields: %i" % len(fields)
            print "String = %s" % string                    
        result_seq = Annotated_sequence(fields[1], fields[3], "Unk", fields[5], fields[7],
                              -1, -1, 0, "Unk", fields[6], string) 

    if format == "NCBI": #FIX: version 2.4
        #>gi|365992322|ref|NP_212397.2| signal peptidase I [Borrelia burgdorferi B31]
        #Now also the following strings, FIX: version 2.7
        #>gi|57116782|ref|NP_215295.2| Probable protease II PtrBb [second part] (oligopeptidase B) [Mycobacterium tuberculosis H37Rv]
        fields = string.split(" ", 1)
        if len(fields) != 2:
            print "FATAL ERROR: Unexpected file format. Check that 'NCBI' format was used!"
            print "Number of fields: %i" % len(fields)
            print "String = %s" % string                    
            raise FastaException
        ids = fields[0].split("|")
        gi = ids[1]
        protein_id = ids[3]
        org = re.search("\[[^\]]+\]$", fields[1]).group(0)
        fields[1] = fields[1].replace(org, "")
        org = org.strip("[]")
        product = fields[1].strip(" ")
        result_seq = Annotated_sequence(gi, protein_id, "Unk", product, org, -1, -1, 0, 
                                        "Unk", "Unk", string) 

    if format == "NCBI_2016": #FIX: version 2.16
        #>NP_212397.2 signal peptidase I [Borrelia burgdorferi B31]
        fields = string.split(" ", 1)
        if len(fields) != 2:
            print "FATAL ERROR: Unexpected file format. Check that 'NCBI' format was used!"
            print "Number of fields: %i" % len(fields)
            print "String = %s" % string                    
            raise FastaException        
        gi = fields[0]
        protein_id = fields[0]
        try:
            org = re.search("\[[^\]]+\]$", fields[1]).group(0)
        except:
            print ("WARNING: organism was not found:")
            print ("String = %s" % string)
            org = "Unk"
        fields[1] = fields[1].replace(org, "")
        org = org.strip("[]")
        product = fields[1].strip(" ")
        result_seq = Annotated_sequence(gi, protein_id, "Unk", product, org, -1, -1, 0, 
                                        "Unk", "Unk", string) 

    if format == "COG": #FIX: version 2.5
        #>52784727|COG1600 Bacillus licheniformis ATCC 14580
        fields = string.split(" ", 1)
        ids = fields[0].split("|")
        gi = ids[0]
        protein_id = ids[0]
        desc_part = ids[1]
        product = ids[1]
        org = fields[1]
        result_seq = Annotated_sequence(gi, protein_id, "Unk", product, org, -1, -1, 0, 
                                        "Unk", "Unk", string) 
        result_seq.COG = desc_part.replace("/", ".")

    if format == "URef": #FIX: version 2.0
        id_part = string.split(" ", 1)[0]
        ids = id_part.split("|")
        if len(ids) != 4:
            print "WARNING: Unexpected file format: expected 'URef', changed to 'Basic'"
            print "Number of fields in id part: %i" % len(ids)
            print "String = %s" % string
            print ids
            format = "Basic" # FIX: 2.18 (quiet behavior)
            #raise FastaException
        else:
            gi = ids[1]
            protein_id = ids[3]
            description_part = string.split(" ", 1)[1]
            fields = description_part.split("|")
            if len(fields) != 9: 
                print "FATAL ERROR: Unexpected file format. Check that 'URef' format was used!"
                print "Number of fields in description part: %i" % len(fields)
                print "String = %s" % string
                print fields
                raise FastaException
            result_seq = Annotated_sequence(gi, protein_id, fields[0], fields[1], fields[3],
                                  fields[4], fields[5], fields[6], fields[7], fields[8], string, fields[2]) 

    if format == "Olesya": #FIX: version 2.10
        id_part = string.split(" ", 1)[0]
        ids = id_part.split("|")
        gi = ids[1]
        protein_id = ids[3]
        description_part = string.split(" ", 1)[1]
        fields = description_part.split("|")
        result_seq = Annotated_sequence(gi, protein_id, fields[0], fields[4], fields[7],
                              fields[2], fields[3], fields[1], fields[8], fields[6], string) 

    if format == "COGcollator": #FIX: version 2.11
        #>556563019 COG0699/1 [Actinoplanes friuliensis DSM 7358]
        #>167931392 interferon-inducible GTPase family member [Mus musculus]
        fields = string.split(" ", 1)
        org = re.search("\[[^\]]+\]$", fields[1]).group(0)
        product = string.replace(fields[0], "").replace(org, "").strip()
        result_seq = Annotated_sequence(fields[0], fields[0], "Unk", product, org.strip("[]"), 
                                        -1, -1, 0, "Unk", "Unk", string)

    if format == "German":
        #>288817733_Hydrogenobacter_thermophilus_TK_6
        fields = string.split("_", 1)       
        org = fields[1]
        result_seq = Annotated_sequence(fields[0], fields[0], "Unk", "Unk", org, 
                                        -1, -1, 0, "Unk", "Unk", string)

    if format == "Prodigal":
       #>Aenigmarchaeota_1 # 3 # 479 # -1 # ID=1_1;partial=10;start_type=ATG;rbs_motif=GGA/GAG/AGG;rbs_spacer=5-10bp;gc_cont=0.434
       fields = string.split(" # ")
       begin = int(fields[1])
       end = int(fields[2])
       direction = int(fields[3])
       attributes = fields[4].split(";")
       protein_id = attributes[0].split("=")[1]
       result_seq = Annotated_sequence(fields[0], protein_id, "Unk", fields[4], "Unk",
                                       begin, end, direction, "Unk", "Unk", string)

    if format == "Basic": #FIX: version 1.7
        #>id description
        fields = string.split(" ", 1)
        protein_id = fields[0]
        description = "Undef"
        if len(fields) == 2:
            description = fields[1]
        result_seq = Annotated_sequence(protein_id, protein_id, "Unk", description, "Unk", -1, -1, 0, "Unk", "Unk", string)

    if result_seq == None:
        print ("WARNING: sequence from this string was not obtained. Possibly unsupported file format: %s" % format)
        print (string)

    return result_seq

def read_fasta (filename, sample_filename, occurrence_filename, protein_occur, verbose_limit, big_file, required_id, required_org, min_len, max_len, format = "URef", directions = None, duplicate_filename = None, type_of_id = "ID", attr_for_protein_occur = "organism"):
    """
    Reads FASTA-format bank and returns it as a list of Sequence objects. 
    Also prints it to file. Can also reject sequences based on their length

    Attributes:
      str  filename               - name of the input bank file in FASTA format
      str  sample_filename        - prefix for the output files
      str  occurrence_filename    - name of file with occurence of proteins in organisms
      dict protein_occur          - hash where protein occurence should be deposited (non-empty or empty)
      int  verbose_limit          - how many sequences should be red before anouncement on the screen appears
      bool big_file               - if True, resulting gene list will be empty as this is a large file
      dict required_id            - if not None, dictionary of protein_id requered
      dict required_org           - of not None, dictionary of requered organism names
      int  min_len                - minimal protein length to be included into the sample
      int  max_len                - maximal protein length to be included into the sample
      str  format                 - format of the input file (see method 'get_sequence_data' for all supported)
      str  attr_for_protein_occur - name of protein
    """
    print "Started reading input fasta file: %s" % filename
    if sample_filename != None: # Sample file is to be printed
        print "Sample (which meet requirements) will be printed to the file %s" % sample_filename
        reject_filename = sample_filename + ".reject"
        print "Data on rejections (if any) will be printed to the file %s" % reject_filename
        short_filename = sample_filename + ".short"
        print "Sample in 'My' format will be printed to the file %s" % short_filename
        sample_file = open(sample_filename, "w")
        short_file = open(short_filename, "w")
        reject_file = open(reject_filename, "w")
        id_file = open("%s.ids" % sample_filename, "w")
        table_data_file = open(sample_filename + ".table", "w") #FIX (version 2.9)
        table_data_file.write("#protein_id\tgi\torganism\tlength\tsource\tlocus_tag\n") #FIX (version 2.15)
        reject_file.write("# Sequences would be rejected based on the length\n")
        reject_file.write("# Minimal length: %s\n" % min_len)
        reject_file.write("# Maximal length: %s\n" % max_len)
        reject_file.write("#ID\tlength\tproduct\n")
    else:
        print "No sample (or rejection) file will be created!"

    fasta_file = open(filename, "r")
    seqs = list()
    big_file_seqs = list()
    take_seq = False
    found = dict()
    duplicate = dict()
    v = 0
    n = 0 
    for string in fasta_file:
        string = string.strip()
        if len(string) == 0:
            continue
        if string[0] == ">": # Description string
            v += 1
            n += 1
            if v > verbose_limit:
                print "Proceeding %i sequence..." % n                
                v = 0                
            take_seq = True
            curr_seq = get_sequence_data(string, format)            
            #-------------------------------------- Requirement check ---------------------              
            if required_id != None:
                #FIX (version 1.1): also GI is checked
                #FIX (version 1.6): part of standart fasta-format name (before space) is checked
                #FIX (version 2.3): now values in <required_id> list are changed to "False" if found                 
                #FIX (version 2.15): locus is checked
                if (not curr_seq.protein_id in required_id) and (not curr_seq.gi in required_id) and (not curr_seq.ID in required_id) and (not curr_seq.locus in required_id):
                    take_seq = False
                if take_seq == True: # This protein is found in the required list by one of its IDs                   
                    unique_attributes = ["protein_id", "gi", "locus"]
                    for attr in unique_attributes:
                        attr_value = getattr(curr_seq, attr)
                        if attr_value in required_id: #FIX (version 2.15): now protein_id and locus could work together with COGs as well as gi\
                            if type(required_id[attr_value]) != type(True): # COG data is available here
                                curr_seq.COG = required_id[attr_value]
                            found[attr_value] = True                            
                    if curr_seq.ID in required_id:
                        found[curr_seq.ID] = True

                    if curr_seq.protein_id != "Unk": #-------------------- DUPLICATES
                        if curr_seq.COG == None: #FIX (version 2.15): not in the COG mode
                            if not curr_seq.protein_id in duplicate:
                                duplicate[curr_seq.protein_id] = list()
                            duplicate[curr_seq.protein_id].append(curr_seq)
            else:
                #FIX (version 2.20): record data is added to organism name, if present (... @ XXX)
                found_data = curr_seq.organism
                if curr_seq.source_record.count("@") == 1:
                    assembly_data = curr_seq.source_record.split(" @ ", 1)[1]
                    found_data += ("@" + assembly_data)
                found[curr_seq.ID] = found_data
                found[curr_seq.gi] = found_data
                found[curr_seq.protein_id] = found_data
          
            if required_org != None:
                if not curr_seq.organism in required_org:
                    take_seq = False
                    print (" Sequence is rejected: '%s'; org is wrong: '%s'" % (curr_seq.protein_id, curr_seq.organism))
            #if curr_seq.source_record == "na" and format == "PDB": # This is not a protein!
            #    take_seq = False 
            #------------------------------------------------------------------------------  
            if take_seq:                
                if directions != None:
                    #curr_interest = curr_seq.source_record
                    curr_interest = curr_seq.organism
                    if not curr_interest in directions:
                        directions[curr_interest] = [curr_seq.organism, 0, 0]
            
                    directions[curr_interest][0] = curr_seq.organism
                    if curr_seq.gene_direction == 1:
                        directions[curr_interest][1] += 1
                    else:
                        directions[curr_interest][2] += 1

                if len(seqs) != 0:
                    if seqs[-1].length_in_range(min_len, max_len):                    
                        if sample_filename != None:
                            table_data_file.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (seqs[-1].protein_id, seqs[-1].gi, seqs[-1].organism, len(seqs[-1].sequence), seqs[-1].source_name, seqs[-1].locus))
                            curr_mode = "normal"
                            if seqs[-1].COG != None: # COG data is available here
                                curr_mode = "cog"
                            seqs[-1].print_fasta(sample_file)
                            seqs[-1].print_short(type_of_id, short_file, None, curr_mode)
                            id_file.write("%s\n" % get_id(seqs[-1], type_of_id)) #FIX: version 2.15 (locus, GI or ID depending on <type_of_id>)
                        #-------------------------------------- Occurence -----------------------------
                        curr_value = getattr(seqs[-1], attr_for_protein_occur)
                        if curr_value in protein_occur.keys():
                            protein_occur[curr_value] += 1
                        else:
                            protein_occur[curr_value] = 1
                        #------------------------------------------------------------------------------
                        if big_file: # This should be operated without usage of memory
                            if required_id != None: #FIX (version 2.19): required sequences are stored
                                big_file_seqs.append(seqs[-1])
                            seqs.pop()
                    else:
                        if sample_filename != None: reject_file.write("%s\t%i\t%s\n" % (seqs[-1].protein_id, len(seqs[-1].sequence), seqs[-1].product))
                        seqs.pop()                    
                seqs.append(curr_seq)

        else: # Sequence string
            if take_seq:                
                seqs[-1].sequence += string                
    if len(seqs) != 0: # Printing the last sequence into the sample
        if seqs[-1].length_in_range(min_len, max_len):                    
            if sample_filename != None:                
                table_data_file.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (seqs[-1].protein_id, seqs[-1].gi, seqs[-1].organism, len(seqs[-1].sequence), seqs[-1].source_name, seqs[-1].locus))
                curr_mode = "normal"
                if seqs[-1].COG != None: # COG data is available here
                    curr_mode = "cog"
                seqs[-1].print_fasta(sample_file)
                seqs[-1].print_short(type_of_id, short_file, None, curr_mode)
                id_file.write("%s\n" % get_id(seqs[-1], type_of_id)) #FIX: version 2.15 (locus, GI or ID depending on <type_of_id>)
            #-------------------------------------- Occurence -----------------------------
            curr_value = getattr(seqs[-1], attr_for_protein_occur)
            if curr_value in protein_occur.keys():
                protein_occur[curr_value] += 1
            else:
                protein_occur[curr_value] = 1
            #------------------------------------------------------------------------------
            if big_file: # This should be operated without usage of memory
                if required_id != None: #FIX (version 2.19): required sequences are stored
                    big_file_seqs.append(seqs[-1])
                seqs.pop()
        else:
            if sample_filename != None: reject_file.write("%s\t%i\t%s\n" % (seqs[-1].protein_id, len(seqs[-1].sequence), seqs[-1].product))
            seqs.pop()
    print "Total records in bank found: %i" % n
        
    fasta_file.close()
    if sample_filename != None:
        sample_file.close() 
        reject_file.close()
        short_file.close()
        table_data_file.close()
        id_file.close()

    if occurrence_filename != None:
        req_id_num = None
        req_org_num = None
        if required_id != None:
            req_id_num = len(required_id.keys())
        if required_org != None:
            req_org_num = len(required_org.keys())       
        occurrence = open (occurrence_filename, "w")
        occurrence.write("# Occurence of proteins in %s file\n" % filename)
        occurrence.write("# Number of proteins of interest in external list ('None' if not external): %s\n" % req_id_num)
        occurrence.write("# Number of organism of interest in external list ('None' if not external): %s\n" % req_org_num)
        occurrence.write("# Organism\tNumber\n")
        for key in protein_occur:
            occurrence.write("%s\t%i\n" % (key, protein_occur[key]))
        occurrence.close()

    if (duplicate_filename != None) and (required_id != None):
        duplicate_file = open (duplicate_filename, "w")
        duplicate_file.write("# Duplicates of proteins in %s file\n" % filename)
        duplicate_file.write("# Records in external id list file: %i\n" % len(required_id.keys()))
        duplicate_file.write("# ID\tOccurence\tOrganism<i>\tRecord<i>\t...\n")  
        for key in duplicate.keys():
            if len(duplicate[key]) > 1:
                duplicate_file.write("%s\t%s" % (key, len(duplicate[key])))
                for seq in duplicate[key]:
                    duplicate_file.write("\t%s\t%s" % (seq.organism, seq.source_record))
                duplicate_file.write("\n")
        duplicate_file.close()

    if required_id != None: #FIX (version 2.19): required sequences are stored
        seqs = big_file_seqs

    return (seqs, found)

def get_isoform_data(bank_filename, req_proteins = None, id_type = "GI", group_log_filename = None):
    """
    Method reads file at <bank_filename> and creates a dictionary with protein IDs
    (as specified by the <id_type>: 'GI' for gi, 'ID' for protein_id and 'Basic' for
    standart sequence ID (e.g. for NCBI format sequences it would be something like
    gi|123456789|ref|YP_0000000.1)
    Only proteins specified in the <req_proteins> dictionary will be obtained from file.
    If <group_log_filename> is given, it will be created and filled with the log information.
    """
    isoform = dict()
    (proteins, found) = read_fasta (bank_filename, None, None, dict(), 10000, False, req_proteins, None, None, None, "URef", None, None)

    groups = list() # List of [int begin, int end, str source, str org, list protein_IDs, int num]
    for p in proteins:
        group_available = False
        curr_id = get_id(p, id_type)
        for g in groups:
            if p.source_record == g[2]: # Source record is the same
                intersect = min(p.gene_end, g[1]) - max(p.gene_begin, g[0]) + 1
                curr_length = len(p.sequence)
                if 2 * intersect > curr_length: # There is a large intersection between current gene and a group
                #if (p.gene_begin == g[0]) or (p.gene_end == g[1]) or ((p.gene_end <= g[1]) and (p.gene_begin >= g[0])): # Coordinates match                
                    g[4].append(curr_id)
                    group_available = True
                    break
        if not group_available:
            new_group = [p.gene_begin, p.gene_end, p.source_record, p.organism, [curr_id], -1]
            groups.append(new_group)
    
    i = 0
    n = 1
    while i < len(groups):
         if len(groups[i][4]) == 1: # This is not a group but just a single protein
             groups.pop(i)
             i -= 1
         else:
             for protein_id in groups[i][4]:
                 isoform[protein_id] = n
             groups[i][5] = n
             n += 1
         i += 1

    if group_log_filename != None:
        group_log_file = open(group_log_filename, "w")
        group_log_file.write("This log file contains information about isoform groups predicted from the %s databank file\n" % bank_filename)
        if req_proteins != None:
            group_log_file.write("! Only %i required protein IDs considered (%i obtained from databank)\n" % (len(req_proteins.keys()), len(proteins)))
        else:
            group_log_file.write("All protein IDs considered (%i obtained from databank)\n" % len(proteins))
        for i in range(len(groups)):
             group_log_file.write("-----------------------------------------------------\n")
             group_log_file.write("Group #%i (source record %s, organism %s):\n" % (groups[i][5], groups[i][2], groups[i][3]))
             for protein_id in groups[i][4]:
                 group_log_file.write("%s\n" % protein_id)            
        group_log_file.close()

    print ("Defined %i groups of isoforms containing %i proteins!" % (n - 1, len(isoform.keys())))
    return isoform