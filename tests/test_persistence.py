import sys
import os

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


def test_datos_sobreviven_reinicio(tmpdir):
    mA = crear_motor(tmpdir)
    mA.ejecutar({"cmd": "CREATE_TABLE", "tabla": "t1", "esquema": ESQUEMA_T1})
    for i in range(1, 6):
        mA.ejecutar({
            "cmd": "INSERT", "tabla": "t1",
            "datos": {"id": i, "nombre": f"Nombre{i}", "edad": 20 + i,
                      "carrera": "Ing Sistemas", "promedio": 4.0, "activo": True}
        })

    mB = crear_motor(tmpdir)
    r = mB.ejecutar({"cmd": "SELECT", "tabla": "t1", "where": None})
    assert r["ok"] is True
    assert len(r["datos"]) == 5


def test_arbol_avl_se_reconstruye(tmpdir):
    mA = crear_motor(tmpdir)
    mA.ejecutar({"cmd": "CREATE_TABLE", "tabla": "t1", "esquema": ESQUEMA_T1})
    for v in [1, 5, 3, 7, 2]:
        mA.ejecutar({
            "cmd": "INSERT", "tabla": "t1",
            "datos": {"id": v, "nombre": f"N{v}", "edad": 20,
                      "carrera": "Ing Sistemas", "promedio": 3.5, "activo": True}
        })

    mB = crear_motor(tmpdir)
    r = mB.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "rango", "campo": "id", "min": 3, "max": 7}
    })
    assert r["ok"] is True
    ids = [reg["id"] for reg in r["datos"]]
    assert sorted(ids) == [3, 5, 7]


def test_tabla_eliminada_no_persiste(tmpdir):
    mA = crear_motor(tmpdir)
    mA.ejecutar({"cmd": "CREATE_TABLE", "tabla": "t1", "esquema": ESQUEMA_T1})
    mA.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Test", "edad": 20,
                  "carrera": "Medicina", "promedio": 4.0, "activo": True}
    })
    mA.ejecutar({"cmd": "DROP_TABLE", "tabla": "t1"})

    mB = crear_motor(tmpdir)
    r = mB.ejecutar({"cmd": "SELECT", "tabla": "t1", "where": None})
    assert r["ok"] is False


def test_update_persiste(tmpdir):
    mA = crear_motor(tmpdir)
    mA.ejecutar({"cmd": "CREATE_TABLE", "tabla": "t1", "esquema": ESQUEMA_T1})
    mA.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Original", "edad": 20,
                  "carrera": "Medicina", "promedio": 4.0, "activo": True}
    })
    mA.ejecutar({
        "cmd": "UPDATE", "tabla": "t1",
        "set": {"edad": 99},
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })

    mB = crear_motor(tmpdir)
    r = mB.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r["ok"] is True
    assert r["datos"][0]["edad"] == 99
