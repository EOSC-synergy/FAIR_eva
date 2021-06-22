import yaml
from api.coar import RepoTest

from connexion import NoContent


def repo_object(body):
    repo = RepoTest(body.get("oai_base"))
    return repo

def coar_1_1(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_1()
        coar = {'name': 'COAR_1_1', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_1_2(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_2()
        coar = {'name': 'COAR_1_2', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_1_4(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_4()
        coar = {'name': 'COAR_1_4', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_1_6(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_6()
        coar = {'name': 'COAR_1_6', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_1_8(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_8()
        coar = {'name': 'COAR_1_8', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_1_11(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_1_11()
        coar = {'name': 'COAR_1_11', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_2_3(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_2_3()
        coar = {'name': 'COAR_2_3', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_2_4(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_2_4()
        coar = {'name': 'COAR_2_4', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_3_1(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_3_1()
        coar = {'name': 'COAR_3_1', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_3_4(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_3_4()
        coar = {'name': 'COAR_3_4', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_4_4(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_4_4()
        coar = {'name': 'COAR_4_4', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_9_1(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_9_1()
        coar = {'name': 'COAR_9_1', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_9_4(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_9_4()
        coar = {'name': 'COAR_9_4', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201


def coar_9_5(body):
    repo = repo_object(body)
    try:
        points, msg = repo.coar_9_5()
        coar = {'name': 'COAR_9_5', 'msg': msg, 'points': points,
                    'color': repo.get_color(points),
                    'test_status': repo.test_status(points),
                    'score': {'earned': points, 'total': 100}}
        return coar, 200
    except Exception as e:
        print(e)
        error = {'name': 'ERROR', 'msg': 'Exception: %s' % e, 'points': 0,
                 'color': repo.get_color(0),
                 'test_status': repo.test_status(points),
                 'score': {'earned': points, 'total': 100}}
        return error, 201

def coar_all(body):
    try:
        repo = repo_object(body)
    except Exception as e:
        print("Problem creating object")
        error = {'code': 201, 'message': "%s" % e}
        print(e)
        return error, 201
    coar = {}
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
                                    'color': eva.get_color(points),
                                    'test_status': eva.test_status(points),
                                    'score': {'earned': points, 'total': 100}}})
                elif "Accessible" in x_principle:
                    accessible.update({indi_code: {
                                      'name': indi_code, 'msg': msg,
                                      'points': points,
                                      'color': eva.get_color(points),
                                      'test_status': eva.test_status(points),
                                      'score': {'earned': points, 'total': 100}}})
                elif "Interoperable" in x_principle:
                    interoperable.update({indi_code: {
                                         'name': indi_code, 'msg': msg,
                                         'points': points,
                                         'color': eva.get_color(points),
                                         'test_status': eva.test_status(points),
                                         'score': {'earned': points, 'total': 100}}})
                elif "Reusable" in x_principle:
                    reusable.update({indi_code: {
                                    'name': indi_code, 'msg': msg,
                                    'points': points,
                                    'color': eva.get_color(points),
                                    'test_status': eva.test_status(points),
                                    'score': {'earned': points, 'total': 100}}})
        except Exception as e:
            print("Problem in test - %s" % x_principle)
            if "Findable" in x_principle:
                findable.update({indi_code: {
                    'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': eva.get_color(points),
                                'test_status': eva.test_status(points),
                                'score': {'earned': points, 'total': 100}}})
            elif "Accessible" in x_principle:
                accessible.update({indi_code: {
                                  'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                  'points': points,
                                  'color': eva.get_color(points),
                                  'test_status': eva.test_status(points),
                                  'score': {'earned': points, 'total': 100}}})
            elif "Interoperable" in x_principle:
                interoperable.update({indi_code: {
                                     'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                     'points': points,
                                     'color': eva.get_color(points),
                                     'test_status': eva.test_status(points),
                                     'score': {'earned': points, 'total': 100}}})
            elif "Reusable" in x_principle:
                reusable.update({indi_code: {
                                'name': "[ERROR] - %s" % indi_code, 'msg': "Exception: %s" % e,
                                'points': points,
                                'color': eva.get_color(points),
                                'test_status': eva.test_status(points),
                                'score': {'earned': points, 'total': 100}}})
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
