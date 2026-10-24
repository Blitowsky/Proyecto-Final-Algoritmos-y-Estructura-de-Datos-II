# main_test_espectral.py
import csv
import json
import math
import numpy as np


# =====================================================================
# 1. TABLA HASH CUADRÁTICA PROPIA Y COLA FIFO PROPIA
# =====================================================================
class TablaHashCuadratica:
    VACIO = 0
    OCUPADO = 1
    ELIMINADO = 2

    def __init__(self, capacidad_inicial=11):
        self.capacidad = self._siguiente_primo(capacidad_inicial)
        self.tamaño = 0
        self.tabla = [[self.VACIO, None, None] for _ in range(self.capacidad)]

    def _hash(self, clave):
        k = abs(hash(clave))
        A = (math.sqrt(5) - 1) / 2
        return math.floor(self.capacidad * ((k * A) % 1))

    def insertar(self, clave, valor):
        if self.tamaño / self.capacidad >= 0.5:
            self._redimensionar()
        idx_base = self._hash(clave)
        i = 0
        idx_insertar = None
        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]
            if estado == self.VACIO:
                if idx_insertar is None:
                    idx_insertar = idx_actual
                break
            elif estado == self.OCUPADO and c == clave:
                self.tabla[idx_actual][2] = valor
                return
            elif estado == self.ELIMINADO and idx_insertar is None:
                idx_insertar = idx_actual
            i += 1
        self.tabla[idx_insertar] = [self.OCUPADO, clave, valor]
        self.tamaño += 1

    def buscar(self, clave):
        idx_base = self._hash(clave)
        i = 0
        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]
            if estado == self.VACIO:
                return None
            elif estado == self.OCUPADO and c == clave:
                return v
            i += 1

    def _redimensionar(self):
        tabla_antigua = self.tabla
        self.capacidad = self._siguiente_primo(self.capacidad * 2)
        self.tamaño = 0
        self.tabla = [[self.VACIO, None, None] for _ in range(self.capacidad)]
        for estado, clave, valor in tabla_antigua:
            if estado == self.OCUPADO:
                self.insertar(clave, valor)

    def _es_primo(self, n):
        if n <= 1: return False
        if n <= 3: return True
        if n % 2 == 0 or n % 3 == 0: return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0: return False
            i += 6
        return True

    def _siguiente_primo(self, n):
        if n <= 2: return 2
        primo = n if n % 2 != 0 else n + 1
        while not self._es_primo(primo):
            primo += 2
        return primo


class _NodoCola:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class _ColaFIFO:
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamaño = 0

    def esta_vacia(self) -> bool:
        return self.frente is None

    def encolar(self, valor) -> None:
        nuevo = _NodoCola(valor)
        if self.final is not None:
            self.final.siguiente = nuevo
        self.final = nuevo
        if self.frente is None:
            self.frente = nuevo
        self.tamaño += 1

    def desencolar(self):
        if self.frente is None:
            return None
        valor = self.frente.valor
        self.frente = self.frente.siguiente
        if self.frente is None:
            self.final = None
        self.tamaño -= 1
        return valor


# =====================================================================
# 2. MÓDULO DE CLUSTERING ESPECTRAL (INDEPENDIENTE)
# =====================================================================
def _bfs_distancias_desde_origen(grafo, origen: tuple[int, int], destinos_objetivo: set[tuple[int, int]]) -> dict:
    """Calcula pasos reales de pasillo respetando sentido de circulación y racks impenetrables."""
    cola = _ColaFIFO()
    cola.encolar(origen)
    visitados = {origen: 0}
    encontrados = {}

    if origen in destinos_objetivo:
        encontrados[origen] = 0

    while not cola.esta_vacia() and len(encontrados) < len(destinos_objetivo):
        actual = cola.desencolar()
        dist_actual = visitados[actual]
        datos_actual = grafo.buscar(actual)
        vecinos = datos_actual["adyacentes"] if datos_actual else []

        for vecino in vecinos:
            datos_vec = grafo.buscar(vecino)
            es_rack = (datos_vec["tipo"] == "RACK") if datos_vec else False

            if vecino not in visitados:
                if not es_rack:
                    visitados[vecino] = dist_actual + 1
                    if vecino in destinos_objetivo:
                        encontrados[vecino] = dist_actual + 1
                    cola.encolar(vecino)
                else:
                    # Un rack es alcanzable desde su pasillo lateral, pero no se puede atravesar
                    if vecino in destinos_objetivo and vecino not in encontrados:
                        encontrados[vecino] = dist_actual + 1

    return encontrados


