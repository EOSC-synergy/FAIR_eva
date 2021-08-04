#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser
import idutils
import psycopg2
import xml.etree.ElementTree as ET
import re
import requests
from api.evaluator import Evaluator
import pandas as pd
import api.utils as ut
import urllib

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

    def __init__(self, item_id, oai_base=None):
        if ut.get_doi_str(item_id) != '':
            self.item_id = ut.get_doi_str(item_id)
            self.id_type = 'doi'
        elif ut.get_handle_str(item_id) != '':
            self.item_id = ut.get_handle_str(item_id)
            self.id_type = 'handle'
        else:
            self.item_id = item_id
            self.id_type = 'internal'
        self.access_protocols = []
        self.cvs = []
        self.metadata = None
        self.connection = None
        self.oai_base = oai_base
        config = configparser.ConfigParser()
        config.read('config.ini')
        print("CONFIG LOADED")
        try:
            self.connection = psycopg2.connect(
                user=config['digital_csic']['db_user'],
                password=config['digital_csic']['db_pass'],
                host=config['digital_csic']['db_host'],
                port=config['digital_csic']['db_port'],
                database=config['digital_csic']['db_db'])
            print("DB configured")
        except Exception as error:
            print('Error while fetching data from PostgreSQL ')
            print(error)
        
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

            print('INTERNAL ID: %i ITEM ID: %s' % (self.internal_id,
                                                   self.item_id))

            query = \
                'SELECT metadatavalue.text_value, metadatafieldregistry.metadata_schema_id, metadatafieldregistry.element,\
                metadatafieldregistry.qualifier FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s and \
    item.item_id = metadatavalue.item_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id' \
                % self.internal_id
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.metadata = pd.DataFrame(cursor.fetchall(),
                                         columns=['text_value',
                                                  'metadata_schema', 'element',
                                                  'qualifier'])
        except Exception as e:
            print('Error connecting DB')
            print(e)
        if self.metadata is None and self.oai_base is not None and self.oai_base != '':
            print("Trying OAI-PMH")
            metadataFormats = ut.oai_metadataFormats(oai_base)
            dc_prefix = ''
            for e in metadataFormats:
                if metadataFormats[e] == 'http://www.openarchives.org/OAI/2.0/oai_dc/':
                    dc_prefix = e
            print(dc_prefix)

            id_type = idutils.detect_identifier_schemes(self.item_id)[0]

            item_metadata = ut.oai_get_metadata(ut.oai_check_record_url(oai_base, dc_prefix, self.item_id)).find('.//{http://www.openarchives.org/OAI/2.0/}metadata')
            data = []
            for tags in item_metadata.findall('.//'):
                metadata_schema = tags.tag[0:tags.tag.rfind("}")+1]
                element = tags.tag[tags.tag.rfind("}")+1:len(tags.tag)]
                text_value = tags.text
                qualifier = None
                data.append([metadata_schema, element, text_value, qualifier])
            self.metadata = pd.DataFrame(data, columns=['metadata_schema', 'element', 'text_value', 'qualifier'])

            if len(self.metadata) > 0:
                self.access_protocols = ['http', 'oai-pmh']

        # SELECT bitstream.name FROM item2bundle, bundle2bitstream, bitstream WHERE item2bundle.item_id = 319688 AND item2bundle.bundle_id = bundle2bitstream.bundle_id AND bundle2bitstream.bitstream_id = bitstream.bitstream_id;
        # SELECT DISTINCT metadataschemaregistry.namespace,
        # metadataschemaregistry.short_id FROM metadatavalue,
        # metadatafieldregistry, metadataschemaregistry WHERE
        # metadatavalue.item_id = 319688 AND metadatavalue.metadata_field_id =
        # metadatafieldregistry.metadata_field_id AND
        # metadatafieldregistry.metadata_schema_id =
        # metadataschemaregistry.metadata_schema_id;
        print(self.metadata)
        return None

    # TESTS
    #    FINDABLE

    def rda_f2_01m_generic(self):
        """ Indicator RDA-F2-01M_GENERIC
        This indicator is linked to the following principle: F2: Data are described with rich metadata.

        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.

        Technical proposal: Check if all the dublin core terms are OK

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
        # TODO different generic metadata standards?
        # Checkin Dublin Core

        msg = 'Checking Dublin Core'

        terms_quali = [
            ['contributor','author'],
            ['date', 'issued'],
            ['title', None],
            ['identifier', 'citation'],
            ['publisher', None],
            ['identifier', None],
            ['type', None],
            ['language', 'iso'],
            ['relation', 'csic'],
            ['rights', None]
        ]

        md_term_list = pd.DataFrame(terms_quali, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        points = (100 * (len(md_term_list) - (len(md_term_list) - sum(md_term_list['found']))) \
                    / len(md_term_list))
        if points == 100:
            msg = msg + '... All mandatory terms included'
        else:
            msg = msg + '... Missing terms: \n'
            for i, e in md_term_list.iterrows():
                if e['found'] == 0:
                    msg = msg + ' | Term: %s, Qualifier: %s \n' % (e['term'], e['qualifier'])

        return (points, msg)

    # ACCESSIBLE
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
        landing_url = urllib.parse.urlparse(self.oai_base).netloc
        data_formats = [".tif", ".aig", ".asc", ".agr", ".grd", ".nc", ".hdf", ".hdf5",
                        ".pdf", ".odf", ".doc", ".docx", ".csv", ".jpg", ".png", ".gif",
                        ".mp4", ".xml", ".rdf", ".txt", ".mp3", ".wav", ".zip", ".rar", 
                        ".tar", ".tar.gz", ".jpeg", ".xls", ".xlsx"]
        item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
        points, msg, data_files = ut.find_dataset_file(self.metadata, item_id_http, data_formats)

        headers = []
        for f in data_files:
            try:
                url = landing_url + f
                if 'http' not in url:
                    url = "http://" + url
                res = requests.head(url, verify=False, allow_redirects=True)
                if res.status_code == 200:
                    headers.append(res.headers)
            except Exception as e:
                print(e)
            try:
                res = requests.head(f, verify=False, allow_redirects=True)
                if res.status_code == 200:
                    headers.append(res.headers)
            except Exception as e:
                print(e)
        if len(headers) > 0:
            msg = msg + "\n Files can be downloaded: %s" % headers
            points = 100
        else:
            msg = msg + "\n Files can not be downloaded"
            points = 0
        return points, msg

# INTEROPERABLE
    def rda_i1_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, in particular the data model and format.

        Technical proposal: Data format is within a list of accepted standards.

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

        data_formats = [".tif", ".aig", ".asc", ".agr", ".grd", ".nc", ".hdf", ".hdf5",
                        ".pdf", ".odf", ".doc", ".docx", ".csv", ".jpg", ".png", ".gif",
                        ".mp4", ".xml", ".rdf", ".txt", ".mp3", ".wav", ".zip", ".rar",
                        ".tar", ".tar.gz", ".jpeg", ".xls", ".xlsx"]

        item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
        points, msg, data_files = ut.find_dataset_file(self.item_id, item_id_http, data_formats)
        return (points, msg)


    # REUSABLE

    def rda_r1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1: (Meta)data are richly described with a
        plurality of accurate and relevant attributes. More information about that principle can be
        found here.

        The indicator concerns the quantity but also the quality of metadata provided in order to
        enhance data reusability.

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
        #Depending on the metadata schema used, checks that at least the mandatory terms are filled (75%)
        # and the number of terms are high (25%)
        msg = 'Checking Dublin Core as multidisciplinar schema'

        terms_quali = [
            ['contributor','author'],
            ['date', 'issued'],
            ['title', None],
            ['identifier', 'citation'],
            ['publisher', None],
            ['identifier', None],
            ['type', None],
            ['language', 'iso'],
            ['relation', 'csic'],
            ['rights', None]
        ]

        md_term_list = pd.DataFrame(terms_quali, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        points = (100 * (len(md_term_list) - (len(md_term_list) - sum(md_term_list['found']))) \
                    / len(md_term_list))
        if points == 100:
            msg = msg + '... All mandatory terms included'
        else:
            msg = msg + '... Missing terms:'
            for i, e in md_term_list.iterrows():
                if e['found'] == 0:
                    msg = msg + '| term: %s, qualifier: %s' % (e['term'], e['qualifier'])

        return (points, msg)

# DIGITAL_CSIC UTILS

    def get_internal_id(self, item_id, connection):
        internal_id = item_id
        id_to_check = ut.get_doi_str(item_id)
        print('DOI is %s' % id_to_check)
        temp_str = '%' + item_id + '%'
        if len(id_to_check) != 0:
            if ut.check_doi(id_to_check):
                query = \
                    "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.item_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                    % temp_str
                print(query)
                cursor = connection.cursor()
                cursor.execute(query)
                list_id = cursor.fetchall()
                if len(list_id) > 0:
                    for row in list_id:
                        internal_id = row[0]

        if internal_id == item_id:
            id_to_check = ut.get_handle_str(item_id)
            print('PID is %s' % id_to_check)
            temp_str = '%' + item_id + '%'
            query = \
                "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.item_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                % temp_str
            print(query)
            cursor = connection.cursor()
            cursor.execute(query)
            list_id = cursor.fetchall()
            if len(list_id) > 0:
                for row in list_id:
                    internal_id = row[0]

        return internal_id

    def get_handle_id(self, internal_id, connection):
        query = \
            "SELECT metadatavalue.text_value FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s AND item.item_id = metadatavalue.item_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatafieldregistry.qualifier = 'uri'" \
            % internal_id
        cursor = connection.cursor()
        cursor.execute(query)
        list_id = cursor.fetchall()
        handle_id = ''
        if len(list_id) > 0:
            for row in list_id:
                handle_id = row[0]

        return ut.get_handle_str(handle_id)
