# test_motor.py
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "MOTOR", "motor_avl"))

import unittest
from motor import Motor
from db import DB


class TestMotor(unittest.TestCase):

    def setUp(self):
        # directorio temporal para que cada prueba arranque limpia
        self.tmp = tempfile.mkdtemp()
        self.motor = Motor.__new__(Motor)
        self.motor.db = DB(self.tmp)
        self.motor.indices = {}
        self.motor._cargar_indices()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _crear(self):
        return self.motor.ejecutar({
            "cmd": "CREATE_TABLE",
            "tabla": "test",
            "esquema": {"id": "int", "nombre": "text"}
        })

    def _insertar(self, id_, nombre):
        return self.motor.ejecutar({
            "cmd": "INSERT",
            "tabla": "test",
            "datos": {"id": id_, "nombre": nombre}
        })

    # crear tabla
    def test_crear_tabla(self):
        r = self._crear()
        self.assertTrue(r["ok"])

    # no se puede crear la misma tabla dos veces
    def test_crear_tabla_duplicada(self):
        self._crear()
        r = self._crear()
        self.assertFalse(r["ok"])

    # insertar y luego buscar por PK
    def test_insertar_y_seleccionar(self):
        self._crear()
        self._insertar(1, "Ana")
        r = self.motor.ejecutar({
            "cmd": "SELECT", "tabla": "test",
            "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
        })
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["datos"]), 1)
        self.assertEqual(r["datos"][0]["nombre"], "Ana")

    # actualizar un campo
    def test_update(self):
        self._crear()
        self._insertar(1, "Ana")
        r = self.motor.ejecutar({
            "cmd": "UPDATE", "tabla": "test",
            "set": {"nombre": "Luis"},
            "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
        })
        self.assertTrue(r["ok"])
        self.assertEqual(r["afectados"], 1)

    # eliminar un registro
    def test_delete(self):
        self._crear()
        self._insertar(1, "Ana")
        self._insertar(2, "Luis")
        self.motor.ejecutar({
            "cmd": "DELETE", "tabla": "test",
            "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
        })
        r = self.motor.ejecutar({
            "cmd": "SELECT", "tabla": "test",
            "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
        })
        self.assertEqual(r["datos"], [])

    # no se puede insertar PK duplicada
    def test_pk_duplicada(self):
        self._crear()
        self._insertar(1, "Ana")
        r = self._insertar(1, "Luis")
        self.assertFalse(r["ok"])

    # busqueda por rango sobre la PK
    def test_select_rango(self):
        self._crear()
        for i, n in [(1,"A"), (2,"B"), (3,"C"), (4,"D")]:
            self._insertar(i, n)
        r = self.motor.ejecutar({
            "cmd": "SELECT", "tabla": "test",
            "where": {"tipo": "rango", "campo": "id", "min": 2, "max": 3}
        })
        self.assertEqual(len(r["datos"]), 2)


if __name__ == "__main__":
    unittest.main()
