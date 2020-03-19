"""
Module for working with alignments

------- Version: 1.9
        1.5  * Exact equals of medians in <Identity_graph.proceed_graph()> method is
               now properly proceeded
        1.6  * While building graph by <Identity_graph.build_graph()> method only full cliques
               are considered
        1.7  * Motif calculation now consideres amino acid residue simillarity
        1.8  * Motifs can now be standart
        1.9  * Fixed all print calls without ()


Methods included in this module:
        1) list get_positions (site_seq)
           Reads a sequence string <site_seq>, detects any symbols different from '-' and
           fills the resulting list with their positions (starting from 0)       
        2) list get_feature_positions(feature_string)
           Transforms Gblocks-formatted string <feature_string> (e.g 3..6,8..10) to the
           list of positions described in it (here it would be [2, 3, 4, 5, 7, 8, 9])
        3) void print_blocks_regions(seqs, blocks_string, output_filename)
           Prints to the file <output_filename> only described in <blocks_string>
           positions for each sequence in seqs

Classes included in this module:
        1) Seq_vertex (<- Alignment_sequence)
            ~ Variables: ~
         -> str name
         -> str ID
         -> str sequence
            list  edges
            float median
            float better_median
            str   better_id

           ~ Methods: ~
           void get_median()              - finds median of all identities written in <self.edges>
           void print_edges(graph, graph_file, indent, already_printed)
                Prints data about current edges to the <graph_file> object with given <indent> of
                '-' characters. Also runs the same for all edges objects using <graph> and
                incrementing their indent. Data about <already_printed> edges is used to avoid
                recursion cycling

        2) Vertex_data
           ~ Variables: ~
           str   ID
           float identity

        3) Identity_graph
           ~ Variables: ~
           float max_identity     
           list  id_matrix     
           dict  graph 

           ~ Methods: ~

           bool check_immunity(seq1, seq2, site_positions)  - checks if <seq1> and <seq2> have differences in <site_positions>
           list get_id_matrix(seq_list)                     - calculates identity matrix for <seq_list> de novo
           list read_id_matrix(matrix_filename, seq_number) - reads identity matrix from given file
           void print_id_matrix(filename)                   - prints identity matrix to file with given name
           dict build_graph(seq_list)                       - builds graph
           void proceed_graph(seq_list, report_filename, site_positions)
                Method will remove sequences from the <seq_list> if they are identical more
                than <self.max_identity> value. They should also differ in the given
                <site_position> list of positions. Report about removing will be printed to
                the file with given name
           void print_graph(filename)                       - prints graph to file with given name
"""
import sys, os
import udav_base

def get_positions(site_seq):
    positions = list()
    if site_seq != None:
        for i in range(len(site_seq.sequence)):
           if site_seq.sequence[i] != '-':
               positions.append(i)
               print ("Site position found in file: %i" % (i + 1))
    return positions

def get_feature_positions(feature_string):
    feature_range = list()
    blocks = feature_string.split(",")
    for block in blocks:
        start = int(block.split("..")[0]) - 1
        end = start
        if len(block.split("..")) > 1:
            end = int(block.split("..")[1]) - 1
        block_range = range(start, end + 1, 1)
        feature_range.extend(list(block_range))
    return feature_range

def print_blocks_regions(seqs, blocks_string, output_filename):
    output_file = open(output_filename, "w")
    blocks_range = get_feature_positions(blocks_string)
    for s in seqs:
        output_file.write(">%s\n" % s.name)
        for i in blocks_range:
            output_file.write(s.sequence[i])
        output_file.write("\n\n")
    output_file.close()
#----------------------------------------------------------------------------------------------
def get_multiple_positions(site_seq, motif_std = False): # In contrast with <get_positions> method created dictionary
    positions = dict()
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    n = 0
    if site_seq != None:
        for i in range(len(site_seq.sequence)):
            curr_letter = site_seq.sequence[i]
            if curr_letter != "-":
                if motif_std == True: # Motifs are not specified by the user
                    if n >= len(letters):
                        print ("FATAL ERROR: Too many positions in the motifs, no more than %i supported" % len(letters))
                        sys.exit()
                    curr_letter = letters[n]
                    n += 1                  
                if not (curr_letter in positions):
                    positions[curr_letter] = list()
                    print ("New type of letter found in site sequence: '%s'" % curr_letter)
                               
                positions[curr_letter].append(i)
    return positions

