#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import idutils
import logging
import psycopg2
import requests
from api.evaluator import Evaluator
import pandas as pd
import api.utils as ut
import sys
import urllib

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Digital_CSIC(Evaluator):

    """
    A class used to represent an Animal

    ...

    Attributes
    ----------
    says_str : str
        a formatted string to print out what the animal says
    name : str
        the name of the animal
    sound : str
        the sound that the animal makes
    num_legs : int
        the number of legs the animal has (default 4)

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """

    def __init__(self, item_id, oai_base=None, lang='en'):
        if oai_base == "":
            oai_base = None
        logging.debug("Call parent")
        super().__init__(item_id, oai_base, lang)
        logging.debug("Parent called")
        if ut.get_doi_str(item_id) != '':
            self.item_id = ut.get_doi_str(item_id)
            self.id_type = 'doi'
        elif ut.get_handle_str(item_id) != '':
            self.item_id = ut.get_handle_str(item_id)
            self.id_type = 'handle'
        else:
            self.item_id = item_id
            self.id_type = 'internal'

        config = configparser.ConfigParser()
        config.read('config.ini')
        logging.debug("CONFIG LOADED")
        try:
            self.connection = psycopg2.connect(
                user=config['digital_csic']['db_user'],
                password=config['digital_csic']['db_pass'],
                host=config['digital_csic']['db_host'],
                port=config['digital_csic']['db_port'],
                database=config['digital_csic']['db_db'])
            logging.debug("DB configured")
        except Exception as error:
            logging.error('Error while fetching data from PostgreSQL ')
            logging.error(error)

        try:
            self.internal_id = self.get_internal_id(self.item_id,
                                                    self.connection)
            if self.id_type == 'doi':
                self.handle_id = self.get_handle_id(self.internal_id,
                                                    self.connection)
            elif self.id_type == 'internal':
                self.handle_id = self.get_handle_id(self.internal_id,
                                                    self.connection)
                self.item_id = self.handle_id

            logging.debug('INTERNAL ID: %i ITEM ID: %s' % (self.internal_id,
                          self.item_id))

            query = \
                'SELECT metadatavalue.text_value, metadatafieldregistry.metadata_schema_id, metadatafieldregistry.element,\
                metadatafieldregistry.qualifier FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s and \
    item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id' \
                % self.internal_id
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.metadata = pd.DataFrame(cursor.fetchall(),
                                         columns=['text_value',
                                                  'metadata_schema', 'element',
                                                  'qualifier'])
            logging.debug('METADATA: %s' % (self.metadata.to_string()))
        except Exception as e:
            logging.error('Error connecting DB')
            logging.error(e)
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        plugin = 'digital_csic'
        try:
            self.identifier_term = ast.literal_eval(config[plugin]['identifier_term'])
            self.terms_quali_generic = ast.literal_eval(config[plugin]['terms_quali_generic'])
            self.terms_quali_disciplinar = ast.literal_eval(config[plugin]['terms_quali_disciplinar'])
            self.terms_access = ast.literal_eval(config[plugin]['terms_access'])
            self.terms_cv = ast.literal_eval(config[plugin]['terms_cv'])
            self.supported_data_formats = ast.literal_eval(config[plugin]['supported_data_formats'])
            self.terms_qualified_references = ast.literal_eval(config[plugin]['terms_qualified_references'])
            self.terms_relations = ast.literal_eval(config[plugin]['terms_relations'])
            self.terms_license = ast.literal_eval(config[plugin]['terms_license'])
        except Exception as e:
            logging.error("Problem loading plugin config: %s" % e)

        global _
        _ = super().translation()

    # TESTS
    #ACCESS
    def rda_a1_2_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.2: The protocol allows for an
        authentication and authorisation where necessary. More information about that principle
        can be found here.
        The indicator requires the way that access to the digital object can be authenticated and
        authorised and that data accessibility is specifically described and adequately documented.
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
        points = 100
        msg = _("DIGITAL.CSIC allow access management and authentication and authorisation from CSIC CAS")
        return points, msg

    def rda_a2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A2: Metadata should be accessible even
        when the data is no longer available. More information about that principle can be found
        here.
        The indicator intends to verify that information about a digital object is still available after
        the object has been deleted or otherwise has been lost. If possible, the metadata that
        remains available should also indicate why the object is no longer available.
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
        points = 100
        msg = _("DIGITAL.CSIC preservation policy is available at: https://digital.csic.es/dc/politicas/#politica8")
        return points, msg


    def rda_r1_2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.2: (Meta)data are associated with
        detailed provenance. More information about that principle can be found here.
        This indicator requires the metadata to include information about the provenance of the
        data, i.e. information about the origin, history or workflow that generated the data, in a
        way that is compliant with the standards that are used in the community in which the data
        is produced.
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
        # TODO: check provenance in digital CSIC - Dublin Core??
        prov_terms = [['description', 'provenance'],['date','created'], ['description','abstract']]
        msg = _('Provenance information can not be found. Please, include the info in this term: %s' % prov_terms)
        points = 0

        md_term_list = pd.DataFrame(prov_terms, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list['found']) > 0:
            for index, elem in md_term_list.iterrows():
                if elem['found'] == 1:
                    logging.debug(elem)
                    msg = msg + _("| Provenance info found: %s.%s " % (elem['term'], elem['qualifier']))
                    points = 100
        return (points, msg)

# DIGITAL_CSIC UTILS

    def get_internal_id(self, item_id, connection):
        internal_id = item_id
        id_to_check = ut.get_doi_str(item_id)
        logging.debug('DOI is %s' % id_to_check)
        temp_str = '%' + item_id + '%'
        if len(id_to_check) != 0:
            if ut.check_doi(id_to_check):
                query = \
                    "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                    % temp_str
                logging.debug(query)
                cursor = connection.cursor()
                cursor.execute(query)
                list_id = cursor.fetchall()
                if len(list_id) > 0:
                    for row in list_id:
                        internal_id = row[0]

        if internal_id == item_id:
            id_to_check = ut.get_handle_str(item_id)
            logging.debug('PID is %s' % id_to_check)
            temp_str = '%' + item_id + '%'
            query = \
                "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                % temp_str
            logging.debug(query)
            cursor = connection.cursor()
            cursor.execute(query)
            list_id = cursor.fetchall()
            if len(list_id) > 0:
                for row in list_id:
                    internal_id = row[0]

        return internal_id

    def get_handle_id(self, internal_id, connection):
        query = \
            "SELECT metadatavalue.text_value FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s AND item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatafieldregistry.qualifier = 'uri'" \
            % internal_id
        cursor = connection.cursor()
        cursor.execute(query)
        list_id = cursor.fetchall()
        handle_id = ''
        if len(list_id) > 0:
            for row in list_id:
                handle_id = row[0]

        return ut.get_handle_str(handle_id)
