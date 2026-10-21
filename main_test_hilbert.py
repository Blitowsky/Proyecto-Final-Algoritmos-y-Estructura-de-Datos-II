# main_test_hilbert.py
from src.core.warehouse_generator import generar_dos_grafos_warehouse
from src.core.wave_manager.zone_generator import (
    ordenar_y_particionar_por_hilbert,
    imprimir_reporte_distribucion
)

def solicitar_entero_positivo(mensaje: str, minimo: int = 1) -> int:
    """Función auxiliar para validar las entradas temporales de testing por consola."""
    while True:
        try:
            valor = int(input(mensaje))
            if valor >= minimo:
                return valor
            print(f"  [!] Por favor, ingresá un número mayor o igual a {minimo}.")
        except ValueError:
            print("  [!] Entrada inválida. Debés ingresar un número entero.")


def main():
    print("=====================================================================")
    print("   ENTORNO DE TESTING: PARTICIÓN DE GRAFOS CON CURVAS DE HILBERT")
    print("=====================================================================\n")

    # Parámetro 1: Pedir tamaño del Warehouse (temporal para testing)
    ancho_x = solicitar_entero_positivo("1. Ingresá el ancho (eje X) del Warehouse (ej. 8, 12, 18): ", minimo=4)
    largo_y = solicitar_entero_positivo("2. Ingresá el largo (eje Y) del Warehouse (ej. 6, 10, 16): ", minimo=4)

    max_nodos = ancho_x * largo_y
    # Parámetro 4: Pedir cantidad de zonas para particionar la lista de nodos
    cantidad_zonas = solicitar_entero_positivo(
        f"3. Ingresá la cantidad de zonas a generar (1 a {max_nodos}): ", 
        minimo=1
    )
    if cantidad_zonas > max_nodos:
        print(f"  [*] Ajustando cantidad de zonas al máximo de nodos disponibles ({max_nodos}).")
        cantidad_zonas = max_nodos

    # Parámetro 2: Generar dos grafos basados en la estructura de un Warehouse
    print("\nGenerando estructuras de grafos en TablaHashCuadratica...")
    grafo_paralelo, grafo_cruzado = generar_dos_grafos_warehouse(ancho_x, largo_y)

    # Procesar y mostrar Grafo 1
    resultado_g1 = ordenar_y_particionar_por_hilbert(
        grafo_paralelo, ancho_x, largo_y, cantidad_zonas
    )
    imprimir_reporte_distribucion("Grafo 1 - Layout de Pasillos Paralelos", resultado_g1)

    # Procesar y mostrar Grafo 2
    resultado_g2 = ordenar_y_particionar_por_hilbert(
        grafo_cruzado, ancho_x, largo_y, cantidad_zonas
    )
    imprimir_reporte_distribucion("Grafo 2 - Layout Modular con Pasillo Central", resultado_g2)


if __name__ == "__main__":
    main()