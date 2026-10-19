# Estrategia de pruebas

| Proyecto | Fecha | Autor | Estado |
|---|---|---|---|
| Migración del core bancario — Banco Meridiano Austral | 19/10/2026 | Franco Tilleria, Analista de Negocios | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Estrategia, escenarios Gherkin e informe de la última corrida. |

## Propósito

Este documento define cómo se verifican las reglas de transformación, la carga, la
delta del corte y la conciliación antes de habilitar el pasaje a producción. La
estrategia prioriza la evidencia reproducible: toda prueba se ejecuta con
`make pruebas` sobre los artefactos generados por el pipeline, y las cifras de este
informe salen del reporte JUnit de esa corrida.

## Alcance

| Componente | Qué se verifica |
|---|---|
| Reglas de transformación | Conversión de importes, fechas, horas, documentos, normalización y enmascaramiento. |
| Generación del legado | Determinismo con semilla fija y coherencia de los documentos ficticios. |
| Pipeline de migración | Claves únicas, libro mayor balanceado, tarjetas enmascaradas, conteos y rechazos. |
| Delta del corte | Cuentas nuevas, reemplazo de saldos y movimientos incorporados una sola vez. |
| Conciliación | Ecuación de saldo, descuadres, desfases contables y decisión go/no-go. |
| Especificaciones | Cobertura entre los escenarios Gherkin y las pruebas automatizadas. |

## Enfoque

La suite sigue una pirámide de pruebas:

1. **Unitarias**: funciones puras de reglas, fechas, validaciones y generación. Son
   rápidas y no dependen de datos generados.
2. **Integración**: contrastan los Parquet, rechazos y resultados de conciliación
   contra la verdad de terreno y las ecuaciones de control. Se omiten si los
   artefactos no existen, para que la suite funcione en un clon limpio.
3. **Especificaciones Gherkin**: cada escenario tiene un identificador `PR-xxx` y una
   prueba que lo cita con el marker `escenario`. Una prueba de cobertura falla si un
   escenario queda sin implementación.
4. **Seguridad de datos**: se verifica el enmascaramiento determinista y la ausencia
   de números de tarjeta completos en las muestras publicadas.

No se simula UAT con usuarios reales: el alcance es un portafolio reproducible con
datos sintéticos, y esa limitación se declara en los riesgos residuales.

## Entorno y datos

- Python 3.13 con pytest y DuckDB; sin servicios externos.
- Semilla fija `20261019`: el legado, la verdad de terreno y los Parquet se regeneran
  con `make todo`.
- Las pruebas de integración leen `datos/destino/ensayo_v3`, `datos/resultados/` y
  `datos/verdad/defectos_inyectados.csv`; no escriben en el destino.
- La corrida deja `datos/resultados/junit.xml`, insumo del presente informe.

## Criterios de entrada

- Pipeline de migración y conciliación ejecutados sin errores.
- Contratos de destino validados y muestras de 200 filas conformes.
- Verdad de terreno disponible para el contraste de descuadres y desfases.

## Criterios de salida

- 100 % de las pruebas planificadas ejecutadas; ninguna falla bloqueante abierta.
- Todos los escenarios Gherkin con prueba asociada.
- Conteos, saldos y movimientos de la conciliación con diferencia cero.
- Descuadres y desfases coincidentes con la verdad de terreno.
- Decisión go/no-go del ensayo 3 documentada con sus observaciones.

## Escenarios Gherkin

<!-- INICIO AUTO: pruebas-caracteristicas -->
| Caracteristica | Escenarios | Identificadores |
|---|---:|---|
| Conciliacion de saldos y libro mayor | 5 | PR-008, PR-009, PR-010, PR-011, PR-012 |
| Corte delta entre extraccion y migracion | 3 | PR-013, PR-014, PR-015 |
| Transformacion y carga del legado | 7 | PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007 |
| Proteccion de datos en artefactos publicados | 2 | PR-016, PR-017 |
<!-- FIN AUTO: pruebas-caracteristicas -->

Los archivos fuente están en `pruebas/caracteristicas/` y se ejecutan como
especificaciones vivas: la prueba `test_escenarios_implementados` falla si aparece un
escenario sin implementación o una prueba cita un escenario inexistente.

## Resultados de la última ejecución

<!-- INICIO AUTO: pruebas-resumen -->
| Modulo | Pruebas | Pasadas | Fallidas | Omitidas | Duracion (s) |
|---|---:|---:|---:|---:|---:|
| Conciliacion | 5 | 5 | 0 | 0 | 0.43 |
| Especificaciones Gherkin | 3 | 3 | 0 | 0 | 0.00 |
| Generacion determinista | 3 | 3 | 0 | 0 | 0.03 |
| Migracion y carga | 9 | 8 | 0 | 1 | 1.62 |
| Reglas de transformacion | 11 | 11 | 0 | 0 | 0.16 |
| **Total** | **31** | **30** | **0** | **1** | **2.24** |
<!-- FIN AUTO: pruebas-resumen -->

La prueba de muestras queda omitida mientras no se generen los archivos publicables
(`make muestras`); el resto de la suite no depende de esa salida.

## Gestión de defectos

| Severidad | Criterio | Tratamiento |
|---|---|---|
| Bloqueante | Impide cargar o conciliar una entidad; rompe una ecuación de control. | Detiene el corte; se corrige y se repite la suite completa. |
| Grave | Afecta importes, signos o claves de una cuenta o préstamo. | Se documenta, se ajusta con evidencia o se deriva a revisión manual. |
| Leve | Formato, normalización o dato descriptivo sin efecto contable. | Se registra y se corrige en la siguiente iteración. |

Los defectos del legado no se corrigen en origen: el pipeline los rechaza, los ajusta
con evidencia o los deja en revisión, según el ADR-012. La suite verifica que cada
decisión sea trazable.

## Trazabilidad

| Requisito | Cobertura |
|---|---|
| RNF-005 Integridad con sumas de control | Conteos por entidad y conciliación de saldos y movimientos. |
| RNF-014 Reproducibilidad total | Generación determinista con semilla y regeneración completa con `make todo`. |
| RNF-015 Tolerancias configurables | Prueba de la tolerancia monetaria y del umbral de ajuste en `config/reglas/conciliacion.yaml`. |
| RF-024 Conciliación contable automatizada | Descuadres, desfases y libro mayor recalculado contra la verdad de terreno. |

## Riesgos residuales

- No hay UAT con usuarios ni prueba de volumen ampliado; el rendimiento se mide con
  el volumen sintético completo, no con el doble de carga.
- La verdad de terreno es la del generador: valida la lógica del pipeline, no defectos
  nuevos que aparezcan en una extracción real.
- Las muestras aún no se publican; cuando existan, la prueba de tarjetas completas se
  ejecutará sin omitirse.

## Referencias

- [Pipeline de migración](../06-pipeline/pipeline-de-migracion.md)
- [Informe de conciliación](../07-conciliacion/informe-de-conciliacion.md)
- [ADR-012: ajustes de migración](../decisiones/ADR-012-ajustes-de-migracion.md)
- [Requisitos](../../config/requisitos/requisitos.yaml)
