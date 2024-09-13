#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import logging
import os
import sys
import xml.etree.ElementTree as ET

import idutils
import pandas as pd
import requests
from bs4 import BeautifulSoup

from api.evaluator import Evaluator

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger("api.plugin")


class Plugin(Evaluator):
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

    def __init__(self, item_id, oai_base=None, lang="en", config=None):
        plugin = "signposting"
        super().__init__(item_id, oai_base, lang, plugin)
        # TO REDEFINE - WHICH IS YOUR PID TYPE?
        self.id_type = "internal"

        global _
        _ = super().translation()

        self.file_list = None

        (
            metadata_sample,
            self.file_list,
            self.identifier,
            self.license,
        ) = self.get_metadata()
        self.metadata = pd.DataFrame(
            metadata_sample,
            columns=["metadata_schema", "element", "text_value", "qualifier"],
        )

        logger.debug("METADATA: %s" % (self.metadata))
        # Protocol for (meta)data accessing
        if len(self.metadata) > 0:
            self.access_protocols = ["signposting"]

        self.identifier_term = ast.literal_eval(self.config[plugin]["identifier_term"])
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
        self.terms_relations = ast.literal_eval(self.config[plugin]["terms_relations"])
        self.terms_license = ast.literal_eval(self.config[plugin]["terms_license"])
        self.metadata_schemas = ast.literal_eval(
            self.config[plugin]["metadata_schemas"]
        )
        self.metadata_quality = 100  # Value for metadata balancing

    def get_metadata(self):
        def iterar_elementos_con_profundidad(
            elemento, metadata_sample, namespace=None, parent="", profundidad=0
        ):
            # Imprimir el elemento con su profundidad
            if profundidad > 1:
                print(
                    "%i" % profundidad
                    + "  " * profundidad
                    + parent
                    + "."
                    + str(elemento.tag).replace(namespace, "")
                )
                metadata_sample.append(
                    [
                        namespace,
                        parent,
                        elemento.text,
                        str(elemento.tag).replace(namespace, ""),
                    ]
                )
            else:
                print(
                    "%i" % profundidad
                    + "  " * profundidad
                    + str(elemento.tag).replace(namespace, "")
                )
                metadata_sample.append(
                    [
                        namespace,
                        str(elemento.tag).replace(namespace, ""),
                        elemento.text,
                        None,
                    ]
                )
            # Llamada recursiva para los elementos hijos
            for hijo in elemento:
                iterar_elementos_con_profundidad(
                    hijo,
                    metadata_sample,
                    namespace,
                    str(elemento.tag).replace(namespace, ""),
                    profundidad + 1,
                )
            return metadata_sample

        logging.debug("Trying to get metadata via Signposting")
        sp_url = self.item_id
        # You need a way to get your metadata in a similar format
        if idutils.is_doi(self.item_id):
            self.item_id = idutils.normalize_doi(self.item_id)
            sp_url = "https://doi.org/" + self.item_id
        elif idutils.is_handle(self.item_id):
            self.item_id = idutils.normalize_handle(self.item_id)
            sp_url = "http://hdl.handle.net/api/handles/" + self.item_id
        try:
            # Realizar la solicitud HTTP GET
            response = requests.get(sp_url)

            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                # Obtener la URL de dirección después de la redirección
                sp_url = response.url
            else:
                logger.debug(
                    f"Error al resolver el DOI. Código de estado: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Error: {e}")
        res = requests.head(sp_url)
        if res.status_code == 200:
            logging.debug(res.headers["Link"])
            signposting_md = requests.utils.parse_header_links(
                res.headers["Link"].rstrip(">").replace(">,<", ",<")
            )
        else:
            res = requests.get(url)
            if res.status_code == 200:
                content = BeautifulSoup(res.text, "html.parser")
                link_tags = content.find_all("link")

                signposting_md = []
                for link in link_tags:
                    # Obtener el valor del atributo 'href' de la etiqueta <link>, rel y type
                    href = link.get("href")
                    rel = link.get("rel")[0]
                    tipo = link.get("type")
                    signposting_md.append({"rel": rel, "type": tipo, "url": href})

        md_url = None
        file_list = []
        identifier = None
        license = None
        for item in signposting_md:
            if item["rel"] == "describedby":
                if item["type"] == "application/vnd.datacite.datacite+xml":
                    md_url = item["url"]
                    print(md_url)
            elif item["rel"] == "item":
                response = requests.head(item["url"])
                filename = requests.utils.parse_header_links(
                    response.headers["Content-Disposition"]
                )[0]["filename"]
                file_list.append(
                    (filename, filename.split(".")[-1], item["type"], item["url"])
                )
            elif item["rel"] == "cite-as":
                identifier = item["url"]
                logger.debug("Identifier found via Signposting: %s" % identifier)
            elif item["rel"] == "license":
                license = item["url"]
                logger.debug("License found via Signposting: %s" % license)
        if len(file_list) > 0:
            file_list = pd.DataFrame(
                file_list, columns=["name", "extension", "format", "link"]
            )
        else:
            file_list = None

        headers = {"Accept": "application/vnd.datacite.datacite+xml"}
        response = requests.get(md_url, verify=False, headers=headers)
        tree = ET.fromstring(response.text)
        xml_schema = "{http://datacite.org/schema/kernel-4}"
        metadata_sample = []
        metadata_sample = iterar_elementos_con_profundidad(
            tree, metadata_sample, xml_schema
        )
        return metadata_sample, file_list, identifier, license

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
        if self.identifier is not None:
            points = 100
            msg = "Identifier found via Signposting: %s" % self.identifier
        else:
            points, msg = super().rda_f1_01m(self)
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
            if self.identifier is not None:
                id_list = []
                id_list.append([self.identifier, None])
                id_list = pd.DataFrame(id_list, columns=["identifier", "type"])
                logger.debug("Checking identifier: %s" % id_list)
                points, msg = super().identifiers_types_in_metadata(id_list, True)
            else:
                points, msg = super().rda_f1_02m()
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
        msg = ""
        points = 0
        logger.debug("FILES: %s" % self.file_list)
        if self.file_list is None:
            return super().rda_a1_03d()
        elif "link" not in self.file_list:
            return super().rda_a1_03d()
        else:
            headers = []
            for f in self.file_list["link"]:
                try:
                    res = requests.head(f, verify=False, allow_redirects=True)
                    if res.status_code == 200:
                        headers.append(res.headers)
                except Exception as e:
                    logger.error(e)
            if len(headers) > 0:
                msg = msg + "%s: %s" % (
                    _("Files can be downloaded using HTTP-GET protocol"),
                    self.file_list["link"],
                )
                points = 100
            else:
                msg = msg + "\n%s" % _("Files can not be downloaded")
                points = 0
        return points, msg

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
        # TO REDEFINE
        points = 0
        msg = "No machine-actionable metadata format found. OAI-PMH endpoint may help"
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
        if self.license is not None:
            msg = "%s: %s" % (_("License found"), self.license)
            points = 100
        else:
            points, msg = super().rda_r1_1_01m()
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
        if self.license is not None:
            license_name = super().check_standard_license(self.license)
            if license_name is not None:
                msg = msg + _(
                    "| Standard license found: %s : %s" % (license_name, self.license)
                )
                points = 100
            else:
                msg = _("Provided license is not standard: %s" % self.license)
        else:
            points, msg = super().rda_r1_1_02m()
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
        msg = ""
        points = 0
        if self.license is not None:
            license_name = super().check_standard_license(self.license)
            if license_name is not None:
                msg = msg + _(
                    "| Machine-actionable license found: %s : %s"
                    % (license_name, self.license)
                )
                points = 100
            else:
                msg = _("Provided license is not Machine-actionable: %s" % self.license)
        else:
            points, msg = super().rda_r1_1_03m()
        return (points, msg)

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
        # TO REDEFINE
        points = 0
        msg = _(
            "Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact."
        )
        return (points, msg)

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
        return (points, msg)

    def data_01(self):
        points = 100
        msg = "This is a data test"
        return (points, msg)
