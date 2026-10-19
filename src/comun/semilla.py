"""Semilla unica del proyecto para garantizar reproducibilidad total."""

import random

import numpy as np

SEMILLA = 20261019


def generador_numpy() -> np.random.Generator:
    """Devuelve un generador de numeros aleatorios determinista."""
    return np.random.default_rng(SEMILLA)


def generador_aleatorio() -> random.Random:
    """Devuelve un generador de la libreria estandar con la misma semilla."""
    return random.Random(SEMILLA)
