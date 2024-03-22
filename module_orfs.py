import os
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


def openFile(NameFile):
    F=open(NameFile, "r")
    L=F.readlines()
    return L 


def extract_orfs(sequence, transc_name, dico_orfs):
    list_stops = ["TAG", "TAA", "TGA"]
    min_size = 91
    max_size = 9000
    compteur = 1

    start_pos = 0
    ## Frame 1
    if len(sequence) >= min_size:
        while start_pos < 3:
            iter = start_pos
            while iter < (len(sequence)+1-min_size):#in range(start_pos, (len(sequence)+1-min_size), 3):
                start = sequence[iter:iter+3].upper()
                stop_attributed = False
                if start == "ATG":
                    
                    for iter2 in range((iter + 3) , iter + max_size, 3):
                        if iter2 + 2 < len(sequence):
                            stop = sequence[iter2:iter2+3].upper()
                            if stop in list_stops:
                                if (iter2 + 3 - iter) < min_size:
                                    break
                                else:
                                    my_orf = sequence[iter:iter2]
                                    official_start = str(iter + 1)
                                    official_stop = str(iter2)
                                    new_orf_name = transc_name + "_" + str(compteur) + "_" + official_start + "_" + official_stop
                                    dico_orfs[new_orf_name] = my_orf
                                    compteur += 1
                                    stop_attributed = True
                                    break
                        else:
                            break
                if stop_attributed == True:
                    iter = iter2+3
                else:
                    iter += 3
            start_pos += 1
    

                          


def my_get_orfs(file_name):
    dico_orfs = {}
    c = 1
    for seq_record in SeqIO.parse(file_name, "fasta"):
        ID_seq = str(seq_record.id)
        sequence = str(seq_record.seq)
        extract_orfs(sequence, ID_seq, dico_orfs)
    return dico_orfs


def remove_orfs_end_transcript(dico_orfs, dico_transcripts):
    """
    This function performs the first step of ORF cleaning. The software getORF that we use makes a mistake:
    if a sequence starting with an ATG and a triplet code ends by the end of a transcript, the software considers
    that it is an ORF, while it does not have a stop codon. This function takes the dictionary of all transcripts
    and the one with all ORFs as input, and removes all ORFs that end by the end of the transcript
    (final codon size of 0, 1, or 2). It returns a dictionary cleaned of the wrong ORFs.
    """

    # Initialize a dictionary to store corrected ORFs
    dico_orf_corrected = {}

    # Iterate through each ORF in the dictionary of all ORFs
    for orf_name in dico_orfs.keys():
        # Extract the transcript ID from the ORF name
        transcript_of_orf = orf_name.split("_")[0]

        # Extract the position of the end of the ORF from the ORF name
        pos_end_orf = int(orf_name.split("_")[3])

        # Calculate the size of the transcript
        size_transcript = len(dico_transcripts[transcript_of_orf])

        # Check if the ORF does not end by the end of the transcript (final codon size > 2)
        if size_transcript - pos_end_orf > 2:
            # Store the corrected ORF in the dictionary
            dico_orf_corrected[orf_name] = dico_orfs[orf_name]

    # Return the dictionary of corrected ORFs
    return dico_orf_corrected


def build_dict_orfs_per_transcript(dict_orfs):
    """
    This function creates a dictionary with transcripts as keys and lists of their corresponding ORFs as items.
    It takes a dictionary of ORFs as input and returns the new dictionary.
    """

    # Initialize an empty dictionary to store transcripts and their corresponding ORFs
    dict_transcrit_all_orfs = {}

    # Iterate through each ORF in the input dictionary
    for orf in dict_orfs.keys():
        # Extract the transcript name from the ORF
        transcript_name = orf.split("_")[0]

        # Update the dictionary with the transcript and its corresponding ORF
        if transcript_name not in dict_transcrit_all_orfs.keys():
            dict_transcrit_all_orfs[transcript_name] = [orf]
        else:
            dict_transcrit_all_orfs[transcript_name].append(orf)

    # Return the dictionary with transcripts and their corresponding ORFs
    return dict_transcrit_all_orfs


