# main.py
# Responsabilidad UNICA: leer comandos del usuario e imprimir resultados.
# No sabe nada de AVL, ni de JSON, ni de validaciones.
# Solo habla con Parser y Motor.
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import math
from motor_parser import Parser, ComandoInvalido
from motor import Motor
from visualizacion import mostrar_arbol, mostrar_recorridos, mostrar_busqueda, mostrar_estadisticas

BANNER = """
╔══════════════════════════════════════════╗
║       MOTOR DE BASE DE DATOS - AVL       ║
║    Escribe COMANDOS para ver los comandos    ║
╚══════════════════════════════════════════╝
"""

AYUDA = """
  Comandos disponibles:
  ─────────────────────────────────────────────────────────────
  CREATE TABLE nombre campo:tipo ...     Crear tabla con esquema
  DROP TABLE nombre                      Eliminar tabla
  SHOW TABLES                            Listar tablas existentes

  INSERT nombre campo=valor ...          Insertar registro
  SELECT nombre                          Ver todos los registros
  SELECT nombre WHERE campo=valor        Buscar por valor exacto
  SELECT nombre WHERE id>=2 AND id<=5    Buscar por rango (AVL)
  UPDATE nombre SET campo=valor WHERE campo=valor   Actualizar
  DELETE nombre WHERE campo=valor        Eliminar registro

  SHOW TREE nombre                       Ver árbol AVL visual
  SHOW TRAVERSAL nombre                  Ver recorridos inorden/pre/post
  SHOW STATS nombre                      Ver estadísticas del árbol AVL

  COMANDOS                                   Ver esta ayuda
  SALIR                                   Salir
  ─────────────────────────────────────────────────────────────
  Tipos soportados: int  text  real  bool

  Ejemplos:
    CREATE TABLE productos id:int nombre:text precio:real
    INSERT productos id=1 nombre=Cafe precio=3.5
    SELECT productos WHERE id=1
    SELECT productos WHERE id>=1 AND id<=10
    UPDATE productos SET precio=4.0 WHERE id=1
    DELETE productos WHERE id=1
    SHOW TREE productos
"""


