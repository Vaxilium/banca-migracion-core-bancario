# Puntos de dolor del estado actual (AS-IS)

| Proyecto | Migración del core bancario — Banco Meridiano Austral (entidad ficticia) |
|---|---|
| **Versión** | 1.0 |
| **Fecha** | 19/10/2026 |
| **Autor** | Franco Tilleria, Analista de Negocios |
| **Estado** | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Versión inicial. |

## Propósito

Registrar los puntos de dolor del AS-IS con su impacto, severidad y la forma de
verificarlos con evidencia; constituyen la justificación funcional de las brechas
(fase 3) y de los beneficios del [caso de negocio](../01-marco-y-estrategia/caso-de-negocio.md).

## Alcance

Puntos de dolor de negocio, operativos y de datos observados en el core legado y sus
interfaces. La evidencia cuantitativa se genera en fases posteriores.

## Registro de puntos de dolor

| ID | Área | Punto de dolor | Impacto | Severidad | Cómo se verifica |
|---|---|---|---|---|---|
| PD-01 | Clientes | Duplicidad de clientes por comparación exacta de nombre | Reportes inflados, metas erróneas, múltiples cartas | Alta | Perfilado del origen: duplicados detectados (fase 5). |
| PD-02 | Canales | Movimientos visibles recién al día siguiente | Reclamos de clientes; pérdida de competitividad | Alta | Diseño del batch (fase 2) y objetivos del core nuevo. |
| PD-03 | Préstamos | Un único reintento nocturno de débito automático | Mora técnica evitable | Media | Flujo de cobro de cuota (fase 2). |
| PD-04 | Tarjetas de débito | Altas y bloqueos por lote nocturno | Cliente sin tarjeta hasta 24 h | Media | Tiempos del flujo de apertura (fase 2). |
| PD-05 | Cumplimiento | Validación manual de documentos si el padrón no responde | Riesgo de alta con documento inválido | Alta | Defectos de documento inyectados y detectados (fases 4 y 5). |
| PD-06 | Cobranzas | Avisos de mora por lote postal/correo | Cobranza tardía y costosa | Media | Flujo de cobro de cuota (fase 2). |
| PD-07 | Contabilidad | Descuadres detectados en el cierre y resueltos a mano | Horas extra; riesgo de ajustes sin pista | Alta | Defectos de descuadre medidos por la conciliación (fase 7). |
| PD-08 | Contabilidad | Cuadre del mayor mensual en planillas | Sin trazabilidad automática asiento a asiento | Alta | Reglas de conciliación contable (fase 7). |
| PD-09 | Datos | Direcciones incompletas y texto libre sobrecargado | Correspondencia perdida; campañas inefectivas | Media | Perfilado de calidad de datos (fase 5). |
| PD-10 | Sistemas | Sin APIs: cada canal duplica archivos y lógica | Costo de evolución; errores por duplicación | Alta | Inventario de interfaces (fase 2). |
| PD-11 | Operaciones | Cambios de parámetros requieren ventana de fin de semana | Lentitud comercial | Media | Proceso batch nocturno (fase 2). |
| PD-12 | Auditoría | Pista de auditoría incompleta por operador | Hallazgos recurrentes de auditoría interna | Alta | Control CAP-15 con madurez 1 (fase 2). |

## Evidencia cuantificada por el perfilado

El siguiente cuadro se completa automáticamente con las salidas reales del perfilado
del origen generado en la fase 4 (nunca con cifras escritas a mano).

<!-- INICIO AUTO: dolores-perfilado -->
_(Sección generada automáticamente por `src/informes/actualizar_documentos.py`.)_
<!-- FIN AUTO: dolores-perfilado -->

## Priorización

| Prioridad | Puntos | Criterio |
|---|---|---|
| 1 | PD-05, PD-07, PD-08, PD-10, PD-12 | Riesgo contable, regulatorio o de control. |
| 2 | PD-01, PD-02, PD-09 | Experiencia del cliente y calidad de información. |
| 3 | PD-03, PD-04, PD-06, PD-11 | Eficiencia operativa y tiempos de mercado. |

## Supuestos

- La severidad es una evaluación funcional; se recalibra con incidentes reales de
  Operaciones y Auditoría.
- Los puntos de dolor se vinculan a brechas en la fase 3 mediante la matriz de
  trazabilidad (fase 12).

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Puntos de dolor sin dueño | Asignación en el comité operativo. |
| Evidencia insuficiente | El perfilado y la conciliación producen métricas verificables. |

## Glosario

Ver [glosario único](../glosario.md).
