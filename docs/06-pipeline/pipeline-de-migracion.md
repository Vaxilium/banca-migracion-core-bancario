# Pipeline de migración

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

Describir cómo la extracción del legado se convierte en las tablas del
[modelo destino](../05-mapeo-de-datos/modelo-de-datos.md) mediante tres ensayos
sucesivos y una carga delta del corte. El pipeline es reproducible con semilla fija:
cualquier cifra de este documento se regenera con `make todo`.

## Arquitectura

| Etapa | Módulo | Qué hace |
|---|---|---|
| Extracción | `src/migracion/extraccion.py` | Lee los archivos de ancho fijo guiándose por `config/disenos_legado/*.yaml`; separa registros con longitud incorrecta (`registro_corrupto`). |
| Reglas | `src/migracion/reglas.py` | Conversiones vectorizadas: fechas AAMMDD con umbral de siglo, importes con signo final, horas, enteros, catálogos y validación de documentos. |
| Transformación | `src/migracion/transformacion.py` | Aplica las reglas de cada ensayo, deduplica clientes, repara siglos con contexto, corrige signos y resuelve integridad referencial. |
| Contratos | `src/migracion/contratos.py` | Genera un JSON Schema por tabla destino desde `config/mapeos/modelo_destino.yaml` y valida una muestra de 200 filas antes de publicar. |
| Carga | `src/migracion/carga.py` | Escribe Parquet por tabla con DuckDB y aplica la delta del corte con semántica de upsert (ANTI/SEMI JOIN). |
| Orquestación | `src/migracion/pipeline.py` | Ejecuta un ensayo o los tres, escribe rechazos, bitácora y resumen JSON por corrida. |

## Ensayos sucesivos

Cada ensayo usa el mismo legado: solo cambian los parámetros de
`config/reglas/reglas_v1.yaml`, `reglas_v2.yaml` y `reglas_v3.yaml`. Así se mide el
efecto de cada decisión sin comparar corridas sobre datos distintos.

<!-- INICIO AUTO: pipeline-ensayos -->
| Parametro | Ensayo 1 | Ensayo 2 | Ensayo 3 |
|---|---|---|---|
| Umbral de siglo | 25 | 30 | 30 |
| Deduplicacion de clientes | no | si | si |
| Validacion contextual de fechas | no | si | si |
| Correccion de signos | no | no | si |
| Extraccion de texto libre | no | no | si |
| Ajustes contables | no | no | si |
|  |  |  |  |
| Filas cargadas en el destino | 1.538.579 | 1.451.632 | 1.476.247 |
| Duracion (segundos) | 51,5 | 68,5 | 70,4 |
| Clientes | 60.873 | 59.179 | 59.179 |
| Movimientos | 810.366 | 755.530 | 774.877 |
| Cuentas | 78.153 | 73.990 | 76.419 |

Los ensayos son acumulativos: el 1 deja los defectos documentados, el 2 activa deduplicacion y validacion contextual, y el 3 corrige signos, extrae texto libre y aplica ajustes contables respaldados.
<!-- FIN AUTO: pipeline-ensayos -->

## Salidas de una corrida

| Salida | Ubicación | Contenido |
|---|---|---|
| Tablas destino | `datos/destino/ensayo_v{n}/*.parquet` | Una tabla del modelo por archivo, con contratos validados. |
| Rechazos | `datos/resultados/rechazos_ensayo_v{n}.csv` | Fila a fila: entidad, motivo, clave, detalle y destino (`rechazo` o `revision`). |
| Bitácora | `datos/bitacora/bitacora_ensayo_v{n}.csv` | Decisiones aplicadas: fusiones, reparaciones de siglo, correcciones de signo, marcas de producto y extracción de texto libre. |
| Resumen | `datos/resultados/resumen_ensayo_v{n}.json` | Parámetros, motivos por entidad, tablas cargadas, contratos y duración. |
| Delta | `datos/resultados/rechazos_delta_v3.csv` | Rechazos de la carga del corte; el resumen suma la sección `delta`. |

Un **rechazo** impide cargar la fila; una **revisión** deja el caso registrado para
tratamiento manual (por ejemplo, un cliente con documento inválido migra, pero su
documento no). Los motivos son un vocabulario cerrado y se cuentan una vez por fila
y motivo: una misma fila puede aparecer en más de un motivo cuando acumula defectos.

## Reglas de transformación aplicadas

1. **Deduplicación de clientes** en dos pasadas (nombre normalizado + nacimiento y
   documento + nacimiento), conservando el `id_cliente` menor y reapuntando hijos
   ([ADR-009](../decisiones/ADR-009-deduplicacion-clientes.md)).
2. **Reparación de siglo con contexto**: si una fecha queda antes de su referencia
   (vencimiento antes de emisión, último movimiento antes de apertura), se
   reinterpreta sumando 100 años y se anota `siglo_reinterpretado`
   ([ADR-008](../decisiones/ADR-008-umbral-de-siglo.md)).
3. **Corrección de signos** (ensayo 3): toda operación de débito con importe positivo
   se invierte y se registra `correccion_signo`.
