# Matriz de trazabilidad

| Proyecto | Fecha | Autor | Estado |
|---|---|---|---|
| Migración del core bancario — Banco Meridiano Austral | 19/10/2026 | Franco Tilleria, Analista de Negocios | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Matriz de requisitos, evidencia y estado de cobertura. |

## Propósito

Vincular cada requisito con su evidencia verificable y su estado en el proyecto. La
matriz permite responder, para cualquier requisito, dónde está diseñado, dónde se
implementa y qué artefacto lo demuestra.

## Método

| Estado | Significado |
|---|---|
| Implementado | Existe un artefacto ejecutable o verificable en el repositorio. |
| Parcial | El dato o control existe, pero la funcionalidad completa queda para el core nuevo. |
| Diseñado | Está analizado y especificado; su ejecución pertenece al core nuevo o a un alcance posterior. |

La fuente de requisitos es `config/requisitos/requisitos.yaml` (56 requisitos). El
generador `src/informes/trazabilidad.py` verifica que no falte ningún identificador y
actualiza el resumen.

## Resumen de cobertura

<!-- INICIO AUTO: trazabilidad-resumen -->
| Estado | Requisitos | Must | Porcentaje |
|---|---:|---:|---:|
| Implementado | 31 | 28 | 55,4 % |
| Parcial | 8 | 4 | 14,3 % |
| Diseñado | 17 | 10 | 30,4 % |
| **Total** | **56** | **42** | **100,0 %** |

39 de 56 requisitos (69,6 %) tienen evidencia implementada o parcial; el resto queda diseñado para el core nuevo.
<!-- FIN AUTO: trazabilidad-resumen -->

## Matriz

