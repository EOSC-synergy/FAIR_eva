#!/usr/bin/python
# -*- coding: utf-8 -*-
import api.utils as ut
import ast
import configparser
import gettext
import json
import logging
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import sys
import api.utils as ut
from api.evaluator import Evaluator

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='\'%(name)s:%(lineno)s\' | %(message)s')
    
logger = logging.getLogger(os.path.basename(__file__))



class DSpace_7(Evaluator):

    """ A class used to define FAIR indicators tests. It contains all the references to all the tests 
    ...
    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an identifier from the repo)
    oai_base : str
        Open Archives initiative , This is the place in which the API will ask for the metadata
    lang : Language
    """

    def __init__(self, item_id, oai_base=None, lang='en'):
        if oai_base == "":
            oai_base = None
        logger.debug("Call parent")
        super().__init__(item_id, oai_base, lang)
        logger.debug("Parent called")
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
        config.read('./config.ini')
        self.base_url = config['dspace7']['base_url']
        print('BASE %s' % self.base_url)
        self.internal_id = self.get_internal_id(item_id)
        self.metadata = self.get_item_metadata(self.internal_id)
        self.access_protocol = []
        self.oai_base = oai_base
        print('INTERNAL ID: %s ITEM ID: %s' % (self.internal_id,
                                               self.item_id))
        if len(self.metadata) > 0:
            self.access_protocols = ['http', 'REST-API']

        # Config attributes
        config = configparser.ConfigParser()
        config.read('config.ini')
        plugin = 'dspace7'
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
            self.metadata_quality = 100  # Value for metadata quality
            self.metadata_schemas = ast.literal_eval(config[plugin]['metadata_schemas'])
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)
        
        # Translations
        global _
        _ = super().translation()

        return None

    # TESTS
    #    FINDABLE

    # ACCESSIBLE

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
        msg = 'Digital Object is not accessible'

        url = self.base_url + 'api/core/items/%s/bundles' \
            % self.internal_id
        resp = requests.get(url)
        items = json.loads(resp.content)
        num_files = 0
        name_files = ''
        for e in items['_embedded']['bundles']:
            url = self.base_url + 'api/core/bundles/%s/bitstreams' \
                % e['uuid']
            resp_file = requests.get(url)
            print(url)
            files = json.loads(resp_file.content)
            print(files)
            for e_b in files['_embedded']['bitstreams']:
                print('Bitstream ID: %s | Name: %s' % (e_b['uuid'],
                                                       e_b['name']))
                name_files = name_files + ' ' + e_b['name']
                num_files = num_files + 1
                if ut.check_url(e_b['_links']['content']['href']):
                    points = points + 100
        points = points / num_files
        if points == 100:
            msg = \
                'Your files (%s) are automatically accessible via HTTP' \
                % name_files
        else:
            msg = 'Some of your files (%s) are not accessible via HTTP' \
                % name_files

        return (points, msg)

    def rda_a1_1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Technical proposal:

        Parameters:

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
            'DSpace allows restricted access to digital object using institutional AAI'
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
            'DSpace preserves the metadata even if the digital object is deleted'
        return (points, msg)

    # INTEROPERABLE

    def rda_i1_01m(self):

        # TODO Check

        points = 0
        url = self.base_url \
            + 'oai/request?verb=GetRecord&metadataPrefix=oai_dc&identifier=%s%s' \
            % ('oai:localhost:', self.internal_id)
        oai = requests.get(url)
        xml_check = False
        json_check = False
        msg = ''
        try:
            xmlTree = ET.fromstring(oai.text)
            xml_check = True
            msg = msg + ' XML '
        except ET.ParseError as err:
            msg = \
                'Metadata IS NOT using interoperable representation (XML)'
        except Exception as err:
            msg = 'Internal problem executing the test: %s' % err

        if type(self.metadata).__name__ == 'dict':
            json_check = True
            msg = msg + ' JSON '
        if xml_check or json_check:
            points = 100
            msg = \
                'Metadata is represented by interoperable formats (%s)' \
                % msg
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

        url = self.base_url + 'api/core/items/%s/bundles' \
            % self.internal_id
        resp = requests.get(url)
        items = json.loads(resp.content)
        num_files = 0
        name_files = ''
        for e in items['_embedded']['bundles']:
            url = self.base_url + 'api/core/bundles/%s/bitstreams' \
                % e['uuid']
            resp_file = requests.get(url)
            files = json.loads(resp_file.content)
            for e_b in files['_embedded']['bitstreams']:
                print('Bitstream ID: %s | Name: %s' % (e_b['uuid'],
                                                       e_b['name']))
                name_files = name_files + ' ' + e_b['name']
                num_files = num_files + 1
                if e_b['name'].split('.')[-1] in standard_list:
                    points = points + 100

        if points == 0:
            msg = \
                'The digital object is not in an accepted standard format. If you think the format should be accepted, please contact DSpace admin'
        elif points < 100:
            msg = \
                'Some of the files are in an standard format. Please Check (%s)' \
                % name_files
        else:
            msg = 'Your digital objects are in an standard format: %s' \
                % name_files

        return (points, msg)

    def rda_i1_02m(self):
        (points, msg) = self.rda_i1_01m()
        if points == 100:
            msg = \
                'Metadata can be extracted using machine-actionable features (XML/JSON Metadata)'
        else:
            msg = \
                'Metadata CAN NOT be extracted using machine-actionable features'

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

        return self.rda_a1_05d()

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

        md_schemas = []
        for e in self.metadata:
            if e.split('.')[0] not in md_schemas:
                md_schemas.append(e.split('.')[0])

        url = self.base_url + 'api/core/metadataschemas'
        resp = requests.get(url)
        sch = json.loads(resp.content)
        for e in sch['_embedded']['metadataschemas']:
            if e['prefix'] in md_schemas:
                if ut.check_url(e['namespace']):
                    points = 100
                    msg = \
                        'The metadata standard is well-document within a persistent identifier'

        if points == 0:
            msg = \
                'The metadata standard documentation can not be retrieved. Schema(s): %s' \
                % str(md_schemas)
        elif points < 100:
            msg = \
                'Some of the metadata schemas used are not accessible via persistent identifier. Schema(s): %s' \
                % str(md_schemas)

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
        for elem in self.metadata:
            if 'contributor' in elem:
                orcids = orcids + 1
            if 'relation' in elem:
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
            for elem in self.metadata:
                if ut.check_orcid(self.metadata[elem][0]['value']):
                    orcids = orcids + 1
                elif ut.check_handle(self.metadata[elem][0]['value']):
                    pids = pids + 1
                elif ut.check_doi(self.metadata[elem][0]['value']):
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
        for elem in self.metadata:
            if 'relation' in elem:
                qualifiers = qualifiers + ' %s' \
                    % self.metadata[elem][0]['value']

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

        for elem in self.metadata:
            if 'license' in elem:
                msg = ' %s' % self.metadata[elem][0]['value']
        if len(msg) > 0:
            points = 100
            msg = \
                'Indicator OK. Your digital object includes license information: ' \
                + msg
        else:
            points = 0
            msg = 'You should include information about the license.'

        return (points, msg)

    def rda_r1_1_02m(self):

        # TODO check more than one license
        # Check if license is URL

        points = 0
        msg = ''
        lic_ok = False
        for elem in self.metadata:
            if 'license' in elem:
                lic_ok = ut.check_url(self.metadata[elem][0]['value'])

        if lic_ok:
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

        # TODO check if it is standard

        points = 0
        msg = ''

        lic_ok = False
        for elem in self.metadata:
            if 'license' in elem:
                lic_ok = ut.check_url(self.metadata[elem][0]['value'])

        if lic_ok:
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
            'Currently, DSpace 7 does not include community-bsed schemas. If you need to include yours, please contact.'
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
            'Currently, DSpace 7 does not include community-bsed schemas. If you need to include yours, please contact.'
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
            'Currently, DSpace 7 does not include community-bsed schemas. If you need to include yours, please contact.'
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
            'Currently, DSpace 7 does not include community-bsed schemas. If you need to include yours, please contact.'
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
            'Currently, DSpace 7 does not include community-bsed schemas. If you need to include yours, please contact.'
        return (points, msg)

# UTILS

    def get_internal_id(self, item_id):
        internal_id = item_id
        resp = requests.get(self.base_url + 'api/pid/find?id=%s'
                            % item_id)
        print(resp)
        try:
            item = json.loads(resp.content)
            internal_id = item['id']
        except Exception as err:

            print('Exception: %s' % err)
            return internal_id

        # print("Internal ID: %s" % internal_id)

        return internal_id

    def get_item_metadata(self, internal_id):
        url = self.base_url + 'api/core/items/' + internal_id
        resp = requests.get(url)
        try:
            items = json.loads(resp.content)
            data = []
            for e in items['metadata']:
                elements = e.split(".")
                if len(elements) == 3:
                    for ec in items['metadata'][e]:
                        data.append([elements[0], elements[1], ec["value"], elements[2]])
                if len(elements) == 2:
                    for ec in items['metadata'][e]:
                        data.append([elements[0], elements[1], ec["value"], None])
            metadata = pd.DataFrame(data, columns=['metadata_schema', 'element', 'text_value', 'qualifier'])
            return metadata
        except Exception as err:
            print('Esception: %s' % err)
            return None
