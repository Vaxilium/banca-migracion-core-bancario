"""Transformacion del legado al modelo destino con reglas por version de ensayo.

Cada entidad se procesa con funciones vectorizadas: se rechazan las filas que no
pueden migrar, se envian a revision las dudosas y se anota en bitacora toda
decision con su evidencia (regla, clave y detalle). Las fechas que quedan antes
de una referencia (por ejemplo un vencimiento anterior a su emision) se
reinterpretan sumando un siglo, tecnica de reparacion documentada en el ADR-008.
"""

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.migracion import reglas

MAPA_TIPO_CUENTA = {"A": "activo", "P": "pasivo", "R": "resultado"}
MAPA_TIPO_DIRECCION = {"P": "particular", "L": "laboral"}


def _reparar_siglo(serie: pd.Series, referencia: pd.Series) -> tuple[pd.Series, np.ndarray]:
    """Suma 100 anios a las fechas anteriores a su referencia (RN-03)."""
    fechas = pd.to_datetime(serie, errors="coerce")
    limite = pd.to_datetime(referencia, errors="coerce")
    anterior = (fechas.notna() & limite.notna() & (fechas < limite)).to_numpy()
    if anterior.any():
        fechas = fechas.copy()
        fechas[anterior] = fechas[anterior] + pd.DateOffset(years=100)
    return fechas, anterior


def _a_texto_nulo(serie: pd.Series, sin_valor: np.ndarray) -> np.ndarray:
    """Convierte una columna a object y reemplaza por None las posiciones indicadas."""
    resultado = serie.astype(object).to_numpy(copy=True)
    resultado[sin_valor] = None
    return resultado


@dataclass
class Contexto:
    """Estado compartido de una corrida del pipeline."""

    version: int
    reglas: dict
    catalogos: dict
    fecha_extraccion: date
    fecha_corte: date
    umbral: int
    fusion: dict[int, int] = field(default_factory=dict)
    ids_clientes: set[int] = field(default_factory=set)
    ids_cuentas: set[int] = field(default_factory=set)
    ids_prestamos: set[int] = field(default_factory=set)
    ids_contables: set[str] = field(default_factory=set)

    @property
    def ventana_inicio(self) -> date:
        """Primer dia de la ventana movil de migracion."""
        return reglas.fecha_ventana(self.fecha_corte, self.reglas["ventana_meses"])

    def reasignar_cliente(self, serie: pd.Series) -> pd.Series:
        """Aplica el mapa de fusion de clientes (deduplicacion) a una columna."""
        return serie.map(lambda valor: self.fusion.get(valor, valor))


class Registro:
    """Acumula rechazos, revisiones y bitacora de una corrida."""

    def __init__(self) -> None:
        self.rechazos: list[dict] = []
        self.bitacora: list[dict] = []

    def rechazar(self, entidad, motivo, clave, detalle="", destino="rechazo") -> None:
        self.rechazos.append(
            {
                "entidad": entidad,
                "motivo": motivo,
                "destino": destino,
                "clave": str(clave),
                "detalle": str(detalle),
            }
        )

    def anotar(self, entidad, accion, clave, detalle="") -> None:
        self.bitacora.append(
            {
                "entidad": entidad,
                "accion": accion,
                "clave": str(clave),
                "detalle": str(detalle),
            }
        )


