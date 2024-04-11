import os
import glob
import yaml
from api.evaluator import Evaluator
import api.utils as ut
from connexion import NoContent
from fair import app_dirname, load_config
import importlib
import logging
import sys
from functools import wraps

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)
logger = logging.getLogger(os.path.basename(__file__))

config = load_config()


def load_evaluator(wrapped_func):
    @wraps(wrapped_func)
    def wrapper(body, **kwargs):
        repo = body.get("repo")
        item_id = body.get("id", "")
        oai_base = body.get("oai_base")
        lang = body.get("lang", "en")
        pattern_to_query = body.get("q", "")

        logger.debug("JSON payload received: %s" % body)
        # Exit if there is no way to obtain the identifier/s: either (i) provided through "id" or (ii) by a search query term
        if not (item_id or pattern_to_query):
            msg = "Neither the identifier nor the pattern to query was provided. Exiting.."
            logger.error(msg)
            return msg, 400

        # Get the identifiers through a search query
        ids = [item_id]
        # FIXME oai-pmh should be no different
        if repo not in ["oai-pmh"]:
            try:
                logger.debug("Trying to import plugin from plugins.%s.plugin" % (repo))
                plugin = importlib.import_module("plugins.%s.plugin" % (repo), ".")
            except Exception as e:
                logger.error(str(e))
                return str(e), 400
            if pattern_to_query:
                try:
                    ids = plugin.Plugin.get_ids(
                        oai_base=oai_base, pattern_to_query=pattern_to_query
                    )
                except Exception as e:
                    logger.error(str(e))
                    return str(e), 400

        # Collect FAIR checks per metadata identifier
        result = {}
        exit_code = 200
        for item_id in ids:
            # FIXME oai-pmh should be no different
            if repo in ["oai-pmh"]:
                eva = Evaluator(item_id, oai_base, lang)
            else:
                eva = plugin.Plugin(item_id, oai_base, lang)
            _result, _exit_code = wrapped_func(body, eva=eva)
            result[item_id] = _result
            if _exit_code != 200:
                exit_code = _exit_code

        return result, exit_code

    return wrapper


def endpoints(plugin=None, plugins_path="plugins"):
    plugins_with_endpoint = []
    links = []

    # Get the list of plugins
    modules = glob.glob(os.path.join(app_dirname, plugins_path, "*"))
    plugins_list = [
        os.path.basename(folder) for folder in modules if os.path.isdir(folder)
    ]

    # Obtain endpoint from each plugin's config
    for plug in plugins_list:
        config = load_config(plugin=plug, fail_if_no_config=False)
        endpoint = config.get("Generic", "endpoint", fallback="")
        if not endpoint:
            logger.debug(
                "Plugin's config does not contain 'Generic:endpoint' section: %s" % plug
            )
            logger.warning(
                "Could not get (meta)data endpoint from plugin's config: %s " % plug
            )
        else:
            logger.debug("Obtained endpoint for plugin '%s': %s" % (plug, endpoint))
            links.append(endpoint)
            plugins_with_endpoint.append(plug)
    # Create a dict with all the found endpoints
    enp = dict(zip(plugins_with_endpoint, links))
    # If the plugin is given then only returns a message
    if plugin:
        try:
            return enp[plugin]
        except:
            return "Input plugin not found"
    return enp


