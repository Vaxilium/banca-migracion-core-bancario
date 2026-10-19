# Glosario único del proyecto

| Versión | Fecha | Autor | Estado |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria, Analista de Negocios | Vigente |

Este glosario es la referencia terminológica única del repositorio. Cuando otro
documento menciona "el glosario", se refiere a este archivo.

| Término | Definición |
|---|---|
| Ajuste de migración | Asiento o regularización registrada y evidenciada durante la conciliación para explicar una diferencia entre el origen y el destino. No se aplica sin evidencia ni aprobación. |
| Ancho fijo | Formato de archivo plano legado en el que cada campo ocupa una posición y longitud constantes, definidas por un diseño de registro. |
| AS-IS | Estado actual de procesos y sistemas antes de la migración. |
| Batch nocturno | Procesamiento por lotes que el core legado ejecuta durante la noche; habilita el cierre diario y la puesta al día de intereses, comisiones y estados. |
| Big bang | Estrategia de corte que migra todos los productos y clientes en una única ventana. |
| Calidad de datos | Grado en que los datos son completos, válidos, únicos, consistentes y conciliables para el propósito de migración. |
| Carga delta | Carga incremental de lo ocurrido entre la última extracción completa y el momento del corte (movimientos y altas del día del corte). |
| Causa raíz | Categoría que explica una discrepancia: defecto de datos, regla errónea, diferencia de diseño o diferencia aceptada. |
| Cierre diario | Conjunto de procesos que consolidan las operaciones del día y determinan los saldos oficiales. |
| Conciliación | Comparación sistemática entre origen y destino (conteos, sumas de control, saldos) con tolerancias definidas y registro de diferencias. |
| Core bancario | Sistema central que registra clientes, productos, saldos, movimientos y contabilidad del banco. |
| Corte (cutover) | Ventana controlada en la que se apaga el legado, se carga el destino y se activan los canales sobre el core nuevo. |
| Cuenta huérfana | Cuenta cuyo cliente referenciado no existe en el maestro de clientes del origen. |
| Descuadre | Inconsistencia entre el saldo informado de una cuenta y la suma de sus movimientos más el saldo de apertura. |
| Diseño de registro | Especificación de la estructura de un archivo de ancho fijo (campos, posiciones, longitudes, tipos). Equivale al copybook legado. |
| Defecto | Incorrección detectada en software, datos o documentación, registrada con severidad, prioridad, estado y causa. |
| Delta final | Última carga incremental, realizada dentro de la ventana de corte, con las operaciones posteriores a la extracción completa. |
| Enmascaramiento | Técnica que reemplaza datos personales por valores seudoanonimizados deterministas en entornos de prueba y muestras publicadas. |
| Ensayo de migración | Ejecución completa del pipeline sobre la extracción vigente, con resultados medidos y conciliados, previa al corte. |
| Evidencia | Artefacto verificable (CSV, informe, bitácora, captura del tablero) que respalda una afirmación de estado o un control. |
| Gherkin | Formato de criterios de aceptación estructurado en Dado / Cuando / Entonces. |
| Go/no-go | Decisión formal de avanzar o detener el corte, basada en criterios y semáforos predefinidos. |
| Hypercare | Periodo de soporte intensivo inmediatamente posterior al corte, con guardias y seguimiento diario. |
| Importe con signo final | Codificación legada donde el último carácter del campo indica el signo (`+`/`-`) y los decimales son implícitos. |
| Libro mayor | Registro contable de cuentas con saldos deudores y acreedores. |
| Mandato | Autorización del cliente para debitar automáticamente una cuenta por un servicio o cuota. |
| MoSCoW | Priorización de requisitos y brechas: Must, Should, Could, Won't. |
| Paralelo | Estrategia en la que el legado y el nuevo core operan simultáneamente y se comparan resultados. |
| Pipeline | Cadena automatizada de extracción, transformación, carga, conciliación y generación de informes. |
| Punto de no retorno | Momento del corte a partir del cual revertir al legado deja de ser viable sin costos mayores; queda documentado en el plan de reversa. |
| RACI | Matriz de roles: Responsable, Aprueba, Consultado, Informado. |
| Regla de transformación | Instrucción versionada que convierte un dato de origen en uno de destino (normalización, mapeo, corrección, rechazo). |
| Rechazo | Registro que no puede cargarse al destino; queda con motivo, entidad y clave para su tratamiento (corrección, ajuste o exclusión). |
| Reversa | Plan de retorno al legado si el corte falla, con actividades, responsables y tiempos. |
| SIT | Pruebas de integración de sistemas (System Integration Testing). |
| Suma de control | Total agregado (conteo o importe) usado para verificar que origen y destino coinciden. |
| UAT | Pruebas de aceptación de usuario (User Acceptance Testing). |
| Ventana histórica | Periodo de movimientos históricos que se decide migrar (por ejemplo, 12 meses). |
| Verdad de terreno | Archivo generado al inyectar defectos sintéticos que registra qué se corrompió, para medir la detección real del pipeline. |
