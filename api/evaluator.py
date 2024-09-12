import ast
import gettext
import logging
import os
import sys
import urllib
import xml.etree.ElementTree as ET
from functools import wraps

import idutils
import pandas as pd
import requests

import api.utils as ut
from fair import load_config

logger = logging.getLogger("api.plugin.evaluation_steps")
logger_api = logging.getLogger("api.plugin")


class Evaluator(object):
    """A class used to define FAIR indicators tests. It contains all the references to all the tests

    ...

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

    oai_base : str
        Open Archives initiative , This is the place in which the API will ask for the metadata

    lang : Language
    """

    def __init__(self, item_id, oai_base=None, lang="en", plugin=None):
        self.item_id = item_id
        self.oai_base = oai_base
        self.metadata = None
        self.access_protocols = []
        self.cvs = []
        self.config = load_config(plugin=plugin)
        # configuration terms
        self.terms_access_metadata = pd.DataFrame()
        self.terms_license_metadata = pd.DataFrame()

        logger.debug("OAI_BASE IN evaluator: %s" % oai_base)
        if oai_base is not None and oai_base != "" and self.metadata is None:
            metadataFormats = ut.oai_metadataFormats(oai_base)
            dc_prefix = ""
            for e in metadataFormats:
                if metadataFormats[e] == "http://www.openarchives.org/OAI/2.0/oai_dc/":
                    dc_prefix = e
            logger.debug("DC_PREFIX: %s" % dc_prefix)

            try:
                id_type = idutils.detect_identifier_schemes(self.item_id)[0]
            except Exception as e:
                id_type = "internal"

            logger.debug("Trying to get metadata")
            try:
                item_metadata = ut.oai_get_metadata(
                    ut.oai_check_record_url(oai_base, dc_prefix, self.item_id)
                ).find(".//{http://www.openarchives.org/OAI/2.0/}metadata")
            except Exception as e:
                logger.error("Problem getting metadata: %s" % e)
                item_metadata = ET.fromstring("<metadata></metadata>")
            data = []
            for tags in item_metadata.findall(".//"):
                metadata_schema = tags.tag[0 : tags.tag.rfind("}") + 1]
                element = tags.tag[tags.tag.rfind("}") + 1 : len(tags.tag)]
                text_value = tags.text
                qualifier = None
                data.append([metadata_schema, element, text_value, qualifier])
            self.metadata = pd.DataFrame(
                data, columns=["metadata_schema", "element", "text_value", "qualifier"]
            )

        if self.metadata is not None:
            if len(self.metadata) > 0:
                self.access_protocols = ["http", "oai-pmh"]

        # Config attributes
        plugin = "oai-pmh"
        try:
            self.identifier_term = ast.literal_eval(
                self.config[plugin]["identifier_term"]
            )
            self.terms_quali_generic = ast.literal_eval(
                self.config[plugin]["terms_quali_generic"]
            )
            self.terms_quali_disciplinar = ast.literal_eval(
                self.config[plugin]["terms_quali_disciplinar"]
            )
            self.terms_access = ast.literal_eval(self.config[plugin]["terms_access"])
            self.terms_cv = ast.literal_eval(self.config[plugin]["terms_cv"])
            self.supported_data_formats = ast.literal_eval(
                self.config[plugin]["supported_data_formats"]
            )
            self.terms_qualified_references = ast.literal_eval(
                self.config[plugin]["terms_qualified_references"]
            )
            self.terms_relations = ast.literal_eval(
                self.config[plugin]["terms_relations"]
            )
            self.terms_license = ast.literal_eval(self.config[plugin]["terms_license"])
            self.metadata_quality = 100  # Value for metadata quality
            self.metadata_schemas = ast.literal_eval(
                self.config[plugin]["metadata_schemas"]
            )
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)

        # Translations
        self.lang = lang
        logger.debug("El idioma es: %s" % self.lang)
        logger.debug("METAdata: %s" % self.metadata)
        global _
        _ = self.translation()

    def metadata_values(self):
        raise NotImplementedError

    def translation(self):
        # Translations
        t = gettext.translation(
            "messages", "translations", fallback=True, languages=[self.lang]
        )
        _ = t.gettext
        return _

    # TESTS
    #    FINDABLE
    def rda_f1_01m(self):
        """Indicator RDA-F1-01M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the metadata is identified by a persistent identifier.
        A persistent identifier ensures that the metadata will remain findable over time, and reduces
        the risk of broken links.

        Technical proposal:Depending on the type od item_id, defined, it should check if it is any of
        the allowed Persistent Identifiers (DOI, PID) to identify digital objects.

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
            points, msg = self.identifiers_types_in_metadata(id_list)
        except Exception as e:
            logger.error(e)
        return (points, msg)

    def rda_f1_01d(self):
        """Indicator RDA-F1-01D
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the data is identified by a persistent identifier. A
        persistent identifier ensures that the data will remain findable over time, and reduces the
        risk of broken links.

        Technical proposal: If the repository/system where the digital object is stored has both data
        and metadata integrated, this method only need to call the previous one. Otherwise, it needs
        to be re-defined.

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
        points, msg = self.rda_f1_01m()
        return points, msg

    def rda_f1_02m(self):
        """Indicator RDA-F1-02M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.
        The indicator serves to evaluate whether the identifier of the metadata is globally unique,
        i.e. that there are no two identical identifiers that identify different metadata records.
        Technical proposal: It should check not only if the persistent identifier exists, but also
        if it can be resolved and if it is minted by any authorizated organization (e.g. DataCite)
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

    def rda_f1_02d(self):
        """Indicator RDA-F1-02D
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.
        The indicator serves to evaluate whether the identifier of the data is globally unique, i.e.
        that there are no two people that would use that same identifier for two different digital
        objects.
        Technical proposal:  If the repository/system where the digital object is stored has both data
        and metadata integrated, this method only need to call the previous one. Otherwise, it needs
        to be re-defined.
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
        return self.rda_f1_02m()

    def rda_f2_01m(self):
        """Indicator RDA-F2-01M
        This indicator is linked to the following principle: F2: Data are described with rich metadata.
        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.
        Technical proposal: Two different tests to evaluate generic and disciplinar metadata if needed.
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
        points_g, msg_g = self.rda_f2_01m_generic()
        points_d, msg_d = self.rda_f2_01m_disciplinar()
        points = (points_g + points_d) / 2
        self.metadata_quality = points  # Value for metadata quality

        return points, msg_g + " | " + msg_d

    def rda_f2_01m_generic(self):
        """Indicator RDA-F2-01M_GENERIC
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
        msg = _("Checking Dublin Core")

        md_term_list = pd.DataFrame(
            self.terms_quali_generic, columns=["term", "qualifier"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        points = (
            100
            * (len(md_term_list) - (len(md_term_list) - sum(md_term_list["found"])))
            / len(md_term_list)
        )
        if points == 100:
            msg = msg + _("... All mandatory terms included")
        else:
            msg = msg + _("... Missing terms:")
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg = msg + _(
                        "| term: %s, qualifier: %s" % (e["term"], e["qualifier"])
                    )

        return (points, msg)

    def rda_f2_01m_disciplinar(self):
        """Indicator RDA-F2-01M_DISCIPLINAR
        This indicator is linked to the following principle: F2: Data are described with rich metadata.
        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.
        Technical proposal: This test should be more complex
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
        msg = "Checking Dublin Core as multidisciplinar schema"
        md_term_list = pd.DataFrame(
            self.terms_quali_disciplinar, columns=["term", "qualifier"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        points = (
            100
            * (len(md_term_list) - (len(md_term_list) - sum(md_term_list["found"])))
            / len(md_term_list)
        )
        if points == 100:
            msg = msg + _("... All mandatory terms included")
        else:
            msg = msg + _("... Missing terms:")
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg = msg + _(
                        "| term: %s, qualifier: %s" % (e["term"], e["qualifier"])
                    )

        return (points, msg)

    def rda_f3_01m(self):
        """Indicator RDA-F3-01M
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
        msg = ""
        points = 0
        if len(self.identifier_term) > 1:
            id_term_list = pd.DataFrame(
                self.identifier_term, columns=["term", "qualifier"]
            )
        else:
            id_term_list = pd.DataFrame(self.identifier_term, columns=["term"])
        id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
        if len(id_list) > 0:
            if len(id_list[id_list.type.notnull()]) > 0:
                msg = _("Your data is identified with this identifier(s) and type(s): ")
                points = 100
                for i, e in id_list[id_list.type.notnull()].iterrows():
                    msg = msg + _("| %s: %s | " % (e.identifier, e.type))
            else:
                msg = _("Your data is identified by non-persistent identifiers: ")
                for i, e in id_list.iterrows():
                    msg = msg + "| %s: %s | " % (e.identifier, e.type)
        else:
            msg = _("Your data is not identified by persistent identifiers")

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
        Technical proposal: Check some standard harvester like OAI-PMH
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
        if len(self.metadata) > 0:
            points = 100
            msg = _("Your digital object is available via OAI-PMH harvesting protocol")
        else:
            points = 0
            msg = _(
                "Your digital object is not available via OAI-PMH. Please, contact to DIGITAL.CSIC admins"
            )

        return (points, msg)

    #  ACCESSIBLE
    def rda_a1_01m(self):
        """Indicator RDA-A1-01M
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
        msg = (
            "%s: "
            % _(
                "No access information can be found in the metadata. Please, add information to the following term(s): %s"
            )
            % self.terms_access
        )
        points = 0
        md_term_list = pd.DataFrame(self.terms_access, columns=["term", "qualifier"])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    msg = _(
                        "| Metadata: %s.%s: ... %s"
                        % (
                            elem["term"],
                            elem["qualifier"],
                            self.metadata.loc[
                                self.metadata["element"] == elem["term"]
                            ].loc[self.metadata["qualifier"] == elem["qualifier"]],
                        )
                    )
                    points = 100
        # 2 - Parse HTML in order to find the data file
        msg_2 = 0
        points_2 = 0
        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            msg_2, points_2, data_files = ut.find_dataset_file(
                self.metadata, item_id_http, self.supported_data_formats
            )
        except Exception as e:
            logger.error(e)
        if points_2 == 100 and points == 100:
            msg = _("%s \n Data can be accessed manually | %s" % (msg, msg_2))
        elif points_2 == 0 and points == 100:
            msg = _("%s \n Data can not be accessed manually | %s" % (msg, msg_2))
        elif points_2 == 100 and points == 0:
            msg = _("%s \n Data can be accessed manually | %s" % (msg, msg_2))
            points = 100
        elif points_2 == 0 and points == 0:
            msg = _(
                "No access information can be found in the metadata. Please, add information to the following term(s): %s"
                % self.terms_access
            )
        return (points, msg)

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
        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
        except Exception as e:
            logger.error(e)
            item_id_http = self.oai_base
        points, msg = ut.metadata_human_accessibility(self.metadata, item_id_http)

        return (points, msg)

    def rda_a1_02d(self):
        """Indicator RDA-A1-02D
        This indicator is linked to the following principle: A1: (Meta)data are retrievable
        by their identifier using a standardised communication protocol.
        The indicator refers to any human interactions that are needed if the requester
        wants to access the digital object. The FAIR principle refers mostly to
        automated interactions where a machine is able to access the digital object, but
        there may also be digital objects that require human interactions, such as
        clicking on a link on a landing page, sending an e-mail to the data owner, or
        even calling by telephone.
        The indicator can be evaluated by looking for information in the metadata that
        describes how access to the digital object can be obtained through human
        intervention.
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
        msg = (
            "%s: "
            % _(
                "No access information can be found in the metadata. Please, add information to the following term(s): %s"
            )
            % self.terms_access
        )
        points = 0

        md_term_list = pd.DataFrame(self.terms_access, columns=["term", "qualifier"])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    msg = _(
                        "| Metadata: %s.%s: ... %s"
                        % (
                            elem["term"],
                            elem["qualifier"],
                            self.metadata.loc[
                                self.metadata["element"] == elem["term"]
                            ].loc[self.metadata["qualifier"] == elem["qualifier"]],
                        )
                    )
                    points = 100

        return points, msg

    def rda_a1_03m(self):
        """Indicator RDA-A1-03M Metadata identifier resolves to a metadata record
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
        points = 0
        msg = "Metadata can not be found"
        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            points, msg = ut.metadata_human_accessibility(self.metadata, item_id_http)
            msg = _("%s \nMetadata found via Identifier" % msg)
        except Exception as e:
            logger.error(e)
        return (points, msg)

    def rda_a1_03d(self):
        """Indicator RDA-A1-01M
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
        msg = "Data can not be accessed"
        points = 0
        try:
            landing_url = urllib.parse.urlparse(self.oai_base).netloc
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            points, msg, data_files = ut.find_dataset_file(
                self.metadata, item_id_http, self.supported_data_formats
            )

            headers = []
            for f in data_files:
                try:
                    url = landing_url + f
                    if "http" not in url and "http:" in self.oai_base:
                        url = "http://" + url
                    elif "https:" not in url and "https:" in self.oai_base:
                        url = "https://" + url
                    res = requests.head(url, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                except Exception as e:
                    logger.error(e)
                try:
                    res = requests.head(f, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                except Exception as e:
                    logger.error(e)
            if len(headers) > 0:
                msg = msg + _("\n Files can be downloaded: %s" % headers)
                points = 100
            else:
                msg = msg + _("\n Files can not be downloaded")
                points = 0
        except Exception as e:
            logger.error(e)

        return points, msg

    def rda_a1_04m(self):
        """Indicator RDA-A1-01M
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
        msg = ""
        points = 0
        if len(self.access_protocols) > 0:
            msg = "%s %s" % (
                _("Metadata can be accessed through these protocols:"),
                self.access_protocols,
            )
            points = 100
        else:
            msg = _("No protocols found to access metadata")

        return (points, msg)

    def rda_a1_04d(self):
        """Indicator RDA-A1-01M
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
        points, msg = self.rda_a1_03d()
        if points == 100:
            msg = _("Files can be downloaded using HTTP-GET protocol")
        else:
            msg = _("No protocol for downloading data can be found")

        return (points, msg)

    def rda_a1_05d(self):
        """Indicator RDA-A1-01M
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
        msg = _("OAI-PMH does not support machine-actionable access to data")

        return points, msg

    def rda_a1_1_01m(self):
        """Indicator RDA-A1-01M
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
        points = 0
        msg = ""
        if len(self.access_protocols) > 0:
            points = 100
            msg = "%s %s" % (
                _("Metadata is accessible using these free protocols:"),
                self.access_protocols,
            )
        else:
            points = 0
            msg = _("Metadata can not be accessed via free protocols")
        return points, msg

    def rda_a1_1_01d(self):
        """Indicator RDA-A1-01M
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
        points, msg = self.rda_a1_03d()
        if points == 100:
            msg = _("Files can be downloaded using HTTP-GET FREE protocol")
        else:
            msg = _("No FREE protocol for downloading data can be found")

        return (points, msg)

    def rda_a1_2_01d(self):
        """Indicator RDA-A1-01M
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
        points = 0
        msg = _(
            "OAI-PMH is a open protocol without any Authorization or Authentication required"
        )
        return points, msg

    def rda_a2_01m(self):
        """Indicator RDA-A1-01M
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
        points = 50
        msg = _(
            "Preservation policy depends on the authority where this Digital Object is stored"
        )
        return points, msg

    # INTEROPERABLE

    def rda_i1_01m(self):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.
        The indicator serves to determine that an appropriate standard is used to express
        knowledge, for example, controlled vocabularies for subject classifications.
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
        msg = "%s: %s" % (_("Terms to check"), self.terms_cv)
        points = 0
        md_term_list = pd.DataFrame(self.terms_cv, columns=["term", "qualifier"])
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    tmp_md = self.metadata.loc[
                        self.metadata["element"] == elem["term"]
                    ].loc[self.metadata["qualifier"] == elem["qualifier"]]
                    for t_k, e_k in tmp_md.iterrows():
                        tmp_msg, cv = ut.check_controlled_vocabulary(e_k["text_value"])
                        if tmp_msg is not None:
                            msg = msg + "| %s: %s\n" % (
                                _("Found potential vocabulary"),
                                tmp_msg,
                            )
                            points = 100
                            self.cvs.append(cv)
        if points == 0:
            msg = _(
                "There is no standard used to express knowledge. Suggested controlled vocabularies: Library of Congress, Geonames, etc."
            )
        return (points, msg)

    def rda_i1_01d(self):
        """Indicator RDA-A1-01M
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
        msg = _("Test not implemented")

        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            points, msg, data_files = ut.find_dataset_file(
                self.item_id, item_id_http, self.supported_data_formats
            )
        except Exception as e:
            logger.error(e)

        return (points, msg)

    def rda_i1_02m(self):
        """Indicator RDA-A1-01M
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
        points = 0
        msg = ""
        try:
            if self.oai_base is not None:
                metadata_formats = ut.get_rdf_metadata_format(self.oai_base)
                rdf_metadata = None
                for e in metadata_formats:
                    url = ut.oai_check_record_url(self.oai_base, e, self.item_id)
                    rdf_metadata = ut.oai_get_metadata(url)
                    if rdf_metadata is not None:
                        points = 100
                        msg = msg + "\n%s %s" % (
                            _("Machine-actionable metadata format found:"),
                            e,
                        )
        except Exception as e:
            logger.debug(e)
        if points == 0:
            msg = _(
                "No machine-actionable metadata format found. If you are using OAI-PMH endpoint it should expose RDF schema"
            )

        return (points, msg)

    def rda_i1_02d(self):
        """Indicator RDA-A1-01M
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

    def rda_i2_01m(self):
        """Indicator RDA-A1-01M
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
        msg = ""
        if len(self.cvs) > 0:
            for e in self.cvs:
                pid = ut.controlled_vocabulary_pid(e)
                msg = msg + "\n%s %s %s: %s" % (
                    _("Controlled vocabulary"),
                    e,
                    _("has PID"),
                    pid,
                )
                points = 100
        else:
            msg = _(
                "No controlled vocabularies found. Suggested: ORCID, Library of Congress, Geonames, etc."
            )

        return (points, msg)

    def rda_i2_01d(self):
        """Indicator RDA-A1-01M
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
        """Indicator RDA-A1-01M
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
            if len(self.terms_qualified_references[0]) > 1:
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

    def rda_i3_01d(self):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        This indicator is about the way data is connected to other data, for example linking to
        previous or related research data that provides additional context to the data.
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

    def rda_i3_02m(self):
        """Indicator RDA-A1-01M
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
            if len(self.terms_relations[0]) > 1:
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

    def rda_i3_02d(self):
        """Indicator RDA-A1-01M
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
        return self.rda_i3_03m()

    def rda_i3_03m(self):
        """Indicator RDA-A1-01M
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
            if len(self.terms_relations[0]) > 1:
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

    def rda_i3_04m(self):
        """Indicator RDA-A1-01M
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
        return self.rda_i3_03m()

    # REUSABLE
    def rda_r1_01m(self):
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
        # Depending on the metadata schema used, checks that at least the mandatory terms are filled (75%)
        # and the number of terms are high (25%)
        msg = _("Checking Dublin Core as multidisciplinar schema")

        md_term_list = pd.DataFrame(
            self.terms_quali_disciplinar, columns=["term", "qualifier"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        points = (
            100
            * (len(md_term_list) - (len(md_term_list) - sum(md_term_list["found"])))
            / len(md_term_list)
        )
        if points == 100:
            msg = msg + _("... All mandatory terms included")
        else:
            msg = msg + _("... Missing terms:")
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg = msg + _(
                        "| term: %s, qualifier: %s" % (e["term"], e["qualifier"])
                    )

        return (points, msg)

    def rda_r1_1_01m(self):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.
        This indicator is about the information that is provided in the metadata related to the
        conditions (e.g. obligations, restrictions) under which data can be reused.
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
        md_term_list = pd.DataFrame(
            self.terms_license, columns=["term", "qualifier", "text_value"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    msg = msg + "| %s: %s.%s: %s" % (
                        _("License found"),
                        elem["term"],
                        elem["qualifier"],
                        elem["text_value"],
                    )
                    points = 100
        if points == 0:
            msg = "%s: %s" % (
                _(
                    "License information can not be found. Please, include the license in this term"
                ),
                self.terms_license,
            )
        return (points, msg)

    def rda_r1_1_02m(self):
        """Indicator RDA-A1-01M
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
        # Checks the presence of license information in metadata and if it is included in
        # the list https://spdx.org/licenses/licenses.json
        msg = ""
        points = 0

        md_term_list = pd.DataFrame(
            self.terms_license, columns=["term", "qualifier", "text_value"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    license_name = self.check_standard_license(elem["text_value"])
                    if license_name is not None:
                        msg = msg + _(
                            "| Standard license found: %s.%s: ... %s : %s"
                            % (
                                elem["term"],
                                elem["qualifier"],
                                license_name,
                                elem["text_value"],
                            )
                        )
                        points = 100
        if points == 0:
            msg = _(
                "License information can not be found. Please, include the license in this term: %s"
                % self.terms_license
            )
        return (points, msg)

    def rda_r1_1_03m(self):
        """Indicator RDA-A1-01M
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
        # Checks the presence of license information in metadata and if it uses an id from
        # the list https://spdx.org/licenses/licenses.json
        msg = _(
            "License information can not be found. Please, include the license in this term: %s"
            % self.terms_license
        )
        points = 0

        md_term_list = pd.DataFrame(
            self.terms_license, columns=["term", "qualifier", "text_value"]
        )
        md_term_list = ut.check_metadata_terms(self.metadata, md_term_list)
        if sum(md_term_list["found"]) > 0:
            for index, elem in md_term_list.iterrows():
                if elem["found"] == 1:
                    license_name = self.check_standard_license(elem["text_value"])
                    if license_name is not None:
                        msg = msg + _(
                            "| Machine-Actionable found: %s.%s: ... %s"
                            % (elem["term"], elem["qualifier"], elem["text_value"])
                        )
                        points = 100

        return (points, msg)

    def rda_r1_2_01m(self):
        """Indicator RDA-A1-01M
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
        points = 0
        msg = "Not implemented yet"
        return (points, msg)

    def rda_r1_2_02m(self):
        """Indicator RDA-A1-01M
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
        # rda_r1_2_01m
        return self.rda_r1_2_01m()

    def rda_r1_3_01m(self):
        """Indicator RDA-A1-01M
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
        msg = _(
            "Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact."
        )
        try:
            if self.oai_base is not None:
                metadata_formats = ut.get_rdf_metadata_format(self.oai_base)
                if "oai_dc" in metadata_formats or "dc" in metadata_formats:
                    points = 100
                    msg = "Dublin Core found as metadata schema"
            if self.metadata_schemas is not None:
                for e in self.metadata.metadata_schema.unique():
                    for s in self.metadata_schemas:  # Check Dublin Core
                        if "{" in e[0]:
                            e = e.partition("{")[-1]
                        if "}" in e[-1]:
                            e = e.partition("}")[0]
                        logger.debug("Checking: %s" % e)
                        logger.debug("Trying: %s" % self.metadata_schemas[s])
                        if e == self.metadata_schemas[s]:
                            if ut.check_url(e):
                                points = 100
                                msg = _("Community schema found: %s" % e)
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logger.error(e)

        return (points, msg)

    def rda_r1_3_01d(self):
        """Indicator RDA-A1-01M
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
        # Check data format is OK for a multi-domain repo
        return self.rda_i1_01d()

    def rda_r1_3_02m(self):
        """Indicator RDA-A1-01M
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
            "Currently, this tool does not include community-bsed schemas. If you need to include yours, please contact."
        )
        try:
            headers = {"Accept": "application/xml"}  # Type of response accpeted
            loc = "https://dublincore.org/schemas/xmls/qdc/2008/02/11/dc.xsd"
            r = requests.get(loc, headers=headers)  # GET with headers
            xmlTree = ET.fromstring(r.text)
            points = 100
            msg = "%s: %s" % (_("Dublin Core defined in XML"), loc)
        except Exception as err:
            logger.error("Error: %s" % err)

        return (points, msg)

    def rda_r1_3_02d(self):
        """Indicator RDA-A1-01M
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
        # Difficult for data
        # TEMP
        return self.rda_i1_01d()

    # Technical tests
    def identifiers_types_in_metadata(self, id_list, delete_url_type=False):
        if delete_url_type:
            return self.persistent_id_types_in_metadata(id_list)
        else:
            msg = ""
            points = 0

            if len(id_list) > 0:
                if len(id_list[id_list.type.notnull()]) > 0:
                    msg = _(
                        "Your (meta)data is identified with this identifier(s) and type(s): "
                    )
                    points = 100

                    for i, e in id_list[id_list.type.notnull()].iterrows():
                        msg = msg + "| ID: %s - %s: %s | " % (
                            e.identifier,
                            _("Type(s)"),
                            e.type,
                        )
                else:
                    msg = _(
                        "Your (meta)data is identified by non-persistent identifiers: "
                    )
                    for i, e in id_list:
                        msg = msg + "| ID: %s - %s: %s | " % (
                            e.identifier,
                            _("Type(s)"),
                            e.type,
                        )
            else:
                msg = _("Your (meta)data is not identified by persistent identifiers:")
            return (points, msg)

    def persistent_id_types_in_metadata(self, id_list):
        msg = ""
        points = 0
        if len(self.identifier_term) > 1:
            id_term_list = pd.DataFrame(
                self.identifier_term, columns=["term", "qualifier"]
            )
        else:
            id_term_list = pd.DataFrame(self.identifier_term, columns=["term"])
        id_list = ut.find_ids_in_metadata(self.metadata, id_term_list)
        if len(id_list) > 0:
            if len(id_list[id_list.type.notnull()]) > 0:
                for i, e in id_list[id_list.type.notnull()].iterrows():
                    if "url" in e.type:
                        e.type.remove("url")
                        if len(e.type) > 0:
                            msg = _(
                                "Your (meta)data is identified with this identifier(s) and type(s): "
                            )
                            points = 100
                            msg = msg + "| %s: %s | " % (e.identifier, e.type)
                        else:
                            msg = _(
                                "Your (meta)data is identified only by URL identifiers:| %s: %s | "
                                % (e.identifier, e.type)
                            )
                    elif len(e.type) > 0:
                        msg = _(
                            "Your (meta)data is identified with this identifier(s) and type(s): "
                        )
                        points = 100
                        msg = msg + _("| %s: %s | " % (e.identifier, e.type))
            else:
                msg = "Your (meta)data is identified by non-persistent identifiers: "
                for i, e in id_list:
                    msg = msg + _("| %s: %s | " % (e.identifier, e.type))
        else:
            msg = (
                "Your (meta)data is not identified by persistent & unique identifiers:"
            )

        return (points, msg)

    def check_standard_license(self, license_id_or_url):
        license_name = None
        standard_licenses = dict(ut.licenses_list())
        if license_id_or_url in standard_licenses.keys():
            license_name = license_id_or_url
            logger.debug(
                "Found standard license in SPDX license list, matched by name: %s"
                % license_name
            )
        else:
            for _id, _url_list in standard_licenses.items():
                for _url in _url_list:
                    if (
                        _url.find(license_id_or_url) == 0
                    ):  # use find() since it could be a substring
                        license_name = _url
                        logger.debug(
                            "Found standard license in SPDX license list, matched by URL: %s"
                            % _url
                        )
        return license_name


class ConfigTerms(property):
    """Class that simplifies and standarizes the management of the given metadata
    elements and its values by generic plugins. It is expected to be called as a
    decorator of the Plugin's method that implements the evaluation of a RDA indicator,
    e.g.:

    @ConfigTerms(term_id="identifier_term_data")
    def rda_f1_02d(self, **kwargs):
        ...

    which will add the results to the 'kwargs' dictionary (see Outputs below).

    This class decorator features a 3-level of processing of each metadata element and its corresponding values:
        1) Harmonization of metadata elements: which maps the Plugin's metadata element to a common FAIR-EVA's internal element name. It relies on the definition of the 'terms_map' configuration parameter within the plugin's config.ini file.
        2) Homogenization of the metadata values: resulting in a common format and type in order to facilitate further processing.
        3) Validation of the metadata values: with respect to well-known, standarized vocabularies.

    Input parameters:
        - 'term_id' (required, str): shall correspond to the name of the configuration parameter (within plugin's config.ini) containing the metadata terms.
        - 'validate' (optional, boolean): triggers the validation of the gathered metadata values for each of those metadata terms.

    Outputs:
        - Returned values are different according to the value of 'validate' input:
            + If disabled (validate=False), the class decorator returns a dictionary of:
                {
                    <metadata_element_1>: [<metadata_value_1>, ..]
                }
            + If enabled (validate=True), the class decorator adds the validation info as:
                {
                    <metadata_element_1>: {
                        'values': [<metadata_value_1>, ..],
                        'validation': {
                            <vocabulary_1>: {
                                'valid': [<metadata_value_1>, ..],
                                'non_valid': [<metadata_value_1>, ..],
                            }
                        }
                    }
                }
        - Usually captured by the decorated method through the keyword arguments dict -> **kwargs.
    """

    def __init__(self, term_id, validate=False):
        self.term_id = term_id
        self.validate = validate

    def __call__(self, wrapped_func):
        @wraps(wrapped_func)
        def wrapper(plugin, **kwargs):
            metadata = plugin.metadata
            has_metadata = True

            term_list = ast.literal_eval(plugin.config[plugin.name][self.term_id])
            logger.debug(
                "List of metadata elements associated with the requested configuration term ID '%s': %s"
                % (self.term_id, term_list)
            )
            # Get values in config for the given term
            if not term_list:
                msg = (
                    "Metadata values are not defined in configuration for the term '%s'"
                    % self.term_id
                )
                has_metadata = False
            else:
                # Get metadata associated with the term ID
                term_metadata = pd.DataFrame(
                    term_list, columns=["element", "qualifier"]
                )
                term_metadata = ut.check_metadata_terms_with_values(
                    metadata, term_metadata
                )
                if term_metadata.empty:
                    msg = (
                        "No access information can be found in the metadata for: %s. Please double-check the value/s provided for '%s' configuration parameter"
                        % (term_list, self.term_id)
                    )
                    has_metadata = False

            if not has_metadata:
                logger.warning(msg)
                return (0, msg)

            # Harmonization of metadata terms, homogenization of the data type of the metadata values & validation of those metadata values in accordance with CVs
            _msg = "Proceeding with stages of: 1) Harmonization of metadata terms, 2) Homogenization of data types of metadata values"
            if self.validate:
                _msg += " & 3) Validation of metadata values in accordance with existing CVs"
            logger_api.debug(_msg)
            for term_tuple in term_list:
                # 1. Get harmonized metadata term
                logger_api.debug(
                    "Get harmonized metadata term for the given term tuple: %s"
                    % term_tuple
                )
                term_key_plugin = term_tuple[0]
                logger_api.debug(
                    "Using term key '%s' to find harmonized metadata term"
                    % term_key_plugin
                )
                try:
                    term_key_harmonized = plugin.terms_map[term_key_plugin]
                except KeyError:
                    raise NotImplementedError(
                        "No mapping found for the metadata term '%s': cannot proceed with the harmonization of the metadata term"
                        % term_key_plugin
                    )
                else:
                    logger.debug(
                        "Harmonizing metadata term '%s' to '%s'"
                        % (term_key_plugin, term_key_harmonized)
                    )

                # 2. Homogenize the data format and type (list) of the metadata values
                term_values = term_metadata.loc[
                    term_metadata["element"] == term_key_plugin
                ].text_value.to_list()
                term_values_list = []
                if not term_values:
                    logger.warning(
                        "No values found in the metadata associated with element '%s'"
                        % term_key_harmonized
                    )
                    logger_api.warning(
                        "Not proceeding with metadata value homogenization and validation"
                    )
                else:
                    term_values = term_values[
                        0
                    ]  # NOTE: is it safe to take always the first element?
                    logger_api.warning(
                        "Considering only first element of the values returned: %s"
                        % term_values
                    )
                    logger.debug(
                        "Values found for metadata element '%s': %s"
                        % (term_key_harmonized, term_values)
                    )
                    # Homogeneise metadata values
                    logger_api.debug(
                        "Homogenizing format and type of the metadata value for the given (raw) metadata: %s"
                        % term_values
                    )
                    term_values_list = plugin.metadata_utils.gather(
                        term_values, element=term_key_harmonized
                    )
                    # Raise exception if the homogenization resulted in no values
                    if not term_values_list:
                        raise Exception(
                            "No values for metadata element '%s' resulted from the homogenization process"
                            % term_key_harmonized
                        )
                    else:
                        logger_api.debug(
                            "Homogenized values for the metadata element '%s': %s"
                            % (term_key_harmonized, term_values_list)
                        )

                # 3. Validate metadata values (if validate==True)
                if self.validate:
                    term_values_list_validated = {}
                    if term_values_list:
                        logger_api.debug(
                            "Validating values for '%s' metadata element: %s"
                            % (term_key_harmonized, term_values_list)
                        )
                        term_values_list_validated = plugin.metadata_utils.validate(
                            term_values_list, element=term_key_harmonized
                        )
                        if term_values_list_validated:
                            logger_api.debug(
                                "Validation results for metadata element '%s': %s"
                                % (term_key_harmonized, term_values_list_validated)
                            )
                        else:
                            logger_api.warning(
                                "Validation could not be done for metadata element '%s'"
                                % term_key_harmonized
                            )
                    # Update kwargs according to format:
                    #       <metadata_element_1>: {
                    #           'values': [<metadata_value_1>, ..],
                    #           'validation': {
                    #               <vocabulary_1>: {
                    #                   'valid': [<metadata_value_1>, ..],
                    #                   'non_valid': [<metadata_value_1>, ..],
                    #               }
                    #           }
                    #       }
                    kwargs.update(
                        {
                            term_key_harmonized: {
                                "values": term_values_list,
                                "validation": term_values_list_validated,
                            }
                        }
                    )
                else:
                    logger.debug(
                        "Not validating values from metadata element '%s'"
                        % term_key_harmonized
                    )
                    # Update kwargs according to format:
                    #       {
                    #           <metadata_element_1>: [<metadata_value_1>, ..]
                    #       }
                    kwargs.update({term_key_harmonized: term_values_list})

            logger.info(
                "Passing metadata elements and associated values to wrapped method '%s': %s"
                % (wrapped_func.__name__, kwargs)
            )

            return wrapped_func(plugin, **kwargs)

        return wrapper


class MetadataValuesBase(property):
    """Base class that provides the main methods for processing the metadata values:
    - gather(), which transforms metadata values to a common representation (data format and type).
    - validate(), which performs the validation of the metadata values across a series of vocabularies.

    Specific gathering (_get_* methods) and validation (_validate_* methods) can be defined. In particular case of the validation, these methods shall return a dictionary of the form:
        {
            <vocabulary_1>: {
                "valid": [<metadata_value_1>, ..],
                "non_valid": [<metadata_value_1>, ..]
            }
        }
    """

    @classmethod
    def gather(cls, element_values, element):
        """Gets the metadata value according to the given element.

        It calls the appropriate class method.
        """
        _values = []
        try:
            if element == "Metadata Identifier":
                _values = cls._get_identifiers_metadata(element_values)
            elif element == "Data Identifier":
                _values = cls._get_identifiers_data(element_values)
            elif element == "Temporal Coverage":
                _values = cls._get_temporal_coverage(element_values)
            elif element == "Person Identifier":
                _values = cls._get_person(element_values)
            elif element == "Format":
                _values = cls._get_formats(element_values)
            else:
                raise NotImplementedError("Self-invoking NotImplementedError exception")
        except NotImplementedError as e:
            logger_api.warning(
                "No specific gathering method for metadata element '%s'. Trying to return values according to object type."
                % element
            )
            _values = element_values
            if isinstance(element_values, str):
                _values = [element_values]
            logger_api.warning(
                "No specific plugin's gather method defined for metadata element '%s'. Returning input values formatted to list: %s"
                % (element, _values)
            )
        else:
            logger_api.debug(
                "Successful call to plugin's gather method for the metadata element '%s'. Returning: %s"
                % (element, _values)
            )
        finally:
            return _values

    @classmethod
    def validate(cls, element_values, element, **kwargs):
        """Validates the metadata values provided with respect to the supported
        controlled vocabularies.

        E.g. call:
        >>> MetadataValuesBase.validate(["http://orcid.org/0000-0003-4551-3339/Contact"], "Person Identifier")
        """
        from itertools import chain

        from fair import load_config

        # Get CVs
        main_config = load_config()
        controlled_vocabularies = ast.literal_eval(
            main_config["Generic"]["controlled_vocabularies"]
        )
        if not controlled_vocabularies:
            logger_api.error(
                "Controlled vocabularies not defined in the general configuration (config.ini)"
            )
        matching_vocabularies = controlled_vocabularies.get(element, {})
        if matching_vocabularies:
            logger_api.debug(
                "Found matching vocabulary/ies for element <%s>: %s"
                % (element, matching_vocabularies)
            )
        else:
            logger_api.warning(
                "No matching vocabulary found for element <%s>" % element
            )

        # Trigger validation
        if element == "Format":
            logger_api.debug(
                "Calling _validate_format() method for element: <%s>" % element
            )
            _result_data = cls._validate_format(
                cls, element_values, matching_vocabularies, **kwargs
            )
        elif element == "License":
            logger_api.debug(
                "Calling _validate_license() method for element: <%s>" % element
            )
            _result_data = cls._validate_license(
                cls, element_values, matching_vocabularies, **kwargs
            )
        else:
            logger_api.warning("Validation not implemented for element: <%s>" % element)
            _result_data = {}

        return _result_data

    @classmethod
    def _get_identifiers_metadata(cls, element_values):
        raise NotImplementedError

    @classmethod
    def _get_identifiers_data(cls, element_values):
        raise NotImplementedError

    @classmethod
    def _get_formats(cls, element_values):
        return NotImplementedError

    @classmethod
    def _get_licenses(cls, element_values):
        return NotImplementedError

    @classmethod
    def _get_temporal_coverage(cls, element_values):
        """Get start and end dates, when defined, that characterise the temporal
        coverage of the dataset.

        * Expected output:
         [
            {
                'start_date': <class 'datetime.datetime'>,
                'end_date': <class 'datetime.datetime'>,
            }
        ]
        """
        return NotImplementedError

    @classmethod
    def _validate_format(cls, element_values):
        return NotImplementedError

    @classmethod
    def _validate_license(cls, element_values):
        return NotImplementedError
