#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import idutils
import logging
import os
import urllib

# import urllib.request
from api.evaluator import Evaluator
from api.evaluator import ConfigTerms
from fair import load_config
import pandas as pd
import requests
import sys
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

    def __init__(self, item_id, oai_base=None, lang="en", config=None):
        logger.debug("Creating epos")
        plugin = "epos"
        super().__init__(item_id, oai_base, lang, plugin)
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
        self.identifier_term = ast.literal_eval(self.config[plugin]["identifier_term"])
        self.terms_quali_generic = ast.literal_eval(
            self.config[plugin]["terms_quali_generic"]
        )
        self.terms_quali_disciplinar = ast.literal_eval(
            self.config[plugin]["terms_quali_disciplinar"]
        )
        self.terms_access = ast.literal_eval(self.config[plugin]["terms_access"])
        self.terms_access_metadata = pd.DataFrame()
        self.terms_cv = ast.literal_eval(self.config[plugin]["terms_cv"])
        self.supported_data_formats = ast.literal_eval(
            self.config[plugin]["supported_data_formats"]
        )
        self.terms_qualified_references = ast.literal_eval(
            self.config[plugin]["terms_qualified_references"]
        )
        self.terms_relations = ast.literal_eval(self.config[plugin]["terms_relations"])
        self.terms_license = ast.literal_eval(self.config[plugin]["terms_license"])
        self.metadata_access_manual = ast.literal_eval(
            self.config[plugin]["metadata_access_manual"]
        )
        self.data_access_manual = ast.literal_eval(
            self.config[plugin]["data_access_manual"]
        )

        self.terms_access_protocols = ast.literal_eval(
            self.config[plugin]["terms_access_protocols"]
        )

    # TO REDEFINE - HOW YOU ACCESS METADATA?

    def get_metadata(self):
        # leave this here for a while until we make sure everthing works
        metadata_sample = []
        eml_schema = "epos"
        final_url = (
            "https://www.ics-c.epos-eu.org/api/v1/resources/details?id=" + self.item_id
        )
        response = requests.get(final_url, verify=False)
        dicion = response.json()
        for i in dicion.keys():
            if str(type(dicion[i])) == "<class 'dict'>":
                q = dicion[i]
                for j in q.keys():
                    metadata_sample.append([eml_schema, j, q[j], i])
            else:
                metadata_sample.append([eml_schema, i, dicion[i], None])

        return metadata_sample

    def rda_f1_01m(self):
        """Indicator RDA-F1-01M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the metadata is identified by a persistent identifier.
        A persistent identifier ensures that the metadata will remain findable over time, and reduces
        the risk of broken links.

        Technical assesment:
        -   100/100 if the identifier is a UUID or is accepted by ut-find_ids_in_metadata
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
        logger.debug("ID ChECKING: %s" % self.identifier_term)

        try:
            if len(self.identifier_term) > 1:
                id_term_list = pd.DataFrame(
                    self.identifier_term, columns=["term", "qualifier"]
                )
            else:
                id_term_list = pd.DataFrame(self.identifier_term, columns=["term"])

            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
            points, msg = ut.is_uuid(id_list.iloc[0, 0])
            if points == 0 and msg == "":
                points, msg = self.identifiers_types_in_metadata(id_list)
        except Exception as e:
            logger.error(e)

        return (points, msg)

    def rda_f3_01m(self):  # improve thist test with the wrapper for the ID
        id_term_list = pd.DataFrame(self.identifier_term, columns=["term"])
        id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
        points, msg = ut.is_uuid(id_list.iloc[0, 0])
        return (points, msg)

    def rda_f4_01m(self):
        """Indicator RDA-F4-01M
        This indicator is linked to the following principle: F4: (Meta)data are registered or indexed
        in a searchable resource. More information about that principle can be found here.
        The indicator tests whether the metadata is offered in such a way that it can be indexed.
        In some cases, metadata could be provided together with the data to a local institutional
        repository or to a domain-specific or regional portal, or metadata could be included in a
        landing page where it can be harvested by a search engine. The indicator remains broad
        enough on purpose not to  limit the way how and by whom the harvesting and indexing of
        the data might be done.

        Technical assesment:
        -    100/100 if the metadata is harvested by the tool


        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "Metadata could not be found"
        if not self.metadata.empty:
            points = 100
            msg = "Metadata Found"
        return (points, msg)

    @ConfigTerms(term="terms_access")
    def rda_a1_01m(self):
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

        # Check #1: presence of 'downloadURL' and 'DOI'
        _elements = ["downloadURL", "DOI"]
        data_access_elements = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"].isin(_elements)
        ]
        _indexes = data_access_elements.index.to_list()
        for _index in _indexes:
            points += 40
        _msg = "Found %s metadata elements for accessing the data: %s (points: %s)" % (
            len(_indexes),
            _elements,
            points,
        )
        logger.info(_msg)
        msg_list.append(_msg)

        # Check #2: presence of a license
        license_elements = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"].isin(["license"]), "text_value"
        ]
        license_list = license_elements.values
        if len(license_list) > 0:
            points += 10
            _msg = "Found a license for the data (points: 10)"
        else:
            _msg = "License not found for the data (points: 0)"
        logger.info(_msg)
        msg_list.append(_msg)

        # Check #2.1: open license listed in SPDX
        _points_license, _msg_license = self.rda_r1_1_02m(license_list=license_list)
        if _points_license == 100:
            points += 10
            _msg = "License listed in SPDX license list (points: 10)"
        else:
            _msg = "License not listed in SPDX license list (points: 0)"
        logger.info(_msg)
        msg_list.append(_msg)

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
        msg = "No link to the manual obtention of the metadata"
        if self.metadata_access_manual:
            if ut.check_link(self.metadata_access_manual[0]):
                msg = "The link to the manual obtention  of the metadata is " + str(
                    self.metadata_access_manual[0]
                )
                points = 100
        return (points, msg)

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
        msg = "No link to the manual obtention of the data"
        if self.data_access_manual:
            if ut.check_link(self.data_access_manual[0]):
                msg = "The link to the manual obtention  of the data is " + str(
                    self.data_access_manual[0]
                )
                points = 100
        return (points, msg)

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
        msg = "Metadata can not be found"
        if not self.metadata.empty:
            points = 100
            msg = "Metadata Found"
        return (points, msg)

    @ConfigTerms(term="terms_access")
    def rda_a1_03d(self):
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
        -    % of identifiers validated is the number points given out of a 100

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []

        doi = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"] == "DOI"
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
                msg_list.append(str(e))
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
                msg_list.append(" ".join(_msgs))
        remainder = _resolves_num % doi_items_num
        if remainder == 0:
            if _resolves_num > 0:
                points = 100
        else:
            points = round((_resolves_num * 100) / doi_items_num)

        return (points, msg_list)

    def rda_a1_04m(self):
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

        msg = "Metadata can not be found"

        parsed_endpoint = urllib.parse.urlparse(self.oai_base)
        protocol = parsed_endpoint.scheme
        if protocol in self.terms_access_protocols:
            points = 100
            msg = "The access protocol to the metadata is: " + str(protocol)

        return (points, msg)

    @ConfigTerms(term="terms_access")
    def rda_a1_04d(self):
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
        msg = "No protocol found"
        msg2 = "Your access protocols are: "

        _elements = [
            "downloadURL",
        ]
        data_access_elements = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"].isin(_elements)
        ]

        url = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"] == "downloadURL", "text_value"
        ]

        if len(url.values) == 0:
            return (points, "No download URL found")

        for i in url.values:
            parsed_endpoint = urllib.parse.urlparse(url.values)
            protocol = parsed_endpoint.scheme
            if protocol in self.terms_access_protocols:
                points = 100

                msg2 += str(protocol) + " "
        if points == 100:
            msg = msg2
        return (points, msg)

    @ConfigTerms(term="terms_access")
    def rda_a1_05d(self):
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
        msg = "No data access method was found in the metadata"
        msg2 = ""

        url = self.terms_access_metadata.loc[
            self.terms_access_metadata["element"] == "downloadURL", "text_value"
        ]

        url_list = url.values

        if len(url_list) > 0:
            msg = "Data acquisition could not be guaranteed "
            for link in url_list:
                if ut.check_link(link):
                    points = 100
                    msg2 += "Your download URL " + str(link) + " works. "

        if points == 100:
            msg = msg2
        return (points, msg)

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
        points, msg = self.rda_a1_04m()
        if points == 100:
            msg = msg + " which is free"
        return (points, msg)

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
        points, msg = self.rda_a1_04d()
        if points == 100:
            msg = msg + " which is free"
        return (points, msg)

    def rda_i1_02d(self):
        """Indicator RDA-I1-02d
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

    def rda_i1_02m(self):
        """Indicator RDA-I1-02M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here."""
        points = 0
        msg = ""
        return (points, msg)

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
        return (points, msg)

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
        msg = _(
            "No references found. Suggested terms to add: %s" % self.terms_relations
        )
        try:
            if len([self.terms_relations[0]]) > 1:
                id_term_list = pd.DataFrame(
                    self.terms_relations, columns=["term", "qualifier"]
                )
            else:
                id_term_list = pd.DataFrame(self.terms_relations, columns=["term"])
            id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
            if len(id_list) > 0:
                if len(id_list[id_list.type.notnull()]) > 0:
                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        if "url" in e.type:
                            e.type.remove("url")
                        if len(e.type) > 0:
                            msg = _("Your (meta)data reference this digital object: ")
                            points = 100
                            msg = msg + "| %s: %s | " % (e.identifier, e.type)
        except Exception as e:
            logger.error(e)
        return (points, msg)

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
        return (points, msg)

    def rda_r1_1_01m(self):
        return (0, "RDA-R1-1-01M not implemented for EPOS plugin")

    def rda_r1_1_03m(self):
        return (0, "RDA-R1-1-03M not implemented for EPOS plugin")

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

        return (points, msg)

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
        return (points, msg)

    def rda_r1_3_01d(self):
        """Indicator RDA_R1.3_01D

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
        return (points, msg)

    @ConfigTerms(term="terms_license")
    def rda_r1_1_02m(self, license_list=[]):
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
        msg_list = []
        points = 0
        max_points = 100

        if not license_list:
            license_elements = self.terms_license_metadata.loc[
                self.terms_license_metadata["element"].isin(["license"]), "text_value"
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
            _msg = (
                "License/s in use are considered as standard according to SPDX license list: %s"
                % license_standard_list
            )
        elif points > 0:
            _msg = (
                "A subset of the license/s in use (%s out of %s) are standard according to SDPX license list: %s"
                % (len(license_standard_list), license_num, license_standard_list)
            )
        else:
            _msg = "None of the license/s defined are standard according to SPDX license list"
        _msg = " ".join([_msg, "(points: %s)" % points])
        logger.info(_msg)
        msg_list.append(_msg)

        return (points, msg_list)


def check_CC_license(license):
    standard_licenses = ut.licenses_list()
    license_name = None
    for e in standard_licenses:
        if license in e[1] and e[0][0:2] == "CC":
            license_name = e[0]
    return license_name
