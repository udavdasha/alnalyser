<img src="https://github.com/udavdasha/alnalyser/blob/master/images/adv_image.png" alt="Alnalyser preview">

# alnalyser
**Your helper for a reasonable work with multiple sequence alignments (in bioinformatics)**

This software is aimed to help in a daily routine work of a bioinformatician who works with multiple 
sequence alignments and uses them further to build phylogenetic trees. Briefly, it is a graphical interface
which allows to maintain multiple projects with sequence alignment and additional data for it. First, it
can map information about hits of profile HMMs from a certain database on the sequence alignment, including
predictions of transmembrane helices. Also it can be used to remove poorly aligned or truncated sequences in 
semi-automated mode. Finally, as a small cherry on top, it has a sequence format converter which allows to 
convert all main sequence formats (NCBI, Uniprot, PDB etc) into more convenient format for working with
multiple alignment and phylogenetic tree.

Please visit our web page for other bioinformatical tools and more info: http://boabio.belozersky.msu.ru/en/scientific-group

# Dependencies
The script is written in Python2.7 / Tkinter, and I hope soon it will also work smoothly on Python3+!

One questionable feature of this piece of software is that it does NOT utilize specific bioinformatical
python modules (like biopython), but instead in several steps it uses native binary programs.
* **muscle** (https://drive5.com/muscle/downloads_v3.htm) - for multiple alignment (use version 3.8.31)
* **hmmbuild, hmmsearch and hmmscan** from HMMer (http://hmmer.org/) - for similary searches with profiles

In order to work with the 'Features' tab, which from my point of view is a very nice idea, one should have two
databases of sequence profiles:
* **Pfam** (get a release from here: https://www.ebi.ac.uk/interpro/download/pfam/)
* **COG** (look for a button "Download all HMM profiles" here: https://depo.msu.ru/module/cogcollator)

As mentioned above, Alnalyser can store and work out information about transmembrane helices predictions
in the format given by the **DeepTMHMM** (https://dtu.biolib.com/DeepTMHMM). Please use the .gff3 output format
and copy the result into the corresponding window.

# Running
You can run Alnalyser with a settings filename as a single argument. For example:
```
python Alnalyser.py dummy_settings.ini
```
If the script is opened without any argument, it will try to load settings from the file *settings.ini*.

# Acknowledgements
Creation of this tool was supported by the Dmitry Zimin's Dynasty Foundation, grant for young biologists, 2014
