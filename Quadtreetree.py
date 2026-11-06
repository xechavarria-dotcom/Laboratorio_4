"""
Quadtree k-dimensional (hiperoctree) implementado desde cero.

Idea general:
    El mapa se divide en cuadros. Si un cuadro tiene muchos puntos,
    se parte en cuadros más pequeños. Así, al buscar, se pueden
    descartar cuadros completos sin revisar sus puntos.

    - En 2D cada cuadro se parte en 4  (quadtree).
    - En 3D cada cubo se parte en 8    (octree).
    - En K dimensiones se parte en 2^K (hiperoctree).

Unidades: todas las coordenadas están en METROS.
Por eso un radio de 500 significa 500 metros.
"""

import random
import math
import itertools


# 1. DATOS Y DISTANCIA

def generar_puntos(n, tamano=10000, dimensiones=2, semilla=42):
    """Genera n puntos al azar dentro de una ciudad de tamano x tamano metros.

    La semilla hace que siempre salgan los mismos puntos,
    por eso los datos son estáticos (no cambian entre ejecuciones).
    """
    random.seed(semilla)
    puntos = []
    for _ in range(n):
        # Un número al azar por cada dimensión: (x, y) en 2D, (x, y, z) en 3D...
        punto = tuple(random.uniform(0, tamano) for _ in range(dimensiones))
        puntos.append(punto)
    return puntos


def distancia(a, b):
    """Distancia en línea recta entre dos puntos (teorema de Pitágoras).

    Funciona en cualquier número de dimensiones porque recorre
    todas las coordenadas del punto.
    """
    suma = 0
    for i in range(len(a)):
        suma += (a[i] - b[i]) ** 2
    return math.sqrt(suma)


# 2. FUERZA BRUTA: revisa TODOS los puntos, uno por uno.
#    Es lenta, pero nunca se equivoca. Sirve para comparar y para
#    comprobar que el árbol da las respuestas correctas.

def fuerza_bruta_radio(puntos, centro, radio):
    """Todos los puntos a una distancia menor o igual al radio."""
    encontrados = []
    for p in puntos:
        if distancia(p, centro) <= radio:
            encontrados.append(p)
    return encontrados


def fuerza_bruta_mas_cercano(puntos, objetivo):
    """El punto más cercano al objetivo y su distancia."""
    mejor = None
    mejor_dist = float("inf")  # infinito: cualquier punto será más cercano
    for p in puntos:
        d = distancia(p, objetivo)
        if d < mejor_dist:
            mejor = p
            mejor_dist = d
    return mejor, mejor_dist


def fuerza_bruta_k_vecinos(puntos, objetivo, k):
    """Los k puntos más cercanos, como lista de (distancia, punto)."""
    # La distancia va primero para que sort() ordene por distancia.
    todos = [(distancia(p, objetivo), p) for p in puntos]
    todos.sort()
    return todos[:k]


# 3. NODO DEL ÁRBOL: representa un cuadro (o cubo, o hipercubo) del mapa

