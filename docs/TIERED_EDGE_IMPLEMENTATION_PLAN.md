# OMA-CORE — Plan Tier 1–5 para Edge Trading

Fecha: 2026-09-29. Alcance objetivo fijado por el usuario. Este documento ordena la migración; no declara implementadas capacidades ni sustituye contratos operacionales existentes.

## Corrección del alcance actual

Market Mechanics v1 implementa observaciones OHLCV, controles de calidad/tiempo y snapshots en decisiones. El ensayo MM-H1 probó un único filtro de ruptura/volumen sobre señales técnicas. No probó Event + Price + Mechanics, porque no incluyó eventos externos y su transmisión. Su resultado desfavorable no decide la validez de la arquitectura objetivo. El benchmark de los runtimes completos también sigue pendiente.

La presencia de clases, indicadores o nombres en documentación no certifica una capacidad integrada. La inspección actual no identifica motores canónicos completos para los 17 bloques. Hay bases reutilizables en esquemas científicos, Outcome, diario de decisiones, agentes, guardas, PerformanceMemory y snapshots de mercado. Los tests de software no acreditan Edge económico.

## Mapa de capacidades y aceptación

| ID / Tier | Capacidad y prioridad del usuario | Base actual / trabajo requerido | Salida y validación |
|---|---|---|---|
| A / 1 | Market Mechanics — EXTREMA | OHLCV parcial. Añadir Market Structure, Order Flow, Volume, Auction Dynamics, Liquidity, Absorption, Imbalance, Volatility, Price Discovery y Execution Dynamics. | MechanicsSnapshot con observaciones e inferencias separadas. Event + Price contra Event + Price + Mechanics, fuera de muestra. |
| B / 1 | Market Regime — EXTREMA | Tendencia/volatilidad heurísticas dispersas; falta estado común, temporal y validado. | RegimeState multidimensional; estrategia condicionada al régimen y estabilidad de transiciones. |
| C / 1 | Expectations + Surprise — EXTREMA | Falta expectativa previa vinculada a publicación y revisión. | ExpectationSnapshot y SurpriseObservation: expected, actual, surprise, price response, después positioning; evaluar revisiones y fugas temporales. |
| D / 1 | Priced-In — MUY ALTA | Falta estimación explícita de información incorporada al precio. | PricedInAssessment como inferencia incierta, con proxies y alternativas; nunca un porcentaje exacto sin validación. Medir aportación adicional a C y B. |
| E / 1 | Positioning — MUY ALTA | Posiciones de nuestra cuenta no representan posicionamiento del mercado. | PositioningState con OI, funding, basis, options, liquidations, short interest, ETF flows y crowdedness según cobertura. Hipótesis sobre participantes vulnerables. |
| F / 1 | Liquidity — MUY ALTA | Slippage simulado no equivale a liquidez observada. | LiquidityState: localización, profundidad, consumo, retirada, sweeps, absorción, slippage e impacto. Stop clusters como inferencia salvo observación verificable. |
| G / 2 | Participant & Incentive — ALTA | Falta modelo de actores/objetivos/restricciones. | Participant → Objective → Constraint → Incentive → LikelyAction → MarketImpact, con alternativas y evidencia. |
| H / 2 | Capital Flow — ALTA | Falta contabilidad de flujos entre mercados. | FlowObservation y FlowHypothesis; distinguir flujos observados de movimientos de precios; efectivo, bonos, oro, equities, commodities, crypto. |
| I / 2 | Dynamic Cross-Market Graph — ALTA | Correlación/causalidad objetivo; no asumir implementación por mención documental. | Relaciones Source, Target, Direction, Lag, Strength, Regime, Evidence, Confidence, HistoricalOutcomes, versión y vigencia. Correlación y causalidad separadas. |
| J / 2 | Relative Value — MEDIA-ALTA | Falta modelo de divergencias condicionadas. | RelativeValueHypothesis con spread, régimen, costes, horizonte e invalidación. Relaciones oro/yields, petróleo/inventarios, cobre/China, BTC/liquidez, equities/rates, FX/diferenciales. |
| K / 3 | Scenario — ALTA | Hypothesis existe; falta conjunto de escenarios comparables. | Continuación, reversión, no continuación, transmisión cruzada; supporting/contradicting evidence, trigger, invalidation y mecanismo. |
| L / 3 | Counterfactual — ALTA | Condición de invalidación textual parcial. | Predicciones discriminantes: qué esperaríamos observar si la explicación fuera incorrecta. Sin afirmar causalidad por un relato. |
| M / 3 | Uncertainty — ALTA | Scores/confidencias heurísticos y calidad parcial. | Separar Score, probabilidad de hipótesis, incertidumbre, calidad de datos, confianza causal, confirmación de mechanics y riesgo de ejecución. Unknown debe ser representable. |
| N / 3 | Calibration — ALTA | PerformanceMemory tiene sesgo confianza/accuracy agregado; insuficiente como calibrador. | Definir evento y horizonte; evaluar probabilidades guardadas antes del resultado mediante Brier/log loss, curvas de fiabilidad y tamaños de muestra. PnL positivo no es etiqueta universal. |
| O / 4 | Reflexivity — MEDIA-ALTA | Falta modelo de bucles de respuesta. | FeedbackScenario con participantes, señal observada, reacción y actualización del estado; validación contra secuencias observadas. |
| P / 4 | Adversarial Reasoning — MEDIA | Falta protocolo estructurado de explicaciones rivales. | Challenges que generen pruebas falsables y alternativas estratégicas; no presuponer manipulación. |
| Q / 5 | Alternative Data — EDGE UNKNOWN | Cobertura por evaluar. | Satellite, shipping, weather, energy, search, web traffic, jobs, supply chain y on-chain; cada fuente entra por una hipótesis y prueba de valor incremental. |

