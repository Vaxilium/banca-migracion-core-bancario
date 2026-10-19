# Catálogo de productos y parámetros (AS-IS)

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

Catalogar los productos del legado con sus códigos, parámetros y equivalencia
prevista en el core nuevo, como base del mapeo de datos (fase 5).

## Alcance

Productos del banco minorista incluidos y excluidos del alcance de la migración.

## Productos incluidos

| Código legado | Producto | Descripción | Moneda | Parámetros principales | Equivalencia destino |
|---|---|---|---|---|---|
| CA | Caja de ahorro | Cuenta de depósito a la vista de personas | Local | Tasa nominal anual 2 %, sin comisión de mantenimiento | `caja_ahorro` |
| CC | Cuenta corriente | Cuenta a la vista con descubierto | Local | Descubierto hasta 30 % del salario declarado; comisión mensual | `cuenta_corriente` |
| CJ | Caja juvenil | Caja de ahorro para menores de 18 años | Local | Sin costo; límite de extracción mensual | `caja_ahorro` (segmento juvenil) |
| CI | Cuenta corriente internacional | Cuenta corriente con moneda extranjera | Bimonetaria | Comisiones por transferencia internacional | `cuenta_corriente` (bandera internacional) |
| PF | Plazo fijo tradicional | Depósito a plazo con tasa fija | Local | Tasas nominales anuales 30 %–45 % según plazo; renovación automática opcional | `plazo_fijo` |
| PE | Plazo fijo especial | Plazo fijo con tasa promocional | Local | Tasa preferencial para clientes con haberes | `plazo_fijo` (tipo promocional) |
| PP | Préstamo personal | Crédito amortizable en cuotas fijas | Local | Tasa nominal anual; sistemas francés; seguros asociados | `prestamo_personal` |
| TD | Tarjeta de débito | Producto asociado a cuenta CA/CC | Local | Emisión, reposición y bloqueo | `tarjeta_debito` |

## Productos excluidos del alcance

| Código legado | Producto | Motivo de exclusión | Tratamiento |
|---|---|---|---|
| TR | Tarjeta de crédito | Motor de facturación sin equivalente directo; rubro aparte | Permanece en satélite; rechazo `fuera_de_alcance` si aparece en extracción |
| PH | Préstamo hipotecario | Gestión en sistema de créditos especializado | Permanece en satélite; rechazo `fuera_de_alcance` |
| PX | Plazo fijo en moneda extranjera | Tratamiento cambiario específico | Permanece en satélite; rechazo `fuera_de_alcance` |

## Parámetros de negocio transversales

| Parámetro | Valor AS-IS | Observación |
|---|---|---|
| Redondeo de importes | 2 decimales, redondeo a par (banker's rounding) | Se mantiene en el destino. |
| Días base para intereses | 365 días | Igual en préstamos y plazos. |
| Comisión de mantenimiento de cuenta corriente | Mensual, debitada por batch | Se migra como condición de producto. |
| Impuesto sobre débitos y créditos | 0,6 % sobre movimientos en cuenta corriente | Ilustrativo; aplicado por batch nocturno. |
| Ventana de extracción histórica | 12 meses de movimientos | Ver [ADR-007](../decisiones/ADR-007-ventana-historica.md). |

## Reglas de estado de productos

| Entidad | Estados legados | Migración |
|---|---|---|
| Cliente | A activo, I inactivo, B bloqueado, D fallecido | D queda fuera de migración automática (sucesión manual). |
| Cuenta | A activa, B bloqueada, C cerrada, D dormida, X desconocido | C no se migra como activa; X pasa a revisión manual. |
| Préstamo | VI vigente, MO en mora, CA cancelado, AT atrasado | Cancelados se migran solo como histórico. |
| Plazo fijo | V vigente, C cancelado, R renovado | Cancelados se migran como histórico. |

## Supuestos

- Tasas, comisiones e impuestos son valores ilustrativos y no citan normativa real.
- Las equivalencias se detallan campo a campo en la especificación de mapeo (fase 5).

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Parámetros desconocidos de productos raros | Perfilado de la extracción y tabla de equivalencias de códigos. |
| Productos excluidos que reaparezcan en canales | Comunicación a canales y rechazo controlado en el pipeline. |

## Glosario

Ver [glosario único](../glosario.md).
