# Matriz de riesgos y controles

| Proyecto | Fecha | Autor | Estado |
|---|---|---|---|
| Migración del core bancario — Banco Meridiano Austral | 19/10/2026 | Franco Tilleria, Analista de Negocios | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Matriz inicial de riesgos, controles y riesgo residual. |

## Método

Cada riesgo se evalúa con probabilidad (P) e impacto (I) de 1 a 5. La exposición es
P × I: 1–4 bajo, 5–9 medio, 10–16 alto y 17–25 crítico. El riesgo residual se evalúa
después de aplicar el control y antes del corte.

| Nivel | Exposición | Tratamiento |
|---|---|---|
| Bajo | 1–4 | Aceptar y monitorear. |
| Medio | 5–9 | Mitigar con control y seguimiento mensual. |
| Alto | 10–16 | Plan de acción con dueño y reporte quincenal. |
| Crítico | 17–25 | Escalamiento al comité directivo y bloqueo de go. |

## Matriz

| ID | Riesgo | P | I | Exp. | Control / mitigación | Dueño | Residual |
|---|---|---:|---:|---:|---|---|---|
| R-01 | Pérdida o duplicación de registros durante la carga. | 2 | 5 | 10 | Conteos por entidad, contratos, conciliación y delta con suma de control. | Migración | 4 |
| R-02 | Descuadre de saldo no detectado en el corte. | 2 | 5 | 10 | Reconstrucción de movimientos y conciliación contra verdad; 1.405 ajustes automáticos y 342 casos en revisión. | Contabilidad | 6 |
| R-03 | Desfase contable sin ajuste aprobado. | 1 | 5 | 5 | Recálculo del mayor, 8 ajustes con contrapartida 3.3.01 y firma contable (ADR-012). | Contabilidad | 3 |
| R-04 | Clientes fusionados incorrectamente por la deduplicación. | 2 | 4 | 8 | Doble condición de deduplicación y muestreo de 1.694 fusiones. | Datos | 4 |
| R-05 | Documento de identidad inválido o repetido cargado. | 2 | 4 | 8 | Validación por tipo, rechazo de repetidos y 2.065 casos con revisión. | Cumplimiento | 4 |
| R-06 | Cuenta en estado desconocido operando sin decisión. | 3 | 4 | 12 | Carga informativa, cola de decisión y bloqueo operativo (RF-010). | Operaciones | 6 |
| R-07 | Movimientos con signo invertido o duplicados. | 1 | 5 | 5 | Corrección de signos en v3 y deduplicación por clave; pruebas y conciliación. | Migración | 2 |
| R-08 | Delta incompleta o desactualizada al momento del corte. | 2 | 5 | 10 | Doble extracción, suma de control y validación contra resumen. | Datos | 4 |
| R-09 | Falla de canales o batch en la apertura. | 2 | 5 | 10 | Smoke tests, monitoreo, plan de reversa y conmutación. | Operaciones y TI | 5 |
| R-10 | Respaldo del legado no restaurable. | 1 | 5 | 5 | Simulacro de restauración y verificación de hash. | TI | 2 |
| R-11 | Exposición de datos personales en muestras o tablero. | 1 | 5 | 5 | Enmascaramiento determinista, control de tarjetas y pruebas de seguridad (ADR-010). | Seguridad | 2 |
| R-12 | Ajustes contables sin evidencia suficiente. | 1 | 5 | 5 | Evidencia recalculable, tolerancia configurada y aprobación del comité. | Contabilidad | 3 |
| R-13 | Dependencia de una persona clave durante el corte. | 3 | 3 | 9 | Roles de relevo, runbook y traspaso técnico. | Programa | 4 |
| R-14 | Resistencia de usuarios y errores de operación. | 3 | 3 | 9 | Capacitación por rol, guías y mentor en piso. | Gestión del cambio | 4 |
| R-15 | Incumplimiento del RTO/RPO ante una falla crítica. | 2 | 5 | 10 | Reversa probada, respaldo a las 19:45 y canales en consulta desde las 19:30. | TI | 4 |

## Controles clave

| Control | Tipo | Evidencia | Frecuencia |
|---|---|---|---|
| Conteos origen = cargados + fusionados + rechazados | Preventivo/detectivo | `conciliacion_ensayo_v3.json` | Cada corrida y cada corte |
| Conciliación de saldos y movimientos | Detectivo | JSON y CSV de conciliación | Cada corrida |
| Recálculo del libro mayor | Detectivo | `conciliacion_ensayo_v3_desfases.csv` | Cada corrida |
| Contratos de destino | Preventivo | `config/contratos/*.json` y bitácora | Cada carga |
| Pruebas automatizadas | Detectivo | `datos/resultados/junit.xml` | Cada cambio |
| Enmascaramiento | Preventivo | Pruebas PR-006 y PR-016/PR-017 | Cada publicación |
| Reversa y respaldo | Correctivo | Runbook y simulacro | Antes del corte |

## Riesgos aceptados

- La verdad de terreno es sintética y no reemplaza una extracción real: se acepta para
  el alcance de portafolio y se declara en pruebas y conciliación.
- No se ejecuta UAT con usuarios reales ni prueba de volumen ampliado; el riesgo se
  mitiga con el simulacro de ventana y el monitoreo de hypercare.
- La regularización de los 927 clientes no migrados y los 540 préstamos incongruentes
  queda fuera del corte, con dueño y seguimiento posterior.

## Seguimiento

El comité operativo revisa los riesgos altos cada semana y el comité directivo los
críticos en cada sesión. Un riesgo crítico sin control implementado bloquea el
go/no-go. Después del corte, el war room actualiza la matriz a diario durante los
primeros diez días.

## Referencias

- [Runbook de corte](../09-corte-y-reversa/runbook-de-corte.md)
- [Informe de conciliación](../07-conciliacion/informe-de-conciliacion.md)
- [ADR-012: ajustes de migración](../decisiones/ADR-012-ajustes-de-migracion.md)
- [Requisitos](https://github.com/Vaxilium/banca-migracion-core-bancario/blob/main/config/requisitos/requisitos.yaml)
