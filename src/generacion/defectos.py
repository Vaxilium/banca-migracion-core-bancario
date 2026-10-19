"""Inyeccion controlada de defectos sinteticos con registro de verdad de terreno.

Cada defecto inyectado queda registrado en la lista `verdad` para medir con datos
la deteccion real del pipeline y del perfilado (nunca se reportan tasas a mano).
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha, fecha_desde_aammdd

VARIANTES_FECHA_IMPOSIBLE = ("133201", "000230", "023201", "124506")

VARIANTES_PROVINCIA = ("ZZ", "XX")


class Inyector:
    """Aplica defectos por entidad y acumula la verdad de terreno."""

    def __init__(self, rng: np.random.Generator, tasas: dict) -> None:
        self.rng = rng
        self.tasas = tasas
        self.verdad: list[dict] = []

    def _registrar(self, entidad: str, tipo: str, clave, detalle: str) -> None:
        self.verdad.append(
            {"entidad": entidad, "tipo_defecto": tipo, "clave": str(clave), "detalle": detalle}
        )

    def _elegir_indices(self, cantidad: int, tasa: float) -> np.ndarray:
        cuantos = int(round(cantidad * tasa))
        if cuantos <= 0:
            return np.array([], dtype=int)
        return self.rng.choice(cantidad, size=min(cuantos, cantidad), replace=False)

    def clientes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Duplicados por variante de nombre, documentos invalidos y fechas imposibles."""
        tasas = self.tasas["clientes"]
        df = df.copy()
        base_nombres = df["nombre_completo"].astype(str)

        indices = self._elegir_indices(len(df), tasas["duplicado_nombre_variante"])
        if len(indices):
            duplicados = df.iloc[indices].copy()
            siguiente = int(df["id_cliente"].max()) + 1
            duplicados["id_cliente"] = np.arange(siguiente, siguiente + len(duplicados))
            nuevos_nombres = []
            for posicion, indice in enumerate(indices):
                palabras = base_nombres.iloc[indice].split()
                if posicion % 3 == 0 and len(palabras) >= 3:
                    nuevos_nombres.append(
                        " ".join([palabras[1], palabras[0], *palabras[2:]])
                    )
                elif posicion % 3 == 1:
                    nuevos_nombres.append(
                        base_nombres.iloc[indice].replace(" ", "  ", 1)
                    )
                else:
                    primera = palabras[0]
                    nuevos_nombres.append(
                        " ".join([primera[:-1] + ("O" if primera[-1] != "O" else "A"),
                                  *palabras[1:]])
                    )
            duplicados["nombre_completo"] = nuevos_nombres
            df = pd.concat([df, duplicados], ignore_index=True)
            for indice_nuevo, id_original in zip(
                duplicados["id_cliente"], df["id_cliente"].iloc[indices], strict=False
            ):
                self._registrar(
                    "clientes", "duplicado_nombre_variante", id_original,
                    f"creado id_cliente={indice_nuevo}",
                )

        indices = self._elegir_indices(len(df), tasas["documento_invalido"])
        for indice in indices:
            documento = str(df.at[indice, "numero_documento"]).strip()
            if documento and documento[-1].isdigit():
                reemplazo = (int(documento[-1]) + 1) % 10
                df.at[indice, "numero_documento"] = documento[:-1] + str(reemplazo)
            else:
                df.at[indice, "numero_documento"] = documento + "X"
            self._registrar(
                "clientes", "documento_invalido", df.at[indice, "id_cliente"],
                f"documento={df.at[indice, 'numero_documento']}",
            )

        indices = self._elegir_indices(len(df), tasas["documento_repetido_otro_cliente"])
        if len(indices) >= 2:
            mitad = len(indices) // 2
            for origen, destino in zip(indices[:mitad], indices[mitad:], strict=False):
                if origen == destino:
                    continue
                df.at[destino, "numero_documento"] = df.at[origen, "numero_documento"]
                df.at[destino, "tipo_documento"] = df.at[origen, "tipo_documento"]
                self._registrar(
                    "clientes", "documento_repetido_otro_cliente", df.at[destino, "id_cliente"],
                    f"documento copiado de id_cliente={df.at[origen, 'id_cliente']}",
                )

        indices = self._elegir_indices(len(df), tasas["fecha_nacimiento_imposible"])
        for indice in indices:
            df.at[indice, "fecha_nacimiento"] = str(
                self.rng.choice(VARIANTES_FECHA_IMPOSIBLE)
            )
            self._registrar(
                "clientes", "fecha_nacimiento_imposible", df.at[indice, "id_cliente"],
                f"fecha={df.at[indice, 'fecha_nacimiento']}",
            )
        return df

    def documentos(self, df: pd.DataFrame, fecha_extraccion: date) -> pd.DataFrame:
        """Documentos vencidos que siguen marcados como validados (vencido sin marcar)."""
        df = df.copy()
        vencimiento = df["fecha_vencimiento"].astype(str)
        expirado = np.array(
            [
                (v.isdigit() and v != "000000" and fecha_desde_aammdd(v) < fecha_extraccion)
                for v in vencimiento
            ]
        )
        candidatas = df.index[expirado & (df["validado"] == "N")]
        indices = self._elegir_indices(
            len(candidatas), self.tasas["documentos"]["vencido_sin_marcar"]
        )
        for indice in candidatas[indices]:
            df.at[indice, "validado"] = "S"
            self._registrar(
                "documentos", "vencido_sin_marcar", df.at[indice, "numero_documento"],
                f"id_cliente={df.at[indice, 'id_cliente']} "
                f"vencimiento={df.at[indice, 'fecha_vencimiento']}",
            )
        return df

    def direcciones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Direcciones incompletas: sin localidad, sin provincia o sin codigo postal."""
        df = df.copy()
        indices = self._elegir_indices(len(df), self.tasas["direcciones"]["incompleta"])
        for indice in indices:
            campo = str(self.rng.choice(["localidad", "provincia", "codigo_postal"]))
            df.at[indice, campo] = ""
            self._registrar(
                "direcciones", "direccion_incompleta", df.at[indice, "id_cliente"],
                f"campo vacio: {campo}",
            )
        return df

    def cuentas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cuentas huerfanas, estados desconocidos y productos sin equivalente."""
        tasas = self.tasas["cuentas"]
        df = df.copy()
        indices = self._elegir_indices(len(df), tasas["huerfana"])
        for posicion, indice in enumerate(indices):
            df.at[indice, "id_cliente"] = 99900000 + posicion
            self._registrar(
                "cuentas", "cuenta_huerfana", df.at[indice, "id_cuenta"],
                f"id_cliente inexistente: {df.at[indice, 'id_cliente']}",
            )
        indices = self._elegir_indices(len(df), tasas["estado_desconocido"])
        for indice in indices:
            df.at[indice, "estado_cuenta"] = "X"
            self._registrar(
                "cuentas", "estado_desconocido", df.at[indice, "id_cuenta"],
                "estado X inyectado sobre cuenta activa",
            )
        candidatas = df.index[df["codigo_producto"].isin(["CA", "CC"])]
        indices = self._elegir_indices(len(candidatas), tasas["producto_fuera_alcance"])
        for indice in candidatas[indices]:
            df.at[indice, "codigo_producto"] = "TR"
            self._registrar(
                "cuentas", "producto_fuera_alcance", df.at[indice, "id_cuenta"],
                "producto TR (tarjeta de credito) inyectado",
            )
        candidatas = df.index[df["codigo_producto"].isin(["CA", "CC", "CJ"])]
        indices = self._elegir_indices(len(candidatas), tasas["producto_desconocido"])
        for indice in candidatas[indices]:
            df.at[indice, "codigo_producto"] = "ZZ"
            self._registrar(
                "cuentas", "producto_desconocido", df.at[indice, "id_cuenta"],
                "producto ZZ sin equivalente inyectado",
            )
        return df

    def movimientos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Signos invertidos en comisiones, fechas imposibles y duplicados de reproceso."""
        tasas = self.tasas["movimientos"]
        df = df.copy()
        comisiones = df.index[df["codigo_operacion"] == "06"]
        indices = self._elegir_indices(len(comisiones), tasas["signo_invertido"])
        for indice in comisiones[indices]:
            df.at[indice, "importe"] = round(-float(df.at[indice, "importe"]), 2)
            self._registrar(
                "movimientos", "signo_invertido", df.at[indice, "id_movimiento"],
                f"comision con signo invertido en cuenta {df.at[indice, 'id_cuenta']}",
            )
        indices = self._elegir_indices(len(df), tasas["fecha_imposible"])
        for indice in indices:
            df.at[indice, "fecha_movimiento"] = str(
                self.rng.choice(VARIANTES_FECHA_IMPOSIBLE)
            )
            self._registrar(
                "movimientos", "fecha_imposible", df.at[indice, "id_movimiento"],
                f"fecha={df.at[indice, 'fecha_movimiento']}",
            )
        indices = self._elegir_indices(len(df), tasas["duplicado_reproceso"])
        if len(indices):
            duplicados = df.iloc[indices].copy()
            siguiente = int(df["id_movimiento"].max()) + 1
            duplicados["id_movimiento"] = np.arange(siguiente, siguiente + len(duplicados))
            df = pd.concat([df, duplicados], ignore_index=True)
            for id_nuevo, id_original in zip(
                duplicados["id_movimiento"], df["id_movimiento"].iloc[indices], strict=False
            ):
                self._registrar(
                    "movimientos", "duplicado_reproceso", id_nuevo,
                    f"duplicado de id_movimiento={id_original}",
                )
        return df

    def saldos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Descuadres leves y graves entre saldo final y suma de movimientos."""
        tasas = self.tasas["saldos"]
        df = df.copy()
        for tipo, clave in (
            ("descuadre_leve", "descuadre_leve"),
            ("descuadre_grave", "descuadre_grave"),
        ):
            indices = self._elegir_indices(len(df), tasas[clave])
            for indice in indices:
                if tipo == "descuadre_leve":
                    delta = round(float(self.rng.uniform(0.5, 50.0)), 2)
                else:
                    delta = round(float(self.rng.uniform(500.0, 5000.0)), 2)
                if self.rng.random() < 0.5:
                    delta = -delta
                df.at[indice, "saldo_final"] = round(
                    float(df.at[indice, "saldo_final"]) + delta, 2
                )
                self._registrar(
                    "saldos", tipo, df.at[indice, "id_cuenta"], f"delta={delta}"
                )
        return df

    def prestamos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Saldo de capital incongruente con la suma de cuotas pendientes."""
        df = df.copy()
        indices = self._elegir_indices(len(df), self.tasas["prestamos"]["saldo_incongruente"])
        for indice in indices:
            factor = 1 + float(self.rng.uniform(0.005, 0.05)) * (
                1 if self.rng.random() < 0.5 else -1
            )
            df.at[indice, "saldo_capital"] = round(
                float(df.at[indice, "saldo_capital"]) * factor, 2
            )
            self._registrar(
                "prestamos", "saldo_incongruente", df.at[indice, "id_prestamo"],
                f"factor={factor:.4f}",
            )
        return df

    def plazos_fijos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vencimiento incongruente con constitucion mas plazo en dias."""
        df = df.copy()
        indices = self._elegir_indices(
            len(df), self.tasas["plazos_fijos"]["vencimiento_incongruente"]
        )
        for indice in indices:
            try:
                vencimiento: date = fecha_desde_aammdd(str(df.at[indice, "fecha_vencimiento"]))
            except ValueError:
                continue
            desvio = int(self.rng.integers(10, 31)) * (1 if self.rng.random() < 0.5 else -1)
            nuevo = vencimiento + timedelta(days=desvio)
            df.at[indice, "fecha_vencimiento"] = aammdd_desde_fecha(nuevo)
            self._registrar(
                "plazos_fijos", "vencimiento_incongruente", df.at[indice, "id_plazo"],
                f"desvio={desvio} dias",
            )
        return df

    def mandatos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mandatos apuntando a cuentas inexistentes."""
        df = df.copy()
        indices = self._elegir_indices(
            len(df), self.tasas["mandatos"]["cuenta_inexistente"]
        )
        for indice in indices:
            cuenta = "999" + "".join(
                str(d) for d in self.rng.integers(0, 10, 7)
            )
            df.at[indice, "id_cuenta_debito"] = cuenta
            self._registrar(
                "mandatos", "cuenta_inexistente", df.at[indice, "id_mandato"],
                f"cuenta inexistente: {cuenta}",
            )
        return df
