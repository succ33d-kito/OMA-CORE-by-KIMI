# Mechanics v2.1 — freeze de exclusión, 2026-09-30

**Data Gate FAIL. Subconjunto causal admisible vacío. Experimento BLOCKED.**
No se ha congelado un experimento ejecutable ni demostrado Edge. Se congela
explícitamente qué NO puede usarse bajo el contrato causal actual. No existe
una versión reducida admisible de M_t con la evidencia histórica disponible.

## Checkpoint anterior cerrado

Branch `main`, commit `c900946ef559a8f72cffa47a3f019c3df92f8d08`, remoto
`https://github.com/succ33d-kito/OMA-CORE-by-KIMI.git`. Push confirmado por
`ls-remote`: SHA remoto idéntico. Suite ya verificada: 1.055 passed, 15 skipped,
1 deselected, tanto local como desde exportación del índice Git. No se repite
esa suite ni la reducción anual en esta continuación.

## Clasificación exacta de cada issue actual

A = causal: excluir. B = semántico: cuarentena. C = limitación: preservar NULL.
D = discrepancia entendida: documentar, sin cambiar el significado del dato.
Cada issue del manifest recibe exactamente una categoría; diferentes riesgos
de una misma característica pueden figurar como issues distintos.

| Issue | Clase | Acción |
|---|---|---|
| AGGTRADES_HISTORICAL_AVAILABILITY_UNKNOWN | A | EXCLUDE until causality is independently established |
| AGGTRADES_KLINES_RECONCILIATION_FAILED | B | QUARANTINE unresolved comparability; do not force equality |
| FUNDING_HISTORICAL_AVAILABILITY_UNKNOWN | A | EXCLUDE until causality is independently established |
| METRICS_HISTORICAL_AVAILABILITY_UNKNOWN | A | EXCLUDE until causality is independently established |
| METRICS_MISSING_VALUES | C | Keep NULL; nonmissing sample still fails independent causal gates |
| PRICE_HISTORICAL_AVAILABILITY_UNKNOWN | A | EXCLUDE until causality is independently established |
| 37 primary metric archives have unordered rows | D | Stable sort already performed without imputation; preserve raw hashes |
| Aggregate record count differs from individual kline count | D | Distinct quantities; retain distinct names, never require equality as proof of aggregate record count |
| ID span treated as exact individual trade count | B | Already removed unsupported trade-size/intensity estimators; diagnostic field excluded |

La diferencia de conteo agregado frente al conteo individual es D **sólo para
la variable que cuenta registros agregados**. No resuelve las discrepancias de
volumen ni valida los spans como operaciones individuales: esas siguen B.
El missingness es C, pero no convierte en causal el resto de la muestra.
Hay 8.774/8.784 horas con métricas; la muestra causal certificada sigue siendo
cero. Los motivos de indisponibilidad de precio, régimen y métricas son A.

## Disponibilidad causal por característica

En todas las filas: publicación/recepción histórica **no acreditada**;
`available_at=NULL`; uso en `decision_at` **no admisible**, disposición EXCLUDED.
La columna de conocimiento es un límite inferior, nunca un timestamp fabricado.

| Característica | Timestamp fuente | Significado | Cuándo podría conocerse, como mínimo |
|---|---|---|---|
| Price/OHLCV | open_time, close_time | UTC bar interval labels; close time is not a receipt | Not before the entire H1 interval closes |
| Regime | derived; last_bar_closed_at | Function of 81 closed H1 bars | Not before every input is available and computation completes |
| OpenInterest | create_time / metric_observed_at | Provider metric row time; no recorded publication time | Not before the selected snapshot and its predecessor are published/received |
| AggressorFlow | transact_time | Exchange timestamp of aggregate trade record, milliseconds UTC | Not before all records needed for the H1 aggregate are available |
| Positioning | create_time / metric_observed_at | Provider metric row time, not receipt | Not before publication/receipt of that row |
| TakerMetrics | create_time / metric_observed_at | Archive row time; precise per-field measurement window must be established separately | Not before complete measurement window and publication |
| Funding | calc_time | Funding calculation/settlement record time; not proof of publication | Only after actual publication/receipt, not automatically at settlement |
| aggregate_trade_count | transact_time aggregated over [hour, hour+1h) | Count of actual aggTrades records in the interval | After full interval and its records are available |
| underlying_id_span_count | first_trade_id, last_trade_id; transact_time | Sum of ID spans, diagnostic only | Not admissible as individual count even if availability is later established |
| official_kline_trade_count | open_time, close_time | Provider count attached to the kline interval | After complete kline publication/receipt |

`source_metric_at` conserva el timestamp original, separado de `available_at`.
`decision_at` debe ser una decisión independiente fijada en el protocolo;
no se desplaza retrospectivamente hasta que el dato resulte conveniente.
Un feature derivado requiere todos los inputs disponibles y el cálculo terminado.
El chequeo legacy `metrics_asof` compara observación y decisión, pero no verifica
recepción: no se lo acepta como gate causal. El receipt ledger prospectivo sí
registra recepción local; no demuestra retrospectivamente disponibilidad en 2024.

