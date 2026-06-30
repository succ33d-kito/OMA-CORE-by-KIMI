# INTEGRATION_ARCHITECTURE_V1.1.md

**Proyecto:** O.M.A.-C.O.R.E.

**Versión:** 1.1

**Estado:** CANONICAL SPECIFICATION

**Fecha:** Junio 2026

**Alcance:** Arquitectura únicamente

---

# 1. Propósito

Este documento revisa `INTEGRATION_ARCHITECTURE_V1.md` para resolver el conflicto arquitectónico detectado entre la integración externa y la fundación del Execution Engine interno.

La decisión canónica es:

**Execution Engine es el propietario de la ejecución.**

La Integration Layer deja de ser propietaria de la ejecución y pasa a ser una capa opcional de infraestructura para conectividad externa futura.

La integración NO tiene como objetivo aumentar la autonomía del sistema.

Su objetivo futuro será permitir que el Execution Engine pueda, si una arquitectura posterior lo autoriza, conectarse a plataformas externas sin modificar el núcleo del sistema.

La ejecución primaria de O.M.A.-C.O.R.E. es interna y simulada.

Simulation es el modo por defecto.

Este documento debe leerse junto con:

- `ARCHITECTURE_V2.md`
- `PIPELINE_V2.md`
- `INTEGRATION_ARCHITECTURE_V1.md`

Cuando `INTEGRATION_ARCHITECTURE_V1.md` asume que TradingView o cualquier broker externo es el objetivo primario, esta versión 1.1 lo reemplaza.

`INTEGRATION_ARCHITECTURE_V1.md` no se elimina. Queda preservado como antecedente histórico y como referencia de principios, pero no gobierna Sprint 15.

---

# 2. Principios

Los principios arquitectónicos originales se mantienen sin cambios.

## P1

O.M.A.-C.O.R.E. toma decisiones.

Los brokers únicamente ejecutan.

Nunca al revés.

---

## P2

Toda decisión debe ser reconstruible.

Debe poder responderse:

- qué evento la originó;
- qué hipótesis existía;
- qué evidencia había;
- quién aprobó la decisión;
- qué ocurrió finalmente.

---

## P3

La integración nunca modifica el pipeline operacional.

Debe añadirse como una nueva capa.

---

## P4

El Scientific Layer jamás envía órdenes.

Sólo aprende.

---

## P5

Toda plataforma externa debe implementarse mediante adaptadores.

Nunca mediante lógica condicional distribuida.

---

## P6

La integración debe ser mantenible por una sola persona.

---

# 3. Decisión Arquitectónica V1.1

La arquitectura oficial queda actualizada de la siguiente forma.

## 3.1 Execution Engine como subsistema canónico

Execution Engine es el subsistema canónico de ejecución de O.M.A.-C.O.R.E.

Execution Engine owns:

- execution flow;
- portfolio;
- positions;
- orders;
- execution ledger;
- execution metrics.

Execution Engine consume únicamente decisiones ya aprobadas.

Execution Engine produce únicamente resultados de ejecución.

Execution Engine no decide, no evalúa, no puntúa, no aprende y no modifica conocimiento científico.

## 3.2 Integration Layer como infraestructura opcional

Integration Layer ya no posee la ejecución.

Integration Layer sólo proporciona conectividad opcional a plataformas externas futuras.

Su función futura será adaptar una instrucción de ejecución ya producida por Execution Engine hacia un entorno externo autorizado.

Integration Layer no forma parte de Sprint 15.

## 3.3 Brokers externos como extensiones futuras

Los brokers externos son extensiones futuras.

No son parte de la fundación del Execution Engine.

No son parte de Sprint 15A.

No son necesarios para completar el ciclo interno:

ApprovedDecision → ExecutionSignal → ExecutionResult → Outcome

## 3.4 TradingView deja de ser objetivo primario

TradingView ya no es el objetivo primario de integración.

TradingView puede permanecer como ejemplo conceptual de un adaptador futuro, pero no debe implementarse como parte de Sprint 15.

Ningún diseño de Sprint 15 debe depender de TradingView.

Ningún módulo de Sprint 15 debe contener lógica, nombres, dependencias o rutas específicas de TradingView.

---

# 4. Arquitectura General Revisada

La arquitectura revisada es:

Reality

↓

Collectors

↓

Event Bus

↓

Opportunity Engine

