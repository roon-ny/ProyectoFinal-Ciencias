import pytest

@pytest.fixture
def motor_con_10(motor_tmp):
    for i in range(1, 11):
        motor_tmp.ejecutar({
            "cmd": "INSERT", "tabla": "t1",
            "datos": {"id": i, "nombre": f"Nombre{i}", "edad": 20 + i,
                      "carrera": "Ing Sistemas", "promedio": 4.0, "activo": True}
        })
    return motor_tmp

def test_select_todos(motor_con_10):
    r = motor_con_10.ejecutar({"cmd": "SELECT", "tabla": "t1", "where": None})
    assert r["ok"] is True
    assert len(r["datos"]) == 10

def test_select_por_pk(motor_con_10):
    r = motor_con_10.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 5}
    })
    assert r["ok"] is True
    assert len(r["datos"]) == 1
    assert r["datos"][0]["id"] == 5
    assert r["datos"][0]["nombre"] == "Nombre5"

def test_select_rango(motor_con_10):
    r = motor_con_10.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "rango", "campo": "id", "min": 3, "max": 7}
    })
    assert r["ok"] is True
    assert len(r["datos"]) == 5

def test_select_sin_resultados(motor_con_10):
    r = motor_con_10.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 99}
    })
    assert r["ok"] is True
    assert r["datos"] == []

def test_select_tabla_inexistente(motor_tmp):
    r = motor_tmp.ejecutar({
        "cmd": "SELECT", "tabla": "no_existe", "where": None
    })
    assert r["ok"] is False
