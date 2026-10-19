# ADR-011: Motor de carga y formato del destino

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

La migración debe dejar el resultado en un formato apto para análisis (conciliación,
tablero, pruebas) y reproducible por cualquier persona que clone el repositorio. Las
opciones evaluadas: cargar en un motor de base de datos (PostgreSQL, SQL Server),
generar CSV, o escribir archivos columnares.

El volumen del legado sintético (más de 1,4 millones de filas destino en total) y la
necesidad de dejar **evidencia de cada rechazo y cada decisión** obligan a que la
carga sea transaccional por tabla, idempotente y auditable.

## Decisión

1. **DuckDB embebido** como motor de carga y lectura analítica: no requiere servidor,
   se instala con `pip`, y escribe y consulta Parquet con SQL estándar.
2. **Parquet por tabla** en `datos/destino/ensayo_v{n}/`: compresión y tipado fuerte,
   lectura columnar para los informes y el tablero. Los datos grandes quedan fuera de
   Git; el repositorio publica las cifras y las muestras.
3. **Rechazos y bitácora en CSV**: son el rastro auditable pedido por la
   conciliación; cada fila lleva entidad, motivo, clave, detalle y acción. Se
   publican también como muestra recortada.
4. **Contratos por tabla**: antes de publicar, se genera un JSON Schema desde
   `config/mapeos/modelo_destino.yaml` y se valida una muestra de 200 filas; si una
   tabla incumple, la corrida falla y no se publica.
5. **Delta con upsert por clave**: la carga del corte se resuelve con un ANTI JOIN
   (insertar claves nuevas) y un SEMI JOIN (reemplazar vigentes), todo dentro de
   DuckDB, sin reprocesar el histórico completo.

## Alternativas consideradas

1. PostgreSQL local: exige servicio, usuarios y versiones fijas; sobra para el
   objetivo de análisis y complica la reproducibilidad.
2. CSV para todo el destino: pierde tipos y es lento de consultar a este volumen.
3. Cargar la delta reprocesando todo el legado: multiplica el tiempo de corrida y el
   riesgo operativo del corte.

## Consecuencias

- El pipeline completo corre en minutos con `make migracion` y no necesita
  infraestructura.
- La conciliación (fase 7) y el tablero consultan las mismas tablas Parquet: una sola
  fuente de verdad para todas las cifras publicadas.
- El formato Parquet permite migrar a un motor productivo después sin cambiar las
  reglas: la lógica de transformación vive en Python y las claves son las del legado.
