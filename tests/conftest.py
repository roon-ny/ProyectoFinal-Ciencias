import sys
import os
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
    "ProyectoFinalCiencias-master", "MOTOR", "motor_avl"))

from motor import Motor
from db import DB

ESQUEMA_T1 = {
    "id": "int",
    "nombre": "text",
    "edad": "int",
    "carrera": "text",
    "promedio": "real",
    "activo": "bool",
}

def crear_motor(directorio):
    m = Motor.__new__(Motor)
    m.db = DB(directorio)
    m.indices = {}
    m._cargar_indices()
    return m

@pytest.fixture
def tmpdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

@pytest.fixture
def motor_tmp(tmpdir):
    m = crear_motor(tmpdir)
    m.ejecutar({"cmd": "CREATE_TABLE", "tabla": "t1", "esquema": ESQUEMA_T1})
    return m
