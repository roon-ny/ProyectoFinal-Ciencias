# ProyectoFinal-Ciencias

# Motor de Base de Datos con Arbol AVL

**Realizado por:**

Juan Esteban Quintero — 20251020137
Johan Sebastian Candia — 20251020139
Ronaldo Andres Alvarado — 20251020122

---

Sistema gestor de bases de datos con interfaz de linea de comandos (REPL), persistencia en archivos JSON e indexacion mediante arboles AVL implementados desde cero.

---

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas (usa solo la biblioteca estandar: `json`, `os`, `re`, `math`)

---

## Estructura del proyecto

```
motor_avl/
├── avl.py              # Arbol AVL: estructura de datos en memoria
├── db.py               # Persistencia: lectura y escritura de archivos JSON
├── motor.py            # Motor: logica de negocio, coordina AVL y DB
├── parser.py           # Parser: convierte comandos de texto a dicts
├── visualizacion.py    # Visualizacion: imprime el arbol y sus metricas
├── main.py             # Main con REPL: interfaz de linea de comandos (punto de entrada)
└── data/               # Directorio creado automaticamente con los archivos JSON
```

Cada archivo tiene una unica responsabilidad. Ninguno conoce los detalles internos de los otros, solo su interfaz.

---

## Como ejecutar

```bash
python main.py
```

Al iniciar, el sistema reconstruye automaticamente los arboles AVL desde los archivos JSON existentes en `data/`.

---

## Comandos disponibles

### Gestion de tablas

```
CREATE TABLE nombre campo:tipo ...   Crear una tabla con esquema
DROP TABLE nombre                    Eliminar una tabla y sus datos
SHOW TABLES                          Listar todas las tablas existentes
```

**Tipos de datos soportados:** `int` `text` `real` `bool`

El primer campo declarado es siempre la clave primaria (debe ser `int`). Es el campo que indexa el arbol AVL.

### Operaciones CRUD

```
INSERT nombre campo=valor ...                    Insertar un registro
SELECT nombre                                    Ver todos los registros
SELECT nombre WHERE campo=valor                  Buscar por valor exacto
SELECT nombre WHERE campo>=min AND campo<=max    Buscar por rango (usa AVL)
UPDATE nombre SET campo=valor WHERE campo=valor  Actualizar registros
DELETE nombre WHERE campo=valor                  Eliminar registros
```

### Visualizacion del arbol AVL

```
SHOW TREE nombre        Ver el arbol AVL dibujado
SHOW TRAVERSAL nombre   Ver recorridos inorden, preorden y postorden
SHOW STATS nombre       Ver altura, balance y eficiencia del arbol
```

### Otros

```
COMANDOS    Ver todos los comandos con ejemplos
SALIR    Salir del programa
```

---

## Ejemplos de uso

### Crear una tabla

```
db> CREATE TABLE estudiantes id:int nombre:text edad:int carrera:text
  [OK] Tabla 'estudiantes' creada.
```

### Insertar registros

```
db> INSERT estudiantes id=1 nombre=Ana edad=20 carrera=Sistemas
  [OK] Registro insertado con ID: 1
  [AVL] Comparaciones: 0 | Nodos visitados: 1

db> INSERT estudiantes id=2 nombre=Luis edad=22 carrera=Industrial
  [OK] Registro insertado con ID: 2
  [AVL] Comparaciones: 1 | Nodos visitados: 2
```

### Buscar por clave primaria (O log n)

```
db> SELECT estudiantes WHERE id=1
  ID  NOMBRE  EDAD  CARRERA
  --  ------  ----  -------
  1   Ana     20    Sistemas

  1 registro(s) encontrado(s).
  [AVL] Comparaciones: 1 | Nodos visitados: 1
  [AVL] Camino: 1
```

### Buscar por rango (O log n + k)

```
db> SELECT estudiantes WHERE id>=2 AND id<=4
  ID  NOMBRE  EDAD  CARRERA
  --  ------  ----  -------
  2   Luis    22    Industrial
  3   Maria   19    Sistemas
  4   Carlos  21    Civil

  3 registro(s) encontrado(s).
  [AVL] Comparaciones: 3 | Nodos visitados: 3
```

### Actualizar

```
db> UPDATE estudiantes SET edad=21 WHERE id=1
  [OK] 1 registro(s) actualizado(s).
```

### Eliminar

```
db> DELETE estudiantes WHERE id=3
  [OK] Registro eliminado.
  [AVL] Comparaciones: 2 | Nodos visitados: 2
```

### Ver el arbol AVL

```
db> SHOW TREE estudiantes

=== Arbol AVL - estudiantes ===
        /-- 5
    /-- 4
2
    \-- 1
```

