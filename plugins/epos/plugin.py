#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import csv
import json
import logging
import os
import sys
import urllib
import xml.etree.ElementTree as ET

import idutils
import numpy as np
import pandas as pd
import requests
from dicttoxml import dicttoxml

import api.utils as ut
from api.evaluator import ConfigTerms, Evaluator, MetadataValuesBase
from fair import load_config

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))


class MetadataValues(MetadataValuesBase):
    def _get_identifiers_metadata(self, element_values):
        """Get the list of identifiers for the metadata.

        * Format EPOS DEV API:
            "id": "77c89ce5-cbaa-4ea8-bcae-fdb1da932f6e"
        """
        return [element_values]

    def _get_identifiers_data(self, element_values):
        """Get the list of identifiers for the data.

        * Format EPOS DEV API:
            "identifiers": [{
                "type": "DOI",
                "value": "https://doi.org/10.13127/tsunami/neamthm18"
            }]
        """
        # DOI
        return [
            value_data["value"]
            for value_data in element_values
            if value_data.get("type", "").lower() == "doi"
        ]

    def _get_formats(self, element_values):
        """Return the list of formats defined through <availableFormats> metadata
        attribute.

        * Format EPOS PROD & DEV API:
             "availableFormats": [{
                 "format": "SHAPE-ZIP",
                 "href": "https://www.ics-c.epos-eu.org/api/v1/execute/b8b5f0c3-a71c-448e-88ac-3a3c5d97b08f?format=SHAPE-ZIP",
                 "label": "SHAPE-ZIP",
                 "originalFormat": "SHAPE-ZIP",
                 "type": "ORIGINAL"
             }]
        """
        return list(
            filter(
                None, [value_data.get("format", "") for value_data in element_values]
            )
        )

    def _get_temporal_coverage(self, element_values):
        """Return a list of tuples with temporal coverages for start and end date.

        * Format EPOS PROD & DEV API:
            "temporalCoverage": [{
                "startDate": "2018-01-31T00:00:00Z"
            }]
        """
        return [
            (value_data.get("startDate", ""), value_data.get("endDate", ""))
            for value_data in element_values
        ]

    def _get_person(self, element_values):
        """Return a list with person-related info.

        * Format EPOS DEV API:
            "contactPoints": [{
              "id": "8069667d-7676-4c02-b98e-b1e044ab4cd7",
              "metaid": "2870c8e4-c616-4eaf-b84d-502f6a3ee2fb",
              "uid": "http://orcid.org/0000-0003-4551-3339/Contact"
            }]
        """
        return [value_data.get("uid", "") for value_data in element_values]

    def _validate_format(self, formats):
        from fair import app_dirname

        formats_data = {}
        non_valid_formats = []

        # IANA internet_media_types
        formats_data["iana"] = []
        iana_formats = []
        plugin_config = load_config(plugin="epos")  # FIXME: don't hardcode 'epos' here
        internet_media_types_path = ast.literal_eval(
            plugin_config.get("internet_media_types", "path")
        )
        internet_media_types_path = os.path.join(app_dirname, internet_media_types_path)
        logging.debug(
            "Using local file for IANA Internet Media Types: %s"
            % internet_media_types_path
        )
        try:
            with open(internet_media_types_path, "r") as fname:
                csv_reader = csv.reader(fname)
                for row in csv_reader:
                    iana_formats.append(row[0].lower())
            logging.debug(
                "Collected %s formats from IANA Internet Media Types"
                % len(iana_formats)
            )
        except (FileNotFoundError, IOError):
            msg = "Could not get media types from IANA Internet Media Types. Check `internet_media_types:path` section in plugin's config.ini"
            logging.error(msg)  # FIXME: throw custom exception
        for _format in formats:
            if _format.lower() in iana_formats:
                logging.debug(
                    "Format complies with IANA Internet Media Types vocabulary: %s"
                    % _format
                )
                formats_data["iana"].append(_format)
            else:
                logging.debug(
                    "Format does not comply with IANA Internet Media Types vocabulary: %s"
                    % _format
                )
                non_valid_formats.append(_format)

        return formats_data, non_valid_formats

    def _get_license(self, element_values):
        """Return a list of licenses.

        * Format EPOS PROD & DEV API:
            "license": "https://spdx.org/licenses/CC-BY-4.0.html"
        """
        if isinstance(element_values, str):
            logging.debug(
                "Provided licenses as a string for metadata element <license>: %s"
                % element_values
            )
            return [element_values]
        elif isinstance(element_values, list):
            logging.debug(
                "Provided licenses as a list for metadata element <license>: %s"
                % element_values
            )
            return element_values

    def _validate_license(self, licenses, vocabularies, machine_readable=False):
        license_data = {}
        non_valid_licenses = []
        for vocabulary_id, vocabulary_url in vocabularies.items():
            # Store successfully validated licenses, grouped by CV
            license_data[vocabulary_id] = []
            # SPDX
            if vocabulary_id in ["spdx"]:
                logging.debug("Validating licenses according to SPDX: %s" % licenses)
                for _license in licenses:
                    if ut.is_spdx_license(_license, machine_readable=machine_readable):
                        logging.debug(
                            "License successfully validated according to SPDX vocabulary: %s"
                            % _license
                        )
                        license_data[vocabulary_id].append(_license)
                    else:
                        non_valid_licenses.append(_license)

        return license_data, non_valid_licenses


