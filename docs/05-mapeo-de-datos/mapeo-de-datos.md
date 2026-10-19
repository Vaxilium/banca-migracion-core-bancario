# Mapeo de datos campo a campo

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

Documentar, campo a campo, cómo cada registro de la extracción del legado se
convierte en filas del [modelo destino](modelo-de-datos.md). El mapeo vive en
`config/mapeos/*.csv` y estas tablas se generan desde esos archivos: el documento y
la configuración que ejecuta el pipeline no pueden divergir.

## Convenciones del mapeo

| Columna | Significado |
|---|---|
| `carga` | `S` la columna se carga al destino; `N` se usa solo para control (por ejemplo, el documento del maestro de clientes que se cruza contra documentos.dat). |
| `obligatorio` | `S` el pipeline no puede cargar la fila sin ese campo; `N` admite nulo. |
| `transformacion` | `directo` copia sin cambios; las demás aplican una regla `RN-xx` con nombre. |
| `derivado` | El campo no existe en el origen: lo calcula el pipeline (identificadores sustitutos, banderas de vigencia, extracción de texto libre). |

## Cobertura del mapeo

<!-- INICIO AUTO: cobertura-mapeo -->
| Archivo origen | Campos | Carga directa | Con regla | Derivados | Solo control |
|---|---:|---:|---:|---:|---:|
| `clientes.dat` | 12 | 2 | 7 | 1 | 2 |
| `cuentas.dat` | 13 | 4 | 7 | 2 | 0 |
| `cuotas.dat` | 8 | 2 | 6 | 0 | 0 |
| `direcciones.dat` | 11 | 7 | 3 | 1 | 0 |
| `documentos.dat` | 10 | 2 | 5 | 3 | 0 |
| `mandatos.dat` | 9 | 3 | 6 | 0 | 0 |
| `movimientos.dat` | 11 | 4 | 7 | 0 | 0 |
| `plan_cuentas.dat` | 6 | 4 | 2 | 0 | 0 |
| `plazos_fijos.dat` | 11 | 5 | 6 | 0 | 0 |
| `prestamos.dat` | 14 | 7 | 7 | 0 | 0 |
| `saldos.dat` | 5 | 2 | 3 | 0 | 0 |
| `saldos_contables.dat` | 5 | 1 | 4 | 0 | 0 |

Se mapearon 115 campos de origen hacia 12 tablas del destino.
<!-- FIN AUTO: cobertura-mapeo -->

## Detalle campo a campo

