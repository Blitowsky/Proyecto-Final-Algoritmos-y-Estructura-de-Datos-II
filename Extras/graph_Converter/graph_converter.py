from .parsers import (
    parse_ev_set,
    parse_adj_list,
    parse_inc_list,
    parse_adj_matrix,
    parse_inc_matrix
)
from .exporters import (
    export_ev_set,
    export_adj_list,
    export_inc_list,
    export_adj_matrix,
    export_inc_matrix
)

# Diccionario Dispatcher de Entrada (Mapea la flag con su función Parser)
PARSERS = {
    "ev_set": parse_ev_set,
    "adj_list": parse_adj_list,
    "inc_list": parse_inc_list,
    "adj_matrix": parse_adj_matrix,
    "inc_matrix": parse_inc_matrix
}

# Diccionario Dispatcher de Salida (Mapea la flag con su función Exporter)
EXPORTERS = {
    "ev_set": export_ev_set,
    "adj_list": export_adj_list,
    "inc_list": export_inc_list,
    "adj_matrix": export_adj_matrix,
    "inc_matrix": export_inc_matrix
}


def cargar_a_memoria(data, input_flag: str):
    """
    Recibe un grafo en cualquiera de los 5 formatos y devuelve 
    la representación intermedia oficial (TablaHashCuadratica).
    Ideal para cargar el Warehouse al iniciar la aplicación.
    """
    if input_flag not in PARSERS:
        raise ValueError(f"Formato de entrada '{input_flag}' no válido. Opciones: {list(PARSERS.keys())}")
    
    parser_func = PARSERS[input_flag]
    return parser_func(data)


def exportar_de_memoria(standard_graph, output_flag: str):
    """
    Recibe la TablaHashCuadratica en memoria y la transforma 
    a cualquiera de los 5 formatos de salida.
    """
    if output_flag not in EXPORTERS:
        raise ValueError(f"Formato de salida '{output_flag}' no válido. Opciones: {list(EXPORTERS.keys())}")
    
    exporter_func = EXPORTERS[output_flag]
    return exporter_func(standard_graph)


def convertir_grafo(data, input_flag: str, output_flag: str):
    """
    Función principal de conversión directa entre formatos mediante flags.
    Pasa por la TablaHashCuadratica como representación intermedia.
    """
    # 1. Parsear la entrada a la estructura estándar en memoria
    grafo_en_memoria = cargar_a_memoria(data, input_flag)
    
    # 2. Exportar desde la memoria hacia el formato de salida requerido
    resultado = exportar_de_memoria(grafo_en_memoria, output_flag)
    
    return resultado


def imprimir_lista_adyacencia(grafo_hash):
    """
    Función de utilidad para depuración visual por consola.
    """
    print("\n--- Lista de Adyacencia (Tabla Hash en Memoria) ---")
    if grafo_hash.tamaño == 0:
        print("El grafo está vacío.")
        print("---------------------------------------------------\n")
        return

    for celda in grafo_hash.tabla:
        estado, clave, adyacentes = celda
        if estado == grafo_hash.OCUPADO:
            print(f"[{clave}] -> {adyacentes}")
    print("---------------------------------------------------\n")