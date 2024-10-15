#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import sys

from api.evaluator import ConfigTerms
from plugins.epos.plugin import MetadataValues as EPOSMetadataValues
from plugins.epos.plugin import Plugin as EPOSDevPlugin
from plugins.epos.plugin import logger, logger_api


class MetadataValues(EPOSMetadataValues):
    @classmethod
    def _get_identifiers_metadata(cls, element_values):
        raise NotImplementedError

    @classmethod
    def _get_identifiers_data(cls, element_values):
        return super()._get_identifiers_data(element_values)

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

        * Format EPOS API:
            [{
                "id": "5ac04716-c056-4d04-af99-24a67206c08d",
                "metaid": "bf860e2e-667e-4b58-a2b7-16cd820b700a",
                "person": {
                    "id": "0407c0ee-4e57-4fad-80c0-ef83fc7230d0",
                    "metaid": "feaff2df-c8fc-4a0b-b2c6-78765256cfd0",
                    "uid": "https://orcid.org/0000-0001-7641-4689"
                },
                "uid": "http://www.w3.org/ns/Manager_contact1_astarte"
            }]
        """
        return [
            value_data.get("person", {}).get("uid", "") for value_data in element_values
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

    def __init__(self, *args, **kwargs):
        super().__init__(name=self.name, *args, **kwargs)

    @property
    def metadata_utils(self):
        return MetadataValues()
