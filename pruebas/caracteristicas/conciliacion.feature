# lenguaje: es
Caracteristica: Conciliacion de saldos y libro mayor
  Como responsable de conciliacion
  Quiero reconstruir la ecuacion de cada cuenta y el libro mayor
  Para aprobar el corte con evidencia y no con supuestos

  Escenario: PR-008 Ecuacion de saldo reconstruida
    Dado el legado con sus movimientos y saldos
    Cuando la conciliacion elimina duplicados y normaliza los signos
    Entonces la suma de movimientos explica el saldo final de cada cuenta
    Y el resumen de saldos coincide con el destino

  Escenario: PR-009 Descuadre leve se ajusta automaticamente
    Dado un descuadre menor o igual a la tolerancia de ajuste
    Cuando se clasifica la cuenta
    Entonces queda como ajuste automatico con apertura regularizada

  Escenario: PR-010 Descuadre grave va a revision manual
    Dado un descuadre mayor a la tolerancia de ajuste
    Cuando se clasifica la cuenta
    Entonces queda en revision manual con evidencia y sin ajuste automatico

  Escenario: PR-011 Desfase contable se ajusta contra resultados
    Dado un desfase entre el mayor cargado y el esperado
    Cuando se recalcula el libro mayor
    Entonces el ajuste se imputa a la contrapartida 3.3.01
    Y el desbalance interno del destino sigue siendo cero

  Escenario: PR-012 Decision de go no-go por ensayo
    Dado los tres ensayos de migracion conciliados
    Cuando se evaluan los criterios de aceptacion
    Entonces los ensayos 1 y 2 resultan no-go
    Y el ensayo 3 resulta go con observaciones
