# INTEGRATION_ARCHITECTURE_V1.md

**Proyecto:** O.M.A.-C.O.R.E.

**Versión:** 1.0

**Estado:** CANONICAL SPECIFICATION

**Fecha:** Junio 2026

---

# 1. Propósito

Este documento define la arquitectura oficial para integrar O.M.A.-C.O.R.E. con plataformas externas de ejecución, comenzando por TradingView Paper Trading.

La integración NO tiene como objetivo aumentar la autonomía del sistema.

Su objetivo es conectar el motor de decisión existente con un entorno de ejecución controlado para obtener evidencia real que alimente el Scientific Layer.

Esta arquitectura debe cumplir cuatro objetivos:

* desacoplar completamente la lógica de decisión de cualquier plataforma externa;
* preservar la trazabilidad completa desde un evento hasta un resultado;
* alimentar automáticamente el ciclo científico;
* permitir futuras integraciones sin modificar el núcleo del sistema.

Este documento es canónico. Ninguna implementación debe desviarse de él sin una decisión arquitectónica explícita.

---

# 2. Principios

La implementación debe respetar obligatoriamente los siguientes principios.

## P1

O.M.A.-C.O.R.E. toma decisiones.

Los brokers únicamente ejecutan.

Nunca al revés.

---

## P2

Toda decisión debe ser reconstruible.

Debe poder responderse:

* qué evento la originó;
* qué hipótesis existía;
* qué evidencia había;
* quién aprobó la decisión;
* qué ocurrió finalmente.

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

# 3. Arquitectura General

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

Signal Dispatcher

↓

Execution Adapter

↓

TradingView Paper Trading

↓

Execution Monitor

↓

Outcome Collector

↓

Scientific Bridge

↓

scientific.db

---

# 4. Nuevo módulo

Crear:

core/integration/

Submódulos:

adapters/

dispatcher/

monitoring/

bridge/

schemas/

config/

Nunca añadir esta lógica dentro de execution/.

---

# 5. Dispatcher

Responsabilidad única:

recibir una señal aprobada y enviarla al adaptador correspondiente.

No contiene reglas de negocio.

No conoce TradingView.

Trabaja exclusivamente contra la interfaz ExecutionAdapter.

---

# 6. ExecutionAdapter

Todos los adaptadores deberán implementar exactamente la misma interfaz.

Métodos mínimos:

connect()

disconnect()

health()

send_order()

cancel_order()

close_position()

sync_orders()

sync_positions()

get_orders()

get_positions()

Ningún adaptador podrá añadir lógica de decisión.

---

# 7. TradingView Adapter

Responsabilidades:

traducir ExecutionSignal al formato requerido por TradingView;

enviar órdenes;

consultar estados;

obtener posiciones;

obtener resultados.

No calcula riesgo.

No modifica señales.

No interpreta mercado.

---

# 8. Approval Layer

Nueva capa situada entre Council y Dispatcher.

Estados posibles:

APPROVED

REJECTED

MANUAL_REVIEW

Validaciones mínimas:

score

conviction

riesgo

cooldown

capital

duplicados

mercado abierto

calidad de datos

calidad científica

La capa Approval no ejecuta órdenes.

---

# 9. Máquina de Estados

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

FAILED

CANCELLED

REJECTED

Nunca se permite volver a un estado anterior.

Toda transición queda registrada.

---

# 10. Identificadores

Cada operación deberá mantener trazabilidad completa.

event_id

opportunity_id

decision_id

approval_id

signal_id

broker_order_id

position_id

trade_id

outcome_id

hypothesis_id

Todos deben persistirse.

---

# 11. Outcome Collector

Cuando una operación finalice deberá registrarse:

precio entrada

precio salida

duración

PnL

MAE

MFE

slippage

fees

motivo de cierre

timestamp

No interpreta resultados.

Sólo registra.

---

# 12. Scientific Bridge

Una vez registrado el resultado:

Outcome

↓

Hypothesis

↓

Evidence

↓

Outcome Comparison

↓

Knowledge

↓

Criterion Delta

La integración nunca modifica el Operational DB.

Scientific utiliza exclusivamente scientific.db.

---

# 13. Telemetría

Registrar:

tiempo hasta aprobación

tiempo hasta envío

latencia broker

latencia fill

duración posición

duración total

errores

reintentos

heartbeat

Toda la telemetría será utilizada posteriormente para análisis científico.

---

# 14. Gestión de Errores

Clasificación obligatoria.

NETWORK

AUTH

BROKER

TIMEOUT

RATE_LIMIT

INVALID_SIGNAL

MARKET_CLOSED

UNKNOWN

Nunca utilizar excepciones genéricas como resultado final.

---

# 15. Configuración

Archivo:

config/integration.yaml

Debe permitir:

adaptador activo

modo

timeouts

heartbeat

retry

logging

sin modificar código.

---

# 16. Seguridad

Esta integración queda limitada a:

Paper Trading.

Queda expresamente prohibido:

capital real;

auto-aprobación;

autonomía adicional;

ejecución sin Approval Layer.

---

# 17. Iteraciones

## Sprint 15A

Estructura de carpetas.

Interfaces.

Schemas.

Configuración.

Sin lógica.

---

## Sprint 15B

Dispatcher.

ExecutionAdapter.

TradingViewAdapter simulado.

---

## Sprint 15C

Execution Monitor.

Order Tracker.

PnL Tracker.

---

## Sprint 15D

Outcome Collector.

Scientific Bridge.

---

## Sprint 15E

Pruebas completas.

Integración end-to-end.

Sin capital real.

---

# 18. Criterios de aceptación

La arquitectura se considerará completada cuando:

* el pipeline pueda enviar una señal a TradingView Paper Trading;
* la operación pueda abrirse y cerrarse correctamente;
* todos los estados queden registrados;
* el resultado se almacene automáticamente;
* el Scientific Layer reciba la información necesaria para iniciar el aprendizaje;
* el sistema mantenga el desacoplamiento total respecto a TradingView.

---

# 19. Restricciones

No modificar:

Score Engine.

Council.

Collectors.

Scientific Layer.

Pipeline.

Operational Database.

La integración deberá añadirse como una capa nueva.

---

# 20. Definición de éxito

El éxito de esta arquitectura NO es ejecutar más operaciones.

El éxito consiste en que cada operación ejecutada produzca un ciclo completo y auditable:

Evento → Decisión → Aprobación → Ejecución → Resultado → Aprendizaje.

Sólo cuando ese ciclo esté completamente operativo podrá considerarse finalizada la integración y autorizarse la siguiente fase del proyecto.
