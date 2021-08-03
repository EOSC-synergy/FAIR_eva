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
        self.access_protocol = []
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
        if self.metadata is None and self.oai_base is not None:
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

    def rda_f1_01m(self):
        msg = ''
        points = 0
        elements = ['identifier'] #Configurable
        id_list = ut.find_ids_in_metadata(self.metadata, elements)
        if len(id_list) > 0:
            if len(id_list[id_list.type.notnull()]) > 0:
                msg = 'Your (meta)data is identified with this identifier(s) and type(s): '
                points = 100
                for i, e in id_list[id_list.type.notnull()].iterrows():
                    msg = msg + "| %s: %s | " % (e.identifier, e.type)
            else:
                msg = 'Your (meta)data is identified by non-persistent identifiers: '
                for i, e in id_list:
                    msg = msg + "| %s: %s | " % (e.identifier, e.type)
        else:
            msg = 'Your (meta)data is not identified by persistent identifiers:'


        return (points, msg)

    def rda_f1_01d(self):
        (points, msg) = self.rda_f1_01m()
        return (points, msg)

    def rda_f2_01m(self):
        (points_g, msg_g) = self.rda_f2_01m_generic()
        (points_d, msg_d) = self.rda_f2_01m_disciplinar()
        return ((points_g + points_d) / 2, msg_g + ' | ' + msg_d)

    def rda_f4_01m(self):

        # TODO Any other way?

        msg = ''
        base_url = 'http://digital.csic.es/dspace-oai/request'
        oai_id = 'oai:digital.csic.es:%s' % self.item_id
        if ut.check_oai_pmh_item(base_url, oai_id):
            points = 100
            msg = \
                'Your digital object is available via OAI-PMH harvesting protocol'
            self.access_protocol = ['http', 'oai-pmh']
        else:
            points = 0
            msg = \
                'Your digital object is not available via OAI-PMH. Please, contact to DIGITAL.CSIC admins'

        return (points, msg)

    # ACCESSIBLE

    def rda_a1_01m(self):
        # 1 - Check metadata record for access info
        msg = 'Checking Dublin Core'
        points = 0
        terms_quali = [['access', ''], ['rights', '']]

        md_term_list = pd.DataFrame(terms_quali, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list['found']) > 0:
            for index, elem in md_term_list.iterrows():
                if elem['found'] == 1:
                    msg = msg + "| Metadata: %s.%s: ... %s" % (elem['term'], elem['qualifier'], self.metadata.loc[self.metadata['element'] == elem['term']].loc[self.metadata['qualifier'] == elem['qualifier']])
                    points = 100
        # 2 - Parse HTML in order to find the data file
        data_formats = [".txt", ".pdf", ".csv", ".nc", ".doc", ".xls", ".zip", ".rar", ".tar", ".png", ".jpg"]
        msg_2, points_2, data_files = ut.find_dataset_file(self.metadata, self.item_id, data_formats)
        if points_2 == 100 and points == 100:
            msg = "%s \n Data can be accessed manually | %s" % (msg, msg_2)
        elif points_2 == 0 and points == 100:
            msg = "%s \n Data can not be accessed manually | %s" % (msg, msg_2)
        elif points_2 == 100 and points == 0:
            msg = "%s \n Data can be accessed manually | %s" % (msg, msg_2)
            points = 100
        elif points_2 == 0 and points == 0:
            msg = msg + "No access information can be found in metadata"
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
        landing_url = urllib.parse.urlparse(self.oai_base).netloc
        data_formats = [".txt", ".pdf", ".csv", ".nc", ".doc", ".xls", ".zip", ".rar", ".tar", ".png", ".jpg"]
        points, msg, data_files = ut.find_dataset_file(self.metadata, self.item_id, data_formats)

        headers = []
        for f in data_files:
            try:
                url = landing_url + f
                if 'http' not in url:
                    url = "http://" + url
                res = requests.head(url, verify=False)
                if res.status_code == 200:
                    headers.append(res.headers)
            except Exception as e:
                print(e)
            try:
                res = requests.head(f, verify=False)
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


    def rda_a1_05d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to automated interactions between machines to access digital objects.
        The way machines interact and grant access to the digital object will be evaluated by the
        indicator.

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
        msg = \
            'DIGITAL.CSIC does not currently provides an automatic protocol to retrieve the digital object'
        return (points, msg)


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
        msg = \
            'DIGITAL.CSIC allows restricted access to digital object using institutional AAI'
        return (points, msg)

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

        # TODO Check this

        points = 100
        msg = \
            'DIGITAL.CSIC preserves the metadata even if the digital object is deleted'
        return (points, msg)

    # INTEROPERABLE

    def rda_i1_01m(self):

        # TODO Check

        points = 0
        url = \
            'http://digital.csic.es/dspace-oai/request?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:digital.csic.es:10261/%s' \
            % self.internal_id
        oai = requests.get(url)
        msg = ''
        try:
            xmlTree = ET.fromstring(oai.text)
            msg = 'Metadata using interoperable representation (XML)'
            points = 100
        except ET.ParseError as err:
            msg = \
                'Metadata IS NOT using interoperable representation (XML)'
        except Exception as err:
            msg = 'Internal problem executing the test: %s' % err

        return (points, msg)

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
        msg = 'Test not implemented'

        standard_list = [
            'pdf',
            'csv',
            'jpg',
            'jpeg',
            'nc',
            'hdf',
            'mp4',
            'mp3',
            'wav',
            'doc',
            'txt',
            'xls',
            'xlsx',
            'sgy',
            'zip',
        ]

        query = \
            "SELECT bitstream.name FROM item2bundle, bundle2bitstream, bitstream WHERE item2bundle.item_id = '%s' AND item2bundle.bundle_id = bundle2bitstream.bundle_id AND bundle2bitstream.bitstream_id = bitstream.bitstream_id" \
            % self.internal_id
        print('Format: %s' % query)
        cursor = self.connection.cursor()
        cursor.execute(query)
        filename_list = cursor.fetchall()

        for row in filename_list:
            print('File format: %s' % row[0])
            if row[0].split('.')[-1] in standard_list:
                points = points + 100 / len(filename_list)
                msg = 'The digital object is in an standard format'

        if points == 0:
            msg = \
                'The digital object is not in an accepted standard format. If you think the format should be accepted, please contact DIGITAL.CSIC'
        elif points < 100:
            msg = 'Some of the files are in an standard format'

        return (points, msg)

    def rda_i1_02m(self):
        points = 0
        url = \
            'http://digital.csic.es/dspace-oai/request?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:digital.csic.es:10261/%s' \
            % self.internal_id
        oai = requests.get(url)
        msg = ''
        try:
            xmlTree = ET.fromstring(oai.text)
            msg = \
                'Metadata can be extracted using machine-actionable features (XML Metadata)'
            points = 100
        except Exception as err:
            msg = \
                'Metadata CAN NOT be extracted using machine-actionable features'
        except Exception as err:
            msg = 'Internal problem executing the test: %s' % err

        return (points, msg)

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

        points = 0
        msg = \
            'DIGITAL.CSIC does not currently provides an automatic protocol to retrieve the digital object'
        return (points, msg)

    def rda_i2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the vocabulary used for the metadata to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique and persistent
        identifiers. The documentation needs to be easily findable and accessible.

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
        msg = ''

        query = \
            'SELECT DISTINCT metadataschemaregistry.namespace, metadataschemaregistry.short_id FROM metadatavalue, metadatafieldregistry, metadataschemaregistry WHERE metadatavalue.item_id = %s AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.metadata_schema_id = metadataschemaregistry.metadata_schema_id' \
            % self.internal_id
        cursor = self.connection.cursor()
        cursor.execute(query)
        namespace_list = cursor.fetchall()
        schemas = ''
        for row in namespace_list:
            schemas = schemas + ' ' + row[1]
            if ut.check_url(row[0]):
                points = points + 100 / len(namespace_list)
                msg = \
                    'The metadata standard is well-document within a persistent identifier'

        if points == 0:
            msg = \
                'The metadata standard documentation can not be retrieved. Schema(s): %s' \
                % schemas
        elif points < 100:
            msg = \
                'Some of the metadata schemas used are not accessible via persistent identifier. Schema(s): %s' \
                % schemas

        return (points, msg)

    def rda_i2_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique
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

        (points, msg) = self.rda_i2_01m()
        return (points, msg)

    def rda_i3_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

        Technical proposal: Checks if includes some metadata term to refer any other digital object or contributor people

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

        orcids = 0
        pids = 0
        for (index, row) in self.metadata.iterrows():
            if row['element'] == 'contributor':
                orcids = orcids + 1
            if row['element'] == 'relation':
                pids = pids + 1

        if orcids > 0 or pids > 0:
            points = 100
            msg = \
                'Your (meta)data includes %i references to other digital objects and %i references for contributors. Do you think you can improve that information?' \
                % (pids, orcids)
        else:

            points = 0
            msg = \
                'Your (meta)data does not include references to other digital objects or contributors. If your digital object is isolated, you can consider this OK, but it is recommendable to include such as references'

        return (points, msg)

    def rda_i3_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

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

        return self.rda_i3_01m()

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
        msg = ''

        orcids = 0
        pids = 0
        dois = 0
        try:
            for (index, row) in self.metadata.iterrows():
                if len(ut.get_orcid_str(row['text_value'])) > 0 \
                    and ut.check_orcid(ut.get_orcid_str(row['text_value'
                                                                ])):
                    orcids = orcids + 1
                if len(ut.get_handle_str(row['text_value'])) > 0 \
                    and ut.check_handle(ut.get_handle_str(row['text_value'
                                                                  ])):
                    pids = pids + 1
                if len(ut.get_doi_str(row['text_value'])) > 0 \
                    and ut.check_doi(ut.get_doi_str(row['text_value'
                                                            ])):
                    dois = dois + 1
        except Exception as err:
            print('Exception: %s' % err)

        if orcids > 0 or pids > 0 or dois > 0:
            points = 100
            msg = \
                'Your (meta)data includes %i qualified references to other digital objects and %i references to contributors. Do you think you can improve that information?' \
                % (pids + dois, orcids)
        else:

            points = 0
            msg = \
                'Your (meta)data does not include qualified references to other digital objects or contributors. If your digital object is isolated, you can consider this OK, but it is recommendable to include such as references'

        return (points, msg)

    def rda_i3_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        Description of the indicator RDA-I3-02D

        This indicator is about the way data is connected to other data. The references need to be
        qualified which means that the relationship role of the related resource is specified, for
        example that a particular link is a specification of a unit of m

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

        return self.rda_i3_02m()

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
        msg = ''
        qualifiers = ''
        for (index, row) in self.metadata.iterrows():
            if row['element'] == 'relation':
                qualifiers = qualifiers + ' %s' % row['text_value']
        if qualifiers != '':
            points = 100
            msg = \
                'Your (meta)data is connected with the following relationships: %s' \
                % qualifiers
        else:
            points = 0
            msg = \
                'Your (meta)data does not include any relationship. If yoour digital object is isolated, this indicator is OK, but it is recommendable to include at least some contextual information'
        return (points, msg)

    def rda_i3_04m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data. The references need
        to be qualified which means that the relationship role of the related resource is specified,
        for example dataset X is derived from dataset Y.

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

        # TODO check

        return self.rda_i3_03m()

    # REUSABLE

    def rda_r1_1_01m(self):
        points = 0
        msg = ''
        license = []
        for (index, row) in self.metadata.iterrows():
            if row['qualifier'] == 'license':
                license.append(row['text_value'])

        if len(license) > 0:
            points = 100
            msg = \
                'Indicator OK. Your digital object includes license information'
        else:
            points = 0
            msg = 'You should include information about the license.'

        return (points, msg)

    def rda_r1_1_02m(self):

        # Check if license is URL

        points = 0
        msg = ''
        license = []
        for (index, row) in self.metadata.iterrows():
            if row['qualifier'] == 'license':
                license.append(row['text_value'])

        for row in license:
            lic_ok = ut.check_url(row[0])

        if len(license) and lic_ok:
            points = 100
            msg = 'Your license refers to a standard reuse license'
        else:
            points = 0
            msg = \
                'Your license is NOT included or DOES NOT refer to a standard reuse license'

        return (points, msg)

    def rda_r1_1_03m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license. More information about that principle can be found here.

        This indicator is about the way that the reuse licence is expressed. Rather than being a
        human-readable text, the licence should be expressed in such a way that it can be processed
        by machines, without human intervention, for example in automated searches.

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
        msg = ''
        license = []
        for (index, row) in self.metadata.iterrows():
            if row['qualifier'] == 'license':
                license.append(row['text_value'])

        for row in license:
            lic_ok = ut.check_url(row[0])

        if len(license) and lic_ok:
            points = 100
            msg = 'Your license refers to a standard reuse license'
        else:
            points = 0
            msg = \
                'Your license is NOT included or DOES NOT refer to a standard reuse license'

        return (points, msg)

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

        points = 0
        msg = \
            'Currently, DIGITAL.CSIC does not include community-bsed schemas. If you need to include yours, please contact.'
        return (points, msg)

    def rda_r1_2_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.2: (Meta)data are associated with
        detailed provenance. More information about that principle can be found here.

        This indicator requires that the metadata provides provenance information according to a
        cross-domain language.

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
        msg = \
            'Currently, DIGITAL.CSIC does not include community-bsed schemas. If you need to include yours, please contact.'
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

        points = 0
        msg = \
            'Currently, DIGITAL.CSIC does not include community-bsed schemas. If you need to include yours, please contact.'
        return (points, msg)

    def rda_r1_3_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.

        This indicator requires that data complies with community standards.
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
        msg = \
            'Your data format does not complies with your community standards. If you think this is wrong, please, contact us to include your format.'
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

        points = 0
        msg = \
            'Currently, DIGITAL.CSIC does not include community-bsed schemas. If you need to include yours, please contact.'
        return (points, msg)

    def rda_r1_3_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that the data follows a community standard that has a machineunderstandable expression.

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
        msg = \
            'Currently, DIGITAL.CSIC does not include community-bsed schemas. If you need to include yours, please contact.'
        return (points, msg)

# UTILS

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