↓

Score Engine

↓

Council

↓

Approval Layer

↓

Execution Engine

↓

Execution Ledger

↓

Outcome Collector

↓

Scientific Bridge

↓

scientific.db

La Integration Layer queda fuera del flujo obligatorio.

Cuando exista una integración externa autorizada en el futuro, se conectará lateralmente al Execution Engine, no reemplazará al Execution Engine.

Flujo futuro opcional:

Execution Engine

↓

Integration Layer

↓

External Adapter

↓

External Broker or Platform

↓

Integration Layer

↓

Execution Engine

↓

Execution Ledger

Este flujo futuro opcional no está autorizado para Sprint 15.

---

# 5. Relación con Pipeline V2

`PIPELINE_V2.md` define el objeto canónico:

ApprovedDecision → ExecutionSignal → ExecutionResult → Outcome

Esta versión 1.1 asigna la propiedad de esos pasos internos.

## 5.1 Execution Laboratory

La capa Execution Laboratory queda representada internamente por Execution Engine cuando opera en modo SIMULATION.

Execution Engine transforma una decisión aprobada en una estructura interna de ejecución sin contactar brokers externos.

## 5.2 Execution

La capa Execution queda bajo propiedad de Execution Engine.

Execution Engine registra qué ocurrió dentro del entorno virtual interno.

## 5.3 Integration Layer

Integration Layer sólo existe como infraestructura opcional para futuros modos que requieran conectividad externa.

Integration Layer no es un requisito para producir ExecutionResult en modo SIMULATION.

---

# 6. Execution Engine

Execution Engine es el propietario canónico de la ejecución.

## 6.1 Responsabilidades

Execution Engine owns:

- execution flow;
- virtual portfolio;
- virtual positions;
- virtual orders;
- execution ledger;
- execution metrics;
- execution reports;
- execution summaries.

## 6.2 Entrada canónica

Execution Engine consume:

ApprovedDecision

No consume directamente:

- Event;
- OpportunityCandidate;
- EvaluatedOpportunity;
- raw score;
- unapproved Decision;
- hypotheses;
- Knowledge;
- Criterion.

## 6.3 Salida canónica

Execution Engine produce:

ExecutionResult

ExecutionResult es consumido posteriormente por Outcome Collector.

## 6.4 Responsabilidades prohibidas

Execution Engine nunca puede:

- puntuar oportunidades;
- modificar eventos;
- modificar hipótesis;
- modificar scientific.db;
- crear Knowledge;
- cambiar decisiones del Council;
- aprobar decisiones;
- aumentar autonomía;
- conectarse a brokers externos sin una arquitectura posterior explícita.

---

# 7. Componentes Internos del Execution Engine

Execution Engine queda compuesto por dominios internos separados.

## 7.1 Engine

Coordina el flujo interno de ejecución.

No contiene trading logic.

No contiene scoring.

No decide.

## 7.2 Portfolio

Representa el estado del portfolio virtual.

Incluye arquitectura para:

- virtual cash;
- virtual equity;
- buying power;
- realized pnl;
- unrealized pnl;
- portfolio statistics.

No calcula todavía.

## 7.3 Orders

Representa el dominio de órdenes internas.

Estados soportados:

- NEW;
- PENDING;
- FILLED;
- PARTIAL;
- CANCELLED;
- REJECTED;
- EXPIRED.

No ejecuta matching.

No contacta brokers.

## 7.4 Positions

Representa el dominio de posiciones virtuales.

Estados soportados:

- OPEN;
- CLOSING;
- CLOSED.

No calcula PnL todavía.

## 7.5 Ledger

Representa el historial inmutable de ejecución.

Toda operación realizada por Execution Engine debe eventualmente convertirse en un registro de ledger.

Ledger records son append-only.

Nada se elimina.

Nada se modifica.

Correcciones futuras deben registrarse como nuevos eventos de ledger, nunca como mutaciones.

## 7.6 Metrics

Representa placeholders para métricas futuras.

Ejemplos:

- Win Rate;
- Profit Factor;
- Expectancy;
- Average Win;
- Average Loss;
- Sharpe;
- Sortino;
- Maximum Drawdown;
- Recovery Factor.

No se implementan cálculos en Sprint 15A.

---

# 8. Execution Modes

Los modos canónicos de ejecución son:

- SIMULATION
- SHADOW
- PAPER
- LIVE

