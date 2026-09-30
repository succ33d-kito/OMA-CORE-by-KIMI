# MM-H1: validación histórica BTCUSDT 2025

## Dictamen

No promover el filtro MM-H1 a la estrategia operativa. La hipótesis de mejora de entradas no queda respaldada en este ensayo: el retorno medio por trade fuera de muestra es peor, ambas variantes pierden tras costes y el filtro sólo produce 46 operaciones, por debajo del mínimo predefinido de 50. Esto no es una refutación estadística de todo Market Mechanics ni una evaluación del sistema OMA-CORE completo.

## Datos y procedimiento

8.760 velas horarias spot BTCUSDT, 1 enero–31 diciembre de 2025, descargadas de Binance Data Vision. Se verificaron los checksums SHA-256 de los 12 ZIP mensuales; el manifiesto registra las URLs, fechas de descarga y hashes. El validador comprobó continuidad horaria, unicidad, orden y coherencia de precios/volumen.

Desarrollo: primera partición del 60% después del calentamiento. Corte: 10 agosto de 2025 00:00 UTC. Embargo: 24 barras. Holdout: señales a partir del 11 agosto de 2025 00:00 UTC; las últimas señales sin horizonte completo se excluyen. Las barras anteriores al holdout se usan sólo como contexto causal, sin recalibración de umbrales.

Base: MarketAgent + RiskAgent + Council, sólo compras. Variante: mismas compras, con cierre por encima del rango previo y volumen relativo >= 1.5. Ejecución común: siguiente open, 20% de asignación, stop 2%, objetivo 4%, máximo 24 barras, una posición simultánea. Comisión 5 bps por lado y slippage 5 bps por lado. Son supuestos de simulación, no precios de ejecución garantizados.

## Resultados

| Partición | Variante | Trades | Retorno neto cartera | DD equity cerrada | Win rate | Media neta/trade | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| development | baseline | 238 | -5.318% | 9.258% | 44.12% | -0.1107% | 0.880 |
| development | mechanics_filter | 67 | -0.558% | 2.002% | 43.28% | -0.0381% | 0.953 |
| holdout | baseline | 151 | -10.221% | 10.546% | 41.72% | -0.3540% | 0.613 |
| holdout | mechanics_filter | 46 | -3.524% | 3.524% | 39.13% | -0.3870% | 0.580 |

El drawdown mostrado sólo se mide al cerrar trades; no incluye pérdidas flotantes intratrade. El rendimiento no está anualizado. No se deben mezclar estas cifras con métricas antiguas obtenidas con otra cartera, otro periodo, otra ejecución o información futura.

## Sensibilidad a costes en holdout

| Coste adicional por lado | Base: retorno neto | Filtro: retorno neto |
|---|---:|---:|
| 0 bps | -10.221% | -3.524% |
| 10 bps | -15.481% | -5.282% |
| 20 bps | -20.435% | -7.009% |

## Interpretación y aprendizaje

El filtro ejecutó cerca del 30% del número de operaciones de la base en holdout. Su menor pérdida agregada es compatible con menor actividad; no demuestra mejor selección. La media neta por operación y el profit factor son peores. La muestra no permite declarar un Edge validado.

El holdout 2025 ya ha sido observado y no debe reutilizarse como prueba independiente tras modificar el filtro. Cualquier nueva hipótesis deberá tener una versión y una muestra reservada distintas. No se modificaron automáticamente pesos ni Criterion a partir de estos resultados.

## Alcance pendiente

Este ensayo compara selección de entradas con ejecución común. Una comparación del runtime completo requiere reproducir guardas, reloj, sizing, shorts, cartera multiactivo y aprendizaje adaptativo de ambas versiones. La rentabilidad de las versiones completas sigue sin establecerse con esta prueba.

## Reproducción

```bash
python scripts/download_btc_2025.py
python scripts/compare_market_mechanics.py --input research/data/BTCUSDT_1h_2025.json --symbol BTC --source binance:spot:BTCUSDT:1h:archive:2025 --output research/mm_h1_btc_2025.json
```

Incluidos: dataset normalizado, manifiesto de integridad, protocolo MM-H1-v1, candidatos y operaciones completos, sensibilidad a costes. La suite del comparador previamente ejecutada terminó en 954 passed, 12 skipped; el downloader fue ejecutado con los doce archivos reales y sus checksums.