**ALLOWED = []**. EXCLUDED = Price/OHLCV, Regime, OpenInterest, AggressorFlow,
Positioning, TakerMetrics, Funding, aggregate_trade_count,
underlying_id_span_count, official_kline_trade_count para experimentos causales
históricos de este freeze. Los datos descriptivos se conservan.
UNKNOWN = disponibilidad histórica, los valores métricos ausentes, ventanas por
campo no acreditadas y reconciliación de universos pendiente. Unknown describe
atributos de los inputs; no es una lista alternativa de features autorizados.

## Registro MM incorporado explícitamente ahora

Procedencia: **conversation-specified conceptual hypothesis set supplied by
project owner on 2026-09-30**. La instrucción inicial que asumía estos IDs ya
presentes en el repositorio fue corregida por su propietario. No se inventa una
equivalencia con las ocho familias anteriores. Registro completo y fórmulas en
`HYPOTHESIS_REGISTRY_MM_V1.json`, unido por hash al freeze.

| ID | Hipótesis conceptual | Inputs esenciales incluyendo comparator | Estado |
|---|---|---|---|
| MM-01 | Long Initiation | Price/OHLCV, OpenInterest, AggressorFlow | BLOCKED |
| MM-02 | Short Initiation | Price/OHLCV, OpenInterest, AggressorFlow | BLOCKED |
| MM-03 | Short Covering | Price/OHLCV, OpenInterest, AggressorFlow | BLOCKED |
| MM-04 | Long Unwind | Price/OHLCV, OpenInterest, AggressorFlow | BLOCKED |
| MM-05 | Buy Pressure Without Proportional Price Response | Price/OHLCV, AggressorFlow | BLOCKED |
| MM-06 | Sell Pressure Without Proportional Price Response | Price/OHLCV, AggressorFlow | BLOCKED |
| MM-07 | Crowded Longs | Price/OHLCV, OpenInterest, AggressorFlow, Funding, Positioning | BLOCKED |
| MM-08 | Crowded Shorts | Price/OHLCV, OpenInterest, AggressorFlow, Funding, Positioning | BLOCKED |
| MM-09 | Flow Acceleration | Price/OHLCV, AggressorFlow | BLOCKED |
| MM-10 | Flow Exhaustion | Price/OHLCV, AggressorFlow | BLOCKED |

M_t = (ΔP, ΔOI, AF, ΔAF, F, POS, R). EPR = |AF|/(|ΔP|+ε) y su versión
normalizada exclusivamente con pasado son conceptos operacionalizables;
no prueban absorción. ε, escalas, strong/extreme/weak/acceleration/divergence
permanecen sin operacionalizar; no se han elegido mirando outcomes.
MM-03/04 necesitan AF para construir su comparator de iniciación. MM-07/08 no
sustituyen Funding por Positioning; además deberá fijarse el operador conjunto
exacto antes de ejecución. No hay READY ni PARTIALLY_TESTABLE. NO_PROXY es una
prohibición aplicable a todas, no una excusa para cambiar sus condiciones.

## Alcance real del freeze científico

Freeze por SHA de evidencia, clasificación, admisibilidad vacía y registro
conceptual. Las diez hipótesis están bloqueadas, **no falsadas**. No hay subset
para el que fijar un experimento ejecutable. Horizonte, comparador operacional,
n mínimo, bootstrap, costes, umbral económico, estabilidad y multiplicidad
figuran como NULL/no aplicables; rellenarlos con números ahora daría una falsa
apariencia de protocolo listo. El protocolo OI+taker anterior es distinto y no
se reutiliza como si fuera MM-01…MM-10.

Para desbloquear: evidencia independiente de disponibilidad, semántica resuelta
para los inputs elegidos y una nueva revisión inmutable del protocolo, con TODOS
los parámetros que solicita el propietario definidos antes de resultados. El
verificador no puede levantar el gate ni ejecutar outcomes.

```text
python scripts/check_mechanics_v2_1_freeze.py --verify-only
```

Esto comprueba únicamente integridad del freeze, sin leer datasets. Sin
`--verify-only`, devuelve exit code 2 y `experiment=BLOCKED`: es el comando de
preflight barato para la próxima sesión. PASS de integridad NO es PASS de datos.

Verificación de esta continuación: 3 tests específicos pasan (integridad,
manipulación del hash y clasificación incompleta). CLI `--verify-only` devuelve
0; preflight normal devuelve 2/BLOCKED, tal como exige el freeze. No se repitió
la suite amplia porque no cambió el motor ni se ejecutó otro experimento.

## Holdouts y aprendizaje

Binance 2025: SECONDARY TEMPORAL CONFIRMATION, exposición anterior reconocida;
no se abrió en esta continuación. Kraken Q2-2026:
SEALED_CROSS_EXCHANGE_HOLDOUT, sin acceso. Sin discovery sweep, nuevos outcomes,
retuning, proxies ni promoción. La exposición del fixture mixto en el sprint
previo permanece documentada en la bitácora; no se borra del historial.

Observation → Event → Hypothesis → Evidence → Decision → Outcome → Knowledge
→ Criterion. Outcome ≠ LearningSignal; PnL no actualiza Criterion. La cuarentena
permanece hasta validación y replicación definidas por protocolo.

## Próxima única acción

Establecer y verificar el contrato de disponibilidad de Price/OHLCV con el
capturador de receipts prospectivos existente, sin inventar recibos de 2024.
Esto busca obtener el primer input causal acreditado; no rehabilita por sí solo
el histórico ni autoriza el experimento. No se activó captura automática ahora.
