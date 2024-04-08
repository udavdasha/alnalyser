"""
Module for working with svg (Inkscape) documents considered there are trees there
------- Version: 2.3
        1.5  * Proper class & function documentation added
             * <Path_object_svg> class is added
        1.6  * Recursion cyclisation is prevented in graph
        1.7  * Method for the obtaing IDs is separated from the tree printing
        1.8  * Removal of bootstrap tags
        1.9  * Locus could now be sequence ID; bootstrap tags could be replaced with circles
        1.91 * Sequences IDs are fixed with '_', if they appear to be like: XP 002951836.1|Volvox...
        1.92 * Now 'My' format can be used to enter additional sequences information in the middle
        1.93 * Group coloring is improved: now multiple groups are allowed
        2.0  * Not only tree svg, but custom svg should be red correctry
        2.3  * Method <get_id_order> now relies on the y coordinate of text object instead of its 
               position in file (iTOL compatible)
"""

import sys, re, math
import svgwrite

def read_taxonomy_colors(input_filename):
    taxonomy_colors = dict()
    taxa_order = list()
    input_file = open(input_filename)
    for string in input_file:
        string = string.strip()
        if len(string) == 0:
            continue
        if string[0] == "#":
            continue
        fields = string.split("\t")
        if len(fields) != 4:
            print ("FATAL ERROR: Cannot read taxonomy colors, check string '%s'!" % string)
            print (fields)
            sys.exit()
        red   = str( hex(int(fields[0])) ).replace("0x", "")
        if len(red) == 1:
           red = "0" + red
        green = str( hex(int(fields[1])) ).replace("0x", "")
        if len(green) == 1:
           green = "0" + green
        blue  = str( hex(int(fields[2])) ).replace("0x", "")
        if len(blue) == 1:
           blue = "0" + blue
        taxon = fields[3]
        color = "#" + red + green + blue
        taxonomy_colors[taxon] = color
        taxa_order.append(taxon)
    input_file.close()
    return (taxonomy_colors, taxa_order)

def print_simple_legend(name_to_color, order_list, output_filename):
    text_style = "font-size:%ipx; font-family:%s" % (24, "Courier New")
    letter_w = 7.195 * 2 #7.2
    letter_h = 9.6 * 2
    max_name = 0
    for name in order_list:
        if len(name) > max_name:
            max_name = len(name)
    legend_size_x = letter_w * 5
    legend_size_y = letter_h
    spacer = 20
    field = 5
    max_x_size = legend_size_x + spacer + (max_name * letter_w) + (field * 2)
    max_y_size = (legend_size_y * len(order_list)) + (field * 2)
    my_svg = svgwrite.Drawing(filename = output_filename + ".svg", size = ("%ipx" % max_x_size, "%ipx" % max_y_size))
    for i in range(len(order_list)):
        curr_name = order_list[i]
        curr_color = name_to_color[curr_name]
        
        legend_rect = my_svg.rect(insert = (field, (i * letter_h) + field),
                              size = ("%.2fpx" % legend_size_x, "%.2fpx" % legend_size_y),                                      
                              stroke = "none",
                              fill = curr_color)
        name_text = my_svg.text(curr_name, insert=(field + legend_size_x + spacer, (i + 1) * letter_h), fill="black", style=text_style)
        my_svg.add(legend_rect)
        my_svg.add(name_text)
    my_svg.save() 

class Object_svg:
    """
    Typical object in SVG format.
    Contains the following attributes:
    <self.features> - dictionary of keys->values written in the tag
    <self.tags> - list of tags <Object_svg> inside this tag (e.g. <tspan> inside <text> or <title> inside <path>) #FIX: version 2.0
    <self.content> - content of the tag (if it contains nothing - None)
    <self.tag_type> name of the current tag type (e.g., "text" or "path")    
    """
    def __init__(self, tag_content):
