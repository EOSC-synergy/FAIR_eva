from bs4 import BeautifulSoup
import idutils
import pandas as pd
import xml.etree.ElementTree as ET
import re
import requests
import urllib

def is_persistent_id(item_id):
    """ is_persistent_id
    Returns boolean if the item id is or not a persistent identifier
    Parameters
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID ...), or an internal (e.g. an
        identifier from the repo)
    Returns
    -------
    boolean
        True if the item id is a persistent identifier. False if not
    """
    if len(idutils.detect_identifier_schemes(item_id)) > 0:
        return True
    else:
        return False
    
def find_ids_in_metadata(metadata, elements):
    """ find_ids_in_metadata
    Returns the list of identifiers found in metadata nad its types
    Parameters
    ----------
    metadata: data frame with the following columns: metadata_schema, element, text_value, qualifier
              contains the metadata of the digital object to be analyzed
    elements: list of the metadata elements where the identifier can be found
    
    Returns
    -------
    identifiers
        Data frame with the list of identifiers and its types
    """
    identifiers = []
    for (index, row) in metadata.iterrows():
        if row['element'] in elements:
            if is_persistent_id(row['text_value']):
                identifiers.append([row['text_value'], idutils.detect_identifier_schemes(row['text_value'])])
            else:
                identifiers.append([row['text_value'], None])
    ids_list = pd.DataFrame(identifiers, columns=['identifier', 'type'])
    return ids_list

def check_metadata_terms(metadata, terms):
    """ check_metadata_terms
    Checks if the list of expected terms are or not in the metadata
    Parameters
    ----------
    metadata: data frame with the following columns: metadata_schema, element, text_value, qualifier
              contains the metadata of the digital object to be analyzed
    terms: list of the metadata terms expected. DataFrame  where the identifier can be found
        columns: terms, qualifier
    
    Returns
    -------
    checked_terms
        Data frame with the list of terms found and not found
    """
    print(metadata) 
    found = []
    for e in terms.iterrows():
        found.append(0)
    terms['found'] = found
    
    for (index, row) in metadata.iterrows():
        if row['element'] in terms.term.tolist():
            if row['qualifier'] == terms.qualifier[terms[terms['term'] == row['element']].index.values[0]]:
                terms.found[terms[terms['term'] == row['element']].index.values[0]] = 1
    return terms


def find_dataset_file(metadata, url, data_formats):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, features="html.parser")

    msg = 'No dataset files found'
    points = 0

    data_files = []
    for tag in soup.find_all("a"):
        for f in data_formats:
            try:
                if f in tag.get('href'):
                    data_files.append(tag.get('href'))
            except Exception as e:
                pass

    if len(data_files) > 0:
        points = 100
        msg = "Potential datasets files found: %s" % data_files

    return points, msg, data_files


def metadata_human_accessibility(metadata, url):
    msg = ''
    points = 0
    response = requests.get(url, verify=False)

    found_items = 0
    for index, text in metadata.iterrows():
        if text['text_value'] in response.text:
            print("FOUND: %s" % text['text_value'])
            found_items = found_items + 1

    msg = msg + "Found metadata terms (Human accesibility): %i/%i" % (found_items, len(metadata))
    points = (found_items * 100) / len(metadata)
    return points, msg
