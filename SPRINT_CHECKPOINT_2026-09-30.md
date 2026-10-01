# O.M.A.-C.O.R.E. — checkpoint científico y técnico

**Resultado: Data Gate FAIL; ningún Edge validado; ninguna promoción.**
Continuar desde esta bitácora y el manifest portátil, no desde porcentajes de
madurez ni desde resultados históricos de otros períodos.

## Continuidad y autoridad

Se reanudó el pilot-day `aggTrades — BTCUSDT USDⓈ-M — 2024-01-01` indicado por el
usuario. Los ZIP descargados durante la ejecución interrumpida ya estaban
completos; se reutilizaron con sus checksums, sin volver a descargarlos.
No se localizó una bitácora `.md` independiente de aquella sesión; se usaron
las instrucciones actuales, el contexto adjunto y los archivos verificables.
La candidata inicial y su hash están en [el check-up](docs/CHECKUP_ARCHITECTURE_2026-09-30.md).

## Cambios de este corte

- Captura primaria 2024 reanudable y verificada; reducción H1 por chunks, sin
  rellenar horas ni microestructura ausente, y manifest con URLs/checksums.
- Registro experimental [Hypothesis Registry V2](research/edge_discovery/HYPOTHESIS_REGISTRY_V2.md):
  Price + OI + Aggressor Flow + Funding + Positioning + Regime; ocho familias,
  estados de participantes no causales y Effort → Price Response no confundido
  con absorción demostrada. Ninguna fórmula de Edge fue retuneada.
- Bloqueos de Knowledge VALIDATED y Criterion APPLIED tanto en lifecycle como
  en persistencia. Los candidatos quedan en cuarentena, sin autoridad operativa.
- Council EMA corregida; adaptación automática por PnL deshabilitada mientras
  falta provenance. Se conserva contabilidad descriptiva y control de riesgo.
- OutcomeBridge soporta filas SQLite reales. Parsers de outcomes evitan las
  falsas confirmaciones por substrings, negaciones y neutralidad sin evidencia.
- Evaluador prospectivo verifica disponibilidad de **las 81 barras**. Su
  comparador incluye ratio=1 cuando corresponde a la especificación existente;
  esto corrige implementación, no cambia el protocolo ni recalcula sus outcomes.
- La semántica de conteo se corrige: registros agregados observados sí;
  `last_trade_id - first_trade_id + 1` es sólo diagnóstico, nunca conteo exacto
  individual ni sustituto de intensidad/tamaño individual. Cachés v1 migradas
  con hash previo conservado; sin modificar datos fuente.

## Datos y resultados verificables

| Comprobación | Resultado |
|---|---|
| Pilot-day | 761.222 registros; 24 horas; 0 huecos de aggregate ID |
| Pilot diario vs primeras 24 h del mensual | PASS en volúmenes, quote volume, aggregate count e ID spans |
| Año 2024, 12 aggTrades mensuales | **530.973.404 registros**, 8.784 horas, 0 huecos de aggregate ID, 0 horas vacías |
| Funding | 12 archivos, 1.098 observaciones; 1.098 sin receipt histórico verificable |
| Métricas primarias | 366 archivos; 8.774 horas observadas; 10 horas ausentes |
| Valores ausentes tras unión a H1 | 10 por campo; 11 en `sum_toptrader_long_short_ratio` |
| Orden original de métricas | 37 archivos desordenados; ordenación estable, sin imputación ni eliminación de duplicados |
| Diferencias de volumen base vs klines | 2.127 horas fuera de tolerancia; máximo absoluto 6.427,855 BTC |
| Diferencias de taker buy volume | 1.151 horas; máximo absoluto 3.451,772 BTC |
| Diferencias de quote volume | 2.129 horas; máximo absoluto 446.794.114,1169 USDT |
| ID spans vs conteo oficial | 4.396 horas distintas; máximo absoluto 94.034 |
| Archivos externos primarios, incluido piloto | 391 receipts; **6.833.833.222 bytes** fuera de Git |