class Transformador:
    """Ejecuta las transformaciones de todas las entidades para una version."""

    def __init__(self, ctx: Contexto) -> None:
        self.ctx = ctx
        self.registro = Registro()

    # ------------------------------------------------------------------ clientes

    def clientes(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Clientes: fechas, documentos, duplicados y deduplicacion."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = pd.to_numeric(df["id_cliente"], errors="coerce").astype("int64")
        nac, val_nac = reglas.convertir_fechas(df["fecha_nacimiento"], ctx.umbral)
        alta, val_alta = reglas.convertir_fechas(df["fecha_alta"], ctx.umbral)
        for campo, valida in (("fecha_nacimiento", val_nac), ("fecha_alta", val_alta)):
            for posicion in df.index[~valida]:
                reg.rechazar(
                    "clientes",
                    "fecha_imposible",
                    df.at[posicion, "id_cliente"],
                    f"{campo}={df.at[posicion, campo]}",
                )
        df = df[val_nac & val_alta].copy()
        df["fecha_nacimiento"] = nac[val_nac & val_alta]
        df["fecha_alta"] = alta[val_nac & val_alta]

        tipo = df["tipo_documento"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "tipo_documento", codigo)
        )
        df["tipo_documento_destino"] = tipo.fillna("")
        valido = self._documento_valido(df["tipo_documento_destino"], df["numero_documento"])
        for posicion in df.index[~valido]:
            reg.rechazar(
                "clientes",
                "documento_invalido",
                df.at[posicion, "id_cliente"],
                f"documento={df.at[posicion, 'numero_documento']}",
                destino="revision",
            )
        clave_doc = df["tipo_documento_destino"] + "|" + df["numero_documento"].str.strip()
        nacimientos_por_doc = df.groupby(clave_doc)["fecha_nacimiento"].nunique()
        for posicion in df.index[(clave_doc.map(nacimientos_por_doc) > 1).to_numpy()]:
            reg.rechazar(
                "clientes",
                "documento_repetido",
                df.at[posicion, "id_cliente"],
                f"documento={df.at[posicion, 'numero_documento']} en varios clientes",
                destino="revision",
            )

        if ctx.reglas["deduplicacion_clientes"]:
            df = self._deduplicar_clientes(df)
        cargados = df[~df["id_cliente"].isin(set(ctx.fusion))].copy()

        correo = cargados["correo"].map(reglas.normalizar_correo)
        estado = cargados["estado_cliente"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_cliente", codigo)
        )
        for posicion in cargados.index[estado.isna()]:
            reg.rechazar(
                "clientes",
                "estado_desconocido",
                cargados.at[posicion, "id_cliente"],
                f"estado={cargados.at[posicion, 'estado_cliente']}",
                destino="revision",
            )

        destino = pd.DataFrame(
            {
                "id_cliente": cargados["id_cliente"].to_numpy(),
                "nombre_completo": cargados["nombre_completo"].map(reglas.normalizar_texto),
                "nombre_normalizado": cargados["nombre_completo"].map(reglas.normalizar_nombre),
                "fecha_nacimiento": cargados["fecha_nacimiento"].to_numpy(),
                "sexo": cargados["sexo"].to_numpy(),
                "telefono": cargados["telefono"].map(reglas.normalizar_telefono).to_numpy(),
                "correo": correo.to_numpy(),
                "estado": estado.fillna("inactivo").to_numpy(),
                "fecha_alta": cargados["fecha_alta"].to_numpy(),
                "observacion": cargados["observaciones"].replace("", np.nan).to_numpy(),
            }
        )
        ctx.ids_clientes = set(destino["id_cliente"])
        return destino.reset_index(drop=True)

    def _documento_valido(self, tipo: pd.Series, numero: pd.Series) -> np.ndarray:
        tipo_texto = tipo.fillna("").to_numpy()
        valido = np.zeros(len(tipo_texto), dtype=bool)
        valido |= (tipo_texto == "DNI") & reglas.validar_dni_vector(numero)
        valido |= (tipo_texto == "CI") & reglas.validar_ci_vector(numero)
        valido |= (tipo_texto == "PAS") & reglas.validar_pasaporte_vector(numero)
        return valido

    def _deduplicar_clientes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Dos pasadas (nombre+nacimiento, documento+nacimiento) segun ADR-009."""
        ctx, reg = self.ctx, self.registro
        nacimiento = df["fecha_nacimiento"].fillna("?")
        clave_nombre = df["nombre_completo"].map(reglas.normalizar_nombre) + "|" + nacimiento
        clave_documento = (
            df["tipo_documento_destino"] + "|" + df["numero_documento"].str.strip() + "|"
            + nacimiento
        )
        mapa: dict[int, int] = {}
        for clave in (clave_nombre, clave_documento):
            for _, indices in df[~df["id_cliente"].isin(mapa)].groupby(clave).groups.items():
                ids = df.loc[indices, "id_cliente"].to_numpy()
                if len(ids) < 2:
                    continue
                superviviente = int(ids.min())
                for otro in ids:
                    if int(otro) != superviviente:
                        mapa[int(otro)] = superviviente
        for eliminado, superviviente in mapa.items():
            reg.anotar(
                "clientes",
                "fusion_cliente",
                eliminado,
                f"fusionado en id_cliente={superviviente}",
            )
        ctx.fusion = self._resolver_fusion(mapa)
        return df

    @staticmethod
    def _resolver_fusion(mapa: dict[int, int]) -> dict[int, int]:
        """Resuelve cadenas de fusion para que todas apunten al superviviente."""
        resuelto = {}
        for clave in mapa:
            valor = mapa[clave]
            while valor in mapa:
                valor = mapa[valor]
            resuelto[clave] = valor
        return resuelto

    # ---------------------------------------------------------------- documentos

    def documentos(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Documentos: vigencia, validacion, repetidos y reparacion de siglo."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        en_destino = df["id_cliente"].isin(ctx.ids_clientes).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "documentos",
                "cliente_no_migrado",
                df.at[posicion, "numero_documento"],
                f"id_cliente={df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        df = df[en_destino].copy()

        exactos = df.duplicated(subset=["id_cliente", "tipo_documento", "numero_documento"])
        if exactos.any():
            df = df[~exactos].copy()
        tipo = df["tipo_documento"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "tipo_documento", codigo)
        )
        valido = self._documento_valido(tipo.fillna(""), df["numero_documento"])
        clave_doc = tipo.fillna("") + "|" + df["numero_documento"].str.strip()
        repetido = (clave_doc.map(df.groupby(clave_doc)["id_cliente"].nunique()) > 1).to_numpy()
        emision, val_emision = reglas.convertir_fechas(df["fecha_emision"], ctx.umbral)
        vencimiento, val_vencimiento = reglas.convertir_fechas(df["fecha_vencimiento"], ctx.umbral)
        vencimiento_legado = vencimiento.copy()
        sin_vencimiento = df["fecha_vencimiento"].str.fullmatch(r"0{6}").to_numpy()
        for posicion in df.index[~val_emision]:
            reg.rechazar(
                "documentos",
                "fecha_imposible",
                df.at[posicion, "numero_documento"],
                f"fecha_emision={df.at[posicion, 'fecha_emision']}",
            )
        for posicion in df.index[val_emision & ~val_vencimiento & ~sin_vencimiento]:
            reg.rechazar(
                "documentos",
                "fecha_imposible",
                df.at[posicion, "numero_documento"],
                f"fecha_vencimiento={df.at[posicion, 'fecha_vencimiento']}",
            )
        for posicion in df.index[~valido]:
            reg.rechazar(
                "documentos",
                "documento_invalido",
                df.at[posicion, "numero_documento"],
                f"id_cliente={df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        for posicion in df.index[repetido]:
            reg.rechazar(
                "documentos",
                "documento_repetido",
                df.at[posicion, "numero_documento"],
                "documento compartido por mas de un cliente",
                destino="revision",
            )

        vencimiento, reparado = _reparar_siglo(vencimiento, emision)
        for posicion in df.index[reparado]:
            reg.anotar(
                "documentos",
                "siglo_reinterpretado",
                df.at[posicion, "numero_documento"],
                f"vencimiento anterior a la emision: {vencimiento[posicion].date()}",
            )
        cargar = valido & val_emision & ~repetido & (val_vencimiento | sin_vencimiento)
        df = df[cargar].copy()
        emision, vencimiento, sin_vencimiento = (
            emision[cargar],
            vencimiento[cargar],
            sin_vencimiento[cargar],
        )
        validado = df["validado"].str.upper().eq("S").to_numpy()
        fecha_vencimiento = _a_texto_nulo(vencimiento.dt.strftime("%Y-%m-%d"), sin_vencimiento)
        vencimiento_segun_legado = _a_texto_nulo(vencimiento_legado[cargar], sin_vencimiento)
        vencido = np.array(
            [
                bool(validado[i])
                and vencimiento_segun_legado[i] is not None
                and str(vencimiento_segun_legado[i]) < ctx.fecha_extraccion.isoformat()
                for i in range(len(df))
            ]
        )
        vigente = validado & ~vencido
        for posicion in df.index[vencido]:
            reg.anotar(
                "documentos",
                "documento_vencido_sin_marcar",
                df.at[posicion, "numero_documento"],
                f"vencimiento={df.at[posicion, 'fecha_vencimiento']} validado=S",
            )
        destino = pd.DataFrame(
            {
                "id_documento": np.arange(1, len(df) + 1),
                "id_cliente": df["id_cliente"].to_numpy(),
                "tipo_documento": tipo[cargar].to_numpy(),
                "numero_documento": df["numero_documento"].to_numpy(),
                "pais": df["pais"].to_numpy(),
                "fecha_emision": emision.to_numpy(),
                "fecha_vencimiento": fecha_vencimiento,
                "validado": validado,
                "vigente": vigente,
                "en_revision": validado & ~vigente,
            }
        )
        return destino.reset_index(drop=True)

    # ---------------------------------------------------------------- direcciones

    def direcciones(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Domicilios: tipo, secuencia y calidad de campos incompletos."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        en_destino = df["id_cliente"].isin(ctx.ids_clientes).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "direcciones",
                "cliente_no_migrado",
                df.at[posicion, "id_cliente"],
                "direccion de cliente no migrado",
                destino="revision",
            )
        df = df[en_destino].copy()
        incompletas = (
            df["calle"].str.strip().eq("")
            | df["localidad"].str.strip().eq("")
            | df["provincia"].str.strip().eq("")
            | df["codigo_postal"].str.strip().eq("")
        )
        for posicion in df.index[incompletas]:
            reg.anotar(
                "direcciones",
                "direccion_incompleta",
                df.at[posicion, "id_cliente"],
                "campo vacio en calle/localidad/provincia/codigo_postal",
            )
        destino = pd.DataFrame(
            {
                "id_domicilio": np.arange(1, len(df) + 1),
                "id_cliente": df["id_cliente"].to_numpy(),
                "tipo": df["tipo_direccion"]
                .map(MAPA_TIPO_DIRECCION)
                .fillna("particular")
                .to_numpy(),
                "calle": df["calle"].replace("", np.nan).to_numpy(),
                "numero": pd.to_numeric(df["numero"], errors="coerce")
                .replace(0, np.nan)
                .to_numpy(),
                "piso": df["piso"].replace("", np.nan).to_numpy(),
                "departamento": df["departamento"].replace("", np.nan).to_numpy(),
                "localidad": df["localidad"].replace("", np.nan).to_numpy(),
                "provincia": df["provincia"].replace("", np.nan).to_numpy(),
                "codigo_postal": df["codigo_postal"].replace("", np.nan).to_numpy(),
                "pais": df["pais"].to_numpy(),
            }
        )
        return destino.reset_index(drop=True)

    # ------------------------------------------------------------------- cuentas

    def cuentas(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Cuentas: mapeo de producto segun version, estados y texto libre."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        df["id_cuenta"] = pd.to_numeric(df["id_cuenta"], errors="coerce").astype("int64")
        mapa_productos = ctx.reglas["mapeo_productos"]

        entradas = df["codigo_producto"].map(lambda codigo: mapa_productos.get(str(codigo).strip()))
        destino_producto = entradas.map(
            lambda e: e["destino"] if e and e["tratamiento"] == "cargar" else None
        )
        tratamiento = entradas.map(lambda e: e["tratamiento"] if e else "sin_mapeo")
        for posicion in df.index[tratamiento == "sin_mapeo"]:
            reg.rechazar(
                "cuentas",
                "producto_desconocido",
                df.at[posicion, "id_cuenta"],
                f"producto={df.at[posicion, 'codigo_producto']} sin equivalente",
            )
        for posicion in df.index[tratamiento == "rechazar"]:
            reg.rechazar(
                "cuentas",
                "producto_fuera_de_alcance",
                df.at[posicion, "id_cuenta"],
                f"producto={df.at[posicion, 'codigo_producto']} fuera de alcance",
            )
        for posicion in df.index[tratamiento == "revisar"]:
            reg.rechazar(
                "cuentas",
                "producto_revision",
                df.at[posicion, "id_cuenta"],
                f"producto={df.at[posicion, 'codigo_producto']} a revision",
                destino="revision",
            )
        con_marca = entradas.map(lambda e: bool(e and e.get("marca")))
        for posicion in df.index[con_marca]:
            reg.anotar(
                "cuentas",
                "marca_producto",
                df.at[posicion, "id_cuenta"],
                f"marca={entradas[posicion]['marca']} "
                f"producto={df.at[posicion, 'codigo_producto']}",
            )
        huerfanas = ~df["id_cliente"].isin(ctx.ids_clientes)
        for posicion in df.index[huerfanas]:
            reg.rechazar(
                "cuentas",
                "cuenta_huerfana",
                df.at[posicion, "id_cuenta"],
                f"id_cliente inexistente: {df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        estado = df["estado_cuenta"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_cuenta", codigo)
        )
        for posicion in df.index[df["estado_cuenta"].str.upper().eq("X")]:
            reg.rechazar(
                "cuentas",
                "estado_desconocido",
                df.at[posicion, "id_cuenta"],
                "estado X cargado como desconocida",
                destino="revision",
            )
        for posicion in df.index[estado.isna()]:
            reg.rechazar(
                "cuentas",
                "estado_desconocido",
                df.at[posicion, "id_cuenta"],
                f"estado={df.at[posicion, 'estado_cuenta']} cargado como desconocida",
                destino="revision",
            )
        apertura, val_apertura = reglas.convertir_fechas(df["fecha_apertura"], ctx.umbral)
        ultimo, val_ultimo = reglas.convertir_fechas(df["fecha_ultimo_movimiento"], ctx.umbral)
        sin_ultimo = df["fecha_ultimo_movimiento"].str.fullmatch(r"0{6}").to_numpy()
        ultimo, reparado = _reparar_siglo(ultimo, apertura)
        for posicion in df.index[reparado]:
            reg.anotar(
                "cuentas",
                "siglo_reinterpretado",
                df.at[posicion, "id_cuenta"],
                f"ultimo movimiento anterior a la apertura: {ultimo[posicion].date()}",
            )
        for posicion in df.index[~val_apertura]:
            reg.rechazar(
                "cuentas",
                "fecha_imposible",
                df.at[posicion, "id_cuenta"],
                f"fecha_apertura={df.at[posicion, 'fecha_apertura']}",
            )
        for posicion in df.index[(~val_ultimo) & (~sin_ultimo)]:
            reg.rechazar(
                "cuentas",
                "fecha_imposible",
                df.at[posicion, "id_cuenta"],
                f"fecha_ultimo_movimiento={df.at[posicion, 'fecha_ultimo_movimiento']}",
            )
        cargar = (
            destino_producto.notna() & ~huerfanas & val_apertura & (val_ultimo | sin_ultimo)
        ).to_numpy()
        df = df[cargar].copy()
        fecha_ultimo = _a_texto_nulo(
            ultimo[cargar].dt.strftime("%Y-%m-%d"), sin_ultimo[cargar]
        )

        telefono = np.full(len(df), None, dtype=object)
        documento_pendiente = np.zeros(len(df), dtype=bool)
        if ctx.reglas["extraccion_texto_libre"]:
            extraido = df["observaciones"].map(reglas.extraer_observacion_cuenta)
            telefono = extraido.map(lambda par: par[0]).to_numpy()
            documento_pendiente = extraido.map(lambda par: par[1]).to_numpy()
            for posicion in df.index[documento_pendiente]:
                reg.anotar(
                    "cuentas",
                    "documento_pendiente_detectado",
                    df.at[posicion, "id_cuenta"],
                    df.at[posicion, "observaciones"],
                )
        destino = pd.DataFrame(
            {
                "id_cuenta": df["id_cuenta"].to_numpy(),
                "id_cliente": df["id_cliente"].to_numpy(),
                "codigo_producto": destino_producto[cargar].to_numpy(),
                "codigo_sucursal": pd.to_numeric(df["codigo_sucursal"], errors="coerce").to_numpy(),
                "moneda": df["moneda"].to_numpy(),
                "fecha_apertura": apertura[cargar].to_numpy(),
                "estado": estado[cargar].fillna("desconocida").to_numpy(),
                "tiene_tarjeta": df["indicador_tarjeta"].str.upper().eq("S").to_numpy(),
                "numero_tarjeta_enmascarado": df["numero_tarjeta"]
                .map(reglas.enmascarar_tarjeta)
                .to_numpy(),
                "fecha_ultimo_movimiento": fecha_ultimo,
                "observacion": df["observaciones"].replace("", np.nan).to_numpy(),
                "telefono_alternativo": telefono,
                "documento_pendiente": documento_pendiente,
            }
        )
        ctx.ids_cuentas.update(destino["id_cuenta"])
        return destino.reset_index(drop=True)

    # -------------------------------------------------------------- saldo_cuenta

    def saldos(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Saldos por cuenta: solo cuentas migradas; descuadres se conservan."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cuenta"] = pd.to_numeric(df["id_cuenta"], errors="coerce").astype("int64")
        en_destino = df["id_cuenta"].isin(ctx.ids_cuentas).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "saldos",
                "cuenta_no_migrada",
                df.at[posicion, "id_cuenta"],
                "saldo de cuenta no migrada",
            )
        df = df[en_destino].copy()
        apertura, val_apertura = reglas.convertir_importes(df["saldo_apertura"])
        final, val_final = reglas.convertir_importes(df["saldo_final"])
        fecha, val_fecha = reglas.convertir_fechas(df["fecha_saldo"], ctx.umbral)
        for posicion in df.index[~val_apertura]:
            reg.rechazar(
                "saldos",
                "importe_invalido",
                df.at[posicion, "id_cuenta"],
                f"saldo_apertura={df.at[posicion, 'saldo_apertura']!r}",
            )
        for posicion in df.index[~val_fecha]:
            reg.rechazar(
                "saldos",
                "fecha_imposible",
                df.at[posicion, "id_cuenta"],
                f"fecha_saldo={df.at[posicion, 'fecha_saldo']}",
            )
        cargar = val_apertura & val_final & val_fecha
        destino = pd.DataFrame(
            {
                "id_cuenta": df["id_cuenta"][cargar].to_numpy(),
                "moneda": df["moneda"][cargar].to_numpy(),
                "saldo_apertura": apertura[cargar].to_numpy(),
                "saldo_final": final[cargar].to_numpy(),
                "fecha_saldo": fecha[cargar].to_numpy(),
            }
        )
        return destino.reset_index(drop=True)

    # --------------------------------------------------------------- movimientos

    def movimientos(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Movimientos: ventana, signos, duplicados de reproceso y catalogos."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cuenta"] = pd.to_numeric(df["id_cuenta"], errors="coerce").astype("int64")
        df["id_movimiento"] = pd.to_numeric(df["id_movimiento"], errors="coerce").astype("int64")
        en_destino = df["id_cuenta"].isin(ctx.ids_cuentas).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "movimientos",
                "cuenta_no_migrada",
                df.at[posicion, "id_movimiento"],
                f"id_cuenta={df.at[posicion, 'id_cuenta']}",
            )
        df = df[en_destino].copy()

        fecha, val_fecha = reglas.convertir_fechas(df["fecha_movimiento"], ctx.umbral)
        hora, val_hora = reglas.convertir_horas(df["hora_movimiento"])
        importe, val_importe = reglas.convertir_importes(df["importe"])
        saldo, val_saldo = reglas.convertir_importes(df["saldo_despues"])
        for posicion in df.index[~val_fecha]:
            reg.rechazar(
                "movimientos",
                "fecha_imposible",
                df.at[posicion, "id_movimiento"],
                f"fecha={df.at[posicion, 'fecha_movimiento']}",
            )
        for posicion in df.index[~val_hora]:
            reg.rechazar(
                "movimientos",
                "hora_invalida",
                df.at[posicion, "id_movimiento"],
                f"hora={df.at[posicion, 'hora_movimiento']}",
            )
        for posicion in df.index[~(val_importe & val_saldo)]:
            reg.rechazar(
                "movimientos",
                "importe_invalido",
                df.at[posicion, "id_movimiento"],
                f"importe={df.at[posicion, 'importe']!r}",
            )
        codigos_op = ctx.catalogos.get("codigo_operacion", {})
        operacion_ok = df["codigo_operacion"].isin(codigos_op).to_numpy()
        canal_ok = df["canal"].isin(ctx.catalogos.get("canal", {})).to_numpy()
        for posicion in df.index[~(operacion_ok & canal_ok)]:
            reg.rechazar(
                "movimientos",
                "codigo_desconocido",
                df.at[posicion, "id_movimiento"],
                f"operacion={df.at[posicion, 'codigo_operacion']} "
                f"canal={df.at[posicion, 'canal']}",
                destino="revision",
            )
        valida = val_fecha & val_hora & val_importe & val_saldo & operacion_ok & canal_ok
        if ctx.reglas["validar_fechas_contextual"]:
            dentro = (
                fecha.ge(ctx.ventana_inicio.isoformat())
                & fecha.le(ctx.fecha_corte.isoformat())
            ).to_numpy()
            for posicion in np.flatnonzero(valida & ~dentro):
                reg.rechazar(
                    "movimientos",
                    "fuera_de_ventana",
                    df["id_movimiento"].iloc[posicion],
                    f"fecha={fecha.iloc[posicion]}",
                )
            valida = valida & dentro
        df = df[valida].copy()
        fecha, hora = fecha[df.index], hora[df.index]
        importe, saldo = importe[df.index], saldo[df.index]

        clave_duplicado = (
            df["id_cuenta"].astype(str) + "|" + df["fecha_movimiento"].astype(str) + "|"
            + df["hora_movimiento"].astype(str) + "|" + df["codigo_operacion"] + "|"
            + df["importe"] + "|" + df["numero_comprobante"]
        )
        duplicados = clave_duplicado.duplicated(keep="first").to_numpy()
        for posicion in df.index[duplicados]:
            reg.rechazar(
                "movimientos",
                "duplicado_reproceso",
                df.at[posicion, "id_movimiento"],
                f"reproceso de {clave_duplicado[posicion]}",
            )
        df = df[~duplicados].copy()
        fecha, hora = fecha[df.index], hora[df.index]
        importe, saldo = importe[df.index], saldo[df.index]

        if ctx.reglas["correccion_signos"]:
            es_debito = df["codigo_operacion"].isin(reglas.CODIGOS_DEBITO)
            invertidos = (es_debito & (importe > 0)).to_numpy()
            for posicion in df.index[invertidos]:
                reg.anotar(
                    "movimientos",
                    "correccion_signo",
                    df.at[posicion, "id_movimiento"],
                    f"importe {float(importe[posicion]):.2f} invertido a "
                    f"{-float(importe[posicion]):.2f} (operacion es debito)",
                )
            importe = importe.mask(invertidos, -importe)

        destino = pd.DataFrame(
            {
                "id_movimiento": df["id_movimiento"].to_numpy(),
                "id_cuenta": df["id_cuenta"].to_numpy(),
                "fecha": fecha.to_numpy(),
                "hora": hora.to_numpy(),
                "codigo_operacion": df["codigo_operacion"].to_numpy(),
                "canal": df["canal"].to_numpy(),
                "importe": np.round(importe.to_numpy(), 2),
                "saldo_despues": saldo.to_numpy(),
                "numero_comprobante": pd.to_numeric(
                    df["numero_comprobante"], errors="coerce"
                ).to_numpy(),
                "descripcion": df["descripcion"].replace("", np.nan).to_numpy(),
                "codigo_sucursal": pd.to_numeric(df["sucursal"], errors="coerce").to_numpy(),
            }
        )
        return destino.reset_index(drop=True)

    # ----------------------------------------------------------------- prestamos

    def prestamos(self, crudo: pd.DataFrame, cuotas_crudo: pd.DataFrame) -> pd.DataFrame:
        """Prestamos: producto, referencias, estado y coherencia con cuotas."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        df["id_prestamo"] = pd.to_numeric(df["id_prestamo"], errors="coerce").astype("int64")
        df["id_cuenta_debito"] = pd.to_numeric(
            df["id_cuenta_debito"], errors="coerce"
        ).astype("int64")

        mapa_productos = ctx.reglas["mapeo_productos"]
        entradas = df["codigo_producto"].map(
            lambda codigo: mapa_productos.get(str(codigo).strip())
        )
        destino_producto = entradas.map(
            lambda e: e["destino"] if e and e["tratamiento"] == "cargar" else None
        )
        for posicion in df.index[entradas.isna()]:
            reg.rechazar(
                "prestamos",
                "producto_desconocido",
                df.at[posicion, "id_prestamo"],
                f"producto={df.at[posicion, 'codigo_producto']}",
            )
        for posicion in df.index[
            entradas.map(lambda e: bool(e) and e["tratamiento"] == "rechazar")
        ]:
            reg.rechazar(
                "prestamos",
                "producto_fuera_de_alcance",
                df.at[posicion, "id_prestamo"],
                f"producto={df.at[posicion, 'codigo_producto']}",
            )
        for posicion in df.index[
            entradas.map(lambda e: bool(e) and e["tratamiento"] == "revisar")
        ]:
            reg.rechazar(
                "prestamos",
                "producto_revision",
                df.at[posicion, "id_prestamo"],
                f"producto={df.at[posicion, 'codigo_producto']}",
                destino="revision",
            )
        sin_cliente = ~df["id_cliente"].isin(ctx.ids_clientes)
        for posicion in df.index[sin_cliente]:
            reg.rechazar(
                "prestamos",
                "cliente_no_migrado",
                df.at[posicion, "id_prestamo"],
                f"id_cliente={df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        sin_cuenta = ~df["id_cuenta_debito"].isin(ctx.ids_cuentas)
        for posicion in df.index[sin_cuenta]:
            reg.rechazar(
                "prestamos",
                "cuenta_no_migrada",
                df.at[posicion, "id_prestamo"],
                f"id_cuenta_debito={df.at[posicion, 'id_cuenta_debito']}",
                destino="revision",
            )
        otorgamiento, val_otorgamiento = reglas.convertir_fechas(
            df["fecha_otorgamiento"], ctx.umbral
        )
        ultimo, val_ultimo = reglas.convertir_fechas(df["fecha_ultimo_pago"], ctx.umbral)
        sin_ultimo = df["fecha_ultimo_pago"].str.fullmatch(r"0{6}").to_numpy()
        ultimo, reparado = _reparar_siglo(ultimo, otorgamiento)
        for posicion in df.index[reparado]:
            reg.anotar(
                "prestamos",
                "siglo_reinterpretado",
                df.at[posicion, "id_prestamo"],
                f"ultimo pago anterior al otorgamiento: {ultimo[posicion].date()}",
            )
        for posicion in df.index[~val_otorgamiento]:
            reg.rechazar(
                "prestamos",
                "fecha_imposible",
                df.at[posicion, "id_prestamo"],
                f"fecha_otorgamiento={df.at[posicion, 'fecha_otorgamiento']}",
            )
        monto, val_monto = reglas.convertir_importes(df["monto_original"])
        capital, val_capital = reglas.convertir_importes(df["saldo_capital"])
        tasa, val_tasa = reglas.convertir_importes(df["tasa_anual"])
        estado = df["estado_prestamo"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_prestamo", codigo)
        )
        for posicion in df.index[estado.isna()]:
            reg.rechazar(
                "prestamos",
                "estado_desconocido",
                df.at[posicion, "id_prestamo"],
                f"estado={df.at[posicion, 'estado_prestamo']}",
                destino="revision",
            )
        cargar = (
            destino_producto.notna()
            & ~sin_cliente
            & ~sin_cuenta
            & val_otorgamiento
            & (val_ultimo | sin_ultimo)
            & val_monto
            & val_capital
            & val_tasa
            & estado.notna()
        ).to_numpy()
        df = df[cargar].copy()
        capital_cargado = capital[cargar]

        pendiente = self._cuotas_pendientes(cuotas_crudo)
        esperado = df["id_prestamo"].map(pendiente).fillna(0.0)
        desvio = (capital_cargado - esperado).abs()
        incongruentes = (desvio > np.maximum(0.01, esperado * 0.002)).to_numpy()
        for posicion in df.index[incongruentes]:
            reg.rechazar(
                "prestamos",
                "saldo_incongruente",
                df.at[posicion, "id_prestamo"],
                f"saldo_capital={float(capital_cargado[posicion]):.2f} "
                f"esperado={float(esperado[posicion]):.2f}",
                destino="revision",
            )
        destino = pd.DataFrame(
            {
                "id_prestamo": df["id_prestamo"].to_numpy(),
                "id_cliente": df["id_cliente"].to_numpy(),
                "id_cuenta_debito": df["id_cuenta_debito"].to_numpy(),
                "codigo_producto": destino_producto[cargar].to_numpy(),
                "moneda": df["moneda"].to_numpy(),
                "fecha_otorgamiento": otorgamiento[cargar].to_numpy(),
                "monto_original": monto[cargar].to_numpy(),
                "saldo_capital": capital_cargado.to_numpy(),
                "tasa_anual": tasa[cargar].to_numpy(),
                "plazo_meses": pd.to_numeric(df["plazo_meses"], errors="coerce").to_numpy(),
                "cantidad_cuotas": pd.to_numeric(
                    df["cantidad_cuotas"], errors="coerce"
                ).to_numpy(),
                "cuota_actual": pd.to_numeric(df["cuota_actual"], errors="coerce").to_numpy(),
                "estado": estado[cargar].to_numpy(),
                "fecha_ultimo_pago": _a_texto_nulo(
                    ultimo[cargar].dt.strftime("%Y-%m-%d"), sin_ultimo[cargar]
                ),
            }
        )
        ctx.ids_prestamos = set(destino["id_prestamo"])
        return destino.reset_index(drop=True)

    @staticmethod
    def _cuotas_pendientes(cuotas_crudo: pd.DataFrame) -> pd.Series:
        """Capital pendiente por prestamo segun las cuotas crudas (estado != C)."""
        capital, _ = reglas.convertir_importes(cuotas_crudo["capital"])
        pendientes = cuotas_crudo["estado_cuota"].ne("C")
        identificadores = pd.to_numeric(
            cuotas_crudo.loc[pendientes, "id_prestamo"], errors="coerce"
        )
        return capital[pendientes].groupby(identificadores).sum()

    # ------------------------------------------------------------ cuota_prestamo

    def cuotas(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Cuotas de prestamos migrados."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_prestamo"] = pd.to_numeric(df["id_prestamo"], errors="coerce").astype("int64")
        en_destino = df["id_prestamo"].isin(ctx.ids_prestamos).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "cuotas",
                "prestamo_no_migrado",
                df.at[posicion, "id_prestamo"],
                f"cuota {df.at[posicion, 'numero_cuota']} de prestamo no migrado",
            )
        df = df[en_destino].copy()
        vencimiento, val_vencimiento = reglas.convertir_fechas(
            df["fecha_vencimiento"], ctx.umbral
        )
        pago, val_pago = reglas.convertir_fechas(df["fecha_pago"], ctx.umbral)
        sin_pago = df["fecha_pago"].str.fullmatch(r"0{6}").to_numpy()
        pago, reparado = _reparar_siglo(pago, vencimiento)
        for posicion in df.index[reparado]:
            reg.anotar(
                "cuotas",
                "siglo_reinterpretado",
                df.at[posicion, "id_prestamo"],
                f"pago anterior al vencimiento de la cuota "
                f"{df.at[posicion, 'numero_cuota']}",
            )
        capital, val_capital = reglas.convertir_importes(df["capital"])
        interes, val_interes = reglas.convertir_importes(df["interes"])
        total, val_total = reglas.convertir_importes(df["total"])
        estado = df["estado_cuota"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_cuota", codigo)
        )
        for posicion in df.index[estado.isna()]:
            reg.rechazar(
                "cuotas",
                "estado_desconocido",
                df.at[posicion, "id_prestamo"],
                f"estado={df.at[posicion, 'estado_cuota']}",
                destino="revision",
            )
        descuadre = (total - (capital + interes)).abs() > 0.01
        for posicion in df.index[descuadre & estado.notna()]:
            reg.rechazar(
                "cuotas",
                "total_incongruente",
                df.at[posicion, "id_prestamo"],
                f"cuota {df.at[posicion, 'numero_cuota']}: total={float(total[posicion]):.2f}",
                destino="revision",
            )
        cargar = (
            val_vencimiento
            & (val_pago | sin_pago)
            & val_capital
            & val_interes
            & val_total
            & estado.notna()
        ).to_numpy()
        df = df[cargar].copy()
        destino = pd.DataFrame(
            {
                "id_prestamo": df["id_prestamo"].to_numpy(),
                "numero_cuota": pd.to_numeric(df["numero_cuota"], errors="coerce").to_numpy(),
                "fecha_vencimiento": vencimiento[cargar].to_numpy(),
                "capital": capital[cargar].to_numpy(),
                "interes": interes[cargar].to_numpy(),
                "total": total[cargar].to_numpy(),
                "estado": estado[cargar].to_numpy(),
                "fecha_pago": _a_texto_nulo(
                    pago[cargar].dt.strftime("%Y-%m-%d"), sin_pago[cargar]
                ),
            }
        )
        return destino.reset_index(drop=True)

    # ---------------------------------------------------------------- plazo_fijo

    def plazos(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Plazos fijos: referencias, siglo reparado y coherencia del vencimiento."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        df["id_plazo"] = pd.to_numeric(df["id_plazo"], errors="coerce").astype("int64")
        df["id_cuenta_acredita"] = pd.to_numeric(
            df["id_cuenta_acredita"], errors="coerce"
        ).astype("int64")
        mapa_productos = ctx.reglas["mapeo_productos"]
        entradas = df["codigo_producto"].map(
            lambda codigo: mapa_productos.get(str(codigo).strip())
        )
        destino_producto = entradas.map(
            lambda e: e["destino"] if e and e["tratamiento"] == "cargar" else None
        )
        for posicion in df.index[destino_producto.isna()]:
            reg.rechazar(
                "plazos_fijos",
                "producto_fuera_de_alcance",
                df.at[posicion, "id_plazo"],
                f"producto={df.at[posicion, 'codigo_producto']}",
            )
        for posicion in df.index[~df["id_cliente"].isin(ctx.ids_clientes)]:
            reg.rechazar(
                "plazos_fijos",
                "cliente_no_migrado",
                df.at[posicion, "id_plazo"],
                f"id_cliente={df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        for posicion in df.index[~df["id_cuenta_acredita"].isin(ctx.ids_cuentas)]:
            reg.rechazar(
                "plazos_fijos",
                "cuenta_no_migrada",
                df.at[posicion, "id_plazo"],
                f"id_cuenta_acredita={df.at[posicion, 'id_cuenta_acredita']}",
                destino="revision",
            )
        constitucion, val_constitucion = reglas.convertir_fechas(
            df["fecha_constitucion"], ctx.umbral
        )
        vencimiento, val_vencimiento = reglas.convertir_fechas(
            df["fecha_vencimiento"], ctx.umbral
        )
        vencimiento, reparado = _reparar_siglo(vencimiento, constitucion)
        for posicion in df.index[reparado]:
            reg.anotar(
                "plazos_fijos",
                "siglo_reinterpretado",
                df.at[posicion, "id_plazo"],
                f"vencimiento anterior a la constitucion: {vencimiento[posicion].date()}",
            )
        monto, val_monto = reglas.convertir_importes(df["monto_capital"])
        tasa, val_tasa = reglas.convertir_importes(df["tasa_anual"])
        estado = df["estado_plazo"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_plazo", codigo)
        )
        cargar = (
            destino_producto.notna()
            & df["id_cliente"].isin(ctx.ids_clientes)
            & df["id_cuenta_acredita"].isin(ctx.ids_cuentas)
            & val_constitucion
            & val_vencimiento
            & val_monto
            & val_tasa
            & estado.notna()
        ).to_numpy()
        df = df[cargar].copy()
        plazo_dias = pd.to_numeric(df["plazo_dias"], errors="coerce")
        esperado = pd.to_datetime(
            constitucion[cargar], errors="coerce"
        ) + pd.to_timedelta(plazo_dias, unit="D")
        vencimiento_cargado = pd.to_datetime(vencimiento[cargar], errors="coerce")
        desvio = (vencimiento_cargado - esperado).dt.days.abs()
        for posicion in df.index[(desvio > 3).to_numpy()]:
            reg.rechazar(
                "plazos_fijos",
                "vencimiento_incongruente",
                df.at[posicion, "id_plazo"],
                f"vencimiento={vencimiento[posicion]} esperado={esperado[posicion].date()}",
                destino="revision",
            )
        destino = pd.DataFrame(
            {
                "id_plazo": df["id_plazo"].to_numpy(),
                "id_cliente": df["id_cliente"].to_numpy(),
                "id_cuenta_acredita": df["id_cuenta_acredita"].to_numpy(),
                "codigo_producto": destino_producto[cargar].to_numpy(),
                "moneda": df["moneda"].to_numpy(),
                "fecha_constitucion": constitucion[cargar].to_numpy(),
                "fecha_vencimiento": vencimiento[cargar].to_numpy(),
                "monto_capital": monto[cargar].to_numpy(),
                "tasa_anual": tasa[cargar].to_numpy(),
                "plazo_dias": plazo_dias.to_numpy(),
                "estado": estado[cargar].to_numpy(),
            }
        )
        return destino.reset_index(drop=True)

    # ------------------------------------------------------------ mandato_debito

    def mandatos(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Mandatos de debito automatico y sus referencias."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        df["id_cliente"] = ctx.reasignar_cliente(
            pd.to_numeric(df["id_cliente"], errors="coerce")
        )
        df["id_mandato"] = pd.to_numeric(df["id_mandato"], errors="coerce").astype("int64")
        df["id_cuenta_debito"] = pd.to_numeric(
            df["id_cuenta_debito"], errors="coerce"
        ).astype("int64")
        for posicion in df.index[~df["id_cliente"].isin(ctx.ids_clientes)]:
            reg.rechazar(
                "mandatos",
                "cliente_no_migrado",
                df.at[posicion, "id_mandato"],
                f"id_cliente={df.at[posicion, 'id_cliente']}",
                destino="revision",
            )
        for posicion in df.index[~df["id_cuenta_debito"].isin(ctx.ids_cuentas)]:
            reg.rechazar(
                "mandatos",
                "cuenta_no_migrada",
                df.at[posicion, "id_mandato"],
                f"id_cuenta_debito={df.at[posicion, 'id_cuenta_debito']}",
                destino="revision",
            )
        servicio = df["codigo_servicio"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "servicio_mandato", codigo)
        )
        frecuencia = df["frecuencia"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "frecuencia", codigo)
        )
        estado = df["estado_mandato"].map(
            lambda codigo: reglas.mapear_catalogo(ctx.catalogos, "estado_mandato", codigo)
        )
        for posicion in df.index[servicio.isna() | frecuencia.isna() | estado.isna()]:
            reg.rechazar(
                "mandatos",
                "codigo_desconocido",
                df.at[posicion, "id_mandato"],
                f"servicio={df.at[posicion, 'codigo_servicio']} "
                f"frecuencia={df.at[posicion, 'frecuencia']} "
                f"estado={df.at[posicion, 'estado_mandato']}",
                destino="revision",
            )
        alta, val_alta = reglas.convertir_fechas(df["fecha_alta"], ctx.umbral)
        importe, val_importe = reglas.convertir_importes(df["importe_maximo"])
        cargar = (
            df["id_cliente"].isin(ctx.ids_clientes)
            & df["id_cuenta_debito"].isin(ctx.ids_cuentas)
            & servicio.notna()
            & frecuencia.notna()
            & estado.notna()
            & val_alta
            & val_importe
        ).to_numpy()
        df = df[cargar].copy()
        destino = pd.DataFrame(
            {
                "id_mandato": df["id_mandato"].to_numpy(),
                "id_cliente": df["id_cliente"].to_numpy(),
                "id_cuenta_debito": df["id_cuenta_debito"].to_numpy(),
                "codigo_servicio": servicio[cargar].to_numpy(),
                "referencia_servicio": df["referencia_servicio"].replace("", np.nan).to_numpy(),
                "importe_maximo": importe[cargar].to_numpy(),
                "fecha_alta": alta[cargar].to_numpy(),
                "estado": estado[cargar].to_numpy(),
                "frecuencia": frecuencia[cargar].to_numpy(),
            }
        )
        return destino.reset_index(drop=True)

    # ------------------------------------------------------------- contabilidad

    def plan_cuentas(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Plan de cuentas contable con jerarquia validada."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        codigos = df["codigo_contable"].str.strip()
        padres = df["cuenta_padre"].str.strip()
        nivel = pd.to_numeric(df["nivel"], errors="coerce")
        invalidos = (nivel.gt(1) & ~padres.isin(set(codigos))).to_numpy()
        for posicion in df.index[invalidos]:
            reg.rechazar(
                "plan_cuentas",
                "padre_inexistente",
                df.at[posicion, "codigo_contable"],
                f"cuenta_padre={df.at[posicion, 'cuenta_padre']!r}",
                destino="revision",
            )
        cargar = ~invalidos
        destino = pd.DataFrame(
            {
                "codigo_contable": codigos[cargar].to_numpy(),
                "nombre_cuenta": df["nombre_cuenta"]
                .map(reglas.normalizar_texto)[cargar]
                .to_numpy(),
                "tipo_cuenta": df["tipo_cuenta"].map(MAPA_TIPO_CUENTA)[cargar].to_numpy(),
                "nivel": nivel[cargar].to_numpy(),
                "cuenta_padre": padres[cargar].replace("", np.nan).to_numpy(),
                "moneda": df["moneda"][cargar].to_numpy(),
            }
        )
        ctx.ids_contables = set(destino["codigo_contable"])
        return destino.reset_index(drop=True)

    def saldos_contables(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Saldos del mayor: balance verificado y ajuste contable con evidencia."""
        ctx, reg = self.ctx, self.registro
        df = crudo.copy()
        codigos = df["codigo_contable"].str.strip()
        en_destino = codigos.isin(ctx.ids_contables).to_numpy()
        for posicion in df.index[~en_destino]:
            reg.rechazar(
                "saldos_contables",
                "contable_no_migrado",
                df.at[posicion, "codigo_contable"],
                "cuenta contable no migrada",
                destino="revision",
            )
        df = df[en_destino].copy()
        codigos = codigos[en_destino]
        debe, val_debe = reglas.convertir_importes(df["saldo_debe"])
        haber, val_haber = reglas.convertir_importes(df["saldo_haber"])
        final, val_final = reglas.convertir_importes(df["saldo_final"])
        periodo, val_periodo = reglas.convertir_fechas(df["periodo"], ctx.umbral)
        cargar = val_debe & val_haber & val_final & val_periodo
        codigos, debe = codigos[cargar], debe[cargar]
        haber, final, periodo = haber[cargar], final[cargar], periodo[cargar]
        referencia = pd.Series(
            [str(ctx.fecha_extraccion - timedelta(days=730))] * len(df),
            index=df.index,
        )[cargar]
        periodo, reparado = _reparar_siglo(periodo, referencia)
        for posicion in periodo.index[reparado]:
            reg.anotar(
                "saldos_contables",
                "siglo_reinterpretado",
                codigos[posicion],
                f"periodo reinterpretado: {periodo[posicion].date()}",
            )

        desbalance = (debe - haber - final).abs() > 0.01
        final_ajustado = final.copy()
        for posicion in final.index[desbalance]:
            detalle = (
                f"debe={float(debe[posicion]):.2f} haber={float(haber[posicion]):.2f} "
                f"saldo_final={float(final[posicion]):.2f} "
                f"ajuste={float(debe[posicion] - haber[posicion]):.2f}"
            )
            if ctx.reglas["ajustes_contables"]:
                final_ajustado[posicion] = round(float(debe[posicion] - haber[posicion]), 2)
                reg.anotar(
                    "saldos_contables", "ajuste_contable", codigos[posicion], detalle
                )
            else:
                reg.anotar(
                    "saldos_contables",
                    "desfase_contable_reportado",
                    codigos[posicion],
                    detalle,
                )
        destino = pd.DataFrame(
            {
                "codigo_contable": codigos.to_numpy(),
                "periodo": periodo.to_numpy(),
                "saldo_debe": debe.to_numpy(),
                "saldo_haber": haber.to_numpy(),
                "saldo_final": np.round(final_ajustado.to_numpy(), 2),
            }
        )
        return destino.reset_index(drop=True)

    # ------------------------------------------------------------------ general

    def transformar_todo(self, crudo: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Ejecuta todas las transformaciones en orden de dependencias."""
        destino: dict[str, pd.DataFrame] = {}
        destino["cliente"] = self.clientes(crudo["clientes"])
        destino["documento_cliente"] = self.documentos(crudo["documentos"])
        destino["domicilio_cliente"] = self.direcciones(crudo["direcciones"])
        destino["cuenta"] = self.cuentas(crudo["cuentas"])
        destino["saldo_cuenta"] = self.saldos(crudo["saldos"])
        destino["movimiento"] = self.movimientos(crudo["movimientos"])
        destino["prestamo"] = self.prestamos(crudo["prestamos"], crudo["cuotas"])
        destino["cuota_prestamo"] = self.cuotas(crudo["cuotas"])
        destino["plazo_fijo"] = self.plazos(crudo["plazos_fijos"])
        destino["mandato_debito"] = self.mandatos(crudo["mandatos"])
        destino["cuenta_contable"] = self.plan_cuentas(crudo["plan_cuentas"])
        destino["saldo_contable"] = self.saldos_contables(crudo["saldos_contables"])
        return destino

    def transformar_delta(self, crudo: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Transforma la carga delta del corte sobre el mismo contexto de la base."""
        destino: dict[str, pd.DataFrame] = {}
        destino["cuenta"] = self.cuentas(crudo["cuentas"])
        destino["saldo_cuenta"] = self.saldos(crudo["saldos"])
        destino["movimiento"] = self.movimientos(crudo["movimientos"])
        return destino


def catalogos_destino(
    ctx: Contexto, destino: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    """Deriva los catalogos del destino a partir de los datos cargados."""
    descripciones = _descripciones_catalogo()

    def nombre(dominio: str, codigo: str) -> str:
        return descripciones.get(dominio, {}).get(codigo, codigo)

    productos = sorted(
        set(destino["cuenta"]["codigo_producto"].tolist())
        | set(destino["prestamo"]["codigo_producto"].tolist())
        | set(destino["plazo_fijo"]["codigo_producto"].tolist())
    )
    sucursales = sorted(
        set(destino["cuenta"]["codigo_sucursal"].dropna().astype(int).tolist())
        | set(destino["movimiento"]["codigo_sucursal"].dropna().astype(int).tolist())
    )
    codigos_operacion = sorted(destino["movimiento"]["codigo_operacion"].unique().tolist())
    canales = sorted(destino["movimiento"]["canal"].unique().tolist())
    tipos_documento = sorted(destino["documento_cliente"]["tipo_documento"].unique().tolist())
    servicios = sorted(destino["mandato_debito"]["codigo_servicio"].unique().tolist())
    monedas = sorted(
        set(destino["cuenta"]["moneda"].unique().tolist())
        | set(destino["saldo_cuenta"]["moneda"].unique().tolist())
    )
    familia = {
        "CA": "deposito",
        "CC": "deposito",
        "PP": "credito",
        "PF": "inversion",
        "PE": "inversion",
    }
    return {
        "producto": pd.DataFrame(
            {
                "codigo": productos,
                "nombre": [nombre("producto", c) for c in productos],
                "familia": [familia.get(c, "otro") for c in productos],
                "moneda": ["ARS"] * len(productos),
            }
        ),
        "sucursal": pd.DataFrame(
            {"codigo": sucursales, "nombre": [f"SUCURSAL {c:04d}" for c in sucursales]}
        ),
        "moneda": pd.DataFrame(
            {"codigo": monedas, "nombre": [nombre("moneda", m) for m in monedas]}
        ),
        "tipo_documento": pd.DataFrame(
            {
                "codigo": tipos_documento,
                "nombre": [nombre("tipo_documento", t) for t in tipos_documento],
            }
        ),
        "codigo_operacion": pd.DataFrame(
            {
                "codigo": codigos_operacion,
                "nombre": [nombre("codigo_operacion", c) for c in codigos_operacion],
                "signo": [-1 if c in reglas.CODIGOS_DEBITO else 1 for c in codigos_operacion],
            }
        ),
        "canal": pd.DataFrame(
            {"codigo": canales, "nombre": [nombre("canal", c) for c in canales]}
        ),
        "servicio_mandato": pd.DataFrame(
            {"codigo": servicios, "nombre": [nombre("servicio_mandato", s) for s in servicios]}
        ),
    }


def _descripciones_catalogo() -> dict[str, dict[str, str]]:
    """Descripciones legibles de los codigos destino (mapeo_catalogos.csv)."""
    descripciones: dict[str, dict[str, str]] = {}
    ruta = reglas.CONFIG / "mapeos" / "mapeo_catalogos.csv"
    with ruta.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            descripciones.setdefault(fila["dominio"], {})[fila["valor_destino"]] = fila[
                "descripcion"
            ]
    return descripciones
