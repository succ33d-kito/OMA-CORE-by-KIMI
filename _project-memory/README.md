# OSIRIS / O.M.A.-C.O.R.E.

**One Man Army — Create. Own. Run. Everything.**

A single-person intelligence engine that transforms global events into actionable opportunities across Trading, Entrepreneurship, and Content Creation.

## Core Pipeline

```
GLOBAL EVENT → WorldMonitorV2 → EventBus → Agent Swarm → Agent Council → Opportunity Engine → Profile Filter → Action
```

## Current Architecture

- **Collectors** (7): CoinGecko, YahooFinance, Binance, FRED, RSS (7 feeds), Sentiment (Fear & Greed), Polymarket — orchestrated by WorldMonitorV2
- **EventBus**: Pub/sub message bus, 10 topics, history buffer — the system's nervous system
- **Agent Swarm**: NewsAgent, MacroAgent — produce structured `AgentOpinion` objects via rule-based analysis
- **Agent Council**: Consensus engine — calculates conviction, consensus score, disagreement score — outputs `CouncilDecision`
- **MetaCouncil**: Cross-profile evaluator — scores every opportunity for Trader, Entrepreneur, and Creator value
- **Opportunity Engine**: 6-component weighted scoring (0-100), 24 opportunity types, 13 action templates with rationale
- **Memory Layer**: ShortTermMemory (TTL-expiring), LongTermMemory (tag-indexed), MemoryStore (event-keyed opinion cache)
- **User Profiles**: TraderPreferences, EntrepreneurPreferences, CreatorPreferences — typed, with sensible defaults
- **Action Layer**: Telegram notifications, CLI, 3 dashboard variants (Flask SPA, Render Flask, GitHub Pages static)
- **Database**: SQLite (local dev) + PostgreSQL (production on Render)

## How AI Should Help

1. **Architecture over code** — analyze the system first, propose, then implement. Never start with code.
2. **Structured communication** — agents use `AgentOpinion`/`CouncilDecision`, never free text
3. **Event-driven design** — new capabilities subscribe to EventBus topics; nothing is tightly coupled
4. **Profile-aware reasoning** — every opportunity has different value for Trader vs Entrepreneur vs Creator
5. **Project memory** — sync context to these files at the end of every session so the next AI handoff picks up without repeating work

## Links

- Live Dashboard: https://oma-core-by-kimi.onrender.com
- GitHub: https://github.com/succ33d-kito/OMA-CORE
- Technical Bible: OSIRIS Technical Bible v1 (see system prompt)

## Key Numbers

- ~5,000 lines of Python across 47 files
- 9 external API integrations
- 28 passing tests (ACP, EventBus, Council, Profiles, Memory)
- 1,571+ events collected, 195+ active opportunities (production)