#      <smth
#         a="aaaaa"
#         b="bbb"
#         z="zzzzzzz"> XXX </smth>
        self.features = dict()
        self.tags = list()
        #print (tag_content)
        open_tags_inside = re.findall("\<[A-Za-z]+", tag_content[1:])               
        for tag in open_tags_inside: 
            close_tag = "</%s>" % tag.strip("<")
            regex = "%s.+%s" % (tag, close_tag)
            match = re.search(regex, tag_content)
            try:
                start = match.start()
                end = match.start() + len(match.group(0)) - 1
                this_tag_contents = match.group(0)             
                tag_content = tag_content[:start] + tag_content[end + 1:]
                self.tags.append(Object_svg(this_tag_contents))
            except:
                print ("Regex: '%s'" % regex)
                print ("Tag: '%s'" % tag_content)
        #print ("-----------------------------------")
           
        fields = re.findall('[^\s]+="[^"]+', tag_content)        
        #print (tag_content)
        for f in fields:
            pair = f.split('="')
            if len(pair) != 2:
               print ("WARNING: field in SVG object features is weird: %s" % f)
            self.features[pair[0]] = pair[1]
            #print (pair)
        self.tag_type = re.split("\s", tag_content)[0].strip("<")
        close_tag = "</%s>" % self.tag_type
        self.content = None
        if tag_content.count(close_tag) == 1: # There is a close tag here
            content_result = re.search('(?<=\>)[^\<]+', tag_content)
            if content_result == None:
                self.content = ""
            else:
                self.content = content_result.group(0)                               

    def proceed_feature(self, feature_name):
        """
        Method for replacing pure string with the dictionary of key->values for a given
        <feature_name> 
        """
        if feature_name in self.features:
            #style="font-size:12.715518px;font-style:normal;font-weight:normal;text-align:start;text-anchor:start;fill:#ff0000;font-family:Arial"
            feature_string = self.features[feature_name]
            feature_string = feature_string.strip(";")
            fields = feature_string.split(";")
            feature = dict()
            for f in fields:
                prop = f.split(":")
                if len(prop) != 2:
                   print ("WARNING: in object '%s' feature string '%s' is weird ('%s' part)" % (self.features["id"], feature_string, f))
                feature[prop[0]] = prop[1]
            self.features[feature_name] = feature

    def create_svg_tag(self):
         """
         Method returns a new tag based on the data into this object
         """
         text_tag = "<%s " % self.tag_type
         for key in self.features.keys():
             value = self.features[key]
             if type(value) == type(str()): # This is a "normal" key
                 text_tag += '%s="%s" ' % (key, value)
             else:                          # This feature is a hash itself
                 text_tag += '%s="' % key
                 for internal_key in value.keys():
                     internal_value = value[internal_key] 
                     text_tag += '%s:%s;' % (internal_key, internal_value)
                 text_tag = text_tag.strip(";")
                 text_tag += '" '
         text_tag = text_tag.strip(" ")
         if self.content != None: # Requires close tag
             text_tag += ">"
             for tag in self.tags: # Internal tags (if any) are inside the content FIX: version 2.0
                 text_tag += tag.create_svg_tag()
                 
             if self.content.count("|") != 0: # Trying ID fixing FIX: version 1.91
                 parts = self.content.split("|", 1)
                 parts[0] = " " + parts[0].strip().replace(" ", "_")                 
                 self.content = "|".join(parts)
             text_tag += self.content
             text_tag += "</%s>" % self.tag_type       
         else:
             text_tag += " />"
         
         return text_tag    

class Path_object_svg(Object_svg):
    def __init__(self, path_tag_content):
