#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import csv
import json
import logging
import os
import sys
import urllib
from functools import wraps

import idutils
import pandas as pd
import psycopg2
import requests
from bs4 import BeautifulSoup

import api.utils as ut
from api.evaluator import Evaluator

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger("api.plugin")


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


class Plugin(Evaluator):
    """A class used to define FAIR indicators tests. It is tailored towards the
    DigitalCSIC repository.

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

    oai_base : str
        Open Archives Initiative , This is the place in which the API will ask for the metadata. If you are working with  Digital CSIC http://digital.csic.es/dspace-oai/request

    lang : Language
    """

    def __init__(self, item_id, oai_base=None, lang="en", config=None):
        logger.debug("Call parent")
        plugin = "digital_csic"
        super().__init__(item_id, oai_base, lang, plugin)
        logger.debug("Parent called")
        if oai_base == "":
            self.oai_base = None
        if ut.get_doi_str(item_id) != "":
            self.item_id = ut.get_doi_str(item_id)
            self.id_type = "doi"
        elif ut.get_handle_str(item_id) != "":
            self.item_id = ut.get_handle_str(item_id)
            self.id_type = "handle"
        else:
            self.item_id = item_id
            self.id_type = "internal"
        oai_metadata = self.metadata
        self.metadata = None
        self.file_list = None

        if self.id_type == "doi" or self.id_type == "handle":
            api_endpoint = "https://digital.csic.es"
            api_metadata = None
            api_metadata, self.file_list = self.get_metadata_api(
                api_endpoint, self.item_id, self.id_type
            )
            if api_metadata is not None:
                if len(api_metadata) > 0:
                    logger.debug("A102: MEtadata from API OK")
                    self.access_protocols = ["http"]
                    self.metadata = api_metadata
                    temp_md = self.metadata.query("element == 'identifier'")
                    self.item_id = temp_md.query("qualifier == 'uri'")[
                        "text_value"
                    ].values[0]
            logger.info("API metadata: %s" % api_metadata)
        if api_metadata is None or len(api_metadata) == 0:
            logger.debug("Trying DB connect")
            try:
                self.connection = psycopg2.connect(
                    user=self.config["digital_csic"]["db_user"],
                    password=self.config["digital_csic"]["db_pass"],
                    host=self.config["digital_csic"]["db_host"],
                    port=self.config["digital_csic"]["db_port"],
                    database=self.config["digital_csic"]["db_db"],
                )
                logger.debug("DB configured")
            except Exception as error:
                logger.error("Error while fetching data from PostgreSQL ")
                logger.error(error)

            try:
                self.internal_id = self.get_internal_id(self.item_id, self.connection)
                if self.id_type == "doi":
                    self.handle_id = self.get_handle_id(
                        self.internal_id, self.connection
                    )
                elif self.id_type == "internal":
                    self.handle_id = self.get_handle_id(
                        self.internal_id, self.connection
                    )
                    self.item_id = self.handle_id

                logger.debug(
                    "INTERNAL ID: %i ITEM ID: %s" % (self.internal_id, self.item_id)
                )

                self.metadata = self.get_metadata_db()
                logger.debug("METADATA: %s" % (self.metadata.to_string()))
            except Exception as e:
                logger.error("Error connecting DB")
                logger.error(e)
        global _
        _ = super().translation()

        if self.metadata is None or len(self.metadata) == 0:
            raise Exception(_("Problem accessing data and metadata. Please, try again"))
            # self.metadata = oai_metadata
        logger.debug("Metadata is: %s" % self.metadata)

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
            if self.oai_base == None:
                self.oai_base = self.config[plugin]["oai_base"]
            self.terms_access = ast.literal_eval(self.config[plugin]["terms_access"])
            self.terms_access_protocols = ast.literal_eval(
                self.config[plugin]["terms_access_protocols"]
            )
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

            self.metadata_quality = 100  # Value for metadata balancing
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)

    def get_metadata_api(self, api_endpoint, item_pid, item_type):
        if item_type == "doi":
            md_key = "dc.identifier.doi"
            item_pid = idutils.to_url(item_pid, item_type, "https")
        elif item_type == "handle":
            md_key = "dc.identifier.uri"
            item_pid = ut.pid_to_url(item_pid, item_type)

        try:
            logger.debug("get_metadata_api IMPORTANT: %s" % item_pid)
            data = {"key": md_key, "value": item_pid}
            headers = {"accept": "application/json", "Content-Type": "application/json"}
            logger.debug("get_metadata_api to POST: %s" % data)
            url = api_endpoint + "/rest/items/find-by-metadata-field"
            logger.debug("get_metadata_api POST / %s" % url)
            MAX_RETRIES = 5
            for _ in range(MAX_RETRIES):
                r = requests.post(
                    url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                    timeout=15,
                )
                if r.status_code == 200:
                    break
            if len(r.text) == 2:
                data = {"key": md_key, "value": idutils.normalize_doi(item_pid)}
                for _ in range(MAX_RETRIES):
                    r = requests.post(
                        url,
                        data=json.dumps(data),
                        headers=headers,
                        verify=False,
                        timeout=15,
                    )
                    if r.status_code == 200:
                        break
            logger.debug("get_metadata_api ID FOUND: %s" % r.text)
            if r.status_code == 200:
                item_id = r.json()[0]["id"]
                url = api_endpoint + "/rest/items/%s/metadata" % item_id
                for _ in range(MAX_RETRIES):
                    r = requests.get(url, headers=headers, verify=False, timeout=15)
                    if r.status_code == 200:
                        break
            else:
                logger.error(
                    "get_metadata_api Request to URL: %s failed with STATUS: %i"
                    % (url, r.status_code)
                )
            md = []
            for e in r.json():
                split_term = e["key"].split(".")
                metadata_schema = self.metadata_prefix_to_uri(split_term[0])
                element = split_term[1]
                if len(split_term) > 2:
                    qualifier = split_term[2]
                else:
                    qualifier = ""
                text_value = e["value"]
                md.append([text_value, metadata_schema, element, qualifier])
            metadata = pd.DataFrame(
                md, columns=["text_value", "metadata_schema", "element", "qualifier"]
            )
            url = api_endpoint + "/rest/items/%s/bitstreams" % item_id
            logger.debug("get_metadata_api GET / %s" % url)
            for _ in range(MAX_RETRIES):
                r = requests.get(url, headers=headers, verify=False, timeout=15)
                if r.status_code == 200:
                    break
            file_list = []

            for e in r.json():
                file_list.append(
                    [
                        e["name"],
                        e["name"].split(".")[-1],
                        e["format"],
                        api_endpoint + e["link"],
                    ]
                )
            file_list = pd.DataFrame(
                file_list, columns=["name", "extension", "format", "link"]
            )
        except Exception as e:
            logger.error(
                "get_metadata_api Problem creating Metadata from API: %s when calling URL"
                % e
            )
            metadata = []
            file_list = []
        return metadata, file_list

    def get_metadata_db(self):
        query = (
            "SELECT metadatavalue.text_value, metadataschemaregistry.short_id, metadatafieldregistry.element,\
                metadatafieldregistry.qualifier FROM item, metadatavalue, metadataschemaregistry, metadatafieldregistry WHERE item.item_id = %s and \
    item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id \
    AND metadatafieldregistry.metadata_schema_id = metadataschemaregistry.metadata_schema_id AND resource_type_id = 2"
            % self.internal_id
        )
        cursor = self.connection.cursor()
        cursor.execute(query)
        metadata = pd.DataFrame(
            cursor.fetchall(),
            columns=["text_value", "metadata_schema", "element", "qualifier"],
        )
        for i in range(len(metadata["metadata_schema"])):
            metadata["metadata_schema"][i] = self.metadata_prefix_to_uri(
                metadata["metadata_schema"][i]
            )
        return metadata

        # TESTS

    # ACCESS
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
        item_id_http = idutils.to_url(
            self.item_id,
            idutils.detect_identifier_schemes(self.item_id)[0],
            url_scheme="http",
        )
        resp = requests.head(item_id_http, allow_redirects=False, verify=False)
        if resp.status_code == 302:
            item_id_http = resp.headers["Location"]
        resp = requests.head(item_id_http + "?mode=full", verify=False)
        if resp.status_code == 200:
            item_id_http = item_id_http + "?mode=full"

        msg_2, points_2, data_files = self.find_dataset_file(
            self.metadata, item_id_http, self.supported_data_formats
        )
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
        msg_list = []
        item_id_http = idutils.to_url(
            self.item_id,
            idutils.detect_identifier_schemes(self.item_id)[0],
            url_scheme="http",
        )
        resp = requests.head(item_id_http, allow_redirects=False, verify=False)
        if resp.status_code == 302 or resp.status_code == 301:
            item_id_http = resp.headers["Location"]
            resp = requests.get(item_id_http + "?mode=full", verify=False)
        item_id_http = resp.url
        if resp.status_code == 200:
            if "?mode=full" not in item_id_http:
                item_id_http = item_id_http + "?mode=full"
        logging.debug("URL TO VISIT: %s" % item_id_http)
        logging.debug("TEST A102M: Metadata %s" % self.metadata["metadata_schema"])
        for e in self.metadata["metadata_schema"]:
            logging.debug("TEST A102M: Metadata schemas %s" % e)
        metadata_dc = self.metadata[
            self.metadata["metadata_schema"] == self.metadata_schemas["dc"]
        ]
        logging.debug("TEST A102M: Metadata %s" % metadata_dc)
        for e in metadata_dc["metadata_schema"]:
            logging.debug(e)
        points, msg = ut.metadata_human_accessibility(metadata_dc, item_id_http)
        msg_list.append({"message": msg, "points": points})
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logging.error(e)
            msglist.append({"message": "%s | %s" % (msg, e), "points": points})
        return (points, msg_list)

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
        # 1 - Look for the metadata terms in HTML in order to know if they can be accessed manueally
        points = 0
        msg_list = []
        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            resp = requests.head(item_id_http, allow_redirects=False, verify=False)
            if resp.status_code == 302:
                item_id_http = resp.headers["Location"]
            resp = requests.head(item_id_http + "?mode=full", verify=False)
            if resp.status_code == 200:
                if "?mode=full" not in item_id_http:
                    item_id_http = item_id_http + "?mode=full"
            metadata_dc = self.metadata[
                self.metadata["metadata_schema"] == self.metadata_schemas["dc"]
            ]
            points, msg = ut.metadata_human_accessibility(metadata_dc, item_id_http)
            msg_list.append(
                {
                    "message": _("%s \nMetadata found via Identifier" % msg),
                    "points": points,
                }
            )
        except Exception as e:
            logger.error(e)
        try:
            points = (points * self.metadata_quality) / 100
            msg_list.append(
                {
                    "message": _("Total score after applying metadata quality factor")
                    + ": "
                    + points,
                    "points": points,
                }
            )
        except Exception as e:
            logger.error(e)
        if points == 0:
            msg_list.append(
                {"message": _("Metadata can not be found"), "points": points}
            )
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

    def rda_a1_03d(self):
        """Indicator RDA-A1-01M.

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
            points, msg, data_files = self.find_dataset_file(
                self.metadata, item_id_http, self.supported_data_formats
            )
            logger.debug(msg)

            headers = []
            headers_text = ""
            for f in data_files:
                try:
                    res = requests.head(
                        "https://digital.csic.es" + f,
                        verify=False,
                        allow_redirects=True,
                    )
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
        msg_list = []
        points = 0
        if self.file_list is None:
            return super().rda_a1_05d()
        else:
            try:
                protocol = "http"
                number_of_files = len(self.file_list["link"])
                accessible_files = 0
                accessible_files_list = []
                for f in self.file_list["link"]:
                    try:
                        res = requests.head(f, verify=False, allow_redirects=True)
                        if res.status_code == 200:
                            accessible_files += 1
                            accessible_files_list.append(f)
                    except Exception as e:
                        logging.error(e)
                if accessible_files == number_of_files:
                    points = 100
                    msg_list.append(
                        {
                            "message": _("Data is accessible automatically via HTTP:")
                            + accessible_files_list,
                            "points": points,
                        }
                    )
                elif accessible_files == 0:
                    points = 0
                    msg_list.append(
                        {
                            "message": _("Files are not accessible via HTTP"),
                            "points": points,
                        }
                    )
                else:
                    points = (accessible_files * 100) / number_of_files
                    msg_list.append(
                        {
                            "message": _(
                                "Some of digital objects are accessible automatically via HTTP:"
                            )
                            + accessible_files_list,
                            "points": points,
                        }
                    )
            except Exception as e:
                logging.debug(e)

        return points, msg_list

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
        msg = _(
            "DIGITAL.CSIC allow access management and authentication and authorisation from CSIC CAS"
        )

        return points, [{"message": msg, "points": points}]

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
        points = 100
        msg = _(
            "DIGITAL.CSIC preservation policy is available at: https://digital.csic.es/dc/politicas/#politica8"
        )
        return points, [{"message": msg, "points": points}]

        # INTEROPERABLE

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
        supported_data_formats = [
            ".tif",
            ".aig",
            ".asc",
            ".agr",
            ".grd",
            ".nc",
            ".hdf",
            ".hdf5",
            ".pdf",
            ".odf",
            ".doc",
            ".docx",
            ".csv",
            ".jpg",
            ".png",
            ".gif",
            ".mp4",
            ".xml",
            ".rdf",
            ".txt",
            ".mp3",
            ".wav",
            ".zip",
            ".rar",
            ".tar",
            ".tar.gz",
            ".jpeg",
            ".xls",
            ".xlsx",
        ]

        try:
            f = open(path)
            f.close()

        except:
            msg = "The config.ini internet media types file path does not arrive at any file. Try 'static/internetmediatipes190224.csv'"
            logger.error(msg)
            return (points, [{"message": msg, "points": points}])
        logger.debug("Trying to open accepted media formats")
        f = open(path)
        csv_reader = csv.reader(f)

        for row in csv_reader:
            internetMediaFormats.append(row[1])

        f.close()
        for e in supported_data_formats:
            internetMediaFormats.append(e)
        logger.debug("List: %s" % internetMediaFormats)

        try:
            item_id_http = idutils.to_url(
                self.item_id,
                idutils.detect_identifier_schemes(self.item_id)[0],
                url_scheme="http",
            )
            logger.debug("Searching for dataset files")
            points, msg, data_files = self.find_dataset_file(
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
        identifier_temp = self.item_id
        df = pd.DataFrame(self.metadata)

        # Hacer la selección donde la columna 'term' es igual a 'identifier' y 'qualifier' es igual a 'uri'
        selected_handle = df.loc[
            (df["element"] == "identifier") & (df["qualifier"] == "uri"), "text_value"
        ]
        self.item_id = ut.get_handle_str(selected_handle.iloc[0])
        points, msg_list = super().rda_i1_02m()
        try:
            points = (points * self.metadata_quality) / 100
            msg_list.append({"message": _("After applying weigh"), "points": points})
        except Exception as e:
            logging.error(e)
        self.item_id = identifier_temp
        return (points, msg_list)

    @ConfigTerms(term_id="terms_qualified_references")
    def rda_i3_01m(self, **kwargs):
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
        msg_list = []

        term_data = kwargs["terms_qualified_references"]
        term_metadata = term_data["metadata"]
        id_list = []
        try:
            for index, row in term_metadata.iterrows():
                if ut.check_standard_project_relation(row["text_value"]):
                    points = 100
                    msg_list.append(
                        {
                            "message": _("Qualified references to related object")
                            + ": "
                            + row["text_value"],
                            "points": points,
                        }
                    )
                elif ut.check_controlled_vocabulary(row["text_value"]):
                    points = 100
                    msg_list.append(
                        {
                            "message": _("Qualified references to related object")
                            + ": "
                            + row["text_value"],
                            "points": points,
                        }
                    )
        except Exception as e:
            logging.error("Error in I3_01M: %s" % e)
        return (points, msg_list)

    @ConfigTerms(term_id="terms_relations")
    def rda_i3_02m(self, **kwargs):
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
        msg_list = []

        term_data = kwargs["terms_relations"]
        term_metadata = term_data["metadata"]
        id_list = []
        try:
            for index, row in term_metadata.iterrows():
                if ut.check_standard_project_relation(row["text_value"]):
                    points = 100
                    msg_list.append(
                        {
                            "message": _("References to related object")
                            + ": "
                            + row["text_value"],
                            "points": points,
                        }
                    )
                elif ut.check_controlled_vocabulary(row["text_value"]):
                    points = 100
                    msg_list.append(
                        {
                            "message": _("References to related object")
                            + ": "
                            + row["text_value"],
                            "points": points,
                        }
                    )
                elif ut.get_orcid_str(row["text_value"]) != "":
                    if ut.check_orcid(row["text_value"]):
                        points = 100
                        msg_list.append(
                            {
                                "message": _("References to ORCID")
                                + ": "
                                + row["text_value"],
                                "points": points,
                            }
                        )

        except Exception as e:
            logger.error("Error in I3_02M: %s" % e)
        return (points, msg_list)

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
        return self.rda_i3_02m()

    def rda_i3_03m(self):
        """Indicator RDA-I3-03M
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
        return self.rda_i3_02m()

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
        return super().rda_r1_1_03m(machine_readable=False)

    @ConfigTerms(term_id="prov_terms")
    def rda_r1_2_01m(self, **kwargs):
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
        points = 0
        msg_list = []

        term_data = kwargs["prov_terms"]
        logger.debug(term_data)
        term_metadata = term_data["metadata"]
        logger.debug(term_metadata.element)
        id_list = []
        try:
            for index, row in term_metadata.iterrows():
                _points = 100
                msg_list.append(
                    {
                        "message": _("Provenance info found")
                        + ": %s" % (row["text_value"]),
                        "points": _points,
                    }
                )
            points = (
                100 * len(term_metadata[["element", "qualifier"]].drop_duplicates())
            ) / len(term_data["list"])

        except Exception as e:
            logger.error("Error in I3_02M: %s" % e)

        if points == 0:
            msg_list.append(
                {
                    "message": _(
                        "Provenance information can not be found. Please, include the info in config.ini"
                    ),
                    "points": points,
                }
            )
        return (points, msg_list)

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
        msg_list = []

        try:
            for e in self.metadata.metadata_schema.unique():
                logger.debug("Checking: %s" % e)
                logger.debug("Trying: %s" % self.metadata_schemas["dc"])
                if e == self.metadata_schemas["dc"]:  # Check Dublin Core
                    if ut.check_url(e):
                        points = 100
                        msg_list.append(
                            {
                                "message": _(
                                    "DIGITAL.CSIC supports qualified Dublin Core as well as other discipline agnostics schemes like DataCite. Terms found"
                                ),
                                "points": points,
                            }
                        )
        except Exception as e:
            logger.error("Problem loading plugin config: %s" % e)
        try:
            points = (points * self.metadata_quality) / 100
        except Exception as e:
            logger.error(e)
        if points == 0:
            msg_list.append(
                {
                    "message": _(
                        "Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact."
                    ),
                    "points": points,
                }
            )

        return (points, msg_list)

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
        points, msg_list = super().rda_r1_3_02m()
        try:
            points = (points * self.metadata_quality) / 100
            msg_list.append(
                {
                    "message": _("Total score after applying metadata quality factor")
                    + ": %f" % points,
                    "points": points,
                }
            )
        except Exception as e:
            logger.error(e)

        return (points, msg_list)

    # DIGITAL_CSIC UTILS
    def get_internal_id(self, item_id, connection):
        internal_id = item_id
        id_to_check = ut.get_doi_str(item_id)
        logger.debug("DOI is %s" % id_to_check)
        temp_str = "%" + item_id + "%"
        if len(id_to_check) != 0:
            if ut.check_doi(id_to_check):
                query = (
                    "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'"
                    % temp_str
                )
                logger.debug(query)
                cursor = connection.cursor()
                cursor.execute(query)
                list_id = cursor.fetchall()
                if len(list_id) > 0:
                    for row in list_id:
                        internal_id = row[0]

        if internal_id == item_id:
            id_to_check = ut.get_handle_str(item_id)
            logger.debug("PID is %s" % id_to_check)
            temp_str = "%" + item_id + "%"
            query = (
                "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'"
                % temp_str
            )
            logger.debug(query)
            cursor = connection.cursor()
            cursor.execute(query)
            list_id = cursor.fetchall()
            if len(list_id) > 0:
                for row in list_id:
                    internal_id = row[0]

        return internal_id

    def get_handle_id(self, internal_id, connection):
        query = (
            "SELECT metadatavalue.text_value FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s AND item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatafieldregistry.qualifier = 'uri'"
            % internal_id
        )
        cursor = connection.cursor()
        cursor.execute(query)
        list_id = cursor.fetchall()
        handle_id = ""
        if len(list_id) > 0:
            for row in list_id:
                handle_id = row[0]

        return ut.get_handle_str(handle_id)

    def metadata_prefix_to_uri(self, prefix):
        uri = prefix
        try:
            logging.debug("TEST A102M: we have this prefix: %s" % prefix)
            metadata_schemas = ast.literal_eval(
                self.config[self.name]["metadata_schemas"]
            )
            if prefix in metadata_schemas:
                uri = metadata_schemas[prefix]
        except Exception as e:
            logger.error("TEST A102M: Problem loading plugin config: %s" % e)
        return uri

    def find_dataset_file(self, metadata, url, data_formats):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        }
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, features="html.parser")

        msg = "No dataset files found"
        points = 0

        data_files = []
        for tag in soup.find_all("a"):
            for f in data_formats:
                try:
                    if f in tag.get("href") or f in tag.text:
                        data_files.append(tag.get("href"))
                except Exception as e:
                    pass

        if len(data_files) > 0:
            self.data_files = data_files
            points = 100
            msg = "Potential datasets files found: %s" % data_files

        return points, msg, data_files
