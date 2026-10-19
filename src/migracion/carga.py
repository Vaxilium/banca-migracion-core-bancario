"""Carga del destino en Parquet con DuckDB y validacion de contratos.

La base por ensayo se guarda como una tabla Parquet por entidad en
datos/destino/ensayo_v{n}. La carga delta del corte reemplaza filas por clave
primaria (saldos) o inserta filas nuevas (cuentas y movimientos).
"""

from pathlib import Path

import duckdb
import pandas as pd

from src.comun.rutas import DESTINO

CLAVES = {
    "cliente": ["id_cliente"],
    "documento_cliente": ["id_documento"],
    "domicilio_cliente": ["id_domicilio"],
    "cuenta": ["id_cuenta"],
    "saldo_cuenta": ["id_cuenta"],
    "movimiento": ["id_movimiento"],
    "prestamo": ["id_prestamo"],
    "cuota_prestamo": ["id_prestamo", "numero_cuota"],
    "plazo_fijo": ["id_plazo"],
    "mandato_debito": ["id_mandato"],
    "cuenta_contable": ["codigo_contable"],
    "saldo_contable": ["codigo_contable", "periodo"],
}


def carpeta_ensayo(version: int) -> Path:
    """Carpeta de destino del ensayo indicado."""
    carpeta = DESTINO / f"ensayo_v{version}"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def escribir_tabla(df: pd.DataFrame, tabla: str, version: int) -> int:
    """Escribe (o reemplaza) la tabla del ensayo y devuelve el conteo de filas."""
    archivo = carpeta_ensayo(version) / f"{tabla}.parquet"
    con = duckdb.connect()
    try:
        con.register("nuevo", df)
        con.execute(f"COPY (SELECT * FROM nuevo) TO '{archivo}' (FORMAT PARQUET)")
        return int(con.sql("SELECT count(*) FROM nuevo").fetchone()[0])
    finally:
        con.close()


def incorporar_delta(df: pd.DataFrame, tabla: str, version: int) -> tuple[int, int]:
    """Upsert de la carga delta: reemplaza filas por clave e inserta nuevas.

    Devuelve (insertadas, reemplazadas).
    """
    archivo = carpeta_ensayo(version) / f"{tabla}.parquet"
    con = duckdb.connect()
    try:
        claves = CLAVES[tabla]
        con.execute(f"CREATE VIEW previo AS SELECT * FROM read_parquet('{archivo}')")
        con.register("nuevo", df)
        condicion = " AND ".join(f"previo.{clave} = nuevo.{clave}" for clave in claves)
        insertadas = int(
            con.sql(
                f"SELECT count(*) FROM nuevo ANTI JOIN previo ON {condicion}"
            ).fetchone()[0]
        )
        reemplazadas = int(
            con.sql(
                f"SELECT count(*) FROM nuevo SEMI JOIN previo ON {condicion}"
            ).fetchone()[0]
        )
        con.execute(
            f"COPY (SELECT * FROM previo ANTI JOIN nuevo ON {condicion} "
            f"UNION ALL BY NAME SELECT * FROM nuevo) TO '{archivo}' (FORMAT PARQUET)"
        )
        return insertadas, reemplazadas
    finally:
        con.close()


def contar_tabla(tabla: str, version: int) -> int:
    """Cuenta las filas persistidas de una tabla del ensayo."""
    archivo = carpeta_ensayo(version) / f"{tabla}.parquet"
    con = duckdb.connect()
    try:
        return int(con.sql(f"SELECT count(*) FROM read_parquet('{archivo}')").fetchone()[0])
    finally:
        con.close()
