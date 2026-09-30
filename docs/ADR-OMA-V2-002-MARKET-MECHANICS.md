# ADR OMA-V2-002 — Market Mechanics v1

Estado: implementada como observación auditable para la demo paper, 2026-09-29.

## Capacidad

`core/market_mechanics/state.py` transforma barras OHLCV cerradas y validadas en un `MarketState` inmutable. La demo lo crea antes del análisis de agentes y lo adjunta íntegro al DecisionRecord junto con su ID. Este corte establece datos reproducibles para evaluación posterior; no demuestra rentabilidad ni modifica pesos de Council con estos indicadores.

## Datos y reloj

Cada lote tiene fuente, símbolo, temporalidad, instante de recepción (`observed_at`) e instante de evaluación (`as_of`). La hora de apertura más la duración define el cierre exclusivo de una vela. La demo descarta la vela abierta; el constructor rechaza velas abiertas/futuras, tiempos sin zona, duplicados, huecos, desorden, valores no finitos, volumen negativo y OHLC incoherente. Exige 21 barras para lookback 20. El último cierre no puede superar dos intervalos de antigüedad. La disponibilidad del lote se fija en su recepción; no se presupone que estuvo disponible históricamente al cierre.

Una actualización fallida elimina el precio cacheado de ese símbolo. Si faltan datos actuales, se retrasa la evaluación de cierres; no se inventa una ejecución ni se imputa un precio anterior como actual. La demo continúa usando cierres horarios como precios de simulación: no ofrece precisión intrabar ni certifica precios de ejecución reales.

## Métricas v1

| Campo | Definición |
|---|---|
| `last_return` | Último cierre dividido por cierre anterior, menos uno. |
| `prior_high`, `prior_low` | Máximo high y mínimo low de las 20 barras anteriores; excluyen la última. |
| `range_status` | Cierre encima, debajo o dentro del rango previo; una igualdad se considera dentro. |
| `volume_ratio` | Volumen de última barra dividido por media de las 20 anteriores; `null` si la media es cero. |
| `return_volatility` | Desviación estándar muestral de 20 retornos simples, por barra y sin anualizar. |

No se deduce causalidad, identidad de participantes, absorción ni órdenes agresoras de estas métricas. Las dimensiones desconocidas son order_flow, resting_liquidity, positioning, derivatives, capital_flow y execution_depth.

## Persistencia y aprendizaje

El estado conserva todas las barras de entrada como tuplas (time, open, high, low, close, volume), el hash de datos, el lookback y la versión del algoritmo. El ID incorpora fuente, reloj, parámetros e inputs. El DecisionRecord contiene el JSON completo, evitando referencias a una instantánea que no esté almacenada. La evidencia científica validada permanece vacía cuando no existe; una observación de mercado no la sustituye.

El cierre paper ya se vincula a la decisión, de modo que el par snapshot → resultado puede utilizarse en investigación. No hay todavía extracción de conocimiento ni actualización automática de Criterion desde estos campos. El siguiente paso científico es evaluar hipótesis previamente definidas con particiones temporales, costes y comparación contra una referencia.

## Validación

Tests numéricos de rango/volumen/volatilidad; rechazo de datos futuros y malformados; cero volumen; antigüedad; snapshot persistido y desacoplado de la lista mutable original; filtro de vela abierta y eliminación de precios cacheados en demo. El test de disponibilidad es causal en el reloj de entrada: no atribuye capacidades predictivas a la correlación.
