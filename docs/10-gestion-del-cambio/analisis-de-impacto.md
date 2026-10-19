# Análisis de impacto y gestión del cambio

| Proyecto | Fecha | Autor | Estado |
|---|---|---|---|
| Migración del core bancario — Banco Meridiano Austral | 19/10/2026 | Franco Tilleria, Analista de Negocios | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Análisis de impacto, plan de comunicación y capacitación. |

## Propósito

Identificar qué cambia para cada área, quién debe estar preparado y cómo se acompaña
la transición para que el lunes posterior al corte la operación funcione sin fricción.
El análisis cubre personas, procesos, tecnología, datos y controles.

## Alcance

Aplica a sucursales, atención al cliente, operaciones, contabilidad, sistemas,
cumplimiento y proveedores. Los clientes finales solo perciben continuidad de servicio
y extractos digitales; no hay cambio de producto ni de contrato.

## Impacto por dimensión

| Dimensión | Situación actual | Situación futura | Impacto | Mitigación |
|---|---|---|---|---|
| Procesos de sucursal | Consulta y caja sobre el legado, con tiempos de batch nocturno. | Consulta en línea y cierre diario más simple. | Medio | Guía rápida de tres pasos y acompañamiento en piso la primera semana. |
| Atención al cliente | Reclamos por demoras de acreditación. | Acreditaciones en línea y extractos digitales. | Medio | FAQ, guion de atención y derivación de casos al war room. |
| Operaciones | Batch rígido y reprocesos manuales. | Pipeline reproducible y delta controlada. | Alto | Capacitación en runbook, tablero y conciliación diaria. |
| Contabilidad | Conciliación manual y ajustes sin trazabilidad homogénea. | Conciliación automatizada con evidencia y ajustes aprobados. | Alto | Taller de conciliación, revisión de los 8 ajustes y firma del mayor. |
| Sistemas | Monitoreo del core legado y del scheduler. | Monitoreo del core nuevo, contratos y pipeline. | Alto | Traspaso técnico, monitoreo conjunto y plan de reversa. |
| Datos | Extracciones de ancho fijo y reprocesos. | Parquet, contratos y delta con suma de control. | Alto | Documentación de linaje y validación de muestras. |
| Cumplimiento | Documentos observados sin cierre sistemático. | 2.065 documentos observados con seguimiento. | Medio | Bandeja de revisión y control compensatorio hasta regularizar. |
| Clientes no migrados | 927 clientes con fecha imposible. | Altas manuales posteriores al corte. | Medio | Comunicación y cola de regularización con dueño. |
| Cuentas en estado X | 3.748 cuentas cargadas como informativas. | Decisión registrada antes del corte (RF-010). | Alto | Triage previo y bloqueo de operación hasta decisión. |
| Préstamos incongruentes | 540 préstamos con capital distinto a cuotas pendientes. | Diferencia 4.889,14 explicada y fuera del mayor. | Bajo | Seguimiento contable y regularización posterior. |
| Proveedor del core | Soporte del legado en modo reactivo. | Soporte nuevo con SLA y mesa conjunta. | Medio | Plan de soporte extendido durante hypercare. |
| Cultura y roles | Responsabilidad difusa entre datos y negocio. | Dueños de dato y controles definidos. | Medio | Matriz RACI y rituales de control. |

## Grupos afectados y preparación

| Grupo | Personas | Cambio principal | Capacitación | Soporte |
|---|---:|---|---|---|
| Sucursales | 120 | Consulta, caja y extractos en el core nuevo. | Taller de 2 horas y guía de una página. | Mentor en piso, primera semana. |
| Atención al cliente | 40 | Guion de consultas y reclamos. | Taller de 1 hora y FAQ. | Mesa de ayuda y war room. |
| Operaciones | 25 | Ejecución del runbook, delta y monitoreo. | Simulacro de 4 horas. | Ingeniero de guardia. |
| Contabilidad | 12 | Conciliación, ajustes y firma diaria. | Taller de 3 horas con casos reales del ensayo 3. | Analista de datos asignado. |
| Sistemas y proveedor | 18 | Pipeline, contratos, respaldo y reversa. | Traspaso técnico de 2 días. | Comité técnico diario en hypercare. |
| Cumplimiento | 8 | Documentos observados y accesos. | Sesión de 1 hora. | Reporte semanal. |

