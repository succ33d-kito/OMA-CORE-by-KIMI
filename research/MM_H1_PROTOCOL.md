# MM-H1-v1 — Protocolo previo de comparación

Fecha: 2026-09-29. Estado: hipótesis fijada; sin evidencia histórica suficiente.

## Hipótesis falsable

En señales de compra de MarketAgent + RiskAgent + AgentCouncil, exigir cierre por encima del máximo de las 20 velas previas y volumen >= 1.5 veces la media de esas velas mejora el retorno neto por trade fuera de muestra, sin empeorar el drawdown de equity al cierre.

H0: el filtro no produce esa mejora. Los umbrales no se optimizan en el holdout. Una modificación de parámetros requiere nueva versión de protocolo y un periodo futuro no utilizado. El estado observado de Market Mechanics v1 por sí solo no altera señales: la diferencia experimental es este filtro explícito.

## Comparación controlada

| Elemento | Regla común |
|---|---|
| Señal base | Agentes Market y Risk originales y Council con pesos iniciales fijos; BUY/STRONG_BUY. |
| Universo inicial | BTC, datos spot horarios; sólo largos; un activo por ejecución. |
| Información | Ventana de 120 barras cerradas, incluida la barra de señal. |
| Entrada | Open de la siguiente barra con slippage adverso. |
| Posición | 20% del equity; una posición simultánea; sin apalancamiento. |
| Stop / target | 2% / 4% del precio de entrada ejecutado. |
| Salida temporal | Cierre de la barra 24 desde entrada. |
| Costes base | Comisión 5 bps por lado y slippage 5 bps por lado; supuestos, no tarifa verificada. |
| Stop y target en misma barra | Stop primero, interpretación conservadora. |
| Gap bajo stop | Salida al open inferior, con slippage. |
| División | 60% desarrollo, embargo de 24 barras, resto holdout; 120 barras iniciales de contexto. |
| Bordes | No iniciar operaciones sin horizonte completo dentro de la partición. |

Es una ablación de selección de entradas, **no una réplica económica completa del runtime anterior**: no reproduce CapitalGuard dinámico, short, online learning, cartera multiactivo, todos los costes de microestructura ni ejecución intrabar. El sistema actual de demo sigue sin usar este filtro en producción.

## Sesgo encontrado en validaciones previas

`scripts/run_validation.py` y `scripts/reality_test.py` entregan a agentes la serie completa mientras iteran eventos históricos. Sus resultados no sirven como baseline limpio de esta prueba. `core/scientific/mechanics_comparison.py` recorta estrictamente el input hasta cada barra de decisión. Una prueba cambia toda la cola futura y exige igualdad de los candidatos anteriores.

## Métricas y límites

Se reportan cantidad de operaciones, retorno de cartera neto, media de retorno neto por trade, win rate, profit factor y drawdown de equity **sólo al cierre**. El último no mide pérdidas flotantes intratrade. Profit factor sin pérdidas y métricas sin operaciones se expresan como null; no se declara rentabilidad infinita. Los resultados incluyen todas las operaciones, candidatos, hash de input y versión/parámetros del protocolo.

Menos de 50 operaciones por variante en holdout implica muestra insuficiente para promover la hipótesis. Superar ese número tampoco prueba un Edge. Antes de promover: sensibilidad a costes (10/20 bps adicionales por lado), periodos y regímenes independientes, intervalos de incertidumbre con bloques temporales, control del número de variantes probadas y paper prospectivo. No se autoriza capital real por pasar esta comparación.

## Uso

Smoke test exclusivamente sintético:

```bash
python scripts/compare_market_mechanics.py --synthetic-smoke --output research/mm_h1_smoke.json
```

Datos históricos provistos como array JSON: `time` ISO UTC de apertura, `open`, `high`, `low`, `close`, `volume`; barras horarias contiguas y cerradas:

```bash
python scripts/compare_market_mechanics.py --input history.json --symbol BTC --source exchange:spot:BTC:1h --output research/mm_h1_historical.json
```

El usuario debe conservar procedencia, fecha de descarga y confirmar que no hay datos sintéticos o revisados dentro de `history.json`. Una etiqueta `historical` no certifica autenticidad por sí sola. En esta sesión la descarga Binance respondió HTTP 451. El fixture sintético sólo valida software y sus métricas no constituyen evidencia de rendimiento.

## Evidencia de software de esta entrega

`python -m pytest tests -q`: **954 passed, 12 skipped, 3 warnings** en 73.70s. La ejecución sintética de 720 barras está en `research/mm_h1_smoke.json`. La comparación histórica permanece pendiente por falta de un dataset real accesible. No hay conclusión de superioridad entre versiones del sistema.
