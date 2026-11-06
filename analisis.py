"""
Análisis comparativo: Quadtree vs fuerza bruta.

Pregunta del laboratorio:
    ¿Para qué tamaño de datos el Quadtree comienza a ser más rápido
    que la fuerza bruta?

Qué se mide para cada tamaño N:
    1. Cuánto tarda construir el árbol (la fuerza bruta no construye nada).
    2. Cuánto tarda UNA búsqueda en radio de 500 m (árbol vs fuerza bruta).
    3. Cuánto tarda UNA búsqueda del vecino más cercano (árbol vs fuerza bruta).

Ejecutar sin depurador (Ctrl + F5 en VS Code):  python analisis.py
"""

import os
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Quadtreetree import (Quadtree, generar_puntos,
                          fuerza_bruta_radio, fuerza_bruta_mas_cercano)

TAMANOS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 50000, 100000]
RADIO = 500          # metros
N_CONSULTAS = 100    # ubicaciones al azar por cada tamaño (se promedian)
REPETICIONES = 3     # cada medición se repite y se toma la más rápida
CARPETA = "graficas"


# 1. CÓMO SE MIDE EL TIEMPO

def cronometrar(funcion, consultas):
    """Tiempo promedio (en segundos) de una consulta.

    Se repite REPETICIONES veces y se toma el MÍNIMO. El ruido (otros
    programas usando el procesador) solo puede SUMAR tiempo, nunca
    restarlo, así que la medición más rápida es la más cercana a la real.
    """
    mejores = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        for c in consultas:
            funcion(c)
        mejores.append((time.perf_counter() - inicio) / len(consultas))
    return min(mejores)


def cronometrar_construccion(puntos):
    """Construye el árbol REPETICIONES veces y devuelve el mejor tiempo."""
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        arbol = Quadtree(puntos)
        tiempos.append(time.perf_counter() - inicio)
    return arbol, min(tiempos)


def medir():
    """Mide todos los tiempos para cada tamaño N."""
    random.seed(99)
    consultas = [(random.uniform(0, 10000), random.uniform(0, 10000))
                 for _ in range(N_CONSULTAS)]
    resultados = []

    for n in TAMANOS:
        puntos = generar_puntos(n)
        arbol, construccion = cronometrar_construccion(puntos)

        resultados.append({
            "n": n,
            "construccion": construccion,
            "radio_arbol": cronometrar(lambda c: arbol.buscar_radio(c, RADIO), consultas),
            "radio_bruta": cronometrar(lambda c: fuerza_bruta_radio(puntos, c, RADIO), consultas),
            "vecino_arbol": cronometrar(lambda c: arbol.mas_cercano(c), consultas),
            "vecino_bruta": cronometrar(lambda c: fuerza_bruta_mas_cercano(puntos, c), consultas),
        })
        print(f"  N={n:>6} listo")
    return resultados

# 2. RESULTADOS

def imprimir_tabla(res):
    print("\nTiempos promedio por consulta (milisegundos)")
    print(f"{'N':>7} | {'construir':>9} | {'radio arbol':>11} | {'radio bruta':>11} | "
          f"{'vecino arbol':>12} | {'vecino bruta':>12}")
    print("-" * 80)
    for r in res:
        print(f"{r['n']:>7} | {r['construccion'] * 1000:>9.2f} | "
              f"{r['radio_arbol'] * 1000:>11.4f} | {r['radio_bruta'] * 1000:>11.4f} | "
              f"{r['vecino_arbol'] * 1000:>12.4f} | {r['vecino_bruta'] * 1000:>12.4f}")


def primer_n_donde_gana_arbol(res, clave_arbol, clave_bruta):
    """Primer N desde el cual el árbol es más rápido en TODOS los tamaños
    siguientes (así un resultado suelto por ruido no engaña)."""
    for i in range(len(res)):
        if all(r[clave_arbol] < r[clave_bruta] for r in res[i:]):
            return res[i]["n"]
    return None


