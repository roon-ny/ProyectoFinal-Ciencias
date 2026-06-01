# motor.py
# Responsabilidad unica: coordinar el AVL y la DB para ejecutar comandos.
# Recibe dicts del Parser, llama a DB y ArbolAVL, devuelve dicts al REPL.
# Aqui vive toda la logica de negocio: validar tipos, manejar PK, etc.

from avl import ArbolAVL
from db import DB, ErrorTabla

# esta excepcion es como nuestro salvavidas para cuando intentan hacer algo ilegal a nivel de logica,
# como meter un texto donde va un numero o repetir un id que ya existe
class ErrorMotor(Exception):
    """Se lanza cuando hay un error de logica: tipo incorrecto, PK duplicada, etc."""
    pass


# Que tipo Python corresponde a cada tipo del esquema
TIPOS_PYTHON = {
    "int":  int,
    "text": str,
    "real": float,
    "bool": bool,
}

# este es el verdadero jefe de la operacion, el que coge las instrucciones ya traducidas por el parser
# y pone a trabajar a la base de datos (el disco) y a los arboles avl (la memoria) en equipo
class Motor:
    """
    Orquesta la DB y los arboles AVL para ejecutar cualquier comando.

    Cada tabla tiene su propio ArbolAVL en self.indices.
    Al iniciar, reconstruye los arboles leyendo los archivos JSON existentes.

    Regla de clave primaria:
      El primer campo del esquema es siempre la clave primaria (PK).
      Debe ser de tipo int. El AVL indexa por ese campo.
    """

    def __init__(self):
        self.db = DB()
        self.indices = {}           # {"nombre_tabla": ArbolAVL}
        self._cargar_indices()      # reconstruir arboles desde disco al iniciar

    # aca es donde la magia pasa al prender el sistema: leemos todos los datos guardados en el disco
    # y volvemos a armar los arboles avl en memoria para que las busquedas sigan siendo rapidas
    def _cargar_indices(self):
        """
        Reconstruye el arbol AVL de cada tabla al iniciar el sistema.
        Lee los registros del JSON y los inserta en el arbol en memoria.
        Complejidad: O(n log n) por tabla.
        """
        for tabla in self.db.listar_tablas():
            self.indices[tabla] = ArbolAVL()
            pk = self._campo_pk(tabla)
            for registro in self.db.leer_registros(tabla):
                self.indices[tabla].insertar(registro[pk])

    def _campo_pk(self, tabla):
        """Devuelve el nombre del primer campo del esquema (la clave primaria)."""
        esquema = self.db.obtener_esquema(tabla)
        return list(esquema.keys())[0]

    # ──────────────────────────────────────────────────────────────
    #  Punto de entrada principal
    # ──────────────────────────────────────────────────────────────

    # este es el portero que recibe los diccionarios limpios del parser y decide a cual funcion delegar el trabajo,
    # y de paso atrapa cualquier error para que la consola no se muera y solo muestre un mensaje de advertencia
    def ejecutar(self, comando):
        """
        Recibe el dict del Parser y devuelve un dict de resultado para el REPL.
        Todos los errores quedan atrapados aqui para que el REPL solo reciba ok/error.
        """
        cmd = comando["cmd"]
        try:
            if cmd == "CREATE_TABLE":    return self._crear_tabla(comando)
            if cmd == "DROP_TABLE":      return self._borrar_tabla(comando)
            if cmd == "SHOW_TABLES":     return self._listar_tablas()
            if cmd == "INSERT":          return self._insertar(comando)
            if cmd == "SELECT":          return self._seleccionar(comando)
            if cmd == "UPDATE":          return self._actualizar(comando)
            if cmd == "DELETE":          return self._eliminar(comando)
            if cmd == "SHOW_TREE":       return self._show_tree(comando)
            if cmd == "SHOW_TRAVERSAL":  return self._show_traversal(comando)
            if cmd == "SHOW_STATS":      return self._show_stats(comando)
            return {"ok": False, "mensaje": f"comando '{cmd}' no implementado"}
        except (ErrorMotor, ErrorTabla) as e:
            return {"ok": False, "mensaje": str(e)}

    # ──────────────────────────────────────────────────────────────
    #  Gestion de tablas
    # ──────────────────────────────────────────────────────────────

    # cuando creamos una tabla nos ponemos estrictos exigiendo que el primer campo sea un numero entero,
    # porque si no el arbol avl se vuelve loco y no tiene como ordenar ni indexar los datos despues
    def _crear_tabla(self, comando):
        tabla   = comando["tabla"]
        esquema = comando["esquema"]

        # el primer campo es la PK y debe ser int para poder indexarlo en el AVL
        pk = list(esquema.keys())[0]
        if esquema[pk] != "int":
            raise ErrorMotor(
                f"el primer campo '{pk}' debe ser de tipo int, "
                "es la clave primaria que indexa el arbol AVL"
            )

        self.db.crear_tabla(tabla, esquema)
        self.indices[tabla] = ArbolAVL()
        return {"ok": True, "tipo": "tabla_creada", "tabla": tabla}

    def _borrar_tabla(self, comando):
        tabla = comando["tabla"]
        self._verificar_tabla(tabla)
        self.db.eliminar_tabla(tabla)
        del self.indices[tabla]
        return {"ok": True, "tipo": "tabla_eliminada", "tabla": tabla}

    def _listar_tablas(self):
        return {"ok": True, "tipo": "show_tables", "tablas": self.db.listar_tablas()}

    # ──────────────────────────────────────────────────────────────
    #  INSERT
    # ──────────────────────────────────────────────────────────────

    # antes de meter un registro nuevo verificamos dos cosas clave: que vengan todos los campos obligatorios
    # y que la llave primaria no exista ya en el arbol, para no sobrescribir ni dañar el indice
    def _insertar(self, comando):
        tabla = comando["tabla"]
        datos = comando["datos"]

        self._verificar_tabla(tabla)
        esquema = self.db.obtener_esquema(tabla)
        pk      = self._campo_pk(tabla)

        # todos los campos del esquema deben estar presentes
        for campo in esquema:
            if campo not in datos:
                raise ErrorMotor(
                    f"falta el campo '{campo}' en el INSERT. "
                    f"Los campos de la tabla son: {list(esquema.keys())}"
                )

        datos_validados = self._validar_tipos(datos, esquema)
        pk_valor = datos_validados[pk]

        # verificar que no exista ya un registro con esa PK
        if self.indices[tabla].buscar(pk_valor) is not None:
            raise ErrorMotor(
                f"ya existe un registro con {pk}={pk_valor}"
            )

        # guardar en disco y luego actualizar el arbol
        registros = self.db.leer_registros(tabla)
        registros.append(datos_validados)
        self.db.guardar_registros(tabla, registros)
        self.indices[tabla].insertar(pk_valor)

        return {
            "ok":      True,
            "tipo":    "insercion",
            "id":      pk_valor,
            "info_avl": self._info_avl(tabla),
        }

    # ──────────────────────────────────────────────────────────────
    #  SELECT
    # ──────────────────────────────────────────────────────────────

    # aca es donde brilla el AVL: si la condicion del select es sobre la llave primaria usa el arbol para ir rapidisimo,
    # pero si buscas por otro campo le toca hacer la de revisar registro por registro de manera lineal
    def _seleccionar(self, comando):
        tabla = comando["tabla"]
        where = comando.get("where")

        self._verificar_tabla(tabla)
        pk = self._campo_pk(tabla)

        # sin WHERE: devolver todos los registros
        if where is None:
            registros = self.db.leer_registros(tabla)
            return {"ok": True, "tipo": "seleccion", "datos": registros, "info_avl": None}

        # WHERE rango sobre la PK → AVL buscar_rango O(log n + k)
        if where["tipo"] == "rango" and where["campo"] == pk:
            ids_encontrados = self.indices[tabla].buscar_rango(where["min"], where["max"])
            registros = self.db.leer_registros(tabla)
            datos = [r for r in registros if r[pk] in ids_encontrados]
            return {
                "ok":      True,
                "tipo":    "seleccion",
                "datos":   datos,
                "info_avl": self._info_avl(tabla),
            }

        # WHERE igualdad sobre la PK → AVL buscar O(log n)
        if where["tipo"] == "simple" and where["campo"] == pk and where["op"] == "=":
            encontrado = self.indices[tabla].buscar(where["valor"])
            if encontrado is None:
                return {"ok": True, "tipo": "seleccion", "datos": [], "info_avl": self._info_avl(tabla)}
            registros = self.db.leer_registros(tabla)
            datos = [r for r in registros if r[pk] == encontrado]
            return {
                "ok":      True,
                "tipo":    "seleccion",
                "datos":   datos,
                "info_avl": self._info_avl(tabla),
            }

        # WHERE sobre otro campo → scan lineal (no es la PK, no hay AVL disponible)
        registros = self.db.leer_registros(tabla)
        datos = [r for r in registros if self._cumple_condicion(r, where)]
        return {"ok": True, "tipo": "seleccion", "datos": datos, "info_avl": None}

    # ──────────────────────────────────────────────────────────────
    #  UPDATE
    # ──────────────────────────────────────────────────────────────

    # aca actualizamos los datos pero bloqueamos a toda costa que traten de cambiar la llave primaria,
    # porque hacer eso nos desbalancearia todo el arbol y perderiamos la referencia del indice
    def _actualizar(self, comando):
        tabla   = comando["tabla"]
        nuevos  = comando["set"]
        where   = comando["where"]

        self._verificar_tabla(tabla)
        esquema = self.db.obtener_esquema(tabla)
        pk      = self._campo_pk(tabla)

        # no se puede cambiar la PK porque romperia el indice AVL
        if pk in nuevos:
            raise ErrorMotor(
                f"no se puede cambiar la clave primaria '{pk}' con UPDATE. "
                "Elimina el registro e inserta uno nuevo si necesitas cambiar el ID"
            )

        # validar solo los campos que vienen en SET (los otros no se tocan)
        nuevos_validados = self._validar_tipos(nuevos, esquema, solo_presentes=True)

        registros = self.db.leer_registros(tabla)
        afectados = 0
        for r in registros:
            if self._cumple_condicion(r, where):
                r.update(nuevos_validados)
                afectados += 1

        if afectados == 0:
            return {"ok": False, "mensaje": "no se encontro ningun registro con esa condicion"}

        self.db.guardar_registros(tabla, registros)
        return {"ok": True, "tipo": "actualizacion", "afectados": afectados}

    # ──────────────────────────────────────────────────────────────
    #  DELETE
    # ──────────────────────────────────────────────────────────────

    # la logica aca es iterar sobre todo, guardar solo los que NO cumplen la condicion (los que sobreviven),
    # y a los que matamos los sacamos tambien del arbol avl para que todo quede limpio
    def _eliminar(self, comando):
        tabla = comando["tabla"]
        where = comando["where"]

        self._verificar_tabla(tabla)
        pk = self._campo_pk(tabla)

        registros   = self.db.leer_registros(tabla)
        restantes   = []
        pks_borradas = []

        for r in registros:
            if self._cumple_condicion(r, where):
                pks_borradas.append(r[pk])
            else:
                restantes.append(r)

        if not pks_borradas:
            return {"ok": False, "mensaje": "no se encontro ningun registro con esa condicion"}

        # primero guardar en disco, luego actualizar el arbol
        self.db.guardar_registros(tabla, restantes)
        for pk_val in pks_borradas:
            self.indices[tabla].eliminar(pk_val)

        return {
            "ok":      True,
            "tipo":    "eliminacion",
            "info_avl": self._info_avl(tabla),
        }

    # ──────────────────────────────────────────────────────────────
    #  SHOW TREE / TRAVERSAL / STATS
    # ──────────────────────────────────────────────────────────────

    def _show_tree(self, comando):
        tabla = comando["tabla"]
        self._verificar_tabla(tabla)
        return {
            "ok":    True,
            "tipo":  "show_tree",
            "tabla": tabla,
            "arbol": self.indices[tabla],       # objeto AVL completo, visualizacion usa .raiz
        }

    def _show_traversal(self, comando):
        tabla = comando["tabla"]
        self._verificar_tabla(tabla)
        return {
            "ok":    True,
            "tipo":  "show_traversal",
            "tabla": tabla,
            "arbol": self.indices[tabla],       # visualizacion llama recorrido_inorden() etc.
        }

    def _show_stats(self, comando):
        tabla = comando["tabla"]
        self._verificar_tabla(tabla)
        avl = self.indices[tabla]
        return {
            "ok":    True,
            "tipo":  "show_stats",
            "tabla": tabla,
            "stats": {
                "total_nodos":  avl.total_nodos(),
                "altura":       avl.obtener_altura(),
                "balance_raiz": avl.obtener_factor_balance(),
            },
        }

    # ──────────────────────────────────────────────────────────────
    #  Helpers privados
    # ──────────────────────────────────────────────────────────────

    def _verificar_tabla(self, tabla):
        """Lanza ErrorMotor si la tabla no existe."""
        if not self.db.tabla_existe(tabla):
            raise ErrorMotor(f"la tabla '{tabla}' no existe. Usa SHOW TABLES para ver las disponibles")

    def _info_avl(self, tabla):
        """Empaca las metricas de la ultima operacion AVL para devolverlas al REPL."""
        avl = self.indices[tabla]
        return {
            "comparaciones":   avl.get_ultima_busqueda_comparaciones(),
            "nodos_visitados": avl.get_ultima_busqueda_nodos(),
            "recorrido":       avl.get_ultima_busqueda_recorrido(),
        }

    # esta funcion nos asegura de que no nos vayan a meter letras donde van numeros enteros o decimales,
    # aunque somos un poquito flexibles: si esperan un real y mandan un entero, lo convertimos calladitos
    def _validar_tipos(self, datos, esquema, solo_presentes=False):
        """
        Verifica que cada campo tenga el tipo correcto segun el esquema.
        solo_presentes=True se usa en UPDATE: solo valida los campos que vienen.

        Para 'real', acepta enteros tambien (3 es un real valido, se convierte a 3.0).
        """
        validados = {}
        campos_a_revisar = datos.keys() if solo_presentes else esquema.keys()

        for campo in campos_a_revisar:
            if campo not in datos:
                continue

            valor         = datos[campo]
            tipo_esperado = esquema.get(campo)

            if tipo_esperado is None:
                raise ErrorMotor(
                    f"el campo '{campo}' no existe en el esquema de la tabla"
                )

            # int se acepta como real y se convierte automaticamente
            if tipo_esperado == "real" and isinstance(valor, int) and not isinstance(valor, bool):
                valor = float(valor)

            tipo_python = TIPOS_PYTHON[tipo_esperado]
            if not isinstance(valor, tipo_python):
                raise ErrorMotor(
                    f"tipo incorrecto en '{campo}': se esperaba {tipo_esperado} "
                    f"pero llego '{valor}' ({type(valor).__name__})"
                )

            validados[campo] = valor

        return validados

    # un validador super sencillo pero necesario para saber si un registro especifico hace match con lo que pidio
    # el usuario en la clausula where, ya sea una condicion simple o un rango
    def _cumple_condicion(self, registro, where):
        """
        Dice si un registro cumple la condicion WHERE.
        Soporta: = != > < >= <=  y tambien rangos.
        """
        campo = where["campo"]
        if campo not in registro:
            return False

        val_reg = registro[campo]

        if where["tipo"] == "rango":
            return where["min"] <= val_reg <= where["max"]

        # condicion simple
        op        = where["op"]
        val_where = where["valor"]

        if op == "=":   return val_reg == val_where
        if op == "!=":  return val_reg != val_where
        if op == ">":   return val_reg >  val_where
        if op == "<":   return val_reg <  val_where
        if op == ">=":  return val_reg >= val_where
        if op == "<=":  return val_reg <= val_where
        return False
