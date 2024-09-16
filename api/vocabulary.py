import ast
import json
import logging
import os
import sys

import requests

from fair import app_dirname, load_config

logger = logging.getLogger("plugin.py")


class VocabularyConnection:
    def __init__(self, **config_items):
        self.vocabulary_name = config_items.get("vocabulary_name", "")
        self.enable_remote_check = ast.literal_eval(
            config_items.get("enable_remote_check", "True")
        )
        self.remote_path = config_items.get("remote_path", "")
        self.remote_username = config_items.get("remote_username", "")
        self.remote_password = config_items.get("remote_password", "")
        self.local_path = config_items.get("local_path", "")
        self.local_path_full = ""

    def _get_token(self):
        return NotImplementedError

    def _login(self):
        return NotImplementedError

    def _remote_collect(self):
        """Performs the remote call to the vocabulary registry. It shall return a tuple (error_on_request, content), where 'error_on_request' is a boolean and 'content' is the actual content returned by the request when successful."""
        raise NotImplementedError

    def _local_collect(self):
        raise NotImplementedError

    def collect(self, search_item=None, perform_login=False):
        content = []
        # Get content from remote endpoint
        error_on_request = False
        if self.enable_remote_check:
            logger.debug(
                "Accessing vocabulary '%s' remotely through %s"
                % (self.name, self.remote_path)
            )
            error_on_request, content = self._remote_collect()
        # Get content from local cache
        if not self.enable_remote_check or error_on_request:
            logger.debug(
                "Accessing vocabulary '%s' from local cache: %s"
                % (self.name, self.local_path)
            )
            self.local_path_full = os.path.join(app_dirname, self.local_path)
            logger.debug("Full path to local cache: %s" % self.local_path_full)
            content = self._local_collect()

        return content


class IANAMediaTypes(VocabularyConnection):
    def __init__(self, config):
        self.name = "IANA Media Types"
        self._config_items = dict(config.items("vocabularies:iana_media_types"))

    def _parse_xml(self, from_file=False, from_string=""):
        property_key_xml = self._config_items.get(
            "property_key_xml", "{http://www.iana.org/assignments}file"
        )
        logger.debug(
            "Using XML property key '%s' to gather the list of media types"
            % property_key_xml
        )

        import xml.etree.ElementTree as ET

        tree = None
        if from_file:
            tree = ET.parse(self.local_path_full)
            root = tree.getroot()
        elif from_string:
            root = ET.fromstring(from_string)
        else:
            logger.error("Could not get IANA Media Types from %s" % self.remote_path)
            return []

        media_types_list = [
            media_type.text for media_type in root.iter(property_key_xml)
        ]
        logger.debug("Found %s items for IANA media types" % len(media_types_list))

        return media_types_list

    def _remote_collect(self):
        error_on_request = False
        content = []
        headers = {"Content-Type": "application/xml"}
        response = requests.request("GET", self.remote_path, headers=headers)
        if response.ok:
            content = response.text
            media_types_list = self._parse_xml(from_string=content)
            if not media_types_list:
                error_on_request = True
        else:
            error_on_request = True

        return error_on_request, content

    def _local_collect(self):
        return self._parse_xml(self, from_file=True)

    def collect(self):
        super().__init__(**self._config_items)
        content = super().collect()

        return content


class FAIRsharingRegistry(VocabularyConnection):
    def __init__(self, config):
        self.name = "FAIRsharing registry"
        self._config_items = dict(config.items("vocabularies:fairsharing"))

    def _login(self):
        url_api_login = "https://api.fairsharing.org/users/sign_in"
        payload = {
            "user": {"login": self.remote_username, "password": self.remote_password}
        }
        login_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url_api_login, headers=login_headers, data=json.dumps(payload)
        )
        # Get the JWT from the response.text to use in the next part.
        headers = {}
        if response.ok:
            data = response.json()
            token = data["jwt"]
            logger.debug("Get token from FAIRsharing API: %s" % token)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(token),
            }
        else:
            logger.warning(
                "Could not get token from FAIRsharing API: %s" % response.text
            )

        return headers

    def _remote_collect(self):
        error_on_request = False
        content = []
        if not (self.remote_username and self.remote_password):
            logger.error(
                "Could not get required 'username' and 'password' properties for accessing FAIRsharing registry API"
            )
        else:
            headers = self._login()
            logger.debug("Got headers from sign in process: %s" % headers)
            response = requests.request("POST", self.remote_path, headers=headers)
            if response.ok:
                content = response.json().get("data", [])
                if content:
                    logger.debug(
                        "Successfully returned %s items from search query: %s"
                        % (len(content), self.remote_path)
                    )
                else:
                    error_on_request = True
            else:
                logger.warning(
                    "Failed to obtain records from endpoint: %s" % response.text
                )
                error_on_request = True

        return error_on_request, content

    def _local_collect(self):
        with open(self.local_path, "r") as f:
            content = json.load(f).get("data", [])
            logger.debug("Successfully loaded local cache: %s" % content)

        return content

    def collect(self, search_topic):
        # Set specific query parameters for remote requests
        remote_path = self._config_items.get("remote_path", "")
        if not remote_path:
            logger.warning(
                "Could not get FAIRsharing API endpoint from configuration (check 'remote_path' property)"
            )
        else:
            query_parameter = "q=%s" % search_topic
            remote_path_with_query = "?page[size]=2500&".join(
                [remote_path, query_parameter]
            )
            self._config_items["remote_path"] = remote_path_with_query
            logger.debug(
                "Request URL to FAIRsharing API with search topic '%s': %s"
                % (search_topic, self._config_items["remote_path"])
            )
        super().__init__(**self._config_items)
        content = super().collect()

        return content


class Vocabulary:
    def __init__(self, config):
        self.config = config

    def get_iana_media_types(self):
        vocabulary = IANAMediaTypes(self.config)
        return vocabulary.collect()

    def get_fairsharing(self, search_topic):
        vocabulary = FAIRsharingRegistry(self.config)
        return vocabulary.collect(search_topic=search_topic)
