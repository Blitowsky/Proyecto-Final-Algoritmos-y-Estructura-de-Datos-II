def rot(n: int, x: int, y: int, rx: int, ry: int) -> tuple[int, int]:
    """
    Función auxiliar para rotar/voltear el cuadrante fractal de Hilbert.
    Debido a que Python no tiene paso por referencia (punteros *x, *y), 
    la función retorna los valores actualizados como una tupla (x, y).
    """
    if ry == 0:
        if rx == 1:
            # Cuadrante Inferior Derecho (3): Invertimos coordenadas restándolas del tamaño actual
            x = n - 1 - x
            y = n - 1 - y
            
        # Cuadrante Inferior Izquierdo (0) y Derecho (3): Transposición geométrica
        x, y = y, x 
        
    return x, y

def xy2d(n: int, x: int, y: int) -> int:
    """Convierte coordenadas (x,y) a índice de Hilbert d."""
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
    """Convierte índice de Hilbert d a coordenadas (x,y)."""
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