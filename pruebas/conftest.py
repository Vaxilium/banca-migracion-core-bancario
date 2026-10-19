"""Fixtures compartidas por las pruebas del proyecto."""

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.comun.rutas import CONCILIACION, DESTINO, RESULTADOS, VERDAD

RUTA_DESTINO = DESTINO / "ensayo_v3"


@pytest.fixture(scope="session")
def con():
    """Conexion DuckDB en memoria para consultar los Parquet del destino."""
    conexion = duckdb.connect()
    yield conexion
    conexion.close()


@pytest.fixture(scope="session")
def tablas(con):
    """Lee una tabla del destino v3, cacheada por corrida."""
    if not RUTA_DESTINO.exists():
        pytest.skip("destino no generado; ejecutar make todo")

    cache: dict[str, pd.DataFrame] = {}

    def leer(nombre: str) -> pd.DataFrame:
        if nombre not in cache:
            ruta = RUTA_DESTINO / f"{nombre}.parquet"
            cache[nombre] = con.execute(f"SELECT * FROM read_parquet('{ruta}')").df()
        return cache[nombre]

    return leer


@pytest.fixture(scope="session")
def conciliacion_v3() -> dict:
    """Resultado de conciliacion del ensayo 3."""
    ruta = CONCILIACION / "conciliacion_ensayo_v3.json"
    if not ruta.exists():
        pytest.skip("conciliacion no generada; ejecutar make conciliacion")
    return json.loads(ruta.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def verdad() -> pd.DataFrame:
    """Defectos inyectados en el legado, como verdad de contraste."""
    ruta = VERDAD / "defectos_inyectados.csv"
    if not ruta.exists():
        pytest.skip("verdad no generada; ejecutar make datos")
    return pd.read_csv(ruta, dtype=str)


@pytest.fixture(scope="session")
def rechazos_v3() -> pd.DataFrame:
    """Rechazos del ensayo 3."""
    ruta = RESULTADOS / "rechazos_ensayo_v3.csv"
    if not ruta.exists():
        pytest.skip("rechazos no generados; ejecutar make migracion")
    return pd.read_csv(ruta, dtype=str)


@pytest.fixture(scope="session")
def ruta_resultados() -> Path:
    """Directorio de resultados del pipeline."""
    return RESULTADOS
