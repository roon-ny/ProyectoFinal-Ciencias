# parser.py
# Responsabilidad unica: convertir una linea de texto en un dict estructurado.
# No valida tipos contra el esquema, no toca el AVL, no lee archivos.
# Solo analiza la sintaxis y dice "esto es un INSERT a la tabla X con estos datos".

import re

# Tipos que el sistema reconoce en CREATE TABLE
TIPOS_VALIDOS = {"int", "text", "real", "bool"}


# esta clase es como que para manejar los errores cuando uno escribe mal un comando, un poco para avisar que la embarramos,
# por lo general salta y corta el proceso diciendo que la sintaxis no cuadra para que uno corrija
class ComandoInvalido(Exception):
    """Se lanza cuando el texto no forma un comando valido."""
    pass


# aca es donde cogemos el texto que mete el usuario y lo desarmamos para entender que quiere hacer, como que lo traducimos,
# y tambien armamos un diccionario bien organizado con las instrucciones listas para que el motor las pueda ejecutar sin enredarse
class Parser:
    """
    Toma una linea como string y devuelve un dict con el comando y sus argumentos.

    Cada metodo _parsear_X maneja un comando distinto y devuelve siempre un dict.
    Si la sintaxis esta mal, lanza ComandoInvalido con un mensaje claro.

    Comandos soportados:
      CREATE TABLE nombre campo:tipo ...
      DROP TABLE nombre
      SHOW TABLES | SHOW TREE nombre | SHOW TRAVERSAL nombre | SHOW STATS nombre
      INSERT nombre campo=valor ...
      SELECT nombre [WHERE campo=valor | campo>=min AND campo<=max]
      UPDATE nombre SET campo=valor WHERE campo=valor
      DELETE nombre WHERE campo=valor
    """

    # este es el punto de entrada principal donde llega el string crudo y lo partimos por espacios para ver cual es la primera palabra,
    # asi que dependiendo de si dice create o insert o lo que sea lo mandamos a otra funcion mas especifica para que lo procese bien
    def parsear(self, linea):
        """Punto de entrada. Recibe el string del usuario y devuelve el dict del comando."""
        tokens = linea.strip().split()
        if not tokens:
            raise ComandoInvalido("el comando esta vacio")

        cmd = tokens[0].upper()

        if cmd == "CREATE":
            return self._parsear_create(tokens)
        elif cmd == "DROP":
            return self._parsear_drop(tokens)
        elif cmd == "SHOW":
            return self._parsear_show(tokens)
        elif cmd == "INSERT":
            return self._parsear_insert(linea, tokens)
        elif cmd == "SELECT":
            return self._parsear_select(linea, tokens)
        elif cmd == "UPDATE":
            return self._parsear_update(linea, tokens)
        elif cmd == "DELETE":
            return self._parsear_delete(linea, tokens)
        else:
            raise ComandoInvalido(
                f"'{tokens[0]}' no es un comando reconocido. Escribe HELP para ver los disponibles"
            )

    # ──────────────────────────────────────────────────────────────
    #  CREATE TABLE nombre campo:tipo campo:tipo ...
    #
    #  Resultado:
    #    {"cmd": "CREATE_TABLE", "tabla": "productos",
    #     "esquema": {"id": "int", "nombre": "text", "precio": "real"}}
    # ──────────────────────────────────────────────────────────────
    # por lo menos aca revisamos que la instruccion tenga el formato correcto para crear una tabla con sus columnas y tipos de datos,
    # como que validamos que diga table y que los campos tengan dos puntos para separar el nombre del tipo y si no lanzamos un error
    def _parsear_create(self, tokens):
        if len(tokens) < 2 or tokens[1].upper() != "TABLE":
            raise ComandoInvalido("sintaxis: CREATE TABLE nombre campo:tipo ...")
        if len(tokens) < 3:
            raise ComandoInvalido("falta el nombre de la tabla")
        if len(tokens) < 4:
            raise ComandoInvalido(
                "la tabla necesita al menos un campo, ejemplo: id:int nombre:text"
            )

        nombre_tabla = tokens[2]
        esquema = {}

        for token in tokens[3:]:
            if ":" not in token:
                raise ComandoInvalido(
                    f"'{token}' no tiene el formato campo:tipo, ejemplo: edad:int"
                )
            campo, tipo = token.split(":", 1)
            if not campo:
                raise ComandoInvalido("el nombre del campo no puede estar vacio")
            if tipo not in TIPOS_VALIDOS:
                raise ComandoInvalido(
                    f"tipo '{tipo}' no es valido, los tipos permitidos son: {', '.join(TIPOS_VALIDOS)}"
                )
            esquema[campo] = tipo

        return {"cmd": "CREATE_TABLE", "tabla": nombre_tabla, "esquema": esquema}

    # ──────────────────────────────────────────────────────────────
    #  DROP TABLE nombre
    #
    #  Resultado:
    #    {"cmd": "DROP_TABLE", "tabla": "productos"}
    # ──────────────────────────────────────────────────────────────
    # aca la idea es super sencilla porque solo necesitamos confirmar que diga table y sacar el nombre de la tabla que vamos a borrar,
    # un poco para evitar daños verificamos que vengan las palabras completas antes de mandar la orden de eliminar todo
    def _parsear_drop(self, tokens):
        if len(tokens) < 2 or tokens[1].upper() != "TABLE":
            raise ComandoInvalido("sintaxis: DROP TABLE nombre")
        if len(tokens) < 3:
            raise ComandoInvalido("falta el nombre de la tabla a eliminar")

        return {"cmd": "DROP_TABLE", "tabla": tokens[2]}

    # ──────────────────────────────────────────────────────────────
    #  SHOW TABLES
    #  SHOW TREE nombre
    #  SHOW TRAVERSAL nombre
    #  SHOW STATS nombre
    #
    #  Resultado:
    #    {"cmd": "SHOW_TABLES"}
    #    {"cmd": "SHOW_TREE", "tabla": "productos"}
    # ──────────────────────────────────────────────────────────────
    # esta parte es para cuando queremos ver cosas que ya estan guardadas como las tablas o el arbol o las estadisticas,
    # por lo general revisa cual es la segunda palabra para saber exactamente que mostrar y si pide algo del arbol exige el nombre de la tabla
    def _parsear_show(self, tokens):
        if len(tokens) < 2:
            raise ComandoInvalido(
                "sintaxis: SHOW TABLES | SHOW TREE nombre | SHOW TRAVERSAL nombre | SHOW STATS nombre"
            )

        sub = tokens[1].upper()

        if sub == "TABLES":
            return {"cmd": "SHOW_TABLES"}

        if sub in ("TREE", "TRAVERSAL", "STATS"):
            if len(tokens) < 3:
                raise ComandoInvalido(f"falta el nombre de la tabla: SHOW {sub} nombre")
            return {"cmd": f"SHOW_{sub}", "tabla": tokens[2]}

        raise ComandoInvalido(
            f"SHOW {tokens[1]} no reconocido. Opciones: TABLES, TREE, TRAVERSAL, STATS"
        )

    # ──────────────────────────────────────────────────────────────
    #  INSERT nombre campo=valor campo=valor ...
    #  Los valores con espacios van entre comillas: nombre="Cafe con leche"
    #
    #  Resultado:
    #    {"cmd": "INSERT", "tabla": "productos",
    #     "datos": {"id": 1, "nombre": "Cafe con leche", "precio": 3.5}}
    # ──────────────────────────────────────────────────────────────
    # aca es donde sacamos los datos que vamos a meter a la base de datos separando la instruccion del resto del texto,
    # y tambien usamos una funcion auxiliar para extraer las parejas de campo y valor asegurandonos de que por lo menos haya una
    def _parsear_insert(self, linea, tokens):
        if len(tokens) < 3:
            raise ComandoInvalido(
                "sintaxis: INSERT nombre campo=valor ..."
            )

        nombre_tabla = tokens[1]
        # el texto despues de "INSERT nombre" es donde van los pares campo=valor
        resto = _texto_despues_de(linea, 2)
        datos = self._extraer_pares(resto)

        if not datos:
            raise ComandoInvalido(
                "INSERT necesita al menos un campo=valor, ejemplo: id=1 nombre=Ana"
            )

        return {"cmd": "INSERT", "tabla": nombre_tabla, "datos": datos}

    # ──────────────────────────────────────────────────────────────
    #  SELECT nombre
    #  SELECT nombre WHERE campo=valor
    #  SELECT nombre WHERE campo>=min AND campo<=max
    #
    #  Resultado:
    #    {"cmd": "SELECT", "tabla": "productos", "where": None}
    #    {"cmd": "SELECT", "tabla": "productos",
    #     "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}}
    #    {"cmd": "SELECT", "tabla": "productos",
    #     "where": {"tipo": "rango", "campo": "id", "min": 1, "max": 5}}
    # ──────────────────────────────────────────────────────────────
    # este metodo es clave porque nos deja buscar cosas y si vemos que la instruccion tiene un where cortamos el texto ahi,
    # luego mandamos ese pedazo a otra funcion para que analise la condicion de busqueda y asi filtrar los resultados despues
    def _parsear_select(self, linea, tokens):
        if len(tokens) < 2:
            raise ComandoInvalido("sintaxis: SELECT nombre [WHERE ...]")

        nombre_tabla = tokens[1]
        where = None

        linea_upper = linea.upper()
        if "WHERE" in linea_upper:
            idx = linea_upper.index("WHERE")
            clausula = linea[idx + 5:].strip()
            where = self._parsear_where(clausula)

        return {"cmd": "SELECT", "tabla": nombre_tabla, "where": where}

    # ──────────────────────────────────────────────────────────────
    #  UPDATE nombre SET campo=valor WHERE campo=valor
    #
    #  Resultado:
    #    {"cmd": "UPDATE", "tabla": "productos",
    #     "set": {"precio": 4.0},
    #     "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}}
    # ──────────────────────────────────────────────────────────────
    # aca la vuelta es un poco mas larga porque hay que partir el texto en tres pedazos buscando donde dice set y donde dice where,
    # como que extraemos los valores nuevos por un lado y la condicion por otro para saber que registros vamos a actualizar exactamente
    def _parsear_update(self, linea, tokens):
        linea_upper = linea.upper()

        if "SET" not in linea_upper:
            raise ComandoInvalido("UPDATE necesita SET, ejemplo: UPDATE tabla SET campo=valor WHERE id=1")
        if "WHERE" not in linea_upper:
            raise ComandoInvalido("UPDATE necesita WHERE para saber que registros actualizar")

        if len(tokens) < 2:
            raise ComandoInvalido("falta el nombre de la tabla en UPDATE")

        nombre_tabla = tokens[1]
        idx_set = linea_upper.index("SET")
        idx_where = linea_upper.index("WHERE")

        if idx_set > idx_where:
            raise ComandoInvalido("SET debe ir antes que WHERE")

        parte_set = linea[idx_set + 3: idx_where].strip()
        parte_where = linea[idx_where + 5:].strip()

        nuevos_valores = self._extraer_pares(parte_set)
        if not nuevos_valores:
            raise ComandoInvalido("SET necesita al menos un campo=valor")

        where = self._parsear_where(parte_where)

        return {
            "cmd": "UPDATE",
            "tabla": nombre_tabla,
            "set": nuevos_valores,
            "where": where,
        }

    # ──────────────────────────────────────────────────────────────
    #  DELETE nombre WHERE campo=valor
    #
    #  Resultado:
    #    {"cmd": "DELETE", "tabla": "productos",
    #     "where": {"tipo": "simple", "campo": "id", "op": "=", "valor": 1}}
    # ──────────────────────────────────────────────────────────────
    # por lo menos aca nos aseguramos de que el usuario siempre ponga un where para no ir a borrar toda la tabla por accidente,
    # asi que sacamos la condicion y armamos el diccionario con la orden de eliminar para que el motor se encargue del resto
    def _parsear_delete(self, linea, tokens):
        if len(tokens) < 2:
            raise ComandoInvalido("sintaxis: DELETE nombre WHERE campo=valor")

        nombre_tabla = tokens[1]
        linea_upper = linea.upper()

        if "WHERE" not in linea_upper:
            raise ComandoInvalido(
                "DELETE necesita WHERE para no borrar todos los registros de golpe"
            )

        idx_where = linea_upper.index("WHERE")
        parte_where = linea[idx_where + 5:].strip()
        where = self._parsear_where(parte_where)

        return {"cmd": "DELETE", "tabla": nombre_tabla, "where": where}

    # ──────────────────────────────────────────────────────────────
    #  Helpers privados
    # ──────────────────────────────────────────────────────────────

    # esta funcion coge el pedazo de texto del where y revisa si es una condicion normalita o si tiene un and para un rango de valores,
    # por lo general usa expresiones regulares para sacar el campo y el operador y el valor y dejar todo listo para comparar
    def _parsear_where(self, texto):
        """
        Parsea el texto que sigue despues de WHERE.

        Dos casos posibles:
          - Simple:  campo=valor  o  campo>valor  o  campo!=valor
          - Rango:   campo>=min AND campo<=max   (usa recorrido inorden del AVL)
        """
        texto = texto.strip()

        if re.search(r'\bAND\b', texto, re.IGNORECASE):
            return self._parsear_rango(texto)

        # simple: campo op valor
        patron = r'^(\w+)\s*(>=|<=|!=|>|<|=)\s*(.+)$'
        match = re.match(patron, texto)
        if not match:
            raise ComandoInvalido(
                f"WHERE '{texto}' no tiene el formato esperado, ejemplo: id=1 o nombre=Ana"
            )

        campo = match.group(1)
        operador = match.group(2)
        valor = _convertir_valor(match.group(3).strip().strip('"'))

        return {"tipo": "simple", "campo": campo, "op": operador, "valor": valor}

    # aca es donde aprovechamos el arbol avl para buscar entre dos limites asi que partimos el texto por el and,
    # y tambien sacamos cual es el minimo y cual es el maximo revisando los signos de mayor y menor para armar bien el rango
    def _parsear_rango(self, texto):
        """
        Parsea WHERE campo>=min AND campo<=max.
        Este tipo de busqueda aprovecha el recorrido inorden del AVL
        para obtener todos los IDs en rango en O(log n + k).
        """
        partes = re.split(r'\s+AND\s+', texto, flags=re.IGNORECASE)
        if len(partes) != 2:
            raise ComandoInvalido(
                "el rango necesita exactamente dos condiciones: campo>=min AND campo<=max"
            )

        patron = r'^(\w+)\s*(>=|<=|>|<)\s*(.+)$'
        match1 = re.match(patron, partes[0].strip())
        match2 = re.match(patron, partes[1].strip())

        if not match1 or not match2:
            raise ComandoInvalido(
                "formato de rango incorrecto, ejemplo: id>=2 AND id<=10"
            )

        campo1, op1, val1 = match1.group(1), match1.group(2), match1.group(3).strip()
        campo2, op2, val2 = match2.group(1), match2.group(2), match2.group(3).strip()

        if campo1 != campo2:
            raise ComandoInvalido("las dos condiciones del rango deben ser sobre el mismo campo")

        # determinar cual es el limite inferior y cual el superior
        # acepta id>=2 AND id<=10 o tambien id<=10 AND id>=2
        limites = {}
        for op, val in [(op1, val1), (op2, val2)]:
            if op in (">=", ">"):
                limites["min"] = _convertir_valor(val)
            elif op in ("<=", "<"):
                limites["max"] = _convertir_valor(val)

        if "min" not in limites or "max" not in limites:
            raise ComandoInvalido(
                "el rango necesita un limite inferior (>=) y uno superior (<=)"
            )

        return {
            "tipo": "rango",
            "campo": campo1,
            "min": limites["min"],
            "max": limites["max"],
        }

    # esto es re util porque saca los valores aunque tengan espacios si estan entre comillas usando un patron de busqueda,
    # como que va iterando por el texto y guardando cada parejita en un diccionario convirtiendo el valor al tipo que corresponde
    def _extraer_pares(self, texto):
        """
        Extrae pares campo=valor de un texto.
        Soporta valores entre comillas dobles para textos con espacios.
        Ejemplos:
          id=1 nombre=Ana edad=20
          nombre="Cafe con leche" precio=3.5
        """
        pares = {}
        # campo= seguido de valor entre comillas o una palabra sin espacios
        patron = r'(\w+)=("(?:[^"\\]|\\.)*"|[^\s"]+)'
        for match in re.finditer(patron, texto):
            campo = match.group(1)
            valor_raw = match.group(2)
            if valor_raw.startswith('"') and valor_raw.endswith('"'):
                valor = valor_raw[1:-1]  # quitar comillas
            else:
                valor = valor_raw
            pares[campo] = _convertir_valor(valor)
        return pares


# ──────────────────────────────────────────────────────────────
#  Funciones auxiliares (fuera de la clase porque no necesitan self)
# ──────────────────────────────────────────────────────────────

# esta funcion suelta es como que para ignorar las primeras palabras del comando y quedarnos solo con lo que importa al final
def _texto_despues_de(linea, n_palabras):
    """Devuelve el texto de la linea despues de saltarse n_palabras."""
    partes = linea.strip().split(None, n_palabras)
    return partes[n_palabras] if len(partes) > n_palabras else ""


# por ultimo aca intentamos adivinar de que tipo es el dato que nos pasaron probando si es booleano o entero o decimal,
# un poco para facilitar las cosas y si no logra convertirlo a numero pues lo deja como texto normalito y ya
def _convertir_valor(texto):
    """
    Intenta convertir el texto al tipo Python mas apropiado.
    Orden: bool -> int -> float -> str.
    El Motor luego verifica que el tipo coincida con el esquema de la tabla.
    """
    if texto.lower() == "true":
        return True
    if texto.lower() == "false":
        return False
    try:
        return int(texto)
    except ValueError:
        pass
    try:
        return float(texto)
    except ValueError:
        pass
    return texto
