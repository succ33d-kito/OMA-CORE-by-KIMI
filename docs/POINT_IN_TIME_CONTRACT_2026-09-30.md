# Point-in-Time Observation Contract v1

Base: main/f8b967a. Auditoría previa en `POINT_IN_TIME_CAPTURE_AUDIT_2026-09-30.md`.
Se extienden `prospective_receipts.py` y el adaptador Binance existentes. Tabla
`observations_v2` en el mismo archivo SQLite que acepta receipts legacy; éstos
no se reinterpretan ni se exportan como si cumplieran este nuevo contrato.

## Timestamps y confianza

- `event_time`: evento/fin exclusivo del intervalo según la fuente. Para Price
  H1: open_time + 1 h. No implica que OMA ya hubiera recibido la vela.
- `source_metric_at`: timestamp original de cierre Binance, inclusive, conservado
  separado del fin exclusivo. También se preservan los milisegundos originales.
- `received_at`: UTC local capturado inmediatamente después de consumir la
  respuesta HTTP completa. No se usa el reloj tomado antes de la petición.
- `available_at`: límite conservador de disponibilidad demostrada, asignado por
  el writer tras normalización/validación; nunca aceptado como argumento externo.
- `computed_at`: límite conservador al terminar/registrar una derivación en el
  writer. La disponibilidad derivada es max(dependencias, computed_at).
- `decision_at`: lectura UTC independiente posterior, dada al gate. No se
  fabrica a partir del tiempo fuente. Si alguna dependencia falta o tiene
  available_at UNKNOWN, el resultado derivado conserva UNKNOWN.

Dominio de confianza explícito: código de captura, TLS y reloj UTC del host.
Se rechazan timestamps naive, regresiones observables y tiempo del servidor
posterior a la recepción local. No se afirma sincronización NTP certificada,
autenticación criptográfica de respuestas ni defensa frente a un host malicioso.
Clock injection es para tests; los CLI reales usan UTC del sistema. Para una
decisión en otro host se necesita acreditar compatibilidad de relojes.

## Cierre H1 y provenance

El REST no suministra el flag `x` de WebSocket. Se consultan en orden:
`/fapi/v1/time` y `/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=3`.
Se elige la última vela cuyo fin exclusivo no supera la hora del servidor
observada **antes** de pedir klines. Se verifica close_time=open+1h−1ms,
alineación H1, OHLCV válido, instrumento/fuente y orden de recepción/petición.
`bar_closed=true` describe esta prueba REST, no un campo inventado del proveedor.
Se guardan ambas respuestas brutas y los campos normalizados; el gate vuelve a
comprobar su correspondencia. Las demás filas de la respuesta no son inputs.
Semántica oficial: [Binance market data REST](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

El gate sólo acepta IDs presentes en el ledger verificado. Rechaza provenance
ausente/inválida, payload alterado, intervalos abiertos, futuro, receipts tardíos,
dependencias ausentes/no admisibles o de otro instrumento. UNKNOWN siempre es
inadmisible. La disponibilidad no prueba exactitud económica, Edge ni validez
de una hipótesis; no alimenta Knowledge/Criterion.

## Persistencia

JSON canónico, identidad determinista de fuente/instrumento/feature/timestamps/
dependencias, hash del payload y cadena de recibos. SQLite WAL/FULL y transacción
atómica. Triggers rechazan UPDATE/DELETE en esta tabla. Duplicado con mismo
payload devuelve el primer receipt sin cambiar provenance; payload diferente
bajo la misma identidad falla, sin sobrescritura. No se admite backfill de más
de un día como receipt prospectivo. Un receipt actual nunca acredita 2024.

Hash chaining detecta modificación de registros, no protege de un atacante que
reescriba toda la base o restaure un prefijo válido. El reporte versionado deja
un ancla externa del receipt observado; backup/replicación continua queda fuera
del alcance. Reinicio y replay se verificaron sin alterar provenance.

Source/instrument/feature/payload/provenance permiten representar posteriormente
OI, AF, Positioning y Funding. Sin sus contratos específicos, las observaciones
raw distintas de Price quedan UNKNOWN. No se añadieron collectors para ellas.
La primitive derivada valida disponibilidad de dependencias, no la verdad de
la fórmula o del valor que aporta el productor confiable.

## Evidencia y revisión nueva

`research/edge_discovery/price_point_in_time/PROBE.json` conserva una prueba real
de 2026-09-30. Available_at: **18:14:57.387351 UTC**. Decision_at:
**18:14:57.401121 UTC**. Recepción menos close_time: **897,361120 s** (una muestra,
incluye polling REST; no es estimación de latencia de publicación del exchange).
La recarga del ledger reprodujo exactamente la observación y el gate pasó.
La evidencia es de ese receipt individual, no de captura continua ni de 2024.

Nueva revisión: `PIT_PRICE_RECEIPTS_V1_2026_09_30`, ligada por hashes al probe,
código y freeze previo. El freeze Mechanics v2.1 anterior está intacto:
Data Gate histórico FAIL, ALLOWED=[], READY=0, BLOCKED=10. Regime no acreditado;
no existe aún ventana real de 81 barras con provenance. Sin outcomes ni holdouts.

## Reproducción mínima

```text
python -m pytest tests/test_point_in_time_observations.py tests/test_prospective_receipts.py tests/test_binance_live_adapter.py tests/test_mechanics_v2_1_freeze.py -q
python scripts/probe_price_point_in_time.py --ledger EXTERNAL_PROSPECTIVE/receipts.db --report EXTERNAL_PROSPECTIVE/new_probe.json
```

Resultado de tests: 22 pasando. Sólo se amplió la verificación a consumers del
módulo compartido y al freeze. No se repitió la suite amplia, datasets ni
experimentos. El CLI consulta dos endpoints públicos, sin keys, retries,
proxy, scheduler, métricas ni órdenes; si no puede demostrar la captura informa
LIVE NOT VERIFIED y sale con código 2. Usar un reporte nuevo preserva la prueba
anterior. El ledger externo no se sube a Git; el receipt de muestra es pequeño.

Siguiente acción única: establecer captura periódica sólo de Price para reunir
81 barras H1 consecutivas con receipts, sin ejecutar Mechanics/hipótesis todavía.
