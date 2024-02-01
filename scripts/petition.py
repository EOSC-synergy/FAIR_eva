from flask_babel import Babel, gettext, lazy_gettext as _l
import requests
import json


# How to use this tool
# The API needs info about what you are asking about mainly the ID (ussualy doi or handle) of the object, the oai_base, and repo,
# You need to open the API in a terminal and then make a petition to it
# If you are interested on an easy way to use the tool you can use this program,
# You need to set the variables oaibase, ide, and repo to the ones you want, you have 2 examples at the bottom


def petition(
    ide,
    oai_base,
    repo,
    lang="en",
):
    body = '{"id":"%s","lang":"%s","oai_base": "%s","repo":"%s"}' % (
        ide,
        lang,
        oai_base,
        repo,
    )
    url = "http://localhost:9090/v1.0/rda/rda_all"
    result = requests.post(url, data=body, headers={"Content-Type": "application/json"})
    result = json.loads(result.text)
    result_points = 0
    weight_of_tests = 0
    for key in result:
        g_weight = 0
        g_points = 0
        for kk in result[key]:
            result[key][kk]["indicator"] = gettext(
                "%s.indicator" % result[key][kk]["name"]
            )
            result[key][kk]["name_smart"] = gettext("%s" % result[key][kk]["name"])
            # pesos
            weight = result[key][kk]["score"]["weight"]
            weight_of_tests += weight
            g_weight += weight
            result_points += result[key][kk]["points"] * weight
            g_points += result[key][kk]["points"] * weight

        print(
            "In %s your item has %f points "
            % (
                key,
                round((g_points / g_weight), 3),
            )
        )
    result_points = round((result_points / weight_of_tests), 2)
    print("In total your item has " + str(result_points) + " points from a 100 total")


ide = "208d3855-8576-483c-ae92-89502516c28e"
oaibase = "https://www.ics-c.epos-eu.org/api/v1/resources/details"
repo = "epos"

ide2 = "http://hdl.handle.net/10261/157765"
oaibase2 = "http://digital.csic.es/dspace-oai/request"
repo2 = "oai-pmh"

petition(ide, oaibase, repo)
