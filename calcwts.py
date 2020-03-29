###########################################################
## File: tokenize.py
## Project: CMSC 476 Project, Phase 1
## Author: Kate Atwell
## Date: 2/12/2020
## Section: 01
## Email: akath1@umbc.edu
## 
## This file contains a program that takes in a directory
## of HTML files and tokenizes them, then compiles the
## tokens together across all documents in the directory
## and calculates the frequency of each token. It then
## writes three files: one containing the tokens sorted
## in alphabetical order, another containing the tokens
## sorted in descending order by frequency, and the last
## one containing the names of all of the files contained
## in the given directory. All of these files are stored
## in a new directory whose name is given by the user.

import getopt
import html2text
import math
import os
import shutil
import sys
import time

"""TODO:
-Remove unneeded code
-Remove stopwords
-Remove words that occur only once
-Remove single-letter/character words
"""

# Uses html2text to tokenize documents in inputdir and 
# creates corresponding tokenized files in outputdir.
# Pre: takes in two strings, one with the name of the 
#      input directory and one with the name of the 
#      output directory
# Post: Adds tokenized files to the output directory        
def convert_to_text(inputdir, outputdir):
  tokens_dict = {}
  directory = inputdir
  num_files = 0

  stopwords = []
  with open("stoplist.txt") as stopwords_list:
    stopwords_file = stopwords_list.read()
    stopwords = stopwords_file.split()
    stopwords = [i.strip() for i in stopwords]

  for filename in os.listdir(directory):
    if filename.endswith(".html"): 
      h = html2text.HTML2Text()
      h.ignore_images = True
      h.ignore_links = True
      h.escape_all = True
      with open(inputdir + "/" + filename, encoding='latin-1') as html_file:
        html = html_file.read()
        text = h.handle(html)
        tokens = text.split()
        tokens = [i.strip() for i in tokens]
      with open(outputdir + "/tokens/" + filename[:-5] + ".txt", 'w') as new_file:
        for token in tokens:
          new_token = tokenize(token)
          if new_token not in stopwords and new_token != "":
            new_file.write(new_token + "\n")
            if not new_token in tokens_dict:
              tokens_dict[new_token] = []
            tokens_dict[new_token].append(filename)
            num_files += 1
            continue

  return tokens_dict, num_files

# Creates dictionary that will contain the filenames and corresponding
# weights for each token.
# Pre:  takes in the dictionary of tokens
# Post: outputs a dictionary with key-value pairs of the tokens and 
#       an empty list to be filled later with tuples of filename-weight
#       pairs 
def create_weights_dict(tokens_dict):
  weights_dict = {}
  for key, value in sorted(tokens_dict.items()):
    weights_dict[key] = []
  return weights_dict

# Adds tokens from tokenized files in outputdir to
# new dictionary. 
# Pre: takes in string with the name of the output
#      directory
# Post: returns dictionary containing tokens from all
#      files and the name of the file they were found
#      in at each occurrence  
def tokenize(token):
  token = token.lower()
  first_char = token[0]
  last_char = token[-1]
  i=len(token) - 1
  
  while (len(token) > 0 and i>=0):
    if (ord(token[i]) < 65 or ord(token[i]) > 122 or (ord(token[i]) > 90 and ord(token[i]) < 97)):
      if (i<len(token) - 1):
        temp = token[:i] + token[i+1:]
      elif (i==0):
        temp = token[i+1:]
      else:
        temp = token[:i]
      token = temp
    i-=1
  return token


# Takes in existing dictionary filled with tokens and removes tokens
# with either a length of 1 or a frequency of 1 (ones in stoplist 
# have already been removed).
# Pre:  dictionary with all tokens from input files
# Post: dictionary is returns with all invalid tokens removed
def remove_unneeded_tokens(tokens_dict):
  with open("stoplist.txt") as f:
    stopwords_file = f.read()
    stopwords = stopwords_file.split()
    stopwords = [i.strip() for i in stopwords]
  for key, value in sorted(tokens_dict.items()):
    if (len(value) == 1 or len(key) == 1):
      del tokens_dict[key]
  return tokens_dict


# Writes the tfidf scores of each token in each doc to a corresponding
# ".wts" file.
# Pre:  Takes in the name of the directory in which to store the weights,
#       the dictionary of all valid tokens, the total number of files, and
#       the dictionary that will contain the weights for all valid tokens
# Post: Writes calculated weights to ".wts" file for each text file and 
#       populates the weights_dict with weights for each file where it occurs
def write_token_weights(outputdir, tokens_dict, num_files, weights_dict):
  directory = outputdir + "/tokens/";
  filenames = []
  for filename in os.listdir(directory):
    filenames.append(filename)
  filenames.sort()

  for filename in filenames:
    weights = calc_tfidf(outputdir, filename, tokens_dict, num_files)
    sorted_by_weights = []
    for key, value in sorted(weights.items(), key = lambda x: x[1], reverse=True):
      sorted_by_weights.append((key, value))
      weights_dict[key].append((filename[:-4], value))
    write_tuple_list_to_file(sorted_by_weights, outputdir + "/weights", filename[:-4] + ".wts", False)
    #return weights_dict

      
