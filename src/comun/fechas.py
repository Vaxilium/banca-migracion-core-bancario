"""Manejo de fechas del legado: formato AAMMDD con ambiguedad de siglo."""

from datetime import date

UMBRAL_SIGLO_DEFECTO = 30


def fecha_desde_aammdd(texto: str, umbral_siglo: int = UMBRAL_SIGLO_DEFECTO) -> date:
    """Convierte un texto AAMMDD a fecha.

    Regla de siglo (supuesto documentado): si AA <= umbral, el anio pertenece al
    siglo 2000; en caso contrario, al siglo 1900. Lanza ValueError si la fecha
    es imposible (mes o dia fuera de rango).
    """
    limpio = texto.strip()
    if len(limpio) != 6 or not limpio.isdigit():
        raise ValueError(f"fecha AAMMDD invalida: {texto!r}")
    anio_corto = int(limpio[0:2])
    mes = int(limpio[2:4])
    dia = int(limpio[4:6])
    siglo = 2000 if anio_corto <= umbral_siglo else 1900
    return date(siglo + anio_corto, mes, dia)


def aammdd_desde_fecha(fecha: date) -> str:
    """Convierte una fecha a texto AAMMDD (formato del legado)."""
    return f"{fecha.year % 100:02d}{fecha.month:02d}{fecha.day:02d}"


def dd_mm_aaaa(fecha: date) -> str:
    """Formatea una fecha como dd/mm/aaaa para textos e informes."""
    return fecha.strftime("%d/%m/%Y")
