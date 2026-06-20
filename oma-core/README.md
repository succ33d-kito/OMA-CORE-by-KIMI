# O.M.A.-C.O.R.E.

**One Man Army — Create. Own. Run. Everything.**

Plataforma de inteligencia operativa que transforma información global en oportunidades accionables para traders, creadores y emprendedores.

## Arquitectura

```
O.M.A.-C.O.R.E.
│
├── World Monitor      → Recolección de datos (CoinGecko, Yahoo Finance, RSS, GDELT)
├── Event Processor    → Normalización y clasificación
├── Score Engine       → Puntuación heurística de eventos
├── Opportunity Engine → Generación de oportunidades accionables
├── Action Layer       → CLI con visualización rica
└── Memory (SQLite)    → Almacenamiento local
```

## Instalación

```bash
git clone <repo-url>
cd oma-core
pip install -r requirements.txt
```

## Uso

```bash
# Ciclo completo: recolectar + procesar
python -m core.cli.main run

# Monitoreo continuo (cada 5 minutos)
python -m core.cli.main watch --interval 300

# Ver oportunidades
python -m core.cli.main opportunities --limit 20

# Estado del sistema
python -m core.cli.main status
```

## Fuentes de datos

| Fuente | Tipo | Costo |
|--------|------|-------|
| CoinGecko API | Crypto precios/volumen | Gratuito |
| Yahoo Finance | Stocks, Forex, Commodities | Gratuito |
| RSS Feeds | Noticias financieras | Gratuito |
| GDELT v2 | Eventos globales | Gratuito |

## Roadmap

- [x] Event Schema
- [x] Database Layer (SQLite)
- [x] World Monitor (Collectors)
- [x] Score Engine (Heurístico)
- [x] Opportunity Engine
- [x] CLI Interface
- [ ] Agent Swarm (Market, News, Sentiment)
- [ ] User Profile Engine
- [ ] OSIRIS Integration
- [ ] Local LLM for enrichment

## Licencia

MIT
