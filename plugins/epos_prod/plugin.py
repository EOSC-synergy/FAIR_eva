#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
import sys

from api.evaluator import ConfigTerms
from plugins.epos.plugin import Plugin as EPOSDevPlugin

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))


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
        identifiers = term_metadata.text_value.values[0]

        points, msg_list = self.eval_persistency(identifiers, data_or_metadata="data")
        logger.debug(msg_list)

        return (points, msg_list)