<!-- INICIO AUTO: detalle-mapeo -->
| Archivo origen | Campo origen | Campo destino | Tipo | Carga | Transformación | Regla |
|---|---|---|---|:-:|---|---|
| `clientes.dat` | correo | `cliente.correo` | texto | S | normalizar_correo | RN-07 |
| `clientes.dat` | estado_cliente | `cliente.estado` | texto | S | mapear_estado_cliente | RN-08 |
| `clientes.dat` | fecha_alta | `cliente.fecha_alta` | fecha | S | fecha_aammdd | RN-03 |
| `clientes.dat` | fecha_nacimiento | `cliente.fecha_nacimiento` | fecha | S | fecha_aammdd | RN-03 |
| `clientes.dat` | id_cliente | `cliente.id_cliente` | entero | S | directo | RN-00 |
| `clientes.dat` | nombre_completo | `cliente.nombre_completo` | texto | S | normalizar_texto | RN-01 |
| `clientes.dat` | — (derivado) | `cliente.nombre_normalizado` | texto | S | derivado | RN-02 |
| `clientes.dat` | observaciones | `cliente.observacion` | texto | S | normalizar_texto | RN-01 |
| `clientes.dat` | sexo | `cliente.sexo` | texto | S | directo | — |
| `clientes.dat` | telefono | `cliente.telefono` | texto | S | normalizar_telefono | RN-06 |
| `clientes.dat` | numero_documento | `documento_cliente.numero_documento` | texto | N | validar_documento | RN-04 |
| `clientes.dat` | tipo_documento | `documento_cliente.tipo_documento` | texto | N | mapear_tipo_documento | RN-05 |
| `cuentas.dat` | codigo_producto | `cuenta.codigo_producto` | texto | S | mapear_producto | RN-10 |
| `cuentas.dat` | codigo_sucursal | `cuenta.codigo_sucursal` | entero | S | directo | — |
| `cuentas.dat` | — (derivado) | `cuenta.documento_pendiente` | booleano | S | derivado | RN-12 |
| `cuentas.dat` | estado_cuenta | `cuenta.estado` | texto | S | mapear_estado_cuenta | RN-09 |
| `cuentas.dat` | fecha_apertura | `cuenta.fecha_apertura` | fecha | S | fecha_aammdd | RN-03 |
| `cuentas.dat` | fecha_ultimo_movimiento | `cuenta.fecha_ultimo_movimiento` | fecha | S | fecha_aammdd | RN-03 |
| `cuentas.dat` | id_cliente | `cuenta.id_cliente` | entero | S | directo | — |
| `cuentas.dat` | id_cuenta | `cuenta.id_cuenta` | entero | S | directo | RN-00 |
| `cuentas.dat` | moneda | `cuenta.moneda` | texto | S | directo | — |
| `cuentas.dat` | numero_tarjeta | `cuenta.numero_tarjeta_enmascarado` | texto | S | enmascarar_tarjeta | RN-11 |
| `cuentas.dat` | observaciones | `cuenta.observacion` | texto | S | normalizar_texto | RN-01 |
| `cuentas.dat` | — (derivado) | `cuenta.telefono_alternativo` | texto | S | derivado | RN-12 |
| `cuentas.dat` | indicador_tarjeta | `cuenta.tiene_tarjeta` | booleano | S | mapear_booleano | RN-25 |
| `cuotas.dat` | capital | `cuota_prestamo.capital` | importe | S | importe_signo_final | RN-17 |
| `cuotas.dat` | estado_cuota | `cuota_prestamo.estado` | texto | S | mapear_estado_cuota | RN-14 |
| `cuotas.dat` | fecha_pago | `cuota_prestamo.fecha_pago` | fecha | S | fecha_aammdd_opcional | RN-03 |
| `cuotas.dat` | fecha_vencimiento | `cuota_prestamo.fecha_vencimiento` | fecha | S | fecha_aammdd | RN-03 |
| `cuotas.dat` | id_prestamo | `cuota_prestamo.id_prestamo` | entero | S | directo | — |
| `cuotas.dat` | interes | `cuota_prestamo.interes` | importe | S | importe_signo_final | RN-17 |
| `cuotas.dat` | numero_cuota | `cuota_prestamo.numero_cuota` | entero | S | directo | — |
| `cuotas.dat` | total | `cuota_prestamo.total` | importe | S | importe_signo_final | RN-17 |
| `direcciones.dat` | calle | `domicilio_cliente.calle` | texto | S | normalizar_texto | RN-01 |
| `direcciones.dat` | codigo_postal | `domicilio_cliente.codigo_postal` | texto | S | directo | — |
| `direcciones.dat` | departamento | `domicilio_cliente.departamento` | texto | S | directo | — |
| `direcciones.dat` | id_cliente | `domicilio_cliente.id_cliente` | entero | S | directo | — |
| `direcciones.dat` | — (derivado) | `domicilio_cliente.id_domicilio` | entero | S | derivado | RN-26 |
| `direcciones.dat` | localidad | `domicilio_cliente.localidad` | texto | S | normalizar_texto | RN-01 |
| `direcciones.dat` | numero | `domicilio_cliente.numero` | entero | S | directo | — |
| `direcciones.dat` | pais | `domicilio_cliente.pais` | texto | S | directo | — |
| `direcciones.dat` | piso | `domicilio_cliente.piso` | texto | S | directo | — |
| `direcciones.dat` | provincia | `domicilio_cliente.provincia` | texto | S | directo | — |
| `direcciones.dat` | tipo_direccion | `domicilio_cliente.tipo` | texto | S | mapear_tipo_direccion | RN-29 |
| `documentos.dat` | — (derivado) | `documento_cliente.en_revision` | booleano | S | derivado | RN-25 |
| `documentos.dat` | fecha_emision | `documento_cliente.fecha_emision` | fecha | S | fecha_aammdd | RN-03 |
| `documentos.dat` | fecha_vencimiento | `documento_cliente.fecha_vencimiento` | fecha | S | fecha_aammdd | RN-03 |
| `documentos.dat` | id_cliente | `documento_cliente.id_cliente` | entero | S | directo | — |
| `documentos.dat` | — (derivado) | `documento_cliente.id_documento` | entero | S | derivado | RN-26 |
| `documentos.dat` | numero_documento | `documento_cliente.numero_documento` | texto | S | validar_documento | RN-04 |
| `documentos.dat` | pais | `documento_cliente.pais` | texto | S | directo | — |
| `documentos.dat` | tipo_documento | `documento_cliente.tipo_documento` | texto | S | mapear_tipo_documento | RN-05 |
| `documentos.dat` | validado | `documento_cliente.validado` | booleano | S | mapear_booleano | RN-25 |
| `documentos.dat` | — (derivado) | `documento_cliente.vigente` | booleano | S | derivado | RN-25 |
| `mandatos.dat` | codigo_servicio | `mandato_debito.codigo_servicio` | texto | S | mapear_servicio | RN-28 |
| `mandatos.dat` | estado_mandato | `mandato_debito.estado` | texto | S | mapear_estado_mandato | RN-16 |
| `mandatos.dat` | fecha_alta | `mandato_debito.fecha_alta` | fecha | S | fecha_aammdd | RN-03 |
| `mandatos.dat` | frecuencia | `mandato_debito.frecuencia` | texto | S | mapear_frecuencia | RN-27 |
| `mandatos.dat` | id_cliente | `mandato_debito.id_cliente` | entero | S | directo | — |
| `mandatos.dat` | id_cuenta_debito | `mandato_debito.id_cuenta_debito` | entero | S | directo | — |
| `mandatos.dat` | id_mandato | `mandato_debito.id_mandato` | entero | S | directo | RN-00 |
| `mandatos.dat` | importe_maximo | `mandato_debito.importe_maximo` | importe | S | importe_signo_final | RN-17 |
| `mandatos.dat` | referencia_servicio | `mandato_debito.referencia_servicio` | texto | S | normalizar_texto | RN-01 |
| `movimientos.dat` | canal | `movimiento.canal` | texto | S | mapear_canal | RN-19 |
| `movimientos.dat` | codigo_operacion | `movimiento.codigo_operacion` | texto | S | mapear_codigo_operacion | RN-20 |
| `movimientos.dat` | sucursal | `movimiento.codigo_sucursal` | entero | S | directo | — |
| `movimientos.dat` | descripcion | `movimiento.descripcion` | texto | S | normalizar_texto | RN-01 |
| `movimientos.dat` | fecha_movimiento | `movimiento.fecha` | fecha | S | fecha_aammdd | RN-03 |
| `movimientos.dat` | hora_movimiento | `movimiento.hora` | hora | S | fecha_hora | RN-22 |
| `movimientos.dat` | id_cuenta | `movimiento.id_cuenta` | entero | S | directo | — |
| `movimientos.dat` | id_movimiento | `movimiento.id_movimiento` | entero | S | directo | RN-00 |
| `movimientos.dat` | importe | `movimiento.importe` | importe | S | importe_signo_final | RN-17 |
| `movimientos.dat` | numero_comprobante | `movimiento.numero_comprobante` | entero | S | directo | — |
| `movimientos.dat` | saldo_despues | `movimiento.saldo_despues` | importe | S | importe_signo_final | RN-17 |
| `plan_cuentas.dat` | codigo_contable | `cuenta_contable.codigo_contable` | texto | S | directo | RN-00 |
| `plan_cuentas.dat` | cuenta_padre | `cuenta_contable.cuenta_padre` | texto | S | directo | — |
| `plan_cuentas.dat` | moneda | `cuenta_contable.moneda` | texto | S | directo | — |
| `plan_cuentas.dat` | nivel | `cuenta_contable.nivel` | entero | S | directo | — |
| `plan_cuentas.dat` | nombre_cuenta | `cuenta_contable.nombre_cuenta` | texto | S | normalizar_texto | RN-01 |
| `plan_cuentas.dat` | tipo_cuenta | `cuenta_contable.tipo_cuenta` | texto | S | mapear_tipo_cuenta | RN-30 |
| `plazos_fijos.dat` | codigo_producto | `plazo_fijo.codigo_producto` | texto | S | mapear_producto | RN-10 |
| `plazos_fijos.dat` | estado_plazo | `plazo_fijo.estado` | texto | S | mapear_estado_plazo | RN-15 |
| `plazos_fijos.dat` | fecha_constitucion | `plazo_fijo.fecha_constitucion` | fecha | S | fecha_aammdd | RN-03 |
| `plazos_fijos.dat` | fecha_vencimiento | `plazo_fijo.fecha_vencimiento` | fecha | S | fecha_aammdd | RN-03 |
| `plazos_fijos.dat` | id_cliente | `plazo_fijo.id_cliente` | entero | S | directo | — |
| `plazos_fijos.dat` | id_cuenta_acredita | `plazo_fijo.id_cuenta_acredita` | entero | S | directo | — |
| `plazos_fijos.dat` | id_plazo | `plazo_fijo.id_plazo` | entero | S | directo | RN-00 |
| `plazos_fijos.dat` | moneda | `plazo_fijo.moneda` | texto | S | directo | — |
| `plazos_fijos.dat` | monto_capital | `plazo_fijo.monto_capital` | importe | S | importe_signo_final | RN-17 |
| `plazos_fijos.dat` | plazo_dias | `plazo_fijo.plazo_dias` | entero | S | directo | — |
| `plazos_fijos.dat` | tasa_anual | `plazo_fijo.tasa_anual` | porcentaje | S | importe_signo_final | RN-17 |
| `prestamos.dat` | cantidad_cuotas | `prestamo.cantidad_cuotas` | entero | S | directo | — |
| `prestamos.dat` | codigo_producto | `prestamo.codigo_producto` | texto | S | mapear_producto | RN-10 |
| `prestamos.dat` | cuota_actual | `prestamo.cuota_actual` | entero | S | directo | — |
| `prestamos.dat` | estado_prestamo | `prestamo.estado` | texto | S | mapear_estado_prestamo | RN-13 |
| `prestamos.dat` | fecha_otorgamiento | `prestamo.fecha_otorgamiento` | fecha | S | fecha_aammdd | RN-03 |
| `prestamos.dat` | fecha_ultimo_pago | `prestamo.fecha_ultimo_pago` | fecha | S | fecha_aammdd | RN-03 |
| `prestamos.dat` | id_cliente | `prestamo.id_cliente` | entero | S | directo | — |
| `prestamos.dat` | id_cuenta_debito | `prestamo.id_cuenta_debito` | entero | S | directo | — |
| `prestamos.dat` | id_prestamo | `prestamo.id_prestamo` | entero | S | directo | RN-00 |
| `prestamos.dat` | moneda | `prestamo.moneda` | texto | S | directo | — |
| `prestamos.dat` | monto_original | `prestamo.monto_original` | importe | S | importe_signo_final | RN-17 |
| `prestamos.dat` | plazo_meses | `prestamo.plazo_meses` | entero | S | directo | — |
| `prestamos.dat` | saldo_capital | `prestamo.saldo_capital` | importe | S | importe_signo_final | RN-17 |
| `prestamos.dat` | tasa_anual | `prestamo.tasa_anual` | porcentaje | S | importe_signo_final | RN-17 |
| `saldos.dat` | fecha_saldo | `saldo_cuenta.fecha_saldo` | fecha | S | fecha_aammdd | RN-03 |
| `saldos.dat` | id_cuenta | `saldo_cuenta.id_cuenta` | entero | S | directo | — |
| `saldos.dat` | moneda | `saldo_cuenta.moneda` | texto | S | directo | — |
| `saldos.dat` | saldo_apertura | `saldo_cuenta.saldo_apertura` | importe | S | importe_signo_final | RN-17 |
| `saldos.dat` | saldo_final | `saldo_cuenta.saldo_final` | importe | S | importe_signo_final | RN-17 |
| `saldos_contables.dat` | codigo_contable | `saldo_contable.codigo_contable` | texto | S | directo | — |
| `saldos_contables.dat` | periodo | `saldo_contable.periodo` | fecha | S | fecha_aammdd | RN-03 |
| `saldos_contables.dat` | saldo_debe | `saldo_contable.saldo_debe` | importe | S | importe_signo_final | RN-17 |
| `saldos_contables.dat` | saldo_final | `saldo_contable.saldo_final` | importe | S | importe_signo_final | RN-17 |
| `saldos_contables.dat` | saldo_haber | `saldo_contable.saldo_haber` | importe | S | importe_signo_final | RN-17 |
<!-- FIN AUTO: detalle-mapeo -->

## Tratamiento de casos especiales

- **Códigos de producto sin equivalente:** el destino no adivina. `TR` y `PH` se
  rechazan por diseño; `XX` va a revisión (ver [ADR-005](../decisiones/ADR-005-productos-sin-equivalente.md)).
- **Duplicados de cliente:** la deduplicación usa nombre normalizado más documento
  (ver [ADR-009](../decisiones/ADR-009-deduplicacion-clientes.md)); el registro
  fusionado deja rastro en la bitácora.
- **Fechas:** toda fecha pasa por la conversión AAMMDD con umbral de siglo 30 y su
  validación contextual (ver [ADR-008](../decisiones/ADR-008-umbral-de-siglo.md)).
- **Signos:** los importes conservan el signo del campo; las inconsistencias
  detectadas se corrigen solo en las reglas v3 y quedan contadas en la bitácora.
- **Numero de tarjeta:** se persiste enmascarado (`**** **** **** 1234`).
