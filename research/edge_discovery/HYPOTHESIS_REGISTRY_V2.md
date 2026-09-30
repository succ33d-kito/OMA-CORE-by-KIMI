# Hypothesis Registry V2 — diseño experimental, 2026-09-30

Estado: CONCEPTUAL / NOT_EVALUATED / NO_PROMOTION. Este registro no es un freeze
formal de una hipótesis ni una autorización para abrir holdouts.

Principio: **ΔEdge > ΔComplexity**. Ejes: Price + OI + Aggressor Flow + Funding +
Positioning + Regime. No se identifica a participantes individuales con datos
agregados. Las relaciones observadas no establecen causalidad.

| Familia | Clasificación candidata | Límite de interpretación |
|---|---|---|
| Long Initiation | Precio sube, OI aumenta, agresión compradora | Cada contrato tiene contraparte; no demuestra quién inicia |
| Short Initiation | Precio baja, OI aumenta, agresión vendedora | Mismo límite de identificación |
| Short Covering | Precio sube y OI disminuye | Compatible con cierre de shorts; no lo identifica |
| Long Unwind | Precio baja y OI disminuye | Compatible con cierre de longs; no lo identifica |
| Buy/Sell Pressure without proportional Price Response | Flujo agresor elevado y respuesta de precio reducida | Primitive Effort → Price Response; NO absorción demostrada |
| Crowding | Concentración de positioning y funding, condicionada al régimen | Ratios públicos son muestras/proxies de población; no inventar microestructura |
| Flow Acceleration | Cambio causal de intensidad/imbalance | Comparar sólo con historial disponible; no percentiles futuros |
| Flow Exhaustion | Desaceleración de flujo después de expansión | No implica reversión ni agotamiento causal probado |

Participant State: Initiation → Expansion → Crowding → Exhaustion → Unwind es
una clasificación experimental. No es una máquina causal validada ni una
secuencia obligatoria del mercado. Estado desconocido permanece desconocido.

Effort: volumen agresor firmado, imbalance y registros aggTrades por segundo.
El span de IDs individuales es sólo diagnóstico: no reproduce el conteo oficial
y no se usa como estimador de intensidad ni tamaño medio individual. Response:
retorno/rango del mismo intervalo cerrado, con escala basada sólo en pasado.
Esto clasifica observaciones; la respuesta futura sería una variable dependiente
separada. Evitar divisiones inestables cuando el movimiento de precio es cero.
No se fijan thresholds después de observar un holdout.

## Orden de ablation propuesto

1. Baseline de precio/régimen existente, mismo universo y ventana temporal.
2. Añadir Price × ΔOI; comparar contra el baseline con soporte común.
3. Añadir agresión observada; después intensidad y Effort → Price Response,
   una primitive por contraste y sin búsqueda combinatoria de umbrales.
4. Añadir funding y positioning sólo donde su disponibilidad esté acreditada.
5. Probar estados de participantes sólo si las capas anteriores añaden información.

Antes de ejecutar: registrar fórmula, horizonte primario, familia completa de
comparaciones, comparador, costes, tamaño mínimo, missingness, purga/embargo y
criterios de supervivencia/falsación. Reutilizar inferencia por bloques de
calendario; controlar multiplicidad de todas las alternativas probadas. Evaluar
incremento fuera de muestra dentro de discovery, estabilidad temporal, soporte,
costes y sensibilidad; una celda significativa no basta.

No se ha ejecutado esta ablation: Data Gate estricto FAIL. Ninguna familia
sobrevivió ni fue falsada en este corte; todas siguen NOT_EVALUATED. Las 51
comparaciones mencionadas en el contexto anterior carecen aquí de un protocolo
y artefactos identificados suficientes para una reproducción: no se inventan.

## Barreras obligatorias

- Binance 2024: discovery exclusivamente.
- Binance 2025: cerrado hasta freeze formal nuevo. Exposición histórica previa
  consta en el repositorio; no presentarlo como holdout nunca visto.
- Kraken XBTUSD Spot H1 Q2-2026: SEALED_CROSS_EXCHANGE_HOLDOUT, sin abrir ahora.
  La existencia de análisis Kraken previos impide asumir independencia sin
  auditar después sus ventanas; no se inspeccionan outcomes para resolverlo.
- Sin retuning sobre holdouts ni sustitutos sintéticos de microestructura.
- Incomplete provenance => NO LEARNING.
- Unvalidated Knowledge => NO Criterion update.
- Promoción deshabilitada hasta integrar lineage verificada, replicación
  independiente y recibos verificables de gates científicos.