def print_multiple_positions(positions, output_filename): # Prints in motif format
    #{X}	4,28,45
    #{Y}	1,196,423,592	
    output_file = open(output_filename, "w")
    for letter in positions.keys():      
         curr_string = "{%s}\t" % letter
         for i in positions[letter]:
             curr_string += "%i," % (i + 1)
         curr_string = curr_string.strip(",") + "\t"            
         output_file.write(curr_string + "\n")
    output_file.close()

def get_similarity_hash():
    # Groups: 1) Hydrophobic: L, V, I, A, M
    #         2) Positive:    K, R
    #         3) Negative:    D, E
    #         4) Amides:      N, Q
    #         5) OH-grouped:  S, T
    aa_groups = ("LVIAM", "KR", "DE", "NQ", "ST")   
    aa_similar = dict()     
    for group in aa_groups:
        for i in group:
            aa_similar[i] = list()
            for j in group:
                if i != j:
                    aa_similar[i].append(j)                    
    return aa_similar

def get_motif_std_color(motif):
    color = None 
    aa_groups_colors = {"LVIAM" : "(102,102,102)", "KR": "(0,0,255)", "DE" : "(255,0,0)", 
                        "NQ" : "(255,102,0)", "STC" : "(128,128,0)", "H": "(0,255,255)", "G": "(0,255,0)",
                        "FYW" : "(85,0,212)", "P" : "(0,128,0)", "-" : "(0,0,0)"}
    for letter in motif:     
        for group in aa_groups_colors.keys():
            if letter in group:
                if (color != None) and (aa_groups_colors[group] != color):
                    print ("Warning: color for the motif '%s' is unstable! Previous: %s, new: %s" % (motif, color, aa_groups_colors[group])) 
                color = aa_groups_colors[group]
    if color == None:
        color = "(255,255,255)"
    return color

def process_similarity(motifs, aa_similar):
    n = 0
    r = 0
    for motif in motifs.keys():
        occurence = motifs[motif]
        if occurence == 0: # This motif was already processed and should be removed
            motifs.pop(motif)
            r += 1
            continue

        synonim_motifs = list()        #---- 1) Synonimous motifs obtaining        
        for i in range(len(motif)):
            left_part = motif[:i]
            right_part = motif[i + 1:]
            if motif[i] in aa_similar: # This amino acid have similar and thus can be varied
                for aa in aa_similar[motif[i]]:
                    synonim_motifs.append(left_part + aa + right_part)
        motif_var = list()             #---- 2) Preparing variation list        
        for l in motif:
            motif_var.append(dict())
            motif_var[-1][l] = True        
        for s in synonim_motifs:       #---- 3) Filling variation list
            if s in motifs: # This synonim motif exists in reality
                for i in range(len(motif)):                  
                    if not s[i] in motif_var[i]:
                        motif_var[i][s[i]] = True
                occurence += motifs[s]
                motifs[s] = 0
        new_motif = ""                 #---- 4) Creating new motif
        for i in motif_var:
            if len(i.keys()) == 1: # No variation in this site
                new_motif += i.keys()[0]
            else: 
                new_motif += "["
                for letter in i.keys():
                    new_motif += letter
                new_motif += "]"
        if new_motif != motif:
             #print ("Popping '%s', adding '%s'; previous occupancy = %i, new = %i" % (motif, new_motif,
             #                                                                        motifs[motif], occurence))
             motifs.pop(motif)
             motifs[new_motif] = occurence
             n += 1

    print ("Total %i motifs compressed by simillarity; %i motifs with variable letters added!" % (r, n))
    return motifs

