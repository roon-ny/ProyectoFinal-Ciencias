# avl.py
# Responsabilidad unica: implementar el arbol AVL en memoria.
# No sabe nada de archivos, de comandos, ni de esquemas de tablas.
# Solo guarda IDs (enteros) y permite insertarlos, buscarlos,
# eliminarlos y recorrerlos con O(log n) garantizado.

# Este es el ladrillo basico de nuestro arbol. Cada nodo guarda el ID (dato),
# y tiene dos "brazos" (izquierda y derecha). Tambien guarda su altura,
# que es la clave para saber si el arbol se esta enchuecando.
class NodoAVL:
    def __init__(self, dato):
        self.dato = dato
        self.izquierda = None
        self.derecha = None
        self.altura = 1


class ArbolAVL:
    def __init__(self):
        self.raiz = None
        # Estas variables nos sirven para llevar metricas y mostrarle al usuario
        # cuanto esfuerzo le tomo al arbol hacer una operacion.
        self._comparaciones = 0
        self._nodos_visitados = 0
        self._recorrido = []

    def _altura(self, nodo):
        if nodo is None:
            return 0
        return nodo.altura

    # El factor de balance. Si da 0, 1 o -1 todo esta perfecto.
    # Si da 2 o -2, significa que un lado pesa mas que el otro y toca rotar.
    def _balance(self, nodo):
        if nodo is None:
            return 0
        return self._altura(nodo.izquierda) - self._altura(nodo.derecha)

    # ──────────────────────────────────────────────────────────────
    #  Gimnasia del arbol (Rotaciones)
    # ──────────────────────────────────────────────────────────────
    # Aca es donde ocurre la magia del AVL. Cuando el arbol se desbalancea,
    # hacemos estos "giros" para reacomodar los nodos sin perder el orden.

    def _rotacion_izquierda(self, z):
        y = z.derecha
        T2 = y.izquierda
        y.izquierda = z
        z.derecha = T2
        z.altura = 1 + max(self._altura(z.izquierda), self._altura(z.derecha))
        y.altura = 1 + max(self._altura(y.izquierda), self._altura(y.derecha))
        return y

    def _rotacion_derecha(self, z):
        y = z.izquierda
        T3 = y.derecha
        y.derecha = z
        z.izquierda = T3
        z.altura = 1 + max(self._altura(z.izquierda), self._altura(z.derecha))
        y.altura = 1 + max(self._altura(y.izquierda), self._altura(y.derecha))
        return y

    # A veces una sola rotacion no alcanza porque el desbalance tiene forma de "zig-zag".
    # Ahi aplicamos estas rotaciones dobles.
    def _rotacion_doble_izquierda_derecha(self, z):
        z.izquierda = self._rotacion_izquierda(z.izquierda)
        return self._rotacion_derecha(z)

    def _rotacion_doble_derecha_izquierda(self, z):
        z.derecha = self._rotacion_derecha(z.derecha)
        return self._rotacion_izquierda(z)

    # El medico del arbol: revisa el factor de balance y decide que pastilla
    # (rotacion) darle al nodo para que vuelva a estar sano.
    def _balancear(self, nodo, dato):
        balance = self._balance(nodo)
        if balance > 1 and dato < nodo.izquierda.dato:
            return self._rotacion_derecha(nodo)
        if balance < -1 and dato > nodo.derecha.dato:
            return self._rotacion_izquierda(nodo)
        if balance > 1 and dato > nodo.izquierda.dato:
            return self._rotacion_doble_izquierda_derecha(nodo)
        if balance < -1 and dato < nodo.derecha.dato:
            return self._rotacion_doble_derecha_izquierda(nodo)
        return nodo

    # ──────────────────────────────────────────────────────────────
    #  Operaciones principales
    # ──────────────────────────────────────────────────────────────

    def insertar(self, dato):
        self._recorrido = []
        self._comparaciones = 0
        self._nodos_visitados = 0
        self.raiz = self._insertar_rec(self.raiz, dato)

    def _insertar_rec(self, nodo, dato):
        # Cuando llegamos a un vacio, ahi es donde va el nuevo dato.
        if nodo is None:
            self._nodos_visitados += 1
            return NodoAVL(dato)
        self._comparaciones += 1
        self._nodos_visitados += 1
        if dato < nodo.dato:
            nodo.izquierda = self._insertar_rec(nodo.izquierda, dato)
        elif dato > nodo.dato:
            nodo.derecha = self._insertar_rec(nodo.derecha, dato)
        else:
            return nodo # no aceptamos datos duplicados
        
        # Al regresar de la recursion, actualizamos alturas y balanceamos si es necesario
        nodo.altura = 1 + max(self._altura(nodo.izquierda), self._altura(nodo.derecha))
        return self._balancear(nodo, dato)

    def eliminar(self, dato):
        self._recorrido = []
        self._comparaciones = 0
        self._nodos_visitados = 0
        self.raiz = self._eliminar_rec(self.raiz, dato)

    def _eliminar_rec(self, nodo, dato):
        if nodo is None:
            self._nodos_visitados += 1
            return nodo
        self._comparaciones += 1
        self._nodos_visitados += 1
        if dato < nodo.dato:
            nodo.izquierda = self._eliminar_rec(nodo.izquierda, dato)
        elif dato > nodo.dato:
            nodo.derecha = self._eliminar_rec(nodo.derecha, dato)
        else:
            # Encontramos al nodo a matar. Si tiene un solo hijo (o ninguno),
            # simplemente lo reemplazamos con ese hijo.
            if nodo.izquierda is None:
                return nodo.derecha
            elif nodo.derecha is None:
                return nodo.izquierda
            
            # Si tiene dos hijos, buscamos al menor de los mayores (el sucesor inorden),
            # le copiamos su valor, y luego eliminamos a ese sucesor abajo.
            temp = self._minimo(nodo.derecha)
            nodo.dato = temp.dato
            nodo.derecha = self._eliminar_rec(nodo.derecha, temp.dato)
            
        if nodo is None:
            return nodo
        nodo.altura = 1 + max(self._altura(nodo.izquierda), self._altura(nodo.derecha))
        balance = self._balance(nodo)
        
        # El balanceo despues de eliminar es un poco distinto al de insertar,
        # pero la logica de fondo (las 4 rotaciones posibles) es la misma.
        if balance > 1 and self._balance(nodo.izquierda) >= 0:
            return self._rotacion_derecha(nodo)
        if balance < -1 and self._balance(nodo.derecha) <= 0:
            return self._rotacion_izquierda(nodo)
        if balance > 1 and self._balance(nodo.izquierda) < 0:
            return self._rotacion_doble_izquierda_derecha(nodo)
        if balance < -1 and self._balance(nodo.derecha) > 0:
            return self._rotacion_doble_derecha_izquierda(nodo)
        return nodo

    def _minimo(self, nodo):
        actual = nodo
        while actual.izquierda is not None:
            actual = actual.izquierda
        return actual

    def buscar(self, dato):
        self._recorrido = []
        self._comparaciones = 0
        self._nodos_visitados = 0
        return self._buscar_rec(self.raiz, dato)

    def _buscar_rec(self, nodo, dato):
        if nodo is None:
            self._nodos_visitados += 1
            return None
        self._comparaciones += 1
        self._nodos_visitados += 1
        self._recorrido.append(nodo.dato)   # guardamos la ruta de busqueda para el REPL
        if dato == nodo.dato:
            return nodo.dato
        elif dato < nodo.dato:
            return self._buscar_rec(nodo.izquierda, dato)
        else:
            return self._buscar_rec(nodo.derecha, dato)

    # ──────────────────────────────────────────────────────────────
    #  Recorridos y Consultas
    # ──────────────────────────────────────────────────────────────

    # Inorden es el recorrido natural para ver los datos ordenados de menor a mayor.
    def recorrido_inorden(self):
        resultado = []
        self._inorden_rec(self.raiz, resultado)
        return resultado

    def _inorden_rec(self, nodo, resultado):
        if nodo:
            self._inorden_rec(nodo.izquierda, resultado)
            resultado.append(nodo.dato)
            self._inorden_rec(nodo.derecha, resultado)

    def recorrido_preorden(self):
        resultado = []
        self._preorden_rec(self.raiz, resultado)
        return resultado

    def _preorden_rec(self, nodo, resultado):
        if nodo:
            resultado.append(nodo.dato)
            self._preorden_rec(nodo.izquierda, resultado)
            self._preorden_rec(nodo.derecha, resultado)

    def recorrido_postorden(self):
        resultado = []
        self._postorden_rec(self.raiz, resultado)
        return resultado

    def _postorden_rec(self, nodo, resultado):
        if nodo:
            self._postorden_rec(nodo.izquierda, resultado)
            self._postorden_rec(nodo.derecha, resultado)
            resultado.append(nodo.dato)

    def obtener_altura(self):
        return self._altura(self.raiz)

    def obtener_factor_balance(self):
        return self._balance(self.raiz)

    # Aca esta una de las joyas de la corona: la busqueda por rango.
    # En vez de pasar por todos los nodos, la funcion poda las ramas (descarta
    # caminos enteros) si sabe que los datos ahi son muy grandes o muy chiquitos.
    def buscar_rango(self, minimo, maximo):
        """
        Devuelve una lista de IDs entre minimo y maximo (inclusive).
        No recorre todo el arbol, solo las ramas que pueden tener valores en el rango.
        Complejidad: O(log n + k), donde k es la cantidad de resultados.

        Ejemplo: buscar_rango(3, 8) en [1,3,4,7,10,12] devuelve [3, 4, 7]
        """
        self._comparaciones = 0
        self._nodos_visitados = 0
        resultado = []
        self._rango_rec(self.raiz, minimo, maximo, resultado)
        return resultado

    def _rango_rec(self, nodo, minimo, maximo, resultado):
        if nodo is None:
            return
        self._nodos_visitados += 1
        self._comparaciones += 1
        # si el nodo es mayor que el minimo, puede haber valores validos a la izquierda
        if nodo.dato > minimo:
            self._rango_rec(nodo.izquierda, minimo, maximo, resultado)
        # si el nodo esta dentro del rango, lo incluimos
        if minimo <= nodo.dato <= maximo:
            resultado.append(nodo.dato)
        # si el nodo es menor que el maximo, puede haber valores validos a la derecha
        if nodo.dato < maximo:
            self._rango_rec(nodo.derecha, minimo, maximo, resultado)

    def obtener_profundidad(self, valor):
        return self._profundidad_rec(self.raiz, valor, 0)

    def _profundidad_rec(self, nodo, valor, prof):
        if nodo is None:
            return -1
        if nodo.dato == valor:
            return prof
        if valor < nodo.dato:
            return self._profundidad_rec(nodo.izquierda, valor, prof + 1)
        return self._profundidad_rec(nodo.derecha, valor, prof + 1)

    def total_nodos(self):
        return self._contar_nodos(self.raiz)

    def _contar_nodos(self, nodo):
        if nodo is None:
            return 0
        return 1 + self._contar_nodos(nodo.izquierda) + self._contar_nodos(nodo.derecha)

    def obtener_datos(self):
        return self.recorrido_inorden()

    def get_ultima_busqueda_recorrido(self):
        return self._recorrido

    def get_ultima_busqueda_comparaciones(self):
        return self._comparaciones

    def get_ultima_busqueda_nodos(self):
        return self._nodos_visitados
