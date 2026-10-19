# Requisitos funcionales y no funcionales

| Proyecto | Migración del core bancario — Banco Meridiano Austral (entidad ficticia) |
|---|---|
| **Versión** | 1.0 |
| **Fecha** | 19/10/2026 |
| **Autor** | Franco Tilleria, Analista de Negocios |
| **Estado** | Aprobado |

> Documento generado automáticamente por `src/informes/brechas.py` a partir de
> `config/requisitos/requisitos.yaml`. No editar a mano.

## Propósito

Derivar los requisitos funcionales y no funcionales del análisis de brechas,
con identificadores únicos que alimentan la matriz de trazabilidad (fase 12).

## Alcance

Requisitos derivados de la matriz de brechas vigente: **41 funcionales** y **15 no funcionales**.

## Renuncia necesaria

Cada requisito tiene identificador único, prioridad MoSCoW y criterio de
aceptación verificable. Su cumplimiento se demuestra con casos de prueba (fase 8).

## Requisitos funcionales

| ID | Título | Descripción | Criterio de aceptación | Capacidad | Prioridad |
|---|---|---|---|---|---|
| RF-001 | Deduplicacion de clientes al migrar | El pipeline debe detectar clientes duplicados por documento o por similitud de nombre normalizado y cargar un unico cliente superviviente, preservando las referencias de cuentas. | Toda cuenta del origen referencia un cliente unico en el destino y el conteo de clientes del destino coincide con el esperado tras la deduplicacion. | CAP-01 | Must |
| RF-002 | Validacion de documentos de identidad | El pipeline debe validar formato y digito verificador de los documentos; los invalidos se rechazan con motivo y quedan para revision manual. | El 100 por ciento de los documentos cargados supera la validacion y todo rechazo tiene motivo registrado en la bitacora. | CAP-01 | Must |
| RF-003 | Exclusion de titulares fallecidos | Los clientes en estado fallecido no se cargan al destino; se listan para el proceso de sucesion. | Cero clientes fallecidos en el destino y listado completo de exclusiones disponible para Operaciones. | CAP-01 | Must |
| RF-004 | Contacto ampliado obligatorio | El cliente migrado requiere telefono y correo con formato valido; el faltante se completa desde texto libre o queda marcado como pendiente. | Al menos el 99 por ciento de los clientes migrados posee correo valido o marca de pendiente con intento de completado. | CAP-01 | Must |
| RF-005 | Control de vigencia documental | El destino registra fecha de vencimiento de documentos y los marca vencidos para bloqueo operativo configurable. | Todo documento migrado con vencimiento informado queda marcado segun su estado de vigencia a la fecha de corte. | CAP-02 | Should |
| RF-006 | Rechazo de documentos repetidos | Documentos identicos en clientes distintos se rechazan y se derivan a cumplimiento con evidencia. | Ningun documento duplicado entre clientes distintos queda cargado sin investigacion registrada. | CAP-02 | Should |
| RF-007 | Normalizacion de direcciones | Las direcciones se normalizan a un catalogo de localidades y provincias; lo incompleto se completa con valor por defecto y marca de revision. | El 100 por ciento de las direcciones cargadas tiene localidad y provincia validas o marca de revision. | CAP-03 | Must |
| RF-008 | Extraccion de datos desde texto libre | Se extraen telefonos, correos y direcciones reconocibles del campo de observaciones sobrecargado, conservando el texto original. | Todo patron reconocible queda extraido a su campo y el texto original se conserva integro en el destino. | CAP-03 | Should |
| RF-009 | Parametros de producto configurables | Tasas, limites y comisiones se cargan como parametros versionados del producto, no como constantes. | Un cambio de parametro se aplica sin despliegue de codigo y queda auditado. | CAP-04 | Must |
| RF-010 | Cola de revision para estados desconocidos | Cuentas con estado legado desconocido pasan a una cola de revision con decision obligatoria antes del corte. | El 100 por ciento de los estados desconocidos tiene decision registrada y el destino no contiene estados invalidos. | CAP-04 | Must |
| RF-011 | Descubierto y comisiones como condiciones de cuenta | Limite de descubierto y comision mensual se migran como condiciones de la cuenta corriente. | Toda cuenta corriente migrada posee condiciones de descubierto y comision segun su contrato de origen. | CAP-05 | Must |
| RF-012 | Impuesto sobre debitos y creditos | El destino calcula y registra el impuesto sobre movimientos de cuenta corriente segun parametro vigente. | Los movimientos gravados del periodo tienen su impuesto registrado y la suma concilia con la cuenta contable correspondiente. | CAP-05 | Must |
| RF-013 | Renovacion automatica de plazos fijos | El plazo fijo se renueva automaticamente al vencimiento segun condicion del contrato, con opcion de cancelacion. | Todo plazo fijo vigente migrado define su comportamiento de vencimiento y ninguno se renueva sin condicion informada. | CAP-06 | Should |
| RF-014 | Cancelacion anticipada con prorrateo | La cancelacion anticipada calcula intereses devengados y tasa de precancelacion segun parametro. | El importe de cancelacion coincide con el calculo parametrizado y queda registrado el detalle del prorrateo. | CAP-06 | Should |
| RF-015 | Cronogramas de cuotas consistentes | Los cronogramas migrados discriminan capital, interes y seguros, y el saldo de capital del prestamo equivale a la suma de capitales pendientes. | Todo prestamo migrado cumple la ecuacion saldo de capital igual a suma de cuotas pendientes dentro de la tolerancia definida. | CAP-07 | Must |
| RF-016 | Mora y refinanciacion | El destino calcula mora diaria y permite refinanciar un prestamo generando nuevo cronograma y cancelando el anterior. | Los prestamos en mora migrados reflejan cuotas vencidas correctas y una refinanciacion de prueba genera cronograma consistente. | CAP-07 | Must |
| RF-017 | Exclusion de prestamos hipotecarios | Los prestamos hipotecarios de la extraccion no se migran; se registran como fuera de alcance. | Cero prestamos hipotecarios cargados y listado de exclusiones informado al area de creditos. | CAP-07 | Must |
| RF-018 | Gestion de tarjetas de debito en linea | Emision, reposicion y bloqueo de tarjetas se integran con el procesador sin esperar el lote nocturno. | Un alta o bloqueo de prueba se refleja en el procesador dentro de los 5 minutos posteriores al evento. | CAP-08 | Must |
| RF-019 | Tarjeta de debito asociada a cuenta | La tarjeta migrada conserva su asociacion a la cuenta con estado, numero enmascarado y fecha de emision. | Toda tarjeta migrada referencia una cuenta valida y su estado corresponde al origen. | CAP-08 | Must |
| RF-020 | Mandatos de debito automatico operativos | Los mandatos activos migran con servicio, cuenta, tope, frecuencia y firma; los suspendidos y dados de baja se migran como historico. | El 100 por ciento de los mandatos activos ejecuta su debito del periodo de prueba segun condicion. | CAP-09 | Must |
| RF-021 | Transferencias por servicio | Las transferencias se ejecutan por servicio del core nuevo con validacion de saldo, limites y registro de la operacion. | Una transferencia de prueba descuenta y acredita de forma atomica y genera movimiento y asiento. | CAP-09 | Must |
| RF-022 | Plan de cuentas y matriz producto-contabilidad | El plan de cuentas migra completo y cada producto tiene definida su cuenta contable principal y su contrapartida. | Todo saldo de producto tiene cuenta contable asignada y la matriz esta aprobada por Contabilidad. | CAP-10 | Must |
| RF-023 | Asientos automaticos por evento | Los eventos de negocio generan asientos balanceados con referencia al documento de origen. | Todo asiento de los casos de prueba esta balanceado y referenciado a su operacion de origen. | CAP-10 | Must |
| RF-024 | Conciliacion contable automatizada | El pipeline compara, por cuenta contable, la suma de saldos de producto contra el mayor migrado y reporta diferencias con causa raiz. | El informe de conciliacion presenta el 100 por ciento de las cuentas conciliadas de forma directa o con ajuste evidenciado. | CAP-10 | Must |
| RF-025 | Intereses diarios de cajas de ahorro | El core nuevo causa intereses diarios sobre saldos de caja de ahorro y los capitaliza segun condicion del producto. | El interes de un periodo de prueba coincide con recalculo independiente dentro de la tolerancia de un centavo por cuenta. | CAP-11 | Must |
| RF-026 | Comisiones configurables y reversibles | Las comisiones se aplican por parametro de producto y su reversion requiere autorizacion de segundo nivel. | Una reversion de prueba exige dos usuarios y deja pista de auditoria con valores anteriores y posteriores. | CAP-11 | Must |
| RF-027 | Reportes regulatorios desde el modelo destino | Los reportes periodicos se generan desde el modelo relacional del core nuevo, con validaciones de calidad previas. | El reporte de prueba cuadra con los saldos conciliados del ensayo y no requiere ajustes manuales. | CAP-12 | Must |
| RF-028 | Trazabilidad de la informacion migrada | Cada registro migrado conserva identificador de origen, version de reglas y fecha de carga. | Es posible reconstruir el origen de cualquier registro del destino a partir de los identificadores de migracion. | CAP-12 | Must |
| RF-029 | Extractos y consultas en linea | Los extractos se generan desde el core nuevo con el historial migrado y las consultas responden en linea. | El extracto de un cliente de prueba incluye los movimientos migrados de los ultimos 12 meses sin diferencias con el origen. | CAP-13 | Should |
| RF-030 | Migracion de historial de movimientos | Se migran los movimientos de los ultimos 12 meses con conteos y sumas de control por cuenta y por periodo. | Conteo y suma de importes de movimientos del destino igualan al origen dentro de la tolerancia y toda exclusion esta justificada. | CAP-13 | Must |
| RF-031 | Reintentos programables de cobro | El core nuevo reintenta debitos fallidos segun calendario de cobranza configurado por producto. | Un debito fallido de prueba se reintenta los dias configurados y el exito detiene los reintentos. | CAP-14 | Should |
| RF-032 | Avisos de mora multicanal | Los avisos de mora se envian por correo y celular desde eventos del core. | Una cuota vencida de prueba genera los avisos configurados en el canal correcto. | CAP-14 | Could |
| RF-033 | Pista de auditoria completa | Toda operacion registra usuario, canal, fecha, valores previos y posteriores. | La pista de la operacion de prueba permite reconstruir el cambio completo y no admite edicion. | CAP-15 | Must |
| RF-034 | Segregacion de funciones | Los perfiles limitan funciones criticas; acciones sensibles requieren doble autorizacion. | Un usuario unico no puede ejecutar y autorizar la misma operacion critica. | CAP-15 | Must |
| RF-036 | Conciliacion de saldos por cuenta | El pipeline valida por cuenta que saldo final igual a saldo de apertura mas movimientos, con tolerancia parametrica. | Toda cuenta del destino cumple la ecuacion dentro de tolerancia o tiene ajuste registrado con evidencia. | TRV | Must |
| RF-037 | Bitacora de ejecucion del pipeline | Cada ejecucion registra conteos por etapa, tiempos, rechazos y version de reglas aplicada. | La bitacora permite reconstruir que reglas produjeron cada resultado del ensayo. | TRV | Must |
| RF-038 | Intercambio controlado con satelites | Mientras los satelites no se integren por servicio, los archivos de intercambio llevan conteo y suma de control obligatorios. | Ningun archivo de satelite se procesa sin cuadre de conteo y suma. | TRV | Should |
| RF-039 | Rechazo controlado de productos fuera de alcance | Los productos de rubros excluidos se rechazan con motivo fuera_de_alcance y se informan al area responsable. | Cero productos fuera de alcance cargados al destino y reporte de rechazos disponible. | TRV | Must |
| RF-040 | Mapeo de tipos de firma y condiciones | Los tipos de firma legados se mapean a condiciones del destino o se derivan a revision manual. | Toda cuenta migrada declara su condicion de firma o su derivacion a revision. | TRV | Could |
| RF-041 | Operatoria de caja cubierta | Depositos y extracciones por ventanilla operan sobre el core nuevo con limites parametrizados. | La operacion de caja de prueba se registra con asiento y movimiento asociados. | TRV | Must |
| RF-042 | Consulta de saldos por servicio | Los canales obtienen saldos y movimientos por servicio del core, sin archivos de posiciones. | La consulta de un cliente de prueba devuelve el mismo saldo conciliado del ensayo. | TRV | Must |

