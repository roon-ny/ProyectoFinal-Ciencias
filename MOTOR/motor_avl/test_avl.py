# test_avl.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "MOTOR", "motor_avl"))

import unittest
from avl import ArbolAVL


class TestArbolAVL(unittest.TestCase):

    def setUp(self):
        self.avl = ArbolAVL()

    # insercion y busqueda basica
    def test_insertar_y_buscar(self):
        self.avl.insertar(5)
        self.assertEqual(self.avl.buscar(5), 5)

    def test_buscar_inexistente(self):
        self.avl.insertar(3)
        self.assertIsNone(self.avl.buscar(99))

    # el inorden siempre debe salir ordenado
    def test_inorden_ordenado(self):
        for n in [4, 2, 6, 1, 3, 5, 7]:
            self.avl.insertar(n)
        self.assertEqual(self.avl.recorrido_inorden(), [1, 2, 3, 4, 5, 6, 7])

    # el factor de balance en la raiz nunca puede salir de [-1, 1]
    def test_balance_valido(self):
        for n in [10, 20, 30, 40, 50, 25]:
            self.avl.insertar(n)
        self.assertIn(self.avl.obtener_factor_balance(), [-1, 0, 1])

    # despues de eliminar el nodo ya no debe estar
    def test_eliminar(self):
        for n in [5, 3, 7]:
            self.avl.insertar(n)
        self.avl.eliminar(3)
        self.assertIsNone(self.avl.buscar(3))
        self.assertEqual(self.avl.total_nodos(), 2)

    # la busqueda por rango solo devuelve lo que cae dentro
    def test_buscar_rango(self):
        for n in [1, 3, 5, 7, 9]:
            self.avl.insertar(n)
        self.assertEqual(self.avl.buscar_rango(3, 7), [3, 5, 7])

    # no inserta duplicados
    def test_no_duplicados(self):
        self.avl.insertar(10)
        self.avl.insertar(10)
        self.assertEqual(self.avl.total_nodos(), 1)


if __name__ == "__main__":
    unittest.main()
