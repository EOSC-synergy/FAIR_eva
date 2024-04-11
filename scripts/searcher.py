#!/usr/bin/env python3


import argparse
import json
import logging
import requests
import socket
import sys
import time
from flask_babel import Babel, gettext, lazy_gettext as _l


def get_input_args():
    parser = argparse.ArgumentParser(
        description=("Command-line interface for FAIR EVA tool")
    )
    parser.add_argument(
        "-q",
        "--query",
        metavar="QUERY",
        type=str,
        help="Text to search",
    )

    return parser.parse_args()


def search(keytext):
    args = get_input_args()
    max_tries = 5

    headers = {
        "accept": "application/json",
    }
    good = 0
    params = {"facets": "false", "q": keytext}
    print(args.query)
    response = requests.get(
        "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1/resources/search",
        params=params,
        headers=headers,
    )
    terms = response.json()
    # print(response.json())
    # print(terms.keys())
    # print(terms['filters'])
    # print(len(terms['results']['distributions']))
    print(terms["results"]["distributions"][0])
    # print(terms['results']['distributions'][0]['title'])
    number_of_items = len(terms["results"]["distributions"])
    for index in range((len(terms["results"]["distributions"]))):
        print(index, (terms["results"]["distributions"][index]["title"]))
    for j in range(max_tries):
        ind = input(
            "Please choose the index of the item you want to evaluate. From 0 to "
            + str(len(terms["results"]["distributions"]))
            + " "
        )
        try:
            if int(ind) > (-1) and int(ind) < number_of_items:
                good = 1
        except:
            print("Please introduce an integer between 0 and " + str(max_tries))
        if good == 1:
            break
    if good == 0:
        print("Max tries , restart program")
        return ()

    print(
        "You choose "
        + str(ind)
        + " "
        + terms["results"]["distributions"][int(ind)]["title"]
    )
    print(
        "The url to conect is  "
        + " "
        + terms["results"]["distributions"][int(ind)]["href"]
    )
    print("The UUID is  " + " " + terms["results"]["distributions"][int(ind)]["id"])


search("")
