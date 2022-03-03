from bs4 import BeautifulSoup
import idutils
import logging
import pandas as pd
import xml.etree.ElementTree as ET
import re
import requests
import sys
import urllib

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_doi_str(doi_str):
    doi_to_check = re.findall(r'10[\.-]+.[\d\.-]+/[\w\.-]+[\w\.-]+/[\w\.-]+[\w\.-]', doi_str)
    if len(doi_to_check) == 0:
        doi_to_check = re.findall(r'10[\.-]+.[\d\.-]+/[\w\.-]+[\w\.-]', doi_str)
    if len(doi_to_check) != 0:
        return doi_to_check[0]
    else:
        return ''


def get_handle_str(pid_str):
    handle_to_check = re.findall(r'[\d\.-]+/[\w\.-]+[\w\.-]', pid_str)
    if len(handle_to_check) != 0:
        return handle_to_check[0]
    else:
        return ''


def get_orcid_str(orcid_str):
    orcid_to_check = re.findall(
        r'[\d\.-]+-[\w\.-]+-[\w\.-]+-[\w\.-]', orcid_str)
    if len(orcid_to_check) != 0:
        return orcid_to_check[0]
    else:
        return ''


def check_doi(doi):
    url = "http://dx.doi.org/%s" % str(doi)  # DOI solver URL
    # Type of response accpeted
    headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}
    r = requests.post(url, headers=headers)  # POST with headers
    if r.status_code == 200:
        return True
    else:
        return False


def check_handle(pid):
    handle_base_url = "http://hdl.handle.net/"
    return check_url(handle_base_url + pid)


def check_orcid(orcid):
    orcid_base_url = "https://orcid.org/"
    return check_url(orcid_base_url + orcid)


def check_url(url):
    try:
        resp = False
        r = requests.head(url, verify=False)  # Get URL
        if r.status_code == 200:
            resp = True
        else:
            resp = False
    except Exception as err:
        resp = False
    return resp


def check_oai_pmh_item(base_url, identifier):
    try:
        resp = False
        url = "%s?verb=GetRecord&metadataPrefix=oai_dc&identifier=%s" % (
            base_url, identifier)
        r = requests.get(url, verify=False)  # Get URL
        xmlTree = ET.fromstring(r.text)
        resp = True
    except Exception as err:
        resp = False
        logging.info("Error: %s" % err)
    return resp


def get_color(points):
    color = "#F4D03F"
    if points < 50:
        color = "#E74C3C"
    elif points > 80:
        color = "#2ECC71"
    return color


def test_status(points):
    test_status = 'fail'
    if points > 50 and points < 75:
        test_status = 'indeterminate'
    if points >= 75:
        test_status = 'pass'
    return test_status


def check_handle(pid):
    handle_base_url = "http://hdl.handle.net/"
    return check_url(handle_base_url + pid)


def check_orcid(orcid):
    orcid_base_url = "https://orcid.org/"
    return check_url(orcid_base_url + orcid)


def oai_identify(oai_base):
    action = "?verb=Identify"
    return oai_request(oai_base, action)


def oai_metadataFormats(oai_base):
    action = '?verb=ListMetadataFormats'
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


def get_persistent_id_type(item_id):
    """ get_persistent_id_type
    Returns the list of persistent id potential types
    Parameters
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID ...), or an internal (e.g. an
        identifier from the repo)
    Returns
    -------
    List: PID types
        Like DOI, Handle, etc.
    """
    id_type = idutils.detect_identifier_schemes(item_id)
    if len(id_type) == 0:
        id_type = ['internal']
    return id_type


def pid_to_url(pid, pid_type):
    if pid_type == "internal":
        return pid
    else:
        return idutils.to_url(pid, pid_type)


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
        if row['element'] in elements.term.tolist():
            if 'qualifier' in elements:
                if row['qualifier'] in elements.qualifier[elements[elements['term'] == row['element']].index.values].tolist():
                    if is_persistent_id(row['text_value']):
                        identifiers.append([row['text_value'], idutils.detect_identifier_schemes(row['text_value'])])
                    else:
                        identifiers.append([row['text_value'], None])
            else:
                if is_persistent_id(row['text_value']):
                    identifiers.append([row['text_value'], idutils.detect_identifier_schemes(row['text_value'])])
                else:
                    identifiers.append([row['text_value'], None])
    ids_list = pd.DataFrame(identifiers, columns=['identifier', 'type'])
    return ids_list


