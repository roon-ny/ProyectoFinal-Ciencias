import pytest

@pytest.fixture
def motor_con_5(motor_tmp):
    for i in range(1, 6):
        motor_tmp.ejecutar({
            "cmd": "INSERT", "tabla": "t1",
            "datos": {"id": i, "nombre": f"Nombre{i}", "edad": 20 + i,
                      "carrera": "Ing Sistemas", "promedio": 4.0, "activo": True}
        })
    return motor_tmp

def test_delete_exitoso(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "DELETE", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 3}
    })
    assert r["ok"] is True

    r2 = motor_con_5.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 3}
    })
    assert r2["datos"] == []

def test_delete_inexistente(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "DELETE", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 999}
    })
    assert r["ok"] is False
    assert "no se encontro" in r["mensaje"]

def test_delete_tabla_inexistente(motor_tmp):
    r = motor_tmp.ejecutar({
        "cmd": "DELETE", "tabla": "no_existe",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r["ok"] is False

def test_delete_y_reinsertar(motor_con_5):
    motor_con_5.ejecutar({
        "cmd": "DELETE", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    r = motor_con_5.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Reinsertado", "edad": 25,
                  "carrera": "Medicina", "promedio": 4.0, "activo": True}
    })
    assert r["ok"] is True
