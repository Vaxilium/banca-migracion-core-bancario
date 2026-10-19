# Indicadores del proyecto

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

Definir los indicadores con los que se mide el avance y el éxito de la migración,
su fórmula, su meta y su fuente de evidencia.

## Indicadores de proceso

| Indicador | Definición | Meta | Fuente |
|---|---|---|---|
| Avance por fase | Fases cerradas con evidencia / total de fases | 100 % al corte | Repositorio y actas. |
| Brechas cerradas | Brechas en estado cerrado / total priorizadas | ≥ 95 % al corte | Matriz de brechas. |
| Casos de prueba ejecutados | Ejecutados / planificados por ciclo | 100 % por ciclo | Informe de pruebas. |
| Defectos críticos abiertos | Críticos y altos sin resolver | 0 al corte | Registro de defectos. |
| Requisitos cubiertos por prueba | Requisitos con al menos un caso / total | ≥ 95 % | Matriz de trazabilidad. |

## Indicadores de calidad del dato y migración

| Indicador | Definición | Meta | Fuente |
|---|---|---|---|
| Tasa de rechazos | Registros rechazados / leídos, por entidad y ensayo | ≤ 1 % por entidad | Bitácora del pipeline. |
| Conciliación contable | Cuentas contables conciliadas (directa o con ajuste) / total | 100 % | Informe de conciliación. |
| Conciliación de saldos por cuenta | Cuentas con saldo consistente / total | ≥ 99,9 % | Informe de conciliación. |
| Defectos de datos detectados | Defectos detectados / defectos inyectados (verdad de terreno) | ≥ 90 % | Perfilado y verdad de terreno. |
| Rechazos resueltos | Rechazos con decisión registrada / total de rechazos | 100 % | Registro de rechazos. |

## Indicadores operativos posteriores al corte

| Indicador | Definición | Meta | Fuente |
|---|---|---|---|
| Duración del cierre diario | Minutos desde cierre de operaciones hasta saldos oficiales | ≤ 120 min | Monitoreo del core nuevo. |
| Disponibilidad del core | Uptime semanal percibido por canales | ≥ 99,9 % | Monitoreo. |
| Incidentes de hypercare | Incidentes severidad 1 y 2 por semana | ≤ 3 en semana 1, decreciente | Mesa de ayuda. |
| Reversa no activada | Activar plan de reversa | No | Comité de corte. |
| Adopción de capacitación | Personal crítico capacitado / planificado | ≥ 95 % | LMS y asistencia. |

## Indicadores de beneficios (posteriores al cierre)

| Indicador | Definición | Meta | Fuente |
|---|---|---|---|
| Ahorro de licencias del legado | Apagado efectivo del legado | Mes 3 post-corte | Finanzas. |
| Tiempo de lanzamiento de productos | Semanas desde definición a producción | ≤ 6 semanas | Producto. |
| Conciliaciones manuales eliminadas | Interfaces conciliadas automáticamente | 100 % | Operaciones. |

## Supuestos

- Los umbrales se fijan en el comité directivo y pueden recalibrarse con evidencia
  de los ensayos.
- Los indicadores posteriores al corte requieren instrumentación del core nuevo.

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Indicadores sin fuente automatizada | Todo indicador debe declarar fuente verificable. |
| Metas poco realistas | Recalibración tras cada ensayo con datos reales. |

## Glosario

Ver [glosario único](../glosario.md).