El modo por defecto es:

SIMULATION

## 8.1 SIMULATION

Modo interno primario.

No requiere broker externo.

No requiere Integration Layer.

No requiere credenciales externas.

Es el único modo dentro del alcance fundacional de Sprint 15A.

## 8.2 SHADOW

Modo futuro donde el sistema podría observar decisiones y comparar contra ejecución externa o contexto externo sin enviar órdenes.

No forma parte de Sprint 15A.

## 8.3 PAPER

Modo futuro donde el sistema podría comunicarse con un entorno externo de paper trading autorizado.

Requiere decisión arquitectónica posterior.

No forma parte de Sprint 15A.

## 8.4 LIVE

Modo futuro de capital real.

No autorizado.

Expresamente fuera de alcance.

Requiere evidencia, aprobación arquitectónica explícita y controles adicionales.

---

# 9. Integration Layer Revisada

Integration Layer es una capa opcional de infraestructura.

## 9.1 Responsabilidades permitidas futuras

Integration Layer podrá, cuando una arquitectura posterior lo autorice:

- conectar Execution Engine con plataformas externas;
- traducir instrucciones internas hacia formatos externos;
- traducir estados externos hacia resultados internos;
- aislar dependencias externas;
- mantener broker agnosticism;
- preservar trazabilidad.

## 9.2 Responsabilidades prohibidas

Integration Layer nunca puede:

- decidir;
- aprobar;
- puntuar;
- crear oportunidades;
- modificar señales aprobadas;
- modificar Knowledge;
- escribir directamente en scientific.db;
- reemplazar Execution Engine;
- convertirse en propietaria de portfolio, orders, positions, ledger o metrics.

## 9.3 Adaptadores externos

Todo broker externo futuro deberá implementarse mediante adaptadores.

Los adaptadores son future work.

No forman parte de Sprint 15.

TradingView, si reaparece, será sólo un ejemplo posible de adaptador futuro.

---

# 10. Identificadores y Trazabilidad

La trazabilidad completa sigue siendo obligatoria.

Execution Engine debe preservar los identificadores recibidos desde ApprovedDecision y generar los identificadores internos necesarios para ejecución.

Identificadores mínimos:

- event_id
- opportunity_id
- decision_id
- approval_id
- execution_signal_id
- order_id
- position_id
- trade_id
- execution_result_id
- outcome_id
- hypothesis_id cuando exista

Para integración externa futura podrán existir identificadores externos adicionales, como broker_order_id.

broker_order_id no es obligatorio en modo SIMULATION.

Cuando un identificador externo no exista por operar en SIMULATION, la ausencia debe ser explícita y trazable.

---

# 11. Estados de Ejecución

La máquina de estados de ExecutionSignal se mantiene compatible con Pipeline V2.

ExecutionSignal

CREATED

↓

VALIDATED

↓

APPROVED

↓

DISPATCHED

↓

ACKNOWLEDGED

↓

FILLED

↓

ACTIVE

↓

EXITING

↓

CLOSED

Estados alternativos:

- FAILED
- CANCELLED
- REJECTED

Nunca se permite volver a un estado anterior.

Toda transición debe quedar registrada en el Execution Ledger.

En modo SIMULATION, estos estados representan transición interna virtual, no interacción con broker externo.

---

# 12. Outcome Collector y Scientific Bridge

Outcome Collector sigue siendo downstream de Execution Engine.

Execution Engine produce ExecutionResult.

Outcome Collector transforma ExecutionResult en Outcome.

Scientific Bridge consume Outcome.

Scientific Layer aprende downstream.

Execution Engine no aprende.

Integration Layer no aprende.

Scientific Layer jamás envía órdenes.

---

# 13. Telemetría

La telemetría canónica debe separarse por propietario.

## 13.1 Execution Engine telemetry

Execution Engine puede registrar:

- tiempo hasta ejecución interna;
- duración de posición virtual;
- duración total;
- errores internos;
- reintentos internos si existieran en el futuro;
- heartbeat interno;
- ledger append status;
- portfolio state snapshot references.

## 13.2 Integration Layer telemetry futura

Integration Layer futura podrá registrar:

- latencia externa;
- latencia broker;
- latencia fill externa;
- errores externos;
- rate limits;
- authentication failures;
- external heartbeat.

Esta telemetría futura no forma parte de Sprint 15A.

