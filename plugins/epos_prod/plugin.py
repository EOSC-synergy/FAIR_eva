#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
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
    @classmethod
    def _get_identifiers_metadata(cls, element_values):
        raise NotImplementedError

    @classmethod
    def _get_identifiers_data(cls, element_values):
        raise NotImplementedError

    @classmethod
    def _get_temporal_coverage(cls, element_values):
        """Get start and end dates, when defined, that characterise the temporal
        coverage of the dataset.

        * Format EPOS PROD API:
            "temporalCoverage": {
                {'startDate': '2017-03-28T18:25:40Z'}
            }
        """
        value_list = []
        for value_data in element_values:
            start_date = value_data.get("startDate", None)
            end_date = value_data.get("endDate", None)

            value_data_normalised = {}
            if start_date:
                start_date = datetime.datetime.strptime(
                    start_date, "%Y-%m-%dT%H:%M:%SZ"
                )
                value_data_normalised["start_date"] = start_date

            if end_date:
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")
                value_data_normalised["end_date"] = end_date

            value_list.append(value_data_normalised)

        return value_list

    @classmethod
    def _get_person(cls, element_values):
        """Return a list with person-related info.

        * Format EPOS PROD API:
            "availableContactPoints": [
                {
                    "href": "https://www.ics-c.epos-eu.org/api/v1/sender/send-email?id=1c793c32-469d-422a-a3c8-c5e4ac8aecf2&contactType=SERVICEPROVIDERS",
                    "type": "SERVICEPROVIDERS"
                },
                {
                    "href": "https://www.ics-c.epos-eu.org/api/v1/sender/send-email?id=be29415c-66c4-42ad-a6d9-982d0afc166e&contactType=DATAPROVIDERS",
                    "type": "DATAPROVIDERS"
               },
               {
                    "href": "https://www.ics-c.epos-eu.org/api/v1/sender/send-email?id=b8b5f0c3-a71c-448e-88ac-3a3c5d97b08f&contactType=ALL",
                    "type": "ALL"
               }
             ]
        """
        return [
            value_data.get("href", "")
            for value_data in element_values
            if value_data.get("type", "") == "ALL"
        ]


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

    @property
    def metadata_utils(self):
        return MetadataValues()
