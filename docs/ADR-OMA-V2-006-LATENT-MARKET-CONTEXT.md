# ADR-OMA-V2-006 — Latent Market Context

## Status
Accepted as an experimental data contract. No Edge promotion.

## Problem
OHLCV regime labels show weak longitudinal transportability. Adding more price-derived labels risks feature proliferation without identifying the state variables that cause conditional effects to change.

## Decision
OMA-CORE will model externally observed market state separately from price-derived context. The first contract supports open-interest change, funding, long/short ratio, liquidation imbalance, taker imbalance and spot netflow. Missing dimensions remain explicitly unknown.

## Causality
Every observation carries an `observed_at` timestamp and source provenance. Values unavailable at decision time are rejected. No retrospective publication may be treated as contemporaneously known.

## Provider independence
Core semantics do not depend on Binance, Kraken, CoinGlass or another vendor. Adapters map provider schemas into the canonical contract.

## Promotion
No latent feature becomes Criterion/Knowledge because it improves an in-sample backtest. It must clear longitudinal, uncertainty, execution and prospective gates.