def consultas_para_recuperar(r, clave_arbol, clave_bruta):
    """Cuántas consultas hacen falta para que el tiempo de construir el
    árbol se pague con lo que se ahorra en cada consulta."""
    ahorro = r[clave_bruta] - r[clave_arbol]
    if ahorro <= 0:
        return None
    return r["construccion"] / ahorro


def graficar(res):
    """Gráfica 3: tiempo por consulta del árbol vs la fuerza bruta."""
    os.makedirs(CARPETA, exist_ok=True)
    ns = [r["n"] for r in res]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for ax, ca, cb, titulo in (
        (ax1, "radio_arbol", "radio_bruta", f"Busqueda en radio ({RADIO} m)"),
        (ax2, "vecino_arbol", "vecino_bruta", "Vecino mas cercano"),
    ):
        ax.plot(ns, [r[ca] * 1000 for r in res], "o-", color="green", label="Quadtree")
        ax.plot(ns, [r[cb] * 1000 for r in res], "s-", color="orangered", label="Fuerza bruta")
        corte = primer_n_donde_gana_arbol(res, ca, cb)
        if corte:
            ax.axvline(corte, color="gray", linestyle=":",
                       label=f"Arbol gana desde N={corte}")
        # Escala logarítmica: los N van de 10 a 100.000, sin ella los
        # valores pequeños quedarían aplastados contra el cero.
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Numero de puntos (N)")
        ax.set_ylabel("Tiempo por consulta (ms)")
        ax.set_title(titulo)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "comparacion_tiempos.png"), dpi=150)
    plt.close(fig)
    
# 3. DISCUSIÓN

def discusion(res):
    corte_radio = primer_n_donde_gana_arbol(res, "radio_arbol", "radio_bruta")
    corte_vecino = primer_n_donde_gana_arbol(res, "vecino_arbol", "vecino_bruta")
    r10k = next(r for r in res if r["n"] == 10000)

    print("\n================ DISCUSION ================")
    print(f"* Busqueda en radio: el Quadtree es mas rapido desde N = {corte_radio}.")
    print(f"* Vecino mas cercano: el Quadtree es mas rapido desde N = {corte_vecino}.")
    print(f"* Con N = 10.000 (el caso del enunciado):")
    print(f"    radio:  arbol {r10k['radio_arbol'] * 1000:.3f} ms vs "
          f"bruta {r10k['radio_bruta'] * 1000:.3f} ms "
          f"(~{r10k['radio_bruta'] / r10k['radio_arbol']:.0f} veces mas rapido)")
    print(f"    vecino: arbol {r10k['vecino_arbol'] * 1000:.3f} ms vs "
          f"bruta {r10k['vecino_bruta'] * 1000:.3f} ms "
          f"(~{r10k['vecino_bruta'] / r10k['vecino_arbol']:.0f} veces mas rapido)")
    rec = consultas_para_recuperar(r10k, "vecino_arbol", "vecino_bruta")
    print(f"    construir el arbol tarda {r10k['construccion'] * 1000:.1f} ms; "
          f"se recupera despues de ~{rec:.0f} consultas de vecino.")
    print("* Con pocos puntos gana la fuerza bruta: el arbol tiene costos extra")
    print("  (recursion, crear nodos, calcular distancias a los cuadros) que")
    print("  no se compensan cuando hay poco que descartar.")
    print("* La fuerza bruta crece lineal O(N). El arbol crece mucho mas lento")
    print("  (aprox. O(log N) por consulta con datos uniformes), porque descarta")
    print("  cuadros completos sin revisar sus puntos.")
    print("* Como los datos son estaticos, el arbol se construye una sola vez y")
    print("  se reutiliza en miles de consultas: ahi esta su ventaja real.")


if __name__ == "__main__":
    print("Midiendo tiempos (tarda 1 o 2 minutos)...")
    resultados = medir()
    imprimir_tabla(resultados)
    graficar(resultados)
    discusion(resultados)
    print(f"\nGrafica guardada en '{CARPETA}/'")