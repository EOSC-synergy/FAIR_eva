import idutils
import json
import pandas as pd
import xml.etree.ElementTree as ET
import re
import requests
import urllib

class RepoTest(object):
    """
    A class used to define FAIR indicators tests

    ...

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

    """

    def __init__(self, oai_base):
        self.oai_base = oai_base

    # TESTS
    #   COAR

    def coar_1_1(self):
        """ COAR 1.1
        The repository supports quality metadata and controlled vocabularies 
        (discipline-based, regional or general metadata schema such as Dublin Core)
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not passed'

        test_passed = False
        acepted_schemas = ['http://datacite.org/schema/kernel-4/',
                           'http://www.openarchives.org/OAI/2.0/oai_dc/']
        avail_schemas = []
        try:
            elem = oai_metadataFormats(self.oai_base)
            for e in elem:
                if elem[e] in acepted_schemas:
                    test_passed = True
                    avail_schemas.append(elem[e])

        except Exception as e:
            print("Exception: %e \n Please, check your OAI-PMH endpoint" % e)
        if test_passed:
            msg = "Test passed: %s | Available schemas: %s" % (test_passed, avail_schemas)
            points = 100
        return (points, msg)

    def coar_1_2(self):
        """ COAR 1.2
        The repository supports harvesting of metadata using OAI-PMH
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not passed'
        test_passed = False
        try:
            elem = oai_identify(self.oai_base)
            for e in elem.findall('{http://www.openarchives.org/OAI/2.0/}Identify'):
                for child in e:
                    if child.tag == '{http://www.openarchives.org/OAI/2.0/}baseURL':
                        if child.text == self.oai_base:
                            test_passed = True
        except Exception as e:
            print("Exception: %e \n Please, check your OAI-PMH endpoint" % e)
        if test_passed:
            msg = "Test passed: %s" % test_passed
            points = 100
        return (points, msg)


    def coar_1_4(self):
        """ COAR 1.4
        The repository assigns a persistent identifier (PID) that points to the landing page 
        of the resource, even in cases where the resource is not available
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_1_6(self):
        """ COAR 1.6
        The repository is included in one or more disciplinary or general registries of resources 
        (e.g. Re3data, OpenDOAR or other national, regional or domain registries) 
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not passed'
        url = 'https://v2.sherpa.ac.uk/cgi/search/repository/advanced?screen=Search&repository_name_merge=ALL'
        headers = {'Accept': 'application/json'} #Type of response accpeted
        r = requests.get(url, headers=headers) #GET with headers

        search = self.oai_base[self.oai_base.find('://') + len('://'):]
        search = search[0:search.find('/')]
        search = search.split('.')
        search = search[0:len(search)-1]

        #R3DATA

        url = 'https://www.re3data.org/api/v1/repositories'
        headers = {'Accept': 'application/json'} #Type of response accpeted
        r = requests.get(url, headers=headers) #GET with headers
        xmlTree = ET.fromstring(r.text)

        test_passed = False
        output_urls = []
        save_id = ''
        list_ids = []
        for elem in xmlTree.findall('repository'):
            for child in elem:
                if child.tag == 'id':
                    save_id = child.text
                if child.tag == 'name':
                    for n in search:
                        if n.lower() in child.text.lower():
                            list_ids.append(save_id)
        for repo in list_ids:
            url = 'https://www.re3data.org/api/v1/repository/%s' % repo
            r = requests.get(url, headers=headers) #GET with headers
            xmlTree2 = ET.fromstring(r.text)
            for elem in xmlTree2.findall(".//{http://www.re3data.org/schema/2-2}api"):
                if self.oai_base[self.oai_base.find('://') + len('://'):].lower() in elem.text.lower():
                    output_urls.append(url)
                    test_passed = True

        if test_passed:
            msg = "Test passed | URL: %s" % output_urls
            points = 100
        return (points, msg)


    def coar_1_8(self):
        """ COAR 1.8
        The repository supports HTTP link headers to provide automated discovery of metadata 
        records and content resources associated with repository items. We recommend Signposting 
        typed links to support this.
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_1_11(self):
        """ COAR 1.11
        The metadata in the repositories are available in human-readable and machine-readable formats
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_2_3(self):
        """ COAR 2.3
        The repository supports access to its documentation and metadata for persons with disabilities
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_2_4(self):
        """ COAR 2.4
        Device neutrality – no specific device needed for users to access the repository
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_3_1(self):
        """ COAR 3.1
        The repository includes licensing information in the metadata record which stipulates reuse conditions
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_3_4(self):
        """ COAR 3.4
        The landing pages include the metadata about the item including information required
        for citation in machine and human readable format        
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_4_4(self):
        """ COAR 4.4
        The repository provides information about the content provider(s) in the metadata including
        the name of the person(s) and/or institution(s) responsible for the resource       
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_9_1(self):
        """ COAR 9.1
        The repository has a contact point or helpdesk to assist depositors and users        
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_9_4(self):
        """ COAR 9.4
        he repository collects and shares usage information using a standard methodology
        (e.g. number of views, downloads)
        
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)


    def coar_9_5(self):
        """ COAR 9.5
        The repository functions on well-supported operating systems and other core infrastructural software
 
        Parameters
        ----------
        oai_base : str
            OAI-PMH endpoint

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = 'Test has not been implemented'
        return (points, msg)

    def get_color(self, points):
        color = "#F4D03F"
        if points < 50:
            color = "#E74C3C"
        elif points > 80:
            color = "#2ECC71"
        return color


    def test_status(self, points):
        test_status = 'fail'
        if points > 50 and points < 75:
            test_status = 'indeterminate'
        if points >= 75:
            test_status = 'pass'
        return test_status

def oai_request(oai_base, action):
    oai = requests.get(oai_base + action) #Peticion al servidor
    xmlTree = ET.fromstring(oai.text)
    return xmlTree


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
        print(metadataPrefix, ':', namespace)
    return metadataFormats
