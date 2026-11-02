# visualizar_zonas_csv.py

"""Herramienta de visualización de los archivos .csv 
generados por la clusterización espectral"""


import csv
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def cargar_datos_csv(ruta_csv: str) -> list[dict]:
    """Lee el archivo CSV generado por el clustering espectral."""
    filas = []
    with open(ruta_csv, mode="r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            fila["x"] = int(fila["x"])
            fila["y"] = int(fila["y"])
            fila["zona_id"] = int(fila["zona_id"])
            filas.append(fila)
    return filas


def graficar_por_consola_desde_csv(filas: list[dict]) -> None:
    """
    Grafica por consola el mapa del Warehouse con colores ANSI para cada zona,
    mostrando la estructura física y los productos.
    """
    max_x = max(f["x"] for f in filas) + 1
    max_y = max(f["y"] for f in filas) + 1
    mapa = {(f["x"], f["y"]): f for f in filas}

    # Códigos de color ANSI para terminal
    ANSI_COLORES = {
        1: "\033[91m",  # Rojo Coral (Zona 1)
        2: "\033[96m",  # Verde/Cian Turquesa (Zona 2)
        3: "\033[94m",  # Azul Acero (Zona 3)
        4: "\033[93m",  # Naranja/Amarillo Arena (Zona 4)
        0: "\033[90m",  # Gris Neutro (Inactivo/Vacío)
    }
    RESET = "\033[0m"

    simbolos = {
        "RACK": "##",
        "DESPACHO": "DD",
        "PUERTA": "PP",
        "PASILLO": "..",
        "VACIO": "  "
    }

    print("\n" + "=" * 80)
    print(" VISUALIZACIÓN EN CONSOLA DESDE CSV: DISTRIBUCIÓN DE ZONAS ESPECTRALES")
    print("=" * 80)
    print(" Leyenda de Estructuras : [Z#]=Rack, [ZD]=Despacho, [ZP]=Puerta, [Z.]=Pasillo, [Z*]=Producto")
    print(" Leyenda de Zonas       : "
          f"{ANSI_COLORES[1]}■ ZONA_1 (Rojo){RESET} | "
          f"{ANSI_COLORES[2]}■ ZONA_2 (Turquesa){RESET} | "
          f"{ANSI_COLORES[3]}■ ZONA_3 (Azul){RESET} | "
          f"{ANSI_COLORES[4]}■ ZONA_4 (Naranja){RESET}")
    print("-" * 80)

    for y in range(max_y - 1, -1, -1):
        linea = f"y={y:<2} | "
        for x in range(max_x):
            celda = mapa[(x, y)]
            z = celda["zona_id"]
            tipo = celda["tipo_celda"]
            tiene_prod = celda["tiene_producto"] == "SI"
            color = ANSI_COLORES.get(z, RESET)

            if z == 0:
                token = f"{color} . {RESET}"
            else:
                if tiene_prod:
                    simb = "*"
                elif tipo == "RACK":
                    simb = "#"
                elif tipo == "DESPACHO":
                    simb = "D"
                elif tipo == "PUERTA":
                    simb = "P"
                else:
                    simb = "·"
                token = f"{color}{z}{simb} {RESET}"
            linea += token
        print(linea)

    print("     +" + "---" * max_x)
    print("       " + "".join(f"{x:<3}" for x in range(max_x)))
    print("=" * 80 + "\n")


def graficar_ventana_matplotlib(filas: list[dict], guardar_png: str = "mapa_zonas_espectral.png") -> None:
    """
    Genera un gráfico 2D limpio a partir del CSV, pintando cada celda con su
    color_hex asignado, diferenciando Racks, Pasillos, Despacho, Puertas y Productos.
    """
    max_x = max(f["x"] for f in filas) + 1
    max_y = max(f["y"] for f in filas) + 1

    fig, ax = plt.subplots(figsize=(13, 10), dpi=120)
    ax.set_xlim(-0.5, max_x - 0.5)
    ax.set_ylim(-0.5, max_y - 0.5)
    ax.set_aspect("equal")

    # Diccionario para armar la leyenda sin duplicados
    leyenda_zonas = {}

    FlechasSentido = {
        "N": (0, 0.28),
        "S": (0, -0.28),
        "E": (0.28, 0),
        "O": (-0.28, 0)
    }

    for f in filas:
        x, y = f["x"], f["y"]
        z_id = f["zona_id"]
        z_nom = f["zona_nombre"]
        c_hex = f["color_hex"]
        c_nom = f["color_nombre"]
        tipo = f["tipo_celda"]
        sentido = f["sentido_pasillo"]
        tiene_prod = (f["tiene_producto"] == "SI")
        prods_ids = f["productos_ids"]

        if z_nom not in leyenda_zonas:
            leyenda_zonas[z_nom] = (c_hex, f"{z_nom}: {c_nom}")

        # Ajustar estilo de borde y opacidad según el tipo de estructura
        if tipo == "VACIO":
            alpha = 0.25
            borde = "#BBBBBB"
            grosor = 0.5
            hatch = None
        elif tipo == "RACK":
            alpha = 0.92
            borde = "#1D1D1D"
            grosor = 1.8
            hatch = "///"
        elif tipo in ("DESPACHO", "PUERTA"):
            alpha = 0.85
            borde = "#000000"
            grosor = 1.5
            hatch = ".."
        else:  # PASILLO
            alpha = 0.60
            borde = "#555555"
            grosor = 0.7
            hatch = None

        rect = mpatches.Rectangle(
            (x - 0.5, y - 0.5), 1.0, 1.0,
            facecolor=c_hex, edgecolor=borde,
            linewidth=grosor, alpha=alpha, hatch=hatch
        )
        ax.add_patch(rect)

        # Etiqueta interna de celda
        if tiene_prod:
            # Destacar productos con un marcador circular blanco/dorado
            ax.scatter(x, y, s=210, c="#FFD166", edgecolors="#000000", linewidths=1.8, zorder=5)
            ax.text(
                x, y, prods_ids.replace("|", "\n"),
                ha="center", va="center", fontsize=6.5,
                fontweight="bold", color="#000000", zorder=6
            )
        elif tipo == "RACK":
            ax.text(x, y, f"R\nZ{z_id}", ha="center", va="center", fontsize=7, fontweight="bold", color="white")
        elif tipo == "DESPACHO":
            ax.text(x, y, f"DSP\nZ{z_id}", ha="center", va="center", fontsize=6.5, fontweight="bold", color="white")
        elif tipo == "PUERTA":
            ax.text(x, y, f"PTA\nZ{z_id}", ha="center", va="center", fontsize=6.5, fontweight="bold", color="yellow")
        elif tipo == "PASILLO":
            if sentido in FlechasSentido:
                dx, dy = FlechasSentido[sentido]
                ax.arrow(
                    x - dx * 0.5, y - dy * 0.5, dx, dy,
                    head_width=0.22, head_length=0.18,
                    fc="#222222", ec="#222222", alpha=0.65, zorder=3
                )
            else:
                ax.text(x, y, f"Z{z_id}", ha="center", va="center", fontsize=6.5, color="#111111", alpha=0.7)

    ax.set_xticks(range(max_x))
    ax.set_yticks(range(max_y))
    ax.set_xlabel("Coordenada X (Columnas del Warehouse)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Coordenada Y (Filas del Warehouse)", fontsize=11, fontweight="bold")
    ax.set_title(
        "Distribución de Zonas en el Warehouse mediante Clustering Espectral\n"
        "(Basado en Distancia Topológica Real sobre el Grafo de Pasillos)",
        fontsize=13, fontweight="bold", pad=15
    )

    # Construir leyenda combinada (Zonas + Elementos)
    parches_leyenda = [
        mpatches.Patch(facecolor=color, edgecolor="black", label=etiqueta)
        for _, (color, etiqueta) in sorted(leyenda_zonas.items())
    ]
    parches_leyenda.append(mpatches.Patch(facecolor="#888888", edgecolor="black", hatch="///", label="Estructura de Rack (Impenetrable)"))
    parches_leyenda.append(mpatches.Patch(facecolor="#888888", edgecolor="black", hatch="..", label="Zona de Despacho / Puerta"))
    parches_leyenda.append(mpatches.Patch(facecolor="#FFD166", edgecolor="black", label="Ubicación de Producto (P001..P008)"))

    ax.legend(
        handles=parches_leyenda,
        loc="upper center", bbox_to_anchor=(0.5, -0.07),
        ncol=3, frameon=True, fontsize=9
    )

    plt.tight_layout()
    plt.savefig(guardar_png, bbox_inches="tight")
    print(f"[OK] Gráfico guardado exitosamente en '{guardar_png}'.")
    plt.show()


if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else "distribucion_zonas_espectral.csv"
    datos = cargar_datos_csv(archivo)
    graficar_por_consola_desde_csv(datos)
    graficar_ventana_matplotlib(datos)