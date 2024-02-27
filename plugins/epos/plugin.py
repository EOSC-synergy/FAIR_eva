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

        self.metadata_standard = ast.literal_eval(
            self.config[self.name]["metadata_standard"]
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

    def get_metadata(self):
        metadata_sample = []
        eml_schema = "epos"
        final_url = self.oai_base + "/resources/details?id=" + self.item_id
        error_in_metadata = False
        response = requests.get(final_url, verify=False)
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

        for i in dicion.keys():
            if str(type(dicion[i])) == "<class 'dict'>":
                q = dicion[i]
                for j in q.keys():
                    metadata_sample.append([eml_schema, j, q[j], i])
            else:
                metadata_sample.append([eml_schema, i, dicion[i], None])
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
        """Indicator RDA-F1-01M
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

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term_data")
    def rda_f1_01d(self, **kwargs):
        """Indicator RDA-F1-01D
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

        id_list = term_metadata.text_value.values[0]
        points, msg_list = self.eval_persistency(id_list, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)

    @ConfigTerms(term_id="identifier_term")
    def rda_f1_02m(self, **kwargs):
        """Indicator RDA-F1-02M
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
        """Indicator RDA-F1-02D
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
            Returns a value (out of 100) that reflects the amount of data identifiers that are globally unique.
        msg
            Message with the results or recommendations to improve this indicator
        """
        term_data = kwargs["identifier_term_data"]
        term_metadata = term_data["metadata"]

        id_list = term_metadata.text_value.values[0]
        points, msg_list = self.eval_uniqueness(id_list, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)

    @ConfigTerms(term_id="terms_findability_richness")
    def rda_f2_01m(self, **kwargs):
        """Indicator RDA-F2-01M
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
        """Indicator RDA-F3-01M
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
        """Indicator RDA-F4-01M
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
        """RDA indicator:  RDA-A1-01M

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        The indicator refers to the information that is necessary to allow the requester to gain access
        to the digital object. It is (i) about whether there are restrictions to access the data (i.e.
        access to the data may be open, restricted or closed), (ii) the actions to be taken by a
        person who is interested to access the data, in particular when the data has not been
        published on the Web and (iii) specifications that the resources are available through
        eduGAIN7 or through specialised solutions such as proposed for EPOS.

        Technical assessment:
        - 80/100 points if pointers for downloading the data are provided
        - 20/100 points if license information is provided (10 if license exists & 10 if open license)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []
        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        # Check #1: presence of 'downloadURL' and 'DOI'
        _elements = ["downloadURL", "DOI"]
        data_access_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(_elements)
        ]
        _indexes = data_access_elements.index.to_list()
        for _index in _indexes:
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
        """Indicator RDA-A1-02M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.
        The indicator refers to any human interactions that are needed if the requester wants to
        access metadata. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.

        Technical assesment:
        -   100/100 if the link to the manual aquisition of the  metadata is checked


        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
        """Indicator RDA-A1-02M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.
        The indicator refers to any human interactions that are needed if the requester wants to
        access metadata. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.

        Technical assesment:
        -   100/100 if the link to the manual aquisition of the  data is checked


        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
        """Indicator RDA-A1-03M Metadata identifier resolves to a metadata record
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.
        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.

        Technical assesment:
        -   100/100 if the metadata is found by the tool

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
        """Indicator RDA-A1-03d
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        This indicator is about the resolution of the identifier that identifies the digital object. The
        identifier assigned to the data should be associated with a formally defined
        retrieval/resolution mechanism that enables access to the digital object, or provides access
        instructions for access in the case of human-mediated access. The FAIR principle and this
        indicator do not say anything about the mutability or immutability of the digital object that
        is identified by the data identifier -- this is an aspect that should be governed by a
        persistence policy of the data provider.

        Technical assesment:
        -    100/100 if all object identifiers are resolvable 0 if none
        -    On any other case the resultant points will be proportional to the % of resovable identifiers

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        _msg_list = []
        terms_access = kwargs["terms_access"]
        terms_access_list = terms_access["list"]
        terms_access_metadata = terms_access["metadata"]

        _elements = ["downloadURL", "DOI"]
        data_access_elements = terms_access_metadata.loc[
            terms_access_metadata["element"].isin(_elements)
        ]
        _indexes = data_access_elements.index.to_list()

        if _indexes == []:
            return (
                points,
                {
                    "message": "No DOI or way to access the data was found",
                    "points": points,
                },
            )

        doi = terms_access_metadata.loc[
            terms_access_metadata["element"] == "DOI"
        ].text_value.values[0]
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
        """Indicator RDA-A1-04M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        The indicator concerns the protocol through which the metadata is accessed and requires
        the protocol to be defined in a standard.

        Tecnical assesment:
        -   100/100 if the endpoint protocol is in the accepted protocols list

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
        """Indicator RDA-A1-04D
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        The indicator concerns the protocol through which the digital object is accessed and requires
        the protocol to be defined in a standard.

        Tecnical assesment:
        -   100/100 if the download protocol is in the accepted protocols list

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
                {
                    "message": "Could not check data access protocol: EPOS metadata element <downloadURL> not found",
                    "points": points,
                },
            )

        protocol_list = []
        for i in url.values:
            parsed_endpoint = urllib.parse.urlparse(url.values)
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
        """Indicator RDA-A1-05M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.
        The indicator refers to automated interactions between machines to access digital objects.
        The way machines interact and grant access to the digital object will be evaluated by the
        indicator.

        Tecnical assesment:
        -   100/100 if the downloadURL link is checked

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
                {
                    "message": "Could not check data access protocol: EPOS metadata element <downloadURL> not found",
                    "points": points,
                },
            )

        return (points, msg_list)

    def rda_a1_1_01m(self):
        """Indicator RDA-A1.1_01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.
        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Technical assesment:
        -   100/100 if the endpoint protocol is in the accepted protocols list

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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
        """Indicator RDA-A1-01D
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.
        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Technical assesment:
        -   100/100 if the downloadURL protocol is in the accepted protocols list

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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

    @ConfigTerms(term_id="terms_reusability_richness")
    def rda_i1_01d(self, **kwargs):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal,
        accessible, shared, and broadly applicable language for knowledge
        representation.
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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

    @ConfigTerms(term_id="terms_data_model")
    def rda_i1_02d(self, **kwargs):
        """Indicator RDA-I1-02d
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Technical proposal:

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
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

    def rda_i1_02m(self):
        """Indicator RDA-I1-02M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here."""
        points = 0

        return (
            points,
            [
                {
                    "message": "Test not implemented for EPOS ICS-C metadata catalog",
                    "points": points,
                }
            ],
        )

    def rda_i2_01d(self):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.
        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique
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
        """Indicator RDA-I3-01M
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

        points = 0
        msg = ""
        try:
            if len(self.terms_qualified_references) > 1:
                id_term_list = pd.DataFrame(
                    self.terms_qualified_references, columns=["term", "qualifier"]
                )
            else:
                id_term_list = pd.DataFrame(
                    self.terms_qualified_references, columns=["term"]
                )
            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)

            if len(id_list) > 0:
                if len(id_list[id_list.type.notnull()]) > 0:
                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        if "url" in e.type:
                            e.type.remove("url")
                            if "orcid" in e.type:
                                msg = _(
                                    "Your (meta)data is identified with this ORCID: "
                                )
                                points = 100
                                msg = msg + "| %s: %s | " % (e.identifier, e.type)
        except Exception as e:
            logger.error(e)
        if points == 0:
            msg = "%s: %s" % (
                _(
                    "No contributors found with persistent identifiers (ORCID). You should add some reference on the following element(s)"
                ),
                self.terms_qualified_references,
            )
        return (points, [{"message": msg, "points": points}])

    def rda_i3_01d(self):
        """Indicator RDA-I3-01D
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
        points = 0
        msg = "This test implies checking the presence of qualified references within the content of the data. As it is defined, its implementation is too costly."

        return (points, [{"message": msg, "points": points}])

    def rda_i3_02m(self):
        """Indicator RDA-I3-02M
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
        msg = "No references to other data."

        return (points, [{"message": msg, "points": points}])

    def rda_i3_02d(self):
        """Indicator RDA-I3-02D
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.
        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """

        points = 0
        msg = "This test implies checking the presence of qualified references within the content of the data. As it is defined, its implementation is too costly."

        return (points, [{"message": msg, "points": points}])

    def rda_i3_03m(self):
        """Indicator RDA-I3-03M
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
        msg = _(
            "No references found. Suggested terms to add: %s" % self.terms_relations
        )
        try:
            if len(self.terms_relations) > 1:
                id_term_list = pd.DataFrame(
                    self.terms_relations, columns=["term", "qualifier"]
                )
            else:
                id_term_list = pd.DataFrame(self.terms_relations, columns=["term"])

            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)

            if len(id_list) > 0:
                if len(id_list[id_list.type.notnull()]) > 0:
                    p
                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        if "url" in e.type:
                            e.type.remove("url")
                        if len(e.type) > 0:
                            msg = _("Your (meta)data reference this digital object: ")
                            points = 100
                            msg = msg + "| %s: %s | " % (e.identifier, e.type)
        except Exception as e:
            logger.error(e)

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_reusability_richness")
    def rda_r1_01m(self, **kwargs):
        """Indicator RDA-A1-01M
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
        points = 0

        terms_reusability_richness = kwargs["terms_reusability_richness"]
        terms_reusability_richness_list = terms_reusability_richness["list"]
        terms_reusability_richness_metadata = terms_reusability_richness["metadata"]

        reusability_element_list = []
        for element in terms_reusability_richness:
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
        points = len(reusability_element_list) / len(terms_reusability_richness) * 100

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_02m(self):
        """Indicator RDA-R1.3-02M
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
        msg = _(
            "Currently, this tool does not include community-based schemas. If you need to include yours, please contact."
        )

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_01m(self):
        """Indicator RDA-R1.3-01M
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
        msg = _(
            "Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact."
        )

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_01d(self):
        """Indicator RDA_R1.3_01D.

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
        msg = _(
            "Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact."
        )

        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_license")
    def rda_r1_1_01m(self, license_list=[], **kwargs):
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
    def rda_r1_1_02m(self, license_list=[], **kwargs):
        """Indicator R1.1-02M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.
        This indicator requires the reference to the conditions of reuse to be a standard licence,
        rather than a locally defined licence.
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
            _license_name = self.check_standard_license(_license)
            if _license_name:
                license_standard_list.append(_license_name)
                points += points_per_license
                logger.debug(
                    "License <%s> is considered as standard by SPDX: adding %s points"
                    % (_license_name, points_per_license)
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
        # Temporal until we get some machine readibility
        # The metadata received shoulgd look like
        """{
        "reference": "https://spdx.org/licenses/CC-BY-4.0.html",
        "isDeprecatedLicenseId": false,
        "detailsUrl": "https://spdx.org/licenses/CC-BY-4.0.json",
        "referenceNumber": 40,
        "name": "Creative Commons Attribution 4.0 International",
        "licenseId": "CC-BY-4.0",
        "seeAlso": [
          "https://creativecommons.org/licenses/by/4.0/legalcode"
        ],
        "isOsiApproved": false,
        "isFsfLibre": true
            }

          The interpreted format would look like pd.dataframe: {epos , reference ,"https://spdx.org/licenses/CC-BY-4.0.html", license-machine-readable}
        """
        points = 0
        msg = "Test not implemented for EPOS ICS-C metadata catalog"

        return (points, [{"message": msg, "points": points}])

    # Not tested with real data
    @ConfigTerms(term_id="terms_provenance")
    def rda_r1_2_01m(self, **kwargs):
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
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.
        This indicator requires that data complies with community standards.

        Returns
        --------
        Points
           100 If the metadata standard appears in Fairsharing

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
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.
        This indicator requires that data complies with community standards.

        Returns
        --------
        Points
           100 If the metadata standard appears in Fairsharing

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
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.
        This indicator requires that data complies with community standards.

        Returns
        --------
        Points
           100 If the metadata standard appears in Fairsharing it means that it has a machine understandable expresion

        """
        msg = "No metadata standard"
        points = 0

        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        points, msg = self.rda_r1_3_01m()
        if points == 100:
            msg = "Your metadata standard has a machine-understandable expression"

        return (points, [{"message": msg, "points": points}])

    def rda_r1_3_02d(self, **kwargs):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.
        This indicator requires that data complies with community standards.

        Returns
        --------
        Points
           100 If the metadata standard appears in Fairsharing it means that it has a machine understandable expresion

        """
        msg = "No data standard found"
        points = 0

        points, msg = self.rda_r1_3_01d()
        if points == 100:
            msg = "Your data standard has a machine-understandable expression"

        return (points, [{"message": msg, "points": points}])
