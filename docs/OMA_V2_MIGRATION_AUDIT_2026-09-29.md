# OMA-CORE v2 — auditoría inicial de migración

Fecha: 2026-09-29. Fuente: ZIP entregado por el usuario. Alcance: inspección estática selectiva de código, esquemas y documentos canónicos; no certifica ejecución ni rentabilidad.

## Decisión arquitectónica

Conservar el runtime actual como línea base y construir la red de inteligencia por cortes verticales. No renombrar paquetes ni alterar el flujo de órdenes hasta que exista un contrato verificable de decisión, evidencia y resultados. `docs/ENGINEERING_CONSTITUTION.md` declara `docs/ARCHITECTURE_V2.md` autoridad superior; la propuesta Intelligence Network todavía no es un documento canónico en el ZIP. Formalizar una ADR de transición y actualizar la jerarquía antes de cambiar responsabilidades de módulos.

## Mapa de componentes

| Componente existente | Evidencia en ZIP | Clasificación | Destino v2 y primer cambio |
|---|---|---|---|
| Event y bus | `core/schemas/event_schema.py`, `core/event_bus/` | KEEP/TRANSFORM | Añadir proveniencia y tiempo de observación sin romper contratos existentes. |
| Observación | `core/collectors/`, incluidos `world_monitor.py` y `world_monitor_v2.py` | KEEP/MERGE | Registrar fuente, calidad, cobertura y retraso; decidir propietario canónico tras rastrear llamadores. |
| Hipótesis y evidencia | `core/schemas/hypothesis_schema.py`, `evidence_schema.py`, `core/scientific/scientific_store.py` | KEEP/TRANSFORM | Vincular eventos, versiones y evidencia verificable; conservar los ciclos de vida actuales. |
| Knowledge y Criterion | `core/schemas/knowledge_schema.py`, `criterion_delta_schema.py`, `core/scientific/` | KEEP/TRANSFORM | Ya existen; medir su conexión real con decisiones y preservar revisión humana de cambios de Criterion. |
| Council | `core/schemas/agent_schema.py`, `core/council/` | TRANSFORM | Un `CouncilDecision` contiene `event_id`, acción y opiniones, pero no hipótesis, alternativas, probabilidad calibrada ni instantánea de información disponible. |
| Market Agent | `core/agents/market_agent.py` | TRANSFORM | Usa OHLCV, SMA, RSI, ATR, momentum y volumen; requiere estado de mecánica de mercado con campos explícitamente desconocidos si faltan datos de órdenes, liquidez o derivados. |
| Ejecución y riesgo | `core/execution/`, `core/execution_engine/` | MERGE (después) | Identificar qué ruta crea órdenes y cuál certifica resultados antes de mover código; mantener guardas actuales. |
| Outcome | `core/outcome_domain/outcome.py`, `core/scientific/outcome_bridge.py`, `core/schemas/outcome_comparison_schema.py` | KEEP/TRANSFORM | Existen varios objetos: resultado factual, puente científico y comparación. Definir identidad y trazabilidad común sin confundir calidad de decisión con PnL. |
| Backtest | `core/engines/backtest_engine.py`, `core/execution/backtest_engine_v2.py` | MERGE (después) | Auditar entradas, reloj, comisiones y sesgos antes de escoger ruta canónica. |
| Intelligence Graph | No se encontró paquete o esquema canónico de grafo en `core/` | MISSING | Primera versión: relaciones tipadas, temporales y con proveniencia sobre almacenamiento existente; no adoptar base de datos nueva de entrada. |
| Reasoning / causalidad | Razonamiento textual en agentes; no se encontró modelo causal canónico | MISSING | Hipótesis causal separada de correlación observada, con mecanismo, predicción falsable y contradicciones. |
| Market Mechanics | Métricas OHLCV en Market Agent y metadatos parciales en `core/markets/crypto.py` | MISSING | Definir disponibilidad de datos por dimensión; no inferir order flow u opciones a partir de velas. |
| Adaptadores externos | Coleccionistas y UI existentes | ADAPTER | Mantener TradingView/OpenBB/n8n fuera del núcleo hasta que exista una integración concreta. |

## Riesgos que ordenan la migración

