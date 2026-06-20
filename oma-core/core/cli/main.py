"""
O.M.A.-C.O.R.E. — CLI Interface
=================================
Interfaz de línea de comandos para operar el sistema.
Visualización rica de oportunidades y eventos.

Comandos:
    oma collect     — Recolectar datos de todas las fuentes
    oma process     — Procesar eventos pendientes
    oma status      — Ver estado del sistema
    oma opportunities — Ver oportunidades activas
    oma events      — Ver eventos recientes
    oma watch       — Modo monitoreo continuo
    oma export      — Exportar datos a JSON/CSV
"""

import argparse
import json
import csv
import time
import sys
from datetime import datetime
from typing import List, Dict, Any

from core.database.db import OMACoreDatabase
from core.collectors.world_monitor import WorldMonitor
from core.engines.score_opportunity import Pipeline


class Colors:
    """Códigos ANSI para colores en terminal"""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class OMACLI:
    """Interfaz CLI principal"""

    def __init__(self, db_path: str = "oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.pipeline = Pipeline(db_path)
        self.monitor = WorldMonitor()

    def print_banner(self):
        """Imprime banner de inicio"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
 ██████  ███    ███  █████      ██████  ██████  ██████  ███████ 
██    ██ ████  ████ ██   ██    ██      ██    ██ ██   ██ ██      
██    ██ ██ ████ ██ ███████    ██      ██    ██ ██████  █████   
██    ██ ██  ██  ██ ██   ██    ██      ██    ██ ██   ██ ██      
 ██████  ██      ██ ██   ██     ██████  ██████  ██   ██ ███████ 
{Colors.END}
{Colors.YELLOW}  One Man Army — Create. Own. Run. Everything.{Colors.END}
{Colors.GREEN}  Intelligence Engine v1.0 — Trading Focus{Colors.END}
{Colors.BLUE}  ─────────────────────────────────────────{Colors.END}
        """
        print(banner)

    def print_opportunity(self, opp: Dict[str, Any], index: int = 0):
        """Imprime una oportunidad formateada"""
        # Color según prioridad
        priority_colors = {
            "CRITICAL": Colors.RED + Colors.BOLD,
            "HIGH": Colors.YELLOW + Colors.BOLD,
            "MEDIUM": Colors.CYAN,
            "LOW": Colors.BLUE
        }

        # Color según score
        score_color = Colors.GREEN if opp["score"] >= 70 else Colors.YELLOW if opp["score"] >= 50 else Colors.BLUE

        # Color según riesgo
        risk_colors = {
            "VERY_HIGH": Colors.RED + Colors.BOLD,
            "HIGH": Colors.RED,
            "MEDIUM": Colors.YELLOW,
            "LOW": Colors.GREEN
        }

        p_color = priority_colors.get(opp["priority"], Colors.END)
        r_color = risk_colors.get(opp["risk_level"], Colors.END)

        print(f"""
{Colors.BOLD}[{index}] {p_color}[{opp["priority"]}]{Colors.END} {opp["title"]}{Colors.END}
{Colors.BLUE}   ├─ Score:{Colors.END} {score_color}{opp["score"]}/100{Colors.END} | {Colors.BLUE}Convicción:{Colors.END} {opp["conviction"]}/100
{Colors.BLUE}   ├─ Tipo:{Colors.END} {opp["opportunity_type"]} | {Colors.BLUE}Assets:{Colors.END} {', '.join(opp["assets"]) if opp["assets"] else 'N/A'}
{Colors.BLUE}   ├─ Riesgo:{Colors.END} {r_color}{opp["risk_level"]}{Colors.END} | {Colors.BLUE}Fuente:{Colors.END} {opp["source"]}
{Colors.BLUE}   ├─ Acción:{Colors.END} {Colors.GREEN}{opp["action_suggested"]}{Colors.END}
{Colors.BLUE}   ├─ Timeframe:{Colors.END} {opp["action_details"]["timeframe"]}
{Colors.BLUE}   └─ Rationale:{Colors.END} {opp["action_details"]["rationale"]}
        """)

    def print_event(self, event, index: int = 0):
        """Imprime un evento formateado"""
        urgency_colors = {
            "CRITICAL": Colors.RED + Colors.BOLD,
            "HIGH": Colors.YELLOW + Colors.BOLD,
            "MEDIUM": Colors.CYAN,
            "LOW": Colors.BLUE,
            "BACKGROUND": Colors.END
        }

        sentiment_emoji = {
            "VERY_BULLISH": "🚀",
            "BULLISH": "📈",
            "NEUTRAL": "➖",
            "BEARISH": "📉",
            "VERY_BEARISH": "💥"
        }

        u_color = urgency_colors.get(event.urgency.name, Colors.END)
        s_emoji = sentiment_emoji.get(event.sentiment.name, "➖")

        assets = ", ".join([a.symbol for a in event.assets]) if event.assets else "N/A"

        print(f"""
{Colors.BOLD}[{index}] {u_color}[{event.urgency.name}]{Colors.END} {s_emoji} {event.title[:100]}{Colors.END}
{Colors.BLUE}   ├─ Tipo:{Colors.END} {event.event_type.value} | {Colors.BLUE}Fuente:{Colors.END} {event.source}
{Colors.BLUE}   ├─ Assets:{Colors.END} {assets}
{Colors.BLUE}   ├─ Sentimiento:{Colors.END} {event.sentiment.name} ({event.sentiment_score:+.2f})
{Colors.BLUE}   ├─ Confianza:{Colors.END} {event.confidence:.0%}
{Colors.BLUE}   └─ Hora:{Colors.END} {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)

    def cmd_collect(self, args):
        """Comando: recolectar datos"""
        print(f"{Colors.CYAN}{Colors.BOLD}[COLLECT] Iniciando recolección de datos...{Colors.END}\n")

        events = self.monitor.collect_all()

        if not events:
            print(f"{Colors.YELLOW}⚠ No se encontraron eventos.{Colors.END}")
            return

        print(f"{Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}\n")

        # Guardar en DB
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"{Colors.RED}✗ Error guardando evento: {e}{Colors.END}")

        print(f"{Colors.GREEN}✓ {stored}/{len(events)} eventos almacenados en base de datos{Colors.END}")

        # Mostrar resumen
        stats = self.db.get_event_stats()
        print(f"\n{Colors.BLUE}📊 Estadísticas de base de datos:{Colors.END}")
        print(f"   Total eventos: {stats['total_events']}")
        print(f"   Sin procesar: {stats['unprocessed']}")
        print(f"   Por tipo: {stats['by_type']}")

    def cmd_process(self, args):
        """Comando: procesar eventos pendientes"""
        print(f"{Colors.CYAN}{Colors.BOLD}[PROCESS] Procesando eventos pendientes...{Colors.END}\n")

        # Obtener eventos sin procesar
        unprocessed = self.db.get_unprocessed_events(limit=200)

        if not unprocessed:
            print(f"{Colors.YELLOW}⚠ No hay eventos pendientes de procesamiento.{Colors.END}")
            return

        print(f"{Colors.BLUE}📥 {len(unprocessed)} eventos pendientes encontrados{Colors.END}\n")

        # Ejecutar pipeline
        result = self.pipeline.run(unprocessed, min_score=args.min_score)

        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Pipeline completado{Colors.END}")
        print(f"   Eventos procesados: {result['events_processed']}")
        print(f"   Oportunidades generadas: {result['opportunities_generated']}")

        # Mostrar top oportunidades
        if result['top_opportunities']:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}🏆 TOP OPORTUNIDADES:{Colors.END}\n")
            for i, opp in enumerate(result['top_opportunities'][:args.limit], 1):
                self.print_opportunity(opp, i)

    def cmd_opportunities(self, args):
        """Comando: ver oportunidades activas"""
        print(f"{Colors.CYAN}{Colors.BOLD}[OPPORTUNITIES] Oportunidades activas{Colors.END}\n")

        opps = self.db.get_active_opportunities(limit=args.limit)

        if not opps:
            print(f"{Colors.YELLOW}⚠ No hay oportunidades activas.{Colors.END}")
            print(f"   Ejecuta 'oma collect' y 'oma process' primero.")
            return

        print(f"{Colors.GREEN}✓ {len(opps)} oportunidades activas{Colors.END}\n")

        for i, opp in enumerate(opps, 1):
            self.print_opportunity(opp, i)

    def cmd_events(self, args):
        """Comando: ver eventos recientes"""
        print(f"{Colors.CYAN}{Colors.BOLD}[EVENTS] Eventos recientes (últimas {args.hours}h){Colors.END}\n")

        events = self.db.get_recent_events(hours=args.hours, limit=args.limit)

        if not events:
            print(f"{Colors.YELLOW}⚠ No hay eventos recientes.{Colors.END}")
            return

        print(f"{Colors.GREEN}✓ {len(events)} eventos encontrados{Colors.END}\n")

        for i, event in enumerate(events, 1):
            self.print_event(event, i)

    def cmd_status(self, args):
        """Comando: ver estado del sistema"""
        print(f"{Colors.CYAN}{Colors.BOLD}[STATUS] Estado del sistema O.M.A.-C.O.R.E.{Colors.END}\n")

        stats = self.db.get_event_stats()
        opps = self.db.get_active_opportunities(limit=1000)

        print(f"{Colors.BOLD}📊 Base de datos:{Colors.END}")
        print(f"   Total eventos: {stats['total_events']}")
        print(f"   Eventos sin procesar: {stats['unprocessed']}")
        print(f"   Oportunidades activas: {len(opps)}")

        print(f"\n{Colors.BOLD}📈 Distribución por tipo:{Colors.END}")
        for etype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"   {etype:20s} {bar} {count}")

        print(f"\n{Colors.BOLD}⚡ Distribución por urgencia:{Colors.END}")
        urgency_names = {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "BACKGROUND"}
        for urg, count in sorted(stats['by_urgency'].items(), key=lambda x: -x[0]):
            name = urgency_names.get(urg, str(urg))
            bar = "█" * min(count, 20)
            print(f"   {name:20s} {bar} {count}")

        if opps:
            avg_score = sum(o["score"] for o in opps) / len(opps)
            print(f"\n{Colors.BOLD}🎯 Score promedio oportunidades: {avg_score:.1f}{Colors.END}")

    def cmd_watch(self, args):
        """Comando: modo monitoreo continuo"""
        print(f"{Colors.CYAN}{Colors.BOLD}[WATCH] Modo monitoreo continuo{Colors.END}")
        print(f"   Intervalo: {args.interval}s | Min score: {args.min_score}")
        print(f"   Presiona Ctrl+C para detener\n")

        cycle = 0
        try:
            while True:
                cycle += 1
                print(f"{Colors.BLUE}\n[Cycle {cycle}] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC{Colors.END}")

                # Recolectar
                events = self.monitor.collect_all()
                if events:
                    print(f"   {Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}")

                    # Procesar
                    result = self.pipeline.run(events, min_score=args.min_score)

                    if result['opportunities_generated'] > 0:
                        print(f"   {Colors.YELLOW}🏆 {result['opportunities_generated']} oportunidades detectadas!{Colors.END}")
                        for opp in result['top_opportunities'][:3]:
                            p_color = Colors.RED if opp["priority"] == "CRITICAL" else Colors.YELLOW if opp["priority"] == "HIGH" else Colors.CYAN
                            print(f"      {p_color}[{opp['priority']}] {opp['title'][:80]} (Score: {opp['score']}){Colors.END}")
                else:
                    print(f"   {Colors.BLUE}○ Sin eventos nuevos{Colors.END}")

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠ Monitoreo detenido por usuario{Colors.END}")

    def cmd_export(self, args):
        """Comando: exportar datos"""
        print(f"{Colors.CYAN}{Colors.BOLD}[EXPORT] Exportando datos...{Colors.END}\n")

        if args.format == "json":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(opps, f, indent=2, default=str)

            print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")

        elif args.format == "csv":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

            if opps:
                keys = opps[0].keys()
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(opps)

                print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ No hay oportunidades para exportar{Colors.END}")

    def cmd_run(self, args):
        """Comando: ejecutar ciclo completo (collect + process)"""
        self.cmd_collect(args)
        print("\n" + "─" * 60 + "\n")
        self.cmd_process(args)

    def run(self):
        """Punto de entrada principal"""
        parser = argparse.ArgumentParser(
            description="O.M.A.-C.O.R.E. — Intelligence Engine CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos:
  oma collect                    Recolectar datos
  oma process --min-score 50     Procesar con score mínimo 50
  oma run                        Ciclo completo
  oma watch --interval 300       Monitoreo cada 5 minutos
  oma opportunities --limit 20   Ver top 20 oportunidades
  oma export --format json       Exportar a JSON
            """
        )

        subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

        # collect
        p_collect = subparsers.add_parser("collect", help="Recolectar datos de fuentes")

        # process
        p_process = subparsers.add_parser("process", help="Procesar eventos pendientes")
        p_process.add_argument("--min-score", type=float, default=40.0, help="Score mínimo (default: 40)")
        p_process.add_argument("--limit", type=int, default=10, help="Límite de oportunidades a mostrar")

        # opportunities
        p_opps = subparsers.add_parser("opportunities", help="Ver oportunidades activas")
        p_opps.add_argument("--limit", type=int, default=20, help="Límite (default: 20)")

        # events
        p_events = subparsers.add_parser("events", help="Ver eventos recientes")
        p_events.add_argument("--hours", type=int, default=24, help="Horas atrás (default: 24)")
        p_events.add_argument("--limit", type=int, default=20, help="Límite (default: 20)")

        # status
        p_status = subparsers.add_parser("status", help="Estado del sistema")

        # watch
        p_watch = subparsers.add_parser("watch", help="Monitoreo continuo")
        p_watch.add_argument("--interval", type=int, default=300, help="Intervalo en segundos (default: 300)")
        p_watch.add_argument("--min-score", type=float, default=40.0, help="Score mínimo (default: 40)")

        # export
        p_export = subparsers.add_parser("export", help="Exportar datos")
        p_export.add_argument("--format", choices=["json", "csv"], default="json", help="Formato (default: json)")

        # run
        p_run = subparsers.add_parser("run", help="Ejecutar ciclo completo")
        p_run.add_argument("--min-score", type=float, default=40.0, help="Score mínimo")
        p_run.add_argument("--limit", type=int, default=10, help="Límite oportunidades")

        args = parser.parse_args()

        self.print_banner()

        if not args.command:
            parser.print_help()
            return

        command_map = {
            "collect": self.cmd_collect,
            "process": self.cmd_process,
            "opportunities": self.cmd_opportunities,
            "events": self.cmd_events,
            "status": self.cmd_status,
            "watch": self.cmd_watch,
            "export": self.cmd_export,
            "run": self.cmd_run
        }

        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"{Colors.RED}Comando desconocido: {args.command}{Colors.END}")


if __name__ == "__main__":
    cli = OMACLI()
    cli.run()