#      <path
#         id="path3460"
#         d="m 50.99925,-432.46687 0,-4.60133 0,0"
#         style="fill:none;stroke:#000000;stroke-width:0.54070675px;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:0.01;stroke-opacity:1;stroke-dasharray:none"
#         inkscape:connector-curvature="0" />
        Object_svg.__init__(self, path_tag_content)
        self.proceed_feature("style")

    #def get_drawing_start(self):
    #    d_feature_match = re.match("[Mm] ([-\d\.]+)\,([-\d\.])+", self.features["d"])
    #    return (d_feature_match.group(1), d_feature_match.group(2))

    def change_line_color(self, new_color):
        if not "style" in self.features:
            print ("Warning: failed to change color of path object %s, no style feature!" % self.features["id"])
        else:
            self.features["style"]["stroke"] = new_color

    def get_start_coordinate(self):
        #d="m 283.68839,33.110976 0,-11.282258 35.52229,0"
        coordinates = self.features["d"].split(" ")[1:]
        start_x = float(coordinates[0].split(",")[0])
        start_y = float(coordinates[0].split(",")[1])
        return (start_x, start_y)
   
    def get_end_coordinate(self):
        #d="m 283.68839,33.110976 0,-11.282258 35.52229,0"
        #d="M 215.20166,168.35235 190.59946,149.6766"

        mode = self.features["d"].split(" ")[0]        
        coordinates = self.features["d"].split(" ")[1:]
        end_x = 0.0
        end_y = 0.0
        if mode == "m": # Relative positions
            end_x = float(coordinates[0].split(",")[0])
            end_y = float(coordinates[0].split(",")[1])
            for i in range(1, len(coordinates)):
                dx = float(coordinates[i].split(",")[0])
                dy = float(coordinates[i].split(",")[1])
                end_x += dx
                end_y += dy
        if mode == "M": # Absolute positions
            end_x = float(coordinates[-1].split(",")[0])
            end_y = float(coordinates[-1].split(",")[1])
        return (end_x, end_y)

    def distance_to_text(self, text_object):
        """
        Returns distance (in pixels) to the ancor of given <text_object> starting from 
        the end of <self>
        """ 
        text_x = float(text_object.features["x"])
        text_y = float(text_object.features["y"])
        (curr_end_x, curr_end_y) = self.get_end_coordinate()
        dist_to_end = math.sqrt( ((text_x - curr_end_x) ** 2) + ((text_y - curr_end_y) ** 2) )      
        (curr_start_x, curr_start_y) = self.get_start_coordinate()
        dist_to_start = math.sqrt( ((text_x - curr_start_x) ** 2) + ((text_y - curr_start_y) ** 2) )      
        return min(dist_to_end, dist_to_start)

    def distance_to_path(self, path_object):
        """
        Returns distance (in pixels) to the start of given <path_object> starting from 
        the end of <self>
        """
        (path_start_x, path_start_y) = path_object.get_start_coordinate()
        (curr_end_x, curr_end_y) = self.get_end_coordinate()
        dist_to_end = math.sqrt( ((path_start_x - curr_end_x) ** 2) + ((path_start_y - curr_end_y) ** 2) )      
        return dist_to_end

    def get_line_color(self):
        if not "style" in self.features:
            print ("Warning: failed to obtain color of path object %s, no style feature!" % self.features["id"])
            return None
        else:
            return self.features["style"]["stroke"]

    def set_size(self, new_size):
        if not "style" in self.features:
            print ("Warning: failed to set size of stroke of path object %s, no style feature!" % self.features["id"])
            return None
        else:
            self.features["style"]["stroke-width"] = new_size

    def set_fill(self, new_fill):
        if not "style" in self.features:
            print ("Warning: failed to set fill of path object %s, no style feature!" % self.features["id"])
            return None
        else:
            self.features["style"]["fill"] = new_fill

    def set_opacity(self, new_opacity):
        if not "style" in self.features:
            print ("Warning: failed to set opacity of path object %s, no style feature!" % self.features["id"])
            return None
        else:
            self.features["style"]["opacity"] = new_opacity

class Text_object_svg(Object_svg):
    def __init__(self, text_tag_content):
