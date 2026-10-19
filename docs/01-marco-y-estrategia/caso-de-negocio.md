# Caso de negocio de la migración

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

Justificar ante la dirección la decisión de migrar el core bancario, cuantificando el
costo de no hacer nada, los beneficios esperados y las alternativas evaluadas.

> **Nota metodológica.** Todas las cifras monetarias de este documento son supuestos
> ilustrativos en unidades monetarias ficticias (u.m.) y no corresponden a ninguna
> entidad real. Las cifras técnicas (conteos, tasas, tiempos de proceso) que aparecen
> en fases posteriores se generan automáticamente desde el código del repositorio.

## Situación actual: costo de no hacer nada

| Concepto | Valor anual (u.m.) | Sustento |
|---|---|---|
| Licencias y mantenimiento del core legado | 1.800.000 | Contrato vigente; se incrementa 12 % anual. |
| Hardware y ambiente del legado | 420.000 | Servidores dedicados fuera de garantía. |
| Horas de desarrollo sobre tecnología propietaria | 950.000 | Proveedor único; tarifa premium. |
| Operación del batch nocturno y resolución de incidentes | 380.000 | Guardias y reprocesos. |
| Trabajo manual asociado a interfaces por archivo | 260.000 | Conciliaciones manuales diarias. |
| **Total anual estimado** | **3.810.000** | Suma de los conceptos anteriores. |

Riesgos de continuidad si no se migra:

- Fin de soporte del proveedor en marzo de 2027; extensión con recargo del 40 %.
- Dependencia de dos especialistas con conocimiento no documentado del legado.
- Incapacidad de ofrecer APIs, operación 24/7 ni productos nuevos en tiempos de mercado.
- Hallazgos de auditoría por controles manuales sin pista automatizada.

## Alternativas evaluadas

| Alternativa | Descripción | Resultado |
|---|---|---|
| No hacer nada | Mantener el legado y pagar extensión de soporte. | Descartada: el costo crece y los riesgos de continuidad son inaceptables. |
| Remediar el legado | Modernizar por partes (APIs sobre el legado, nuevas interfaces). | Descartada: no elimina el modelo batch ni el costo estructural; pospone el problema. |
| Reemplazar el core | Migrar a un core relacional con servicios y operación casi en línea. | **Recomendada.** |

## Inversión del proyecto (3 olas de implementación)

| Concepto | Año 1 (u.m.) | Año 2 (u.m.) | Año 3 (u.m.) |
|---|---|---|---|
| Licencias del core nuevo | 900.000 | 950.000 | 1.000.000 |
| Implementación y migración (proveedor + interno) | 1.600.000 | 450.000 | 150.000 |
| Infraestructura y nube | 300.000 | 300.000 | 310.000 |
| Capacitación y gestión del cambio | 220.000 | 120.000 | 60.000 |
| **Total anual** | **3.020.000** | **1.820.000** | **1.520.000** |

## Beneficios esperados

| Beneficio | Impacto anual (u.m.) | Plazo |
|---|---|---|
| Ahorro de licencias y hardware del legado | 2.220.000 | Desde el año 2 |
| Menor costo de desarrollo (tecnología abierta, equipo propio) | 600.000 | Desde el año 2 |
| Reducción de operación nocturna e incidentes | 300.000 | Desde el año 2 |
| Eliminación de conciliaciones manuales de interfaces | 240.000 | Desde el año 1 |
| **Total beneficio anual (régimen)** | **3.360.000** | |

Beneficios no monetarios: cierre diario de 9 horas a menos de 2 horas, disponibilidad
para canales digitales casi en línea, capacidad de lanzar productos en semanas,
información consistente para el regulador y trazabilidad completa para auditoría.

## Evaluación económica (supuestos ilustrativos)

| Indicador | Valor |
|---|---|
| Inversión acumulada 3 años | 6.360.000 u.m. |
| Costo de no migrar en el mismo periodo | 10.240.000 u.m. (creciente) |
| Ahorro neto estimado a 3 años | ≈ 3.880.000 u.m. antes de beneficios no monetarios |
| Periodo de repago estimado | ≈ 30 meses |

## Recomendación

Aprobar la migración con estrategia de corte único de fin de semana (ver
[estrategia de migración](estrategia-de-migracion.md)), condicionada a: conciliación
contable completa en el ensayo general, plan de reversa probado y cero defectos
críticos abiertos.

## Supuestos

- Tarifas y volúmenes ilustrativos; se recalibran con datos reales en la práctica.
- El ahorro de licencias se materializa al apagar el legado (año 2 del plan).
- No se incluyen costos de oportunidad por indisponibilidad durante el corte.

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Sobrecosto de implementación | Contrato por hitos y control de cambio. |
| Beneficios menores a los estimados | Medición trimestral de beneficios con Contabilidad. |
| Dependencia del proveedor del core nuevo | Cláusulas de continuidad y escrow del código. |

## Glosario

Ver [glosario único](../glosario.md).
