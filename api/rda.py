import datetime
from api.evaluator import Evaluator
from api.digital_csic import Digital_CSIC
from api.dspace_7 import DSpace_7

from connexion import NoContent


def repo_object(body):
    repo = body.get("repo")
    item_id = body.get("id")
    if repo == "digital_csic":
        eva = Digital_CSIC(item_id)
    elif repo == "dspace_7":
        eva = DSpace_7(item_id)
    return eva


def f1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01m()
        findable = {'name': 'f1_01m', 'msg': "RDA_F1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }
        return findable, 200
    except Exception as e:
        return None, 201 

def f1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def f1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def f1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f1_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def f2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f2_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def f3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f3_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def f4_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_f4_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_03d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_03d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_04d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_04d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_05d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_05d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_1_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a1_2_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a1_2_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def a2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_a2_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i1_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i1_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i1_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i2_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i2_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_03m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def i3_04m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_i3_04m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_1_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_1_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_1_03m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_1_03m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_2_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_2_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_2_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_3_01m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_3_01d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_01d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_3_02m(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02m()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def r1_3_02d(body):
    eva = repo_object(body)
    try:
        points, msg = eva.rda_r1_3_02d()
        result = {'name': '', 'msg': "RDA_: " + msg, 'points': points, 'color': eva.get_color(points) }
        return result, 200
    except Exception as e:
        return None, 201

def all(body):
  eva = repo_object(body)
  findable = {}
  accessible = {}
  interoperable = {}
  reusable = {}
  result_points = 10
  num_of_tests = 10
  try:
    points, msg = eva.rda_f1_01m()
    print("Points: %i MSG = '%s'" % (points, msg))
    findable.update({'rda_f1_01m': {'msg': "RDA_F1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f1_01m')
    points, msg = eva.rda_f1_01d()
    findable.update({'rda_f1_01d':{'msg': "RDA_F1_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f1_01d')
    points, msg = eva.rda_f1_02m()
    findable.update({'rda_f1_02m': {'msg': "RDA_F1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f1_01m')
    points, msg = eva.rda_f1_02d()
    findable.update({'rda_f1_02d':{'msg': "RDA_F1_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f1_02d')
    points, msg = eva.rda_f2_01m()
    findable.update({'rda_f1_02d':{'msg': "RDA_F2_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f2_01m')
    points, msg = eva.rda_f3_01m()
    findable.update({'rda_f3_01m':{'msg': "RDA_F3_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f3_01m')
    points, msg = eva.rda_f4_01m()
    findable.update({'rda_f4_01m': {'msg': "RDA_F4_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_f4_01m')
  except Exception as e:
    print("Problem in 'F' tests")
    print(e)

  try:
    #Accessible tests
    points, msg = eva.rda_a1_01m()
    accessible.update({'rda_a1_01m': {'msg': "RDA_A1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_01m')
    points, msg = eva.rda_a1_02m()
    accessible.update({'rda_a1_02m': {'msg': "RDA_A1_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_02m')
    points, msg = eva.rda_a1_02d()
    accessible.update({'rda_a1_02d': {'msg': "RDA_A1_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_02d')
    points, msg = eva.rda_a1_03m()
    accessible.update({'rda_a1_03m': {'msg': "RDA_A1_03M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_03m')
    points, msg = eva.rda_a1_03d()
    accessible.update({'rda_a1_03d': {'msg': "RDA_A1_03D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_03d')
    points, msg = eva.rda_a1_04m()
    accessible.update({'rda_a1_04m': {'msg': "RDA_A1_04M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_04m')
    points, msg = eva.rda_a1_04d()
    accessible.update({'rda_a1_04d': {'msg': "RDA_A1_04D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_04d')
    points, msg = eva.rda_a1_05d()
    accessible.update({'rda_a1_05d': {'msg': "RDA_A1_05D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_05d')
    points, msg = eva.rda_a1_1_01m()
    accessible.update({'rda_a1_1_01m': {'msg': "RDA_A1.1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_1_01m')
    points, msg = eva.rda_a1_1_01d()
    accessible.update({'rda_a1_1_01d': {'msg': "RDA_A1.1_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_1_01d')
    points, msg = eva.rda_a1_2_02d()
    accessible.update({'rda_a1_2_02d': {'msg': "RDA_A1.2_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a1_2_02d')
    points, msg = eva.rda_a2_01m()
    accessible.update({'rda_a2_01m': {'msg': "RDA_A2_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_a2_01m')
  except Exception as e:
    print("Problem in 'A' tests")
    print(e)

  try:
    #Interoperable tests
    interoperable = {}
    points, msg = eva.rda_i1_01m()
    interoperable.update({'rda_i1_01m': {'msg': "RDA_I1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i1_01m')
    points, msg = eva.rda_i1_01d()
    interoperable.update({'rda_i1_01d': {'msg': "RDA_I1_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i1_01d')
    points, msg = eva.rda_i1_02m()
    interoperable.update({'rda_i1_02m': {'msg': "RDA_I1_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i1_02m')
    points, msg = eva.rda_i1_02d()
    interoperable.update({'rda_i1_02d': {'msg': "RDA_I1_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i1_02d')
    points, msg = eva.rda_i2_01m()
    interoperable.update({'rda_i2_01m': {'msg': "RDA_I2_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i2_01m')
    points, msg = eva.rda_i2_01d()
    interoperable.update({'rda_i2_01d': {'msg': "RDA_I2_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i2_01d')
    points, msg = eva.rda_i3_01m()
    interoperable.update({'rda_i3_01m': {'msg': "RDA_I3_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_01m')
    points, msg = eva.rda_i3_01d()
    interoperable.update({'rda_i3_01d': {'msg': "RDA_I3_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_01d')
    points, msg = eva.rda_i3_02m()
    interoperable.update({'rda_i3_02m': {'msg': "RDA_I3_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_02m')
    points, msg = eva.rda_i3_02d()
    interoperable.update({'rda_i3_02d': {'msg': "RDA_I3_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_02d')
    points, msg = eva.rda_i3_03m()
    interoperable.update({'rda_i3_03m': {'msg': "RDA_I3_03M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_03m')
    points, msg = eva.rda_i3_04m()
    interoperable.update({'rda_i3_04m': {'msg': "RDA_I3_04M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_i3_04m')
  except Exception as e:
    print("Problem in 'I' tests")
    print(e)


  try:
    points, msg = eva.rda_r1_01m()
    result_points = result_points + points
    reusable.update({'rda_r1_01m': {'msg': "RDA_R1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_01m')
    points, msg = eva.rda_r1_1_01m()
    result_points = result_points + points
    reusable.update({'rda_r1_1_01m': {'msg': "RDA_R1.1_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_1_01m')
    points, msg = eva.rda_r1_1_02m()
    result_points = result_points + points
    reusable.update({'rda_r1_1_02m': {'msg': "RDA_R1.1_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_1_02m')
    points, msg = eva.rda_r1_1_03m()
    result_points = result_points + points
    reusable.update({'rda_r1_1_03m': {'msg': "RDA_R1.1_03M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_1_03m')
    points, msg = eva.rda_r1_2_01m()
    result_points = result_points + points
    reusable.update({'rda_r1_2_01m': {'msg': "RDA_R1.2_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_2_01m')
    points, msg = eva.rda_r1_2_02m()
    result_points = result_points + points
    reusable.update({'rda_r1_2_02m': {'msg': "RDA_R1.2_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_2_02m')
    points, msg = eva.rda_r1_3_01m()
    result_points = result_points + points
    reusable.update({'rda_r1_3_01m': {'msg': "RDA_R1.3_01M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_3_01m')
    points, msg = eva.rda_r1_3_01d()
    result_points = result_points + points
    reusable.update({'rda_r1_3_01': {'msg': "RDA_R1.3_01D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_3_01')
    points, msg = eva.rda_r1_3_02m()
    result_points = result_points + points
    reusable.update({'rda_r1_3_02m': {'msg': "RDA_R1.3_02M: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_3_02m')
    points, msg = eva.rda_r1_3_02d()
    result_points = result_points + points
    reusable.update({'rda_r1_3_02d': {'msg': "RDA_R1.3_02D: " + msg, 'points': points, 'color': eva.get_color(points) }})
    print("Test %s performed" % 'rda_r1_3_02d')
    result_points = round((result_points / num_of_tests), 2)
  except Exception as e:
    print("Problem in 'R' tests")
    print(e)

  result = {'findable': findable, 'accessible': accessible, 'interoperable': interoperable, 'reusable': reusable}
  return result, 200

def delete(id_):
    id_ = int(id_)
    if pets.get(id_) is None:
        return NoContent, 404
    del pets[id_]
    return NoContent, 204


def get(name):
    findable = {'name': name, 'msg': "Test %s has been performed" % name, 'points': 100, 'color': "green"}
    return findable


def search(limit=100):
    # NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return get()