class Gene():
    def __init__(self, dict_transcripts_assoc_orfs, gene_name, dict_orf_seq, dict_transcript_seq):
        """
        Constructor for the Gene class.
        
        Parameters:
        - dict_transcripts_assoc_orfs: Dictionary with genes as keys and lists of associated ORFs as items.
        - gene_name: Name of the gene.
        - dict_orf_seq: Dictionary with ORF names as keys and their sequences as items.
        - dict_transcript_seq: Dictionary with transcript names as keys and their sequences as items.
        """
        self.dict_transcripts_assoc_orfs = dict_transcripts_assoc_orfs
        self.gene_name = gene_name
        self.dict_orf_seq = dict_orf_seq
        self.dict_transcript_seq = dict_transcript_seq
        
        
    def get_highest_kozac(self):
        # Initialize dictionaries to store Kozac scores
        dict_kozac_predicted_strg = {}
        dict_kozac_relative_strg = {}  # Note: I do not know which dict is the most relevant; so far, the program uses the dict predicted score.

        # Open the Kozac prediction file
        my_kozac_file = openFile("KCS-predicted.tsv")

        # Iterate through lines in the Kozac file
        for line in my_kozac_file[1:]:
            line = line.split("\n")[0]
            # Split line information into parts
            kozak_seq = line.split(",")[0]
            predicted_strg = int(line.split(",")[1])
            rel_strength = float(line.split(",")[2])

            # Populate the dictionaries with Kozac scores
            dict_kozac_predicted_strg[kozak_seq] = predicted_strg
            dict_kozac_relative_strg[kozak_seq] = rel_strength

        # Initialize a list to store transcripts to be removed
        list_transcript_to_remove = []

        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            best_kozac = 0
            highest_orf = []
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                orf_start_0_python_indent = int(orf_name.split("_")[2]) - 1
                orf_start_3_python_indent = orf_start_0_python_indent + 3

                # Check if the ORF start is beyond the first 3 nucleotides
                if orf_start_0_python_indent > 3:
                    # Extract the Kozac sequence
                    my_kozac = self.dict_transcript_seq[transcript_name][
                            orf_start_0_python_indent - 4:orf_start_3_python_indent + 1]
                    my_kozac = my_kozac.upper()

                    # Retrieve the Kozac score from the predicted dictionary
                    if my_kozac in dict_kozac_predicted_strg.keys():
                        my_kozac_score = dict_kozac_predicted_strg[my_kozac]
                    else:
                        my_kozac_score = "na"

                    # Update the best Kozac score and associated ORFs
                    if my_kozac_score != "na" and my_kozac_score > best_kozac:
                        best_kozac = my_kozac_score
                        highest_orf = [orf_name]
                    elif my_kozac_score == best_kozac:
                        highest_orf.append(orf_name)

            # Update the transcript's associated ORFs with the highest Kozac score
            if len(highest_orf) > 0:
                self.dict_transcripts_assoc_orfs[transcript_name] = highest_orf
            else:
                # If the transcript only has an ORF and cannot have a Kozac score because it is too close to the start,
                # remove the transcript from the list of transcripts having an ORF.
                list_transcript_to_remove.append(transcript_name)

        # Remove transcripts without a valid ORF
        if len(list_transcript_to_remove) > 0:
            for transcript_name in list_transcript_to_remove:
                del (self.dict_transcripts_assoc_orfs[transcript_name])
        # print (self.dict_transcripts_assoc_orfs)

        
    def get_threeshold_kozac(self, min_score):
        # Initialize dictionaries to store Kozac scores
        dict_kozac_predicted_strg = {}
        dict_kozac_relative_strg = {}

        # Open the Kozac prediction file
        my_kozac_file = openFile("KCS-predicted.tsv")

        # Iterate through lines in the Kozac file
        for line in my_kozac_file[1:]:
            line = line.split("\n")[0]
            # Split line information into parts
            kozak_seq = line.split(",")[0]
            predicted_strg = int(line.split(",")[1])
            rel_strength = float(line.split(",")[2])

            # Populate the dictionaries with Kozac scores
            dict_kozac_predicted_strg[kozak_seq] = predicted_strg
            dict_kozac_relative_strg[kozak_seq] = rel_strength

        # Initialize a list to store transcripts to be removed
        list_transcript_to_remove = []

        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            highest_orf = []
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                orf_start_0_python_indent = int(orf_name.split("_")[2]) - 1
                orf_start_3_python_indent = orf_start_0_python_indent + 3

                # Check if the ORF start is beyond the first 3 nucleotides
                if orf_start_0_python_indent > 3:
                    # Extract the Kozac sequence
                    my_kozac = self.dict_transcript_seq[transcript_name][
                            orf_start_0_python_indent - 4:orf_start_3_python_indent + 1]
                    my_kozac = my_kozac.upper()

                    # Retrieve the Kozac score from the predicted dictionary
                    if my_kozac in dict_kozac_predicted_strg.keys():
                        my_kozac_score = dict_kozac_predicted_strg[my_kozac]
                    else:
                        my_kozac_score = "na"

                    # Check if the Kozac score is above or equal to the specified threshold
                    if my_kozac_score != "na" and my_kozac_score >= min_score:
                        highest_orf.append(orf_name)

            # Update the transcript's associated ORFs with those above the threshold
            if len(highest_orf) > 0:
                self.dict_transcripts_assoc_orfs[transcript_name] = highest_orf
            else:
                # If the transcript only has an ORF and cannot have a Kozac score due to proximity to the start,
                # remove the transcript from the list of transcripts having an ORF.
                list_transcript_to_remove.append(transcript_name)

        # Remove transcripts without a valid ORF
        if len(list_transcript_to_remove) > 0:
            for transcript_name in list_transcript_to_remove:
                del (self.dict_transcripts_assoc_orfs[transcript_name])
        # print (self.dict_transcripts_assoc_orfs)


    def get_longest_orf(self):
        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Initialize variables to store information about the longest ORF
            max_orf_len = 0
            longest_orf = ""

            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                # Check the length of the current ORF
                if len(self.dict_orf_seq[orf_name]) > max_orf_len:
                    # Update information if the current ORF is longer
                    max_orf_len = len(self.dict_orf_seq[orf_name])
                    longest_orf = orf_name

            # Update the transcript's associated ORFs with the longest ORF
            self.dict_transcripts_assoc_orfs[transcript_name] = longest_orf
        # print (self.dict_transcripts_assoc_orfs)

        
    def get_start_first_orf(self):
        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Initialize variables to store information about the first ORF
            orf_start_point = 10000000000000
            start_first_orf = ""

            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                # Extract the start position of the current ORF
                orf_start = int(orf_name.split("_")[2])

                # Check if the start position is earlier than the current recorded start point
                if orf_start < orf_start_point:
                    # Update information if the current ORF starts earlier
                    orf_start_point = orf_start
                    start_first_orf = orf_name

            # Update the transcript's associated ORFs with the first ORF
            self.dict_transcripts_assoc_orfs[transcript_name] = start_first_orf
        # print (self.dict_transcripts_assoc_orfs)
        
        
    def min_size_utr(self, five_min, three_min):
        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Initialize lists to store information about ORFs that meet the size criteria
            new_list_orf = []
            
            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                # Extract the start and stop positions of the current ORF
                orf_start = int(orf_name.split("_")[2])
                orf_stop = int(orf_name.split("_")[3])
                
                # Extract the length of the current transcript
                transcript_length = len(self.dict_transcript_seq[transcript_name])

                # Check if the ORF meets the size criteria
                if orf_start > five_min and orf_stop < transcript_length - three_min:
                    # Add the ORF to the new list if it meets the size criteria
                    new_list_orf.append(orf_name)

            # Update the transcript's associated ORFs with the filtered list of ORFs
            if len(new_list_orf) > 0:
                self.dict_transcripts_assoc_orfs[transcript_name] = new_list_orf
            else:
                # If no ORFs meet the size criteria, remove the transcript from the dictionary
                del(self.dict_transcripts_assoc_orfs[transcript_name])

        # Print the updated dictionary of associated ORFs
        # print(self.dict_transcripts_assoc_orfs)


    def handle_orf_duplicate_per_transcript(self):
        # Create a dictionary to map each unique ORF sequence to its corresponding ORF name
        dict_reverse_orf_to_transcript = {}

        # Iterate through transcripts with associated ORFs
        for transcript_name in self.dict_transcripts_assoc_orfs.keys():
            list_orfs = self.dict_transcripts_assoc_orfs[transcript_name]

            # Iterate through ORFs in the current transcript
            for orf_name in list_orfs:
                # Extract the ORF sequence
                orf_seq = self.dict_orf_seq[orf_name]

                # Map the ORF sequence to its ORF name in the reverse dictionary
                dict_reverse_orf_to_transcript[orf_seq] = orf_name

        # Reset the dictionary of associated ORFs for transcripts
        self.dict_transcripts_assoc_orfs = {}

        # Rebuild the dictionary using the reverse mapping of unique ORF sequences
        for orf_seq in dict_reverse_orf_to_transcript.keys():
            orf_name = dict_reverse_orf_to_transcript[orf_seq]
            transcript_name = orf_name.split("_")[0]

            # Add the ORF name to the list of associated ORFs for the transcript
            if transcript_name not in self.dict_transcripts_assoc_orfs.keys():
                self.dict_transcripts_assoc_orfs[transcript_name] = [orf_name]
            else:
                self.dict_transcripts_assoc_orfs[transcript_name].append(orf_name)

        # Print the updated dictionary of associated ORFs for transcripts
        # print(self.dict_transcripts_assoc_orfs)


