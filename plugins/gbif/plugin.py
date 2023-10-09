#!/usr/bin/python
# -*- coding: utf-8 -*-
import ast
import idutils
import logging
import os
from api.evaluator import Evaluator
import pandas as pd
import requests
import sys
import xml.etree.ElementTree as ET

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='\'%(name)s:%(lineno)s\' | %(message)s')

logger = logging.getLogger(os.path.basename(__file__))


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
    def __init__(self, item_id, oai_base=None, lang='en', config=None):
        logger.debug("Creating GBIF")
        super().__init__(item_id, oai_base, lang)
        # TO REDEFINE - WHICH IS YOUR PID TYPE?
        self.id_type = idutils.detect_identifier_schemes(item_id)[0]

        global _
        _ = super().translation()

        self.config = config

        # You need a way to get your metadata in a similar format
        metadata_sample = self.get_metadata()
        self.metadata = pd.DataFrame(metadata_sample,
                                     columns=['metadata_schema',
                                              'element', 'text_value',
                                              'qualifier'])

        logger.debug('METADATA: %s' % (self.metadata))
        # Protocol for (meta)data accessing
        if len(self.metadata) > 0:
            self.access_protocols = ['http']

        # Config attributes
        plugin = 'gbif'
        self.identifier_term = self.config[plugin]['identifier_term']
        self.terms_quali_generic = ast.literal_eval(self.config[plugin]['terms_quali_generic'])
        self.terms_quali_disciplinar = ast.literal_eval(self.config[plugin]['terms_quali_disciplinar'])
        self.terms_access = ast.literal_eval(self.config[plugin]['terms_access'])
        self.terms_cv = ast.literal_eval(self.config[plugin]['terms_cv'])
        self.supported_data_formats = ast.literal_eval(self.config[plugin]['supported_data_formats'])
        self.terms_qualified_references = ast.literal_eval(self.config[plugin]['terms_qualified_references'])
        self.terms_relations = ast.literal_eval(self.config[plugin]['terms_relations'])
        self.terms_license = ast.literal_eval(self.config[plugin]['terms_license'])

    # TO REDEFINE - HOW YOU ACCESS METADATA?

    def get_metadata(self):
        url = idutils.to_url(self.item_id, idutils.detect_identifier_schemes(self.item_id)[0], url_scheme='http')
        response = requests.get(url, verify=False, allow_redirects=True)
        if response.history:
            print("Request was redirected")
            for resp in response.history:
                print(resp.status_code, resp.url)
            print("Final destination:")
            print(response.status_code, response.url)
            final_url = response.url
        else:
            print("Request was not redirected")

        final_url = final_url.replace("/resource?", "/eml.do?")
        response = requests.get(final_url, verify=False)

        tree = ET.fromstring(response.text)
        eml_schema = "{eml://ecoinformatics.org/eml-2.1.1}"
        metadata_sample = []
        elementos = tree.find('.//')
        for e in elementos:
            if e.text != '' or e.text != '\n    ' or e.text != '\n':
                metadata_sample.append([eml_schema, e.tag, e.text, None])
            for i in e.iter():
                if len(list(i.iter())) > 0:
                    for se in i.iter():
                        metadata_sample.append([eml_schema, e.tag + "." + i.tag, se.text, se.tag])
                elif i.tag != e.tag and (i.text != '' or i.text != '\n    ' or i.text != '\n'):
                    metadata_sample.append([eml_schema, e.tag, i.text, i.tag])
        return metadata_sample

    def rda_a1_01m(self):
        # IF your ID is not an standard one (like internal), this method should be redefined
        points = 0
        msg = 'Data is not accessible'
        return (points, msg)

    def rda_a1_02m(self):
        # IF your ID is not an standard one (like internal), this method should be redefined
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
        # TO REDEFINE
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
        # TO REDEFINE
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
        # TO REDEFINE
        points = 0
        msg = \
            _('Currently, this repo does not include community-bsed schemas. If you need to include yours, please contact.')
        return (points, msg)
