#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import idutils
import logging
import os
import urllib
from api.evaluator import Evaluator
import pandas as pd
import requests
import sys
import xml.etree.ElementTree as ET
import json
import api.utils as ut
from dicttoxml import dicttoxml #Add to requirements
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)



class EPOS(Evaluator):
    """A class used to define FAIR indicators tests. It is tailored towards the EPOS repository

    ...

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

    oai_base : str
        Open Archives Initiative , This is the place in which the API will ask for the metadata. If you are working with  EPOS https://www.ics-c.epos-eu.org/api/v1/resources

    lang : Language

    """

    def __init__(self, item_id, oai_base=None, lang='en'):
        logging.debug("Creating epos")
        super().__init__(item_id, oai_base, lang)
        # TO REDEFINE - WHICH IS YOUR PID TYPE?
        self.id_type ="uuid" #idutils.detect_identifier_schemes(item_id)[0]
        global _
        _ = super().translation()

        config = configparser.ConfigParser()
        
        config_file = 'config.ini'
        if "CONFIG_FILE" in os.environ:
            config_file = os.getenv("CONFIG_FILE")
        config.read(config_file)
        logging.debug("CONFIG LOADED")
        #configuration
        # You need a way to get your metadata in a similar format

        metadata_sample = self.get_metadata()
        self.metadata = pd.DataFrame(metadata_sample,
                                     columns=['metadata_schema',
                                              'element', 'text_value',
                                              'qualifier'])
        logging.debug('METADATA: %s' % (self.metadata))
        # Protocol for (meta)data accessing
        if len(self.metadata) > 0:
            self.access_protocols = ['http']
        # Config attributes
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        if "CONFIG_FILE" in os.environ:
            config_file = os.getenv("CONFIG_FILE")
        config.read(config_file)
        plugin = 'epos'
        self.identifier_term = ast.literal_eval(config[plugin]['identifier_term'])
        self.terms_quali_generic = ast.literal_eval(config[plugin]['terms_quali_generic'])
        self.terms_quali_disciplinar = ast.literal_eval(config[plugin]['terms_quali_disciplinar'])
        self.terms_access = ast.literal_eval(config[plugin]['terms_access'])
        self.terms_cv = ast.literal_eval(config[plugin]['terms_cv'])
        self.supported_data_formats = ast.literal_eval(config[plugin]['supported_data_formats'])
        self.terms_qualified_references = ast.literal_eval(config[plugin]['terms_qualified_references'])
        self.terms_relations = ast.literal_eval(config[plugin]['terms_relations'])
        self.terms_license = ast.literal_eval(config[plugin]['terms_license'])
    # TO REDEFINE - HOW YOU ACCESS METADATA?

    def get_metadata(self):
    
        #leave this here for a while until we make sure everthing works
        metadata_sample=[]
        eml_schema="epos"
        final_url="https://www.ics-c.epos-eu.org/api/v1/resources/details?id="+self.item_id
        response = requests.get(final_url, verify=False)
        dicion=(response.json())
        for i in dicion.keys():
             if str(type(dicion[i])) == "<class 'dict'>":
                  q=dicion[i]
                  for j in q.keys():
                       metadata_sample.append([eml_schema,j,q[j],None])
                       
             else:
                 metadata_sample.append([eml_schema,i,dicion[i],None])
        
        return(metadata_sample)
        sys.exit()
        xmlresponse=dicttoxml(response.json())

        tree = ET.fromstring(xmlresponse)
        
      
        eml_schema ={"epos"} #"{eml://ecoinformatics.org/eml-2.1.1}"
        metadata_sample = []
        elementos = tree.find('.//')
 
        

        for i in tree.iter():
                metadata_sample.append([eml_schema, i.tag, i.text, None])
              
        return metadata_sample
   
    def rda_f1_01m(self):
        """ Indicator RDA-F1-01M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the metadata is identified by a persistent identifier.
        A persistent identifier ensures that the metadata will remain findable over time, and reduces
        the risk of broken links.

        Technical proposal:Depending on the type od item_id, defined, it should check if it is any of
        the allowed Persistent Identifiers (DOI, PID) to identify digital objects.

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = ''
        logging.debug("ID ChECKING: %s" % self.identifier_term)

        try:
            if len(self.identifier_term) > 1:
                id_term_list = pd.DataFrame(self.identifier_term, columns=['term', 'qualifier'])
                

            else:
                id_term_list = pd.DataFrame(self.identifier_term, columns=['term'])
                

            
            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
            points, msg = ut.is_uuid(id_list.iloc[0,0])
            if points == 0 and msg == '':
                 points, msg = self.identifiers_types_in_metadata(id_list)    
        except Exception as e:
            logging.error(e)
            
        return (points, msg)
   
    def rda_f3_01m(self):
       
            
        id_term_list = pd.DataFrame(self.identifier_term, columns=['term'])
        id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
        points, msg = ut.is_uuid(id_list.iloc[0,0])
        return (points, msg)

    def rda_f4_01m(self):
        #There is a need to check this clearly
        points = 0
        msg = 'Data is not accessible'
        return (points, msg)
        
    """def rda_a1_01m(self):
        # IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = 'Data is not accessible'
        return (points, msg)
    """
    def rda_a1_02m(self):
        """ Indicator RDA-A1-02M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.
        The indicator refers to any human interactions that are needed if the requester wants to
        access metadata. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        # 2 - Look for the metadata terms in HTML in order to know if they can be accessed manually
        
        return(0,"")
        try:

            item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')

        except Exception as e:
            logging.error(e)
            item_id_http = self.oai_base
        points, msg = ut.metadata_human_accessibility(self.metadata, item_id_http)
        return (points, msg)
    
    def rda_a1_03m(self):
        """ Indicator RDA-A1-03M Metadata identifier resolves to a metadata record
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.
        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        
        points = 0
        msg = "Metadata can not be found"
        try:
            
            
            item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
            points, msg = ut.metadata_human_accessibility(self.metadata, item_id_http)
            msg = _("%s \nMetadata found via Identifier" % msg)
        except Exception as e:
            logging.error(e)
        return (points, msg)
        
    def rda_a1_03d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        This indicator is about the resolution of the identifier that identifies the digital object. The
        identifier assigned to the data should be associated with a formally defined
        retrieval/resolution mechanism that enables access to the digital object, or provides access
        instructions for access in the case of human-mediated access. The FAIR principle and this
        indicator do not say anything about the mutability or immutability of the digital object that
        is identified by the data identifier -- this is an aspect that should be governed by a
        persistence policy of the data provider
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        msg = "Data can not be accessed"
        points = 0

        try:
            
            landing_url = urllib.parse.urlparse(self.oai_base).netloc
            item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
            points, msg, data_files = ut.find_dataset_file(self.metadata, item_id_http, self.supported_data_formats)
            

            headers = []
            for f in data_files:
                try:
                    url = landing_url + f
                    if 'http' not in url and 'http:' in self.oai_base:
                        url = "http://" + url
                    elif 'https:' not in url and 'https:' in self.oai_base:
                        url = "https://" + url
                    res = requests.head(url, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                except Exception as e:
                    logging.error(e)
                try:
                    res = requests.head(f, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                except Exception as e:
                    logging.error(e)
            if len(headers) > 0:
                msg = msg + _("\n Files can be downloaded: %s" % headers)
                points = 100
            else:
                msg = msg + _("\n Files can not be downloaded")
                points = 0
        except Exception as e:
            logging.error(e)
        return points, msg

    """
    def rda_i1_02m(self):
        """""" Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the metadata. This means
        that metadata should be readable and thus interoperable for machines without any
        requirements such as specific translators or mappings.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """"""
        
        # TO REDEFINE
        points = 0
        msg = 'No machine-actionable metadata format found. OAI-PMH endpoint may help'
        return (points, msg)
    """
    def rda_i1_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_i1_02m()
   
    def rda_i3_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        This indicator is about the way metadata is connected to other data, for example linking to
        previous or related research data that provides additional context to the data. Please note
        that this is not about the link from the metadata to the data it describes; that link is
        considered in principle F3 and in indicator RDA-F3-01M.
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
    """
        points = 0
        msg = _('No references found. Suggested terms to add: %s' % self.terms_relations)
        try:

            if len([self.terms_relations[0]]) > 1:
                id_term_list = pd.DataFrame(self.terms_relations, columns=['term', 'qualifier'])
            else:
                id_term_list = pd.DataFrame(self.terms_relations, columns=['term'])
            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
            if len(id_list) > 0:
                if len(id_list[id_list.type.notnull()]) > 0:
                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        if 'url' in e.type:
                            e.type.remove('url')
                        if len(e.type) > 0:
                            msg = _('Your (meta)data reference this digital object: ')
                            points = 100
                            msg = msg + "| %s: %s | " % (e.identifier, e.type)
        except Exception as e:
            logging.error(e)
        return (points, msg)
    def rda_i3_03m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        This indicator is about the way metadata is connected to other metadata, for example to
        descriptions of related resources that provide additional context to the data. The references
        need to be qualified which means that the relation
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = _('No references found. Suggested terms to add: %s' % self.terms_relations)
        try:

            if len(self.terms_relations) > 1:
                id_term_list = pd.DataFrame(self.terms_relations, columns=['term', 'qualifier'])
            else:
                id_term_list = pd.DataFrame(self.terms_relations, columns=['term'])
            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
            if len(id_list) > 0:
                if lenr1(id_list[id_list.type.notnull()]) > 0:
                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        if 'url' in e.type:
                            e.type.remove('url')
                        if len(e.type) > 0:
                            msg = _('Your (meta)data reference this digital object: ')
                            points = 100
                            msg = msg + "| %s: %s | " % (e.identifier, e.type)
        except Exception as e:
            logging.error(e)
        return (points, msg)
    def rda_r1_3_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.
        This indicator requires that the metadata follows a community standard that has a machineunderstandable expression.
        Technical proposal:
        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        # Check metadata XML or RDF schema
        points = 0
        msg = \
            _('Currently, this tool does not include community-based schemas. If you need to include yours, please contact.')
        
        return (points, msg)
    def rda_r1_3_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that metadata complies with community standards.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        # TO REDEFINE
        points = 0
        msg = \
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')
        return (points, msg)

    def rda_r1_3_01d(self):
        """ Indicator RDA_R1.3_01D

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        # TO REDEFINE
        points = 0
        msg = \
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')
        return (points, msg)