#      <text
#         id="text2993"
#         style="font-size:12.715518px;font-style:normal;font-weight:normal;text-align:start;text-anchor:start;fill:#ff0000;font-family:Arial"
#         y="28.297134"
#         x="36.190319"
#         xml:space="preserve"> 14590307 Pyrococcus horikoshii OT3</text>
        Object_svg.__init__(self, text_tag_content)
        self.proceed_feature("style")

    def get_seq_id(self, exact, my_format_important = False):
        """
        This method checks content of this text tag and returns sequence ID.
        * If <exact> is set to True, ID in complicated cases (e.g. ids including 
          information about sequence part, like 123456789_1-456) will be returned
          exact ('123456789_1-456' in this example).
          USAGE: sorting of alignment according to the tree
        * If <exact> is set to False, additional information will be removed and
          thus in this example ID would be '123456789'.
          USAGE: coloring of the tree according to taxonomy file
        * In case when 'My' format contains information about the sequence and should be
          used for the alignment sort, make <my_format_important> True (FIX: 1.92)
        """
        fields = None
        if self.content.count("|") != 0: # 'My' format was preserved
            if my_format_important and (self.content.count("|") == 2):
                complete_id = "\\|".join(self.content.strip().split("|")[0:-1]) # \\ is required because this will be used for search in regular expressions
                complete_id = complete_id.replace(" ", "_")
                fields = [complete_id]
            else:
                fields = self.content.strip().split("|")            
                fields = fields[0].split(" ")
        else:
            fields = self.content.strip().split(" ")

        seq_range = None
        if re.match("^[0-9]+\-[0-9]+$", fields[-1]): # This is identifier like '123456789_1-456' converted to '123456789 1-456'
            seq_range = fields.pop(-1)
        seq_id = "_".join(fields)
        if exact and (seq_range != None): 
            seq_id += "_" + seq_range
        """
        seq_id = fields[0]
        second_part_is_id = None # FIX 1.9: detection of ID is fixed to fit locus IDs
        try:
            int(fields[1])
            if len(fields) == 3: # This could be only 'ID 1 150' #FIX: v.2.2 (also locus_tag could be like: 'OHA_1_00311')!
                second_part_is_id = False
            else: # This could be a locus like 'HVO_0835' converted to 'HVO 0835' or 'HVO 0835 1 150'
                second_part_is_id = True
        except ValueError: # It is not numeric
            if re.match("^[0-9]+\-[0-9]+$", fields[1]): # This is identifier like '123456789_1-456' converted to '123456789 1-456'
                second_part_is_id = False
            else:
                second_part_is_id = True 
        except IndexError: # There is no second part
            pass
        #print ("Second part is ID: %s" % second_part_is_id)
        if second_part_is_id != None: # Addition should be made
            if second_part_is_id:
                seq_id += "_" + fields[1]
                seq_id = seq_id.split(".", 1)[0]
                fields.pop(1)
             
            if exact and (len(fields) > 1):            
                if re.match("^[0-9]+\-[0-9]+$", fields[1]): # This is identifier like '123456789_1-456' converted to '123456789 1-456'
                    seq_id += "_" + fields[1]
                else:
                    try: # This is identifier like '123456789_1-456' converted to '123456789 1 456'
                        begin = int(fields[1])
                        end = int(fields[2])
                        seq_id = "%s_%i-%i" % (seq_id, begin, end)
                    except ValueError:
                        pass
                    except IndexError:
                        pass
        """
        return seq_id

    def set_new_x(self, new_x):
        try:
            float(new_x)
            self.features["x"] = str(new_x)
        except:
            print ("Warning: trying to replace x coordinate with trash: '%s'; it is not done" % new_x)

    def change_text_color(self, new_color):
        if not "style" in self.features:
            print ("Warning: failed to change color of text object %s, no style feature!" % self.features["id"])
        else:
            self.features["style"]["fill"] = new_color

    def get_text_color(self):
        if not "style" in self.features:
            print ("Warning: failed to obtain color of text object %s, no style feature!" % self.features["id"])
            return None
        else:
            return self.features["style"]["fill"]

    def set_text(self, new_text):
         if len(self.tags) != 0:
             self.tags[0].content = new_text
             self.tags = self.tags[:1]

    def change_font(self, new_font, new_size, bold = False):
        if not "style" in self.features:
            print ("Warning: failed to change font of object %s, no style feature!" % self.features["id"])
        else:
            if new_font != None:
                self.features["style"]["font-family"] = new_font
            if new_size != None:
                self.features["style"]["font-size"] = "%spx" % new_size
            if bold == True:
                self.features["style"]["font-weight"] = "bold"    

    def is_leaf(self):
        result = True
        if re.match("\d+\.\d+", self.content) or re.match("\d+\,\d+", self.content) or re.match("^\d+$", self.content):
            result = False
        return result

    def is_support(self):
        result = False
        if re.match("^\d+$", self.content) != None:            
            value = int(self.content)
            if (value >= 0) and (value <= 100):
                result = True
        return result

    def stroke_off(self):
        if not "style" in self.features:
            print ("Warning: failed to turn stroke off in text object %s, no style feature!" % self.features["id"])
        else:
            if "stroke" in self.features["style"]:
                del self.features["style"]["stroke"]

class Edge_svg:
    def __init__(self, path_object):
        self.data = path_object
        self.children = list()
        self.parent = None
        self.color_set = False

    def select_color(self):
        if (self.children == None) or (self.color_set == True):
            return
        if len(self.children) == 2:
            if self.children[0].color_set == False:
               self.children[0].select_color()
            if self.children[1].color_set == False:
               self.children[1].select_color()            
            fst_color = self.children[0].data.get_line_color()
            second_color = self.children[1].data.get_line_color()
            if (fst_color == second_color):                    
                self.data.features["style"]["stroke"] = fst_color
                 
    def get_id(self):
        return self.data.features["id"]       

