from bs4 import BeautifulSoup
import idutils
import pandas as pd
import xml.etree.ElementTree as ET
import re
import requests
import urllib

def oai_identify(oai_base):
    action = "?verb=Identify"
    print("Request to: %s%s" % (oai_base, action))
    return oai_request(oai_base, action)


def oai_metadataFormats(oai_base):
    action = '?verb=ListMetadataFormats'
    print("Request to: %s%s" % (oai_base, action))
    xmlTree = oai_request(oai_base, action)
    metadataFormats = {}
    for e in xmlTree.findall('.//{http://www.openarchives.org/OAI/2.0/}metadataFormat'):
        metadataPrefix = e.find('{http://www.openarchives.org/OAI/2.0/}metadataPrefix').text
        namespace = e.find('{http://www.openarchives.org/OAI/2.0/}metadataNamespace').text
        metadataFormats[metadataPrefix] = namespace
    return metadataFormats

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

def oai_check_record_url(oai_base, metadata_prefix, pid):
    endpoint_root = urllib.parse.urlparse(oai_base).netloc
    pid_type = idutils.detect_identifier_schemes(pid)[0]
    oai_pid = idutils.normalize_pid(pid, pid_type)
    action = "?verb=GetRecord"
    
    test_id = "oai:%s:%s" % (endpoint_root, oai_pid)
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    url_final = ''
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags.text)
        error = error + 1
    if error == 0:
        url_final = url
    
    
    test_id = "%s:%s" % (pid_type, oai_pid)
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags)
        error = error + 1
    if error == 0:
        url_final = url
    
    test_id = "oai:%s:%s" % (endpoint_root, oai_pid[oai_pid.rfind(".")+1:len(oai_pid)])
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags)
        error = error + 1
    if error == 0:
        url_final = url
    
    return url_final


def oai_get_metadata(url):
    oai = requests.get(url)
    xmlTree = ET.fromstring(oai.text)
    return xmlTree


def oai_request(oai_base, action):
    oai = requests.get(oai_base + action) #Peticion al servidor
    xmlTree = ET.fromstring(oai.text)
    return xmlTree

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

def check_controlled_vocabulary(value):
    cv_msg = None
    cv = None
    if 'id.loc.gov' in value:
        cv_msg = "Library of Congress - Controlled vocabulary. Data: %s" % loc_basic_info(value)
        cv = 'id.loc.gov'
    elif 'orcid' in idutils.detect_identifier_schemes(value):
        cv_msg = "ORCID. Data: %s" %orcid_basic_info(value)
        cv = 'orcid'
    elif 'geonames.org' in value:
        cv_msg = "Geonames - Controlled vocabulary. Data: %s" % geonames_basic_info(value)
        cv = 'geonames.org'
    return cv_msg

def controlled_vocabulary_pid(value):
    cv_pid = None
    if 'id.loc.gov' in value:
        cv_pid = "http://www.loc.gov/mads/rdf/v1#"
    elif 'orcid' in idutils.detect_identifier_schemes(value):
        cv_pid = "https://orcid.org/"
    elif 'geonames.org' in value:
        cv_pid = "https://www.geonames.org/ontology"
    return cv_pid


def orcid_basic_info(orcid):
    basic_info = None
    orcid = idutils.normalize_orcid(orcid)
    headers = { 'User-Agent'   : 'Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0',
            'Content-Type' : 'application/vdn.orcid+xml',
            'Authorization': 'Bearer a354d82e-37fa-47de-b4a2-740dbe90f355'
    }
    try:
        url = 'https://pub.orcid.org/v3.0/' + orcid
        r = requests.get(url, headers=headers) #GET with headers
        xmlTree = ET.fromstring(r.text)
        item = xmlTree.findall('.//{http://www.orcid.org/ns/common}assertion-origin-name')
    except Exception as e:
        print(e)
        return basic_info
    basic_info = "ORCID Name: %s" % item[0].text
    return basic_info

def loc_basic_info(loc):
    #Returns the first line of json LD
    headers = {'Accept': 'application/json'} #Type of response accpeted
    r = requests.get(loc, headers=headers) #GET with headers
    output = r.json()
    return output[0]

def geonames_basic_info(geonames):
    #Returns the first line of json LD
    geonames = geonames[geonames.index('geonames.org/') + len('geonames.org/'):]
    geonames = geonames[0:geonames.index('/')]
    url = "http://api.geonames.org/get?geonameId=%s&username=frames" % geonames
    headers = {'Accept': 'application/json'} #Type of response accpeted
    r = requests.get(url, headers=headers) #GET with headers
    output = r.json()
    try:
        return output['asciiName']
    except Exception as e:
        return output

def get_rdf_metadata_format(oai_base):
    rdf_schemas = []
    metadata_formats = oai_metadataFormats(oai_base)
    for e in metadata_formats:
        if 'rdf' in e:
            rdf_schemas.append(e)
    return rdf_schemas