def construir_matriz_distancias_pasillos(coordenadas: list[tuple[int, int]], grafo_pasillos) -> np.ndarray:
    p = len(coordenadas)
    matriz_dist = np.full((p, p), np.inf, dtype=float)
    np.fill_diagonal(matriz_dist, 0.0)

    conjunto_coords = set(coordenadas)
    mapa_bfs = {coord: _bfs_distancias_desde_origen(grafo_pasillos, coord, conjunto_coords) for coord in conjunto_coords}

    for i in range(p):
        u = coordenadas[i]
        for j in range(i + 1, p):
            v = coordenadas[j]
            d_uv = mapa_bfs[u].get(v, math.inf)
            d_vu = mapa_bfs[v].get(u, math.inf)
            if d_uv < math.inf and d_vu < math.inf:
                dist_real = 0.5 * (d_uv + d_vu)
            else:
                dist_real = min(d_uv, d_vu)
            matriz_dist[i, j] = dist_real
            matriz_dist[j, i] = dist_real
    return matriz_dist


def _kmeans_determinista(matriz_puntos: np.ndarray, k: int, max_iter: int = 100) -> list[int]:
    n_puntos = matriz_puntos.shape[0]
    centroides = [matriz_puntos[0].copy()]
    for _ in range(1, k):
        dist_min = np.array([min(np.linalg.norm(p - c) ** 2 for c in centroides) for p in matriz_puntos])
        centroides.append(matriz_puntos[int(np.argmax(dist_min))].copy())
    centroides = np.array(centroides)
    etiquetas = [0] * n_puntos

    for _ in range(max_iter):
        nuevas = [int(np.argmin([np.linalg.norm(matriz_puntos[i] - c) ** 2 for c in centroides])) for i in range(n_puntos)]
        if nuevas == etiquetas:
            break
        etiquetas = nuevas
        for cid in range(k):
            idxs = [i for i, e in enumerate(etiquetas) if e == cid]
            if idxs:
                centroides[cid] = np.mean(matriz_puntos[indices if False else idxs], axis=0)
    return etiquetas


def agrupar_por_clustering_espectral(
    coordenadas: list[tuple[int, int]],
    cantidad_zonas: int,
    grafo_pasillos
) -> tuple[list[list[tuple[int, int]]], list[int]]:
    """
    Recibe una lista de coordenadas (x, y) y devuelve:
      1) Lista de listas con las zonas y puntos correspondientes a cada una.
      2) Lista de etiquetas de zona (0 .. K-1) alineada con 'coordenadas'.
    """
    if not coordenadas:
        return [], []
    n_puntos = len(coordenadas)
    if cantidad_zonas <= 1:
        return [list(coordenadas)], [0] * n_puntos
    if cantidad_zonas >= n_puntos:
        return [[c] for c in coordenadas], list(range(n_puntos))

    matriz_dist = construir_matriz_distancias_pasillos(coordenadas, grafo_pasillos)
    dist_finitas = matriz_dist[(matriz_dist > 0) & np.isfinite(matriz_dist)]
    sigma = float(np.median(dist_finitas)) if dist_finitas.size > 0 else 1.0
    if sigma <= 0:
        sigma = 1.0

    W = np.exp(-(matriz_dist ** 2) / (2.0 * (sigma ** 2)))
    np.fill_diagonal(W, 0.0)

    grados = np.sum(W, axis=1)
    grados_inv_sqrt = np.where(grados > 1e-12, 1.0 / np.sqrt(grados), 0.0)
    D_inv_sqrt = np.diag(grados_inv_sqrt)
    L_sym = np.eye(n_puntos) - (D_inv_sqrt @ W @ D_inv_sqrt)

    _, autovectores = np.linalg.eigh(L_sym)
    U = autovectores[:, :cantidad_zonas]
    normas = np.linalg.norm(U, axis=1, keepdims=True)
    normas = np.where(normas > 1e-12, normas, 1.0)
    T = U / normas

    etiquetas = _kmeans_determinista(T, cantidad_zonas)
    zonas_dict = {z: [] for z in range(cantidad_zonas)}
    for coord, zid in zip(coordenadas, etiquetas):
        zonas_dict[zid].append(coord)

    zonas_lista = [pts for pts in zonas_dict.values() if pts]
    return zonas_lista, etiquetas


