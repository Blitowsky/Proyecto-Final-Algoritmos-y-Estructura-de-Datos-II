import json

def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    if config["width"] <= 0 or config["height"] <= 0:
        raise ValueError("El ancho y alto deben ser positivos.")
    return config