1. **Autoridad documental:** `ARCHITECTURE_V2.md` describe Knowledge como ausente, aunque el ZIP incluye `knowledge_schema.py` y `knowledge_extractor.py`; el documento ya no representa por completo el código.
2. **Falsa proveniencia:** `AgentOpinion.evidence` es una lista de cadenas, distinta de objetos `Evidence` con fuente e hipótesis. No convertir esas cadenas automáticamente en evidencia validada.
3. **Sesgo retrospectivo:** una decisión debe congelar datos conocidos, timestamps, alternativas, hipótesis y versión de criterio en el instante de decidir; evaluar el resultado en una fase posterior.
4. **Datos inaccesibles:** no declarar absorción, posicionamiento o liquidez como observados cuando sólo hay OHLCV.
5. **Regresión operacional:** mantener el flujo paper y guardas mientras se introduce una ruta de observación pasiva para v2.

## Primer corte vertical implementable

1. ADR de autoridad de migración y contratos v2, sin desactivar documentos históricos.
2. `DecisionRecord` inmutable y serializable con `event_id`, `hypothesis_id`, evidencia identificada, alternativa, estado de mercado observado, fuentes, timestamps y restricciones. Adaptador de `CouncilDecision` que indique campos faltantes en vez de inventarlos.
3. Guardar DecisionRecord antes de cualquier acción paper; asociar `Outcome` por identificador y comparar decisión ex ante con resultado ex post.
4. Incorporar una sola dimensión de Market Mechanics sustentada por datos presentes (estructura/volumen); registrar el resto como no observado.
5. Replay cronológico de un evento a outcome, con pruebas de proveniencia, ausencia de fuga temporal e idempotencia. Criterion sólo recibe propuestas revisables.

## Verificación en este entorno

Tras instalar `pytest` y las dependencias declaradas en `requirements.txt`, `python -m pytest tests -q` confirmó **928 passed, 12 skipped, 3 warnings** para el ZIP original. Se agregó el contrato experimental `core/decision_domain/record.py` y `docs/ADR-OMA-V2-001-DECISION-JOURNAL.md`; las dos pruebas dirigidas pasaron. No se modificó la ruta operacional ni se habilitó trading.

## Corte paper posterior

El adaptador `core/decision_domain/paper_adapter.py` se conectó a `scripts/extended_demo_realtime.py`: captura planes antes de `execute_signal`, registra bloqueos y enlaza cierres de `check_positions` con la decisión original. El contrato de `core/outcome_domain/` sigue independiente. El resume del demo conserva contadores pero no posiciones, por lo que la reconciliación tras reinicio queda pendiente. Suite completa tras esta integración: **932 passed, 12 skipped, 3 warnings**.

## Continuidad y Outcome Collector

`core/execution/paper_checkpoint.py` restaura portafolio, posiciones abiertas, operaciones cerradas, capital y estado de guardas desde un checkpoint versionado. El demo rechaza reanudar archivos antiguos sin ese estado. `observe_canonical_outcome` enlaza Outcomes reales de `OutcomeCollector` con decisiones ya registradas, sin fingir trazas. Quedan pendientes la persistencia transaccional ante una caída entre una mutación en memoria y el checkpoint, y la reconciliación de `PerformanceMemory` y Council. Los contadores siguen restaurándose para conservar el historial.

Suite completa después de ambos cortes: **937 passed, 12 skipped, 3 warnings**.

## Checkpoint y outcome en una transacción

`DecisionJournal` ahora guarda en SQLite el checkpoint paper y sus nuevos outcomes en la misma transacción. El JSON queda como proyección/migración; se prefiere SQLite al reanudar. La demo también recupera registros de agentes de PerformanceMemory y pesos de Council. Los planes no confirmados al arrancar quedan marcados como no comprometidos, sin asignarles resultado de trading. El efecto de una apertura en memoria se pierde si el proceso cae antes del commit, lo que es correcto para esta simulación local; la ejecución externa futura necesitará reconciliación con el broker.

Suite completa después del corte transaccional: **939 passed, 12 skipped, 3 warnings**.

## Market Mechanics v1

Se añadió estado OHLCV reproducible con rango previo, retorno, volumen relativo y volatilidad por barra. El estado contiene fuente, tiempos, parámetros, hash y barras originales, y se guarda dentro del DecisionRecord. El demo filtra la vela abierta y rechaza lotes incoherentes, discontinuos o antiguos. Se limpian precios cacheados al fallar una actualización. Liquidez, order flow y derivados siguen desconocidos. Este corte proporciona observaciones para aprendizaje; no implementa aún hipótesis causales, validación de Edge o aprendizaje automático. Especificación: `docs/ADR-OMA-V2-002-MARKET-MECHANICS.md`.

Regresión completa: **950 passed, 12 skipped, 3 warnings**, en 70.13 segundos. Once pruebas nuevas cubren las métricas, calidad de entrada, temporalidad y persistencia del estado.
