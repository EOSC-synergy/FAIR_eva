import idutils
import json
import logging
import requests
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def get_oai_endpoint(base_url):
    """
    Connects with Open Archives URL to search oai-pmh endpoints given a domain name
    :param base_url: domain name to check
    :return: OAI-PMH if found or None if not
    """ 
    logging.debug("Checking OAI-PMH endpoint of |%s|" % base_url)
    url = 'http://www.openarchives.org/pmh/registry/ListFriends'
    headers = {'Accept': 'text/xml'}
    res = requests.get(url, headers=headers)
    tree = ET.fromstring(res.text)
    base_oai = None
    for element in tree.iter():
        for child in element:
            if base_url in child.text:
                base_oai = child.text
    logging.debug("OAI-PMH endpoint found |%s|" % base_oai)
    return base_oai


def get_registry_auth(doi):
    """
    Given a DOI, it returns the Registry Authority which has created de identifier
    :param doi: digital object identifier
    :return: Registry authority
    """ 
    url = "https://doi.org/doiRA/%s" % doi
    res = requests.get(url)
    res_json = res.json()
    return res_json[0]['RA']

def get_datacite_metadata(doi):
    """
    Returns the metadata from DataCite
    :param doi: digital object identifier
    :return: Complete metadata from DataCite
    """
    url = "https://api.datacite.org/dois/%s" % doi
    response = requests.get(url)
    return response.json()

def get_datacite_publisher(metadata):
    """
    Returns the name of the publisher where the Digital Object is hosted and its URL
    :param metadata: complete metadata from DataCite
    :return: name of the publisher where the Digital Object is hosted and its URL
    """
    publisher = metadata['data']['attributes']['publisher']
    url = metadata['data']['attributes']['url']
    return publisher, url

def get_crossref_metadata(doi):
    """
    Returns the metadata from CrossRef
    :param doi: digital object identifier
    :return: Complete metadata from CrossRef
    """
    url = "https://api.crossref.org/works/%s" % doi
    res = requests.get(url)
    return res.json()

def get_crossref_publisher(metadata):
    """
    Returns the name of the publisher where the Digital Object is hosted and its URL
    :param metadata: complete metadata from CrossRef
    :return: name of the publisher where the Digital Object is hosted and its URL
    """
    publisher = metadata['message']['publisher']
    url = metadata['message']['link'][0]['URL']
    return publisher, url
    
def smart_plugin_selection(publisher, url):
    """
    Defines the plugin to select and the url to make thw reqests
    :param metadata: complete metadata from CrossRef
    :return: plugin name and url of the endpoint
    """
    logging.debug("Selecting plugin for publisher: %s at URL: %s" % (publisher, url))
    plugin = None
    oai_base = None
    plugin, oai_base, service_endpoint = get_plugin(urlparse(url).netloc)
    if plugin is None:
        oai_base = get_oai_endpoint(urlparse(url).netloc)
        if oai_base is not None:
            plugin = 'oai-pmh'
    return plugin, oai_base
    
    
def handle_flow(pid):
    url = "http://hdl.handle.net/api/handles/%s" % pid #PID URL with ?noredirect
    headers = {'Content-Type': 'application/json'} #Type of response accpeted
    r = requests.get(url, headers=headers) #POST with headers
    response = r.json()['values']
    for e in response:
        if e['type'] == 'URL':
            url = e['data']['value']
    domain = urlparse(url).netloc
    oai_base = get_oai_endpoint(domain)    
    plugin, url = smart_plugin_selection(domain, domain)
    return plugin, url
    
    
def doi_flow(doi):
    """
    Performs the workflow to identified which plugin need to be called
    :param doi: digital object identifier
    :return: plugin name and url of the endpoint
    """
    logging.debug("Is a doi? - " + str(idutils.is_doi(doi)))
    if (idutils.is_doi(doi)):
        doi = idutils.normalize_doi(doi)
    elif (idutils.is_handle(doi)):
        pid = idutils.normalize_handle(doi)
        return handle_flow(pid)
        
    reg_aut = get_registry_auth(doi)
    metadata = None
    publisher = ''
    domain = None
    url = None
    if reg_aut == 'DataCite':
        metadata = get_datacite_metadata(doi)
        publisher, url = get_datacite_publisher(metadata)
        domain = urlparse(url).netloc
    elif reg_aut == 'Crossref':
        metadata = get_crossref_metadata(doi)
        publisher, url = get_crossref_publisher(metadata)
        domain = urlparse(url).netloc
    elif reg_aut == 'EIDR':
        metadata = None
    elif reg_aut == 'mEDRA':
        metadata = None
    if url == None:
        url = domain
    plugin, url = smart_plugin_selection(publisher, url)
    logging.debug("Selected plugin: %s | URL: %s" % (plugin, url))
    return plugin, url
    

def load_graph():
    """
    Loads the TTL with the graph of the pliugins and FAIR EVA system definition
    :return: Graph with the ttl loaded
    """
    g = Graph()
    g.parse("fair_eva.ttl", format="turtle")
    return g

def get_plugin(netloc):
    """
    Makes a query in the Graph to check if a plugin has been defined for the given DOI
    :param netloc: domain name of the doi landing page
    :return: name of the selected plugin, oai-pmh endpoint and base url
    """
    g = load_graph()
    query_string = """
    prefix aa: <https://w3id.org/fair_eva/>
    SELECT ?plugin ?preservation_policy ?oai_base ?domain
    WHERE {
        ?plug a aa:plugin .
        ?plug rdfs:label ?plugin .
        ?plug aa:connects ?dataService .
        ?dataService aa:preservationPolicy ?preservation_policy .
        ?dataService aa:oai_pmhEndpoint ?oai_base .
        ?dataService aa:serviceEndpoint ?domain
    }
    """
    query = prepareQuery(query_string, initNs={"aa": "<https://w3id.org/fair_eva/>"})

    results = g.query(query)
    plugin = None
    oai_base = None
    service_endpoint = None
    for row in results:
        if netloc in str(row["domain"]):
            plugin = str(row["plugin"])
            oai_base = str(row["oai_base"])
            service_endpoint = str(row["domain"])
    return plugin, oai_base, service_endpoint