class Graph_path_svg:
    def __init__(self, path_objects, dist_threshold):
        edge_graph = dict() 
        for key in path_objects.keys():        
            curr_id = path_objects[key].features["id"]
            edge_graph[curr_id] = Edge_svg(path_objects[key])

        edges = edge_graph.keys()
        for i in range(len(edges)):
            i_id = edges[i]
            for j in range(len(edges)): 
                if i == j:
                    continue
                j_id = edges[j]
                dist_i_j = edge_graph[i_id].data.distance_to_path(edge_graph[j_id].data)
                #print ("i_id = %s, j_id = %s, dist_i_j = %.3f" % (i_id, j_id, dist_i_j))
                if dist_i_j < dist_threshold:
                   if edge_graph[j_id].parent != None: # Multiple parents
                       #print ("Multiple parents detected in the path '%s':" % j_id)
                       #print ("Previous: '%s'" % edge_graph[j_id].parent.get_id())
                       #print ("New: '%s'" % i_id)
                       prev_parent_id = edge_graph[j_id].parent.get_id() # FIX: version 1.6
                       for c in range(len(edge_graph[prev_parent_id].children)): # Removing from previous parent
                           child = edge_graph[prev_parent_id].children[c]
                           if child.get_id() == j_id:
                               edge_graph[prev_parent_id].children.pop(c)
                               #print ("%s removed from children list of %s!" % (j_id, prev_parent_id))
                               break
                   edge_graph[j_id].parent = edge_graph[i_id]
                   if len(edge_graph[i_id].children) >= 2: # More than 2 children
                       print ("Multiple children detected in the edge '%s'!" % i_id)
                   edge_graph[i_id].children.append(edge_graph[j_id])  
        self.edge_graph = edge_graph

    def color_leaves(self, text_objects, dist_threshold):
        """
        This method colors branches of the graph according to the closest neighbor in the <text_objects>
        with the maximum possible distance between the end of the path and it set to <dist_threshold>
        """
        n = 0
        for path_id in self.edge_graph.keys():
            if len(self.edge_graph[path_id].children) != 0: # This is not a leaf branch
                continue
            text_found = False
            for text_id in text_objects.keys():
                dist_path_to_text = self.edge_graph[path_id].data.distance_to_text(text_objects[text_id])
                #if dist_path_to_text < 10:
                #    print ("CURR_DIST: %s" % dist_path_to_text)
                #    print ("path %s; text %s" % (path_id, text_id))                 
                #    raw_input()
                if dist_path_to_text < dist_threshold:                    
                    if text_found == False:                    
                        #print ("       path_id = %s, text_id = %s, dist = %.3f" % (path_id, text_id, dist_path_to_text))
                        self.edge_graph[path_id].data.change_line_color(text_objects[text_id].get_text_color())
                        text_found = dist_path_to_text
                        self.edge_graph[path_id].color_set = True
                    else:
                        #print ("More than one text in the distance less than %.3f found!" % dist_threshold)                        
                        if dist_path_to_text < text_found:
                            #print (" (NEW) path_id = %s, text_id = %s, dist = %.3f" % (path_id, text_id, dist_path_to_text))
                            self.edge_graph[path_id].data.change_line_color(text_objects[text_id].get_text_color())                            
                            text_found = dist_path_to_text
                                        
            if text_found == False: # Text for this branch was not found
                print ("[WARNING]: No proper text found for the path %s; text_found = '%s'" % (path_id, text_found))                 
                n += 1
        print ("Total %i branches were not colored!" % n)

    def color_parents(self):
        for path_id in sorted(self.edge_graph.keys()):
            try:
                self.edge_graph[path_id].select_color()
            except:
                print ("[WARNING]: This path had bad recursion with its children; check it: %s" % path_id)

    def set_size(self, new_size):
        for path_id in self.edge_graph.keys():
            self.edge_graph[path_id].data.set_size(new_size)