# =====================================================================
# 3. CONSTRUCCIÓN DEL ESCENARIO Y GRAFICACIÓN POR CONSOLA
# =====================================================================
def construir_grafo_desde_json(data: dict):
    wh = data["warehouse"]
    ancho_x = wh["dimensiones"]["ancho_x"]
    largo_y = wh["dimensiones"]["largo_y"]

    celdas = {
        (x, y): {"tipo": "VACIO", "sentido": None, "id_elem": None}
        for y in range(largo_y) for x in range(ancho_x)
    }

    for p in wh["puertas"]:
        ux, uy = p["ubicacion"]["x"], p["ubicacion"]["y"]
        celdas[(ux, uy)] = {"tipo": "PUERTA", "sentido": p["tipo"], "id_elem": p["id"]}

    for zd in wh["zonas_despacho"]:
        ux, uy = zd["ubicacion"]["x"], zd["ubicacion"]["y"]
        for dx in range(zd["ancho"]):
            for dy in range(zd["alto"]):
                celdas[(ux + dx, uy + dy)] = {"tipo": "DESPACHO", "sentido": "AMBOS", "id_elem": zd["id"]}

    for r in wh["racks"]:
        ux, uy = r["ubicacion"]["x"], r["ubicacion"]["y"]
        for dx in range(r["ancho"]):
            for dy in range(r["alto"]):
                celdas[(ux + dx, uy + dy)] = {"tipo": "RACK", "sentido": None, "id_elem": r["id"]}

    for pas in wh["pasillos"]:
        ux, uy = pas["ubicacion"]["x"], pas["ubicacion"]["y"]
        for dx in range(pas["ancho"]):
            for dy in range(pas["alto"]):
                celdas[(ux + dx, uy + dy)] = {"tipo": "PASILLO", "sentido": pas["sentido"], "id_elem": pas["id"]}

    grafo = TablaHashCuadratica(ancho_x * largo_y * 2)

    for (x, y), info in celdas.items():
        tipo = info["tipo"]
        sentido = info["sentido"]
        vecinos = []

        if tipo == "PASILLO":
            if sentido == "N":
                candidatos = [(0, 1), (1, 0), (-1, 0)]
            elif sentido == "S":
                candidatos = [(0, -1), (1, 0), (-1, 0)]
            elif sentido == "E":
                candidatos = [(1, 0), (0, 1), (0, -1)]
            elif sentido == "O":
                candidatos = [(-1, 0), (0, 1), (0, -1)]
            else:
                candidatos = [(0, 1), (0, -1), (1, 0), (-1, 0)]

            for dx, dy in candidatos:
                nx, ny = x + dx, y + dy
                if (nx, ny) in celdas:
                    t_vec = celdas[(nx, ny)]["tipo"]
                    if t_vec in ("PASILLO", "DESPACHO"):
                        vecinos.append((nx, ny))
                    elif t_vec == "RACK" and dx != 0:
                        vecinos.append((nx, ny))
        elif tipo == "RACK":
            for dx, dy in [(-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in celdas and celdas[(nx, ny)]["tipo"] == "PASILLO":
                    vecinos.append((nx, ny))
        elif tipo in ("DESPACHO", "PUERTA"):
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in celdas and celdas[(nx, ny)]["tipo"] in ("PASILLO", "DESPACHO", "PUERTA"):
                    vecinos.append((nx, ny))

        grafo.insertar((x, y), {
            "pos": (x, y),
            "tipo": tipo,
            "sentido": sentido,
            "id_elem": info["id_elem"],
            "adyacentes": vecinos
        })

    return grafo, celdas, ancho_x, largo_y


def graficar_solucion_por_consola(
    celdas: dict,
    ancho_x: int,
    largo_y: int,
    mapa_zonas_wh: dict,
    productos: list[dict],
    zonas_productos: list[list[tuple[int, int]]],
    usar_ansi: bool = True
) -> None:
    """
    Grafica directamente en la consola:
      1. El mapa 2D completo del Warehouse coloreado por zona espectral.
      2. El mapa 2D enfocado específicamente en los puntos de recolección (Productos) agrupados.
    """
    ANSI = {
        1: "\033[91m" if usar_ansi else "",  # Rojo
        2: "\033[96m" if usar_ansi else "",  # Turquesa
        3: "\033[94m" if usar_ansi else "",  # Azul
        4: "\033[93m" if usar_ansi else "",  # Naranja
        0: "\033[90m" if usar_ansi else "",  # Gris
    }
    RESET = "\033[0m" if usar_ansi else ""

    mapa_prods_coord = {}
    for p in productos:
        c = (p["ubicacion"]["x"], p["ubicacion"]["y"])
        mapa_prods_coord.setdefault(c, []).append(p["id"])

    print("\n" + "=" * 84)
    print(" [GRÁFICO EN CONSOLA 1] PARTICIÓN ESPECTRAL COMPLETA DEL WAREHOUSE (K = 4 ZONAS)")
    print("=" * 84)
    print(" Símbolos : [Z#]=Rack | [Z*]=Rack con Producto | [ZD]=Despacho | [ZP]=Puerta | [Z·]=Pasillo")
    print(" Colores  : "
          f"{ANSI[1]}ZONA 1 (Rojo Coral){RESET} | "
          f"{ANSI[2]}ZONA 2 (Verde Turquesa){RESET} | "
          f"{ANSI[3]}ZONA 3 (Azul Acero){RESET} | "
          f"{ANSI[4]}ZONA 4 (Naranja Arena){RESET}")
    print("-" * 84)

    for y in range(largo_y - 1, -1, -1):
        fila_str = f"y={y:<2} │ "
        for x in range(ancho_x):
            tipo = celdas[(x, y)]["tipo"]
            z = mapa_zonas_wh.get((x, y), 0)
            col = ANSI.get(z, RESET)

            if z == 0:
                fila_str += f"{col} · {RESET}"
            else:
                if (x, y) in mapa_prods_coord:
                    simb = "*"
                elif tipo == "RACK":
                    simb = "#"
                elif tipo == "DESPACHO":
                    simb = "D"
                elif tipo == "PUERTA":
                    simb = "P"
                else:
                    simb = "·"
                fila_str += f"{col}{z}{simb} {RESET}"
        print(fila_str)

    print("     └" + "───" * ancho_x)
    print("       " + "".join(f"{x:<3}" for x in range(ancho_x)))

    # Segundo gráfico en consola: Exclusivo de las coordenadas de productos recibidas
    mapa_zona_prod = {}
    for idx_z, lista_coords in enumerate(zonas_productos, start=1):
        for c in lista_coords:
            mapa_zona_prod[c] = idx_z

    print("\n" + "=" * 84)
    print(" [GRÁFICO EN CONSOLA 2] AGRUPAMIENTO ESPECTRAL DE LOS PRODUCTOS A RECOGER (K = 2)")
    print("=" * 84)
    print(" Referencia: [G1], [G2] = Grupo/Zona de Productos asignada | ██ = Rack | ↑↓+ = Pasillos")
    print("-" * 84)

    simb_sentido = {"N": " ↑ ", "S": " ↓ ", "AMBOS": " + "}
    for y in range(largo_y - 1, -1, -1):
        fila_str = f"y={y:<2} │ "
        for x in range(ancho_x):
            info = celdas[(x, y)]
            tipo = info["tipo"]
            if (x, y) in mapa_zona_prod:
                gz = mapa_zona_prod[(x, y)]
                col = ANSI.get(gz, RESET)
                fila_str += f"{col}[G{gz}]{RESET}"[:-1] if not usar_ansi else f"{col}G{gz}*{RESET}"
            elif tipo == "RACK":
                fila_str += " ██"
            elif tipo == "DESPACHO":
                fila_str += " DD"
            elif tipo == "PUERTA":
                fila_str += " PP"
            elif tipo == "PASILLO":
                fila_str += simb_sentido.get(info["sentido"], " · ")
            else:
                fila_str += "   "
        print(fila_str)

    print("     └" + "───" * ancho_x)
    print("       " + "".join(f"{x:<3}" for x in range(ancho_x)))
    print("\nDetalle de Zonas de Productos devueltas por agrupar_por_clustering_espectral():")
    for idx_z, z_coords in enumerate(zonas_productos, start=1):
        col = ANSI.get(idx_z, RESET)
        print(f"  -> {col}Zona de Productos {idx_z}{RESET}: {z_coords}")
    print("=" * 84 + "\n")


def exportar_resultados_csv(
    ruta_csv: str,
    celdas: dict,
    ancho_x: int,
    largo_y: int,
    mapa_zonas_wh: dict,
    productos: list[dict]
) -> None:
    paleta_colores = {
        1: ("#E63946", "Rojo Coral"),
        2: ("#2A9D8F", "Verde Turquesa"),
        3: ("#457B9D", "Azul Acero"),
        4: ("#F4A261", "Naranja Arena"),
        0: ("#CCCCCC", "Gris Neutro (Inactivo)")
    }
    mapa_prods_coord = {}
    for prod in productos:
        c = (prod["ubicacion"]["x"], prod["ubicacion"]["y"])
        mapa_prods_coord.setdefault(c, []).append(prod["id"])

    with open(ruta_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "nodo_id", "x", "y", "tipo_celda", "elemento_id",
            "sentido_pasillo", "tiene_producto", "productos_ids",
            "zona_id", "zona_nombre", "color_hex", "color_nombre"
        ])
        for y in range(largo_y):
            for x in range(ancho_x):
                info = celdas[(x, y)]
                tipo = info["tipo"]
                id_elem = info["id_elem"] if info["id_elem"] else "N/A"
                sentido = info["sentido"] if info["sentido"] else "N/A"
                prods = mapa_prods_coord.get((x, y), [])
                tiene_prod = "SI" if prods else "NO"
                prods_str = "|".join(prods) if prods else "Ninguno"

                z_num = mapa_zonas_wh.get((x, y), 0)
                z_nombre = f"ZONA_{z_num}" if z_num > 0 else "SIN_ZONA"
                c_hex, c_nom = paleta_colores[z_num]

                writer.writerow([
                    f"N_{x}_{y}", x, y, tipo, id_elem,
                    sentido, tiene_prod, prods_str,
                    z_num, z_nombre, c_hex, c_nom
                ])


def main():
    with open("escenario_grande.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)

    grafo, celdas, ancho_x, largo_y = construir_grafo_desde_json(data)

    # 1. Agrupar todos los nodos activos del Warehouse en K=4 zonas
    nodos_activos = [
        pos for pos, info in celdas.items()
        if info["tipo"] in ("PASILLO", "RACK", "DESPACHO", "PUERTA")
    ]
    zonas_wh, etiquetas_wh = agrupar_por_clustering_espectral(nodos_activos, 2, grafo)
    mapa_zonas_wh = {coord: zid + 1 for coord, zid in zip(nodos_activos, etiquetas_wh)}

    # 2. Agrupar las coordenadas de los productos del escenario en K=2 zonas
    coords_productos = [(p["ubicacion"]["x"], p["ubicacion"]["y"]) for p in data["productos"]]
    zonas_productos, _ = agrupar_por_clustering_espectral(coords_productos, 2, grafo)

    # 3. Graficar por consola ambas soluciones
    graficar_solucion_por_consola(
        celdas, ancho_x, largo_y,
        mapa_zonas_wh, data["productos"], zonas_productos,
        usar_ansi=False
    )

    # 4. Exportar el CSV para el visualizador
    exportar_resultados_csv(
        "distribucion_zonas_espectral.csv",
        celdas, ancho_x, largo_y,
        mapa_zonas_wh, data["productos"]
    )


if __name__ == "__main__":
    main()
