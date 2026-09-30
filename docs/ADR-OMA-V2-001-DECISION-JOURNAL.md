# ADR OMA-V2-001 — Migración del registro de decisiones

Estado: adoptada para el corte vertical experimental, 2026-09-29.

## Contexto

`ARCHITECTURE_V2.md` y `ENGINEERING_CONSTITUTION.md` siguen gobernando el runtime existente. La arquitectura Intelligence Network acordada por el usuario introduce un Decision Graph; todavía no sustituye contratos operacionales ni guardas de riesgo. `CouncilDecision` registra consenso y opiniones, mientras `Outcome` es un resultado factual de ejecución. Falta congelar una decisión ex ante de forma independiente de su resultado posterior.

## Decisión

Introducir `core/decision_domain/record.py` como contrato experimental, aditivo, con `DecisionRecord` inmutable, `DecisionOutcome` factual y `DecisionJournal` SQLite. Una decisión registra información disponible, referencias a fuentes/evidencia, alternativas, expectativa, invalidación, restricciones y datos ausentes. Los resultados se anexan después sin reescribir la decisión. Los identificadores duplicados con carga idéntica son idempotentes; cargas contradictorias fallan.

Esta ADR **no** cambia la jerarquía de autoridad de `ENGINEERING_CONSTITUTION.md`, ni permite ejecución, scoring, aprendizaje o cambios automáticos de Criterion. El contrato requiere una integración revisada antes de que el flujo paper lo use. El modelo conserva explícitamente los datos faltantes; una cadena de opinión de agente no se convierte en evidencia científica sin validación.

## Integración paper realizada

`scripts/extended_demo_realtime.py` crea un diario separado en `_extended_demo/decisions.db`. Después de formar una señal y antes de `execute_signal`, el adaptador `core/decision_domain/paper_adapter.py` registra el plan paper y adjunta `decision_record_id` a la señal. Si la ejecución es bloqueada, añade un hecho de bloqueo. Al cerrar una posición mediante `check_positions`, registra precio, razón de salida y PnL factual sin calificarlos como calidad de decisión. Las guardas y tamaño de posición no cambiaron.

El checkpoint v1 del demo conserva contadores, posiciones abiertas, capital, operaciones cerradas y estado de las guardas. `_save_state` usa reemplazo atómico y se invoca después de aperturas y cierres. La reanudación de archivos antiguos con sólo contadores se rechaza. Una caída abrupta entre una mutación en memoria y su checkpoint todavía requiere reconciliación transaccional.

`observe_canonical_outcome` acepta exclusivamente un Outcome publicado por `OutcomeCollector` con decisión y timestamp reales, y lo anexa de forma idempotente. Ese Outcome certifica la ejecución, **no el PnL final**. El cierre de la demo paper usa su propio adaptador; no se fabrican identificadores de Approval, ExecutionResult o Ledger.

## Recuperación transaccional posterior

`DecisionJournal.commit_paper_state` confirma el checkpoint y los outcomes paper en una sola transacción SQLite. El archivo JSON es una proyección legible y una ruta de migración; en adelante el estado SQLite es autoritativo. La demo guarda después de aperturas y cierres, y restaura los registros de agentes de PerformanceMemory y los pesos de Council. Una decisión registrada cuya apertura no aparece en el último checkpoint y carece de outcome recibe el hecho `paper_transition_not_committed` al arrancar; no se la cuenta como trade ni como pérdida. Una caída antes de confirmar una apertura descarta ese cambio en memoria; una caída después de confirmar conserva la posición. No hay puente de orden real.

## Siguiente integración

Proporcionar hipótesis, fuentes, evidencia e instantánea de mercado desde sus productores reales. Si falta una referencia, registrarla en `missing_information`. Verificar de forma sostenida las ventanas de crash mediante inyección de fallos y replay cronológico. La promoción de cualquier criterio requiere revisión humana.

## Validación

Suite original del ZIP: 928 passed, 12 skipped, 3 warnings. Pruebas dirigidas del diario y el adaptador paper: 4 passed. La suite completa posterior debe quedar registrada en el reporte de entrega.
