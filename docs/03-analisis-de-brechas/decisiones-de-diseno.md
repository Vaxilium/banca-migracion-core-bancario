# Decisiones de diseño funcional

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

Registrar las decisiones de diseño funcional que resuelven las brechas y que luego
se materializan como reglas de transformación versionadas (fase 6) y decisiones de
conciliación (fase 7).

## Alcance

Decisiones sobre datos de clientes, cuentas, productos y contabilidad.

## Registro de decisiones

| ID | Tema | Decisión | Justificación | ADR/regla |
|---|---|---|---|---|
| DD-01 | Clientes duplicados | Superviviente: el de mayor antigüedad de alta; empate por mayor completitud de datos. | Preserva la antigüedad comercial y el historial más rico. | [ADR-009](../decisiones/ADR-009-deduplicacion-clientes.md) |
| DD-02 | Estados de cuenta desconocidos (X) | No se cargan como activas: pasan a cola de revisión manual con decisión obligatoria. | Un estado inválido no debe propagarse al core nuevo. | Regla `estado_desconocido` |
| DD-03 | Productos fuera de alcance (TR, PH, PX) | Rechazo con motivo `fuera_de_alcance` y notificación a satélites. | Evita contaminar el destino con rubros no migrados. | [ADR-005](../decisiones/ADR-005-productos-sin-equivalente.md) |
| DD-04 | Libretas físicas | Se descontinúan a partir del corte; extractos digitales desde el primer día. | Alineado con canales digitales; costo de impresión. | ADR-005 |
| DD-05 | Tipos de firma | Mapear a condiciones del destino; combinaciones sin equivalente pasan a revisión. | Simplifica el modelo sin perder control. | Regla `tipo_firma` |
| DD-06 | Mandatos suspendidos o de baja | Se migran como histórico de consulta, sin ejecutar débitos. | Solo los activos generan obligaciones. | Regla `mandato_estado` |
| DD-07 | Documentos inválidos | Rechazo con motivo `documento_invalido` y revisión manual antes del corte. | Cumplimiento y prevención de fraude. | Regla `documento` |
| DD-08 | Fechas imposibles | Rechazo con motivo `fecha_invalida`; no se corrigen silenciosamente. | Un cálculo silencioso oculta errores de origen. | Regla `fecha` |
| DD-09 | Signos invertidos en comisiones | Corrección automática con evidencia cuando la naturaleza del movimiento lo determina. | Evita descuadres contables; queda auditado. | Regla `signo_comision` (v3) |
| DD-10 | Descuadres de saldo | Dentro de tolerancia: regularización del saldo de apertura con ajuste evidenciado; fuera de tolerancia: revisión manual. | Mantiene la ecuación saldo = apertura + movimientos. | [ADR-012](../decisiones/ADR-012-ajustes-de-migracion.md) |
| DD-11 | Duplicados de movimientos por reproceso | Detección por clave cuenta + fecha + hora + importe + comprobante. | El job de red podía reprocesar un archivo completo. | Regla `movimiento_duplicado` (v2) |
| DD-12 | Texto libre sobrecargado en observaciones | Extraer teléfono y correo con patrones; conservar el texto original íntegro. | Recupera contactos sin perder información. | Regla `texto_libre` (v3) |
| DD-13 | Plazos fijos cancelados | Se migran como histórico sin cálculo de intereses futuros. | No generan obligaciones. | Regla `plazo_estado` |
| DD-14 | Cuentas cerradas (estado C) | Se migran solo como histórico sin saldo operativo. | No operan; requeridas para consultas. | Regla `cuenta_cerrada` |

## Criterios de aplicación

1. Toda decisión tiene una regla versionada que la implementa o una tarea manual
   asignada en el runbook.
2. Los rechazos asociados tienen motivo único y se agrupan por causa raíz en la
   conciliación.
3. Cambiar una decisión implica nueva versión de reglas y nuevo ensayo, nunca una
   corrección silenciosa sobre un ensayo ya reportado.

## Supuestos

- Las decisiones se validan con Contabilidad y Cumplimiento en el comité de datos.
- Los identificadores DD se citan desde la matriz de trazabilidad (fase 12).

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Regla de deduplicación agresiva que fusione clientes distintos | Doble condición (documento exacto o dos apellidos + nombre normalizado) y revisión por muestreo. |
| Ajustes de saldo sin respaldo | Evidencia obligatoria y aprobación de Contabilidad (ADR-012). |

## Glosario

Ver [glosario único](../glosario.md).
