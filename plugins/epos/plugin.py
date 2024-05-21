#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import idutils
import logging
import os
import urllib

from api.evaluator import Evaluator
from api.evaluator import ConfigTerms
from fair import load_config
import pandas as pd
import numpy as np
import requests
import sys
import csv
import xml.etree.ElementTree as ET
import json
import api.utils as ut
from dicttoxml import dicttoxml


logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))


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
        self.metadata_standard = ast.literal_eval(
            self.config[self.name]["metadata_standard"]
        )

        self.metadata_authentication = ast.literal_eval(
            self.config[self.name]["metadata_authentication"]
        )
        self.metadata_persistence = ast.literal_eval(
            self.config[self.name]["metadata_persistence"]
        )
        self.terms_vocabularies = ast.literal_eval(
            self.config[self.name]["terms_vocabularies"]
        )

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
            self.config["internet media types"]["path"]
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
        term_data = kwargs["identifier_term"]
        term_metadata = term_data["metadata"]

        id_list = term_metadata.text_value.values

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
        term_data = kwargs["identifier_term_data"]
        term_metadata = term_data["metadata"]
        identifiers = []
        id_list = term_metadata.text_value.values[0]
        for ide in id_list:
            identifiers.append(ide["value"])

        points, msg_list = self.eval_persistency(identifiers, data_or_metadata="data")
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
        term_data = kwargs["identifier_term"]
        term_metadata = term_data["metadata"]

        id_list = term_metadata.text_value.values
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
        term_data = kwargs["identifier_term_data"]
        term_metadata = term_data["metadata"]
        identifiers = []
        id_list = term_metadata.text_value.values[0]
        for ide in id_list:
            identifiers.append(ide["value"])

        points, msg_list = self.eval_uniqueness(identifiers, data_or_metadata="data")
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
            term_data = kwargs["terms_findability_richness"]
            term_list = term_data["list"]
            term_metadata = term_data["metadata"]

            dc_term_num = len(terms_findability_dublin_core)
            points_per_dc_term = round(100 / dc_term_num)

            term_metadata_num = len(term_metadata.index.to_list())
            term_list_num = len(term_list)
            if term_metadata_num == term_list_num:
                logger.debug(
                    "Gathered all metadata terms defined in configuration (%s out of %s)"
                    % (term_metadata_num, term_list_num)
                )
            else:
                logger.warning(
                    "The number of metadata elements gathered differs from the expected list defined in configuration (%s out of %s)"
                    % (term_metadata_num, term_list_num)
                )
            points = term_metadata_num * points_per_dc_term
            msg_list = [
                "Found %s (out of %s) metadata elements matching 'Dublin Core Metadata for Resource Discovery' elements"
                % (term_metadata_num, dc_term_num)
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
        term_data = kwargs["identifier_term_data"]
        term_metadata = term_data["metadata"]

        # ConfigTerms already enforces term_metadata not to be empty
        id_list = term_metadata.text_value.values[0]
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
        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        # Check #1: presence of 'downloadURL' and 'DOI'
        _elements = ["downloadURL", "identifiers"]
        data_access_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(_elements)
        ]

        _indexes = data_access_elements.index.to_list()

        for element in data_access_elements.values:
            if element[1] == "identifiers":
                try:
                    if element[2][0]["type"] == "DOI":
                        points += 40
                except:
                    points += 0

            else:
                points += 40

        _msg = "Found %s metadata elements for accessing the data: %s" % (
            len(_indexes),
            _elements,
        )

        logger.info(_msg)
        msg_list.append({"message": _msg, "points": points})

        # Check #2: presence of a license
        _points = 0
        license_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(["license"]), "text_value"
        ]
        license_list = license_elements.values
        if len(license_list) > 0:
            _points = 10
            _msg = "Found a license for the data"
        else:
            _msg = "License not found for the data"
        points += _points
        logger.info(_msg)
        msg_list.append({"message": _msg, "points": _points})

        # Check #2.1: open license listed in SPDX
        _points = 0
        _points_license, _msg_license = self.rda_r1_1_02m(license_list=license_list)
        if _points_license == 100:
            _points = 10
            _msg = "License listed in SPDX license list"
        else:
            _msg = "License not listed in SPDX license list"
        points += _points
        logger.info(_msg)
        msg_list.append({"message": _msg, "points": _points})

        logger.info("Total points for RDA-A1-01M: %s" % points)

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
        msg = "No DOI or way to access the data was found "
        _msg_list = []
        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        _elements = ["downloadURL", "identifiers"]
        data_access_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(_elements)
        ]
        _indexes = data_access_elements.index.to_list()

        if _indexes == []:
            return (
                points,
                [
                    {
                        "message": "No DOI or way to access the data was found",
                        "points": points,
                    }
                ],
            )

        doi = terms_access_metadata.loc[
            terms_access_metadata["element"] == "identifiers"
        ].text_value
        if len(doi) == 0:
            return (points, [{"message": msg, "points": points}])
        doi = doi.values[0][0]["value"]

        if doi[:15] == "https://doi.org":
            doi = [doi[16:]]
        else:
            doi = [doi]

        if type(doi) in [str]:
            doi = [str]
        doi_items_num = len(doi)
        logger.debug("Obtained %s DOIs from metadata: %s" % (doi_items_num, doi))

        _resolves_num = 0
        for doi_item in doi:
            resolves, values = False, []
            _msgs = [
                "Found Handle/DOI identifier: %s (1 out of %s):"
                % (doi_item, doi_items_num)
            ]
            try:
                resolves, msg, values = ut.resolve_handle(doi_item)

            except Exception as e:
                _msg_list.append(str(e))
                logger.error(e)
                continue
            else:
                if resolves:
                    _resolves_num += 1
                    _msgs.append("(i) %s" % msg)
                if values:
                    _resolved_url = None
                    for _value in values:
                        if _value.get("type") in ["URL"]:
                            _resolved_url = _value["data"]["value"]
                    if _resolved_url:
                        _msgs.append("(ii) Resolution URL: %s" % _resolved_url)
                _msg_list.append(" ".join(_msgs))
        remainder = _resolves_num % doi_items_num
        if remainder == 0:
            if _resolves_num > 0:
                points = 100
        else:
            points = round((_resolves_num * 100) / doi_items_num)

        msg_list = [{"message": " ".join(_msg_list), "points": points}]

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

        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        _elements = [
            "downloadURL",
        ]
        data_access_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(_elements)
        ]

        url = terms_access_metadata.loc[
            terms_access_metadata["element"] == "downloadURL", "text_value"
        ]

        if len(url.values) == 0:
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

        for link in url.values:
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

        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        url = terms_access_metadata.loc[
            terms_access_metadata["element"] == "downloadURL", "text_value"
        ]
        url_list = url.values
        if len(url_list) > 0:
            for link in url_list:
                if ut.check_link(link):
                    points = 100
                    msg_list.append(
                        {
                            "message": "Data can be accessed programmatically: the URL is resolvable: %s"
                            % str(link),
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
        found_download_url = False
        result_data = self.rda_a1_04d(return_protocol=True)
        if len(result_data) == 3:
            points, msg_list, protocol_list = result_data
            found_download_url = True
        else:
            points, msg_list = result_data

        if points == 0:
            if found_download_url:
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

    @ConfigTerms(term_id="terms_vocabularies")
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
        points = 0

        msg = "No internet media file path found"
        passed = 0
        terms_vocabularies = kwargs["terms_vocabularies"]
        terms_vocabularies_list = terms_vocabularies["list"]
        terms_vocabularies_metadata = terms_vocabularies["metadata"]
        used_vocabularies = []
        vocabularies_element_list = []
        passed = 0
        not_available_msg = "Not available vocabularies: "
        available_msg = "Checked vocabularies: "
        passed_msg = "Vocabularies followed: "
        total = len(self.vocabularies)
        for element in terms_vocabularies_list:
            element_df = terms_vocabularies_metadata.loc[
                terms_vocabularies_metadata["element"].isin([element[0]]),
                "text_value",
            ]

            element_values = element_df.values
            if len(element_values) > 0:
                vocabularies_element_list.append(element_values)

            else:
                vocabularies_element_list.append("Not available")
        for i in range(len(vocabularies_element_list)):
            if vocabularies_element_list[i] != "Not available":
                used_vocabularies.append(self.vocabularies[i])
        info = dict(zip(self.vocabularies, vocabularies_element_list))

        for vocab in used_vocabularies:
            if vocab == "ROR":
                for iden in info[vocab][0]:
                    # return(0,'testing')
                    if iden["type"] == "ROR":
                        exists, name = ut.check_ror(iden["value"])
                        if exists:
                            if name == info[vocab][0][0]["dataProviderLegalName"]:
                                passed += 1
                                passed_msg += vocab + ", "

            # Not sure on how to validate PIC
            if vocab == "imtypes":
                points2, msg2 = self.rda_i1_01d()

                if points2 == 100:
                    passed += 1
                    passed_msg += vocab + ", "

            if vocab == "spdx":
                points3, mg3 = self.rda_r1_1_02m()

                if points3 == 100:
                    passed += 1
                    passed_msg += vocab + ", "

            if vocab == "ORCID":
                try:
                    orc = info[vocab][0][0]["uid"]

                    if idutils.is_orcid(orc):
                        passed += 1
                        passed_msg += vocab + ", "

                except:
                    pass
            else:
                if info[vocab] == "Not available":
                    total -= 1
                    not_available_msg += vocab + ", "

        points = passed / total * 100

        for voc in used_vocabularies:
            available_msg += voc + ", "

        msg = not_available_msg + "\n" + available_msg + "\n " + passed_msg

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
        terms_relations = kwargs["terms_relations"]
        terms_relations_list = terms_relations["list"]
        terms_relations_metadata = terms_relations["metadata"]

        relations_elements = terms_relations_metadata.loc[
            terms_relations_metadata["element"].isin(["contactPoints"]), "text_value"
        ]
        relations_list = relations_elements.values

        try:
            print(relations_list[0][0]["uid"])
            points = 100
            msg = "Your metadata has qualified references to other metadata"

        except:
            points = 0
            msg = "Your metadata does not have qualified references to other metadata"

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
        msg_list = []
        points = 0
        max_points = 100
        terms_license = kwargs["terms_license"]
        terms_license_list = terms_license["list"]
        terms_license_metadata = terms_license["metadata"]

        if not license_list:
            license_elements = terms_license_metadata.loc[
                terms_license_metadata["element"].isin(["license"]), "text_value"
            ]
            license_list = license_elements.values

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
        points = 0
        max_points = 100

        terms_license = kwargs["terms_license"]
        terms_license_list = terms_license["list"]
        terms_license_metadata = terms_license["metadata"]

        if not license_list:
            license_elements = terms_license_metadata.loc[
                terms_license_metadata["element"].isin(["license"]), "text_value"
            ]
            license_list = license_elements.values

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
            msg = "None of the license/s defined are standard according to SPDX license list"
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
        terms_license = kwargs["terms_license"]
        terms_license_metadata = terms_license["metadata"]

        license_elements = terms_license_metadata.loc[
            terms_license_metadata["element"].isin(["license"]), "text_value"
        ]
        license_list = license_elements.values

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
        points = 0
        msg = "No provenance or curation  data found"
        terms_provenance = kwargs["terms_provenance"]
        terms_provenance_list = terms_provenance["list"]
        terms_provenance_metadata = terms_provenance["metadata"]

        if terms_provenance_metadata.__class__ == tuple:
            return (0, terms_provenance_metadata)

        provenance_elements = terms_provenance_metadata.loc[
            terms_provenance_metadata["element"].isin(
                ["curationAndProvenanceObligations"]
            ),
            "text_value",
        ]
        provenance_list = provenance_elements.values
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
