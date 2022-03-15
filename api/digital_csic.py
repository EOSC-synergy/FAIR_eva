#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import idutils
import json
import logging
import psycopg2
import requests
from api.evaluator import Evaluator
import pandas as pd
import api.utils as ut
import sys

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
        self.file_list = None

        if self.id_type == 'doi' or self.id_type == 'handle':
            api_endpoint = 'https://digital.csic.es'
            api_metadata, self.file_list = self.get_metadata_api(api_endpoint, self.item_id, self.id_type)
            if api_metadata is not None:
                if len(api_metadata) > 0:
                    self.access_protocols = ['http']
                    self.metadata = api_metadata
                    temp_md = self.metadata.query("element == 'identifier'")
                    self.item_id = temp_md.query("qualifier == 'uri'")['text_value'].values[0]
            logging.info("API metadata: %s" % api_metadata)
        else:
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

                self.metadata = self.get_metadata_db()
                logging.debug('METADATA: %s' % (self.metadata.to_string()))
            except Exception as e:
                logging.error('Error connecting DB')
                logging.error(e)
        logging.debug("Metadata is: %s" % self.metadata)
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
            self.metadata_schemas = ast.literal_eval(config[plugin]['metadata_schemas'])
            self.metadata_quality = 100 # Value for metadata balancing
        except Exception as e:
            logging.error("Problem loading plugin config: %s" % e)

        global _
        _ = super().translation()

    def get_metadata_api(self, api_endpoint, item_pid, item_type):
        if item_type == "doi":
            md_key = "dc.identifier.doi"
        elif item_type == "handle":
            md_key = "dc.identifier.uri"
            item_pid = ut.pid_to_url(item_pid, item_type)

        try:
            data = {"key": md_key, "value": item_pid}
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            logging.debug("to POST: %s" % data)
            r = requests.post(api_endpoint + '/rest/items/find-by-metadata-field', data=json.dumps(data),
                              headers=headers, verify=False, timeout=15)
            logging.debug("ID FOUND: %s" % r.text)
            if r.status_code == 200:
                item_id = r.json()[0]['id']
                r = requests.get(api_endpoint + '/rest/items/%s/metadata' % item_id,
                                 headers=headers, verify=False, timeout=15)
            md = []
            for e in r.json():
                split_term = e['key'].split('.')
                metadata_schema = self.metadata_prefix_to_uri(split_term[0])
                element = split_term[1]
                if len(split_term) > 2:
                    qualifier = split_term[2]
                else:
                    qualifier = ''
                text_value = e['value']
                md.append([text_value, metadata_schema, element, qualifier])
            metadata = pd.DataFrame(md, columns=['text_value', 'metadata_schema', 'element', 'qualifier'])

            r = requests.get(api_endpoint + '/rest/items/%s/bitstreams' % item_id,
                             headers=headers, verify=False, timeout=15)
            file_list = []
            for e in r.json():
                file_list.append([e['name'], e['name'].split('.')[-1], e['format'], api_endpoint + e['link']])
            file_list = pd.DataFrame(file_list, columns=['name', 'extension', 'format', 'link'])
        except Exception as e:
            logging.debug("Problem creating Metadata from API: %s" % e)
            metadata = []
            file_list = []
        return metadata, file_list

    def get_metadata_db(self):
        query = 'SELECT metadatavalue.text_value, metadatafieldregistry.metadata_schema_id, metadatafieldregistry.element,\
                metadatafieldregistry.qualifier FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s and \
    item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id' \
                % self.internal_id
        cursor = self.connection.cursor()
        cursor.execute(query)
        metadata = pd.DataFrame(cursor.fetchall(),
                                columns=['text_value',
                                         'metadata_schema', 'element',
                                         'qualifier'])
        return metadata

    # TESTS
    # ACCESS
    def rda_a1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        The indicator refers to the information that is necessary to allow the requester to gain access
        to the digital object. It is (i) about whether there are restrictions to access the data (i.e.
        access to the data may be open, restricted or closed), (ii) the actions to be taken by a
        person who is interested to access the data, in particular when the data has not been
        published on the Web and (iii) specifications that the resources are available through
        eduGAIN7 or through specialised solutions such as proposed for EPOS.
        Technical proposal: Resolve the identifier
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
        # 1 - Check metadata record for access info
        msg = _('No access information can be found in the metadata. Please, add information to the following term(s): %s' % self.terms_access)
        points = 0

        md_term_list = pd.DataFrame(self.terms_access, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list['found']) > 0:
            for index, elem in md_term_list.iterrows():
                if elem['found'] == 1:
                    msg = msg + _("| Metadata: %s.%s: ... %s" % (elem['term'], elem['qualifier'], self.metadata.loc[self.metadata['element'] == elem['term']].loc[self.metadata['qualifier'] == elem['qualifier']]))
                    points = 100
        # 2 - Parse HTML in order to find the data file
        item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
        resp = requests.head(item_id_http, allow_redirects=False, verify=False)
        if resp.status_code == 302:
            item_id_http = resp.headers['Location']
        resp = requests.head(item_id_http + "?mode=full", verify=False)
        if resp.status_code == 200:
            item_id_http = item_id_http + "?mode=full"

        msg_2, points_2, data_files = ut.find_dataset_file(self.metadata, item_id_http, self.supported_data_formats)
        if points_2 == 100 and points == 100:
            msg = _("%s \n Data can be accessed manually | %s" % (msg, msg_2))
        elif points_2 == 0 and points == 100:
            msg = _("%s \n Data can not be accessed manually | %s" % (msg, msg_2))
        elif points_2 == 100 and points == 0:
            msg = _("%s \n Data can be accessed manually | %s" % (msg, msg_2))
            points = 100
        elif points_2 == 0 and points == 0:
            msg = _('No access information can be found in the metadata. Please, add information to the following term(s): %s' % self.terms_access)
        return (points, msg)

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
        item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
        resp = requests.head(item_id_http, allow_redirects=False, verify=False)
        if resp.status_code == 302:
            item_id_http = resp.headers['Location']
        resp = requests.head(item_id_http + "?mode=full", verify=False)
        if resp.status_code == 200:
            item_id_http = item_id_http + "?mode=full"
        logging.debug("URL TO VISIT: %s" % item_id_http)
        metadata_dc = self.metadata[self.metadata['metadata_schema'] == self.metadata_schemas['dc']]
        points, msg = ut.metadata_human_accessibility(metadata_dc, item_id_http)
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logging.error(e)
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
        # 1 - Look for the metadata terms in HTML in order to know if they can be accessed manueally
        points = 0
        msg = "Metadata can not be found"
        try:
            item_id_http = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
            resp = requests.head(item_id_http, allow_redirects=False, verify=False)
            if resp.status_code == 302:
                item_id_http = resp.headers['Location']
            resp = requests.head(item_id_http + "?mode=full", verify=False)
            if resp.status_code == 200:
                item_id_http = item_id_http + "?mode=full"
            metadata_dc = self.metadata[self.metadata['metadata_schema'] == self.metadata_schemas['dc']]
            points, msg = ut.metadata_human_accessibility(metadata_dc, item_id_http)
            msg = _("%s \nMetadata found via Identifier" % msg)
        except Exception as e:
            logging.error(e)
        try:
            points = (points * self.metadata_quality) / 100
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
        msg = ""
        points = 0
        logging.debug("FILES: %s" % self.file_list)
        if self.file_list is None:
            return super().rda_a1_03d()
        elif 'link' not in self.file_list:
            return super().rda_a1_03d()
        else:
            headers = []
            for f in self.file_list['link']:
                try:
                    if ut.check_url(f):
                        res = requests.head(f, verify=False, allow_redirects=True)
                        if res.status_code == 200:
                            headers.append(res.headers)
                except Exception as e:
                        logging.error(e)
            if len(headers) > 0:
                msg = msg + _("\n Files can be downloaded: %s\n %s" % (headers, self.file_list['link']))
                points = 100
            else:
                msg = msg + _("\n Files can not be downloaded")
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
        msg = ""
        points = 0
        if self.file_list is None:
            return super().rda_a1_05d()
        else:
            protocol = 'http'
            number_of_files = len(self.file_list['link'])
            accessible_files = 0
            for f in self.file_list['link']:
                try:
                    res = requests.head(f, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        accessible_files += 1
                        msg = msg + "\n %s" % f
                except Exception as e:
                        logging.error(e)
            if accessible_files == number_of_files:
                points = 100
                msg = _("Data is accessible automatically via HTTP:") + msg
            elif accessible_files == 0:
                points = 0
                msg = _("Files are not accessible via HTTP")
            else:
                points = (accessible_files * 100) / number_of_files
                msg = _("Some of digital objects are accessible automatically via HTTP:") + msg

        return points, msg

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

        # INTEROPERABLE
    def rda_i1_02m(self):
        """ Indicator RDA-A1-01M
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
        """
        points, msg = super().rda_i1_02m()
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logging.error(e)
        return (points, msg)

    def rda_i3_01m(self):
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
        points, msg = super().rda_i3_01m()

        md_term_list = pd.DataFrame(self.terms_relations, columns=['term', 'qualifier'])
        md_term_list['text_value'] = [''] * len(self.terms_relations)
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list['found']) > 0:
            for index, elem in md_term_list.iterrows():
                if elem['found'] == 1:
                    if ut.check_standard_project_relation(elem['text_value']):
                        msg = msg + _("| Qualified references to related object: %s" % elem['text_value'])
                        points = 100
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
        # TODO: check provenance in digital CSIC - Dublin Core??
        prov_terms = [['description', 'provenance'], ['date', 'created'], ['description', 'abstract']]
        msg = _('Provenance information can not be found. Please, include the info in this term: %s' % prov_terms)
        points = 0

        md_term_list = pd.DataFrame(prov_terms, columns=['term', 'qualifier'])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list['found']) > 0:
            for index, elem in md_term_list.iterrows():
                if elem['found'] == 1:
                    msg = msg + _("| Provenance info found: %s.%s " % (elem['term'], elem['qualifier']))
                    points = (100 * (len(md_term_list) - (len(md_term_list) - sum(md_term_list['found']))) / len(md_term_list))
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
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')

        try:
            for e in self.metadata.metadata_schema.unique():
                logging.debug("Checking: %s" % e)
                logging.debug("Trying: %s" % self.metadata_schemas['dc'])
                if e == self.metadata_schemas['dc']:  # Check Dublin Core
                    if ut.check_url(e):
                        points = 100
                        msg = _("DIGITAL.CSIC supports qualified Dublin Core as well as other discipline agnostics schemes like DataCite. Terms found")
        except Exception as e:
            logging.error("Problem loading plugin config: %s" % e)
        try:
            points = (points * self.metadata_quality) / 100
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
        points, msg = super().rda_r1_3_02m()
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logging.error(e)

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

    def metadata_prefix_to_uri(self, prefix):
        config = configparser.ConfigParser()
        config.read('config.ini')
        plugin = 'digital_csic'
        uri = prefix
        try:
            metadata_schemas = ast.literal_eval(config[plugin]['metadata_schemas'])
            if prefix in metadata_schemas:
                uri = metadata_schemas[prefix]
        except Exception as e:
            logging.error("Problem loading plugin config: %s" % e)
        return uri
