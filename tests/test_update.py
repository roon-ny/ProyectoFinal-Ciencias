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

def test_update_exitoso(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "UPDATE", "tabla": "t1",
        "set": {"edad": 99},
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r["ok"] is True
    assert r["afectados"] == 1

    r2 = motor_con_5.ejecutar({
        "cmd": "SELECT", "tabla": "t1",
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r2["datos"][0]["edad"] == 99

def test_update_sin_resultados(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "UPDATE", "tabla": "t1",
        "set": {"edad": 99},
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 999}
    })
    assert r["ok"] is False
    assert "no se encontro" in r["mensaje"]

def test_update_tipo_invalido(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "UPDATE", "tabla": "t1",
        "set": {"edad": "abc"},
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r["ok"] is False

def test_update_intento_cambiar_pk(motor_con_5):
    r = motor_con_5.ejecutar({
        "cmd": "UPDATE", "tabla": "t1",
        "set": {"id": 99},
        "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}
    })
    assert r["ok"] is False
