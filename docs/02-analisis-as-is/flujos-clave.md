# Flujos clave AS-IS

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

Detallar tres flujos representativos del AS-IS (apertura de cuenta, cobro de cuota y
cierre diario) para identificar dependencias funcionales y puntos de dolor que la
migración debe preservar o mejorar.

## Alcance

Flujos de personas físicas en productos incluidos en el alcance.

## Flujo 1: apertura de caja de ahorro

```mermaid
flowchart TD
    A[Cliente en sucursal] --> B[Alta manual de datos en SICOB-2000]
    B --> C{Existe cliente?}
    C -->|No| D[Crear cliente y documentos]
    C -->|Si| E[Recuperar cliente existente]
    D --> F[Validar documento contra padron externo]
    E --> F
    F --> G{Aprobado?}
    G -->|No| H[Rechazo y derivacion a cumplimiento]
    G -->|Si| I[Alta de cuenta CA con tipo de firma]
    I --> J[Emitir tarjeta de debito en TARD-01]
    J --> K[Entrega de contrato y primera libreta]
    K --> L[Deposito inicial]
    L --> M[Cliente opera desde el dia siguiente]
```

| Paso | Sistema | Control | Dolor asociado |
|---|---|---|---|
| Alta de datos | SICOB-2000 | Duplicidad detectada por nombre exacto | PD-01 |
| Validación de documento | Padrón externo | Manual si el servicio no responde | PD-05 |
| Emisión de tarjeta | TARD-01 | Lote nocturno | PD-04 |
| Operación inicial | SICOB-2000 | Disponible al día siguiente | PD-02 |

## Flujo 2: cobro de cuota de préstamo personal

```mermaid
flowchart TD
    A[Job nocturno JOB-MOR04] --> B[Identificar cuotas del dia]
    B --> C{Cliente con mandato de debito?}
    C -->|Si| D[Generar debito en cuenta]
    C -->|No| E[Pago en ventanilla o caja]
    D --> F{Saldo suficiente?}
    F -->|Si| G[Imputar cuota y registrar movimiento]
    F -->|No| H[Marcar mora y reintentar al dia siguiente]
    E --> G
    G --> I[Intereses y actualizacion de saldo de capital]
    H --> J[Generar aviso al cliente por lote]
    I --> K[Asientos contables JOB-CTB01]
```

| Paso | Sistema | Regla | Dolor asociado |
|---|---|---|---|
| Identificación de cuotas | SICOB-2000 | Vencimiento = día del mes pactado | PD-03 |
| Débito automático | SICOB-2000 + SWT-Red | Reintento único nocturno | PD-03 |
| Imputación | SICOB-2000 | Orden: interés causado, capital | — |
| Notificación | CIERRE-RPT | Lote diario; el cliente avisa tarde | PD-06 |

## Flujo 3: cierre diario

```mermaid
flowchart TD
    A[21:00 corte de capturas] --> B[Validaciones de integridad]
    B --> C{Descuadres?}
    C -->|Si| D[Cola de investigacion manual]
    C -->|No| E[Intereses y comisiones]
    D --> F[Correccion y reproceso parcial]
    F --> E
    E --> G[Actualizacion de saldos]
    G --> H[Asientos CONT-GRAL]
    H --> I{Mayor cuadrado?}
    I -->|No| J[Investigacion contable al dia siguiente]
    I -->|Si| K[Reportes y extractos]
    K --> L[06:00 liberacion de operacion]
```

| Paso | Control | Evidencia | Dolor asociado |
|---|---|---|---|
| Validaciones de integridad | Conteos por archivo | Reporte de cierre | PD-07 |
| Investigación de descuadres | Manual, hoja de cálculo | Correo de Operaciones | PD-07 |
| Cuadre del mayor | Manual contra CONT-GRAL | Planilla mensual | PD-08 |

## Resumen de puntos de dolor referenciados

Los identificadores PD-xx se detallan en [puntos de dolor](puntos-de-dolor.md) con su
impacto y la forma de verificarlos con evidencia.

## Supuestos

- Los flujos son una simplificación funcional; no incluyen excepciones de mostrador.
- Los identificadores de jobs coinciden con el documento del batch nocturno.

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Flujos con variantes locales por sucursal | Refinamiento con jefes de sucursal en UAT. |
| Reglas de imputación de cuotas incompletas | Validación con Producto y Contabilidad. |

## Glosario

Ver [glosario único](../glosario.md).