def check_uri_in_term(metadata, term, qualifier):
    """ check_uri_in_term
    Returns the list of identifiers found in metadata with a given term and qualifier
    Parameters
    ----------
    metadata: data frame with the following columns: metadata_schema, element, text_value, qualifier
              contains the metadata of the digital object to be analyzed
    term: list of the metadata elements where the identifier can be found
    qualifier: metadata term qualifier
    Returns
    -------
    uris
        List of PIDs found in the metadata term and qualifier
    """
    uris = []
    for (index, row) in metadata.iterrows():
        if row['element'] == term:
            if row['qualifier'] == qualifier:
                potential_id = row['text_value']
                print(potential_id)
                if len(idutils.detect_identifier_schemes(potential_id)):
                    uris.append("| %s.%s = %s | " % (term, qualifier, potential_id))
    return uris


def check_metadata_terms(metadata, terms):
    """ check_metadata_terms
    Checks if the list of expected terms are or not in the metadata
    Parameters
    ----------
    metadata: data frame with the following columns: metadata_schema, element, text_value, qualifier
              contains the metadata of the digital object to be analyzed
    terms: list of the metadata terms expected. DataFrame  where the identifier can be found
        columns: terms, qualifie
    Returns
    -------
    checked_terms
        Data frame with the list of terms found and not found
    """
    found = []
    for e in terms.iterrows():
        found.append(0)
    terms['found'] = found
    for (index, row) in metadata.iterrows():
        if row['element'] in terms.term.tolist():
            if row['qualifier'] == terms.qualifier[terms[terms['term'] == row['element']].index.values[0]]:
                terms.found[terms[terms['term'] == row['element']].index.values[0]] = 1
                if "text_value" in terms:
                    terms.text_value[terms[terms['term'] == row['element']].index.values[0]] = row['text_value']
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
    response = requests.get(url)
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        logging.debug(tags.text)
        error = error + 1
    if error == 0:
        url_final = url

    test_id = "%s:%s" % (pid_type, oai_pid)
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)

    url = oai_base + action + params
    logging.debug("Trying: " + url)
    response = requests.get(url)
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        logging.debug(tags)
        error = error + 1
    if error == 0:
        url_final = url

    test_id = "oai:%s:%s" % (endpoint_root, oai_pid[oai_pid.rfind(".") + 1:len(oai_pid)])
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)

    url = oai_base + action + params
    logging.debug("Trying: " + url)
    response = requests.get(url)
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        logging.debug(tags)
        error = error + 1
    if error == 0:
        url_final = url

    test_id = "oai:%s:b2rec/%s" % (endpoint_root, oai_pid[oai_pid.rfind(".") + 1:len(oai_pid)])
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)

    url = oai_base + action + params
    logging.debug("Trying: " + url)
    response = requests.get(url)
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        logging.debug(tags)
        error = error + 1
    if error == 0:
        url_final = url

    return url_final


def oai_get_metadata(url):
    oai = requests.get(url)
    try:
        xmlTree = ET.fromstring(oai.text)
    except Exception as e:
        logging.error("OAI_RQUEST: %s" % e)
        xmlTree = None
    return xmlTree


def oai_request(oai_base, action):
    oai = requests.get(oai_base + action)  # Peticion al servidor
    try:
        xmlTree = ET.fromstring(oai.text)
    except Exception as e:
        logging.error("OAI_RQUEST: %s" % e)
        xmlTree = ET.fromstring("<OAI-PMH></OAI-PMH>")
    return xmlTree


def find_dataset_file(metadata, url, data_formats):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, features="html.parser")

    msg = 'No dataset files found'
    points = 0

    data_files = []
    for tag in soup.find_all("a"):
        for f in data_formats:
            try:
                if f in tag.get('href') or f in tag.text:
                    data_files.append(tag.get('href'))
            except Exception as e:
                pass

    if len(data_files) > 0:
        points = 100
        msg = "Potential datasets files found: %s" % data_files

    return points, msg, data_files


def metadata_human_accessibility(metadata, url):
    msg = 'Searching metadata terms in %s | \n' % url
    not_found = ''
    points = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers, verify=False)
    found_items = 0
    for index, text in metadata.iterrows():
        if (text['text_value'] is not None and text['text_value'] in response.text) or ("%s.%s" % (text['element'], text['qualifier']) in response.text):
            msg = msg + ("FOUND: %s.%s | \n" % (text['element'], text['qualifier']))
            found_items = found_items + 1
        else:
            not_found = not_found + ("NOT FOUND: %s.%s | \n" % (text['element'], text['qualifier']))

    if len(metadata) > 0:
        msg = msg + not_found + "Found metadata terms (Human accesibility): %i/%i" % (found_items, len(metadata))
        points = (found_items * 100) / len(metadata)
    return points, msg


