"""Escritura de archivos de ancho fijo guiada por los disenos YAML del legado."""

from pathlib import Path

import numpy as np
import pandas as pd

from src.comun.yaml_util import cargar_yaml


class DisenoError(ValueError):
    """Error de consistencia en un diseno de registro o en los datos a escribir."""


class DisenoAnchoFijo:
    """Representa un diseno de registro y escribe DataFrames en ancho fijo."""

    def __init__(self, ruta_yaml: str | Path) -> None:
        datos = cargar_yaml(ruta_yaml)
        self.entidad: str = datos["entidad"]
        self.archivo: str = datos["archivo"]
        self.longitud_registro: int = int(datos["longitud_registro"])
        self.codificacion: str = datos.get("codificacion", "latin-1")
        self.descripcion: str = datos.get("descripcion", "")
        self.campos: list[dict] = datos["campos"]
        posicion = 1
        for campo in self.campos:
            if int(campo["inicio"]) != posicion:
                raise DisenoError(
                    f"campo {campo['nombre']} inicia en {campo['inicio']}, se esperaba {posicion}"
                )
            posicion += int(campo["longitud"])
        if posicion - 1 != self.longitud_registro:
            raise DisenoError(
                f"la suma de campos ({posicion - 1}) no coincide con la longitud "
                f"del registro ({self.longitud_registro})"
            )

    def _columna(self, df: pd.DataFrame, campo: dict) -> pd.Series:
        nombre = campo["nombre"]
        largo = int(campo["longitud"])
        tipo = campo["tipo"]
        if tipo == "relleno":
            return pd.Series((str(campo.get("relleno", " ")) * largo,) * len(df), index=df.index)
        if tipo == "texto":
            serie = df[nombre].fillna("").astype(str)
            return serie.str.slice(0, largo).str.ljust(largo)
        if tipo == "entero":
            serie = pd.to_numeric(df[nombre], errors="coerce").fillna(0).astype("int64")
            texto = serie.astype(str).str.zfill(largo)
            if (texto.str.len() > largo).any():
                ejemplo = texto[texto.str.len() > largo].iloc[0]
                raise DisenoError(
                    f"campo {nombre} excede su longitud ({largo}): {ejemplo!r}"
                )
            return texto
        if tipo == "fecha":
            serie = df[nombre].fillna("000000").astype(str)
            return serie.str.slice(0, largo).str.zfill(largo)
        if tipo == "hora":
            serie = pd.to_numeric(df[nombre], errors="coerce").fillna(0).astype("int64")
            return serie.astype(str).str.zfill(largo)
        if tipo == "importe":
            decimales = int(campo.get("decimales", 2))
            factor = 10**decimales
            valores = pd.to_numeric(df[nombre], errors="coerce").fillna(0.0).astype(float)
            enteros = np.rint(valores.to_numpy() * factor).astype("int64")
            signos = np.where(enteros < 0, "-", "+")
            digitos = np.char.zfill(np.abs(enteros).astype(str), largo - 1)
            return pd.Series(digitos + signos, index=df.index)
        raise DisenoError(f"tipo de campo desconocido: {tipo}")

    def formatear(self, df: pd.DataFrame) -> pd.Series:
        """Devuelve una serie de registros de longitud fija."""
        registros = None
        for campo in self.campos:
            columna = self._columna(df, campo)
            registros = columna if registros is None else registros.str.cat(columna)
        largos = registros.str.len()
        if not (largos == self.longitud_registro).all():
            ejemplo = registros[largos != self.longitud_registro].iloc[0]
            raise DisenoError(f"registro con longitud invalida ({len(ejemplo)}): {ejemplo!r}")
        return registros

    def escribir(self, df: pd.DataFrame, ruta_salida: str | Path) -> int:
        """Escribe el DataFrame como archivo de ancho fijo y devuelve el conteo."""
        registros = self.formatear(df)
        contenido = "\n".join(registros.tolist()) + "\n"
        Path(ruta_salida).write_bytes(contenido.encode(self.codificacion, errors="replace"))
        return len(registros)