class REPL:
    # esta es la clase principal que mantiene el programa corriendo todo el tiempo, como que se queda dando vueltas esperando instrucciones,
    # un poco para recibir los comandos y pasarlos a las otras partes del sistema para que hagan el trabajo pesado
    """
    Bucle principal de la interfaz de línea de comandos.
    Lee una línea, la pasa al Parser, ejecuta con el Motor,
    e imprime el resultado. Ciclo sin fin hasta que el usuario escriba SALIR.
    """

    def __init__(self):
        # aca simplemente preparamos las herramientas que vamos a usar apenas arranca esto,
        # por lo menos instanciamos el parser para entender el texto y el motor para ejecutar la logica de fondo
        self.parser = Parser()
        self.motor = Motor()

    def iniciar(self):
        # este es el ciclo infinito donde la consola se queda esperando lo que el usuario le pida, y como que va leyendo linea por linea,
        # luego intenta procesar eso con el parser y si todo sale bien lo manda al motor para sacar un resultado final
        print(BANNER)
        while True:
            try:
                linea = input("db> ").strip()
            except (EOFError, KeyboardInterrupt):
                # Ctrl+C o Ctrl+D -> salir limpiamente
                print("\n  Hasta luego!")
                break

            if not linea:
                continue  # línea vacía, pedir otra

            if linea.upper() in ("EXIT", "SALIR", "QUIT"):
                print("  Hasta luego!")
                break

            if linea.upper() == "COMANDOS":
                print(AYUDA)
                continue

            # --- Paso 1: parsear el texto a un dict de comando ---
            try:
                comando = self.parser.parsear(linea)
            except ComandoInvalido as e:
                print(f"  [ERROR] {e}")
                print("  Escribe COMANDOS para ver los comandos disponibles.")
                continue

            # --- Paso 2: ejecutar el comando con el motor ---
            resultado = self.motor.ejecutar(comando)

            # --- Paso 3: imprimir el resultado ---
            self._imprimir(resultado)

    # ─────────────────────────────────────────────
    #  Métodos de visualización (privados)
    #  Cada uno sabe imprimir un tipo de resultado.
    # ─────────────────────────────────────────────

    def _imprimir(self, resultado):
        # esta funcion es como un filtro que revisa que tipo de respuesta llego del motor, por lo general mira la etiqueta,
        # asi sabe si tiene que mostrar un mensaje de exito o de error o si tiene que pintar una tabla por consola
        """Despacha al método de impresión correcto según el tipo."""
        if not resultado["ok"]:
            print(f"  [ERROR] {resultado['mensaje']}")
            return

        tipo = resultado.get("tipo")

        if tipo == "tabla_creada":
            print(f"  [OK] Tabla '{resultado['tabla']}' creada.")

        elif tipo == "tabla_eliminada":
            print(f"  [OK] Tabla '{resultado['tabla']}' eliminada.")

        elif tipo == "show_tables":
            self._imprimir_lista_tablas(resultado["tablas"])

        elif tipo == "insercion":
            print(f"  [OK] Registro insertado con ID: {resultado['id']}")
            self._imprimir_info_avl(resultado.get("info_avl"))

        elif tipo == "seleccion":
            self._imprimir_registros(resultado["datos"])
            self._imprimir_info_avl(resultado.get("info_avl"))

        elif tipo == "actualizacion":
            print(f"  [OK] {resultado['afectados']} registro(s) actualizado(s).")

        elif tipo == "eliminacion":
            print(f"  [OK] Registro eliminado.")
            self._imprimir_info_avl(resultado.get("info_avl"))

        elif tipo == "show_tree":
            mostrar_arbol(resultado["arbol"], f"Arbol AVL - {resultado['tabla']}")

        elif tipo == "show_traversal":
            mostrar_recorridos(resultado["arbol"], resultado["tabla"])

        elif tipo == "show_stats":
            mostrar_estadisticas(resultado["tabla"], resultado["stats"])

    def _imprimir_lista_tablas(self, tablas):
        # aca lo unico que hace es coger la lista de tablas que le pasaron y mostrarlas una por una en pantalla,
        # un poco para que uno vea que hay guardado en la base de datos hasta el momento
        if not tablas:
            print("  (no hay tablas creadas todavia)")
        else:
            print(f"  {len(tablas)} tabla(s) existente(s):")
            for t in tablas:
                print(f"    - {t}")

    def _imprimir_registros(self, registros):
        # esto cuadra los datos para que se vean bien organizados como en una cuadricula, calculando los espacios necesarios,
        # como que acomoda las columnas y las filas iterando sobre los registros que encontro para que no se vea feo
        """Imprime una lista de dicts como tabla formateada."""
        if not registros:
            print("  (sin resultados)")
            return

        columnas = list(registros[0].keys())
        # Calcular el ancho de cada columna
        anchos = {
            col: max(len(col), max(len(str(r.get(col, ""))) for r in registros))
            for col in columnas
        }

        # Encabezado
        header = "  " + "  ".join(col.upper().ljust(anchos[col]) for col in columnas)
        separador = "  " + "  ".join("-" * anchos[col] for col in columnas)
        print(header)
        print(separador)

        # Filas
        for r in registros:
            fila = "  " + "  ".join(str(r.get(col, "")).ljust(anchos[col]) for col in columnas)
            print(fila)

        print(f"\n  {len(registros)} registro(s) encontrado(s).")

    def _imprimir_info_avl(self, info_avl):
        # aca te muestra las estadisticas de lo que hizo el arbol por debajo, como que cuantos saltos dio para encontrar un dato exacto,
        # por lo general es util para entender el rendimiento de la busqueda y mirar todo el camino que tomo
        """Muestra las métricas de la última operación AVL."""
        if not info_avl:
            return
        print(
            f"  [AVL] Comparaciones: {info_avl['comparaciones']} | "
            f"Nodos visitados: {info_avl['nodos_visitados']}"
        )
        if info_avl.get("recorrido"):
            pasos = " → ".join(str(x) for x in info_avl["recorrido"])
            print(f"  [AVL] Camino: {pasos}")

if __name__ == "__main__":
    repl = REPL()
    repl.iniciar()
