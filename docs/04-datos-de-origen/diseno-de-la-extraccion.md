# Diseño de la extracción de datos de origen (sintéticos)

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

Definir el origen de los datos con los que trabaja el proyecto. El "sistema de
origen" es un **generador reproducible** que produce archivos equivalentes a la
extracción del core legado SICOB-2000, con defectos inyectados y registrados que
permiten medir con evidencia la calidad de los datos y la eficacia del pipeline.

## El sistema de origen simulado

El core legado descrito en el [inventario de sistemas](../02-analisis-as-is/inventario-de-sistemas.md)
(S-01, COBOL batch con archivos de ancho fijo) entrega una extracción mensual con
cortes de clientes, cuentas, saldos, movimientos, créditos y contabilidad. El
generador reproduce ese contrato de archivos:

- **Extracción base:** corte al 09/10/2026, con movimientos de los últimos 12 meses
  (ver [ADR-007](../decisiones/ADR-007-ventana-historica.md)).
- **Carga delta:** altas, movimientos y saldos del día de corte del 24/10/2026,
  previo al cierre de fin de semana elegido para la migración.
- **Formato:** registros de ancho fijo, codificación latin-1, importes con signo al
  final y dos decimales implícitos, fechas AAMMDD sin siglo
  (ver [ADR-008](../decisiones/ADR-008-umbral-de-siglo.md)).
- **Contrato de archivos:** cada archivo está definido en `config/disenos_legado/`
  (un YAML por entidad) y ese mismo contrato guía la escritura (fase 4) y el parseo
  (fase 6), de modo que origen y pipeline no puedan divergir.

## Archivos de la extracción

<!-- INICIO AUTO: archivos-legado -->
| Entidad | Archivo | Longitud (bytes) | Registros | Tamaño | Descripción |
|---|---|---:|---:|---:|---|
| Clientes | `clientes.dat` | 212 | 61.800 | 12,6 MB | Maestro de clientes del core legado (nombre sobrecargado, estado legado) |
| Documentos | `documentos.dat` | 60 | 69.000 | 4,0 MB | Documentos de identidad declarados por los clientes |
| Direcciones | `direcciones.dat` | 120 | 75.660 | 8,7 MB | Direcciones particulares y laborales de los clientes |
| Cuentas | `cuentas.dat` | 150 | 90.059 | 13,0 MB | Maestro de cuentas con observaciones de texto libre sobrecargado |
| Saldos | `saldos.dat` | 60 | 90.059 | 5,2 MB | Saldos de apertura y finales por cuenta (importes con signo final) |
| Movimientos | `movimientos.dat` | 90 | 926.794 | 80,4 MB | Movimientos historicos de los ultimos 12 meses (importe con signo final) |
| Prestamos | `prestamos.dat` | 140 | 18.000 | 2,4 MB | Prestamos personales (tasas con 2 decimales implicitos) |
| Cuotas | `cuotas.dat` | 80 | 347.316 | 26,8 MB | Cronogramas de cuotas de prestamos personales |
| Plazos fijos | `plazos_fijos.dat` | 110 | 8.000 | 0,8 MB | Depositos a plazo fijo y sus condiciones |
| Mandatos | `mandatos.dat` | 90 | 25.000 | 2,2 MB | Mandatos de debito automatico (servicios y cuotas) |
| Plan cuentas | `plan_cuentas.dat` | 90 | 48 | 0,0 MB | Plan de cuentas contable del legado (estructura jerarquica) |
| Saldos contables | `saldos_contables.dat` | 70 | 28 | 0,0 MB | Saldos del libro mayor por cuenta contable al cierre del periodo |
| **Total** |  |  | **1.711.764** |  |  |
<!-- FIN AUTO: archivos-legado -->

## Reproducibilidad y escalas

Todos los datos se generan con la semilla fija **20261019** en `src/comun/semilla.py`:
la misma versión del código produce siempre los mismos archivos. La generación se
ejecuta con `make datos` (escala completa) o `make reducido` (escala piloto), y
admite además una escala `humo` para pruebas rápidas del propio generador.

La escala completa es la que usan los ensayos de migración, la conciliación y el
tablero. Los archivos grandes no se versionan en el repositorio (viven en `datos/`,
ignorado por git); solo se publican muestras CSV de tamaño reducido en `muestras/`
para inspección directa.

La generación sigue las decisiones de [ADR-006](../decisiones/ADR-006-datos-sinteticos.md):
datos 100 % ficticios, enmascaramiento determinista de datos personales y banco sin
coincidencia con entidades reales.

