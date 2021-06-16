import yaml
from api.digital_csic import Digital_CSIC
from api.dspace_7 import DSpace_7
from api.evaluator import Evaluator

from connexion import NoContent


def repo_object(body):
    repo = body.get("repo")
    item_id = body.get("id")
    if repo == "digital_csic":
        eva = Digital_CSIC(item_id)
    elif repo == "dspace_7":
        eva = DSpace_7(item_id)
    elif repo == 'oai-pmh':
        oai_base = body.get("oai_base")
        eva = Evaluator(item_id, oai_base)
    return eva


def rda_f1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01m()
        findable = {'name': 'RDA_F1_01M', 'msg': msg, 'points': points,
                    'color': eva.get_color(points)}
        return findable, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01d()
        result = {'name': 'RDA_F1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02m()
        result = {'name': 'RDA_F1_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02d()
        result = {'name': 'RDA_F1_02D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f2_01m()
        result = {'name': 'RDA_F2_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f3_01m()
        result = {'name': 'RDA_F3_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_f4_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f4_01m()
        result = {'name': 'RDA_F4_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_01m()
        result = {'name': 'RDA_A1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02m()
        result = {'name': 'RDA_A1_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02d()
        result = {'name': 'RDA_A1_02D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03m()
        result = {'name': 'RDA_A1_03M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_03d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03d()
        result = {'name': 'RDA_A1_03D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04m()
        result = {'name': 'RDA_A1_04M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_04d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04d()
        result = {'name': 'RDA_A1_04D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_05d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_05d()
        result = {'name': 'RDA_A1_05D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01m()
        result = {'name': 'RDA_A1.1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01d()
        result = {'name': 'RDA_A1.1_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a1_2_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_2_01d()
        result = {'name': 'RDA_A1.2_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_a2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a2_01m()
        result = {'name': 'RDA_A2_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01m()
        result = {'name': 'RDA_I1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01d()
        result = {'name': 'RDA_I1_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02m()
        result = {'name': 'RDA_I1_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02d()
        result = {'name': 'RDA_I1_02D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01m()
        result = {'name': 'RDA_I2_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i2_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01d()
        result = {'name': 'RDA_I2_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01m()
        result = {'name': 'RDA_I3_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01d()
        result = {'name': 'RDA_I3_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02m()
        result = {'name': 'RDA_I3_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02d()
        result = {'name': 'RDA_I3_02D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_03m()
        result = {'name': 'RDA_I3_03M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_i3_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_04m()
        result = {'name': 'RDA_I3_04M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_01m()
        result = {'name': 'RDA_R1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_01m()
        result = {'name': 'RDA_R1.1_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_02m()
        result = {'name': 'RDA_R1.1_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_03m()
        result = {'name': 'RDA_R1.1_03M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_01m()
        result = {'name': 'RDA_R1.2_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_2_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_02m()
        result = {'name': 'RDA_R1.2_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01m()
        result = {'name': 'RDA_R1.3_01M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01d()
        result = {'name': 'RDA_R1.3_01D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02m()
        result = {'name': 'RDA_R1.3_02M', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_r1_3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02d()
        result = {'name': 'RDA_R1.3_02D', 'msg': msg, 'points': points,
                  'color': eva.get_color(points)}
        return result, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': eva.get_color(0)}
        return error, 201


def rda_all(body):
    try:
        eva = repo_object(body)
    except Exception as e:
        print("Problem creating object")
        error = {'code': 201, 'message': "%s" % e}
        print(e)
        return error, 201
    findable = {}
    accessible = {}
    interoperable = {}
    reusable = {}
    error = {}
    x_principle = ''
    result_points = 10
    num_of_tests = 10

    with open('fair-api.yaml', 'r') as f:
        documents = yaml.full_load(f)
    for e in documents['paths']:
        try:
            if documents['paths'][e]['x-indicator']:
                indi_code = e.split("/")
                indi_code = indi_code[len(indi_code) - 1]
                print("Running - %s" % indi_code)
                points, msg = getattr(eva, indi_code)()
                x_principle = documents['paths'][e]['x-principle']
                if "Findable" in x_principle:
                    findable.update({indi_code: {
                                    'name': indi_code, 'msg': msg,
                                    'points': points,
                                    'color': eva.get_color(points)}})
                elif "Accessible" in x_principle:
                    accessible.update({indi_code: {
                                      'name': indi_code, 'msg': msg,
                                      'points': points,
                                      'color': eva.get_color(points)}})
                elif "Interoperable" in x_principle:
                    interoperable.update({indi_code: {
                                         'name': indi_code, 'msg': msg,
                                         'points': points,
                                         'color': eva.get_color(points)}})
                elif "Reusable" in x_principle:
                    reusable.update({indi_code: {
                                    'name': indi_code, 'msg': msg,
                                    'points': points,
                                    'color': eva.get_color(points)}})
        except Exception as e:
            print("Problem in test - %s" % x_principle)
            if "Findable" in x_principle:
                findable.update({indi_code: {
                    'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': eva.get_color(points)}})
            elif "Accessible" in x_principle:
                accessible.update({indi_code: {
                                  'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                  'points': points,
                                  'color': eva.get_color(points)}})
            elif "Interoperable" in x_principle:
                interoperable.update({indi_code: {
                                     'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                     'points': points,
                                     'color': eva.get_color(points)}})
            elif "Reusable" in x_principle:
                reusable.update({indi_code: {
                                'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': eva.get_color(points)}})
            print(e)
            #return error, 201

    result = {'findable': findable, 'accessible': accessible,
            'interoperable': interoperable, 'reusable': reusable}
    return result, 200


def delete(id_):
    id_ = int(id_)
    return NoContent, 204


def get(name):
    findable = {'name': name, 'msg': "Test %s has been performed" % name,
                'points': 100, 'color': "#2ECC71"}
    return findable


def search(limit=100):
    return get()
