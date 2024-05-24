#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
import sys

from api.evaluator import ConfigTerms
from plugins.epos.plugin import MetadataValues as EPOSMetadataValues
from plugins.epos.plugin import Plugin as EPOSDevPlugin

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))


class MetadataValues(EPOSMetadataValues):
    # @staticmethod
    def _get_identifiers(self, element_values):
        """Get the list of identifiers for the data. Supports both EPOS production and
        development schemas.

        * Format EPOS PROD API:
            ["10.13127/tsunami/neamthm18"]
        """
        return element_values


class Plugin(EPOSDevPlugin):
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

    name = "epos_prod"


class EPOSDevMetadataValues(EPOSMetadataValues):
    @staticmethod
    def _get_identifiers(element_values):
        """Get the list of identifiers for the data. Supports both EPOS production and
        development schemas.

        * Format EPOS PROD API:
            ["10.13127/tsunami/neamthm18"]
        """
        return element_values
