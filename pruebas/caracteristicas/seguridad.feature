# lenguaje: es
Caracteristica: Proteccion de datos en artefactos publicados
  Como responsable de seguridad de la informacion
  Quiero que las muestras y los artefactos no expongan datos sensibles
  Para publicar el proyecto sin riesgo reputacional ni regulatorio

  Escenario: PR-016 Documentos seudoanonimizados estables
    Dado un documento del legado
    Cuando se aplica el enmascaramiento con la sal del proyecto
    Entonces el resultado es distinto del original
    Y dos ejecuciones producen el mismo valor enmascarado

  Escenario: PR-017 Sin numeros de tarjeta completos en las muestras
    Dado los archivos publicados en muestras
    Cuando se buscan secuencias de dieciseis digitos
    Entonces no existe ningun numero de tarjeta completo
