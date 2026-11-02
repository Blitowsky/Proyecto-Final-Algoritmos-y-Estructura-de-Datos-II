# main_test_espectral.py
import csv
import json
import math
import numpy as np
import Espectral.spectral_clustering as sc


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
    with open("escenario_basico.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)

    grafo, celdas, ancho_x, largo_y = construir_grafo_desde_json(data)

    # 1. Agrupar todos los nodos activos del Warehouse en K=4 zonas
    nodos_activos = [
        pos for pos, info in celdas.items()
        if info["tipo"] in ("PASILLO", "RACK", "DESPACHO", "PUERTA")
    ]
    zonas_wh, etiquetas_wh = sc.agrupar_por_clustering_espectral(nodos_activos, 2, grafo)
    mapa_zonas_wh = {coord: zid + 1 for coord, zid in zip(nodos_activos, etiquetas_wh)}

    # 2. Agrupar las coordenadas de los productos del escenario en K=2 zonas
    coords_productos = [(p["ubicacion"]["x"], p["ubicacion"]["y"]) for p in data["productos"]]
    zonas_productos, _ = sc.agrupar_por_clustering_espectral(coords_productos, 2, grafo)

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
