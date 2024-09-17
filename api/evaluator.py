import ast
import csv
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

logger = logging.getLogger("api.plugin.evaluation_steps")
logger_api = logging.getLogger("api.plugin")


class ConfigTerms(property):
    def __init__(self, term_id):
        self.term_id = term_id

    def __call__(self, wrapped_func):
        @wraps(wrapped_func)
        def wrapper(plugin, **kwargs):
            metadata = plugin.metadata
            has_metadata = True

            term_list = ast.literal_eval(plugin.config[plugin.name][self.term_id])
            # Get values in config for the given term
            if not term_list:
                msg = (
                    "Cannot find any value for term <%s> in configuration"
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
                return (0, [{"message": msg, "points": 0}])

            # Update kwargs with collected metadata for the required terms
            kwargs.update(
                {self.term_id: {"list": term_list, "metadata": term_metadata}}
            )
            return wrapped_func(plugin, **kwargs)

        return wrapper


class ConfigTerms(property):
    def __init__(self, term_id):
        self.term_id = term_id

    def __call__(self, wrapped_func):
        @wraps(wrapped_func)
        def wrapper(plugin, **kwargs):
            metadata = plugin.metadata
            has_metadata = True

            term_list = ast.literal_eval(plugin.config[plugin.name][self.term_id])
            # Get values in config for the given term
            if not term_list:
                msg = (
                    "Cannot find any value for term <%s> in configuration"
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
                return (0, [{"message": msg, "points": 0}])

            # Update kwargs with collected metadata for the required terms
            kwargs.update(
                {self.term_id: {"list": term_list, "metadata": term_metadata}}
            )
            return wrapped_func(plugin, **kwargs)

        return wrapper


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

    def __init__(self, item_id, oai_base=None, lang="en", plugin=None, config=None):
        self.item_id = item_id
        self.oai_base = oai_base
        self.metadata = None
        self.access_protocols = []
        self.cvs = []
        self.config = config
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
        self.name = plugin
        if self.name == None:
            self.name = "oai-pmh"
        try:
            self.identifier_term = ast.literal_eval(
                self.config[self.name]["identifier_term"]
            )
            self.terms_quali_generic = ast.literal_eval(
                self.config[self.name]["terms_quali_generic"]
            )
            self.terms_quali_disciplinar = ast.literal_eval(
                self.config[self.name]["terms_quali_disciplinar"]
            )
            self.terms_access = ast.literal_eval(self.config[self.name]["terms_access"])
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
            self.terms_license = ast.literal_eval(
                self.config[self.name]["terms_license"]
            )
            self.metadata_quality = 100  # Value for metadata quality
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
            self.metadata_schemas = ast.literal_eval(
                self.config[self.name]["metadata_schemas"]
            )
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)

        # Translations
        self.lang = lang
        logger.debug("El idioma es: %s" % self.lang)
        logger.debug("METAdata: %s" % self.metadata)
        global _
        _ = self.translation()

    def translation(self):
        # Translations
        t = gettext.translation(
            "messages", "translations", fallback=True, languages=[self.lang]
        )
        _ = t.gettext
        return _

    def metadata_values(self):
        raise NotImplementedError

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
                points = 100
            else:
                _msg = "Identifier is not persistent for the %s: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = 0
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
                points = 100
            else:
                _msg = "Identifier found for the %s is not globally unique: %s" % (
                    data_or_metadata,
                    _id,
                )
                _points = 0
            msg_list.append({"message": _msg, "points": _points})

        return (points, msg_list)

    def eval_validated_basic(self, validation_payload):
        """Basic evaluation of validated metadata elements: scores according to the number of metadata elements using standard vocabularies over the total amount of metadata elements given as input.

        This method is useful for RDA methods that use ConfigTerms() decorator with 'validate=True'.

        :validation_payload: dictionary containing the validation results. Format as returned by ConfigTerms(validate=True)
        """
        # Loop over validated metadata elements
        elements_using_vocabulary = []
        for element, data in validation_payload.items():
            validation_data = data.get("validation", {})
            if not validation_data:
                _msg = (
                    "No validation data could be gathered for the metadata element '%s'"
                    % element
                )
                if data["values"]:
                    _msg += ": values present, but FAIR-EVA could not assert compliance with any vocabulary"
                else:
                    _msg += ": values not found in the metadata repository"
                logger_api.warning(_msg)
            else:
                # At least one value compliant with a CV is necessary
                vocabulary_in_use = []
                for vocabulary_id, validation_results in validation_data.items():
                    if len(validation_results["valid"]) > 0:
                        vocabulary_in_use.append(vocabulary_id)
                if vocabulary_in_use:
                    elements_using_vocabulary.append(element)
                    logger.info(
                        "Found standard vocabulary/ies in the values of metadata element '%s': %s"
                        % (element, vocabulary_in_use)
                    )
                else:
                    logger.warning(
                        "Could not find standard vocabulary/ies in the values of metadata element '%s'. Vocabularies being checked: %s"
                        % (element, validation_data.keys())
                    )
        # Compound message
        total_elements = len(validation_payload)
        total_elements_using_vocabulary = len(elements_using_vocabulary)
        _msg = (
            "Found %s (%s) out of %s (%s) metadata elements using standard vocabularies"
            % (
                total_elements_using_vocabulary,
                elements_using_vocabulary,
                total_elements,
                list(validation_payload),
            )
        )
        logger.info(_msg)

        # Get scores
        _points = 0
        if total_elements > 0:
            _points = total_elements_using_vocabulary / total_elements * 100

        return (_msg, _points)

    # TESTS
    #    FINDABLE
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
        id_list = term_metadata.text_value.values
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
        id_list = term_metadata.text_value.values
        points, msg_list = self.eval_uniqueness(id_list, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)

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
            Returns a value (out of 100) that reflects the grade of compliance with the generic and disciplinary metadata schemas.
        msg
            Message with the results or recommendations to improve this indicator.
        """
        points_g, msg_g = self.rda_f2_01m_generic()
        points_d, msg_d = self.rda_f2_01m_disciplinar()
        points = (points_g + points_d) / 2
        msg_list = []
        msg_list.append({"message": msg_g, "points": points_g})
        msg_list.append({"message": msg_d, "points": points_d})
        self.metadata_quality = points  # Value for metadata quality

        return points, msg_list

    @ConfigTerms(term_id="terms_quali_generic")
    def rda_f2_01m_generic(self, **kwargs):
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
        msg_list = []
        logging.debug(_("Checking Dublin Core"))

        term_data = kwargs["terms_quali_generic"]
        md_term_list = ut.check_metadata_terms(
            term_data["metadata"],
            pd.DataFrame(term_data["list"], columns=["term", "qualifier"]),
        )
        points = (
            100
            * (len(md_term_list) - (len(md_term_list) - sum(md_term_list["found"])))
            / len(md_term_list)
        )
        if points == 100:
            msg_list.append(_("All generic mandatory terms included"))
        else:
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg_list.append(
                        _(
                            "Not Found generic term: %s, qualifier: %s"
                            % (e["term"], e["qualifier"])
                        )
                    )

        return (points, msg_list)

    @ConfigTerms(term_id="terms_quali_disciplinar")
    def rda_f2_01m_disciplinar(self, **kwargs):
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

        msg_list = []
        logging.debug(_("Checking Dublin Core as multidisciplinar schema"))

        term_data = kwargs["terms_quali_disciplinar"]
        md_term_list = ut.check_metadata_terms(
            term_data["metadata"],
            pd.DataFrame(term_data["list"], columns=["term", "qualifier"]),
        )
        points = (
            100
            * (len(md_term_list) - (len(md_term_list) - sum(md_term_list["found"])))
            / len(md_term_list)
        )
        if points == 100:
            msg_list.append(_("All disciplinar mandatory terms included"))
        else:
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg_list.append(
                        _(
                            "Not Found disciplinar term: %s, qualifier: %s"
                            % (e["term"], e["qualifier"])
                        )
                    )

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
        msg_list = []
        points = 0
        term_data = kwargs["identifier_term_data"]
        term_metadata = term_data["metadata"]

        # ConfigTerms already enforces term_metadata not to be empty
        id_list = term_metadata.text_value.values[0]
        points = 100
        msg_list.append(
            {
                "message": _("Metadata includes identifier/s for the data:")
                + " %s" % id_list,
                "points": points,
            }
        )

        return (points, msg_list)

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
        msg_list = []
        if len(self.metadata) > 0:
            points = 100
            msg = _("Your digital object is available via OAI-PMH harvesting protocol")
        else:
            points = 0
            msg = _(
                "Your digital object is not available via OAI-PMH. Please, contact to repository admins"
            )
        msg_list.append({"message": msg, "points": points})

        return (points, msg_list)

    #  ACCESSIBLE
    @ConfigTerms(term_id="terms_access")
    def rda_a1_01m(self, **kwargs):
        """Indicator RDA-A1-01M.

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
            - 100 if access metadata is available and data can be access manually
            - 0 otherwise
        msg
            Message with the results or recommendations to improve this indicator
        """
        # 1 - Check metadata record for access info
        msg_list = []
        points = 0

        term_data = kwargs["terms_access"]
        term_metadata = term_data["metadata"]

        msg_st_list = []
        for index, row in term_metadata.iterrows():
            msg_st_list.append(
                _("Metadata found for access") + ": " + row["text_value"]
            )
            logging.debug(_("Metadata found for access") + ": " + row["text_value"])
            points = 100
        msg_list.append({"message": msg_st_list, "points": points})

        # 2 - Parse HTML in order to find the data file
        msg_2 = 0
        points_2 = 0
        try:
            logging.debug("Getting URL for ID: %s" % self.item_id)
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            logging.debug(
                "Trying to check dataset accessibility manually to: %s" % item_id_http
            )
            msg_2, points_2, data_files = ut.find_dataset_file(
                self.metadata, item_id_http, self.supported_data_formats
            )
        except Exception as e:
            logger.error(e)
        if points_2 == 100 and points == 100:
            msg_list.append(
                {
                    "message": _("Data can be accessed manually") + " | %s" % msg_2,
                    "points": points_2,
                }
            )
        elif points_2 == 0 and points == 100:
            msg_list.append(
                {
                    "message": _("Data can not be accessed manually") + " | %s" % msg_2,
                    "points": points_2,
                }
            )
        elif points_2 == 100 and points == 0:
            msg_list.append(
                {
                    "message": _("Data can be accessed manually") + " | %s" % msg_2,
                    "points": points_2,
                }
            )
            points = 100
        elif points_2 == 0 and points == 0:
            msg_list.append(
                {
                    "message": _(
                        "No access information can be found in the metadata. Please, add information to the following term(s)"
                    )
                    + " %s" % term_data,
                    "points": points_2,
                }
            )

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
        return (points, [{"message": msg, "points": points}])

    @ConfigTerms(term_id="terms_access")
    def rda_a1_02d(self, **kwargs):
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
        msg_list = []
        points = 0

        term_data = kwargs["terms_access"]
        term_metadata = term_data["metadata"]

        # ConfigTerms already enforces term_metadata not to be empty
        id_list = term_metadata.text_value.values[0]
        points = 100
        msg_list.append(
            {
                "message": _("Metadata includes data access information:")
                + " %s" % id_list,
                "points": points,
            }
        )

        if points == 0:
            msg_list.append(
                {
                    "message": _(
                        "No access information can be found in the metadata. Please, add information to the following term(s)"
                    )
                    + ": %s" % term_data,
                    "points": points,
                }
            )

        return (points, msg_list)

    def rda_a1_03m(self):
        """Indicator RDA-A1-03M Metadata identifier resolves to a metadata record.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.

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
        return (points, [{"message": msg, "points": points}])

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
        msg_list = []
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
            logger.debug(msg)

            headers = []
            headers_text = ""
            for f in data_files:
                try:
                    res = requests.head(url, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                        headers_text = headers_text + "%s ; " % f
                except Exception as e:
                    logger.error(e)
                try:
                    res = requests.head(f, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                        headers_text = headers_text + "%s ; " % f
                except Exception as e:
                    logger.error(e)
            if len(headers) > 0:
                points = 100
                msg_list.append(
                    {
                        "message": _("Data can be downloaded") + ": %s" % headers_text,
                        "points": points,
                    }
                )
            else:
                points = 0
                msg_list.append(
                    {"message": _("Data can not be downloaded"), "points": points}
                )

        except Exception as e:
            logger.error(e)

        return points, msg_list

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

    def rda_a1_04d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the digital object is accessed and requires
        the protocol to be defined in a standard.

        Returns
        -------
        points
            100/100 if the download protocol is in the accepted protocols list if data can be downloaded via http
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg_list = self.rda_a1_03d()
        msg_list = []
        if points == 100:
            msg_list.append(
                {
                    "message": _("Data can be downloaded using HTTP-GET protocol"),
                    "points": points,
                }
            )
        else:
            msg_list.append(
                {
                    "message": _("No protocol for downloading data can be found"),
                    "points": points,
                }
            )

        return (points, msg_list)

    def rda_a1_05d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to automated interactions between machines to access digital objects.
        The way machines interact and grant access to the digital object will be evaluated by the
        indicator.

        Returns
        -------
        points
            0 since OAI-PMF does not support machine actionable access to data
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []
        msg_list.append(
            {
                "message": _(
                    "OAI-PMH does not support machine-actionable access to data"
                ),
                "points": points,
            }
        )

        return points, msg_list

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
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.
        The indicator requires that the protocol can be used free of charge which facilitates
        unfettered access.
        Technical proposal:

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg_list = self.rda_a1_03d()
        msg_list = []
        if points == 100:
            msg_list.append(
                {
                    "message": _("Data can be downloaded using HTTP-GET FREE protocol"),
                    "points": points,
                }
            )
        else:
            msg_list.append(
                {
                    "message": _("No FREE protocol for downloading data can be found"),
                    "points": points,
                }
            )

        return (points, msg_list)

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
        points = 100
        msg_list = []
        msg_list.append(
            {
                "message": _(
                    "OAI-PMH is a open protocol without any Authorization or Authentication required"
                ),
                "points": points,
            }
        )
        return points, msg_list

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
        msg_list = []
        msg_list.append(
            {
                "message": _(
                    "Preservation policy depends on the authority where this Digital Object is stored"
                ),
                "points": points,
            }
        )
        return points, msg_list

    # INTEROPERABLE
    @ConfigTerms(term_id="terms_cv")
    def rda_i1_01m(self, **kwargs):
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
        msg_list = []
        points = 0

        term_data = kwargs["terms_cv"]
        term_metadata = term_data["metadata"]
        # ConfigTerms already enforces term_metadata not to be empty
        value_list = term_metadata.text_value.values
        points = 100
        logger.debug(
            _("Metadata includes data access information:") + " %s" % value_list
        )

        for index, e_k in term_metadata.iterrows():
            tmp_msg, cv = ut.check_controlled_vocabulary(e_k["text_value"])
            if tmp_msg is not None:
                points = 100
                msg_list.append(
                    {
                        "message": _("Found potential vocabulary") + ": %s" % tmp_msg,
                        "points": points,
                    }
                )
                self.cvs.append(cv)
        if points == 0:
            msg_list.append(
                {
                    "message": _(
                        "There is no standard used to express knowledge. Suggested controlled vocabularies: Library of Congress, Geonames, etc."
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

    def rda_i1_01d(self):
        """Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, in particular the data model and format.
        Technical proposal: Data format is within a list of accepted standards.


        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []
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
            internetMediaFormats.append(row[1])

        f.close()

        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            points, msg, data_files = ut.find_dataset_file(
                self.item_id, item_id_http, internetMediaFormats
            )
            for e in data_files:
                logger.debug(e)
            msg_list.append({"message": msg, "points": points})
            if points == 0:
                msg_list.append({"message": _("No files found"), "points": points})
        except Exception as e:
            logger.error(e)

        return (points, msg_list)

    def rda_i1_02m(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the metadata. This means
        that metadata should be readable and thus interoperable for machines without any
        requirements such as specific translators or mappings.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []
        try:
            if self.oai_base is not None:
                metadata_formats = ut.get_rdf_metadata_format(self.oai_base)
                rdf_metadata = None
                for e in metadata_formats:
                    url = ut.oai_check_record_url(self.oai_base, e, self.item_id)
                    rdf_metadata = ut.oai_get_metadata(url)
                    if rdf_metadata is not None:
                        points = 100
                        msg_list.append(
                            {
                                "message": _("Machine-actionable metadata format found")
                                + ": %s" % e,
                                "points": points,
                            }
                        )
        except Exception as e:
            logger.debug(e)
        if points == 0:
            msg_list.append(
                {
                    "message": _(
                        "No machine-actionable metadata format found. If you are using OAI-PMH endpoint it should expose RDF schema"
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

    def rda_i1_02d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_i1_02m()

    @ConfigTerms(term_id="terms_cv")
    def rda_i2_01m(self, **kwargs):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the vocabulary used for the metadata to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique and persistent
        identifiers. The documentation needs to be easily findable and accessible.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg_list = []

        if len(self.cvs) == 0:
            term_data = kwargs["terms_cv"]
            term_metadata = term_data["metadata"]

            for index, e_k in term_metadata.iterrows():
                tmp_msg, cv = ut.check_controlled_vocabulary(e_k["text_value"])
                if tmp_msg is not None:
                    logger.debug(_("Found potential vocabulary") + ": %s" % tmp_msg)
                    self.cvs.append(cv)

        if len(self.cvs) > 0:
            for e in self.cvs:
                pid = ut.controlled_vocabulary_pid(e)
                if pid is None:
                    pid = "Not found"
                points = 100
                msg_list.append(
                    {
                        "message": _("Controlled vocabulary")
                        + " "
                        + e
                        + " "
                        + _("has PID")
                        + " "
                        + pid,
                        "points": points,
                    }
                )

        else:
            msg_list.append(
                {
                    "message": _(
                        "No controlled vocabularies found. Suggested: ORCID, Library of Congress, Geonames, etc."
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

    def rda_i2_01d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        (points, msg_list) = self.rda_i2_01m()
        return (points, msg_list)

    @ConfigTerms(term_id="terms_qualified_references")
    def rda_i3_01m(self, **kwargs):
        """Indicator RDA-A1-01M.

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
        msg_list = []

        term_data = kwargs["terms_qualified_references"]
        term_metadata = term_data["metadata"]
        id_list = []
        for index, row in term_metadata.iterrows():
            logging.debug(self.item_id)

            if row["text_value"].split("/")[-1] not in self.item_id:
                id_list.append(row["text_value"])
        points, msg_list = self.eval_persistency(id_list)

    def rda_i3_01d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way data is connected to other data, for example linking to
        previous or related research data that provides additional context to the data.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_i3_02m()

    @ConfigTerms(term_id="terms_relations")
    def rda_i3_02m(self, **kwargs):
        """Indicator RDA-I3-02M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data, for example linking to
        previous or related research data that provides additional context to the data. Please note
        that this is not about the link from the metadata to the data it describes; that link is
        considered in principle F3 and in indicator RDA-F3-01M.

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        term_data = kwargs["terms_relations"]
        term_metadata = term_data["metadata"]
        id_list = []
        for index, row in term_metadata.iterrows():
            logging.debug(self.item_id)
            if row["text_value"].split("/")[-1] not in self.item_id:
                id_list.append(row["text_value"])

        points, msg_list = self.eval_persistency(id_list)
        return (points, msg_list)

    def rda_i3_02d(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        Description of the indicator RDA-I3-02D

        This indicator is about the way data is connected to other data. The references need to be
        qualified which means that the relationship role of the related resource is specified, for
        example that a particular link is a specification of a unit of m

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_i3_03m()

    def rda_i3_03m(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other metadata, for example to
        descriptions of related resources that provide additional context to the data. The references
        need to be qualified which means that the relation

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_i3_02m()

    def rda_i3_04m(self):
        """Indicator RDA-A1-01M.

        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data. The references need
        to be qualified which means that the relationship role of the related resource is specified,
        for example dataset X is derived from dataset Y.

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
        msg_list = []
        logger.debug(_("Checking Dublin Core as multidisciplinar schema"))

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
            msg_list.append(
                {"message": _("All mandatory terms included"), "points": points}
            )
        else:
            for i, e in md_term_list.iterrows():
                if e["found"] == 0:
                    msg_list.append(
                        {
                            "message": _("Missing term")
                            + ": %s, qualifier: %s" % (e["term"], e["qualifier"]),
                            "points": points,
                        }
                    )

        return (points, msg_list)

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

        license_list = terms_license_metadata.text_value.values

        license_num = len(license_list)
        if license_num > 0:
            points = 100

            if license_num > 1:
                for license in license_list:
                    msg_list.append(
                        {
                            "message": _("License found") + " : %s" % str(license),
                            "points": points,
                        }
                    )
            else:
                msg_list.append(
                    {
                        "message": _("The license is") + ": " + str(license_list[0]),
                        "points": points,
                    }
                )
        else:
            msg_list.append({"message": _("License not found"), "points": points})

        return (points, msg_list)

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

        terms_license = kwargs["terms_license"]
        terms_license_list = terms_license["list"]
        terms_license_metadata = terms_license["metadata"]

        if not license_list:
            license_list = terms_license_metadata.text_value.values

        license_num = len(license_list)
        license_standard_list = []

        for _license in license_list:
            logger.debug("Checking license: %s" % _license)
            if ut.is_spdx_license(_license, machine_readable=machine_readable):
                logger.debug("%s is in list" % _license)
                license_standard_list.append(_license)
                points = 100
                logger.debug(
                    "License <%s> is considered as standard by SPDX" % _license
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
    def rda_r1_1_03m(self, machine_readable=True, **kwargs):
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
        msg_list = []

        terms_license = kwargs["terms_license"]
        terms_license_metadata = terms_license["metadata"]

        license_elements = terms_license_metadata.loc[
            terms_license_metadata["element"].isin(["license"]), "text_value"
        ]
        license_list = license_elements.values

        _points_license, _msg_license = self.rda_r1_1_02m(
            license_list=license_list, machine_readable=machine_readable
        )
        if _points_license == 100:
            _msg = "License/s are machine readable according to SPDX"
        elif _points_license == 0:
            _msg = "License/s arenot machine readable according to SPDX"
        else:
            _msg = "A subset of the license/s are machine readable according to SPDX"
        logger.info(_msg)
        msg_list.append({"message": _msg, "points": _points_license})

        return (_points_license, [{"message": msg_list, "points": _points_license}])

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
        msg = [
            {
                "message": _("Not provenance information in Dublin Core"),
                "points": points,
            }
        ]
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
        msg_list = []
        points = 0

        if self.metadata_standard == []:
            return (points, [{"message": msg, "points": points}])

        points, msg = self.rda_r1_3_01m()
        msg_list.append(msg)
        if points == 100:
            msg_list.append(
                {
                    "message": _(
                        "The metadata standard in use is compliant with a machine-understandable community standard"
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

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
        msg_list = []
        points = 0

        points, msg = self.rda_r1_3_01d()
        msg_list.append(msg)
        if points == 100:
            msg_list.append(
                {
                    "message": _(
                        "Your data standard is expressed in compliance with a  machine-understandable community standard"
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

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
                    # Update kwargs according to the format:
                    #       <metadata_element_1>: {
                    #           'values': [<metadata_value_1>, ..],
                    #           'validation': {
                    #               <vocabulary_1>: {
                    #                   'valid': [<metadata_value_1>, ..],
                    #                   'non_valid': [<metadata_value_1>, ..],
                    #               }
                    #           }
                    #       }
                    _metadata_payload = {
                        "values": term_values_list,
                        "validation": term_values_list_validated,
                    }
                    logger.debug(
                        "Resulting metadata payload for element '%s': %s"
                        % (term_key_harmonized, _metadata_payload)
                    )
                    # Merge if the same harmonized metadata element points to multiple elements in the original metadata schema (see 'terms_map' config attribute)
                    if term_key_harmonized in list(kwargs):
                        _previous_payload = kwargs[term_key_harmonized]
                        logger.debug(
                            "Merge with previously collected metadata payload: %s"
                            % _previous_payload
                        )
                        _metadata_payload.update(_previous_payload)
                        logger.debug(
                            "Resulting metadata payload for element '%s' (after merging): %s"
                            % (term_key_harmonized, _metadata_payload)
                        )
                    # Update 'kwargs'
                    kwargs.update({term_key_harmonized: _metadata_payload})
                else:
                    logger.debug(
                        "Not validating values from metadata element '%s'"
                        % term_key_harmonized
                    )
                    # Merge if the same harmonized metadata element points to multiple elements in the original metadata schema (see 'terms_map' config attribute)
                    if term_key_harmonized in list(kwargs):
                        _previous_values_list = kwargs[term_key_harmonized]
                        logger.debug(
                            "Merge with previously collected metadata values: %s"
                            % _previous_values_list
                        )
                        term_values_list.extend(_previous_values_list)
                        logger.debug(
                            "Resulting metadata values for element '%s' (after merging): %s"
                            % (term_key_harmonized, term_values_list)
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
        except Exception as e:
            logger_api.exception(str(e))
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