---

# 14. Gestión de Errores

La clasificación obligatoria se mantiene.

Errores internos mínimos:

- INVALID_SIGNAL
- TIMEOUT
- UNKNOWN

Errores futuros de integración externa:

- NETWORK
- AUTH
- BROKER
- RATE_LIMIT
- MARKET_CLOSED

Nunca utilizar excepciones genéricas como resultado final.

En modo SIMULATION, errores externos no deben simular una dependencia real de brokers.

---

# 15. Configuración

La configuración de ejecución pertenece al Execution Engine.

Debe permitir representar:

- execution mode;
- default mode;
- internal execution settings;
- ledger settings;
- portfolio settings;
- metrics settings.

El modo por defecto debe ser SIMULATION.

La configuración de Integration Layer futura deberá estar separada de la configuración del Execution Engine.

Sprint 15A no implementa mode switching.

---

# 16. Seguridad

La seguridad canónica queda actualizada:

- SIMULATION es el modo primario.
- LIVE no está autorizado.
- PAPER externo no está autorizado para Sprint 15.
- SHADOW externo no está autorizado para Sprint 15.
- Ninguna ejecución puede ocurrir sin Approval Layer.
- Ninguna integración externa puede saltarse Execution Engine.
- Ningún broker puede modificar Decisions.
- Ningún broker puede modificar ApprovedDecisions.
- Ninguna ejecución puede modificar Knowledge.

Queda expresamente prohibido:

- capital real;
- auto-aprobación;
- autonomía adicional;
- ejecución sin Approval Layer;
- broker integration durante Sprint 15A;
- TradingView integration durante Sprint 15A.

---

# 17. Iteraciones Revisadas

## Sprint 15A

Execution Engine Foundation.

Incluye:

- estructura de carpetas;
- package initialization;
- skeletons mínimos;
- enums;
- schemas estructurales;
- exception hierarchy;
- configuración estructural;
- organización de tests.

No incluye:

- execution logic;
- trading algorithms;
- broker connectivity;
- external adapters;
- market APIs;
- integration layer implementation;
- CLI integration;
- Scientific Layer changes.

## Sprint 15B

Future internal execution coordination.

Scope exacto por definir después de Sprint 15A.

## Sprint 15C

Future internal monitor, order tracking, position tracking, and ledger evolution.

Scope exacto por definir después de Sprint 15B.

## Sprint 15D

Future outcome handoff from internal ExecutionResult to Outcome Collector.

Scope exacto por definir después de Sprint 15C.

## Sprint 15E

Future end-to-end validation in SIMULATION mode.

No capital real.

No external broker requirement.

---

# 18. Criterios de Aceptación Revisados

La arquitectura se considerará alineada cuando:

- Execution Engine sea el propietario claro de la ejecución;
- Integration Layer sea opcional y futura;
- Simulation sea el modo primario;
- Execution Engine preserve trazabilidad completa;
- Execution Engine produzca ExecutionResult;
- Outcome Collector permanezca downstream;
- Scientific Layer reciba Outcome downstream y no órdenes;
- ningún broker externo sea necesario para completar Sprint 15;
- TradingView no sea dependencia arquitectónica primaria;
- el sistema mantenga desacoplamiento total respecto a brokers externos.

---

# 19. Restricciones

No modificar durante Sprint 15A:

- Collectors;
- Pipeline;
- Council;
- Score Engine;
- Scientific Layer;
- Operational Database;
- Telegram;
- CLI;
- external integration modules.

No crear durante Sprint 15A:

- TradingView adapter;
- broker adapter;
- API integration;
- external execution;
- execution strategy;
- trading algorithm;
- automation beyond structure.

---

# 20. Definición de Éxito

El éxito de esta arquitectura NO es conectarse a brokers.

El éxito de esta arquitectura NO es ejecutar operaciones reales.

El éxito de esta arquitectura es establecer una frontera clara:

Approval Layer → Execution Engine → ExecutionResult → Outcome Collector → Scientific Layer

Execution Engine debe permitir que cada operación interna produzca un ciclo completo y auditable:

Evento → Decisión → Aprobación → Ejecución Interna → Resultado → Aprendizaje

Sólo cuando ese ciclo interno esté completamente operativo, probado y auditable podrá considerarse una futura integración externa.

La Integration Layer será entonces una extensión, no el núcleo de ejecución.
