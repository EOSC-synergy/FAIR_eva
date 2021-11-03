#!/usr/bin/python
# -*- coding: utf-8 -*-
import configparser
import idutils
import logging
import gettext
import psycopg2
import xml.etree.ElementTree as ET
import re
import requests
from api.evaluator import Evaluator
import pandas as pd
import api.utils as ut
import sys
import urllib

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class Example_Plugin(Evaluator):

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

    def __init__(self, item_id, oai_base=None, lang='en'):
        super().__init__(item_id, oai_base, lang)
        self.id_type = 'internal'

        global _
        _ = super().translation()

        config = configparser.ConfigParser()
        config.read('config.ini')
        logging.debug("CONFIG LOADED")

        #You need a way to get your metadata in a similar format
        metadata_sample = [['{http://purl.org/dc/elements/1.1/}','title', 'MyTitle', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'creator', 'TheCreator', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'identifier', '123456', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'rigths', 'https://creativecommons.org/licenses/by/4.0/', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'description', 'This is the description', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'date', '2019-12-12', None],
                           ['{http://purl.org/dc/elements/1.1/}', 'publisher', 'Thematic Service', None]]

        self.metadata = pd.DataFrame(metadata_sample,
                                     columns=['text_value',
                                              'metadata_schema', 'element',
                                              'qualifier'])

        logging.debug('METADATA: %s' % (self.metadata))
        #Protocol for (meta)data accessing
        if len(self.metadata) > 0:
            self.access_protocols = ['http']

    def rda_a1_01m(self):
        #IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = 'Data is not accessible'
        return (points, msg)
    
    def rda_a1_02m(self):
        #IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = 'Data is not accessible'
        return (points, msg)

    def rda_i1_02m(self):
        """ Indicator RDA-A1-01M
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
        #TO REDEFINE
        points = 0
        msg = 'No machine-actionable metadata format found. OAI-PMH endpoint may help'
        return (points, msg)

    def rda_i1_02d(self):
        """ Indicator RDA-A1-01M
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
        """ Indicator RDA-A1-01M
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
        #TO REDEFINE
        points = 0
        msg = \
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')
        return (points, msg)

    def rda_r1_3_01d(self):
        """ Indicator RDA_R1.3_01D

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
        #TO REDEFINE
        points = 0
        msg = \
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')
        return (points, msg)