def check_controlled_vocabulary(value):
    logging.debug("Checking CV: %s" % value)
    cv_msg = None
    cv = None
    if 'id.loc.gov' in value:
        cv_msg = "Library of Congress - Controlled vocabulary. Data: %s" % loc_basic_info(value)
        cv = 'id.loc.gov'
    elif 'orcid' in idutils.detect_identifier_schemes(value):
        cv_msg = "ORCID. Data: %s" % orcid_basic_info(value)
        cv = 'orcid'
    elif 'geonames.org' in value:
        cv_msg = "Geonames - Controlled vocabulary. Data: %s" % geonames_basic_info(value)
        cv = 'geonames.org'
    elif 'vocab.getty.edu' in value:
        getty_check, getty_msg = getty_basic_info(value)
        if getty_check:
            cv_msg = "Getty - Controlled vocabulary. Data: %s" % getty_msg
            cv = 'vocab.getty.edu'
    logging.debug("Message to return: %s" % cv_msg)
    return cv_msg, cv


def controlled_vocabulary_pid(value):
    cv_pid = None
    if 'id.loc.gov' in value:
        cv_pid = "http://www.loc.gov/mads/rdf/v1#"
    elif 'orcid' in idutils.detect_identifier_schemes(value):
        cv_pid = "https://orcid.org/"
    elif 'geonames.org' in value:
        cv_pid = "https://www.geonames.org/ontology"
    elif 'vocab.getty.edu' in value:
        cv_pid = "http://vocab.getty.edu/"
    return cv_pid


def orcid_basic_info(orcid):
    basic_info = None
    orcid = idutils.normalize_orcid(orcid)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0',
               'Content-Type': 'application/vdn.orcid+xml',
               'Authorization': 'Bearer a354d82e-37fa-47de-b4a2-740dbe90f355'}
    try:
        url = 'https://pub.orcid.org/v3.0/' + orcid
        r = requests.get(url, headers=headers)  # GET with headers
        xmlTree = ET.fromstring(r.text)
        item = xmlTree.findall('.//{http://www.orcid.org/ns/common}assertion-origin-name')
    except Exception as e:
        logging.error(e)
        return basic_info
    basic_info = "ORCID Name: %s" % item[0].text
    return basic_info


def loc_basic_info(loc):
    # Returns the first line of json LD
    headers = {'Accept': 'application/json'}  # Type of response accpeted
    r = requests.get(loc, headers=headers)  # GET with headers
    output = r.json()
    return output[0]


def geonames_basic_info(geonames):
    # Returns the first line of json LD
    logging.debug("Checking geonames")
    geonames = geonames[geonames.index('geonames.org/') + len('geonames.org/'):]
    geonames = geonames[0:geonames.index('/')]
    url = "http://api.geonames.org/get?geonameId=%s&username=frames" % geonames
    headers = {'Accept': 'application/json'}  # Type of response accpeted
    r = requests.get(url, headers=headers)  # GET with headers
    logging.debug("Request genoames: %s" % r.text)
    output = ""
    try:
        output = r.json()
        logging.debug("Loaded JSON")
        return output['asciiName']
    except Exception as e:
        return output


def getty_basic_info(loc):
    r = requests.get(loc + ".json")  # GET
    if r.status_code == 200:
        return True, r.json()['results']['bindings'][0]['Subject']['value']
    else:
        return False, ""


def check_standard_project_relation(value):
    if "info:eu-repo/grantAgreement/" in value:
        return True
    else:
        return False


def get_rdf_metadata_format(oai_base):
    rdf_schemas = []
    metadata_formats = oai_metadataFormats(oai_base)
    for e in metadata_formats:
        if 'rdf' in e:
            rdf_schemas.append(e)
    return rdf_schemas


def licenses_list():
    url = 'https://spdx.org/licenses/licenses.json'
    headers = {'Accept': 'application/json'}  # Type of response accpeted
    r = requests.get(url, headers=headers)  # GET with headers
    output = r.json()
    licenses = []
    for e in output['licenses']:
        licenses.append(e['licenseId'])
    return licenses