## Requisitos no funcionales

| ID | Título | Descripción | Criterio de aceptación | Categoría | Prioridad |
|---|---|---|---|---|---|
| RNF-001 | Rendimiento de la carga completa | La carga completa de todas las entidades debe completarse en menos de 4 horas sobre la infraestructura objetivo. | El ensayo general registra una duracion menor a 4 horas y el equipo de operaciones puede monitorearla en linea. | rendimiento | Must |
| RNF-002 | Disponibilidad del core nuevo | El core nuevo debe alcanzar un 99,9 por ciento de disponibilidad mensual percibida por canales en regimen. | El tablero de hypercare no registra caidas superiores a la meta durante los 30 dias posteriores al corte. | disponibilidad | Must |
| RNF-003 | Enmascaramiento de datos personales | Los entornos no productivos y las muestras publicadas usan datos personales seudoanonimizados de forma determinista. | Ninguna muestra publicada contiene documento, nombre, telefono, correo ni direccion reales (aun siendo sinteticos, se aplica el control). | seguridad | Must |
| RNF-004 | Auditabilidad del pipeline | Toda ejecucion del pipeline deja bitacora inmutable con versiones de reglas y resultados por entidad. | La bitacora del repositorio permite reconstruir cada ensayo sin acceso a los datos originales. | auditoria | Must |
| RNF-005 | Integridad con sumas de control | Ninguna carga se declara exitosa sin cuadre de conteo y suma de control contra el origen. | El pipeline detiene la carga de una entidad si su suma de control no cuadra fuera de tolerancia. | integridad | Must |
| RNF-006 | Usabilidad en sucursales | Las pantallas y flujos de caja deben reducir o igualar el tiempo de operacion actual por transaccion. | Los usuarios de UAT completan las tareas criticas en tiempo igual o menor al sistema legado. | usabilidad | Should |
| RNF-007 | Mantenibilidad de reglas | Las reglas de transformacion son datos versionados, no codigo embebido. | Una nueva version de reglas se publica sin recompilar y se puede revertir a la version anterior. | mantenibilidad | Must |
| RNF-008 | Escalabilidad | El modelo destino soporta un crecimiento anual del 30 por ciento en cuentas y movimientos sin rediseno. | La prueba de rendimiento con volumen ampliado mantiene los tiempos dentro de la ventana de carga. | rendimiento | Should |
| RNF-009 | Volumen de archivos | El pipeline procesa archivos de hasta 2 GB por entidad sin acumular todo en memoria. | La extraccion se ejecuta de forma fragmentada y el pico de memoria se mantiene bajo el limite del ambiente. | rendimiento | Should |
| RNF-010 | Objetivos de recuperacion | Ante una falla critica posterior al corte, el RTO objetivo es de 4 horas y el RPO de 15 minutos. | El simulacro de recuperacion restablece la operacion dentro de los tiempos objetivo con perdida de datos dentro del RPO. | continuidad | Must |
| RNF-011 | Observabilidad del pipeline | Cada etapa publica metricas de filas, tiempos y errores consultables por operaciones. | La bitacora y el tablero exponen el estado de cada etapa en cada ensayo. | operacion | Should |
| RNF-012 | Retencion de informacion | La informacion de la migracion (reglas, bitacoras, conciliaciones) se conserva segun la politica de retencion vigente del banco (ilustrativa). | Los artefactos de migracion quedan archivados en el repositorio y en el archivo documental con control de versiones. | cumplimiento | Must |
| RNF-013 | Idioma y terminologia | Documentacion, mensajes y nombres de objetos de negocio en espanol neutro latinoamericano, con glosario unico. | Todo artefacto publicado respeta el glosario y no contiene textos en otro idioma salvo nombres propios de herramientas. | documentacion | Must |
| RNF-014 | Reproducibilidad total | Todo el proyecto se regenera con semilla fija mediante `make todo` sin intervencion manual. | Dos ejecuciones consecutivas producen resultados identicos verificables por las pruebas de determinismo. | reproducibilidad | Must |
| RNF-015 | Tolerancias de conciliacion configurables | Las tolerancias por entidad y regla son parametros aprobados por Contabilidad, no valores de codigo. | Ajustar una tolerancia no requiere tocar codigo y el cambio queda auditado en el repositorio. | integridad | Must |

## Supuestos

- Los criterios de aceptación se expresan en lenguaje verificable; los casos en
  formato Gherkin se desarrollan en la fase 8 de pruebas.

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Requisitos sin caso de prueba | La matriz de trazabilidad marca la cobertura. |
| Cambios de alcance tardíos | Control de cambios vía comité operativo y ADR. |

## Glosario

Ver [glosario único](../glosario.md).
