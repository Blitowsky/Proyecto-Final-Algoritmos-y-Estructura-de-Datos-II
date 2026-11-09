# src/core/wave_manager/zone_generator.py
from src.core.hash_table import TablaHashCuadratica
from src.core.wave_manager.hilbert import obtener_dimension_potencia_2, xy2d

def ordenar_y_particionar_por_hilbert(
    grafo: TablaHashCuadratica, 
    ancho_x: int, 
    largo_y: int, 
    cantidad_zonas: int
) -> dict:
    """
    1. Calcula la grilla fractal contenedora N = 2^k.
    2. Mapea cada nodo (x, y) del grafo a su índice escalar de Hilbert 'd'.
    3. Ordena los nodos ascendentemente según 'd'.
    4. Particiona la secuencia 1D en 'cantidad_zonas' subconjuntos equilibrados.
    """
    n_hilbert = obtener_dimension_potencia_2(ancho_x, largo_y)
    elementos = grafo.obtener_elementos()

    nodos_mapeados = []
    for node_id, datos in elementos:
        x, y = datos["pos"]
        indice_d = xy2d(n_hilbert, x, y)
        nodos_mapeados.append({
            "id": node_id,
            "pos": (x, y),
            "tipo": datos["tipo"],
            "grado": len(datos["adyacentes"]),
            "hilbert_d": indice_d
        })

    # Ordenamiento 1D por índice de Hilbert: O(V log V)
    nodos_ordenados = sorted(nodos_mapeados, key=lambda item: item["hilbert_d"])

    # Partición secuencial equitativa en K zonas
    total_nodos = len(nodos_ordenados)
    zonas = {}
    tamaño_base = total_nodos // cantidad_zonas
    resto = total_nodos % cantidad_zonas

    inicio = 0
    for z in range(cantidad_zonas):
        # Distribuimos el resto (+1 nodo) en las primeras zonas para que sea exacto
        fin = inicio + tamaño_base + (1 if z < resto else 0)
        n_zona = f"ZONA_{z + 1}"
        for nodo in nodos_ordenados[inicio:fin]:
            nodo["zona_asignada"] = n_zona
        zonas[n_zona] = nodos_ordenados[inicio:fin]
        inicio = fin

    return {
        "n_hilbert": n_hilbert,
        "ancho_x": ancho_x,
        "largo_y": largo_y,
        "cantidad_zonas": cantidad_zonas,
        "nodos_ordenados": nodos_ordenados,
        "zonas": zonas
    }


def imprimir_reporte_distribucion(nombre_grafo: str, resultado: dict) -> None:
    """
    Imprime la lista completa de nodos ordenada por el índice de Hilbert,
    el mapa visual de las zonas en el Warehouse y la explicación de cómo se generó.
    """
    n_hilbert = resultado["n_hilbert"]
    ancho_x = resultado["ancho_x"]
    largo_y = resultado["largo_y"]
    k_zonas = resultado["cantidad_zonas"]
    nodos = resultado["nodos_ordenados"]
    zonas = resultado["zonas"]

    print("\n" + "=" * 85)
    print(f" REPORTE DE PARTICIÓN ESPACIAL CON CURVA DE HILBERT: {nombre_grafo.upper()}")
    print("=" * 85)

    # 1. Explicación metodológica de cómo se generó la distribución
    print("\n[1] ¿DE QUÉ FORMA SE GENERÓ ESTA DISTRIBUCIÓN?")
    print(f"  • Dominio Real vs. Dominio Fractal (Padding): El Warehouse tiene dimensiones "
          f"{ancho_x}x{largo_y} ({len(nodos)} nodos).")
    print(f"    Como la curva de Hilbert exige una cuadrícula cuadrada de potencia de 2 (2^k x 2^k), "
          f"se proyectó el grafo sobre un lienzo virtual de {n_hilbert}x{n_hilbert}.")
    print("  • Mapeo Bit a Bit (Reducción 2D -> 1D): Para cada nodo en (x, y), la función 'xy2d' "
          "subdividió recursivamente la cuadrícula en 4 sub-cuadrantes aplicando rotaciones ")
    print("    y transposiciones ('rot') junto con operadores XOR (^) y AND (&), obteniendo el escalar 'd'.")
    print("  • Ordenamiento por Localidad Espacial: Se ordenaron todos los vértices de menor a mayor 'd' "
          "en tiempo O(V log V). Gracias a la continuidad fractal de Hilbert, nodos con valores 'd' ")
    print("    consecutivos son físicamente adyacentes en el plano 2D.")
    print(f"  • Partición Lineal (Cortes): La lista unidimensional de {len(nodos)} nodos fue segmentada "
          f"en {k_zonas} bloques contiguos de ~{len(nodos)//k_zonas} nodos cada uno.")

    # 2. Resumen de las Zonas Generadas
    print("\n[2] RESUMEN DE ZONAS PARTICIONADAS:")
    for nombre_z, lista_z in zonas.items():
        if lista_z:
            d_min = lista_z[0]["hilbert_d"]
            d_max = lista_z[-1]["hilbert_d"]
            racks = sum(1 for n in lista_z if n["tipo"] == "RACK")
            pasillos = len(lista_z) - racks
            print(f"  -> {nombre_z:<8} | Total Nodos: {len(lista_z):<4} "
                  f"(Racks: {racks:<3}, Pasillos/Otros: {pasillos:<3}) | Rango Índice Hilbert d: [{d_min} .. {d_max}]")
        else:
            print(f"  -> {nombre_z:<8} | Zona vacía (se pidieron más zonas que nodos disponibles).")

    # 3. Lista completa de nodos ordenada
    print("\n[3] LISTA COMPLETA DE NODOS ORDENADA POR ÍNDICE DE HILBERT:")
    print("-" * 85)
    print(f"{'ORDEN':<6} | {'ÍNDICE (d)':<10} | {'NODO ID':<10} | {'COORD (x,y)':<12} | {'TIPO ELEMENTO':<20} | {'GRADO':<5} | {'ZONA'}")
    print("-" * 85)
    for idx, n in enumerate(nodos, start=1):
        coord_str = f"({n['pos'][0]}, {n['pos'][1]})"
        print(f"{idx:<6} | {n['hilbert_d']:<10} | {n['id']:<10} | {coord_str:<12} | {n['tipo']:<20} | {n['grado']:<5} | {n['zona_asignada']}")
    print("-" * 85)

    # 4. Mapa de calor ASCII en 2D para verificar visualmente las zonas y estructura del Warehouse
    print("\n[4] VISTA 2D DEL WAREHOUSE (NÚMERO DE ZONA + SÍMBOLO DE ESTRUCTURA):")
    print("    Leyenda: [#]=RACK, [D]=DESPACHO, [P]=PUERTA, [.]=PASILLO  (Ej: '1#' = Zona 1, Rack)")
    mapa_2d = {n["pos"]: (n["zona_asignada"].split("_")[1], n["tipo"]) for n in nodos}
    simbolos = {"RACK": "#", "DESPACHO": "D", "PUERTA": "P", "PASILLO": ".", "PASILLO_TRANSVERSAL": "."}

    for y in range(largo_y - 1, -1, -1):
        fila_str = f"y={y:<2} | "
        for x in range(ancho_x):
            num_z, tipo = mapa_2d[(x, y)]
            fila_str += f"{num_z}{simbolos.get(tipo, '.')} "
        print(fila_str)
    print("     +" + "---" * ancho_x)
    eje_x = "       " + "".join([f"{x:<3}" for x in range(ancho_x)])
    print(eje_x + "\n")