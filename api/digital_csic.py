#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser
import idutils
import logging
import psycopg2
import requests
from api.evaluator import Evaluator
import pandas as pd
import api.utils as ut
import sys
import urllib

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Digital_CSIC(Evaluator):

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
        if oai_base == "":
            oai_base = None
        logging.debug("Call parent")
        super().__init__(item_id, oai_base, lang)
        logging.debug("Parent called")
        if ut.get_doi_str(item_id) != '':
            self.item_id = ut.get_doi_str(item_id)
            self.id_type = 'doi'
        elif ut.get_handle_str(item_id) != '':
            self.item_id = ut.get_handle_str(item_id)
            self.id_type = 'handle'
        else:
            self.item_id = item_id
            self.id_type = 'internal'

        config = configparser.ConfigParser()
        config.read('config.ini')
        logging.debug("CONFIG LOADED")
        try:
            self.connection = psycopg2.connect(
                user=config['digital_csic']['db_user'],
                password=config['digital_csic']['db_pass'],
                host=config['digital_csic']['db_host'],
                port=config['digital_csic']['db_port'],
                database=config['digital_csic']['db_db'])
            logging.debug("DB configured")
        except Exception as error:
            logging.error('Error while fetching data from PostgreSQL ')
            logging.error(error)

        try:
            self.internal_id = self.get_internal_id(self.item_id,
                                                    self.connection)
            if self.id_type == 'doi':
                self.handle_id = self.get_handle_id(self.internal_id,
                                                    self.connection)
            elif self.id_type == 'internal':
                self.handle_id = self.get_handle_id(self.internal_id,
                                                    self.connection)
                self.item_id = self.handle_id

            logging.debug('INTERNAL ID: %i ITEM ID: %s' % (self.internal_id,
                          self.item_id))

            query = \
                'SELECT metadatavalue.text_value, metadatafieldregistry.metadata_schema_id, metadatafieldregistry.element,\
                metadatafieldregistry.qualifier FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s and \
    item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id' \
                % self.internal_id
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.metadata = pd.DataFrame(cursor.fetchall(),
                                         columns=['text_value',
                                                  'metadata_schema', 'element',
                                                  'qualifier'])
            logging.debug('METADATA: %s' % (self.metadata))
        except Exception as e:
            logging.error('Error connecting DB')
            logging.error(e)

        global _
        _ = super().translation()

    # TESTS
# DIGITAL_CSIC UTILS

    def get_internal_id(self, item_id, connection):
        internal_id = item_id
        id_to_check = ut.get_doi_str(item_id)
        logging.debug('DOI is %s' % id_to_check)
        temp_str = '%' + item_id + '%'
        if len(id_to_check) != 0:
            if ut.check_doi(id_to_check):
                query = \
                    "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                    % temp_str
                logging.debug(query)
                cursor = connection.cursor()
                cursor.execute(query)
                list_id = cursor.fetchall()
                if len(list_id) > 0:
                    for row in list_id:
                        internal_id = row[0]

        if internal_id == item_id:
            id_to_check = ut.get_handle_str(item_id)
            logging.debug('PID is %s' % id_to_check)
            temp_str = '%' + item_id + '%'
            query = \
                "SELECT item.item_id FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatavalue.text_value LIKE '%s'" \
                % temp_str
            logging.debug(query)
            cursor = connection.cursor()
            cursor.execute(query)
            list_id = cursor.fetchall()
            if len(list_id) > 0:
                for row in list_id:
                    internal_id = row[0]

        return internal_id

    def get_handle_id(self, internal_id, connection):
        query = \
            "SELECT metadatavalue.text_value FROM item, metadatavalue, metadatafieldregistry WHERE item.item_id = %s AND item.item_id = metadatavalue.resource_id AND metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id AND metadatafieldregistry.element = 'identifier' AND metadatafieldregistry.qualifier = 'uri'" \
            % internal_id
        cursor = connection.cursor()
        cursor.execute(query)
        list_id = cursor.fetchall()
        handle_id = ''
        if len(list_id) > 0:
            for row in list_id:
                handle_id = row[0]

        return ut.get_handle_str(handle_id)