## Inyección de defectos y verdad de terreno

Una extracción real nunca llega limpia: documentos vencidos sin marcar, cuentas
huérfanas, signos invertidos en comisiones, duplicados de reproceso, descuadres y
fechas imposibles. El generador inyecta una tasas controladas de estos defectos
(config/parametrico/defectos.yaml) y registra **cada caso** en
`datos/verdad/defectos_inyectados.csv` (entidad, tipo, clave y detalle).

Esa verdad de terreno es la que permite responder con evidencia preguntas como
"¿qué porcentaje de los descuadres reales detectó la conciliación?" en las fases de
perfilado (6) y conciliación (7): la detección se mide contra el registro, nunca a
partir de supuestos.

<!-- INICIO AUTO: volumen-verdad -->
| Entidad | Defecto inyectado | Casos | Registros de la entidad | Tasa observada |
|---|---|---:|---:|---:|
| clientes | `documento_invalido` | 1.236 | 61.800 | 2,00 % |
| clientes | `documento_repetido_otro_cliente` | 309 | 61.800 | 0,50 % |
| clientes | `duplicado_nombre_variante` | 1.800 | 61.800 | 2,91 % |
| clientes | `fecha_nacimiento_imposible` | 927 | 61.800 | 1,50 % |
| cuentas | `cuenta_huerfana` | 1.801 | 90.059 | 2,00 % |
| cuentas | `estado_desconocido` | 3.602 | 90.059 | 4,00 % |
| cuentas | `producto_desconocido` | 3.194 | 90.059 | 3,55 % |
| cuentas | `producto_fuera_alcance` | 4.866 | 90.059 | 5,40 % |
| direcciones | `direccion_incompleta` | 4.540 | 75.660 | 6,00 % |
| documentos | `vencido_sin_marcar` | 2.732 | 69.000 | 3,96 % |
| mandatos | `cuenta_inexistente` | 500 | 25.000 | 2,00 % |
| movimientos | `duplicado_reproceso` | 18.172 | 926.794 | 1,96 % |
| movimientos | `fecha_imposible` | 10.903 | 926.794 | 1,18 % |
| movimientos | `signo_invertido` | 3.068 | 926.794 | 0,33 % |
| plazos fijos | `vencimiento_incongruente` | 160 | 8.000 | 2,00 % |
| prestamos | `saldo_incongruente` | 540 | 18.000 | 3,00 % |
| saldos | `descuadre_grave` | 450 | 90.059 | 0,50 % |
| saldos | `descuadre_leve` | 1.801 | 90.059 | 2,00 % |
| saldos contables | `desfase_contable` | 8 | 28 | 28,57 % |
| **Total** |  | **60.609** | **1.711.764** | **3,54 %** |
<!-- FIN AUTO: volumen-verdad -->

## Carga delta del día de corte

Además de la extracción base, se genera la carga del **día de corte** con las
novedades posteriores: altas de cuentas, movimientos del día y saldos actualizados.
La carga delta se usa en el ensayo final de migración y en el procedimiento de corte
y reversa (fase 9):

- Las **cuentas nuevas** continúan la numeración del legado sin colisionar con las
  existentes.
- Los **movimientos del día** se encadenan con el saldo final de la extracción base.
- Los **saldos actualizados** llegan en modalidad *upsert*: la cuenta afectada se
  actualiza, no se duplica.

<!-- INICIO AUTO: carga-delta -->
| Archivo delta | Registros | Contenido |
|---|---:|---|
| `cuentas_delta.dat` | 120 | Altas de cuentas del día de corte. |
| `movimientos_delta.dat` | 11.282 | Movimientos del día (incluye el depósito de apertura de las altas). |
| `saldos_delta.dat` | 5.220 | Saldos actualizados de las cuentas afectadas. |

**Fechas del proceso:** extracción base del **09/10/2026**, carga delta del **24/10/2026**. Generación completa en 40,0 segundos.
<!-- FIN AUTO: carga-delta -->

## Uso en las etapas siguientes

| Etapa | Uso de los datos de origen |
|---|---|
| 6. Pipeline | Parseo guiado por los diseños, reglas de transformación, rechazos con motivo. |
| 7. Conciliación | Conteos y sumas de control por entidad y por cuenta contra la verdad registrada. |
| 8. Pruebas | Casos de prueba construidos sobre defectos conocidos y esperados. |
| 9. Corte | Ensayo final con la carga delta y reversa controlada. |
