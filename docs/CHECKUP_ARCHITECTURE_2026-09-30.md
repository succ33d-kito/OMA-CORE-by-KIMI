# Check-up técnico de la candidata O.M.A.-C.O.R.E.

Autoridad: snapshot `OMA-CORE-v2-temporal-evidence-graph-2026-09-29.zip`, SHA-256
`ac24728bbbce0ca9828ace3e9cfee294a0af74d24b75a0432fca20a6f9231e93`, contrastado con
código y tests locales. El remoto `succ33d-kito/OMA-CORE-by-KIMI` estaba en
`8f4f5547bff98c9a78a6da19456c354ade706b86`; la candidata añade módulos posteriores.
La comparación normalizada por finales de línea no encontró archivos del remoto
ausentes en la candidata. No se está auditando una instancia de producción viva.

## Estado por capa

| Capa ideal | Estado verificable | Evidencia y gap |
|---|---|---|
| Data / Observation Fabric | Parcial | Collectors, `market_mechanics/state.py`, adaptador Binance y `prospective_receipts.py`. Hay validación temporal y receipts prospectivos; falta un contrato uniforme de disponibilidad/procedencia para todas las fuentes históricas. Nueva descarga y reducción primaria de 2024 no resuelve ese gap. |
| Event Fabric | Implementado como bus local; parcial como fabric durable | `event_bus/bus.py`: publicación/suscripción. No equivale a log durable unificado con replay y entrega garantizada entre procesos. |
| Temporal Evidence / Intelligence Graph | Implementado como componente; integración parcial | `intelligence_graph/store.py`: nodos/aristas tipados, restricciones temporales, append-only, SQLite y consultas as-of; tests de rollback/reapertura. El caso incluido es retrospectivo. No hay conexión completa y continua entre la operación y el grafo científico. |
| Context | Parcial | `market_mechanics/context.py` y `latent_context.py`: descriptores y unknown explícitos. Ejes macro/eventos/liquidez/posicionamiento no están integrados universalmente; no se infieren de OHLCV. |
| Market Regime | Implementado como clasificación | `regime.py`, `transitions.py`, pruebas de calibración/transiciones. Clasificar régimen no demuestra utilidad predictiva incremental. |
| Market Mechanics | Parcial | Estado OHLCV, participation y métricas públicas. Este corte añade agresión real de aggTrades, funding y métricas 2024; no hay reconstrucción validada de libro, identidad de participantes ni absorción causal. |
| Hypothesis / Evidence | Parcial | Schemas, ScientificStore, lifecycle, OutcomeBridge y grafo existen. Falta lineage verificable común que conecte hipótesis, evidencias disponibles, decisión y outcome. Registry V2 es diseño, no hipótesis validada. |
| Edge | Ausente como ventaja validada | Existen herramientas de comparación y protocolos de investigación. Ningún resultado nuevo de este corte acredita Edge después de costes, multiplicidad, estabilidad y replicación. |
| Decision / Council | Implementado; provenance parcial | Council, `decision_domain/record.py` y paper adapter. El adaptador deja explícitamente `hypothesis_id=None` y `evidence_ids=()`. EMA corregida; adaptación paper por PnL bloqueada. |
| Execution / Risk | Implementado en simulación; madurez operativa parcial | PaperTradingEngine, guards, SL/TP, slippage, ledger y estados de ejecución. Los tests no prueban operación real continua ni rentabilidad. |
| Outcome / Learning | Captura implementada; aprendizaje bloqueado | Journal factual y PerformanceMemory; OutcomeBridge corregido para SQLite. Parsers de texto siguen siendo heurísticos descriptivos. Sin provenance completa no alimentan una promoción ni adaptación del Council. |
| Knowledge | Objetos/CRUD implementados; validación bloqueada | Candidatos de investigación en cuarentena. Lifecycle y Store rechazan VALIDATED, incluso asignación directa previa al CRUD; no se sustituye replicación por un contador declarado. |
| Criterion | Métricas/propuestas implementadas; aplicación bloqueada | `criterion_evolution.py` y Store rechazan APPLIED. Revisión humana por sí sola no acredita gates científicos. |
| Persistencia / recovery | Implementado por componentes; parcial extremo a extremo | SQLite journal/grafo, `paper_checkpoint.py`, commit atómico y pruebas de rollback/recovery. Falta demostrar recuperación coordinada de todos los stores y fuentes en una sesión operativa real. |
| Benchmark / ablation / OOS | Infraestructura parcial; validación pendiente | Bootstrap por calendario, estabilidad, protocolos y evaluador prospectivo. Corregida disponibilidad de las 81 barras. No se ejecutan nuevos outcomes mientras el Data Gate sea FAIL. |

## Riesgos graves tratados en este corte

- Disponibilidad prospectiva: comprobar toda la ventana de 81 barras, no sólo
  la última; receipts ausentes o tardíos invalidan la decisión evaluable.
- Veredictos: `incorrect`/`invalid` no pueden casar como `correct`/`valid`;
  negaciones se tratan conservadoramente y texto desconocido no confirma neutralidad.
  Esto no convierte heurísticas de texto en evidencia científica independiente.
- Council: EMA acotada, rechazo de entradas no booleanas y lectura neutral de
  pesos heredados corruptos. PnL de una operación no prueba cada opinión;
  se mantiene registro descriptivo, se desactiva la actualización automática.
- OutcomeBridge: lectura efectiva de `sqlite3.Row` con tests sobre base temporal.
- Knowledge/Criterion: promoción cerrada en API de lifecycle y persistencia;
  candidatos marcados no elegibles para aprendizaje, sin aumento automático de
  confianza por una confirmación textual.
- Provenance incompleta del paper adapter: gap reconocido y bloqueado en sus
  consecuencias de aprendizaje; no se inventan hypothesis/evidence IDs.
- Microestructura: discrepancias entre aggTrades y velas oficiales se registran;
  spans de IDs no se aceptan como conteo exacto de operaciones.

## Prioridad siguiente

1. Resolver el contrato de disponibilidad y la reconciliación entre fuentes.
   Un timestamp de transacción o descarga actual no es un recibo histórico.
2. Integrar lineage verificable decisión → hipótesis/evidencia → outcome, con
   pruebas negativas; conservar la cuarentena hasta completar gates independientes.
3. Ejecutar la ablation incremental del Registry sólo en discovery elegible;
   registrar negativos, soporte común, costes y multiplicidad.
4. Freeze formal antes de cualquier evaluación nueva de Binance 2025; mantener
   sellado Kraken Q2-2026. Documentar exposición histórica previa sin declarar
   que los períodos vuelven a ser vírgenes.

Puede esperar: ontología más extensa del grafo, nuevas capas del Council, modelos
complejos de Participant State y optimización de Criterion. Añadir complejidad
antes de resolver integridad y utilidad incremental no está justificado.

La bitácora del checkpoint y los manifests de `research/edge_discovery/` contienen
las ejecuciones, resultados, límites y pasos reproducibles de este corte.
