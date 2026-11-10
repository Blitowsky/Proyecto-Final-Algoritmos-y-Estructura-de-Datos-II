

# Proyecto finalizado, entregado y expuesto con éxito. Nota obtenida: 9 (nueve)


# Simulación de Warehouse

## Descripción

Este proyecto desarrolla una simulación de un depósito logístico utilizando Python, aplicando algoritmos y estructuras de datos para optimizar la preparación de pedidos.

El sistema permite representar un depósito con racks, productos, pedidos y operarios (*pickers*), además de comparar diferentes métodos de agrupamiento de pedidos.

## Funcionalidades

- Creación de depósitos a partir de archivos JSON.
- Representación gráfica del depósito mediante PyQt6.
- Gestión de productos, pedidos y pickers.
- Generación de Waves para agrupar pedidos.
- Agrupamiento mediante centroides y clustering espectral.
- Cálculo de distancias Manhattan y Euclidiana.
- Recorridos mediante algoritmos de grafos.
- Guardado y recuperación de simulaciones.
- Comparación de resultados de los algoritmos.

## Tecnologías utilizadas

- **Python:** lenguaje principal.
- **PyQt6:** interfaz gráfica.
- **NumPy:** operaciones numéricas.
- **Pandas:** procesamiento de datos.
- **Git y GitHub:** control de versiones.

## Estructuras de datos

El proyecto implementa estructuras propias, entre ellas:

- **LinkedList:** lista enlazada.
- **Dictionary:** tabla hash.
- **Graph:** representación de grafos.
- **Wave:** agrupamiento de pedidos.

## Instalación


### 1. Crear un entorno virtual dentro de la raiz del proyecto

```bash
python3 -m venv .venv
```

### 2. Activar el entorno virtual

En Linux:

```bash
source .venv/bin/activate
```
En Windows:

```bash
source .venv\Scripts\activate.bat
```

### 3. Instalar dependencias

En Linux:

```bash
pip install -r requirements.txt
```
En Windows:

```bash
python -m pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

En Linux:

```bash
PYTHONPATH=src python src/ui/interfaz.py
```

En Windows:
```bash
set PYTHONPATH=src
python src\ui\interfaz.py
```

## Algoritmos utilizados

### Algoritmos de recorrido

- BFS
- DFS
- Dijkstra
- A*

### Algoritmos de agrupamiento

**Método del centroide:** utiliza la posición central de los productos para determinar la cercanía entre pedidos.

**Clustering espectral:** utiliza técnicas de agrupamiento basadas en similitudes entre los pedidos.

## Persistencia

El sistema permite guardar y recuperar el estado de un depósito mediante serialización con `pickle`.

## Documentacion

Se genera automaticamente al ejectura: 

```bash
PYTHONPATH=src pdoc src/
```

## Autores
- Matias Cuneo
- Pablo Morata
- Emiliano Germani
- Mariano Robledo
