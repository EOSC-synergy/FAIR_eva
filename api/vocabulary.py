import ast
import json
import logging
import os
import sys

import requests

from fair import app_dirname, load_config

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))


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

    @classmethod
    def collect(cls, search_item=None, perform_login=False):
        content = []
        # Get content from remote endpoint
        error_on_request = False
        if cls.enable_remote_check:
            logger.debug("Accessing vocabulary '%s' remotely" % cls.name)
            error_on_request, content = cls._remote_collect(cls)
        # Get content from local cache
        if not cls.enable_remote_check or error_on_request:
            logger.debug(
                "Accessing vocabulary '%s' from local cache: %s"
                % (cls.name, cls.local_path)
            )
            cls.local_path_full = os.path.join(app_dirname, cls.local_path)
            logger.debug("Full path to local cache: %s" % cls.local_path_full)
            content = cls._local_collect(cls)

        return content


class IANAMediaTypes(VocabularyConnection):
    name = "IANA Media Types"

    def _local_collect(self):
        property_key_xml = self._config.get(
            "vocabularies:iana_media_types", "property_key_xml"
        )
        logger.debug(
            "Using XML property key '%s' to gather the list of media types"
            % property_key_xml
        )
        import xml.etree.ElementTree as ET

        tree = ET.parse(self.local_path_full)
        root = tree.getroot()
        media_types_list = [
            media_type.text for media_type in root.iter(property_key_xml)
        ]
        logger.debug("List of IANA media types: %s" % media_types_list)

        return media_types_list

    @classmethod
    def collect(cls):
        _config_items = dict(load_config().items("vocabularies:iana_media_types"))
        super().__init__(cls, **_config_items)
        content = super().collect(cls)

        return content


class FAIRsharingRegistry(VocabularyConnection):
    name = "FAIRsharing registry"

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
            headers = self._login(self)
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

    @classmethod
    def collect(cls, search_topic):
        _config_items = dict(load_config().items("vocabularies:fairsharing"))
        # Set specific query parameters for remote requests
        remote_path = _config_items.get("remote_path", "")
        if not remote_path:
            logger.warning(
                "Could not get FAIRsharing API endpoint from configuration (check 'remote_path' property)"
            )
        else:
            query_parameter = "q=%s" % search_topic
            remote_path_with_query = "?page[size]=2500&".join(
                [remote_path, query_parameter]
            )
            _config_items["remote_path"] = remote_path_with_query
            logger.debug(
                "Request URL to FAIRsharing API with search topic '%s': %s"
                % (search_topic, _config_items["remote_path"])
            )
        super().__init__(cls, **_config_items)
        content = super().collect(cls)

        return content


class Vocabulary:
    @staticmethod
    def get_iana_media_types():
        vocabulary = IANAMediaTypes()
        return vocabulary.collect()

    @staticmethod
    def get_fairsharing(search_topic):
        vocabulary = FAIRsharingRegistry()
        return vocabulary.collect(search_topic=search_topic)
