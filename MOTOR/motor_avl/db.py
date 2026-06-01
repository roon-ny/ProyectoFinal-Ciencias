# db.py
# Responsabilidad unica: leer y escribir archivos JSON en disco.
# No sabe nada de AVL, no valida tipos, no ejecuta comandos.
# Solo guarda y carga datos. Un archivo por tabla.

import os
import json

# Definimos donde se van a guardar los archivos, por defecto en una carpeta llamada 'data'
import os
DIRECTORIO_DATOS = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# Esta excepcion es para avisar si algo salio mal leyendo o escribiendo en los archivos
class ErrorTabla(Exception):
    """Se lanza cuando hay un problema con la tabla: no existe, ya existe, archivo corrupto."""
    pass


class DB:
    """
    Maneja la lectura y escritura de archivos JSON.
    Cada tabla es un archivo .json en el directorio de datos.
    Cada archivo guarda el esquema y los registros juntos.

    La escritura es atomica: primero escribe en un .tmp y luego
    renombra ese archivo al nombre final. Si algo falla en el medio,
    el archivo original queda intacto, sin datos corruptos.
    """

    def __init__(self, directorio=DIRECTORIO_DATOS):
        self.directorio = directorio
        # Al iniciar, nos aseguramos de que la carpeta de datos exista. 
        # Si no, la creamos (exist_ok=True evita errores si ya existia).
        os.makedirs(directorio, exist_ok=True)

    # ──────────────────────────────────────────────────────────────
    #  Gestion de tablas
    # ──────────────────────────────────────────────────────────────

    def tabla_existe(self, nombre):
        """Dice si ya hay un archivo para esa tabla."""
        return os.path.isfile(self._ruta(nombre))

    def listar_tablas(self):
        """Devuelve los nombres de todas las tablas que hay en disco."""
        tablas = []
        for archivo in os.listdir(self.directorio):
            # Solo nos interesan los archivos .json, ignoramos los .tmp temporales
            if archivo.endswith(".json") and not archivo.endswith(".tmp"):
                tablas.append(archivo[:-5])  # quitamos el ".json" para quedarnos solo con el nombre
        return sorted(tablas)

    def crear_tabla(self, nombre, esquema):
        """
        Crea el archivo de la tabla con el esquema dado y sin registros.
        Lanza ErrorTabla si la tabla ya existe.
        """
        if self.tabla_existe(nombre):
            raise ErrorTabla(f"la tabla '{nombre}' ya existe")
        contenido = {"esquema": esquema, "registros": []}
        self._escribir(nombre, contenido)

    def eliminar_tabla(self, nombre):
        """
        Elimina el archivo de la tabla del disco.
        Lanza ErrorTabla si la tabla no existe.
        """
        if not self.tabla_existe(nombre):
            raise ErrorTabla(f"la tabla '{nombre}' no existe")
        os.remove(self._ruta(nombre))

    # ──────────────────────────────────────────────────────────────
    #  Lectura de datos
    # ──────────────────────────────────────────────────────────────

    def obtener_esquema(self, nombre):
        """Devuelve el esquema de la tabla como dict."""
        return self._leer(nombre)["esquema"]

    def leer_registros(self, nombre):
        """Devuelve la lista completa de registros de la tabla."""
        return self._leer(nombre)["registros"]

    # ──────────────────────────────────────────────────────────────
    #  Escritura de datos (atomica)
    # ──────────────────────────────────────────────────────────────

    def guardar_registros(self, nombre, registros):
        """
        Reemplaza la lista de registros de la tabla con la nueva.
        # Primero leemos el archivo actual para mantener el esquema que ya teniamos
        # y solo actualizamos la parte de los registros.
        """
        if not self.tabla_existe(nombre):
            raise ErrorTabla(f"la tabla '{nombre}' no existe")

        contenido = self._leer(nombre)  
        contenido["registros"] = registros
        self._escribir(nombre, contenido)

    # ──────────────────────────────────────────────────────────────
    #  Helpers privados
    # ──────────────────────────────────────────────────────────────

    def _ruta(self, nombre):
        """Construye la ruta completa del archivo de una tabla."""
        return os.path.join(self.directorio, f"{nombre}.json")

    def _leer(self, nombre):
        """
        Lee y parsea el archivo JSON de una tabla.
        Lanza ErrorTabla si no existe o si el archivo esta corrupto.
        """
        if not self.tabla_existe(nombre):
            raise ErrorTabla(f"la tabla '{nombre}' no existe")
        try:
            with open(self._ruta(nombre), "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ErrorTabla(
                f"el archivo de la tabla '{nombre}' esta corrupto y no se puede leer"
            )

    # persistencia atomica:
    # 1. Escribimos en un archivo temporal (.tmp).
    # 2. Si hay un corte de luz justo aquí, nuestro .json original sigue intacto.
    # 3. Solo cuando terminamos de escribir, hacemos os.replace (que es una operacion
    #    atómica a nivel de sistema operativo), reemplazando el viejo por el nuevo.
    def _escribir(self, nombre, contenido):
        ruta_final = self._ruta(nombre)
        ruta_tmp = ruta_final + ".tmp"

        # Abrimos el temporal para escribir
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            json.dump(contenido, f, indent=2, ensure_ascii=False)

        # El cambio de nombre "secreto" que hace todo seguro
        os.replace(ruta_tmp, ruta_final)