def read_svg_file(input_filename):
    file_strings = list()
    text_objects = dict()
    path_objects = dict()
    curr_text_tag = "" 
    curr_tag_type = None   
    input_file = open(input_filename)
    s_number = 0
    for string in input_file:
        s_number += 1
        strip_version = string.strip()
        #---------------------------------------------- 1) Single string per feature
        if (strip_version.split(" ")[0] == "<text") and (strip_version[-7:] == "</text>"):
            new_object = Text_object_svg(strip_version)
            text_objects[new_object.features["id"]] = new_object
            file_strings.append("!%s %s " % ("text", new_object.features["id"]))
            continue
        if (strip_version.split(" ")[0] == "<path") and (strip_version[-2:] == "/>"):
            new_object = Path_object_svg(strip_version)
            path_objects[new_object.features["id"]] = new_object
            file_strings.append("!%s %s " % ("path", new_object.features["id"]))
            continue
        #---------------------------------------------- 2) Not a single string per feature
        if curr_text_tag != "":                 # Text tag reading is in process
           curr_text_tag += " " + strip_version
        else:
           if (strip_version != "<text") and (strip_version != "<path") and (strip_version != "<rect"): # This string is not a new text string
              file_strings.append(string)

        if (strip_version == "<text") or (strip_version == "<path") or (strip_version == "<rect"):  # New <text> or <path> or <rect> tag found
            if curr_text_tag != "":
                print ("Warning: previous required tag was not proceed! Content:")
                print (curr_text_tag)
            curr_text_tag += strip_version
            curr_tag_type = strip_version.strip("<")

        if ((strip_version.count("</text>") != 0) or (strip_version.count("</path>") != 0) or (strip_version.count("</rect>") != 0) or (strip_version.count("/>") != 0) and curr_text_tag != ""): # Terminating tag reading, appending new object
            new_object = None
            try:
                if curr_tag_type == "text":
                    new_object = Text_object_svg(curr_text_tag)
                    text_objects[new_object.features["id"]] = new_object
                elif curr_tag_type == "path":
                    new_object = Path_object_svg(curr_text_tag)
                    path_objects[new_object.features["id"]] = new_object
                elif curr_tag_type == "rect":
                    new_object = Path_object_svg(curr_text_tag)
                    path_objects[new_object.features["id"]] = new_object
                else:
                    print ("FATAL ERROR: <tag_type> is neither 'text' nor 'path' (or 'rect') but '%s'!" % curr_tag_type)
                    print ("String number: '%i'" % s_number)
                    print ("Content: '%s'" % curr_text_tag)
                    sys.exit()
            except KeyError:
                print ("FATAL ERROR: id feature was not found in text object. Content:")
                print (curr_text_tag)
                sys.exit()
            file_strings.append("!%s %s " % (curr_tag_type, new_object.features["id"]))
            curr_text_tag = ""
            curr_tag_type = None
    input_file.close()
    return (file_strings, text_objects, path_objects)

def get_id_order(file_strings, text_objects, my_format_important = True):
    """
    Option <my_format_important> = True will preserve data from My format in the identifiers.
    Make this False to work with the sample of sequences, not with the alignment used to
    produce a tree!
    """
    protein_ids = list()
    text_tags_keys = list(text_objects.keys())
    text_tags_keys = sorted(text_tags_keys, key=lambda k:float(text_objects[k].features["y"])) #FIX: version 2.3
    for text_tag_key in text_tags_keys:
        curr_seq_id = text_objects[text_tag_key].get_seq_id(True, my_format_important)
        if "Tree_scale" in curr_seq_id: #FIX 2.3: iTOL output considered too             
            print ("Label '%s' is technical and will not be considered" % curr_seq_id)
        else:
            protein_ids.append(curr_seq_id)
    """
    for string in file_strings:
        if string[0] == "!": # This is unchanged file string
            curr_type = string.split(" ")[0].strip("!")
            curr_id = string.split(" ")[1]
            try:
                if curr_type == "text":
                    protein_ids.append(text_objects[curr_id].get_seq_id(True, my_format_important))                    
            except KeyError:
                print ("FATAL ERROR: Cannot replace id %s with '%s' tag string!" % (curr_id, curr_type))
                sys.exit()
    """
    return protein_ids