| ID | Requisito | Prioridad | Evidencia | Estado |
|---|---|---|---|---|
| RF-001 | Deduplicación de clientes al migrar | Must | ADR-009; deduplicación v2/v3; 1.694 fusiones conciliadas. | Implementado |
| RF-002 | Validación de documentos de identidad | Must | `reglas.validar_*`; rechazos por documento inválido. | Implementado |
| RF-003 | Exclusión de titulares fallecidos | Must | Análisis de brechas; el legado sintético no trae marca de fallecimiento. | Diseñado |
| RF-004 | Contacto ampliado obligatorio | Must | Normalización de teléfono y correo; modelo destino. | Implementado |
| RF-005 | Control de vigencia documental | Should | Campos de emisión/vencimiento y marca `vigente`. | Implementado |
| RF-006 | Rechazo de documentos repetidos | Should | CAL-001; rechazos por documento repetido. | Implementado |
| RF-007 | Normalización de direcciones | Must | `domicilio_cliente`; normalización de calle y número. | Implementado |
| RF-008 | Extracción de datos desde texto libre | Should | Regla de texto libre v3; teléfono alternativo y documento pendiente. | Implementado |
| RF-009 | Parámetros de producto configurables | Must | `config/parametrico/productos.yaml` y reglas versionadas. | Implementado |
| RF-010 | Cola de revisión para estados desconocidos | Must | Cuentas X cargadas informativas y pendientes del runbook. | Implementado |
| RF-011 | Descubierto y comisiones como condiciones | Must | Modelo de datos y análisis funcional del core nuevo. | Diseñado |
| RF-012 | Impuesto sobre débitos y créditos | Must | Análisis de brechas y reglas de negocio del core nuevo. | Diseñado |
| RF-013 | Renovación automática de plazos fijos | Should | Análisis funcional del core nuevo. | Diseñado |
| RF-014 | Cancelación anticipada con prorrateo | Should | Análisis funcional del core nuevo. | Diseñado |
| RF-015 | Cronogramas de cuotas consistentes | Must | Generación y carga de cuotas; CAL-010. | Implementado |
| RF-016 | Mora y refinanciación | Must | Análisis funcional del core nuevo. | Diseñado |
| RF-017 | Exclusión de préstamos hipotecarios | Must | Mapeo PH a rechazo (ADR-005). | Implementado |
| RF-018 | Gestión de tarjetas de débito en línea | Must | Indicador de tarjeta y número enmascarado (ADR-010). | Implementado |
| RF-019 | Tarjeta de débito asociada a cuenta | Must | Atributos de tarjeta en el maestro de cuentas. | Implementado |
| RF-020 | Mandatos de débito automático operativos | Must | `mandato_debito` y CAL-012. | Implementado |
| RF-021 | Transferencias por servicio | Must | Movimientos y códigos de operación migrados. | Parcial |
| RF-022 | Plan de cuentas y matriz producto-contabilidad | Must | `plan_cuentas`, `saldos_contables` y mapeo contable. | Implementado |
| RF-023 | Asientos automáticos por evento | Must | Saldos contables y conciliación; motor de asientos del core nuevo. | Parcial |
| RF-024 | Conciliación contable automatizada | Must | Informe de conciliación fase 7; 0 diferencias de control. | Implementado |
| RF-025 | Intereses diarios de cajas de ahorro | Must | Análisis funcional del core nuevo. | Diseñado |
| RF-026 | Comisiones configurables y reversibles | Must | Análisis funcional del core nuevo. | Diseñado |
| RF-027 | Reportes regulatorios desde el modelo destino | Must | Modelo destino y análisis; reportes del core nuevo. | Diseñado |
| RF-028 | Trazabilidad de la información migrada | Must | Bitácora, rechazos y esta matriz. | Implementado |
| RF-029 | Extractos y consultas en línea | Should | Análisis funcional del core nuevo. | Diseñado |
| RF-030 | Migración de historial de movimientos | Must | Ventana de 12 meses y delta del corte. | Implementado |
| RF-031 | Reintentos programables de cobro | Should | Análisis funcional del core nuevo. | Diseñado |
| RF-032 | Avisos de mora multicanal | Could | Análisis funcional del core nuevo. | Diseñado |
| RF-033 | Pista de auditoría completa | Must | Bitácora por ensayo y artefactos versionados. | Implementado |
| RF-034 | Segregación de funciones | Must | Modelo de gobierno y matriz RACI. | Diseñado |
| RF-036 | Conciliación de saldos por cuenta | Must | Reconstrucción de movimientos y descuadres. | Implementado |
| RF-037 | Bitácora de ejecución del pipeline | Must | `datos/bitacora/` y resumen por ensayo. | Implementado |
| RF-038 | Intercambio controlado con satélites | Should | Análisis de interfaces y rechazos controlados. | Diseñado |
| RF-039 | Rechazo controlado de productos fuera de alcance | Must | Rechazos TR, PH y PX con motivo. | Implementado |
| RF-040 | Mapeo de tipos de firma y condiciones | Could | Mapeo funcional documentado; sin campo en el legado sintético. | Parcial |
| RF-041 | Operatoria de caja cubierta | Must | Movimientos de caja generados y migrados; operatoria del core nuevo. | Parcial |
| RF-042 | Consulta de saldos por servicio | Must | Saldos conciliados en el destino; consulta del core nuevo. | Parcial |
| RNF-001 | Rendimiento de la carga completa | Must | Corrida completa en 70,4 s para 1.476.247 filas. | Implementado |
| RNF-002 | Disponibilidad del core nuevo | Must | Runbook, hipercare y monitoreo definidos. | Diseñado |
| RNF-003 | Enmascaramiento de datos personales | Must | ADR-010 y pruebas PR-006/PR-016/PR-017. | Implementado |
| RNF-004 | Auditabilidad del pipeline | Must | Bitácora inmutable por ensayo. | Implementado |
| RNF-005 | Integridad con sumas de control | Must | Conteos y conciliación de saldos y movimientos. | Implementado |
| RNF-006 | Usabilidad en sucursales | Should | Plan de cambio, capacitación y smoke tests. | Diseñado |
| RNF-007 | Mantenibilidad de reglas | Must | Reglas YAML versionadas y tres ensayos auditables. | Implementado |
| RNF-008 | Escalabilidad | Should | Modelo y volúmenes; sin prueba de carga ampliada. | Parcial |
| RNF-009 | Volumen de archivos | Should | Lectura de ancho fijo; sin prueba de 2 GB. | Parcial |
| RNF-010 | Objetivos de recuperación | Must | ADR-013 y runbook de reversa (RTO 4 h, RPO 15 min). | Diseñado |
| RNF-011 | Observabilidad del pipeline | Should | Bitácora y resumen; tablero en fase 13. | Parcial |
| RNF-012 | Retención de información | Must | Artefactos y bitácoras versionados en el repositorio. | Implementado |
| RNF-013 | Idioma y terminología | Must | Documentación y salidas en español; glosario único. | Implementado |
| RNF-014 | Reproducibilidad total | Must | Semilla fija, pruebas de determinismo y `make todo`. | Implementado |
| RNF-015 | Tolerancias de conciliación configurables | Must | `config/reglas/conciliacion.yaml` y prueba de umbral. | Implementado |

## Requisitos con brecha

Los requisitos en estado Diseñado corresponden a funcionalidad del core nuevo que no
forma parte de la migración de datos; su análisis y criterio de aceptación están en
`docs/03`. Los estados Parciales tienen el dato migrado o el control definido, pero la
operación completa depende del core nuevo o de una prueba de carga ampliada. Ningún
requisito Must de la migración queda sin evidencia.

## Referencias

- [Requisitos](../../config/requisitos/requisitos.yaml)
- [Análisis de brechas](../03-analisis-de-brechas/analisis-de-brechas.md)
- [Pipeline de migración](../06-pipeline/pipeline-de-migracion.md)
- [Informe de conciliación](../07-conciliacion/informe-de-conciliacion.md)
- [Estrategia de pruebas](../08-pruebas/estrategia-de-pruebas.md)