def print_motif_variants(seqs, positions, output_filename, motif_std = False, motif_percent = 0):
    aa_similar = get_similarity_hash() # FIX (version 1.7): Similarity is considered now
    output_file = open(output_filename, "w")    
    for letter in positions.keys():
        curr_motifs = dict() # Dictionary to contain different versions of the motif
        curr_pos = positions[letter]
        for s in seqs:
            motif = ""
            for i in curr_pos:
                motif += s.sequence[i]
            if not motif in curr_motifs:
                curr_motifs[motif] = 0
            curr_motifs[motif] += 1
        curr_motifs = process_similarity(curr_motifs, aa_similar) # FIX (version 1.7)
        sorted_keys = udav_base.bubble_sort_keys(curr_motifs, True, True)
        for motif in sorted_keys:
            second_value = curr_motifs[motif]
            if motif_std == True: # FIX (version 1.8): motif is not specified by the user
                curr_motif_percent = 100 * float(curr_motifs[motif]) / len(seqs)
                if curr_motif_percent < motif_percent: # This motif is not frequent!
                    continue
                second_value = "%s\t%i" % (get_motif_std_color(motif), curr_motifs[motif])
            output_file.write("{%s_%s}\t%s\n" % (letter, motif, second_value))
        output_file.write("\n")                                      
    output_file.close()

def read_motif_variants(filename):
    positions = dict()
    input_file = open(filename, "r")
    for string in input_file:
        string = string.strip()
        if len(string) == 0:
            continue
        fields = string.split("\t")
        curr_pos = get_feature_positions(fields[1])
        fields[0] = fields[0].strip("{}")
        positions[fields[0]] = curr_pos
    input_file.close()
    return positions
#----------------------------------------------------------------------------------------------  
class Seq_vertex (udav_base.Alignment_sequence):
    def __init__(self, name, sequence):
        udav_base.Alignment_sequence.__init__(self, name, sequence)
        self.edges = list()
        self.median = None
        self.better_median = None
        self.better_id = None

    def get_median(self):
        median = 0
        id_list = list()
        for v in self.edges:
            id_list.append(v.identity)
        id_list = sorted(id_list)
        if (len(id_list) % 2) == 0: #Even number of edges
            median = (id_list[len(id_list)/2] + id_list[len(id_list)/2 - 1]) / 2.0
        else:
            median = id_list[len(id_list)/2]
        self.median = median            

    def print_edges(self, graph, graph_file, indent, already_printed):
        for curr_edge in self.edges:
            if not curr_edge.ID in graph:
                print ("FATAL ERROR: vertex with ID '%s' is missing from the graph!")
                sys.exit()                
            i = 0
            while i < indent:
                graph_file.write("-")
                i += 1
            if curr_edge.ID in already_printed: # Checking if this edge returns to already printed vertex
                graph_file.write("Edge '%s' (%.2f) (already printed)\n" % (curr_edge.ID, curr_edge.identity))
            else:
                graph_file.write("Edge '%s' (%.2f)\n" % (curr_edge.ID, curr_edge.identity))
                already_printed[curr_edge.ID] = True
                graph[curr_edge.ID].print_edges(graph, graph_file, indent + 1, already_printed)        

class Vertex_data:
    def __init__(self, ID, identity):
        self.ID = ID
        self.identity = identity