### Ver recorridos

```
db> SHOW TRAVERSAL estudiantes

=== Recorridos: estudiantes ===
  Inorden   (asc):  [1, 2, 4, 5]
  Preorden  (raiz): [2, 1, 4, 5]
  Postorden (hojas):[1, 5, 4, 2]
```

### Ver estadisticas

```
db> SHOW STATS estudiantes

==================================================
  ESTADISTICAS AVL - ESTUDIANTES
==================================================
  Total nodos:      4
  Altura actual:    3
  Balance raiz:     -1
  Altura optima:    3  (O(log 4) ≈ 3)
  Estado:           altura optima, el arbol esta perfectamente balanceado
==================================================
```

---

## Persistencia

Los datos se guardan en `data/<nombre_tabla>.json`. Cada archivo tiene el esquema y los registros juntos:

```json
{
  "esquema": {"id": "int", "nombre": "text", "edad": "int"},
  "registros": [
    {"id": 1, "nombre": "Ana", "edad": 20}
  ]
}
```

La escritura es **atomica**: el sistema escribe primero en un archivo `.tmp` y luego lo renombra con `os.replace()`. Si el programa falla en medio de una escritura, el archivo original queda intacto.

Al reiniciar, los arboles AVL se reconstruyen desde los archivos JSON en O(n log n).

---

## Arbol AVL: como funciona el indice

Cada tabla tiene su propio arbol AVL en memoria que indexa la clave primaria. El arbol garantiza O(log n) en insercion, busqueda y eliminacion porque se autobalancea despues de cada operacion mediante rotaciones.

| Operacion | Complejidad |
|---|---|
| INSERT | O(log n) |
| SELECT por clave primaria | O(log n) |
| SELECT por rango en PK | O(log n + k) |
| SELECT por otro campo | O(n) — scan lineal |
| UPDATE | O(n) busqueda + O(1) modificacion |
| DELETE | O(log n) en AVL + O(n) en lista |
| Reconstruccion al iniciar | O(n log n) |

Donde `n` es el total de registros y `k` es la cantidad de resultados en un rango.

### Rotaciones implementadas

- Rotacion simple izquierda (caso RR)
- Rotacion simple derecha (caso LL)
- Rotacion doble izquierda-derecha (caso LR)
- Rotacion doble derecha-izquierda (caso RL)

---

## Validaciones

| Capa | Que valida |
|---|---|
| `parser.py` | Sintaxis del comando, tipos declarados en esquema |
| `motor.py` | Tipos de datos contra el esquema, PK duplicada, tabla existente, campos requeridos |
| `db.py` | Existencia del archivo, integridad del JSON |

---

## Notas

- El arbol AVL se puede ver en cualquier momento con `SHOW TREE nombre`.
- La persistencia se demuestra cerrando con `SALIR`, volviendo a ejecutar `python main.py` y corriendo `SELECT nombre` o `SHOW TRAVERSAL nombre`.
- La busqueda por rango usa el recorrido inorden del arbol, lo que evita visitar nodos fuera del rango.
- No se puede cambiar la clave primaria con `UPDATE` para no romper el indice AVL.

---

## Datasets y pruebas

### Carga de datasets

Se incluyen dos scripts que cargan datos de prueba en la tabla `estudiantes`:

```bash
python scripts/load_small.py
```

Carga **15 registros** con nombres y carreras colombianos realistas (IDs 1–15, edades 18–26, promedios 3.0–5.0).

```bash
python scripts/load_medium.py
```

Carga **200 registros** con datos variados (15 carreras distintas, nombres generados aleatoriamente, misma estructura que el dataset pequeño).

Ambos scripts crean la tabla, eliminan datos previos si existían, insertan todos los registros y muestran un resumen al final.

### Suite de pruebas

Ejecutar todas las pruebas con:

```bash
pytest tests/ -v
```

| Archivo | Pruebas | Que verifica |
|---|---|---|
| `test_insert.py` | 5 | Insercion exitosa, PK duplicada, campo faltante, tipo invalido, insercion multiple |
| `test_select.py` | 5 | SELECT total, por PK, por rango AVL, sin resultados, tabla inexistente |
| `test_update.py` | 4 | UPDATE exitoso, sin coincidencias, tipo invalido, proteccion de PK |
| `test_delete.py` | 4 | DELETE exitoso, sin coincidencias, tabla inexistente, reinsercion de PK |
| `test_persistence.py` | 4 | Datos sobreviven reinicio, AVL se reconstruye, DROP persiste, UPDATE persiste |

Las **22 pruebas pasan en menos de 1 segundo**.
