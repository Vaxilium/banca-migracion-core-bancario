# ADR-008: Interpretación de fechas AAMMDD y umbral de siglo

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El legado guarda todas las fechas en formato AAMMDD de 6 dígitos, sin siglo. Para
interpretarlas hay que aplicar una convención de umbral: los años menores al umbral
pertenecen al 2000 y los mayores o iguales, al 1900. El umbral no está documentado
en el sistema de origen y la primera versión de las reglas de migración usó 25.

Con umbral 25, un año como "26" (presente en los movimientos de 2026) se interpreta
como **1926**: las fechas de movimientos recientes se corrompen de forma silenciosa
y la ventana de 12 meses queda vacía, efecto que solo se advierte al conciliar
conteos por período.

## Decisión

1. **Umbral de siglo = 30.** Años "00" a "29" son 2000–2029; años "30" a "99" son
   1930–1999. Con la ventana del proyecto (nacimientos desde 1920, operaciones hacia
   2026) esta convención no produce ambigüedad.
2. **Validación contextual obligatoria después de la conversión**, porque el umbral
   por sí solo no detecta fechas imposibles (por ejemplo `133201`, mes 13; `023201`,
   31 de febrero; `000230`, día 00). Las fechas resultantes se validan contra reglas
   de rango por tipo de fecha:
   - nacimientos entre 01/01/1920 y la fecha de extracción menos 18 años;
   - movimientos y operaciones dentro de la ventana de migración;
   - vencimientos de créditos dentro de [otorgamiento, extracción + 40 años].
3. **Las fechas inválidas se rechazan con motivo explícito** (`fecha_imposible` o
   `fuera_de_rango`), nunca se corrigen en silencio.

## Alternativas consideradas

1. Umbral 25 (versión 1 de reglas): rompe 2026, descartado tras el primer ensayo.
2. Año completo en origen: imposible, el contrato de archivo no lo incluye.
3. Aceptar todas las fechas convertibles: los valores imposibles llegarían al
   destino y romperían la conciliación.

## Consecuencias

- El ensayo v1 queda documentado con su defecto real (fechas 2026 → 1926) y el
  ensayo v2 lo corrige cambiando solo el parámetro `umbral_siglo` en las reglas.
- Los rechazos por fecha se reportan por motivo y se cruzan con la verdad de terreno,
  que registra cada fecha imposible inyectada.