@load_evaluator
def rda_f1_01m(body, eva):
    try:
        points, msg = eva.rda_f1_01m()
        result = {
            "name": "RDA_F1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f1_01d(body, eva):
    try:
        points, msg = eva.rda_f1_01d()
        result = {
            "name": "RDA_F1_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f1_02m(body, eva):
    try:
        points, msg = eva.rda_f1_02m()
        result = {
            "name": "RDA_F1_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f1_02d(body, eva):
    try:
        points, msg = eva.rda_f1_02d()
        result = {
            "name": "RDA_F1_02D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f2_01m(body, eva):
    try:
        points, msg = eva.rda_f2_01m()
        result = {
            "name": "RDA_F2_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f3_01m(body, eva):
    try:
        points, msg = eva.rda_f3_01m()
        result = {
            "name": "RDA_F3_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_f4_01m(body, eva):
    try:
        points, msg = eva.rda_f4_01m()
        result = {
            "name": "RDA_F4_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_01m(body, eva):
    try:
        points, msg = eva.rda_a1_01m()
        result = {
            "name": "RDA_A1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_02m(body, eva):
    try:
        points, msg = eva.rda_a1_02m()
        result = {
            "name": "RDA_A1_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_02d(body, eva):
    try:
        points, msg = eva.rda_a1_02d()
        result = {
            "name": "RDA_A1_02D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_03m(body, eva):
    try:
        points, msg = eva.rda_a1_03m()
        result = {
            "name": "RDA_A1_03M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_03d(body, eva):
    try:
        points, msg = eva.rda_a1_03d()
        result = {
            "name": "RDA_A1_03D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_04m(body, eva):
    try:
        points, msg = eva.rda_a1_04m()
        result = {
            "name": "RDA_A1_04M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_04d(body, eva):
    try:
        points, msg = eva.rda_a1_04d()
        result = {
            "name": "RDA_A1_04D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_05d(body, eva):
    try:
        points, msg = eva.rda_a1_05d()
        result = {
            "name": "RDA_A1_05D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_1_01m(body, eva):
    try:
        points, msg = eva.rda_a1_1_01m()
        result = {
            "name": "RDA_A1.1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_1_01d(body, eva):
    try:
        points, msg = eva.rda_a1_1_01d()
        result = {
            "name": "RDA_A1.1_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a1_2_01d(body, eva):
    try:
        points, msg = eva.rda_a1_2_01d()
        result = {
            "name": "RDA_A1.2_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_a2_01m(body, eva):
    try:
        points, msg = eva.rda_a2_01m()
        result = {
            "name": "RDA_A2_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i1_01m(body, eva):
    try:
        points, msg = eva.rda_i1_01m()
        result = {
            "name": "RDA_I1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i1_01d(body, eva):
    try:
        points, msg = eva.rda_i1_01d()
        result = {
            "name": "RDA_I1_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i1_02m(body, eva):
    try:
        points, msg = eva.rda_i1_02m()
        result = {
            "name": "RDA_I1_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i1_02d(body, eva):
    try:
        points, msg = eva.rda_i1_02d()
        result = {
            "name": "RDA_I1_02D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i2_01m(body, eva):
    try:
        points, msg = eva.rda_i2_01m()
        result = {
            "name": "RDA_I2_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i2_01d(body, eva):
    try:
        points, msg = eva.rda_i2_01d()
        result = {
            "name": "RDA_I2_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_01m(body, eva):
    try:
        points, msg = eva.rda_i3_01m()
        result = {
            "name": "RDA_I3_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_01d(body, eva):
    try:
        points, msg = eva.rda_i3_01d()
        result = {
            "name": "RDA_I3_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_02m(body, eva):
    try:
        points, msg = eva.rda_i3_02m()
        result = {
            "name": "RDA_I3_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_02d(body, eva):
    try:
        points, msg = eva.rda_i3_02d()
        result = {
            "name": "RDA_I3_02D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_03m(body, eva):
    try:
        points, msg = eva.rda_i3_03m()
        result = {
            "name": "RDA_I3_03M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_i3_04m(body, eva):
    try:
        points, msg = eva.rda_i3_04m()
        result = {
            "name": "RDA_I3_04M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_01m(body, eva):
    try:
        points, msg = eva.rda_r1_01m()
        result = {
            "name": "RDA_R1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_1_01m(body, eva):
    try:
        points, msg = eva.rda_r1_1_01m()
        result = {
            "name": "RDA_R1.1_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_1_02m(body, eva):
    try:
        points, msg = eva.rda_r1_1_02m()
        result = {
            "name": "RDA_R1.1_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_1_03m(body, eva):
    try:
        points, msg = eva.rda_r1_1_03m()
        result = {
            "name": "RDA_R1.1_03M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_2_01m(body, eva):
    try:
        points, msg = eva.rda_r1_2_01m()
        result = {
            "name": "RDA_R1.2_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_2_02m(body, eva):
    try:
        points, msg = eva.rda_r1_2_02m()
        result = {
            "name": "RDA_R1.2_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_3_01m(body, eva):
    try:
        points, msg = eva.rda_r1_3_01m()
        result = {
            "name": "RDA_R1.3_01M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_3_01d(body, eva):
    try:
        points, msg = eva.rda_r1_3_01d()
        result = {
            "name": "RDA_R1.3_01D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_3_02m(body, eva):
    try:
        points, msg = eva.rda_r1_3_02m()
        result = {
            "name": "RDA_R1.3_02M",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_r1_3_02d(body, eva):
    try:
        points, msg = eva.rda_r1_3_02d()
        result = {
            "name": "RDA_R1.3_02D",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def data_01(body, eva):
    try:
        points, msg = eva.data_01()
        result = {
            "name": "DATA_01",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def data_02(body, eva):
    try:
        points, msg = eva.data_02()
        result = {
            "name": "DATA_02",
            "msg": msg,
            "points": points,
            "color": ut.get_color(points),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 200
    except Exception as e:
        logger.error(e)
        result = {
            "name": "ERROR",
            "msg": "Exception: %s" % e,
            "points": 0,
            "color": ut.get_color(0),
            "test_status": ut.test_status(points),
            "score": {"earned": points, "total": 100},
        }
        exit_code = 422

    return result, exit_code


@load_evaluator
def rda_all(body, eva):
    findable = {}
    accessible = {}
    interoperable = {}
    reusable = {}
    data_test = {}
    error = {}
    x_principle = ""
    result_points = 10
    num_of_tests = 10

    generic_config = config["Generic"]
    api_config = os.path.join(
        app_dirname, generic_config.get("api_config", "fair-api.yaml")
    )
    try:
        with open(api_config, "r") as f:
            documents = yaml.full_load(f)
        logging.debug("API configuration successfully loaded: %s" % api_config)
    except Exception as e:
        message = "Could not find API config file: %s" % api_config
        logger.error(message)
        logger.debug(e)
        error = {"code": 500, "message": "%s" % message}
        logger.debug("Returning API response: %s" % error)
        return error, 500

    for e in documents["paths"]:
        try:
            if documents["paths"][e]["x-indicator"]:
                indi_code = e.split("/")
                indi_code = indi_code[len(indi_code) - 1]
                logger.debug("Running - %s" % indi_code)
                points, msg = getattr(eva, indi_code)()
                x_principle = documents["paths"][e]["x-principle"]
                if "Findable" in x_principle:
                    findable.update(
                        {
                            indi_code: {
                                "name": indi_code,
                                "msg": msg,
                                "points": points,
                                "color": ut.get_color(points),
                                "test_status": ut.test_status(points),
                                "score": {
                                    "earned": points,
                                    "total": 100,
                                    "weight": documents["paths"][e]["x-level"],
                                },
                            }
                        }
                    )
                elif "Accessible" in x_principle:
                    accessible.update(
                        {
                            indi_code: {
                                "name": indi_code,
                                "msg": msg,
                                "points": points,
                                "color": ut.get_color(points),
                                "test_status": ut.test_status(points),
                                "score": {
                                    "earned": points,
                                    "total": 100,
                                    "weight": documents["paths"][e]["x-level"],
                                },
                            }
                        }
                    )
                elif "Interoperable" in x_principle:
                    interoperable.update(
                        {
                            indi_code: {
                                "name": indi_code,
                                "msg": msg,
                                "points": points,
                                "color": ut.get_color(points),
                                "test_status": ut.test_status(points),
                                "score": {
                                    "earned": points,
                                    "total": 100,
                                    "weight": documents["paths"][e]["x-level"],
                                },
                            }
                        }
                    )
                elif "Reusable" in x_principle:
                    reusable.update(
                        {
                            indi_code: {
                                "name": indi_code,
                                "msg": msg,
                                "points": points,
                                "color": ut.get_color(points),
                                "test_status": ut.test_status(points),
                                "score": {
                                    "earned": points,
                                    "total": 100,
                                    "weight": documents["paths"][e]["x-level"],
                                },
                            }
                        }
                    )
            elif documents["paths"][e]["x-data_test"]:
                try:
                    indi_code = e.split("/")
                    indi_code = indi_code[len(indi_code) - 1]
                    logger.debug("Running Data test - %s" % indi_code)
                    points, msg = getattr(eva, indi_code)()
                    x_principle = documents["paths"][e]["x-principle"]
                    if "Data" in x_principle:
                        data_test.update(
                            {
                                indi_code: {
                                    "name": indi_code,
                                    "msg": msg,
                                    "points": points,
                                    "color": ut.get_color(points),
                                    "test_status": ut.test_status(points),
                                    "score": {
                                        "earned": points,
                                        "total": 100,
                                        "weight": documents["paths"][e]["x-level"],
                                    },
                                }
                            }
                        )
                except Exception as e:
                    logger.error(
                        "Problem in data test - %s | Probably this test does not exist for this plugin"
                        % x_principle
                    )
        except Exception as e:
            logger.error("Problem in test - %s" % x_principle)
            if "Findable" in x_principle:
                findable.update(
                    {
                        indi_code: {
                            "name": "[ERROR] - %s" % indi_code,
                            "msg": "Exception: %s" % e,
                            "points": points,
                            "color": ut.get_color(points),
                            "test_status": ut.test_status(points),
                            "score": {
                                "earned": points,
                                "total": 100,
                                "weight": documents["paths"][e]["x-level"],
                            },
                        }
                    }
                )
            elif "Accessible" in x_principle:
                accessible.update(
                    {
                        indi_code: {
                            "name": "[ERROR] - %s" % indi_code,
                            "msg": "Exception: %s" % e,
                            "points": points,
                            "color": ut.get_color(points),
                            "test_status": ut.test_status(points),
                            "score": {
                                "earned": points,
                                "total": 100,
                                "weight": documents["paths"][e]["x-level"],
                            },
                        }
                    }
                )
            elif "Interoperable" in x_principle:
                interoperable.update(
                    {
                        indi_code: {
                            "name": "[ERROR] - %s" % indi_code,
                            "msg": "Exception: %s" % e,
                            "points": points,
                            "color": ut.get_color(points),
                            "test_status": ut.test_status(points),
                            "score": {
                                "earned": points,
                                "total": 100,
                                "weight": documents["paths"][e]["x-level"],
                            },
                        }
                    }
                )
            elif "Reusable" in x_principle:
                reusable.update(
                    {
                        indi_code: {
                            "name": "[ERROR] - %s" % indi_code,
                            "msg": "Exception: %s" % e,
                            "points": points,
                            "color": ut.get_color(points),
                            "test_status": ut.test_status(points),
                            "score": {
                                "earned": points,
                                "total": 100,
                                "weight": documents["paths"][e]["x-level"],
                            },
                        }
                    }
                )
            logger.error(e)

    if len(data_test) > 0:
        result = {
            "findable": findable,
            "accessible": accessible,
            "interoperable": interoperable,
            "reusable": reusable,
            "data_test": data_test,
        }
    else:
        result = {
            "findable": findable,
            "accessible": accessible,
            "interoperable": interoperable,
            "reusable": reusable,
        }
    return result, 200


def endpoints(plugin=None):
    plugins_list = ["epos", "gbif", "digital_csic", "dspace7", "signposting"]
    plugins_with_endpoint = []
    links = []

    for plug in plugins_list:
        try:
            config = configparser.ConfigParser()
            config.read("plugins/" + plug + "/config.ini")
            links.append(config["Generic"]["endpoint"])
            plugins_with_endpoint.append(plug)
        except:
            logging.debug("No endpoint found for " + plug)
    # Create a dict with all the found endpoints
    enp = dict(zip(plugins_with_endpoint, links))
    # If the plugin is given then only returns a message
    if plugin:
        try:
            return (enp[plugin],)
        except:
            return ("Input plugin not found", 204)
    return enp


def delete(id_):
    id_ = int(id_)
    return NoContent, 204


def get(name):
    findable = {
        "name": name,
        "msg": "Test %s has been performed" % name,
        "points": 100,
        "color": "#2ECC71",
    }
    return findable


def search(limit=100):
    return get()