def print_svg_file(output_filename, file_strings, text_objects, path_objects, no_names = None, group = None, group_color = None, remove_support = False, additional_groups = None):
    output_file = open(output_filename, "w")
    n = 0
    m = 0 
    group_label_strings = list() # List of strings with the group labels (if any)
    prev_string = None     
    for string in file_strings:
        if string.strip() == "</g>": # This is the end of the group
            prev_string = string
            continue
        if (additional_groups != None) and (string.strip() == "</svg>") and (prev_string != None): # This is the last string, now <additional_groups> should be written
                for gbk_id in additional_groups.keys():
                    output_file.write('<g id="%s">\n' % gbk_id)
                    for path_tag in additional_groups[gbk_id]:
                        output_file.write("%s\n" % path_tag.create_svg_tag())
                    output_file.write("</g>\n")
                #for group_string in group_label_strings:
                #    output_file.write(group_string + "\n")
        if prev_string != None:        
            output_file.write(prev_string)
            prev_string = None

        if string[0] != "!": # This is unchanged file string
            output_file.write(string)
        else:
            curr_type = string.split(" ")[0].strip("!")
            curr_id = string.split(" ")[1]
            replace_string = None

            if (group != None) and (curr_type == "text"): # Adding group information
                curr_seq_id = text_objects[curr_id].get_seq_id(False)                
                if curr_seq_id in group:                  
                    n += 1
                    text_x = text_objects[curr_id].features["x"]
                    text_y = text_objects[curr_id].features["y"]                    
                    g_num = 0
                    g_width = 10
                    text_objects[curr_id].set_new_x(float(text_x) + float((len(group[curr_seq_id]) + 1) * g_width))
                    for group_name in group[curr_seq_id]: #FIX: version 1.93 (multiple groups are allowed)
                        g_height = 7
                        if g_num == 0:
                            g_height = 14
                        try:
                            curr_color = "#%02x%02x%02x" % (group_color[group_name][0], group_color[group_name][1], group_color[group_name][2])
                        except KeyError:
                            print ("WARNING: Group '%s' was not found in the group colors provided:" % group_name)
                            print (group_color)
                            print ("Sequence ID: '%s'; group data: '%s'" % (curr_seq_id, group[curr_seq_id]))
                            sys.exit()                                                           
                        new_path_object = Path_object_svg('<rect style="fill:%s;opacity:1.0" id="rect%s"\
                                                           width="%s"\
                                                           height="%s"\
                                                           x="%s"\
                                                           y="%s" />' % (curr_color, n, g_width, g_height,
                                                                         float(text_x) + g_width + (g_width * g_num), float(text_y) - g_height))
                        output_file.write(new_path_object.create_svg_tag() + "\n")
                        g_num += 1
                    #group_label_strings.append(new_path_object.create_svg_tag())

            try:
                if curr_type == "text":
                    if text_objects[curr_id].is_support(): #FIX: version 1.8
                        if remove_support == True: # Support should be removed                    
                            continue
                        elif remove_support == False: # Support should not be removed (normal case)
                            replace_string = text_objects[curr_id].create_svg_tag()
                        else: #FIX: version 1.9 Support should be replaced with the circle 
                            circle_params = re.match("(\d+)_(\d+)_(\d+)", remove_support)
                            if circle_params == None:
                                print ("WARNING: failed to replace bootstrap with circles! <remove_support> was '%s'" % remove_support)
                                continue
                            try:
                                (good, poor, size) = (int(circle_params.group(1)), int(circle_params.group(2)), int(circle_params.group(3)))
                                curr_bootstrap = int(text_objects[curr_id].content)
                                fill = "#ffffff"
                                if curr_bootstrap < poor:
                                    continue
                                elif curr_bootstrap > good:
                                    fill = "#000000" # Filled circle
                                text_x = text_objects[curr_id].features["x"]
                                text_y = text_objects[curr_id].features["y"]
                                m += 1                                  
                                #print ("Size: %s, x = %s, y = %s, fill = %s, number = %s" % (size, float(text_x), float(text_y), fill, m))
                                new_path_object = Path_object_svg('<circle r="%s" cx="%s" cy="%s"\
                                                                   style="fill:%s;fill-opacity:1;stroke:#000000;stroke-width:1"\
                                                                   id="circle%s" />' % (size, float(text_x) + size, float(text_y) - size, fill, m))
                                replace_string = new_path_object.create_svg_tag()
                            except ValueError:
                                print ("WARNING: failed to replace bootstrap with circles! <remove_support was '%s'" % remove_support)
                    else:
                            replace_string = text_objects[curr_id].create_svg_tag()
                if curr_type == "path":
                    replace_string = path_objects[curr_id].create_svg_tag()
                if curr_type == "rect":
                    replace_string = path_objects[curr_id].create_svg_tag()

            except KeyError:
                print ("FATAL ERROR: Cannot replace id %s with '%s' tag string!" % (curr_id, curr_type))
                sys.exit()
            if ((curr_type == "text") and (no_names != True)) or (curr_type == "path") or (curr_type == "rect") or (not text_objects[curr_id].is_leaf()):
                output_file.write(replace_string + "\n") 
    output_file.close()