import pytest

def test_insert_exitoso(motor_tmp):
    r = motor_tmp.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Ana", "edad": 20,
                  "carrera": "Medicina", "promedio": 4.5, "activo": True}
    })
    assert r["ok"] is True

def test_insert_pk_duplicada(motor_tmp):
    motor_tmp.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Ana", "edad": 20,
                  "carrera": "Medicina", "promedio": 4.5, "activo": True}
    })
    r = motor_tmp.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Luis", "edad": 22,
                  "carrera": "Derecho", "promedio": 3.8, "activo": True}
    })
    assert r["ok"] is False

def test_insert_campo_faltante(motor_tmp):
    r = motor_tmp.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "edad": 20,
                  "carrera": "Medicina", "promedio": 4.5, "activo": True}
    })
    assert r["ok"] is False

def test_insert_tipo_invalido(motor_tmp):
    r = motor_tmp.ejecutar({
        "cmd": "INSERT", "tabla": "t1",
        "datos": {"id": 1, "nombre": "Ana", "edad": "veinte",
                  "carrera": "Medicina", "promedio": 4.5, "activo": True}
    })
    assert r["ok"] is False

def test_insert_multiples(motor_tmp):
    for i in range(1, 11):
        r = motor_tmp.ejecutar({
            "cmd": "INSERT", "tabla": "t1",
            "datos": {"id": i, "nombre": f"Nombre{i}", "edad": 20,
                      "carrera": "Ing Sistemas", "promedio": 4.0, "activo": True}
        })
        assert r["ok"] is True, f"Fallo en id={i}: {r.get('mensaje')}"