def generate_list_genes_objects(dict_gene_transcripts, dict_transcript_orf, dict_ORFs_fasta, dict_transcript_fasta):
    # Initialize an empty list to store Gene objects
    list_gene_object = []

    # Iterate through genes in the dictionary of gene transcripts
    for gene_name in dict_gene_transcripts.keys():
        # Create a dictionary to store transcripts with associated ORFs
        dict_transcripts_with_orfs = {}

        # Get the list of transcripts for the current gene
        list_transcripts = dict_gene_transcripts[gene_name]

        # Iterate through transcripts
        for transcript_name in list_transcripts:
            # Check if the transcript has associated ORFs
            if transcript_name in dict_transcript_orf.keys():
                # Add the transcript and its associated ORFs to the dictionary
                dict_transcripts_with_orfs[transcript_name] = dict_transcript_orf[transcript_name]

        # Check if there are transcripts with associated ORFs for the current gene
        if len(dict_transcripts_with_orfs) > 0:
            # Extract the name of the gene
            name_of_my_gene = gene_name

            # Create dictionaries to store transcript sequences and ORF sequences
            dict_transcript_seqs = {}
            dict_orf_seq = {}

            # Iterate through transcripts with associated ORFs
            for transcript_name in dict_transcripts_with_orfs.keys():
                # Add the transcript sequence to the dictionary
                dict_transcript_seqs[transcript_name] = dict_transcript_fasta[transcript_name]

                # Iterate through ORFs associated with the current transcript
                for orf_name in dict_transcripts_with_orfs[transcript_name]:
                    # Add the ORF sequence to the dictionary
                    dict_orf_seq[orf_name] = dict_ORFs_fasta[orf_name]

            # Create a Gene object with the collected information and add it to the list
            gene_instance = Gene(dict_transcripts_with_orfs, name_of_my_gene, dict_orf_seq, dict_transcript_seqs)
            list_gene_object.append(gene_instance)

    # Return the list of Gene objects
    return list_gene_object