class Nodo:
    def __init__(self, minimo, maximo, capacidad=4, profundidad=0):
        self.minimo = minimo            # esquina inferior del cuadro, ej. (0, 0)
        self.maximo = maximo            # esquina superior del cuadro, ej. (10000, 10000)
        self.capacidad = capacidad      # máximo de puntos antes de dividirse
        self.profundidad = profundidad  # cuántas divisiones hubo para llegar aquí
        self.puntos = []                # puntos guardados (solo en las hojas)
        self.hijos = None               # None = es una hoja (no está dividido)

    def contiene(self, punto):
        """True si el punto está dentro de este cuadro."""
        for i in range(len(punto)):
            if punto[i] < self.minimo[i] or punto[i] > self.maximo[i]:
                return False  # se sale por alguna dimensión
        return True

    def dividir(self):
        """Parte el cuadro en 2^k hijos y reparte sus puntos entre ellos."""
        k = len(self.minimo)

        # La mitad del cuadro en cada dimensión (donde se "corta").
        centro = tuple((self.minimo[i] + self.maximo[i]) / 2 for i in range(k))

        # Cada combinación de 0 y 1 es un hijo. Por cada dimensión:
        #   0 = el hijo toma la mitad de abajo
        #   1 = el hijo toma la mitad de arriba
        # En 2D: (0,0) (0,1) (1,0) (1,1) -> 4 hijos. En 3D salen 8.
        self.hijos = []
        for combinacion in itertools.product([0, 1], repeat=k):
            nuevo_min = []
            nuevo_max = []
            for i in range(k):
                if combinacion[i] == 0:
                    nuevo_min.append(self.minimo[i])
                    nuevo_max.append(centro[i])
                else:
                    nuevo_min.append(centro[i])
                    nuevo_max.append(self.maximo[i])
            hijo = Nodo(tuple(nuevo_min), tuple(nuevo_max),
                        self.capacidad, self.profundidad + 1)
            self.hijos.append(hijo)

        # Los puntos que tenía este cuadro pasan a sus hijos.
        viejos = self.puntos
        self.puntos = []
        for p in viejos:
            for hijo in self.hijos:
                if hijo.insertar(p):
                    break  # ya lo guardó un hijo, no seguir buscando

    def insertar(self, punto):
        if not self.contiene(punto):
            return False  # el punto no es de este cuadro

        if self.hijos is None:
            # Es una hoja: si hay espacio, el punto se queda aquí.
            # El límite de profundidad 20 es un seguro: si hay muchos
            # puntos repetidos en el mismo lugar, dividir nunca los
            # separaría y el programa se quedaría dividiendo para siempre.
            if len(self.puntos) < self.capacidad or self.profundidad >= 20:
                self.puntos.append(punto)
                return True
            self.dividir()  # está lleno: se parte en hijos

        # Tiene hijos: se le pasa el punto al hijo que lo contenga.
        for hijo in self.hijos:
            if hijo.insertar(punto):
                return True
        return False

    def distancia_minima(self, punto):
      
        suma = 0
        for i in range(len(punto)):
            if punto[i] < self.minimo[i]:      # el punto queda antes del cuadro
                suma += (self.minimo[i] - punto[i]) ** 2
            elif punto[i] > self.maximo[i]:    # el punto queda después del cuadro
                suma += (punto[i] - self.maximo[i]) ** 2
            # si está entre minimo y maximo, en esta dimensión no suma nada
        return math.sqrt(suma)

    def buscar_radio(self, centro, radio, encontrados):
        # PODA: si el círculo no toca este cuadro, no entramos.
        if self.distancia_minima(centro) > radio:
            return

        if self.hijos is None:
            # Hoja: revisar sus pocos puntos uno por uno.
            for p in self.puntos:
                if distancia(p, centro) <= radio:
                    encontrados.append(p)
        else:
            # Tiene hijos: que cada hijo haga la misma búsqueda (recursión).
            for hijo in self.hijos:
                hijo.buscar_radio(centro, radio, encontrados)

    def buscar_cercanos(self, objetivo, k, mejores):
    
        if len(mejores) == k and self.distancia_minima(objetivo) > mejores[-1][0]:
            return

        if self.hijos is None:
            for p in self.puntos:
                d = distancia(p, objetivo)
                if len(mejores) < k:
                    # Todavía no tengo k candidatos: lo agrego.
                    mejores.append((d, p))
                    mejores.sort()
                elif d < mejores[-1][0]:
                    # Es mejor que el peor: lo reemplaza.
                    mejores[-1] = (d, p)
                    mejores.sort()
        else:
            # Visitar primero los hijos más cercanos: así se encuentran
            # buenos candidatos rápido y después se descartan más cuadros.
            ordenados = sorted(self.hijos,
                               key=lambda h: h.distancia_minima(objetivo))
            for hijo in ordenados:
                hijo.buscar_cercanos(objetivo, k, mejores)

    def contar(self):
        """Cuántos puntos hay guardados en este nodo y todos sus hijos."""
        if self.hijos is None:
            return len(self.puntos)
        total = 0
        for hijo in self.hijos:
            total += hijo.contar()
        return total

    def altura(self):
        """Cuántos niveles de divisiones tiene el árbol debajo de este nodo."""
        if self.hijos is None:
            return 0
        return 1 + max(hijo.altura() for hijo in self.hijos)

# 4. CLASE PRINCIPAL: es la que se usa desde afuera

class Quadtree:
    def __init__(self, puntos, capacidad=4):
        """Construye el árbol con todos los puntos."""
        if len(puntos) == 0:
            raise ValueError("Se necesita al menos un punto")

        k = len(puntos[0])  # número de dimensiones (2 para (x, y))

        # El cuadro raíz abarca exactamente todos los puntos:
        # va del menor al mayor valor en cada dimensión.
        minimo = tuple(min(p[i] for p in puntos) for i in range(k))
        maximo = tuple(max(p[i] for p in puntos) for i in range(k))

        self.dimensiones = k
        self.raiz = Nodo(minimo, maximo, capacidad)
        for p in puntos:
            self.raiz.insertar(p)

    def buscar_radio(self, centro, radio):
        """Todos los puntos a distancia <= radio del centro (Range Search)."""
        encontrados = []
        self.raiz.buscar_radio(centro, radio, encontrados)
        return encontrados

    def vecinos_en_radio(self, centro, radio):
       
        encontrados = self.buscar_radio(centro, radio)
        vecinos = [(distancia(p, centro), p) for p in encontrados]
        vecinos.sort()
        return vecinos

    def k_vecinos(self, objetivo, k=1):
        """Los k puntos más cercanos al objetivo, como lista de (distancia, punto)."""
        mejores = []
        self.raiz.buscar_cercanos(objetivo, k, mejores)
        return mejores

    def mas_cercano(self, objetivo):
        """El punto más cercano al objetivo y su distancia."""
        d, p = self.k_vecinos(objetivo, 1)[0]
        return p, d

    def __len__(self):
        """Permite usar len(arbol) para saber cuántos puntos tiene."""
        return self.raiz.contar()


# Ejemplo rápido (solo se ejecuta si se corre este archivo directamente)

if __name__ == "__main__":
    puntos = generar_puntos(10000)
    arbol = Quadtree(puntos)
    centro = (5000, 5000)

    print("Puntos en el arbol:", len(arbol))
    print("Altura del arbol:", arbol.raiz.altura())
    print("Puntos a 500 m (arbol):", len(arbol.buscar_radio(centro, 500)))
    print("Puntos a 500 m (fuerza bruta):",
          len(fuerza_bruta_radio(puntos, centro, 500)))

    print("Los 3 vecinos mas cercanos dentro del radio:")
    for d, p in arbol.vecinos_en_radio(centro, 500)[:3]:
        print(f"  ({p[0]:.1f}, {p[1]:.1f}) a {d:.1f} m")

    p, d = arbol.mas_cercano(centro)
    print("Mas cercano (arbol):", p, "a", round(d, 2), "m")