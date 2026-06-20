#!/usr/bin/env python3
"""
O.M.A.-C.O.R.E. — Entry Point
=============================
One Man Army — Create. Own. Run. Everything.

Usage:
    python oma.py <command> [options]

    Commands:
        collect         Recolectar datos de fuentes
        process         Procesar eventos pendientes
        run             Ciclo completo (collect + process)
        watch           Monitoreo continuo
        opportunities   Ver oportunidades activas
        events          Ver eventos recientes
        status          Estado del sistema
        export          Exportar datos

Examples:
    python oma.py collect
    python oma.py process --min-score 50
    python oma.py run --min-score 40 --limit 15
    python oma.py watch --interval 300
    python oma.py opportunities --limit 20