class Plugin(Evaluator):
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

    name = "epos"

    @property
    def metadata_utils(self):
        return MetadataValues()

    def __init__(self, item_id, oai_base=None, lang="en", config=None):
        logger.debug("Creating instance of %s plugin" % self.name)
        super().__init__(item_id, oai_base, lang, self.name)
        # TO REDEFINE - WHICH IS YOUR PID TYPE?
        self.id_type = "uuid"
        global _
        _ = super().translation()

        # You need a way to get your metadata in a similar format
        metadata_sample = self.get_metadata()
        self.metadata = pd.DataFrame(
            metadata_sample,
            columns=["metadata_schema", "element", "text_value", "qualifier"],
        )
        logger.debug("METADATA: %s" % (self.metadata))
        # Protocol for (meta)data accessing
        if len(self.metadata) > 0:
            self.access_protocols = ["http"]
        # Config attributes
        self.terms_map = ast.literal_eval(self.config[self.name]["terms_map"])
        self.identifier_term = ast.literal_eval(
            self.config[self.name]["identifier_term"]
        )
        self.terms_quali_generic = ast.literal_eval(
            self.config[self.name]["terms_quali_generic"]
        )
        self.terms_quali_disciplinar = ast.literal_eval(
            self.config[self.name]["terms_quali_disciplinar"]
        )
        self.terms_cv = ast.literal_eval(self.config[self.name]["terms_cv"])
        self.supported_data_formats = ast.literal_eval(
            self.config[self.name]["supported_data_formats"]
        )
        self.terms_qualified_references = ast.literal_eval(
            self.config[self.name]["terms_qualified_references"]
        )
        self.terms_relations = ast.literal_eval(
            self.config[self.name]["terms_relations"]
        )
        self.metadata_access_manual = ast.literal_eval(
            self.config[self.name]["metadata_access_manual"]
        )
        self.data_access_manual = ast.literal_eval(
            self.config[self.name]["data_access_manual"]
        )
        self.terms_access_protocols = ast.literal_eval(
            self.config[self.name]["terms_access_protocols"]
        )

        # self.vocabularies = ast.literal_eval(self.config[self.name]["vocabularies"])
        self.dict_vocabularies = ast.literal_eval(
            self.config[self.name]["dict_vocabularies"]
        )
        self.vocabularies = list(self.dict_vocabularies.keys())
        self.terms_cv_map = ast.literal_eval(self.config[self.name]["terms_cv_map"])

        self.metadata_standard = ast.literal_eval(
            self.config[self.name]["metadata_standard"]
        )

        self.metadata_authentication = ast.literal_eval(
            self.config[self.name]["metadata_authentication"]
        )
        self.metadata_persistence = ast.literal_eval(
            self.config[self.name]["metadata_persistence"]
        )
        self.terms_cv = ast.literal_eval(self.config[self.name]["terms_cv"])

        self.fairsharing_username = ast.literal_eval(
            self.config["fairsharing"]["username"]
        )

        self.fairsharing_password = ast.literal_eval(
            self.config["fairsharing"]["password"]
        )
        self.fairsharing_metadata_path = ast.literal_eval(
            self.config["fairsharing"]["metadata_path"]
        )
        self.fairsharing_formats_path = ast.literal_eval(
            self.config["fairsharing"]["formats_path"]
        )
        self.internet_media_types_path = ast.literal_eval(
            self.config["internet_media_types"]["path"]
        )

    @staticmethod
    def get_ids(oai_base, pattern_to_query=""):
        url = oai_base + "/resources/search?facets=false&q=" + pattern_to_query
        response_payload = ut.make_http_request(url=url)
        results = response_payload.get("results", [])
        return [
            result["id"] for result in results["distributions"] if "id" in result.keys()
        ]

    def get_metadata(self):
        metadata_sample = []
        eml_schema = "epos"

        final_url = (
            self.oai_base + "/resources/details/" + self.item_id + "?extended=true"
        )

        error_in_metadata = False
        headers = {
            "accept": "application/json",
        }
        response = requests.get(
            final_url,
            headers=headers,
        )
        if not response.ok:
            msg = (
                "Error while connecting to metadata repository: %s (status code: %s)"
                % (response.url, response.status_code)
            )
            error_in_metadata = True
        dicion = response.json()
        if not dicion:
            msg = (
                "Error: empty metadata received from metadata repository: %s"
                % final_url
            )
            error_in_metadata = True
        if error_in_metadata:
            logger.error(msg)
            raise Exception(msg)

        for key in dicion.keys():
            if str(type(dicion[key])) == "<class 'dict'>":
                q = dicion[key]
                for key2 in q.keys():
                    metadata_sample.append([eml_schema, key2, q[key2], key])

            if key == "relatedDataProducts":
                q = dicion[key][0]

                for key2 in q.keys():
                    if str(type(q[key2])) == "<class 'dict'>":
                        w = q[key2]
                        for key3 in w.keys():
                            metadata_sample.append([eml_schema, key3, w[key3], key2])
                    elif (
                        str(type(q[key2])) == "<class 'list'>"
                        and len(q[key2]) == 0
                        and str(type(q[key2][0])) == "<class 'dict'>"
                    ):
                        w = q[key2][0]

                        for key3 in w.keys():
                            metadata_sample.append([eml_schema, key3, w[key3], key2])

                    else:
                        metadata_sample.append([eml_schema, key2, q[key2], key])
                        """Elif str(type(dicion[key])) == "<class 'list'>" and:

                        q = dicion[key]
                        if str(type(q[0])) == "<class 'dict'>":
                          if len(q) ==1:
                             q=q[0]
                             for key2 in q.keys():
                                 metadata_sample.append([eml_schema, key2, q[key2], key])
                        else:

                            for elem in q:
                                metadata_sample.append([eml_schema, key, elem, None])
                        """
            else:
                metadata_sample.append([eml_schema, key, dicion[key], None])
        return metadata_sample

    def eval_persistency(self, id_list, data_or_metadata="(meta)data"):
        points = 0
        msg_list = []
        points_per_id = round(100 / len(id_list))
        for _id in id_list:
            _points = 0
            if ut.is_persistent_id(_id):
                _msg = "Found persistent identifier for the %s: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = points_per_id
            else:
                _msg = "Identifier is not persistent for the %s: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = 0
            points += _points
            msg_list.append({"message": _msg, "points": _points})

        return (points, msg_list)

    def eval_uniqueness(self, id_list, data_or_metadata="(meta)data"):
        points = 0
        msg_list = []
        points_per_id = round(100 / len(id_list))
        for _id in id_list:
            _points = 0
            if ut.is_unique_id(_id):
                _msg = "Found a globally unique identifier for the %s: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = points_per_id
            else:
                _msg = "Identifier found for the %s is not globally unique: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = 0
            points += _points
            msg_list.append({"message": _msg, "points": _points})

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term")
    def rda_f1_01m(self, **kwargs):
        """Indicator RDA-F1-01M: Metadata is identified by a persistent identifier.

        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the metadata is identified by a persistent identifier.
        A persistent identifier ensures that the metadata will remain findable over time, and reduces
        the risk of broken links.

        Parameters
        ----------
        identifier_term : dict
            A dictionary with metadata information about the identifier/s used for the metadata (see ConfigTerms class for further details)

        Returns
        -------
        points
            - 0/100   if no persistent identifier is used  for the metadata
            - 100/100 if a persistent identifier is used for the metadata

        msg
            Message with the results or recommendations to improve this indicator
        """
        id_list = kwargs["Metadata Identifier"]

        points, msg_list = self.eval_persistency(id_list, data_or_metadata="metadata")
        logger.debug(msg_list)

        if points == 0:
            if self.metadata_persistence:
                if self.check_link(self.metadata_persistence):
                    points = 100
                    msg = "Identifier found and persistence policy given "
                    return (points, {"message": msg, "points": points})
        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term_data")
    def rda_f1_01d(self, **kwargs):
        """Indicator RDA-F1-01D: Data is identified by a persistent identifier.

        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the data is identified by a persistent identifier.
        A persistent identifier ensures that the data will remain findable over time and reduces the
        risk of broken links.

        Parameters
        ----------
        identifier_term_data : dict
            A dictionary with metadata information about the identifier/s used for the data (see ConfigTerms class for further details)

        Returns
        -------
        points
            Returns a value (out of 100) that reflects the amount of data identifiers that are persistent.
        msg
            Message with the results or recommendations to improve this indicator
        """
        id_list = kwargs["Data Identifier"]

        points, msg_list = self.eval_persistency(id_list, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term")
    def rda_f1_02m(self, **kwargs):
        """Indicator RDA-F1-02M: Metadata is identified by a globally unique identifier.

        This indicator is linked to the following principle: F1 (meta)data are assigned a globally unique and eternally persistent identifier.

        The indicator serves to evaluate whether the identifier of the metadata is globally unique, i.e. that there are no two identical
        identifiers that identify different metadata records.

        Parameters
        ----------
        identifier_term_data : dict
            A dictionary with metadata information about the identifier/s used for the data (see ConfigTerms class for further details)

        Returns
        -------
        points
            - 0/100   if the identifier used for the metadata is not globally unique.
            - 100/100 if the identifier used for the metadata is globally unique.
        msg
            Message with the results or recommendations to improve this indicator
        """
        id_list = kwargs["Metadata Identifier"]

        points, msg_list = self.eval_uniqueness(id_list, data_or_metadata="metadata")
        logger.debug(msg_list)

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term_data")
    def rda_f1_02d(self, **kwargs):
        """Indicator RDA-F1-02D: Data is identified by a globally unique identifier.

        This indicator is linked to the following principle: F1 (meta)data are assigned a globally unique and eternally persistent identifier.

        The indicator serves to evaluate whether the identifier of the data is globally unique, i.e. that there are no two people that would
        use that same identifier for two different digital objects.

        Parameters
        ----------
        identifier_term_data : dict
            A dictionary with metadata information about the identifier/s used for the data (see ConfigTerms class for further details)

        Returns
        -------
        points
            Returns a value (out of 100) that reflects the amount of data identifiers that are globally unique (i.e. DOI, Handle, UUID).
        msg
            Message with the results or recommendations to improve this indicator
        """
        id_list = kwargs["Data Identifier"]

        points, msg_list = self.eval_uniqueness(id_list, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)

    @ConfigTerms(term_id="terms_findability_richness")
    def rda_f2_01m(self, **kwargs):
        """Indicator RDA-F2-01M: Rich metadata is provided to allow discovery.

        This indicator is linked to the following principle: F2: Data are described with rich metadata.

        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.

        Parameters
        ----------
        terms_findability_richness : dict (see ConfigTerms class for further details)
            A dictionary with metadata information about the elements that provide findability/discoverability richness.

        Returns
        -------
        points
            Returns a value (out of 100) that reflects the grade of compliance with the "Dublin Core Metadata for Resource Discovery".
        msg
            Message with the results or recommendations to improve this indicator.
        """
        terms_findability_dublin_core = ast.literal_eval(
            self.config["dublin-core"]["terms_findability_richness"]
        )
        if not terms_findability_dublin_core:
            points, msg_list = (
                0,
                [
                    "Dublin Core's terms/elements for 'Metadata for Resource Discovery' are not defined in configuration. Please do so within '[dublin-core]' section."
                ],
            )
        else:
            dc_term_num = len(terms_findability_dublin_core)
            points_per_dc_term = round(100 / dc_term_num)

            metadata_keys_not_empty = [k for k, v in kwargs.items() if v]
            metadata_keys_not_empty_num = len(metadata_keys_not_empty)
            logger.debug(
                "Found %s metadata keys with values: %s"
                % (metadata_keys_not_empty_num, metadata_keys_not_empty)
            )

            points = metadata_keys_not_empty_num * points_per_dc_term
            msg_list = [
                "Found %s (out of %s) metadata elements matching 'Dublin Core Metadata for Resource Discovery' elements"
                % (metadata_keys_not_empty_num, dc_term_num)
            ]

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term_data")
    def rda_f3_01m(self, **kwargs):
        """Indicator RDA-F3-01M: Metadata includes the identifier for the data.

        This indicator is linked to the following principle: F3: Metadata clearly and explicitly include the identifier of the data they describe.

        The indicator deals with the inclusion of the reference (i.e. the identifier) of the
        digital object in the metadata so that the digital object can be accessed.

        Parameters
        ----------
        identifier_term_data : dict
            A dictionary with metadata information about the identifier/s used for the data (see ConfigTerms class for further details)

        Returns
        -------
        points
            - 100 if metadata contains identifiers for the data.
            - 0 otherwise.
        msg
            Statement about the assessment exercise
        """
        id_list = kwargs["Data Identifier"]

        msg = "Metadata includes identifier/s for the data: %s" % id_list
        points = 100

        return (points, [{"message": msg, "points": points}])

    def rda_f4_01m(self):
        """Indicator RDA-F4-01M: Metadata is offered in such a way that it can be harvested and indexed.

        This indicator is linked to the following principle: F4: (Meta)data are registered or indexed
        in a searchable resource.

        The indicator tests whether the metadata is offered in such a way that it can be indexed.
        In some cases, metadata could be provided together with the data to a local institutional
        repository or to a domain-specific or regional portal, or metadata could be included in a
        landing page where it can be harvested by a search engine. The indicator remains broad
        enough on purpose not to  limit the way how and by whom the harvesting and indexing of
        the data might be done.

        Returns
        -------
        points
            - 100 if metadata could be gathered using any of the supported protocols (OAI-PMH, HTTP).
            - 0 otherwise.
        msg
            Message with the results or recommendations to improve this indicator
        """
        if not self.metadata.empty:
            msg = "Metadata is gathered programmatically through HTTP (API REST), thus can be harvested and indexed."
            points = 100
        else:
            msg = (
                "Could not gather metadata from endpoint: %s. Metadata cannot be harvested and indexed."
                % self.oai_base
            )
            points = 0

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_access")
    def rda_a1_01m(self, **kwargs):
        """RDA indicator RDA-A1-01M: Metadata contains information to enable the user to get access to the data.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to the information that is necessary to allow the requester to gain access
        to the digital object. It is (i) about whether there are restrictions to access the data (i.e.
        access to the data may be open, restricted or closed), (ii) the actions to be taken by a
        person who is interested to access the data, in particular when the data has not been
        published on the Web and (iii) specifications that the resources are available through
        eduGAIN7 or through specialised solutions such as proposed for EPOS.

        Returns
        -------
        points
            - 80/100 points if pointers for downloading the data are provided
            - 20/100 points if license information is provided (10 if license exists & 10 if open license)
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []

        # Check #1: presence of 'DOI' and/or 'downloadURL'
        data_id_list = kwargs["Data Identifier"]
        data_url_list = kwargs["Download Link"]

        if not data_id_list and not data_url_list:
            msg = "Metadata does not provide URI-based identifiers and/or download links to access the data"
            logger.warning(msg)
            return (
                points,
                [
                    {
                        "message": msg,
                        "points": points,
                    }
                ],
            )
        else:
            has_identifiers = False
            has_links = False
            if data_id_list:
                has_identifiers = True
            if data_url_list:
                has_links = True
            msg = (
                "Metadata provides URI-based identifiers and/or download links to access the data: %s"
                % [item for item in data_id_list + data_url_list if item]
            )
            points = 80
            logger.debug(msg)
        msg_list.append({"message": msg, "points": points})

        # Check #2: presence of a license
        point_licenses = 0
        license_list = kwargs["License"]
        if license_list:
            point_licenses = 10
            msg = "Found license/s for the data: %s" % license_list
            logger.info(msg)
        else:
            msg = "License/s not found for the data"
            logger.warning(msg)
        points += point_licenses
        msg_list.append({"message": msg, "points": point_licenses})

        # Check #2.1: open license listed in SPDX
        points_licenses_spdx = 0
        points_license_spdx, msg_license_spdx = self.rda_r1_1_02m(
            license_list=license_list
        )
        if points_license_spdx == 100:
            points_licenses_spdx = 10
            msg = "License/s listed in the SPDX license list: %s" % license_list
            logger.info(msg)
        else:
            msg = "License/s not listed in SPDX license list: %s" % license_list
            logger.warning(msg)
        points += points_licenses_spdx
        msg_list.append({"message": msg, "points": points_licenses_spdx})

        logger.debug("Total points for RDA-A1-01M: %s" % points)

        return (points, msg_list)

    def rda_a1_02m(self):
        """Indicator RDA-A1-02M: Metadata can be accessed manually (i.e. with human intervention).

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        The indicator refers to any human interactions that are needed if the requester wants to
        access metadata. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.

        Returns
        -------
        points
            100/100 if the link to the manual aquisition of the metadata exists
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "No reference has been found for the manual obtention of the metadata"
        msg_list = []

        if self.metadata_access_manual:
            if ut.check_link(self.metadata_access_manual[0]):
                msg = (
                    "Documentation for the manual obtention of the metadata can be found in "
                    + str(self.metadata_access_manual[0])
                )
                points = 100

        msg_list.append({"message": msg, "points": points})

        return (points, msg_list)

    def rda_a1_02d(self):
        """Indicator RDA-A1-02D: Data can be accessed manually (i.e. with human intervention).

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        The indicator refers to any human interactions that are needed if the requester wants to
        access data. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.

        Returns
        -------
        points
            100/100 if the link to the manual aquisition of the data exists
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "No reference has been found for the manual obtention of the data"
        msg_list = []

        if self.data_access_manual:
            if ut.check_link(self.data_access_manual[0]):
                msg = (
                    "Documentation for the manual obtention of the data can be found in "
                    + str(self.data_access_manual[0])
                )
                points = 100

        msg_list.append({"message": msg, "points": points})

        return (points, msg_list)

    def rda_a1_03m(self):
        """Indicator RDA-A1-03M: Metadata identifier resolves to a metadata record.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.

        Returns
        -------
        points
            100/100 if the metadata record can be obtained (0/100 otherwise)
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = (
            "Metadata record cannot be retrieved from metadata identifier: %s"
            % self.item_id
        )
        if not self.metadata.empty:
            points = 100
            msg = (
                "Metadata record could be retrieved from metadata identifier: %s"
                % self.item_id
            )

        msg_list = [{"message": msg, "points": points}]

        return (points, msg_list)

    @ConfigTerms(term_id="terms_access")
    def rda_a1_03d(self, **kwargs):
        """Indicator RDA-A1-03D: Data identifier resolves to a digital object.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        This indicator is about the resolution of the identifier that identifies the digital object. The
        identifier assigned to the data should be associated with a formally defined
        retrieval/resolution mechanism that enables access to the digital object, or provides access
        instructions for access in the case of human-mediated access. The FAIR principle and this
        indicator do not say anything about the mutability or immutability of the digital object that
        is identified by the data identifier -- this is an aspect that should be governed by a
        persistence policy of the data provider.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
            - 100/100 if all object identifiers are resolvable 0 if none
            - For any other case the resultant points will be proportional to the % of resovable identifiers
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = ""

        data_id_list = kwargs["Data Identifier"]
        data_url_list = kwargs["Download Link"]
        if not data_id_list and not data_url_list:
            msg = "No URI-based identifier to access the data was found"
            logger.warning(msg)
            return (
                points,
                [
                    {
                        "message": msg,
                        "points": points,
                    }
                ],
            )

        # Check if resolvable
        data_access_uri = data_id_list + data_url_list
        data_access_uri_num = len(data_access_uri)
        resolvable_uris = []
        for uri in data_access_uri:
            resolves = False
            schemes = idutils.detect_identifier_schemes(uri)
            logger.debug("Identifier schemes found: %s" % schemes)
            if "doi" in schemes or "handle" in schemes:
                resolves = ut.resolve_handle(uri)[0]
            elif "url" in schemes:
                resolves = ut.check_link(uri)
            else:
                logger.warning(
                    "Scheme/s used by the identifier not known: %s" % schemes
                )
            if resolves:
                resolvable_uris.append(uri)

        resolvable_uris_num = len(resolvable_uris)
        if resolvable_uris:
            msg = "Found %s/%s resolvable URIs for accessing the data: %s" % (
                resolvable_uris_num,
                data_access_uri_num,
                resolvable_uris,
            )
            logger.debug(msg)
        else:
            msg = (
                "None of the URIs found for accessing the data is resolvable: %s"
                % data_access_uri
            )
            logger.warning(msg)

        remainder = resolvable_uris_num % data_access_uri_num
        if remainder == 0:
            if resolvable_uris_num > 0:
                points = 100
        else:
            points = round((resolvable_uris_num * 100) / data_access_uri_num)

        msg_list = [{"message": msg, "points": points}]

        return (points, msg_list)

    def rda_a1_04m(self, return_protocol=False):
        """Indicator RDA-A1-04M: Metadata is accessed through standarised protocol.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        The indicator concerns the protocol through which the metadata is accessed and requires
        the protocol to be defined in a standard.

        Returns
        -------
        points
            100/100 if the endpoint protocol is in the accepted list of standarised protocols
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0

        protocol = ut.get_protocol_scheme(self.oai_base)
        if protocol in self.terms_access_protocols:
            points = 100
            msg = "Found a standarised protocol to access the metadata record: " + str(
                protocol
            )
        else:
            msg = (
                "Found a non-standarised protocol to access the metadata record: %s"
                % str(protocol)
            )
        msg_list = [{"message": msg, "points": points}]

        if return_protocol:
            return (points, msg_list, protocol)

        return (points, msg_list)

    @ConfigTerms(term_id="terms_access")
    def rda_a1_04d(self, return_protocol=False, **kwargs):
        """Indicator RDA-A1-04D: Data is accessible through standardized protocol.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        The indicator concerns the protocol through which the digital object is accessed and requires
        the protocol to be defined in a standard.

        Returns
        -------
        points
            100/100 if the download protocol is in the accepted protocols list
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = ""

        url = kwargs["Download Link"]
        if len(url) == 0:
            return (
                points,
                [
                    {
                        "message": "Could not check data access protocol: EPOS metadata element <downloadURL> not found",
                        "points": points,
                    }
                ],
            )

        protocol_list = []
        for link in url:
            parsed_endpoint = urllib.parse.urlparse(link)
            protocol = parsed_endpoint.scheme
            if protocol in self.terms_access_protocols:
                points = 100
                protocol_list.append(protocol)

        if points == 100:
            msg = "Found %s standarised protocols to access the data: %s" % (
                len(protocol_list),
                protocol_list,
            )
        msg_list = [{"message": msg, "points": points}]

        if return_protocol:
            return (points, msg_list, protocol_list)

        return (points, msg_list)

    @ConfigTerms(term_id="terms_access")
    def rda_a1_05d(self, **kwargs):
        """Indicator RDA-A1-05D: Data can be accessed automatically (i.e. by a computer program).

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to automated interactions between machines to access digital objects.
        The way machines interact and grant access to the digital object will be evaluated by the
        indicator.

        Returns
        -------
        points
            100/100 if the downloadURL link is provided and resolvable
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []

        data_url_list = kwargs["Download Link"]
        if data_url_list:
            for url in data_url_list:
                if ut.check_link(url):
                    points = 100
                    msg_list.append(
                        {
                            "message": "Data can be accessed programmatically: the URL is resolvable: %s"
                            % str(url),
                            "points": points,
                        }
                    )
        else:
            return (
                points,
                [
                    {
                        "message": "Could not check data access protocol: EPOS metadata element <downloadURL> not found",
                        "points": points,
                    }
                ],
            )

        return (points, msg_list)

    def rda_a1_1_01m(self):
        """Indicator RDA-A1.1_01M: Metadata is accessible through a free access
        protocol.

        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Returns
        -------
        points
            100/100 if the endpoint protocol is in the list of accepted free protocols
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg_list, protocol = self.rda_a1_04m(return_protocol=True)
        if points == 100:
            msg_list = [
                {
                    "message": "Found a free protocol to access the metadata record: %s"
                    % protocol,
                    "points": points,
                }
            ]

        return (points, msg_list)

    def rda_a1_1_01d(self):
        """Indicator RDA-A1.1-01D: Data is accessible through a free access protocol.

        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Returns
        -------
        points
            100/100 if the downloadURL protocol is in the list of accepted free protocols
        msg
            Message with the results or recommendations to improve this indicator
        """
        result_data = self.rda_a1_04d(return_protocol=True)
        protocol_list = []
        if len(result_data) == 3:
            points, msg_list, protocol_list = result_data
        else:
            points, msg_list = result_data

        if points == 0:
            msg_list = [
                {
                    "message": "None of the protocol/s to access the data is free",
                    "points": points,
                }
            ]
        elif points == 100:
            msg_list = [
                {
                    "message": "Found free protocol/s to access the data: %s"
                    % " ".join(protocol_list),
                    "points": points,
                }
            ]

        return (points, msg_list)

    def rda_a1_2_01d(self):
        """Indicator RDA-A1_2-01D The protocol allows for an authentication and authorisation where necessary.
        The indicator requires the way that access to the digital object can be authenticated and
        authorised and that data accessibility is specifically described and adequately documented.
        Technical proposal:

        Returns
        -------
        points
            - 0/100   if there is no known authentication/authorisation protocol
            - 100/100 If the authentication/authorisation protocol is given through config.ini
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = _(
            "At the time, EPOS does not provide authentication or authorisation protocols"
        )
        if self.metadata_authentication:
            points = 100
            msg = "The authentication is given by: " + str(
                self.metadata_authentication[0]
            )
        return points, msg

    @ConfigTerms(term_id="terms_access")
    def rda_a2_01m(self, return_protocol=False, **kwargs):
        """Indicator RDA-A2-01M A2: Metadata should be  accessible even when the data is no longer available.
        The indicator intends to verify that information about a digital object is still available after
        the object has been deleted or otherwise has been lost. If possible, the metadata that
        remains available should also indicate why the object is no longer available.
        Technical proposal:
        -------

        points
            - 50/100 If there is no given metadata persistence policy , depends on the authority where this Digital Object is stored
            - 100/100 if the metadata persistence policy is given
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = _(
            "Preservation policy depends on the authority where this Digital Object is stored"
        )

        if self.metadata_persistence:
            if ut.check_link(self.metadata_persistence[0]):
                points = 100
                msg = "The preservation policy is: " + str(self.metadata_persistence[0])
            return (points, [{"message": msg, "points": points}])

        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        _elements = [
            "downloadURL",
        ]

        url = terms_access_metadata.loc[
            terms_access_metadata["element"] == "downloadURL", "text_value"
        ]

        if len(url.values) == 0:
            return (
                points,
                [
                    {
                        "message": "Could not check data access protocol or persistence policy: EPOS metadata element <downloadURL> not found",
                        "points": points,
                    }
                ],
            )
        else:
            if not ut.check_link(url.values[0]):
                points = 100
                msg = "Metadata is available after the data is no longer available."

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_cv")
    def rda_i1_01m(self, **kwargs):
        """Indicator RDA-I1-01M: Metadata uses knowledge representation expressed in standarised format.

        This indicator is linked to the following principle: I1: (Meta)data use a formal,
        accessible, shared, and broadly applicable language for knowledge representation.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, in particular the data model and format.

        Returns
        -------
        points
            Points are proportional to the number of followed vocabularies

        msg
            Message with the results or recommendations to improve this indicator
        """
        terms_cv = kwargs["terms_cv"]
        terms_cv_list = terms_cv["list"]
        terms_cv_metadata = terms_cv["metadata"]

        # Dictionary containing the validation results, grouped by metadata element (standarised), e.g.:
        # {'License': {'validated_number': 1, 'not_validated_number': 0, 'data': {'spdx': ['https://spdx.org/licenses/CC-BY-4.0.html'], 'not_validated': []}}}
        validation_results = {}

        total_metadata_values = 0
        for element in terms_cv_list:
            element_map_key = element[0]
            element_map_key_normalised = self.terms_cv_map[element_map_key]
            validation_results[element_map_key_normalised] = {}
            # Get element values
            element_df = terms_cv_metadata.loc[
                terms_cv_metadata["element"].isin([element[0]]),
                "text_value",
            ]
            element_values = element_df.values.tolist()
            if len(element_values) > 0:
                element_values = element_values[
                    0
                ]  # NOTE: check whether it is safe to get only first value
                logging.debug(
                    "Element <%s> has values present in the metadata: %s"
                    % (element, element_values)
                )
                # Gathering
                metadata_values = EPOSMetadataValues.gather(
                    element_values, element=element_map_key_normalised
                )
                if metadata_values:
                    total_metadata_values += len(metadata_values)
                    logging.debug(
                        "Metadata values have been obtained for element <%s>: %s"
                        % (element_map_key, metadata_values)
                    )
                    # Validation
                    validation_data = EPOSMetadataValues.validate(
                        metadata_values, element_map_key_normalised
                    )
                    logging.debug(
                        "Validation data obtained for element <%s>: %s"
                        % (element_map_key, validation_data)
                    )
                    _failed_validation_no = len(
                        validation_data.get("not_validated", [])
                    )
                    _passed_validation_no = len(metadata_values) - _failed_validation_no
                    validation_results[element_map_key_normalised][
                        "validated_number"
                    ] = _passed_validation_no
                    validation_results[element_map_key_normalised][
                        "not_validated_number"
                    ] = _failed_validation_no
                    validation_results[element_map_key_normalised][
                        "data"
                    ] = validation_data
                    logging.info(
                        "Validation results for element <%s>: %s"
                        % (
                            element_map_key_normalised,
                            validation_results[element_map_key_normalised],
                        )
                    )
                else:
                    logging.warning(
                        "No metadata values obtained for element: %s" % element_map_key
                    )
            else:
                logging.warning(
                    "Element <%s> does not have values present in the metadata"
                    % element
                )

        # Get points
        total_not_validated = 0
        for element, results in validation_results.items():
            total_not_validated += results.get("not_validated_number", 0)
        total_validated = total_metadata_values - total_not_validated
        msg = "Found %s out of %s metadata values validated" % (
            total_validated,
            total_metadata_values,
        )
        logging.debug(msg)

        # for i in range(len(vocabularies_element_list)):
        #     if vocabularies_element_list[i] != "Not available":
        #         used_vocabularies.append(self.vocabularies[i])
        # info = dict(zip(self.vocabularies, vocabularies_element_list))
        # for vocab in info.keys():
        #     if vocab == "ROR":
        #         for iden in info[vocab][0]:
        #             # return(0,'testing')
        #             if iden["type"] == "ROR":
        #                 exists, name = ut.check_ror(iden["value"])
        #                 if exists:
        #                     if name == info[vocab][0][0]["dataProviderLegalName"]:
        #                         passed += 1
        #                         passed_msg += vocab + ", "

        #     # Not sure on how to validate PIC
        #     if vocab == "imtypes":
        #         points2, msg2 = self.rda_i1_01d()

        #         if points2 == 100:
        #             passed += 1
        #             passed_msg += vocab + ", "

        #     if vocab == "spdx":
        #         points3, mg3 = self.rda_r1_1_02m()

        #         if points3 == 100:
        #             passed += 1
        #             passed_msg += vocab + ", "

        #     if vocab == "ORCID":
        #         orc = info[vocab][0][0]["uid"]

        #         if idutils.is_orcid(orc):
        #             passed += 1
        #             passed_msg += vocab + ", "

        #     else:
        #         if info[vocab] == "Not available":
        #             total -= 1
        #             not_available_msg += vocab + ", "

        points = 0
        if total_metadata_values > 0:
            points = total_validated / total_metadata_values * 100

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_reusability_richness")
    def rda_i1_01d(self, **kwargs):
        """Indicator RDA-I1-01D: Data uses knowledge representation expressed in standarised format.

        This indicator is linked to the following principle: I1: (Meta)data use a formal,
        accessible, shared, and broadly applicable language for knowledge representation.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, in particular the data model and format.

        Returns
        -------
        points
            100/100 If the file format is listed under IANA Internet Media Types
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "No internet media file path found"
        internetMediaFormats = []
        availableFormats = []
        path = self.internet_media_types_path[0]

        try:
            f = open(path)
            f.close()

        except:
            msg = "The config.ini internet media types file path does not arrive at any file. Try 'static/internetmediatipes190224.csv'"
            return (points, [{"message": msg, "points": points}])

        f = open(path)
        csv_reader = csv.reader(f)

        for row in csv_reader:
            internetMediaFormats.append(row[0])

        f.close()

        terms_reusability_richness = kwargs["terms_reusability_richness"]
        terms_reusability_richness_list = terms_reusability_richness["list"]
        terms_reusability_richness_metadata = terms_reusability_richness["metadata"]

        ele = terms_reusability_richness_metadata.loc[
            terms_reusability_richness_metadata["element"].isin(["availableFormats"]),
            "text_value",
        ]
        if len(ele.values) < 1:
            return (points, [{"message": msg, "points": points}])

        element = terms_reusability_richness_metadata.loc[
            terms_reusability_richness_metadata["element"].isin(["availableFormats"]),
            "text_value",
        ].values[0]

        for form in element:
            availableFormats.append(form["label"])

        msg = "None of the formats appear in internet media types"
        for aform in availableFormats:
            for iform in internetMediaFormats:
                if aform.casefold() == iform.casefold():
                    points = 100
                    msg = "Your data uses a correct way to present information present in https://www.iana.org/assignments/media-types/media-types.xhtml "
        return (points, [{"message": msg, "points": points}])

    def rda_i1_02m(self, **kwargs):
        """Indicator RDA-I1-02M: Metadata uses machine-understandable knowledge representation.

        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. M

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Returns
        -------
        points
            - 100/100 if metadata uses machine understandable knowledge representation (0/100 otherwise)
        msg
            Message with the results or recommendations to improve this indicator
        """
        msg = "No metadata standard"
        points = 0

        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        points, msg = self.rda_r1_3_01m()
        if points == 100:
            msg = (
                "The metadata standard in use provides a machine-understandable knowledge expression: %s"
                % self.metadata_standard
            )

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_data_model")
    def rda_i1_02d(self, **kwargs):
        """Indicator RDA-I1-02D: Data uses machine-understandable knowledge representation.

        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation.

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Returns
        -------
        points
            - 100/100 if data models correspond to machine readable formats
            - Otherwise, the resultant score will be proportional to the percentage of machine readable formats
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0

        terms_data_model = kwargs["terms_data_model"]
        terms_data_model_list = terms_data_model["list"]
        terms_data_model_metadata = terms_data_model["metadata"]

        if len(terms_data_model_list) == 0:
            msg = "EPOS API does not provide information about the knowledge representation model used for the data"

        else:
            element = terms_data_model_list
            data_model_elements = terms_data_model_metadata.loc[
                terms_data_model_metadata["element"].isin([element[0]]),
                "text_value",
            ]
            data_model_list = data_model_elements.values
            if len(data_model_list) > 0:
                points = 100
                msg = "Found information about the knowledge representation model used for the data"

        return (points, [{"message": msg, "points": points}])

    def rda_i2_01m(self):
        """Indicator RDA-I2-01D: Data uses FAIR-compliant vocabularies.

        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles.

        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "The checked vocabularies the current version are:"
        passed = 0

        for vocab in self.dict_vocabularies.keys():
            if not vocab == self.dict_vocabularies[vocab]:
                if ut.check_link(self.dict_vocabularies[vocab]):
                    passed += 1
                    msg += vocab + " "
        points = passed / len(self.dict_vocabularies.keys()) * 100
        return (points, [{"message": msg, "points": points}])

    def rda_i2_01d(self):
        """Indicator RDA-I2-01D: Data uses FAIR-compliant vocabularies.

        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles.

        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "This test implies access to the content of the data and match terms used there with FAIR-compliant vocabularies. As it is defined, its implementation is too costly"

        return (points, [{"message": msg, "points": points}])

    def rda_i3_01m(self):
        """Indicator RDA-I3-01M: Metadata includes references to other metadata.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

        Returns
        -------
        points
            100/100 if ORCID is found in the metadata
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg = self.rda_i3_03m()

        return (points, msg)

    def rda_i3_01d(self):
        """Indicator RDA-I3-01D: Data includes references to other data.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

        Returns
        -------
        points
            Currently returns 0 points, as it requires inspecting the content of the data
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "This test implies checking the presence of qualified references within the content of the data. As it is defined, its implementation is too costly."

        return (points, [{"message": msg, "points": points}])

    def rda_i3_02m(self):
        """Indicator RDA-I3-02M: Metadata includes references to other data.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data, for example linking to
        previous or related research data that provides additional context to the data. Please note
        that this is not about the link from the metadata to the data it describes; that link is
        considered in principle F3 and in indicator RDA-F3-01M.

        Returns
        -------
        points
            Returns 100/100 if qualified references are found (0/100 otherwise)
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "No references to other data."

        return (points, [{"message": msg, "points": points}])

    def rda_i3_02d(self):
        """Indicator RDA-I3-02D: Data includes qualified references to other data.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

        Returns
        -------
        points
            Currently returns 0 points, as it requires inspecting the content of the data
        msg
            Message with the results or recommendations to improve this indicator
        """

        points = 0
        msg = "This test implies checking the presence of qualified references within the content of the data. As it is defined, its implementation is too costly."

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_relations")
    def rda_i3_03m(self, **kwargs):
        """Indicator RDA-I3-03M: Metadata includes qualified references to other metadata.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other metadata, for example to
        descriptions of related resources that provide additional context to the data. The references
        need to be qualified which means that the relation

        Returns
        -------
        points
            100/100 if the ORCID appears in the metadata (ORCID considered a qualified reference to the Author of the file)
        msg
            Message with the results or recommendations to improve this indicator
        """
        person_id_list = kwargs["term_values"]

        # FIXME Need to validate ORCID format in order to report it as 'qualified'
        if person_id_list:
            points = 100
            msg = "Metadata has qualified references to other metadata"
        else:
            points = 0
            msg = "Metadata does not have qualified references to other metadata"

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_reusability_richness")
    def rda_r1_01m(self, **kwargs):
        """Indicator RDA-R1-01M: Plurality of accurate and relevant attributes are provided to allow reuse.

        This indicator is linked to the following principle: R1: (Meta)data are richly described with a
        plurality of accurate and relevant attributes. More information about that principle can be
        found here.

        The indicator concerns the quantity but also the quality of metadata provided in order to
        enhance data reusability.

        Returns
        -------
        points
            Proportional to the number of terms considered to enhance reusability
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0

        terms_reusability_richness = kwargs["terms_reusability_richness"]
        terms_reusability_richness_list = terms_reusability_richness["list"]
        terms_reusability_richness_metadata = terms_reusability_richness["metadata"]

        reusability_element_list = []
        for element in terms_reusability_richness_list:
            element_df = terms_reusability_richness_metadata.loc[
                terms_reusability_richness_metadata["element"].isin([element[0]]),
                "text_value",
            ]

            element_values = element_df.values
            if len(element_values) > 0:
                reusability_element_list.extend(element_values)
        if len(reusability_element_list) > 0:
            msg = "Found %s metadata elements that enhance reusability: %s" % (
                len(reusability_element_list),
                reusability_element_list,
            )
        else:
            msg = "Could not fing any metadata element that enhance reusability"
        points = (
            len(reusability_element_list) / len(terms_reusability_richness_list) * 100
        )

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_license")
    def rda_r1_1_01m(self, license_list=[], **kwargs):
        """Indicator RDA-R1.1-01M: Metadata includes information about the license under
        which the data can be reused.

        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear and accessible data usage license.

        This indicator is about the information that is provided in the metadata related to the conditions (e.g. obligations, restrictions) under which data can be reused. In the absence of licence information, data cannot be reused.

        Returns
        -------
        points
            100/100 if the license for data exists
        msg
            Message with the results or recommendations to improve this indicator
        """
        license_list = kwargs["License"]

        msg_list = []
        points = 0
        max_points = 100

        license_num = len(license_list)
        if license_num > 0:
            points = 100

            if license_num > 1:
                msg = "The licenses are : "
                for license in license_list:
                    msg = msg + " " + str(license) + " "
            else:
                msg = "The license is: " + str(license_list[0])

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_license")
    def rda_r1_1_02m(self, license_list=[], machine_readable=False, **kwargs):
        """Indicator R1.1-02M: Metadata refers to a standard reuse license.

        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.

        This indicator requires the reference to the conditions of reuse to be a standard licence,
        rather than a locally defined license.

        Returns
        -------
        points
            100/100 if the license is listed under the SPDX licenses
        msg
            Message with the results or recommendations to improve this indicator
        """
        license_list = kwargs["License"]

        points = 0
        max_points = 100

        license_num = len(license_list)
        license_standard_list = []
        points_per_license = round(max_points / license_num)
        for _license in license_list:
            if ut.is_spdx_license(_license, machine_readable=machine_readable):
                license_standard_list.append(_license)
                points += points_per_license
                logger.debug(
                    "License <%s> is considered as standard by SPDX: adding %s points"
                    % (_license, points_per_license)
                )
        if points == 100:
            msg = (
                "License/s in use are considered as standard according to SPDX license list: %s"
                % license_standard_list
            )
        elif points > 0:
            msg = (
                "A subset of the license/s in use (%s out of %s) are standard according to SDPX license list: %s"
                % (len(license_standard_list), license_num, license_standard_list)
            )
        else:
            msg = (
                "None of the license/s defined are standard according to SPDX license list: %s"
                % license_list
            )
        msg = " ".join([msg, "(points: %s)" % points])
        logger.info(msg)

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_license")
    def rda_r1_1_03m(self, **kwargs):
        """Indicator R1.1-03M: Metadata refers to a machine-understandable reuse
        license.

        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.

        This indicator is about the way that the reuse licence is expressed. Rather than being a human-readable text, the licence should be expressed in such a way that it can be processed by machines, without human intervention, for example in automated searches.

        Returns
        -------
        points
            100/100 if the license is provided in such a way that is machine understandable
        msg
            Message with the results or recommendations to improve this indicator
        """
        license_list = kwargs["License"]

        _points_license, _msg_license = self.rda_r1_1_02m(
            license_list=license_list, machine_readable=True
        )
        if _points_license == 100:
            _msg = "License/s are machine readable according to SPDX"
        elif _points_license == 0:
            _msg = "License/s are not machine readable according to SPDX"
        else:
            _msg = "A subset of the license/s are machine readable according to SPDX"
        logger.info(_msg)

        return (_points_license, [{"message": _msg, "points": _points_license}])

    @ConfigTerms(term_id="terms_provenance")
    def rda_r1_2_01m(self, **kwargs):
        """Indicator R1.2-01M: Metadata includes provenance information about community-
        specific standard.

        This indicator is linked to the following principle: R1.2: (Meta)data are associated with detailed provenance.

        This indicator requires the metadata to include information about the provenance of the data, i.e. information about the origin, history or workflow that generated the data, in a way that is compliant with the standards that are used in the community for which the data is curated.

        Returns
        -------
        points
            100/100 if provenance information is provided
        msg
            Message with the results or recommendations to improve this indicator
        """
        provenance_list = kwargs["term_values"]

        points = 0
        msg = "No provenance or curation references found in the metadata"

        if len(provenance_list) > 0:
            points = 100

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_01m(self, **kwargs):
        """Indicator RDA-R1.3-01M: Metadata complies with a community standard.

        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that data complies with community standards.

        Returns
        --------
        points
           100/100 if the metadata standard appears is listed under FAIRsharing
        """
        msg = "No metadata standard"
        points = 0
        offline = True
        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        try:
            f = open(self.fairsharing_metadata_path[0])
            f.close()

        except:
            msg = "The config.ini fairshraing metatdata_path does not arrive at any file. Try 'static/fairsharing_metadata_standards140224.json'"
            return (points, [{"message": msg, "points": points}])

        if self.fairsharing_username != [""]:
            offline = False

        fairsharing = ut.get_fairsharing_metadata(
            offline,
            password=self.fairsharing_password[0],
            username=self.fairsharing_username[0],
            path=self.fairsharing_metadata_path[0],
        )
        for standard in fairsharing["data"]:
            if self.metadata_standard[0] == standard["attributes"]["abbreviation"]:
                points = 100
                msg = "Metadata standard in use complies with a community standard according to FAIRsharing.org"
        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_reusability_richness")
    def rda_r1_3_01d(self, **kwargs):
        """Indicator RDA-R1.3-01D: Data complies with a community standard.

        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that data complies with community standards.

        Returns
        --------
        points
           100/100 if the data standard appears in Fairsharing (0/100 otherwise)
        """
        msg = "No metadata standard"
        points = 0
        offline = True
        availableFormats = []
        fairformats = []
        path = self.fairsharing_formats_path[0]

        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        terms_reusability_richness = kwargs["terms_reusability_richness"]
        terms_reusability_richness_list = terms_reusability_richness["list"]
        terms_reusability_richness_metadata = terms_reusability_richness["metadata"]

        ele = terms_reusability_richness_metadata.loc[
            terms_reusability_richness_metadata["element"].isin(["availableFormats"]),
            "text_value",
        ]
        if len(ele.values) < 1:
            return (points, [{"message": msg, "points": points}])

        element = terms_reusability_richness_metadata.loc[
            terms_reusability_richness_metadata["element"].isin(["availableFormats"]),
            "text_value",
        ].values[0]
        for form in element:
            availableFormats.append(form["label"])

        try:
            f = open(path)
            f.close()

        except:
            msg = "The config.ini fairshraing metatdata_path does not arrive at any file. Try 'static/fairsharing_formats260224.txt'"
            if offline == True:
                return (points, [{"message": msg, "points": points}])

        if self.fairsharing_username != [""]:
            offline = False

        if offline == False:
            fairsharing = ut.get_fairsharing_formats(
                offline,
                password=self.fairsharing_password[0],
                username=self.fairsharing_username[0],
                path=path,
            )

            for fform in fairsharing["data"]:
                q = fform["attributes"]["name"][24:]
                fairformats.append(q)

        else:
            f = open(path, "r")
            text = f.read()
            fairformats = text.splitlines()

        for fform in fairformats:
            for aform in availableFormats:
                if fform.casefold() == aform.casefold():
                    if points == 0:
                        msg = "Your item follows the comunity standard formats: "
                    points = 100
                    msg += "  " + str(aform)

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_02m(self, **kwargs):
        """Indicator RDA-1.3-02M: Metadata is expressed in compliance with a machine-
        understandable community standard.

        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that data complies with community standards.

        Returns
        --------
        points
           - 100/100 if the metadata standard is machine understandable (checked through FAIRsharing)
           - 0/100 otherwise
        """
        msg = "No metadata standard"
        points = 0

        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        points, msg = self.rda_r1_3_01m()
        if points == 100:
            msg = "The metadata standard in use is compliant with a machine-understandable community standard"

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_02d(self, **kwargs):
        """Indicator RDA-R1.3-02D: Data is expressed in compliance with a machine-
        understandable community standard.

        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that data complies with community standards.

        Returns
        --------
        Points
           - 100/100 if the data format is machine understandable
           - 0/100 otherwise
        """
        msg = ""
        points = 0

        points, _msg = self.rda_r1_3_01d()
        if points == 100:
            msg = "Your data standard is expressed in compliance with a  machine-understandable community standard"
        else:
            msg = "No data standard found"

        return (points, [{"message": msg, "points": points}])
