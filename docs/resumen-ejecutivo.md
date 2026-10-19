# Resumen ejecutivo

| Proyecto | Fecha | Autor |
|---|---|---|
| Migración del core bancario — Banco Meridiano Austral (entidad ficticia) | 19/10/2026 | Franco Tilleria, Analista de Negocios |

## El problema

El banco operaba un core legado con datos inconsistentes, procesos batch rígidos y
conciliación manual. La migración debía trasladar clientes, cuentas, movimientos,
préstamos, plazos y mandatos sin perder trazabilidad, con un corte controlado y una
reversa posible. El desafío no era solo técnico: había que demostrar que cada cifra
del destino podía explicarse contra el origen.

## El enfoque

Se ejecutó un proyecto completo por fases: análisis AS-IS, brechas, modelo de datos,
reglas versionadas, tres ensayos de migración, conciliación contable, pruebas,
corte y gestión del cambio. Todo se genera con una semilla fija y se publica con
evidencia: legado sintético, verdad de terreno de defectos, bitácoras, Parquet de
destino y documentos con cifras autogeneradas.

## Resultados clave

| Resultado | Cifra |
|---|---|
| Filas migradas en el ensayo final | 1.476.247 |
| Entidades con conteo cerrado | 12 de 12 |
| Diferencias de saldo y movimiento | 0 |
| Descuadres detectados y clasificados | 1.747 (1.405 automáticos, 342 en revisión) |
| Desfases contables detectados y ajustados | 8, neto −3.907.829,68 |
| Cuentas del mayor conciliadas | 20 de 28, sin desbalances internos |
| Delta del corte | 117 cuentas nuevas, 4.902 saldos actualizados, 10.832 movimientos |
| Pruebas automatizadas | 31: 30 aprobadas, 1 omitida por muestras pendientes |
| Decisión del comité | Ensayo 3: GO con observaciones |

Los ensayos 1 y 2 quedaron en NO-GO porque cargaban movimientos con signo invertido y
desfases contables sin ajuste; el ensayo 1 además no deduplicaba clientes. La
comparación entre ensayos es parte de la evidencia: muestra por qué la versión final
es la única aceptable.

## Decisiones que sostienen el resultado

- **Reglas como datos versionados** (`reglas_v1.yaml`, `v2`, `v3`), no código
  embebido: cada ensayo es auditable y reversible.
- **Deduplicación y enmascaramiento** con evidencia: 1.694 fusiones de clientes y
  ningún número de tarjeta completo en el destino.
- **Ajustes con tolerancia**: descuadres de hasta 100 pesos se regularizan con
  apertura evidenciada; los graves van a revisión (ADR-012).
- **Corte big-bang con delta** y reversa por conmutación al legado, con RTO de 4 horas
  y RPO de 15 minutos (ADR-013).

## Riesgos y pendientes

El corte es viable con observaciones: 342 descuadres graves, 3.748 cuentas en estado
desconocido, 2.065 documentos observados y 540 préstamos con saldo incongruente
requieren dueño y decisión antes del congelamiento. Los 927 clientes no migrados por
fecha imposible se regularizan después del corte. Ninguno de estos pendientes afecta
las ecuaciones de control del destino.

## Lectura recomendada

- [Tablero interactivo](tablero.html)
- [Informe de conciliación](07-conciliacion/informe-de-conciliacion.md)
- [Pipeline de migración](06-pipeline/pipeline-de-migracion.md)
- [Runbook de corte](09-corte-y-reversa/runbook-de-corte.md)
- [Presentación al comité](presentacion-comite.md)