# Calculates tfidf score for each token in file.
# Pre:  Given the directory and name of the current file, dict
#       containing all valid tokens, and total number of input
#       files
# Post: Returns dictionary containing the tfidf for each token
def calc_tfidf(outputdir, filename, all_tokens, num_html_docs):
  weights = {}
  with open(outputdir + "/tokens/" + filename) as f:
    file_contents = f.read()
    tokens_in_file = file_contents.split()
    tokens_in_file = [i.strip() for i in tokens_in_file]
    num_tokens = 0
    for token in tokens_in_file:
      # if a token is a valid token that has not been removed from the dictionary
      if token in all_tokens and token not in weights:
        num_tokens += 1
        #counts number of occurrences of token in filename
        tf = all_tokens[token].count(filename[:-4] + ".html") 
        #counts number of unique values in list of occurrences
        df = len(set(all_tokens[token])) 
        n = num_html_docs
        weight = tf*math.log(n/df)
        weights[token] = weight
    for token in weights:
      weights[token] /= num_tokens #normalize tfidf calculation
  return weights

    
# Writes contents of list_of_tuples to a file in outputdir with
# the specified filename.
# Pre: list of (string, int) tuples containing (token, frequency),
#      name of outputdir as string, filename as string
# Post: a file is created and written to which contains each token
#       and its frequency (across every file in inputdir)
def write_tuple_list_to_file(list_of_tuples, outputdir, filename, ranks):
  f= open(outputdir + "/" + filename,"w+")

  #if writing ranks of values to file
  if ranks == True:
    rank = 1
    if len(list_of_tuples) > 0:
      f.write(str(list_of_tuples[0][0]) + "," + str(rank) + "," + str(list_of_tuples[0][1]) + "\n")
    for i in range(1, len(list_of_tuples)):
      if list_of_tuples[i][1] != list_of_tuples[i-1][1]:
        rank += 1
      f.write(str(list_of_tuples[i][0]) + "," + str(rank) + "," + str(list_of_tuples[i][1]) + "\n")

  #otherwise
  else:
    for i in range(0, len(list_of_tuples)):
      f.write(str(list_of_tuples[i][0]) + "," + str(list_of_tuples[i][1]) + "\n")
  
# Writes contents from weights_dict to dictionary file
# Pre:  dictionary with the token as the key and a list of (filename, weight)
#       tuples
# Post: file formatted as such: token/n number of occurrences/n 
#       line of first occurrence in posting/n for each token
def write_dictionary_file(outputdir, weights_dict):
  f = open(outputdir + "/dictionary.txt", "w+")
  first_occurrence = 1
  for key, value in weights_dict.items():
    f.write(key + "\n" + str(len(value)) + "\n" + str(first_occurrence) + "\n")
    first_occurrence += len(value)

# Writes contents from weights_dict to postings file
# Pre:  dictionary with the token as the key and a list of (filename, weight)
#       tuples
# Post: file formatted as such for each occurrence of each token in dict
#       sorted in order of tokens: filename, weight in file\n
def write_postings_file(outputdir, weights_dict):
  f = open(outputdir + "/postings.txt", "w+")
  for key, value in weights_dict.items():
    for i in value:
      f.write(i[0] + "," + str(i[1]) + "\n")

# Creates directory.txt, a file in outputdir that contains
# a list of the names of all files in inputdir.
# Pre: strings with name of inputdir and outputdir
def create_directory_file(inputdir, outputdir):
  f= open("output_files/directory.txt","w+")
  directory = inputdir
  for filename in os.listdir(directory):
    ends_with_str = ".html"
    if filename.endswith(".html"): 
      f.write(filename + "\t" + "tokenized-" + filename + "\n") # TODO: change from .html to .txt
      continue
    else:
      continue
  
# to run: type python3 calcwts.txt <inputdir> <outputdir>  
def main(argv):
  start_time_sec = time.time()
  start_time_cpu = time.process_time()
  
  inputdir = ''
  outputdir = ''
  
  # get inputdir and outputdir from command line args
  try:
    opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
  except getopt.GetoptError:
    print('tokenize.py <inputdir> <outputdir>')
    sys.exit(2)
    
  inputdir = args[0]
  outputdir = args[1]
  
  # recursively removes outputdir and all of its files
  # if it already exists (mostly for testing purposes)
  if os.path.exists(outputdir):
    shutil.rmtree(outputdir)
    
  os.mkdir(outputdir)
  os.mkdir(outputdir + "/tokens")
  os.mkdir(outputdir + "/weights")
  
  # tokenize html docs and sort tokens as required
  tokens, num_files = convert_to_text(inputdir, outputdir)
  updated_tokens = remove_unneeded_tokens(tokens)
  weights = create_weights_dict(updated_tokens)
  write_token_weights(outputdir, updated_tokens, num_files, weights)
  write_dictionary_file(outputdir, weights)
  write_postings_file(outputdir, weights)
  # write directory with list of files
  create_directory_file(inputdir, outputdir)

  print("Time elapsed(sec): ", time.time() - start_time_sec)
  print("Time elapsed(CPU): ", time.process_time() - start_time_cpu)
  
# to use: python3 tokenize.py <inputdir> <outputdir>  
if __name__ == "__main__":
  main(sys.argv[1:])