def sort_orfs_by_properties(filter_gene, list_gene_object, option_list, dict_all_ORFs_purge1, dict_gene_status):
    # Initialize dictionaries to store filtered transcripts and all filtered ORFs
    dict_transcrit_filtered_orfs = {}
    dict_all_ORFs_filtered = {}

    # Iterate through each Gene object in the list
    for gene_object in list_gene_object:
        # Iterate through each option in the provided list of options
        discard_gene = False
        if "duplicate_handle" not in option_list:
            option_list.append("duplicate_handle")
        for option in option_list:
            # Check the type of option and call the corresponding method in the Gene object
            if option[0] == "kozac_threeshold":
                gene_object.get_threeshold_kozac(option[1])
            elif option[0] == "kozac_highest":
                gene_object.get_highest_kozac()
            elif option[0] == "longest":
                gene_object.get_longest_orf()
            elif option[0] == "start_first":
                gene_object.get_start_first_orf()
            elif option[0] == "utr_size":
                gene_object.min_size_utr(option[1], option[2])
            elif option[0] == "duplicate_handle":
                gene_object.handle_orf_duplicate_per_transcript()
            if filter_gene == True:
                if dict_gene_status[gene_object.gene_name] == "genic":
                    discard_gene = True
                

        # Iterate through the transcripts associated with the current Gene object (is the user want a denovo gene, only these will be written)
        if discard_gene == False:
            for transcript_name in gene_object.dict_transcripts_assoc_orfs.keys():
                # Update the dictionary with filtered transcripts and associated ORFs
                dict_transcrit_filtered_orfs[transcript_name] = gene_object.dict_transcripts_assoc_orfs[transcript_name]

                # Iterate through the associated ORFs and update the dictionary with all filtered ORFs
                for orf_name in gene_object.dict_transcripts_assoc_orfs[transcript_name]:
                    dict_all_ORFs_filtered[orf_name] = dict_all_ORFs_purge1[orf_name]

    # Return the dictionaries with filtered transcripts and all filtered ORFs
    return dict_transcrit_filtered_orfs, dict_all_ORFs_filtered
