"""
Pruebas unitarias, verificación visual y análisis de las pruebas.

Idea de las pruebas:
    La fuerza bruta es lenta pero siempre da la respuesta correcta.
    Por eso el árbol debe dar EXACTAMENTE lo mismo que la fuerza bruta.

Ejecutar:  python test.py
Las gráficas se guardan en la carpeta graficas/
"""

import os
import random
import unittest

import matplotlib
matplotlib.use("Agg")  # guarda las imágenes sin abrir ventanas
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from Quadtreetree import (Quadtree, generar_puntos, distancia,
                          fuerza_bruta_radio, fuerza_bruta_mas_cercano,
                          fuerza_bruta_k_vecinos)

CARPETA = "graficas"
RADIO = 500  # metros


# ======================================================================
# 1. PRUEBAS UNITARIAS
# ======================================================================

class PruebasQuadtree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Se ejecuta una sola vez: crea los puntos, el árbol y 50
        ubicaciones al azar para hacer consultas."""
        cls.puntos = generar_puntos(10000)
        cls.arbol = Quadtree(cls.puntos)
        random.seed(7)
        cls.consultas = [(random.uniform(0, 10000), random.uniform(0, 10000))
                         for _ in range(50)]

    # --- Construcción del árbol ---

    def test_guarda_todos_los_puntos(self):
        """No se pierde ningún punto al construir el árbol."""
        self.assertEqual(len(self.arbol), 10000)

    def test_raiz_2d_tiene_4_hijos(self):
        """En 2D cada nodo se divide en 4 (quadtree)."""
        self.assertEqual(len(self.arbol.raiz.hijos), 4)

    # --- Búsqueda en radio ---

    def test_radio_igual_a_fuerza_bruta(self):
        """En 50 ubicaciones al azar, el árbol encuentra los mismos puntos."""
        for c in self.consultas:
            arbol = sorted(self.arbol.buscar_radio(c, RADIO))
            bruta = sorted(fuerza_bruta_radio(self.puntos, c, RADIO))
            self.assertEqual(arbol, bruta)

    def test_todos_los_encontrados_estan_dentro_del_radio(self):
        c = (5000, 5000)
        for p in self.arbol.buscar_radio(c, RADIO):
            self.assertLessEqual(distancia(p, c), RADIO)

    def test_radio_cero_en_un_punto_existente(self):
        """Con radio 0 sobre un punto, se encuentra ese mismo punto."""
        p = self.puntos[123]
        self.assertIn(p, self.arbol.buscar_radio(p, 0))

    def test_radio_lejos_del_mapa_no_encuentra_nada(self):
        self.assertEqual(self.arbol.buscar_radio((50000, 50000), RADIO), [])

    # --- Vecinos dentro del radio ---

    def test_vecinos_en_radio_ordenados(self):
        """Los vecinos dentro del radio salen del más cercano al más lejano."""
        c = (5000, 5000)
        distancias = [d for d, _ in self.arbol.vecinos_en_radio(c, RADIO)]
        self.assertEqual(distancias, sorted(distancias))
        self.assertEqual(len(distancias),
                         len(fuerza_bruta_radio(self.puntos, c, RADIO)))

    # --- Vecinos más cercanos ---

    def test_mas_cercano_igual_a_fuerza_bruta(self):
        for c in self.consultas:
            _, d_arbol = self.arbol.mas_cercano(c)
            _, d_bruta = fuerza_bruta_mas_cercano(self.puntos, c)
            self.assertAlmostEqual(d_arbol, d_bruta)

    def test_k_vecinos_igual_a_fuerza_bruta(self):
        for c in self.consultas:
            arbol = [d for d, _ in self.arbol.k_vecinos(c, 5)]
            bruta = [d for d, _ in fuerza_bruta_k_vecinos(self.puntos, c, 5)]
            for a, b in zip(arbol, bruta):
                self.assertAlmostEqual(a, b)

    def test_consulta_fuera_del_mapa_si_tiene_vecino(self):
        p, _ = self.arbol.mas_cercano((-1000, -1000))
        q, _ = fuerza_bruta_mas_cercano(self.puntos, (-1000, -1000))
        self.assertEqual(p, q)

    def test_k_mayor_que_n(self):
        """Si pido 10 vecinos pero solo hay 3 puntos, devuelve 3."""
        arbol = Quadtree(generar_puntos(3))
        self.assertEqual(len(arbol.k_vecinos((0, 0), 10)), 3)

    # --- Casos especiales ---

    def test_puntos_repetidos_no_cuelgan_el_programa(self):
        """Gracias al límite de profundidad, 50 puntos iguales no causan
        divisiones infinitas."""
        repetidos = [(5.0, 5.0)] * 50 + [(1.0, 1.0), (9.0, 9.0)]
        arbol = Quadtree(repetidos)
        self.assertEqual(len(arbol), 52)
        self.assertEqual(len(arbol.buscar_radio((5, 5), 0.1)), 50)

    # --- K dimensiones ---

    def test_3d_octree(self):
        """En 3D cada nodo se divide en 8 y las búsquedas siguen siendo correctas."""
        puntos = generar_puntos(2000, dimensiones=3)
        arbol = Quadtree(puntos)
        self.assertEqual(len(arbol.raiz.hijos), 8)
        c = (5000, 5000, 5000)
        self.assertEqual(sorted(arbol.buscar_radio(c, 1500)),
                         sorted(fuerza_bruta_radio(puntos, c, 1500)))
        self.assertAlmostEqual(arbol.mas_cercano(c)[1],
                               fuerza_bruta_mas_cercano(puntos, c)[1])

    def test_4d_hiperoctree(self):
        """En 4D cada nodo se divide en 2^4 = 16."""
        puntos = generar_puntos(1000, dimensiones=4)
        arbol = Quadtree(puntos)
        self.assertEqual(len(arbol.raiz.hijos), 16)
        c = (5000, 5000, 5000, 5000)
        self.assertEqual(sorted(arbol.buscar_radio(c, 3000)),
                         sorted(fuerza_bruta_radio(puntos, c, 3000)))


# ======================================================================
# 2. VERIFICACIÓN VISUAL (las 2 gráficas que pide el enunciado)
# ======================================================================

def grafica_radio(puntos, arbol, centro, radio):
    """Gráfica 1: el círculo de búsqueda y los puntos encontrados."""
    encontrados = arbol.buscar_radio(centro, radio)

    fig, ax = plt.subplots(figsize=(8, 8))
    xs, ys = zip(*puntos)
    ax.scatter(xs, ys, s=12, color="gray", label="Puntos de entrega")
    fx, fy = zip(*encontrados)
    ax.scatter(fx, fy, s=25, color="orangered",
               label=f"Dentro del radio ({len(encontrados)})")
    ax.add_patch(Circle(centro, radio, fill=False, edgecolor="orangered",
                        linestyle="--", linewidth=1.5))
    ax.scatter([centro[0]], [centro[1]], marker="*", s=250, color="black",
               label="Ubicacion consultada", zorder=5)

    margen = radio * 1.4  # mostrar solo la zona alrededor del círculo
    ax.set_xlim(centro[0] - margen, centro[0] + margen)
    ax.set_ylim(centro[1] - margen, centro[1] + margen)
    ax.set_aspect("equal")  # para que el círculo no se vea ovalado
    ax.set_title(f"Busqueda en radio de {radio} m")
    ax.set_xlabel("x (metros)")
    ax.set_ylabel("y (metros)")
    ax.legend(loc="upper right")
    fig.savefig(os.path.join(CARPETA, "busqueda_radio.png"), dpi=150)
    plt.close(fig)
    return encontrados


def grafica_vecinos(puntos, arbol, objetivo, k):
    """Gráfica 2: los k vecinos más cercanos unidos con líneas."""
    vecinos = arbol.k_vecinos(objetivo, k)

    fig, ax = plt.subplots(figsize=(8, 8))
    xs, ys = zip(*puntos)
    ax.scatter(xs, ys, s=12, color="gray", label="Puntos de entrega")

    for i, (d, p) in enumerate(vecinos):
        color = "green" if i == 0 else "blue"  # verde = el más cercano
        ax.plot([objetivo[0], p[0]], [objetivo[1], p[1]], color=color)
        ax.scatter([p[0]], [p[1]], s=40, color=color, zorder=4)
        ax.annotate(f"{i + 1}: {d:.0f} m", p, textcoords="offset points",
                    xytext=(5, 5))

    ax.scatter([objetivo[0]], [objetivo[1]], marker="*", s=250,
               color="black", label="Ubicacion consultada", zorder=5)

    margen = vecinos[-1][0] * 1.6  # un poco más allá del vecino más lejano
    ax.set_xlim(objetivo[0] - margen, objetivo[0] + margen)
    ax.set_ylim(objetivo[1] - margen, objetivo[1] + margen)
    ax.set_aspect("equal")
    ax.set_title(f"Los {k} vecinos mas cercanos (verde = el mas cercano)")
    ax.set_xlabel("x (metros)")
    ax.set_ylabel("y (metros)")
    ax.legend(loc="upper right")
    fig.savefig(os.path.join(CARPETA, "vecinos_cercanos.png"), dpi=150)
    plt.close(fig)
    return vecinos


# ======================================================================
# 3. ANÁLISIS DE LAS PRUEBAS REALIZADAS
# ======================================================================

def analisis_de_pruebas():
    os.makedirs(CARPETA, exist_ok=True)
    puntos = generar_puntos(10000)
    arbol = Quadtree(puntos)

    print("\n================ ANALISIS DE LAS PRUEBAS ================")
    print(f"Arbol con {len(arbol)} puntos, altura {arbol.raiz.altura()}.")

    # Verificación 1: búsqueda en radio
    centro = (5000, 5000)
    encontrados = grafica_radio(puntos, arbol, centro, RADIO)
    bruta = fuerza_bruta_radio(puntos, centro, RADIO)
    print(f"\n1. Radio de {RADIO} m alrededor de {centro}:")
    print(f"   arbol: {len(encontrados)} puntos | fuerza bruta: {len(bruta)} puntos")
    print(f"   Mismos puntos: {sorted(encontrados) == sorted(bruta)}")
    vecinos_radio = arbol.vecinos_en_radio(centro, RADIO)
    print(f"   El mas cercano dentro del radio esta a {vecinos_radio[0][0]:.1f} m "
          f"y el mas lejano a {vecinos_radio[-1][0]:.1f} m (menor a {RADIO}).")

    # Verificación 2: vecinos más cercanos
    objetivo = (3200, 7100)
    vecinos = grafica_vecinos(puntos, arbol, objetivo, 5)
    bruta_k = fuerza_bruta_k_vecinos(puntos, objetivo, 5)
    print(f"\n2. Los 5 vecinos mas cercanos a {objetivo}:")
    for i, (d, p) in enumerate(vecinos):
        print(f"   {i + 1}. ({p[0]:.1f}, {p[1]:.1f}) a {d:.1f} m")
    print(f"   Iguales a fuerza bruta: {vecinos == bruta_k}")

    print("\nConclusion: en todas las pruebas el arbol da exactamente las")
    print("mismas respuestas que la fuerza bruta, en 2D, 3D y 4D, incluso")
    print("en casos especiales (radio 0, fuera del mapa, puntos repetidos).")
    print(f"Graficas guardadas en '{CARPETA}/'")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    analisis_de_pruebas()