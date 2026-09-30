# ADR OMA-V2-004 — Predicción de referencia y resolución por evento

La demo emite una referencia probabilística constante 0.5 por símbolo, fuente y vela horaria cerrada observada. Target: el cierre exactamente 24 horas después del cierre de referencia será estrictamente mayor que el cierre de referencia. Un empate es false. El horizonte está anclado al cierre de la vela, no al instante de recepción del lote; ambos tiempos se conservan. El identificador es estable y no se reescribe la probabilidad al repetir un evento.

El registro contiene evento, precio inicial, fuente, snapshot de mercado y régimen. Se emite antes del análisis de agentes para incluir eventos que no generan operaciones. El resolver recibe el siguiente lote validado de la misma fuente/símbolo y exige la vela exacta del horizonte. Sin ella queda pendiente; una interrupción mayor que la ventana disponible necesitará backfill posterior. No se utiliza PnL como etiqueta ni se sustituye por un cierre posterior. Una etiqueta registrada es inmutable.

La referencia 0.5 es un control sin capacidad predictiva atribuida. No convierte scores o conviction en probabilidad. El nuevo productor queda conectado a la demo, pero no modifica entradas, riesgo ni Criterion. El journal permite evaluación por etiqueta de régimen (estructura:volatilidad) además de por snapshot. El siguiente modelo deberá superar esta referencia en datos futuros no usados para diseñarlo.

La autenticidad de tiempos en replay sigue siendo responsabilidad del dataset/productor; la interfaz admite tiempos declarados. Esta entrega prueba persistencia y causalidad del flujo, no presenta nuevas métricas de rentabilidad ni evidencia de calibración real. Los horizontes solapados generan dependencia estadística: el número de registros no equivale al de observaciones independientes.

Validación: 962 passed, 12 skipped, 3 warnings en 66.12 segundos.
