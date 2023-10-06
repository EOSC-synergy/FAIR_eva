import configparser
import os
import yaml
from api.evaluator import Evaluator
import api.utils as ut
from connexion import NoContent
import json
import importlib
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='\'%(name)s:%(lineno)s\' | %(message)s')

logger = logging.getLogger(os.path.basename(__file__))



def repo_object(body):
    logger.debug("REPO OBJECT CREATING...")
    repo = body.get("repo")
    logger.debug("Repo: %s" % repo)
    item_id = body.get("id")
    logger.debug("Item_id: %s" % item_id)
    oai_base = body.get("oai_base")
    logger.debug("OAI: %s" % oai_base)
    lang = 'en'
    if "lang" in body:
        lang = body.get("lang")
    try:
        if repo == "oai-pmh":
            eva = Evaluator(item_id, oai_base, lang)
        else:
            logger.debug("Trying to import plugin from plugins.%s.plugin" % (repo))
            plugin = importlib.import_module("plugins.%s.plugin" % (repo), ".")
            eva = plugin.Plugin(item_id, oai_base, lang)

    except Exception as e:
        logger.error(e)
        raise Exception(e)
    return eva


def rda_f1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01m()
        findable = {'name': 'RDA_F1_01M', 'msg': msg, 'points': points,
                    'color': ut.get_color(points),
                    'test_status': ut.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return findable, 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01d()
        result = {'name': 'RDA_F1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02m()
        result = {'name': 'RDA_F1_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02d()
        result = {'name': 'RDA_F1_02D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f2_01m()
        result = {'name': 'RDA_F2_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f3_01m()
        result = {'name': 'RDA_F3_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_f4_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f4_01m()
        result = {'name': 'RDA_F4_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_01m()
        result = {'name': 'RDA_A1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02m()
        result = {'name': 'RDA_A1_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02d()
        result = {'name': 'RDA_A1_02D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03m()
        result = {'name': 'RDA_A1_03M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_03d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03d()
        result = {'name': 'RDA_A1_03D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04m()
        result = {'name': 'RDA_A1_04M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_04d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04d()
        result = {'name': 'RDA_A1_04D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_05d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_05d()
        result = {'name': 'RDA_A1_05D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01m()
        result = {'name': 'RDA_A1.1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01d()
        result = {'name': 'RDA_A1.1_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a1_2_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_2_01d()
        result = {'name': 'RDA_A1.2_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_a2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a2_01m()
        result = {'name': 'RDA_A2_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01m()
        result = {'name': 'RDA_I1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01d()
        result = {'name': 'RDA_I1_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02m()
        result = {'name': 'RDA_I1_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02d()
        result = {'name': 'RDA_I1_02D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01m()
        result = {'name': 'RDA_I2_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i2_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01d()
        result = {'name': 'RDA_I2_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01m()
        result = {'name': 'RDA_I3_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01d()
        result = {'name': 'RDA_I3_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02m()
        result = {'name': 'RDA_I3_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02d()
        result = {'name': 'RDA_I3_02D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_03m()
        result = {'name': 'RDA_I3_03M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_i3_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_04m()
        result = {'name': 'RDA_I3_04M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_01m()
        result = {'name': 'RDA_R1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_01m()
        result = {'name': 'RDA_R1.1_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_02m()
        result = {'name': 'RDA_R1.1_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_03m()
        result = {'name': 'RDA_R1.1_03M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_01m()
        result = {'name': 'RDA_R1.2_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_2_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_02m()
        result = {'name': 'RDA_R1.2_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01m()
        result = {'name': 'RDA_R1.3_01M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01d()
        result = {'name': 'RDA_R1.3_01D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02m()
        result = {'name': 'RDA_R1.3_02M', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_r1_3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02d()
        result = {'name': 'RDA_R1.3_02D', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201

def data_01(body):
    eva = repo_object(body)
    try:
        points, msg = eva.data_01()
        result = {'name': 'DATA_01', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201

def data_02(body):
    eva = repo_object(body)
    try:
        points, msg = eva.data_02()
        result = {'name': 'DATA_02', 'msg': msg, 'points': points,
                  'color': ut.get_color(points),
                  'test_status': ut.test_status(points),
                  'score': {'earned': points, 'total': 100}}
        return json.dumps(result), 200
    except Exception as e:
        logger.error(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': ut.get_color(0),
                 'test_status': ut.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return json.dumps(error), 201


def rda_all(body):
    try:
        eva = repo_object(body)
    except Exception as e:
        logger.error("Problem creating object")
        error = {'code': 201, 'message': "%s" % e}
        logger.error(error)
        return json.dumps(error), 201
    findable = {}
    accessible = {}
    interoperable = {}
    reusable = {}
    data_test = {}
    error = {}
    x_principle = ''
    result_points = 10
    num_of_tests = 10

    from fair import app_dirname
    config = configparser.ConfigParser()
    if "CONFIG_FILE" in os.environ:
        config_file = os.getenv("CONFIG_FILE")
    try:
        config_file = os.path.join(app_dirname, 'config.ini')
        config.read_file(open(config_file))
        logging.debug(
            'Main configuration successfully loaded: %s' % config_file
        )
    except configparser.MissingSectionHeaderError as e:
        message = 'Could not find main config file: %s' % config_file
        logging.error(message)
        logging.debug(e)
        error = {'code': 500, 'message': '%s' % message}
        logging.debug('Returning API response: %s' % error)
        return json.dumps(error), 500

    generic_config = config['Generic']
    api_config = os.path.join(
        app_dirname,
        generic_config.get('api_config', 'fair-api.yaml')
    )
    try:
        with open(api_config, 'r') as f:
            documents = yaml.full_load(f)
        logging.debug('API configuration successfully loaded: %s' % api_config)
    except Exception as e:
        message = 'Could not find API config file: %s' % api_config
        logger.error(message)
        logger.debug(e)
        error = {'code': 500, 'message': '%s' % message}
        logger.debug('Returning API response: %s' % error)
        return json.dumps(error), 500

    for e in documents['paths']:
        try:
            if documents['paths'][e]['x-indicator']:
                indi_code = e.split("/")
                indi_code = indi_code[len(indi_code) - 1]
                logger.debug("Running - %s" % indi_code)
                points, msg = getattr(eva, indi_code)()
                x_principle = documents['paths'][e]['x-principle']
                if "Findable" in x_principle:
                    findable.update({indi_code: {
                                    'name': indi_code, 'msg': msg,
                                    'points': points,
                                    'color': ut.get_color(points),
                                    'test_status': ut.test_status(points),
                                    'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
                elif "Accessible" in x_principle:
                    accessible.update({indi_code: {
                                      'name': indi_code, 'msg': msg,
                                      'points': points,
                                      'color': ut.get_color(points),
                                      'test_status': ut.test_status(points),
                                      'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
                elif "Interoperable" in x_principle:
                    interoperable.update({indi_code: {
                                         'name': indi_code, 'msg': msg,
                                         'points': points,
                                         'color': ut.get_color(points),
                                         'test_status': ut.test_status(points),
                                         'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
                elif "Reusable" in x_principle:
                    reusable.update({indi_code: {
                                    'name': indi_code, 'msg': msg,
                                    'points': points,
                                    'color': ut.get_color(points),
                                    'test_status': ut.test_status(points),
                                    'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
            elif documents['paths'][e]['x-data_test']:
                try:
                    indi_code = e.split("/")
                    indi_code = indi_code[len(indi_code) - 1]
                    logger.debug("Running Data test - %s" % indi_code)
                    points, msg = getattr(eva, indi_code)()
                    x_principle = documents['paths'][e]['x-principle']
                    if "Data" in x_principle:
                        data_test.update({indi_code: {
                                        'name': indi_code, 'msg': msg,
                                        'points': points,
                                        'color': ut.get_color(points),
                                        'test_status': ut.test_status(points),
                                        'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
                except Exception as e:
                   logger.error("Problem in data test - %s | Probably this test does not exist for this plugin" % x_principle)
        except Exception as e:
            logger.error("Problem in test - %s" % x_principle)
            if "Findable" in x_principle:
                findable.update({indi_code: {
                    'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': ut.get_color(points),
                                'test_status': ut.test_status(points),
                                'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
            elif "Accessible" in x_principle:
                accessible.update({indi_code: {
                                  'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                  'points': points,
                                  'color': ut.get_color(points),
                                  'test_status': ut.test_status(points),
                                  'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
            elif "Interoperable" in x_principle:
                interoperable.update({indi_code: {
                                     'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                     'points': points,
                                     'color': ut.get_color(points),
                                     'test_status': ut.test_status(points),
                                     'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
            elif "Reusable" in x_principle:
                reusable.update({indi_code: {
                                'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': ut.get_color(points),
                                'test_status': ut.test_status(points),
                                'score': {'earned': points, 'total': 100, 'weight': documents['paths'][e]['x-level']}}})
            logger.error(e)
            # return json.dumps(error), 201

    if len(data_test) > 0:
        result = {'findable': findable, 'accessible': accessible,
                  'interoperable': interoperable, 'reusable': reusable, "data_test": data_test}
    else:
        result = {'findable': findable, 'accessible': accessible,
                  'interoperable': interoperable, 'reusable': reusable}
    return json.dumps(result), 200


def delete(id_):
    id_ = int(id_)
    return NoContent, 204


def get(name):
    findable = {'name': name, 'msg': "Test %s has been performed" % name,
                'points': 100, 'color': "#2ECC71"}
    return findable


def search(limit=100):
    return get()