## Estrategia de cambio

Se aplica un enfoque de adopción por evidencias, no por imposición:

1. **Conciencia**: comunicar por qué se migra (cierre diario, trazabilidad, riesgo
   operativo) y qué cambia para cada rol.
2. **Deseo**: involucrar a usuarios clave en el diseño del runbook y en los smoke
   tests; mostrar beneficios concretos.
3. **Conocimiento**: capacitación por rol con casos del ensayo 3 y material de bolsillo.
4. **Habilidad**: simulacro de ventana y práctica en ambiente de ensayo.
5. **Refuerzo**: métricas de adopción, reconocimiento y corrección rápida en hypercare.

## Plan de comunicación

| Momento | Audiencia | Mensaje | Canal | Responsable |
|---|---|---|---|---|
| T-30 | Comité y gerencias | Alcance, fecha y riesgos residuales. | Comité directivo | Patrocinador |
| T-15 | Dueños de proceso | Impacto por área y pendientes. | Taller | Líder de migración |
| T-7 | Usuarios | Qué cambia, qué no cambia y a quién contactar. | Correo e intranet | Gestión del cambio |
| T-1 | Sucursales y atención | Congelamiento y ventana. | Circular | Operaciones |
| Día de corte | Todos | Hitos, decisión go/no-go y apertura. | Canal de guerra | Mesa de ayuda |
| D+1 | Sucursales | Guía rápida, horarios y soporte. | Intranet y piso | Negocio |
| D+7 | Comité | Incidentes, adopción y ajustes. | Informe semanal | Líder de migración |
| D+30 | Organización | Cierre de hypercare y lecciones. | Comunicación final | Patrocinador |

## Readiness previo al corte

- [ ] Cada rol tiene capacitación registrada y material vigente.
- [ ] Los usuarios clave completaron el simulacro y aprobaron los smoke tests.
- [ ] Las guías rápidas y FAQ están publicadas.
- [ ] La mesa de ayuda conoce el escalamiento y el guion de incidentes.
- [ ] Los pendientes de decisión tienen dueño y fecha.
- [ ] El plan de reversa fue comunicado a sucursales y atención.
- [ ] El war room y los reemplazos están confirmados.
- [ ] Los indicadores de adopción y soporte están definidos.

## Indicadores de adopción

| Indicador | Meta | Medición |
|---|---|---|
| Usuarios capacitados por rol | 100 % antes del corte | Registro de asistencia |
| Consultas de soporte por sucursal y día | Reducción de 50 % al día 10 | Mesa de ayuda |
| Incidentes severos en hypercare | Cero por día | War room |
| Conciliación diaria | Cero diferencias no explicadas | Contabilidad |
| Satisfacción de usuarios clave | 4 de 5 o más al día 30 | Encuesta breve |
| Reclamos por extractos o saldos | Sin aumento sostenido | Atención al cliente |

## Riesgos de adopción

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Resistencia por falta de información | Uso de canales informales y errores. | Comunicación temprana y FAQ. |
| Brecha de capacitación en caja | Demoras en atención. | Mentor en piso y guía de una página. |
| Dependencia de una persona clave | Cuello de botella en incidentes. | Reemplazos definidos y documentación. |
| Pendientes de cumplimiento sin cierre | Observación regulatoria. | Bandeja con dueño y reporte semanal. |
| Fatiga del equipo en hypercare | Errores y rotación. | Turnos, relevos y criterios de salida claros. |

## Criterios de cierre del cambio

Se cierra la gestión del cambio cuando se cumplen 30 días de hypercare, la conciliación
diaria está en cero, no hay incidentes severos abiertos, la satisfacción de usuarios
clave alcanza la meta y los pendientes documentales tienen plan aprobado.

## Referencias

- [Interesados y gobierno](../01-marco-y-estrategia/interesados-y-gobierno.md)
- [Runbook de corte](../09-corte-y-reversa/runbook-de-corte.md)
- [Informe de conciliación](../07-conciliacion/informe-de-conciliacion.md)
- [Estrategia de pruebas](../08-pruebas/estrategia-de-pruebas.md)