class Identity_graph:
    def __init__(self, seq_list, max_identity, blocks_string, matrix_filename):
        self.max_identity = max_identity
        if os.path.isfile(matrix_filename): # Matrix will be obtained from the file
            self.id_matrix = self.read_id_matrix(matrix_filename, len(seq_list))
        else:                               # Matrix will be built de novo
            self.id_matrix = self.get_id_matrix(seq_list, blocks_string)
            self.print_id_matrix(matrix_filename)                
        self.graph = self.build_graph(seq_list) 

    def check_immunity(self, seq1, seq2, site_positions):
        result = False
        for p in site_positions:
            if seq1.sequence[p] != seq2.sequence[p]:
                result = True
                break
        return result

    def get_id_matrix(self, seq_list, blocks_string):
        print ("Identity matrix construction started...")
        alignment_length = len(seq_list[0].sequence)
        construction_range = list() # Default: all length
        if blocks_string != None:
            print ("\tRange for identity calculation = blocks")
            construction_range = get_feature_positions(blocks_string)
            print ("\tTotal positions in blocks: %i" % len(construction_range))
        else:	
            for a in range(alignment_length): # Default range reduced
                column_gaps = 0
                for i in range(len(seq_list)):
                    if seq_list[i].sequence[a] == "-":
                        column_gaps += 1
                if 100 * float(column_gaps)/len(seq_list) < 80: # max 80% gaps in the column are allowed
                    construction_range.append(a)
        id_percentage = list()
        for i in range(len(seq_list)):
            new_line = list()
            id_percentage.append(new_line)
            seq_i = seq_list[i].sequence
            for j in range (len(seq_list)):
                seq_j = seq_list[j].sequence
                curr_percent = 0
                for a in construction_range:
                    if seq_i[a] == seq_j[a]:
                        curr_percent += 1
                curr_percent = 100 * (float(curr_percent) / len(construction_range))
                id_percentage[i].append(curr_percent)
            if len(id_percentage[i]) != len(seq_list):
                print ("FATAL ERROR: Matrix constructed by 'get_id_matrix()' method is corrupted")
                print ("             Abnormal length %i is detected (%i expected)" % (len(id_percentage[i]), len(seq_list)))
                sys.exit()
        print ("\t...matrix is done!")
        return id_percentage

    def read_id_matrix(self, matrix_filename, seq_number):
        print ("Identity matrix reading from the file %s started..." % matrix_filename)
        matrix = list()
        matrix_file = open (matrix_filename)
        for string in matrix_file:
            if len(string.strip()) == 0:
                continue
            values = string.strip().split("\t")
            matrix.append(list())
            for value in values:
                matrix[-1].append(float(value))
            if len(matrix[-1]) != seq_number:
                print ("FATAL ERROR: Matrix red by 'read_id_matrix()' method is corrupted")
                print ("             Abnormal length %i is detected (%i expected)" % (len(matrix[-1]), seq_number))
                sys.exit()              
        matrix_file.close()
        print ("\t...matrix is done!")
        return matrix
    
    def print_id_matrix(self, filename):
        print ("Printing matrix to the file %s..." % filename)
        matrix_file = open (filename, "w")
        for i in range(len(self.id_matrix)):
            string = ""
            for j in range(len(self.id_matrix[i])):
                string += "%.2f\t" % self.id_matrix[i][j]
            string = string.strip()
            matrix_file.write(string + "\n")
        matrix_file.close()
        print ("\t...done!")
   
    def build_graph(self, seq_list):
        print ("Graph construction began...")
        vertex = dict()
        for i in range(len(self.id_matrix)):
            curr_ID = seq_list[i].ID
            vertex[curr_ID] = Seq_vertex(seq_list[i].name, seq_list[i].sequence)
            for j in range(len(self.id_matrix)):
                if i == j:
                    continue   
                if self.id_matrix[i][j] >= self.max_identity:
                    found_ID = seq_list[j].ID
                    vertex[curr_ID].edges.append(Vertex_data(found_ID, self.id_matrix[i][j]))
            if len(vertex[curr_ID].edges) == 0: # Vertex remained without edges
                vertex.pop(curr_ID)           
        # FIX (version 1.6): for removal could be marked only edges with the same
        # FIX                neighbor set!
        print ("\t...graph changing began...")
        for ID in vertex.keys():
            i = 0
            while i < len(vertex[ID].edges):
                edge = vertex[ID].edges[i]
                same_sets = self.compare_edge_set(vertex, edge.ID, ID)
                if not same_sets:
                    vertex[ID].edges.pop(i) # Remove this edge from the graph
                    i -= 1
                    j = 0                                        
                    while j < len(vertex[edge.ID].edges):
                        curr_edge = vertex[edge.ID].edges[j]
                        if curr_edge.ID == ID:
                            vertex[edge.ID].edges.pop(j) # Remove backward edge from the graph
                            break
                        j += 1
                i += 1
        for ID in vertex.keys():           
            if len(vertex[ID].edges) == 0: # Vertex remained without edges
                vertex.pop(ID)           
                           
        print ("\t\t...graph is done!")
        return vertex

    def proceed_graph(self, seq_list, report_filename, site_positions):
        print ("Graph proceeding began...")
        id_for_removal = dict()
        redundant_pairs = dict()
        for ID in self.graph.keys(): # ------------------ Median calculation
            self.graph[ID].get_median()
    
        largest_median = 0
        largest_id = None
        for ID in self.graph.keys(): # ------------------ Best ID detection
            largest_median = self.graph[ID].median
            largest_id = ID
            for e in self.graph[ID].edges:
                edge_ID = e.ID
                if self.graph[edge_ID].median > largest_median:
                    largest_median = self.graph[edge_ID].median
                    largest_id = edge_ID       
            for e in self.graph[ID].edges:
                immunity = self.check_immunity(self.graph[e.ID], self.graph[largest_id], site_positions)
                if immunity == True:
                    continue

                if (e.ID != largest_id):
                    if self.graph[e.ID].median != largest_median:
                        id_for_removal[e.ID] = True
                        self.graph[e.ID].better_median = largest_median
                        self.graph[e.ID].better_id = largest_id
                    else:
                        # FIX (version 1.5): not sequence will not be marked for removal if it has
                        # FIX                exactly the same median as one of the edges; both sequences are stored
                        redundant_pairs[e.ID] = largest_id

            curr_immunity = self.check_immunity(self.graph[ID], self.graph[largest_id], site_positions)
            if (ID != largest_id) and (not curr_immunity) and (self.graph[ID].median != largest_median):
                id_for_removal[ID] = True
                self.graph[ID].better_median = largest_median
                self.graph[ID].better_id = largest_id              

        total_removes = 0
        report = open (report_filename, "w")
        report.write("# File created by the script 'remove_seq_limits.py'\n")
        report.write("# Sequences with identity more or equlas to this are removed: %s\n" % self.max_identity)
        report.write("# Initial number of sequences: %i\n" % len(seq_list))
        report.write("# Removed_id\tMedian_identity\tBetter_identity\tBetter_id\n")
        list_length = len(seq_list)
        i = 0
        r = 0
        while i < list_length:
            curr_id = seq_list[i].ID
            if curr_id in redundant_pairs:
                # FIX (version 1.5): now one of redundant proteins will be removed
                second_id = redundant_pairs[curr_id]
                same_sets = self.compare_edge_set(self.graph, curr_id, second_id)
                if same_sets:
                     if second_id in redundant_pairs:
                         redundant_pairs.pop(second_id)
                     id_for_removal[curr_id] = True
                     self.graph[curr_id].better_median = 101
                     self.graph[curr_id].better_id = second_id
                     r += 1
                                     
            if curr_id in id_for_removal:  
               report.write("%s\t%.2f\t%.2f\t%s\n" % (curr_id, self.graph[curr_id].median,
                                                      self.graph[curr_id].better_median, 
                                                      self.graph[curr_id].better_id))
               seq_list.pop(i)
               total_removes += 1
               list_length -= 1
               i -= 1
                
            i += 1
        report.close()
        print ("\t...graph prodeced, total %i sequences removed (%i expected), and %i of them as redundant" % (total_removes, len(id_for_removal.keys()), r))

    def print_graph(self, filename):
        print ("Printing graph to the file %s..." % filename)
        graph_file = open (filename, "w")
        vertex_list = self.graph.keys()
        already_printed = dict()
        for i in range(len(vertex_list)):
            curr_ID = vertex_list[i]
            graph_file.write("Vertex #%i ID=%s\n" % (i, self.graph[curr_ID].ID))
            self.graph[curr_ID].print_edges(self.graph, graph_file, 1, already_printed) 
            
        graph_file.close()
        print ("\t...done!")

    def compare_edge_set(self, graph, id1, id2):
        identical = False
        edges1 = sorted(graph[id1].edges)
        edges2 = sorted(graph[id2].edges)
        if len(edges1) == len(edges2):
            identical = True
            for i in range(len(edges1)): # Popping edge #2 from list of edges #1
                if edges1[i].ID == id2:
                   edges1.pop(i)
                   break
            for i in range(len(edges2)): # Popping edge #1 from list of edges #2
                if edges2[i].ID == id1:
                   edges2.pop(i)
                   break

            if len(edges1) != len(edges2):
                identical = False
            else:
                for i in range(len(edges1)):
                    if edges1[i].ID != edges2[i].ID:
                        identical = False
        return identical