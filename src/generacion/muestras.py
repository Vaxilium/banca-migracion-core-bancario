"""Publica muestras pequenas y seudoanonimizadas del destino."""

from __future__ import annotations

import sys

import duckdb

from src.comun.enmascaramiento import enmascarar_dataframe, enmascarar_direccion
from src.comun.rutas import DESTINO, MUESTRAS
from src.comun.semilla import SEMILLA

TABLAS = {
    "cliente": 100,
    "documento_cliente": 100,
    "domicilio_cliente": 100,
    "cuenta": 100,
    "movimiento": 200,
    "prestamo": 100,
    "plazo_fijo": 100,
    "mandato_debito": 100,
}

MASCARAS = {
    "cliente": {
        "nombre_completo": "nombre",
        "telefono": "telefono",
        "correo": "correo",
    },
    "documento_cliente": {"numero_documento": "documento:tipo_documento"},
    "cuenta": {"telefono_alternativo": "telefono"},
}

COLUMNAS_OMITIDAS = {
    "cliente": ["nombre_normalizado", "observacion"],
    "cuenta": ["observacion"],
}


def main() -> int:
    """Genera un CSV por entidad con datos publicables."""
    origen = DESTINO / "ensayo_v3"
    if not origen.exists():
        raise FileNotFoundError(
            f"no existe {origen}; ejecutar el pipeline antes de publicar muestras"
        )
    MUESTRAS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        for tabla, filas in TABLAS.items():
            consulta = (
                f"SELECT * FROM read_parquet('{origen / f'{tabla}.parquet'}') "
                f"USING SAMPLE {filas} ROWS (reservoir, {SEMILLA})"
            )
            datos = con.execute(consulta).df()
            datos = datos.drop(columns=COLUMNAS_OMITIDAS.get(tabla, []), errors="ignore")
            datos = enmascarar_dataframe(datos, MASCARAS.get(tabla, {}))
            if tabla == "domicilio_cliente":
                datos["calle"] = [
                    enmascarar_direccion(calle, numero)
                    for calle, numero in zip(datos["calle"], datos["numero"], strict=False)
                ]
            ruta = MUESTRAS / f"{tabla}.csv"
            datos.to_csv(ruta, index=False, encoding="utf-8")
            print(f"{ruta.name}: {len(datos)} filas")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
