# src/core/wave_manager/hilbert.py

def obtener_dimension_potencia_2(ancho_x: int, largo_y: int) -> int:
    """
    Calcula la menor potencia de 2 (n = 2^k) que sea mayor o igual 
    a la dimensión máxima del Warehouse (Padding fractal).
    """
    max_dim = max(ancho_x, largo_y)
    n = 1
    while n < max_dim:
        n *= 2
    return max(2, n)


def rot(n: int, x: int, y: int, rx: int, ry: int) -> tuple[int, int]:
    """Rota y voltea el cuadrante adecuadamente según los bits rx y ry."""
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y


def xy2d(n: int, x: int, y: int) -> int:
    """
    Convierte una coordenada 2D (x, y) en su distancia escalar 'd' 
    sobre una curva de Hilbert de dimensión n x n (donde n es potencia de 2).
    """
    d = 0
    s = n // 2
    while s > 0:
        rx = 1 if (x & s) > 0 else 0
        ry = 1 if (y & s) > 0 else 0
        d += s * s * ((3 * rx) ^ ry)
        x, y = rot(s, x, y, rx, ry)
        s //= 2
    return d


def d2xy(n: int, d: int) -> tuple[int, int]:
    """Convierte un índice de Hilbert 'd' de vuelta a su coordenada (x, y)."""
    x = 0
    y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        x, y = rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y