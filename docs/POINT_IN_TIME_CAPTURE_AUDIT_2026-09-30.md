# Auditoría focalizada previa a cambios

Base verificada: main/f8b967a; working tree limpio y checker del freeze intacto.

El capturador existente usa Binance USD-M REST `/fapi/v1/klines` H1 y cinco
endpoints de métricas. Toma el reloj UTC local antes de las peticiones para
seleccionar una vela cerrada. Binance entrega open_time y close_time; el
adaptador sólo conserva open_time y OHLCV. El writer asigna UTC local al grabar,
no al recibir la respuesta, y exporta ese valor como available_at.

Reutilizable: SQLite WAL/FULL, transacciones, cadena SHA-256, serialización
determinista, rechazo de backfill de más de un día, exportación verificada.
Reinicio preserva filas/cadena. UNIQUE(kind,source_at) detecta duplicados pero
no distingue instrumento ni devuelve idempotentemente el primer recibo.

Gaps concretos: payload bruto de precio descartado; se guardan raw metrics pero
no raw klines. No hay evidencia de cierre independiente del reloj local,
instrumento explícito, received_at separado de available_at, computed_at,
dependencias o validator central de admisibilidad. El hash detecta cambios pero
no autentica al proveedor ni prueba sincronización del reloj. El collector de
precio depende innecesariamente del éxito de todos los endpoints métricos.

Intervención acotada: ampliar el mismo módulo/archivo SQLite con tabla versionada
de observaciones (sin migrar ni reinterpretar recibos legacy), primitive común
y captura price-only en el adaptador existente. REST se admitirá sólo con una
consulta previa de hora de Binance que demuestre que el intervalo terminó antes
de solicitar klines; conservar close_time original y ambas respuestas. Sin
atribuir al REST el flag de cierre propio de WebSocket. Reloj local UTC como
dominio de recepción/decisión; rechazo de incoherencias temporales observables.
