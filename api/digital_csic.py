#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser
import psycopg2
import xml.etree.ElementTree as ET
import re
import requests
from api.evaluator import Evaluator
from pandas import DataFrame


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

    def __init__(self, item_id):
        if self.get_doi_str(item_id) != '':
            self.item_id = self.get_doi_str(item_id)
            self.id_type = 'doi'
        elif self.get_handle_str(item_id) != '':
            self.item_id = self.get_handle_str(item_id)
            self.id_type = 'handle'
        else:
            self.item_id = item_id
            self.id_type = 'internal'

        self.connection = None
        config = configparser.ConfigParser()
        config.read('config.ini')
        try:
            self.connection = psycopg2.connect(
                user=config['digital_csic']['db_user'],
                password=config['digital_csic']['db_pass'],
                host=config['digital_csic']['db_host'],
                port=config['digital_csic']['db_port'],
                database=config['digital_csic']['db_db'])
        except Exception as error:
            print('Error while fetching data from PostgreSQL ' + error)
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
            metadatafieldregistry.qualifier FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s and\
item.item_id = metadatavalue.item_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id' \
            % self.internal_id
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.metadata = DataFrame(cursor.fetchall(),
                                  columns=['text_value',
                                           'metadata_schema', 'element',
                                           'qualifier'])

        # SELECT bitstream.name FROM item2bundle, bundle2bitstream, bitstream WHERE item2bundle.item_id = 319688 AND item2bundle.bundle_id = bundle2bitstream.bundle_id AND bundle2bitstream.bitstream_id = bitstream.bitstream_id;
        # SELECT DISTINCT metadataschemaregistry.namespace,
        # metadataschemaregistry.short_id FROM metadatavalue,
        # metadatafieldregistry, metadataschemaregistry WHERE
        # metadatavalue.item_id = 319688 AND metadatavalue.metadata_field_id =
        # metadatafieldregistry.metadata_field_id AND
        # metadatafieldregistry.metadata_schema_id =
        # metadataschemaregistry.metadata_schema_id;

        return None

    # TESTS
    #    FINDABLE

    def rda_f1_01m(self):
        doi_ok = False

        pid_ok = False
        for (index, row) in self.metadata.iterrows():
            print(row)
            if row['qualifier'] == 'doi':
                doi_ok = self.check_doi(
                    re.findall(
                        r'10[\.-]+.[\d\.-]+/[\w\.-]+/[\w\.-]+',
                        row['qualifier'])[0])
            elif row['qualifier'] == 'uri' and row['qualifier'] \
                    == 'url':
                pid_ok = self.check_url(row['text_value'])
        points = 0
        msg = ''
        if doi_ok or pid_ok:
            points = 100
            msg = 'Indicator OK. DOI or PID assigned to your (meta)data'
        else:
            points = 0
            msg = 'You should add a DOI or PID to your (meta)data'

        return (points, msg)

    def rda_f1_01d(self):
        (points, msg) = self.rda_f1_01m()
        return (points, msg)

    def rda_f2_01m(self):
        (points_g, msg_g) = self.rda_f2_01m_generic()
        (points_d, msg_d) = self.rda_f2_01m_disciplinar()
        return ((points_g + points_d) / 2, msg_g + ' | ' + msg_d)

    def rda_f2_01m_generic(self):

        # TODO different generic metadata standards?
        # Checkin Dublin Core

        msg = 'Checking Dublin Core'

        dc_terms = [[
            'contributor',
            'date',
            'description',
            'identifier',
            'publisher',
            'rights',
            'title',
            'subject',
        ], [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]]

        for (index, row) in self.metadata.iterrows():
            if row['element'] in dc_terms[0]:
                dc_terms[1][dc_terms[0].index(row['element'])] = 1

        sum_array = 0
        for e in dc_terms[1]:
            sum_array = sum_array + e
        if len(dc_terms[1]) == sum_array:
            msg = msg + '... All mandatory terms included'
            points = 100
        else:
            msg = msg + '... Missing terms:'
            i = 0
            missing_elements = 0
            for e in dc_terms[1]:
                if e == 0:
                    msg = msg + ' ' + dc_terms[0][i]
                    missing_elements = missing_elements + 1
                i = i + 1
            points = 100 * (len(dc_terms[1]) - missing_elements) \
                / len(dc_terms[1])

        return (points, msg)

    def rda_f2_01m_disciplinar(self):

        # TODO disciplinar standards

        points = 50
        msg = 'No disciplinar metadata defined'
        return (points, msg)

    def rda_f3_01m(self):
        """ Indicator RDA-F3-01M
        This indicator is linked to the following principle: F3: Metadata clearly and explicitly include
        the identifier of the data they describe. More information about that principle can be found
        here.

        The indicator deals with the inclusion of the reference (i.e. the identifier) of the digital object
        in the metadata so that the digital object can be accessed.

        Technical proposal: Check the metadata term where the object is identified

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

        # TODO check relationship if the item is not a datasetitself
        # TODO VERY generic like that

        rela = []
        for (index, row) in self.metadata.iterrows():
            if 'rela' in row['element']:
                rela.append(row)

        points = 0
        msg = ''
        if len(rela) > 0:
            points = 100
            msg = \
                'Indicator OK. Your digital object includes reference to data or other objects'
        else:
            points = 0
            msg = \
                'If your digital object derives from any dataset, it should be referenced'
        return (points, msg)

    def rda_f4_01m(self):

        # TODO Any other way?

        msg = ''
        base_url = 'http://digital.csic.es/dspace-oai/request'
        oai_id = 'oai:digital.csic.es:%s' % self.item_id
        if self.check_oai_pmh_item(base_url, oai_id):
            points = 100
            msg = \
                'Your digital object is available via OAI-PMH harvesting protocol'
        else:
            points = 0
            msg = \
                'Your digital object is not available via OAI-PMH. Please, contact to DIGITAL.CSIC admins'

        return (points, msg)

    # ACCESSIBLE

    def rda_a1_01m(self):
        points = 100
        msg = \
            'Indicator OK. DIGITAL.CSIC provides an standardised protocol to access the (meta)data (HTTP)'
        return (points, msg)

    def rda_a1_02m(self):
        points = 100
        msg = \
            'Indicator OK. DIGITAL.CSIC allows manual access to metadata'
        return (points, msg)

    def rda_a1_02d(self):
        points = 100
        msg = 'Indicator OK. DIGITAL.CSIC allows manual access to data'
        return (points, msg)

    def rda_a1_03m(self):
        """ Indicator RDA-A1-03M Metadata identifier resolves to a metadata record
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.

        Technical proposal: Checks if the identifier is a DOI or PID and tests if it goes to digital.csic.

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

        landing_url = 'digital.csic.es'

        points = 0
        msg = \
            'Provided ID does not resolve to DIGITAL.CSIC. This test need to be improved'

        if self.id_type == 'doi':
            url = 'http://dx.doi.org/%s' % self.item_id
            response = requests.get(url, verify=False)
            if response.history:
                print('Request was redirected')
                for resp in response.history:
                    print(resp.status_code, resp.url)
                if landing_url in response.url:
                    points = 100
                    msg = 'Your Unique identifier is a DOI and redirects correctly to DIGITAL.CSIC'
        else:
            url = 'http://hdl.handle.net/%s' % self.item_id
            response = requests.get(url, verify=False)
            if response.history:
                print('Request was redirected')
                for resp in response.history:
                    print(resp.status_code, resp.url)
                if landing_url in response.url:
                    points = 100
                    msg = \
                        'Your Unique identifier is a Handle PID and redirects correctly to DIGITAL.CSIC'

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

        (points, msg) = self.rda_a1_03m()
        return (points, msg)

    def rda_a1_04m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the metadata is accessed and requires
        the protocol to be defined in a standard.

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

        (points, msg) = self.rda_a1_03m()
        if points == 100:
            msg = msg + '. Accessible via HTTP protocol.'
        msg = \
            '(Meta)data is not accessible using the identifier. Please, check with DIGITAL.CSIC'
        return (points, msg)

    def rda_a1_04d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the digital object is accessed and requires
        the protocol to be defined in a standard.

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

        return self.rda_a1_04m()

    def rda_a1_04m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the metadata is accessed and requires
        the protocol to be defined in a standard.

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

        (points, msg) = self.rda_a1_03m()
        if points == 100:
            msg = msg + '. Accessible via HTTP protocol.'
        msg = \
            'Data is not accessible using the identifier. Please, check with DIGITAL.CSIC'
        return (points, msg)

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

    def rda_a1_1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

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
            'Metadata of this digital object can be accessed via HTTP both manually and automatically (OAI-PMH)'
        return (points, msg)

    def rda_a1_1_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator requires that the protocol can be used free of charge which facilitates
        unfettered access.

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
            'Data of this digital object can be accessed via HTTP manually'
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
            if self.check_url(row[0]):
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
                if len(self.get_orcid_str(row['text_value'])) > 0 \
                    and self.check_orcid(self.get_orcid_str(row['text_value'
                                                                ])):
                    orcids = orcids + 1
                if len(self.get_handle_str(row['text_value'])) > 0 \
                    and self.check_handle(self.get_handle_str(row['text_value'
                                                                  ])):
                    pids = pids + 1
                if len(self.get_doi_str(row['text_value'])) > 0 \
                    and self.check_doi(self.get_doi_str(row['text_value'
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
            lic_ok = self.check_url(row[0])

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
            lic_ok = self.check_url(row[0])

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
        id_to_check = self.get_doi_str(item_id)
        print('DOI is %s' % id_to_check)
        temp_str = '%' + item_id + '%'
        if len(id_to_check) != 0:
            if self.check_doi(id_to_check):
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
            id_to_check = self.get_handle_str(item_id)
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

        return self.get_handle_str(handle_id)