## Dependencias y propiedad

Estos son dominios de capacidad, no 17 microservicios ni 17 agentes nuevos. Un monolito modular puede compartir almacenamiento y contratos. A consume estados especializados de E/F; no recalcula su verdad por separado. I relaciona objetos de todos los dominios. Agentes consultan y producen aportaciones sobre objetos comunes. Decision conserva las versiones usadas y Outcome registra lo ocurrido. La capa científica evalúa; Criterion sólo recibe cambios propuestos con revisión humana.

Los regímenes se modelan sobre ejes coexistentes: estructura (trend/range/transition), volatilidad (high/low), apetito por riesgo (risk-on/off), liquidez (expansion/contraction), contexto de evento y crisis. Una tendencia puede coexistir con alta volatilidad. OHLCV de BTC no basta para declarar risk-on global o expansión de liquidez.

## Orden de implementación

1. **Fundación compartida B + M + N:** estado de régimen con disponibilidad temporal y unknown; contrato de predicción/resultado y medición de calibración. Crear sólo lo necesario para el siguiente ensayo, sin esquemas vacíos de todos los bloques.
2. **A + F con datos observables:** ampliar mecánica con operaciones ejecutadas e inferencias de desequilibrio/absorción; para profundidad y retirada, exigir libro o snapshots adecuados. Validar disponibilidad histórica antes de diseñar mediciones.
3. **C + E:** publicación económica con expectativa previa fechada y posicionamiento disponible. Elegir primero un tipo de evento y un mercado. Snapshot previo y respuesta posterior deben estar separados.
4. **D + K + L:** construir explicaciones y escenarios alternativos del mismo evento, estimación incierta de priced-in e invalidación observable.
5. **I + H + G + J:** transmisión entre mercados, participantes, flujos y valor relativo; relaciones por régimen, lag y evidencia.
6. **O + P + Q:** retroalimentación estratégica y fuentes adicionales conforme a valor demostrado.

Los niveles del usuario preservan prioridad estratégica. M/N se adelantan como instrumentos de medición para evitar construir A–F sin poder medir incertidumbre o calibración.

## Ensayo correcto del núcleo

Congelar eventos, precios, splits, relojes, modelo de ejecución, presupuesto de riesgo y costes. Comparar de forma incremental: Event + Price; + Mechanics; + Regime; + Expectations/Surprise; + Positioning; + estimación Priced-In. Reportar valor marginal de cada bloque y combinado, muestra por régimen, incertidumbre y frecuencia de operaciones. No atribuir una reducción de pérdidas por menor exposición a un mejor pronóstico.

Las probabilidades se registran antes de observar resultados. La calidad de decisión se evalúa respecto a información disponible y alternativas; OutcomeQuality se mantiene separada. Registrar también hipótesis no respaldadas y resultados inconclusos. El holdout BTC 2025 del MM-H1 ya fue observado: no es nuevo holdout para optimizaciones posteriores.

## Próximo corte concreto

Market Regime v1 con ejes limitados a estructura y volatilidad que los datos actuales permiten observar, asociado a MechanicsSnapshot y DecisionRecord; los ejes globales y de liquidez quedan unknown. Añadir contrato de probabilidades calibrables por evento/horizonte y medición sin actualizaciones automáticas. Después ampliar mechanics con datos de trades y fuentes de expectativas/posicionamiento. Este orden no convierte el ensayo MM-H1 en la estrategia oficial ni pospone el objetivo completo de A–Q.
