import json
import logging
import os
import sys

from fair import app_dirname, load_config

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class VocabularyConnection:
    def __init__(self, **config_items):
        self.vocabulary_name = config_items.get("vocabulary_name", "")
        self.enable_remote_check = config_items.get("enable_remote_check", False)
        self.remote_endpoint = config_items.get("remote_endpoint", "")
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
            logging.debug("Accessing vocabulary '%s' remotely" % cls.name)
            headers = {}
            if perform_login:
                logging.debug(
                    "Login is required for endpoint: %s" % cls.remote_endpoint
                )
                headers = cls._login()
            logging.debug(
                "Requesting vocabulary content through endpoint: %s"
                % cls.remote_endpoint
            )
            response = requests.request("POST", cls.remote_endpoint, headers=headers)
            if response.ok:
                logging.debug(
                    "Successfully returned content from endpoint: %s"
                    % cls.remote_endpoint
                )
                content = response.json()
            else:
                logging.warning(
                    "Failed to obtain records from endpoint: %s" % response.text
                )
                error_on_request = True
        # Get content from local cache
        if not cls.enable_remote_check or error_on_request:
            logging.debug(
                "Accessing vocabulary '%s' from local cache: %s"
                % (cls.name, cls.local_path)
            )
            cls.local_path_full = os.path.join(app_dirname, cls.local_path)
            logging.debug("Full path to local cache: %s" % cls.local_path_full)
            content = cls._local_collect(cls)

        return content


class IANAMediaTypes(VocabularyConnection):
    name = "IANA Media Types"
    _config = (
        load_config()
    )  # FIXME: get only the properties from 'iana media types' section

    def _local_collect(self):
        property_key_xml = self._config.get(
            "vocabularies:iana_media_types", "property_key_xml"
        )
        logging.debug(
            "Using XML property key '%s' to gather the list of media types"
            % property_key_xml
        )
        import xml.etree.ElementTree as ET

        tree = ET.parse(self.local_path_full)
        root = tree.getroot()
        media_types_list = [
            media_type.text for media_type in root.iter(property_key_xml)
        ]
        logging.debug("List of IANA media types: %s" % media_types_list)

        return media_types_list

    @classmethod
    def collect(cls):
        config_items = dict(cls._config.items("vocabularies:iana_media_types"))
        super().__init__(cls, **config_items)
        content = super().collect(cls)

        return content


class FAIRsharingRegistry(VocabularyConnection):
    def __init__(self, username, password, metadata_path, format_path):
        self.username = username
        self.password = password
        self._api_url = (
            "https://api.fairsharing.org/search/fairsharing_records?page[size]=2500&%s"
        )
        self.paths = {
            "metadata_standards": {
                "local": metadata_path,
                "remote": self._api_url
                % "fairsharing_registry=standard&user_defined_tags=metadata standardization",
            },
            "formats": {
                "local": format_path,
                "remote": self._api_url % "user_defined_tags=Geospatial data",
            },
            "serialization": {
                "local": "",
                "remote": self._api_url % "domains=Resource metadata",
            },
        }
        self._metadata_standards = {}
        self._formats = {}
        self._serialization = {}

    def _login(self):
        url_api_login = "https://api.fairsharing.org/users/sign_in"
        payload = {"user": {"login": self.username, "password": self.password}}
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
            logging.warning(
                "Could not get token from FAIRsharing API: %s" % response.text
            )

        return headers

    def _remote_collect(self):
        self._login()

    @property
    def metadata_standards(self):
        api_results = self._remote_or_local_query(search_item="metadata_standards")
        self._metadata_standards = api_results
        return self._metadata_standards

    @property
    def formats(self):
        api_results = self._remote_or_local_query(search_item="formats")
        self._formats = api_results
        return self._formats

    @property
    def serialization(self):
        api_results = self._remote_or_local_query(search_item="serialization")
        self._serialization = api_results
        return self._serialization


class Vocabulary:
    @staticmethod
    def get_iana_media_types():
        vocabulary = IANAMediaTypes()
        return vocabulary.collect()

    @staticmethod
    def get_fair_sharing():
        return FAIRsharingRegistry.collect()