La reconciliación compara horas idénticas, con tolerancias explícitas en el
manifest. Discrepancia no implica automáticamente corrupción: los universos y
la agregación de fuentes pueden diferir. La documentación oficial de
[Binance Public Data](https://github.com/binance/binance-public-data) describe
el esquema y checksums. La [API de aggTrades](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Compressed-Aggregate-Trades-List)
excluye operaciones del fondo de seguros y ADL y agrupa operaciones; esto es una
posible explicación de parte de las diferencias, **no una reconciliación probada
de estos archivos de 2024**. No se ajustaron cantidades para forzar coincidencia.

El gate falla por disponibilidad histórica desconocida de precio, métricas,
funding y agresión, missingness de métricas y reconciliación pendiente. El
timestamp del mercado no prueba el instante de recepción. La descarga de hoy
tampoco prueba disponibilidad en 2024. `outcome_testing_allowed=false` y
`outcomes_computed=false`. No hay ablation de retornos nueva, hipótesis
supervivientes/falsadas ni updates de Knowledge/Criterion en este corte.

## Integridad de holdouts

- Binance 2025 permanece cerrado a **nuevos análisis de outcomes** hasta un
  freeze formal. Ya existía exposición histórica, documentada en la candidata;
  no puede presentarse como un período virgen.
- Incidente de tests: dos pruebas heredadas cargaban un CSV mixto 2024–2025
  antes de filtrar y validar sólo 2024. Se ejecutaron durante la primera
  verificación; no calcularon outcomes de 2025. Se sustituyó ese fixture por
  datos sintéticos exclusivamente de test y se excluyó el CSV mixto de Git.
  Estos fixtures no se usan como observaciones ni proxies de microestructura.
- Kraken XBTUSD Spot H1 Q2-2026 sigue `SEALED_CROSS_EXCHANGE_HOLDOUT`; su archivo
  no se abrió. Los informes Kraken heredados no se reanalizaron. Antes de una
  futura validación habrá que resolver la exposición de ventanas históricas.
- El test del caso retrospectivo del grafo que carga un informe de outcomes
  2024–2025 se excluyó expresamente. Los otros tests del grafo usan fixtures.

## Verificación

Suite local: **1.055 passed, 15 skipped, 1 deselected**, sin fallos. De los skips,
12 corresponden a pruebas live de Binance no disponibles y 3 a instalación/
permisos POSIX que Windows no puede validar. Tres warnings heredados de fixtures
de pytest quedan documentados; no son evidencia de operación real.

Se verifica además una exportación del índice Git para comprobar que los tests
no dependen de datos ignorados presentes sólo en esta computadora. Resultado
en `research/edge_discovery/TEST_RESULTS_2026-09-30.json`.

Comando de la suite usada en este corte:

```text
python -m pytest tests -q -k "not bundled_case_is_reproducible_and_retrospective" --tb=short
```

Python y versiones de dependencias quedan en
`research/edge_discovery/ENVIRONMENT_2026-09-30.json`. No se ejecutó trading live,
ni se activó un timer o servicio permanente.

## Reanudar en otra computadora

Remoto: `https://github.com/succ33d-kito/OMA-CORE-by-KIMI.git`; branch: `main`.
Base remota conservada: `8f4f5547bff98c9a78a6da19456c354ade706b86`. El SHA del
checkpoint se obtiene con `git rev-parse HEAD` tras actualizar a este commit;
la respuesta de cierre registra el SHA publicado y verificado remotamente.
No se reescribe historial.

```text
git clone https://github.com/succ33d-kito/OMA-CORE-by-KIMI.git
cd OMA-CORE-by-KIMI
python -m venv .venv
# Activar .venv según el sistema; reproducir versiones del ENVIRONMENT.json.
python -m pip install -r requirements.txt pytest
python -m pytest tests -q -k "not bundled_case_is_reproducible_and_retrospective" --tb=short
```

Los datos masivos no viajan por Git. Para reconstruir observaciones, elegir una
carpeta externa (reemplazar `EXTERNAL_2024_DATA`); las descargas verificadas se
reutilizan y las parciales continúan desde su posición:

```text
python scripts/download_mechanics_v2.py --root EXTERNAL_2024_DATA --kind aggTrades --pilot-day 2024-01-01
python scripts/mechanics_v2_pilot.py --root EXTERNAL_2024_DATA
python scripts/download_mechanics_v2.py --root EXTERNAL_2024_DATA --kind all
python scripts/mechanics_v2_data_gate.py --root EXTERNAL_2024_DATA
python scripts/mechanics_v2_pilot.py --root EXTERNAL_2024_DATA
python scripts/export_mechanics_checkpoint.py --root EXTERNAL_2024_DATA
```

Los tests incluyen fixtures oficiales **sólo de 2024** de tamaño acotado: los 12
ZIP H1 y checksums ocupan menos de 0,5 MB, más un CSV normalizado de 0,58 MB.
Paneles derivados, ZIP masivos, bases, caches, logs y secretos quedan ignorados.
Los artefactos heredados no incluidos tienen inventario de hashes; informes
históricos pequeños se preservan como contexto, no como resultados de este sprint.

Archivos principales: `core/market_mechanics/{microstructure,reconciliation}.py`,
`core/scientific/learning_integrity.py`, fixes de Council/Outcome/lifecycle/Store,
scripts de descarga/gate/exportación, pruebas de integridad, Registry,
check-up de arquitectura y `mechanics_v2/PORTABLE_MANIFEST.json`. También se
incorporan las adiciones v2 de la candidata que aún no existían en el remoto:
Decision Journal, checkpoint paper, graph, Context/Regime e infraestructura
científica con sus tests y ADRs; no se atribuyen como desarrollo nuevo de hoy.

## Siguiente cuello de botella

Resolver comparabilidad de aggTrades/klines, missingness y disponibilidad real
antes de ablation. Mantener la evidencia desconocida como desconocida. Después,
conectar provenance verificable y usar el diseño incremental del Registry en
discovery elegible. No abrir holdouts ni levantar cuarentena para evitar un FAIL.
Este resultado negativo del Data Gate es el corte científicamente coherente;
no justifica añadir modelos ni reclamar una ventaja todavía.

## Continuación acotada Mechanics v2.1

El checkpoint anterior se publicó como `c900946ef559a8f72cffa47a3f019c3df92f8d08`
en `origin/main`; coincidencia remota verificada. La continuación solicitada
clasifica los seis issues sin repetir descargas, reducción ni suite completa.
El propietario proporcionó explícitamente MM-01…MM-10, ahora materializados
con esa procedencia. Ver [freeze causal y registro](research/edge_discovery/mechanics_v2_1/FREEZE.md).

Resultado: subconjunto causal admisible vacío, diez hipótesis BLOCKED, cero
READY; no hay protocolo de resultados ejecutable mientras fallen sus inputs.
Se congela la exclusión, no se presenta un experimento como listo. El guard de
integridad tiene tres tests nuevos pasando y rechaza la ejecución con código 2.
Binance 2025 se clasifica explícitamente como SECONDARY TEMPORAL CONFIRMATION;
Kraken Q2-2026 permanece SEALED_CROSS_EXCHANGE_HOLDOUT. No se abrieron en esta
continuación. El próximo paso único figura en ese freeze.

## Sprint Point-in-Time Price/OHLCV

Partiendo de `f8b967a998f7f7571a6c97f4d44f53dd0966a22a`, se amplió el receipt
ledger existente con observaciones versionadas y gate causal central. Una prueba
real price-only pasó, con disponibilidad demostrada a las
2026-09-30T18:14:57.387351Z. No implica cobertura continua ni acredita 2024.
Freeze previo intacto; MM READY=0/BLOCKED=10; holdouts sin abrir.
22 tests focalizados pasan. Contrato, evidencia, limitaciones y siguiente acción
en [Point-in-Time Contract](docs/POINT_IN_TIME_CONTRACT_2026-09-30.md) y revisión
`research/edge_discovery/price_point_in_time/REVISION.json`.

## Sprint continuous H1 Price capture

Continuation from `7a95a6615ea7da509e0a9c23da1ad1229e0fca47`: UTC boundary
runner, bounded retry, OS singleton lock, gap/streak checker, 81-bar certificate
and external prefix anchors implemented. Windows logon task installed/running;
runtime and live ledger remain outside Git. One real receipt, streak 1,
80 remaining at the checkpoint; Regime not executed. No discovery or holdouts.
Historical Data Gate FAIL and MM READY=0/BLOCKED=10 remain unchanged.
47 focused tests pass; freeze verification PASS. Real scheduled-task restart
verified; no receipt duplication or alteration.
See [operations, evidence and limitations](docs/CONTINUOUS_PRICE_CAPTURE_2026-09-30.md).
Next bottleneck: elapsed real time with continuous causal receipts; leave the
host awake/online and the scheduled task running. No historical backfill.

## Surgical Event Intelligence checkpoint

Baseline `e27e61b` matched the expected HEAD; working tree was clean. No capture
restart, receipt changes, holdout access or environment mixing in this session.
RSS assigned type/sentiment/urgency and assets using substrings of raw HTML:
`attack` treated physical attacks as exploits, `bill` matched `billion`, `ban`
matched `bank`, and `ETH` matched `Ethena`/other words. OpportunityEngine inherited
the resulting type and sentiment; it did not independently infer regulation.
RSS entities remain the schema's empty default; no entity extractor was added.

Minimal fix: visible-text parsing, bounded lexical matches, cyber context for
ambiguous security words, explicit ticker matching and canonical BTC/ETH aliases.
Original raw content is retained and new classifications carry rule version
`rss-token-context-v1`. Existing stored events/opportunities were not rewritten.
FRED now makes no requests without a key. Yahoo diagnostics distinguish a missing
package from dependency import failure. On this host yfinance is installed, but
Windows Application Control blocks a pandas DLL; that policy was not bypassed.

Evidence: 38 semantic/FRED tests plus 88 scoring/Yahoo-guard/freeze tests pass.
A read-only replay of 110 operational RSS records changed hack labels 13 -> 3
and regulatory labels 27 -> 8; this is a diagnostic delta, not measured accuracy.
Controlled feed -> temporary DB -> opportunities passes, including negative and
positive regulatory controls. Main `.venv` has no pytest, so regression tests use
the existing audit environment; the controlled operational check runs directly
in main `.venv`, with no new dependencies. Historical Data Gate remains FAIL;
MM 0 READY / 10 BLOCKED; no Regime execution, Edge or learning promotion.

Remaining limits: lexical rules do not resolve negation, subject attribution or
multi-topic summaries; conservative ticker matching may miss lowercase mentions.
Next action: label a small fixed sample of the remaining ambiguous operational
RSS cases before extending rules. DLL remediation requires the host's approved
application-control process and is separate from semantic validation.

## Event Intelligence fixed semantic baseline

From `63dcb70`, added 24 fixed diagnostic contrast cases and an offline evaluator;
classifier unchanged. References are assistant-authored manual annotations,
explicitly pending human review; HUMAN_GOLD is empty. Predictions are separate.
Set micro-F1: event types .8400, assets .8947, entities .0000 (not implemented).
Sentiment macro-F1 .4531 / accuracy .6818 on 22 scorable cases; two mixed cases
excluded explicitly. These are selected-case diagnostics, not production accuracy.
24 relevant tests pass. Details, hashes, FP/FN and reproduction command in
`research/event_intelligence/baseline_v1/README.md`. Structural deficits: assertion/
negation and clause/subject scope; single-output loss on multi-topic text.
No rule changes or scientific promotion. Next: human adjudication of the fixed
reference, then a small clause-scoped negation/context experiment, not more keywords.

## 2026-10-01 — Event Intelligence intervention v1 closure

KEEP_WITH_LIMITATIONS. Same fixed 24 proposed-reference cases; baseline_v1 and
HUMAN_GOLD unchanged. BEFORE equals frozen metrics; evaluator/reference hashes
match AFTER. Event-type micro-F1 .8400 -> .9600; sentiment macro-F1 .4531 ->
.7381, accuracy .6818 -> .8636. Assets unchanged. Seven corrected cases,
zero observed scored regressions; 38 relevant tests pass. No further rule tuning.
Report: `research/event_intelligence/intervention_v1/README.md`, with paired
predictions, metrics, confusion matrices and unchanged failures. Provisional
freeze only: small known diagnostic set, no human gold or production validation.
No protected scientific/capture components touched. User requested STOP with
local changes preserved, no commit/push; no next experiment launched.