4. **Texto libre de cuentas** (ensayo 3): `TEL xxx` alimenta el teléfono alternativo y
   `DOC PENDIENTE` activa la bandera de documento pendiente.
5. **Enmascaramiento**: el número de tarjeta del mandato se guarda enmascarado
   ([ADR-010](../decisiones/ADR-010-enmascaramiento-de-datos.md)).
6. **Integridad referencial**: documentos, cuentas, saldos, movimientos, cuotas,
   plazos y mandatos de un padre rechazado se rechazan en cascada con motivo
   `cliente_no_migrado`, `cuenta_no_migrada` o `prestamo_no_migrado`.

## Tablas cargadas en el ensayo 3

<!-- INICIO AUTO: pipeline-tablas -->
| Tabla destino | Filas cargadas |
|---|---:|
| `catalogo_canal` | 4 |
| `catalogo_codigo_operacion` | 9 |
| `catalogo_moneda` | 2 |
| `catalogo_producto` | 5 |
| `catalogo_servicio_mandato` | 4 |
| `catalogo_sucursal` | 350 |
| `catalogo_tipo_documento` | 3 |
| `cliente` | 59.179 |
| `cuenta` | 76.419 |
| `cuenta_contable` | 48 |
| `cuota_prestamo` | 302.616 |
| `documento_cliente` | 67.717 |
| `domicilio_cliente` | 74.541 |
| `mandato_debito` | 21.363 |
| `movimiento` | 774.877 |
| `plazo_fijo` | 6.977 |
| `prestamo` | 15.686 |
| `saldo_contable` | 28 |
| `saldo_cuenta` | 76.419 |
| **Total** | **1.476.247** |
<!-- FIN AUTO: pipeline-tablas -->

## Carga delta del corte

La delta representa la operatoria entre la extracción y el corte (24/10/2026):
cuentas nuevas, movimientos nuevos y saldos actualizados. Se transforma con el mismo
contexto del ensayo 3 y se incorpora a las tablas publicadas:

- altas: se agregan si la clave no existe;
- actualizaciones: reemplazan la fila vigente por clave (saldos).

<!-- INICIO AUTO: pipeline-delta -->
| Tabla | Actualizadas | Insertadas |
|---|---:|---:|
| `cuenta` | 0 | 117 |
| `saldo_cuenta` | 4.902 | 117 |
| `movimiento` | 0 | 10.832 |

La ventana del corte (2026-10-09 a 2026-10-24) aporto 654 registros rechazados: `cuenta_no_migrada` 651, `cuenta_huerfana` 3. Son movimientos y saldos de cuentas que no migraron, por lo que la delta hereda el rechazo explicado.
<!-- FIN AUTO: pipeline-delta -->

## Verificación contra la verdad de terreno

El generador de datos deja registrada cada inyección de defectos en
`datos/verdad/defectos_inyectados.csv`. El pipeline no lee ese archivo: la
verificación es un control posterior que cruza ambos resultados.

<!-- INICIO AUTO: pipeline-verificacion -->
| Defecto inyectado | Casos | Detectados | Faltantes |
|---|---:|---:|---:|
| Clientes duplicados (fusionados) | 1.800 | 1.694 | 106 |
| Documentos invalidos de clientes | 1.236 | 1.209 | 27 |
| Documentos repetidos entre clientes | 309 | 295 | 14 |
| Fechas de nacimiento imposibles | 927 | 927 | 0 |
| Documentos vencidos sin marcar | 2.731 | 2.666 | 65 |
| Direcciones incompletas | 4.477 | 4.399 | 78 |
| Cuentas huerfanas | 1.801 | 1.801 | 0 |
| Cuentas con estado desconocido | 3.602 | 3.602 | 0 |
| Cuentas de producto fuera de alcance | 4.866 | 4.866 | 0 |
| Cuentas de producto desconocido | 3.194 | 3.194 | 0 |
| Movimientos con signo invertido | 3.068 | 2.589 | 479 |
| Movimientos con fecha imposible | 10.903 | 9.318 | 1.585 |
| Movimientos duplicados por reproceso | 18.172 | 15.218 | 2.954 |
| Prestamos con saldo incongruente | 540 | 458 | 82 |
| Plazos con vencimiento incongruente | 160 | 134 | 26 |
| Mandatos con cuenta inexistente | 500 | 500 | 0 |

Los faltantes son filas rechazadas antes de la deteccion especifica por otro defecto en la misma fila o por una cascada de integridad referencial (por ejemplo, movimientos de cuentas que no migraron); cada caso queda registrado en los rechazos con su motivo. Las detecciones pueden superar los casos inyectados cuando el defecto afecta a mas de una fila (por ejemplo, un documento compartido queda marcado en ambos clientes).
<!-- FIN AUTO: pipeline-verificacion -->

## Reproducción

```bash
make datos          # genera el legado sintético completo y su verdad de terreno
make migracion      # ejecuta los tres ensayos y la delta del corte
.venv/bin/python -m src.informes.pipeline   # actualiza este documento
```

Los datos grandes no se versionan: el repositorio publica las muestras de
`muestras/` y las cifras agregadas de los documentos.
