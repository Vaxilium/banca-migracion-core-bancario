# Reglas de transformación y calidad

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

Definir las reglas de transformación y calidad que aplica el pipeline, y explicar
por qué existen **tres versiones** de reglas: la migración se ensaya tres veces y la
mejora entre ensayos es parte del trabajo demostrado. Los parámetros viven en
`config/reglas/reglas_v1.yaml`, `reglas_v2.yaml` y `reglas_v3.yaml`, y las reglas de
calidad en `config/reglas/calidad.yaml`.

## Las tres versiones de reglas

1. **Ensayo 1 (línea base).** Primera versión, orientada a validar el flujo de punta
   a punta. Contiene defectos deliberados y documentados: umbral de siglo 25 (rompe
   las fechas de 2026), productos `CJ` y `CI` sin mapeo, `TR` y `XX` ingresando al
   destino sin derecho, sin deduplicación y sin corrección de signos.
2. **Ensayo 2 (alcance y fechas).** Corrige el umbral a 30 con validación contextual
   ([ADR-008](../decisiones/ADR-008-umbral-de-siglo.md)), agrega la deduplicación de
   clientes ([ADR-009](../decisiones/ADR-009-deduplicacion-clientes.md)) y ordena
   los mapeos de producto según [ADR-005](../decisiones/ADR-005-productos-sin-equivalente.md).
3. **Ensayo 3 (datos finos, versión final).** Corrige el signo de las comisiones
   invertidas en origen, migra `CI` como cuenta corriente internacional, extrae
   teléfono y alertas del texto libre de observaciones y aplica ajustes contables con
   evidencia ([ADR-012](../decisiones/ADR-012-ajustes-de-migracion.md)).

Los defectos del ensayo 1 no se corrigen "en su lugar": quedan en su archivo para que
la comparación entre ensayos sea auditable.

## Comparación de parámetros

<!-- INICIO AUTO: matriz-reglas -->
| Parámetro | Ensayo 1 | Ensayo 2 | Ensayo 3 |
|---|---|---|---|
| `umbral_siglo` | 25 | 30 | 30 |
| `deduplicacion_clientes` | no | sí | sí |
| `validar_fechas_contextual` | no | sí | sí |
| `correccion_signos` | no | no | sí |
| `extraccion_texto_libre` | no | no | sí |
| `ajustes_contables` | no | no | sí |
| `tolerancia_conciliacion` | 0,01 | 0,01 | 0,01 |
| `ventana_meses` | 12 | 12 | 12 |
<!-- FIN AUTO: matriz-reglas -->

## Tratamiento por producto en cada ensayo

<!-- INICIO AUTO: mapeo-productos-version -->
| Producto | Ensayo 1 | Ensayo 2 | Ensayo 3 |
|---|---|---|---|
| `CA` | `CA` | `CA` | `CA` |
| `CC` | `CC` | `CC` | `CC` |
| `CI` | **rechazar** | **rechazar** | `CC` (internacional) |
| `CJ` | **rechazar** | `CA` (segmento juvenil) | `CA` (segmento juvenil) |
| `PE` | `PE` | `PE` | `PE` |
| `PF` | `PF` | `PF` | `PF` |
| `PH` | `PP` | **rechazar** | **rechazar** |
| `PP` | `PP` | `PP` | `PP` |
| `TR` | `CC` | **rechazar** | **rechazar** |
| `XX` | `CA` | **revisar** | **revisar** |
<!-- FIN AUTO: mapeo-productos-version -->

## Reglas de calidad

<!-- INICIO AUTO: reglas-calidad -->
| ID | Regla | Entidad | Tipo | Severidad | Acción |
|---|---|---|---|---|---|
| CAL-001 | Documento de identidad único por tipo | `documento_cliente` | unicidad | grave | revisar |
| CAL-002 | Formato de documento según tipo | `documento_cliente` | formato | grave | revisar |
| CAL-003 | Fecha válida y en rango razonable | `todas` | rango | bloqueante | rechazar |
| CAL-004 | Cuenta con cliente existente | `cuenta` | integridad referencial | grave | revisar |
| CAL-005 | Movimiento con cuenta existente | `movimiento` | integridad referencial | bloqueante | rechazar |
| CAL-006 | Movimiento dentro de la ventana de migración | `movimiento` | rango | bloqueante | rechazar |
| CAL-007 | Saldo de cuenta concilia con movimientos | `saldo_cuenta` | coherencia | grave | reportar |
| CAL-008 | Signo coherente con el código de operación | `movimiento` | coherencia | grave | corregir con regla |
| CAL-009 | Saldo de capital no supera el monto original | `prestamo` | rango | grave | revisar |
| CAL-010 | Total de cuota igual a capital más interés | `cuota_prestamo` | coherencia | grave | revisar |
| CAL-011 | Vencimiento de plazo coherente con plazo en días | `plazo_fijo` | coherencia | grave | revisar |
| CAL-012 | Mandato con cuenta de débito existente | `mandato_debito` | integridad referencial | grave | revisar |
| CAL-013 | Saldo contable cuadra con debe menos haber | `saldo_contable` | coherencia | bloqueante | reportar |
| CAL-014 | Número de tarjeta enmascarado | `cuenta` | seguridad | bloqueante | rechazar |
| CAL-015 | Estado dentro del dominio del catálogo | `todas` | dominio | grave | revisar |

15 reglas de calidad: 5 bloqueantes, 10 graves. Las bloqueantes rechazan la fila; las graves la envían a revisión.
<!-- FIN AUTO: reglas-calidad -->

## Resultados por ensayo

Cada ensayo produce sus propias cifras de filas cargadas, rechazadas y enviadas a
revisión. La comparación de ensayos, la conciliación por ensayo y la medición de
detección contra la verdad de terreno se publican en el
[pipeline de migración](../06-pipeline/pipeline-de-migracion.md) y en el
[informe de conciliación](../07-conciliacion/informe-de-conciliacion.md).
