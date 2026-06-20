#!/usr/bin/env python3
"""O.M.A.-C.O.R.E. CLI Interface"""
import argparse
import json
import csv
import time
import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from core.database.db import OMACoreDatabase
from core.collectors.world_monitor import WorldMonitor
from core.engines.score_opportunity import Pipeline

# Cargar variables de entorno desde .env
load_dotenv()

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

class OMACLI:
    def __init__(self, db_path="oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.fred_api_key = os.getenv("FRED_API_KEY")
        self.pipeline = Pipeline(db_path, fred_api_key=self.fred_api_key)
        self.monitor = WorldMonitor(fred_api_key=self.fred_api_key)
    
    def print_banner(self):
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
 ██████  ███    ███  █████      ██████  ██████  ██████  ███████ 
██    ██ ████  ████ ██   ██    ██      ██    ██ ██   ██ ██      
██    ██ ██ ████ ██ ███████    ██      ██    ██ ██████  █████   
██    ██ ██  ██  ██ ██   ██    ██      ██    ██ ██   ██ ██      
 ██████  ██      ██ ██   ██     ██████  ██████  ██   ██ ███████ 
{Colors.END}
{Colors.YELLOW}  One Man Army — Create. Own. Run. Everything.{Colors.END}
{Colors.GREEN}  Intelligence Engine v2.0 — Trading Focus{Colors.END}
{Colors.BLUE}  —————————————————————————————————————————{Colors.END}
        """
        print(banner)
    
    def print_opportunity(self, opp, index=0):
        priority_colors = {"CRITICAL": Colors.RED + Colors.BOLD, "HIGH": Colors.YELLOW + Colors.BOLD, "MEDIUM": Colors.CYAN, "LOW": Colors.BLUE}
        score_color = Colors.GREEN if opp["score"] >= 70 else Colors.YELLOW if opp["score"] >= 50 else Colors.BLUE
        risk_colors = {"VERY_HIGH": Colors.RED + Colors.BOLD, "HIGH": Colors.RED, "MEDIUM": Colors.YELLOW, "LOW": Colors.GREEN}
        p_color = priority_colors.get(opp["priority"], Colors.END)
        r_color = risk_colors.get(opp["risk_level"], Colors.END)
        
        print(f"""
{Colors.BOLD}[{index}] {p_color}[{opp["priority"]}]{Colors.END} {opp["title"]}{Colors.END}
{Colors.BLUE}   |- Score:{Colors.END} {score_color}{opp["score"]}/100{Colors.END} | {Colors.BLUE}Conviccion:{Colors.END} {opp["conviction"]}/100
{Colors.BLUE}   |- Tipo:{Colors.END} {opp["opportunity_type"]} | {Colors.BLUE}Assets:{Colors.END} {', '.join(opp["assets"]) if opp["assets"] else 'N/A'}
{Colors.BLUE}   |- Riesgo:{Colors.END} {r_color}{opp["risk_level"]}{Colors.END} | {Colors.BLUE}Fuente:{Colors.END} {opp["source"]}
{Colors.BLUE}   |- Accion:{Colors.END} {Colors.GREEN}{opp["action_suggested"]}{Colors.END}
{Colors.BLUE}   |- Timeframe:{Colors.END} {opp["action_details"]["timeframe"]}
{Colors.BLUE}   |- Rationale:{Colors.END} {opp["action_details"]["rationale"]}
        """)
    
    def print_event(self, event, index=0):
        urgency_colors = {"CRITICAL": Colors.RED + Colors.BOLD, "HIGH": Colors.YELLOW + Colors.BOLD, "MEDIUM": Colors.CYAN, "LOW": Colors.BLUE, "BACKGROUND": Colors.END}
        sentiment_emoji = {"VERY_BULLISH": "🚀", "BULLISH": "📈", "NEUTRAL": "➖", "BEARISH": "📉", "VERY_BEARISH": "💥"}
        u_color = urgency_colors.get(event.urgency.name, Colors.END)
        s_emoji = sentiment_emoji.get(event.sentiment.name, "➖")
        assets = ", ".join([a.symbol for a in event.assets]) if event.assets else "N/A"
        
        print(f"""
{Colors.BOLD}[{index}] {u_color}[{event.urgency.name}]{Colors.END} {s_emoji} {event.title[:100]}{Colors.END}
{Colors.BLUE}   |- Tipo:{Colors.END} {event.event_type.value} | {Colors.BLUE}Fuente:{Colors.END} {event.source}
{Colors.BLUE}   |- Assets:{Colors.END} {assets}
{Colors.BLUE}   |- Sentimiento:{Colors.END} {event.sentiment.name} ({event.sentiment_score:+.2f})
{Colors.BLUE}   |- Confianza:{Colors.END} {event.confidence:.0%}
{Colors.BLUE}   |- Hora:{Colors.END} {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
    
    def cmd_collect(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[COLLECT] Iniciando recoleccion...{Colors.END}\n")
        events = self.monitor.collect_all()
        if not events:
            print(f"{Colors.YELLOW}⚠ No se encontraron eventos.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}\n")
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        print(f"{Colors.GREEN}✓ {stored}/{len(events)} eventos almacenados{Colors.END}")
        stats = self.db.get_event_stats()
        print(f"\n{Colors.BLUE}📊 Stats:{Colors.END} Total: {stats['total_events']} | Sin procesar: {stats['unprocessed']}")
    
    def cmd_process(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[PROCESS] Procesando eventos...{Colors.END}\n")
        unprocessed = self.db.get_unprocessed_events(limit=200)
        if not unprocessed:
            print(f"{Colors.YELLOW}⚠ No hay eventos pendientes.{Colors.END}")
            return
        print(f"{Colors.BLUE}📥 {len(unprocessed)} eventos pendientes{Colors.END}\n")
        result = self.pipeline.run(unprocessed, min_score=args.min_score)
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Pipeline completado{Colors.END}")
        print(f"   Eventos: {result['events_processed']} | Oportunidades: {result['opportunities_generated']}")
        if result['top_opportunities']:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}🏆 TOP OPORTUNIDADES:{Colors.END}\n")
            for i, opp in enumerate(result['top_opportunities'][:args.limit], 1):
                self.print_opportunity(opp, i)
    
    def cmd_opportunities(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[OPPORTUNITIES] Activas{Colors.END}\n")
        opps = self.db.get_active_opportunities(limit=args.limit)
        if not opps:
            print(f"{Colors.YELLOW}⚠ No hay oportunidades. Ejecuta 'oma collect' y 'oma process' primero.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(opps)} oportunidades{Colors.END}\n")
        for i, opp in enumerate(opps, 1):
            self.print_opportunity(opp, i)
    
    def cmd_events(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[EVENTS] Recientes (ultimas {args.hours}h){Colors.END}\n")
        events = self.db.get_recent_events(hours=args.hours, limit=args.limit)
        if not events:
            print(f"{Colors.YELLOW}⚠ No hay eventos.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(events)} eventos{Colors.END}\n")
        for i, event in enumerate(events, 1):
            self.print_event(event, i)
    
    def cmd_status(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[STATUS] Sistema{Colors.END}\n")
        stats = self.db.get_event_stats()
        opps = self.db.get_active_opportunities(limit=1000)
        print(f"{Colors.BOLD}📊 DB:{Colors.END} Total: {stats['total_events']} | Sin procesar: {stats['unprocessed']} | Oportunidades: {len(opps)}")
        print(f"\n{Colors.BOLD}📈 Por tipo:{Colors.END}")
        for etype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"   {etype:20s} {bar} {count}")
        print(f"\n{Colors.BOLD}⚡ Por urgencia:{Colors.END}")
        urgency_names = {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "BACKGROUND"}
        for urg, count in sorted(stats['by_urgency'].items(), key=lambda x: -x[0]):
            print(f"   {urgency_names.get(urg, str(urg)):20s} {'█' * min(count, 20)} {count}")
        if opps:
            avg_score = sum(o["score"] for o in opps) / len(opps)
            print(f"\n{Colors.BOLD}🎯 Score promedio: {avg_score:.1f}{Colors.END}")
    
    def cmd_watch(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[WATCH] Monitoreo continuo{Colors.END}")
        print(f"   Intervalo: {args.interval}s | Min score: {args.min_score}")
        print(f"   Presiona Ctrl+C para detener\n")
        cycle = 0
        try:
            while True:
                cycle += 1
                print(f"{Colors.BLUE}\n[Cycle {cycle}] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC{Colors.END}")
                events = self.monitor.collect_all()
                if events:
                    print(f"   {Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}")
                    result = self.pipeline.run(events, min_score=args.min_score)
                    if result['opportunities_generated'] > 0:
                        print(f"   {Colors.YELLOW}🏆 {result['opportunities_generated']} oportunidades!{Colors.END}")
                        for opp in result['top_opportunities'][:3]:
                            p_color = Colors.RED if opp["priority"] == "CRITICAL" else Colors.YELLOW if opp["priority"] == "HIGH" else Colors.CYAN
                            print(f"      {p_color}[{opp['priority']}] {opp['title'][:80]} (Score: {opp['score']}){Colors.END}")
                else:
                    print(f"   {Colors.BLUE}○ Sin eventos nuevos{Colors.END}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠ Monitoreo detenido{Colors.END}")
    
    def cmd_export(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[EXPORT] Exportando...{Colors.END}\n")
        if args.format == "json":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(opps, f, indent=2, default=str)
            print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")
        elif args.format == "csv":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            if opps:
                keys = opps[0].keys()
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(opps)
                print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ No hay oportunidades{Colors.END}")
    
    def cmd_run(self, args):
        self.cmd_collect(args)
        print("\n" + "—" * 60 + "\n")
        self.cmd_process(args)
    
    def run(self):
        parser = argparse.ArgumentParser(
            description="O.M.A.-C.O.R.E. — Intelligence Engine CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos:
  python -m core.cli.main collect
  python -m core.cli.main process --min-score 50
  python -m core.cli.main run
  python -m core.cli.main watch --interval 300
  python -m core.cli.main opportunities --limit 20
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
        
        p_collect = subparsers.add_parser("collect", help="Recolectar datos")
        
        p_process = subparsers.add_parser("process", help="Procesar eventos")
        p_process.add_argument("--min-score", type=float, default=40.0)
        p_process.add_argument("--limit", type=int, default=10)
        
        p_opps = subparsers.add_parser("opportunities", help="Ver oportunidades")
        p_opps.add_argument("--limit", type=int, default=20)
        
        p_events = subparsers.add_parser("events", help="Ver eventos")
        p_events.add_argument("--hours", type=int, default=24)
        p_events.add_argument("--limit", type=int, default=20)
        
        p_status = subparsers.add_parser("status", help="Estado del sistema")
        
        p_watch = subparsers.add_parser("watch", help="Monitoreo continuo")
        p_watch.add_argument("--interval", type=int, default=300)
        p_watch.add_argument("--min-score", type=float, default=40.0)
        
        p_export = subparsers.add_parser("export", help="Exportar datos")
        p_export.add_argument("--format", choices=["json", "csv"], default="json")
        
        p_run = subparsers.add_parser("run", help="Ciclo completo")
        p_run.add_argument("--min-score", type=float, default=40.0)
        p_run.add_argument("--limit", type=int, default=10)
        
        args = parser.parse_args()
        self.print_banner()
        
        if not args.command:
            parser.print_help()
            return
        
        command_map = {
            "collect": self.cmd_collect, "process": self.cmd_process,
            "opportunities": self.cmd_opportunities, "events": self.cmd_events,
            "status": self.cmd_status, "watch": self.cmd_watch,
            "export": self.cmd_export, "run": self.cmd_run
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"{Colors.RED}Comando desconocido: {args.command}{Colors.END}")


if __name__ == "__main__":
    cli = OMACLI()
    cli.run()
