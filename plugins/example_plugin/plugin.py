#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import configparser
import logging
import os
from api.evaluator import Evaluator
import pandas as pd
import sys

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)

logger = logging.getLogger(os.path.basename(__file__))


class Example_Plugin(Evaluator):
    """A class used to define FAIR indicators tests. It contains all the references to all the tests. This is an example to be tailored to what your needs.

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an identifier from the repo)
    oai_base : str
        Open Archives initiative , This is the place in which the API will ask for the metadata
    lang : Language
    """

    def __init__(self, item_id, oai_base=None, lang="en"):
        super().__init__(item_id, oai_base, lang)
        # TO REDEFINE - WHICH IS YOUR PID TYPE?
        self.id_type = "internal"

        global _
        _ = super().translation()

        plugin = "example_plugin"
        config = configparser.ConfigParser()
        config_file = "%s/plugins/%s/config.ini" % (os.getcwd(), plugin)
        if "CONFIG_FILE" in os.environ:
            config_file = os.getenv("CONFIG_FILE")
        config.read(config_file)
        logger.debug("CONFIG LOADED")

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

        self.identifier_term = ast.literal_eval(config[plugin]["identifier_term"])
        self.terms_quali_generic = ast.literal_eval(
            config[plugin]["terms_quali_generic"]
        )
        self.terms_quali_disciplinar = ast.literal_eval(
            config[plugin]["terms_quali_disciplinar"]
        )
        self.terms_access = ast.literal_eval(config[plugin]["terms_access"])
        self.terms_cv = ast.literal_eval(config[plugin]["terms_cv"])
        self.supported_data_formats = ast.literal_eval(
            config[plugin]["supported_data_formats"]
        )
        self.terms_qualified_references = ast.literal_eval(
            config[plugin]["terms_qualified_references"]
        )
        self.terms_relations = ast.literal_eval(config[plugin]["terms_relations"])
        self.terms_license = ast.literal_eval(config[plugin]["terms_license"])
        self.metadata_schemas = ast.literal_eval(config[plugin]["metadata_schemas"])
        self.metadata_quality = 100  # Value for metadata balancing

    # TO REDEFINE - HOW YOU ACCESS METADATA?
    def get_metadata(self):
        metadata_sample = [
            ["{http://purl.org/dc/elements/1.1/}", "title", "MyTitle", None],
            ["{http://purl.org/dc/elements/1.1/}", "creator", "TheCreator", None],
            ["{http://purl.org/dc/elements/1.1/}", "identifier", "none", None],
            [
                "{http://purl.org/dc/elements/1.1/}",
                "rigths",
                "https://creativecommons.org/licenses/by/4.0/",
                None,
            ],
            [
                "{http://purl.org/dc/elements/1.1/}",
                "description",
                "This is the description",
                None,
            ],
            ["{http://purl.org/dc/elements/1.1/}", "date", "2019-12-12", None],
            [
                "{http://purl.org/dc/elements/1.1/}",
                "publisher",
                "Thematic Service",
                None,
            ],
        ]
        return metadata_sample

    def rda_a1_01m(self):
        # IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = "Data is not accessible"
        return (points, msg)

    def rda_a1_02m(self):
        # IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = "Data is not accessible"
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
