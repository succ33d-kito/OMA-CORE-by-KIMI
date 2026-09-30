# ADR OMA-V2-003 — Regime y calibración v1

Estado: implementado como observación y medición; 2026-09-29.

`core/market_mechanics/regime.py` clasifica estructura usando eficiencia direccional de 20 variaciones: desplazamiento absoluto dividido por recorrido absoluto. >=0.6 implica trend, <=0.25 range y el resto transition. Dirección up/down/flat se guarda aparte. Son umbrales heurísticos versionados, sin optimizar contra el holdout 2025 ni afirmar probabilidades.

Volatilidad: desviación muestral de 20 retornos comparada con los 60 inmediatamente anteriores, sin solapar ventanas. Ratio >=1.5 high, <=2/3 low, el resto normal. Menos de 81 cierres o referencia casi nula producen unknown. Risk appetite, liquidity, event y crisis quedan unknown: estos ejes requieren datos adicionales. El RegimeState deriva del mismo MarketState usado por la decisión y se guarda íntegro en DecisionRecord; no altera órdenes ni sus umbrales.

`core/scientific/probability_calibration.py` permite registrar predicciones binarias inmutables con probabilidad explícita, target, tiempos disponibles/emisión/horizonte, versión del modelo y referencia de régimen opcional. Su resolución exige etiqueta booleana, procedencia y horizonte completo. Calcula Brier, log loss (clipping 1e-15), fiabilidad por bins y ECE; conserva tamaño de muestra y devuelve null sin casos resueltos. Las métricas son descriptivas, no certifican calibración suficiente ni Edge.

La interfaz admite tiempos declarados para replay. No autentica por sí misma la hora real de producción de una predicción; una auditoría prospectiva debe registrar al productor en tiempo real. El diario se implementa y prueba, pero el Council actual no produce probabilidades de eventos bien definidas. No se convierte conviction a probabilidad ni se inventa una predicción para llenar tablas. La integración con productores y etiquetas de eventos concretos queda como siguiente corte.

La calidad de datos continúa expresándose por validaciones y campos desconocidos, sin porcentajes artificiales. La incertidumbre epistemológica y causal permanece sin estimar. No se actualiza Criterion automáticamente. El aprendizaje requiere objetivos definidos y muestras suficientes por régimen, además de pruebas temporales independientes.

Validación de esta entrega: 959 passed, 12 skipped, 3 warnings en 71.49 segundos.
