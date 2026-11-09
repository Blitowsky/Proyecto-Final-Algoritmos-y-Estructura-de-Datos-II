## T1 - Comparación de estrategias (mismo escenario, distintas waves)

### basico

| metric | A - Sin estrategia | B - Centroide de pedidos | C - Clustering espectral | B - Centroide de pedidos vs A (%) | C - Clustering espectral vs A (%) |
|---|---|---|---|---|---|
| ticks | 122 | 122 | 81 | 0.000 | -33.6 |
| assignments | 5 | 5 | 4 | 0.000 | -20.0 |
| planned_distance | 163.0 | 163.0 | 125.0 | 0.000 | -23.3 |
| steps | 163 | 163 | 125 | 0.000 | -23.3 |
| waits | 1 | 1 | 1 | 0.000 | 0.000 |
| reroutes | 0 | 0 | 0 | - | - |
| side_steps | 1 | 1 | 1 | 0.000 | 0.000 |
| wall_ms | 62.9 | 38.1 | 112.5 | -39.4 | 78.9 |

### grande

| metric | A - Sin estrategia | B - Centroide de pedidos | C - Clustering espectral | B - Centroide de pedidos vs A (%) | C - Clustering espectral vs A (%) |
|---|---|---|---|---|---|
| ticks | 1,698 | 1,542 | 497 | -9.187 | -70.7 |
| assignments | 40 | 11 | 9 | -72.5 | -77.5 |
| planned_distance | 6,251.0 | 4,779.0 | 1,516.0 | -23.5 | -75.7 |
| steps | 6,257 | 4,788 | 1,521 | -23.5 | -75.7 |
| waits | 18 | 19 | 8 | 5.556 | -55.6 |
| reroutes | 4 | 6 | 2 | 50.0 | -50.0 |
| side_steps | 0 | 2 | 2 | - | - |
| wall_ms | 9,073.4 | 7,720.6 | 6,443.1 | -14.9 | -29.0 |

`wall_ms` es la media de tiempo que le tomó a la simulación terminar (1 repeticiones), no solo planear la ruta. % negativo = menos que la primer estrategia.
