# visualizacion.py
# Responsabilidad unica: imprimir el arbol AVL y sus metricas de forma visual.
# No sabe nada de DB, de comandos ni de esquemas.
# Solo recibe un objeto ArbolAVL o un dict de stats y lo muestra bonito.

import math

# Esta es una funcion recursiva ingeniosa.
# Imprime el arbol "de lado": la raiz a la izquierda y las hojas a la derecha.
# Es la forma más fácil de visualizar la profundidad en una terminal.
def _visualizar_arbol(nodo, nivel=0, prefijo=""):
    if nodo is None:
        return ""
    resultado = ""
    # Primero recorre la parte derecha (que se imprimirá arriba)
    if nodo.derecha:
        resultado += _visualizar_arbol(nodo.derecha, nivel + 1, "/-- ")
    
    # Imprime el nodo actual
    resultado += " " * (nivel * 4) + prefijo + str(nodo.dato) + "\n"
    
    # Luego la parte izquierda (que se imprimirá abajo)
    if nodo.izquierda:
        resultado += _visualizar_arbol(nodo.izquierda, nivel + 1, "\\-- ")
    return resultado


def mostrar_arbol(avl, titulo="Arbol AVL"):
    """Imprime el arbol AVL completo de forma visual."""
    print(f"\n=== {titulo} ===")
    if avl.raiz is None:
        print("  (vacio)")
    else:
        print(_visualizar_arbol(avl.raiz))


def mostrar_recorridos(avl, titulo="Arbol"):
    """Imprime los tres recorridos del arbol."""
    print(f"\n=== Recorridos: {titulo} ===")
    print(f"  Inorden   (asc):  {avl.recorrido_inorden()}")
    print(f"  Preorden  (raiz): {avl.recorrido_preorden()}")
    print(f"  Postorden (hojas):{avl.recorrido_postorden()}")


def mostrar_busqueda(avl_info, dato_encontrado):
    """
    Imprime el resultado de una busqueda AVL con sus metricas.
    'avl_info' es el dict con la informacion recolectada durante la operacion.
    """
    print("\n=== Resultado de Busqueda AVL ===")
    if dato_encontrado is not None:
        print(f"  [OK] Dato encontrado: {dato_encontrado}")
    else:
        print("  [NO] Dato no encontrado")
    
    # Mostrar las métricas permite al usuario entender el costo O(log n)
    print(f"  Comparaciones:    {avl_info['comparaciones']}")
    print(f"  Nodos visitados: {avl_info['nodos_visitados']}")
    recorrido_str = " -> ".join(str(x) for x in avl_info['recorrido'])
    print(f"  Recorrido:       {recorrido_str}")


def mostrar_estadisticas(tabla, stats):
    """
    Imprime las estadisticas del arbol AVL de una tabla.
    Esta funcion es educativa: muestra que tan 'cerca' esta el arbol de ser perfecto.
    """
    n = stats['total_nodos']
    print("\n" + "=" * 50)
    print(f"  ESTADISTICAS AVL - {tabla.upper()}")
    print("=" * 50)
    print(f"  Total nodos:      {n}")
    print(f"  Altura actual:    {stats['altura']}")
    print(f"  Balance raiz:     {stats['balance_raiz']}")

    if n > 0:
        # Calculamos la altura logaritmica optima: log2(n+1)
        altura_optima = math.ceil(math.log2(n + 1))
        print(f"  Altura optima:    {altura_optima}  (O(log {n}) ≈ {altura_optima})")
        diferencia = stats['altura'] - altura_optima
        
        if diferencia == 0:
            print("  Estado:          altura optima, el arbol esta perfectamente balanceado")
        else:
            print(f"  Estado:          {diferencia} nivel(es) sobre el optimo, dentro del rango AVL")

    print("=" * 50)
