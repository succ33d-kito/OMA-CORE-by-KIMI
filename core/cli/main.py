#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
"""O.M.A.-C.O.R.E. CLI Interface"""
import argparse
import json
import csv
import time
import sys
from datetime import datetime, timezone
from core.database.db import OMACoreDatabase
from core.collectors.world_monitor_v2 import WorldMonitorV2
from core.engines.score_opportunity import Pipeline
from core.engines.telegram_notifier import TelegramNotifier
from core.event_bus import EventBus, EventTopic
from core.council import AgentCouncil, MetaCouncil
from core.agents import NewsAgent, MacroAgent
from core.schemas.agent_schema import CouncilDecision as CouncilDecisionSchema
from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.evidence_schema import Evidence, EvidenceDirection, EvidenceStatus
from core.schemas.outcome_comparison_schema import OutcomeComparison, Verdict, ErrorType, ComparisonType
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.hypothesis_lifecycle import transition_hypothesis, get_valid_transitions
from core.scientific.evidence_lifecycle import activate_evidence
from core.scientific.outcome_comparison import compare_outcome, classify_error, auto_detect_verdict
from core.scientific.knowledge_lifecycle import (
    extract_knowledge, extract_from_comparison,
    transition_knowledge, can_transition,
    promote_to_provisional, validate_knowledge,
    invalidate_knowledge, revise_knowledge, archive_knowledge,
    decay_confidence,
)
from core.scientific.criterion_evolution import (
    propose_delta, apply_delta, reject_delta,
    compute_criterion_metrics, VALID_DIMENSIONS,
)

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
        self.pipeline = Pipeline(db_path)
        self.monitor = WorldMonitorV2()
        self.notifier = TelegramNotifier()
        self.event_bus = EventBus()
        self.agent_council = AgentCouncil(self.event_bus)
        self.meta_council = MetaCouncil(self.event_bus)
        self.news_agent = NewsAgent(event_bus=self.event_bus)
        self.macro_agent = MacroAgent(event_bus=self.event_bus)
        self.scientific = ScientificStore()
    
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
{Colors.GREEN}  Intelligence Engine v1.0 — Trading Focus{Colors.END}
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
    
    def cmd_council(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[COUNCIL] Running OSIRIS Agent Council...{Colors.END}\n")
        unprocessed = self.db.get_unprocessed_events(limit=args.limit)
        if not unprocessed:
            print(f"{Colors.YELLOW}⚠ No events to analyze.{Colors.END}")
            return
        print(f"{Colors.BLUE}📥 {len(unprocessed)} events for council analysis{Colors.END}\n")

        news_opinions = self.news_agent.analyze_batch(unprocessed)
        print(f"{Colors.GREEN}✓ NewsAgent: {len(news_opinions)} opinions{Colors.END}")
        macro_opinions = self.macro_agent.analyze_batch(unprocessed)
        print(f"{Colors.GREEN}✓ MacroAgent: {len(macro_opinions)} opinions{Colors.END}")

        all_opinions = news_opinions + macro_opinions
        if not all_opinions:
            print(f"{Colors.YELLOW}⚠ No opinions generated.{Colors.END}")
            return

        for opinion in all_opinions:
            self.agent_council.submit_opinion(opinion)

        event_ids = set(o.event_id for o in all_opinions)
        decisions = []
        for event_id in event_ids:
            decision = self.agent_council.decide(event_id)
            if decision:
                decisions.append(decision)
                meta = self.meta_council.decide_best_profile(event_id, decision.opinions)
                print(f"\n{Colors.BOLD}Event: {event_id[:12]}...{Colors.END}")
                print(f"   Council Conviction: {decision.conviction:.1f} | Consensus: {decision.consensus_score:.1f} | Disagreement: {decision.disagreement_score:.1f}")
                print(f"   Action: {Colors.GREEN if decision.action.value in ('buy','strong_buy','hold') else Colors.RED}{decision.action.value.upper()}{Colors.END}")
                print(f"   Best Profile: {Colors.YELLOW}{meta.best_profile.upper()}{Colors.END} (conviction: {meta.meta_conviction:.1f})")
                print(f"   Rationale: {decision.rationale[:200]}...")

        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Council completed: {len(decisions)} decisions{Colors.END}")

    def cmd_hypothesis_create(self, args):
        try:
            hyp = self.scientific.create_hypothesis(
                title=args.title,
                description=args.description,
                predicted_consequence=args.consequence,
                conditions=args.conditions,
                invalidation_conditions=args.invalidation,
                confidence=args.confidence,
            )
            print(f"{Colors.GREEN}✓ Hypothesis created{Colors.END}")
            print(f"   ID:     {hyp.id}")
            print(f"   Title:  {hyp.title}")
            print(f"   Status: {hyp.status.value}")
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to create hypothesis: {e}{Colors.END}")

    def cmd_hypothesis_list(self, args):
        status_filter = None
        if args.status:
            try:
                status_filter = HypothesisStatus(args.status)
            except ValueError:
                print(f"{Colors.RED}✗ Invalid status. Valid: {[s.value for s in HypothesisStatus]}{Colors.END}")
                return
        hypotheses = self.scientific.list_hypotheses(status=status_filter, limit=args.limit)
        if not hypotheses:
            print(f"{Colors.YELLOW}⚠ No hypotheses found.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(hypotheses)} hypotheses{Colors.END}\n")
        for h in hypotheses:
            status_colors = {
                "formulated": Colors.CYAN,
                "active": Colors.GREEN,
                "evaluated": Colors.YELLOW,
                "archived": Colors.BLUE,
            }
            sc = status_colors.get(h.status.value, Colors.END)
            print(f"  [{sc}{h.status.value.upper():12s}{Colors.END}] {h.id[:12]}... {h.title[:60]}")
            print(f"       Confidence: {h.confidence:.2f}  |  Created: {h.created_at.strftime('%Y-%m-%d')}")

    def cmd_hypothesis_show(self, args):
        hyp = self.scientific.get_hypothesis(args.id)
        if not hyp:
            print(f"{Colors.RED}✗ Hypothesis not found: {args.id}{Colors.END}")
            return
        evidence_list = self.scientific.list_evidence(hypothesis_id=hyp.id)
        supports = sum(1 for e in evidence_list if e.direction == EvidenceDirection.SUPPORTS and e.status == EvidenceStatus.ACTIVE)
        contradicts = sum(1 for e in evidence_list if e.direction == EvidenceDirection.CONTRADICTS and e.status == EvidenceStatus.ACTIVE)

        print(f"{Colors.BOLD}Hypothesis: {hyp.title}{Colors.END}")
        print(f"  ID:                     {hyp.id}")
        print(f"  Status:                 {hyp.status.value}")
        print(f"  Confidence:             {hyp.confidence:.2f}")
        print(f"  Description:            {hyp.description}")
        print(f"  Predicted Consequence:  {hyp.predicted_consequence}")
        print(f"  Conditions:             {hyp.conditions}")
        print(f"  Invalidation:           {hyp.invalidation_conditions}")
        print(f"  Created:                {hyp.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Updated:                {hyp.updated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Evidence:               {supports} supports, {contradicts} contradicts")
        if hyp.status_history:
            print(f"  History:")
            for entry in hyp.status_history:
                print(f"    {entry['timestamp']}: {entry['from_status']} → {entry['to_status']}")

    def cmd_hypothesis_transition(self, args):
        hyp = self.scientific.get_hypothesis(args.id)
        if not hyp:
            print(f"{Colors.RED}✗ Hypothesis not found: {args.id}{Colors.END}")
            return
        try:
            target = HypothesisStatus(args.to)
            valid = get_valid_transitions(hyp)
            if target not in valid:
                print(f"{Colors.RED}✗ Invalid transition.{Colors.END}")
                print(f"   Current state: {hyp.status.value}")
                print(f"   Valid targets: {[s.value for s in valid]}")
                return
            transition_hypothesis(hyp, target, reason=args.reason)
            self.scientific.update_hypothesis(hyp)
            print(f"{Colors.GREEN}✓ Transitioned to {target.value}{Colors.END}")
        except ValueError as e:
            print(f"{Colors.RED}✗ {e}{Colors.END}")

    def cmd_hypothesis_archive(self, args):
        self.cmd_hypothesis_transition(argparse.Namespace(
            id=args.id, to="archived", reason=args.reason or "Archived via CLI"
        ))

    def cmd_evidence_add(self, args):
        hyp = self.scientific.get_hypothesis(args.hypothesis_id)
        if not hyp:
            print(f"{Colors.RED}✗ Hypothesis not found: {args.hypothesis_id}{Colors.END}")
            return
        try:
            direction = EvidenceDirection(args.direction)
        except ValueError:
            print(f"{Colors.RED}✗ Invalid direction. Use 'supports' or 'contradicts'{Colors.END}")
            return
        evidence = self.scientific.add_evidence(
            hypothesis_id=args.hypothesis_id,
            direction=direction,
            weight=args.weight,
            content=args.content,
            source_id=args.source,
            source_reliability=args.reliability,
        )
        if evidence:
            activated = activate_evidence(evidence)
            self.scientific.update_evidence(activated)
            print(f"{Colors.GREEN}✓ Evidence added and activated{Colors.END}")
            print(f"   ID:        {evidence.id}")
            print(f"   Direction: {evidence.direction.value}")
            print(f"   Weight:    {evidence.weight:.2f}")
        else:
            print(f"{Colors.RED}✗ Failed to add evidence{Colors.END}")

    def cmd_evidence_list(self, args):
        evidence_list = self.scientific.list_evidence(
            hypothesis_id=args.hypothesis_id, limit=args.limit
        )
        if not evidence_list:
            print(f"{Colors.YELLOW}⚠ No evidence for hypothesis {args.hypothesis_id}{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(evidence_list)} evidence items{Colors.END}\n")
        for e in evidence_list:
            dir_color = Colors.GREEN if e.direction == EvidenceDirection.SUPPORTS else Colors.RED
            dir_symbol = "+" if e.direction == EvidenceDirection.SUPPORTS else "-"
            status_tag = f"[{e.status.value}]" if e.status != EvidenceStatus.ACTIVE else ""
            print(f"  {dir_color}{dir_symbol}{Colors.END} {e.id[:12]}... {status_tag} weight={e.weight:.2f} | {e.content[:80]}")

    def cmd_hypothesis(self, args):
        if not args.hypothesis_command:
            print(f"{Colors.YELLOW}Usage: oma hypothesis {Colors.END}")
            print(f"  Commands: create, list, show, transition, archive")
            return

    def cmd_evidence(self, args):
        if not args.evidence_command:
            print(f"{Colors.YELLOW}Usage: oma evidence {Colors.END}")
            print(f"  Commands: add, list")
            return

    def cmd_scientific_status(self, args):
        stats = self.scientific.get_stats()
        print(f"{Colors.BOLD}Scientific Memory Status{Colors.END}\n")
        print(f"  Hypotheses: {stats['total_hypotheses']}")
        for status, count in stats.get('hypotheses_by_status', {}).items():
            print(f"    {status}: {count}")
        print(f"  Evidence:   {stats['total_evidence']}")
        for direction, count in stats.get('evidence_by_direction', {}).items():
            print(f"    {direction}: {count}")

    # ── Lab Command Handlers ─────────────────────────────────────

    def cmd_lab(self, args):
        if not args.lab_command:
            self.cmd_lab_status(args)
            return

    def cmd_lab_status(self, args):
        stats = self.scientific.get_lab_stats()
        print(f"{Colors.BOLD}{Colors.CYAN}Scientific Learning Laboratory{Colors.END}")
        print(f"{Colors.BLUE}—" + "—" * 50 + f"{Colors.END}\n")
        h = stats["hypotheses"]
        print(f"{Colors.BOLD}Hypotheses:{Colors.END}")
        print(f"  Total:     {h['total']}")
        print(f"  Evaluated: {h['evaluated']}")

        c = stats["comparisons"]
        print(f"\n{Colors.BOLD}Outcome Comparisons:{Colors.END}")
        print(f"  Total:     {c['total']}")
        print(f"  Confirmed: {c['confirmed']}")
        print(f"  Rejected:  {c['rejected']}")

        k = stats["knowledge"]
        print(f"\n{Colors.BOLD}Knowledge:{Colors.END}")
        print(f"  Total:     {k['total']}")
        print(f"  Validated: {k['validated']}")

        d = stats["deltas"]
        print(f"\n{Colors.BOLD}Criterion Deltas:{Colors.END}")
        print(f"  Pending: {d['pending_review']}")
        print(f"  Applied: {d['applied']}")

        print(f"\n{Colors.BLUE}—" + "—" * 50 + f"{Colors.END}")
        print(f"{Colors.YELLOW}Usage: oma lab <command>{Colors.END}")
        print(f"  compare   Compare a hypothesis to an actual outcome")
        print(f"  knowledge Manage knowledge items")
        print(f"  criterion Manage criterion deltas")
        print(f"  status    Show lab status")

    def cmd_lab_compare(self, args):
        hyp = self.scientific.get_hypothesis(args.hypothesis_id)
        if not hyp:
            print(f"{Colors.RED}✗ Hypothesis not found: {args.hypothesis_id}{Colors.END}")
            return

        try:
            verdict = Verdict(args.verdict) if args.verdict else None
        except ValueError:
            print(f"{Colors.RED}✗ Invalid verdict. Valid: {[v.value for v in Verdict]}{Colors.END}")
            return

        error_type = None
        if args.error_type:
            try:
                error_type = ErrorType(args.error_type)
            except ValueError:
                print(f"{Colors.RED}✗ Invalid error type. Valid: {[e.value for e in ErrorType]}{Colors.END}")
                return

        comparison = compare_outcome(
            hypothesis=hyp,
            actual_outcome=args.actual_outcome,
            verdict=verdict,
            comparison_confidence=args.confidence,
            comparison_type=ComparisonType(args.comparison_type),
            error_type=error_type,
            error_detail=args.error_detail,
        )

        self.scientific.create_outcome_comparison(comparison)

        self._print_lab_report_header()
        print(f"{Colors.BOLD}Step 1: Outcome Comparison{Colors.END}")
        print(f"{Colors.BLUE}—" + "—" * 50 + f"{Colors.END}")
        print(f"  Hypothesis:     {hyp.title[:60]}")
        print(f"  Predicted:      {hyp.predicted_consequence[:80]}")
        print(f"  Actual:         {comparison.actual_outcome[:80]}")
        verdict_colors = {
            "confirmed": Colors.GREEN, "rejected": Colors.RED,
            "correct_block": Colors.GREEN, "incorrect_block": Colors.RED,
        }
        vc = verdict_colors.get(comparison.verdict.value, Colors.YELLOW)
        print(f"  Verdict:        {vc}{comparison.verdict.value.upper()}{Colors.END}")
        print(f"  Confidence:     {comparison.comparison_confidence:.2f}")
        if comparison.error_type:
            print(f"  Error Type:     {Colors.RED}{comparison.error_type.value}{Colors.END}")
        if comparison.error_detail:
            print(f"  Error Detail:   {comparison.error_detail}")
        print(f"  Comparison ID:  {comparison.id[:16]}...")

        if args.knowledge:
            auto_knowledge = extract_from_comparison(
                comparison=comparison,
                statement=args.knowledge,
                conditions=args.knowledge_conditions or hyp.conditions,
                scope=args.knowledge_scope or "general",
                time_horizon=args.knowledge_horizon or "swing",
                confidence=args.knowledge_confidence or 0.3,
            )
            self.scientific.create_knowledge(auto_knowledge)
            print(f"\n{Colors.GREEN}✓ Knowledge auto-extracted:{Colors.END}")
            print(f"  {auto_knowledge.statement[:80]}")
            print(f"  Status: {auto_knowledge.status.value} | Confidence: {auto_knowledge.confidence:.2f}")
            print(f"  Knowledge ID: {auto_knowledge.id[:16]}...")

        print(f"\n{Colors.GREEN}✓ Comparison recorded{Colors.END}")

    def cmd_lab_knowledge(self, args):
        if args.knowledge_command == "list":
            status_filter = None
            if args.status:
                try:
                    status_filter = KnowledgeStatus(args.status)
                except ValueError:
                    print(f"{Colors.RED}✗ Invalid status. Valid: {[s.value for s in KnowledgeStatus]}{Colors.END}")
                    return
            items = self.scientific.list_knowledge(status=status_filter, limit=args.limit)
            if not items:
                print(f"{Colors.YELLOW}⚠ No knowledge items.{Colors.END}")
                return
            print(f"{Colors.GREEN}✓ {len(items)} knowledge items{Colors.END}\n")
            for k in items:
                status_colors = {
                    "extracted": Colors.CYAN, "provisional": Colors.YELLOW,
                    "validated": Colors.GREEN, "revised": Colors.BLUE,
                    "invalidated": Colors.RED, "archived": Colors.BLUE,
                }
                sc = status_colors.get(k.status.value, Colors.END)
                print(f"  [{sc}{k.status.value.upper():12s}{Colors.END}] {k.id[:12]}...")
                print(f"       {k.statement[:80]}")
                print(f"       Confidence: {k.confidence:.2f} | Replications: {k.replication_count}")

        elif args.knowledge_command == "show":
            k = self.scientific.get_knowledge(args.id)
            if not k:
                print(f"{Colors.RED}✗ Knowledge not found: {args.id}{Colors.END}")
                return
            print(f"{Colors.BOLD}Knowledge: {k.id}{Colors.END}")
            print(f"  Statement:      {k.statement}")
            print(f"  Status:         {k.status.value}")
            print(f"  Confidence:     {k.confidence:.2f}")
            print(f"  Conditions:     {k.conditions}")
            print(f"  Scope:          {k.scope}")
            print(f"  Horizon:        {k.time_horizon}")
            print(f"  Replications:   {k.replication_count}")
            print(f"  Contradictions: {k.contrary_evidence_count}")
            if k.last_validated_at:
                print(f"  Last Validated: {k.last_validated_at.strftime('%Y-%m-%d')}")
            if k.expires_at:
                print(f"  Expires:        {k.expires_at.strftime('%Y-%m-%d')}")

        elif args.knowledge_command == "extract":
            k = extract_knowledge(
                statement=args.statement,
                hypothesis_ids=args.hypothesis_ids.split(",") if args.hypothesis_ids else [],
                outcome_ids=args.outcome_ids.split(",") if args.outcome_ids else [],
                evidence_summary=args.evidence_summary,
                conditions=args.conditions,
                scope=args.scope,
                time_horizon=args.time_horizon,
                confidence=args.confidence,
            )
            self.scientific.create_knowledge(k)
            print(f"{Colors.GREEN}✓ Knowledge extracted{Colors.END}")
            print(f"  ID:     {k.id}")
            print(f"  Status: {k.status.value}")
            print(f"  Statement: {k.statement[:80]}...")

        elif args.knowledge_command == "transition":
            k = self.scientific.get_knowledge(args.id)
            if not k:
                print(f"{Colors.RED}✗ Knowledge not found: {args.id}{Colors.END}")
                return
            try:
                target = KnowledgeStatus(args.to)
            except ValueError:
                print(f"{Colors.RED}✗ Invalid status. Valid: {[s.value for s in KnowledgeStatus]}{Colors.END}")
                return
            try:
                transition_knowledge(k, target, reason=args.reason)
                self.scientific.update_knowledge(k)
                print(f"{Colors.GREEN}✓ Knowledge transitioned to {target.value}{Colors.END}")
            except ValueError as e:
                print(f"{Colors.RED}✗ {e}{Colors.END}")

        else:
            print(f"{Colors.YELLOW}Usage: oma lab knowledge <command>{Colors.END}")
            print(f"  Commands: list, show, extract, transition")

    def cmd_lab_criterion(self, args):
        if args.criterion_command == "list":
            status_filter = None
            if args.status:
                try:
                    status_filter = DeltaStatus(args.status)
                except ValueError:
                    print(f"{Colors.RED}✗ Invalid status. Valid: {[s.value for s in DeltaStatus]}{Colors.END}")
                    return
            deltas = self.scientific.list_criterion_deltas(
                status=status_filter, dimension=args.dimension, limit=args.limit
            )
            if not deltas:
                print(f"{Colors.YELLOW}⚠ No criterion deltas.{Colors.END}")
                return
            print(f"{Colors.GREEN}✓ {len(deltas)} criterion deltas{Colors.END}\n")
            for d in deltas:
                status_colors = {
                    "pending_review": Colors.YELLOW, "applied": Colors.GREEN,
                    "rejected": Colors.RED,
                }
                sc = status_colors.get(d.status.value, Colors.END)
                print(f"  [{sc}{d.status.value.upper():15s}{Colors.END}] {d.id[:12]}...")
                print(f"       Dimension: {d.dimension}")
                print(f"       Change:    {d.change[:80]}")
                print(f"       Confidence: {d.confidence:.2f}")

        elif args.criterion_command == "propose":
            knowledge_ids = args.knowledge_ids.split(",") if args.knowledge_ids else []
            hypothesis_ids = args.hypothesis_ids.split(",") if args.hypothesis_ids else []
            outcome_ids = args.outcome_ids.split(",") if args.outcome_ids else []

            try:
                delta = propose_delta(
                    knowledge_ids=knowledge_ids,
                    hypothesis_ids=hypothesis_ids,
                    outcome_ids=outcome_ids,
                    dimension=args.dimension,
                    change=args.change,
                    confidence=args.confidence,
                )
                self.scientific.create_criterion_delta(delta)
                print(f"{Colors.GREEN}✓ Criterion delta proposed{Colors.END}")
                print(f"  ID:        {delta.id}")
                print(f"  Dimension: {delta.dimension}")
                print(f"  Status:    {delta.status.value}")
                print(f"\n{Colors.YELLOW}⚠ This delta is PENDING_REVIEW.{Colors.END}")
                print(f"  Human review is required before it can be applied.")
            except ValueError as e:
                print(f"{Colors.RED}✗ {e}{Colors.END}")

        elif args.criterion_command == "apply":
            delta = self.scientific.get_criterion_delta(args.id)
            if not delta:
                print(f"{Colors.RED}✗ Criterion delta not found: {args.id}{Colors.END}")
                return
            if delta.status != DeltaStatus.PENDING_REVIEW:
                print(f"{Colors.RED}✗ Only PENDING_REVIEW deltas can be applied.{Colors.END}")
                return
            print(f"{Colors.BOLD}{Colors.RED}⚠ HUMAN REVIEW REQUIRED{Colors.END}")
            print(f"  Delta:     {delta.id}")
            print(f"  Dimension: {delta.dimension}")
            print(f"  Change:    {delta.change}")
            print(f"  Confidence: {delta.confidence:.2f}")
            print(f"\n  This action applies the criterion delta.")
            print(f"  Type 'yes' to confirm, or anything else to cancel.")
            confirm = input("  > ").strip().lower()
            if confirm == "yes":
                apply_delta(delta)
                self.scientific.update_criterion_delta(delta)
                print(f"{Colors.GREEN}✓ Criterion delta applied{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ Application cancelled{Colors.END}")

        elif args.criterion_command == "reject":
            delta = self.scientific.get_criterion_delta(args.id)
            if not delta:
                print(f"{Colors.RED}✗ Criterion delta not found: {args.id}{Colors.END}")
                return
            reject_delta(delta)
            self.scientific.update_criterion_delta(delta)
            print(f"{Colors.GREEN}✓ Criterion delta rejected{Colors.END}")

        elif args.criterion_command == "metrics":
            hypotheses = self.scientific.list_hypotheses(limit=1000)
            comparisons = self.scientific.list_outcome_comparisons(limit=1000)
            knowledge_list = self.scientific.list_knowledge(limit=1000)

            metrics = compute_criterion_metrics(hypotheses, comparisons, knowledge_list)

            print(f"{Colors.BOLD}{Colors.CYAN}Criterion Metrics{Colors.END}")
            print(f"{Colors.BLUE}—" + "—" * 50 + f"{Colors.END}")

            for dimension, values in metrics.items():
                print(f"\n{Colors.BOLD}{dimension.replace('_', ' ').title()}:{Colors.END}")
                for key, val in values.items():
                    if isinstance(val, float):
                        print(f"  {key.replace('_', ' ').title():30s} {val:.2%}")
                    elif isinstance(val, dict):
                        if val:
                            print(f"  {key.replace('_', ' ').title()}:")
                            for k2, v2 in sorted(val.items()):
                                print(f"    {k2}: {v2}")
                        else:
                            print(f"  {key.replace('_', ' ').title():30s} (none)")
                    else:
                        print(f"  {key.replace('_', ' ').title():30s} {val}")

        else:
            print(f"{Colors.YELLOW}Usage: oma lab criterion <command>{Colors.END}")
            print(f"  Commands: list, propose, apply, reject, metrics")

    def _print_lab_report_header(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}═" * 55)
        print(f"  Scientific Learning Laboratory — Report")
        print(f"═" * 55 + f"{Colors.END}")

    def cmd_run(self, args):
        self.cmd_collect(args)
        print("\n" + "—" * 60 + "\n")
        self.cmd_process(args)

        # Send Telegram notification with quality gate
        try:
            opps = self.db.get_active_opportunities(limit=100)
            stats = self.db.get_event_stats()
            pipeline_result = {
                "events_processed": stats.get("total_events", 0),
                "events_stored": stats.get("unprocessed", 0),
                "opportunities_generated": len(opps),
            }
            from core.engines.telegram_notifier import get_learning_core_stats
            learning_stats = get_learning_core_stats()
            self.notifier.send_run_summary(opps, pipeline_result, learning_stats)
        except Exception as e:
            print(f"[Telegram] Error sending notification: {e}")
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
        
        p_council = subparsers.add_parser("council", help="OSIRIS Agent Council")
        p_council.add_argument("--limit", type=int, default=50)

        # ── Hypothesis commands ──────────────────────────────────
        p_hyp = subparsers.add_parser("hypothesis", help="Manage scientific hypotheses")
        hyp_sub = p_hyp.add_subparsers(dest="hypothesis_command")

        p_hyp_create = hyp_sub.add_parser("create", help="Create a new hypothesis")
        p_hyp_create.add_argument("--title", required=True)
        p_hyp_create.add_argument("--description", required=True)
        p_hyp_create.add_argument("--consequence", required=True, help="Predicted consequence")
        p_hyp_create.add_argument("--conditions", required=True, help="Conditions for the prediction")
        p_hyp_create.add_argument("--invalidation", required=True, help="What would disprove this hypothesis")
        p_hyp_create.add_argument("--confidence", type=float, default=0.5)

        p_hyp_list = hyp_sub.add_parser("list", help="List hypotheses")
        p_hyp_list.add_argument("--status", help="Filter by status (formulated, active, evaluated, archived)")
        p_hyp_list.add_argument("--limit", type=int, default=20)

        p_hyp_show = hyp_sub.add_parser("show", help="Show hypothesis details")
        p_hyp_show.add_argument("id", help="Hypothesis ID")

        p_hyp_transition = hyp_sub.add_parser("transition", help="Transition hypothesis to a new status")
        p_hyp_transition.add_argument("id", help="Hypothesis ID")
        p_hyp_transition.add_argument("--to", required=True, help="Target status")
        p_hyp_transition.add_argument("--reason", default=None, help="Reason for transition")

        p_hyp_archive = hyp_sub.add_parser("archive", help="Archive a hypothesis")
        p_hyp_archive.add_argument("id", help="Hypothesis ID")
        p_hyp_archive.add_argument("--reason", default=None)

        # ── Evidence commands ────────────────────────────────────
        p_ev = subparsers.add_parser("evidence", help="Manage evidence linked to hypotheses")
        ev_sub = p_ev.add_subparsers(dest="evidence_command")

        p_ev_add = ev_sub.add_parser("add", help="Add evidence to a hypothesis")
        p_ev_add.add_argument("hypothesis_id", help="Hypothesis ID")
        p_ev_add.add_argument("--direction", required=True, choices=["supports", "contradicts"])
        p_ev_add.add_argument("--weight", type=float, default=0.5, help="Evidence weight (0.0-1.0)")
        p_ev_add.add_argument("--content", required=True, help="Evidence description")
        p_ev_add.add_argument("--source", default="manual", help="Source identifier")
        p_ev_add.add_argument("--reliability", type=float, default=1.0, help="Source reliability (0.0-1.0)")

        p_ev_list = ev_sub.add_parser("list", help="List evidence for a hypothesis")
        p_ev_list.add_argument("hypothesis_id", help="Hypothesis ID")
        p_ev_list.add_argument("--limit", type=int, default=50)

        # ── Scientific status ────────────────────────────────────
        p_sci = subparsers.add_parser("scientific", help="Scientific memory status")
        p_sci.add_argument("--db", default="scientific.db")

        # ── Lab commands ─────────────────────────────────────────
        p_lab = subparsers.add_parser("lab", help="Scientific Learning Laboratory")
        lab_sub = p_lab.add_subparsers(dest="lab_command")

        p_lab_compare = lab_sub.add_parser("compare", help="Compare hypothesis to outcome")
        p_lab_compare.add_argument("hypothesis_id", help="Hypothesis ID")
        p_lab_compare.add_argument("--actual-outcome", required=True, help="What actually happened")
        p_lab_compare.add_argument("--verdict", choices=[v.value for v in Verdict], help="Override auto-detected verdict")
        p_lab_compare.add_argument("--confidence", type=float, default=0.8, help="Comparison confidence (0-1)")
        p_lab_compare.add_argument("--comparison-type", choices=[c.value for c in ComparisonType], default="executed")
        p_lab_compare.add_argument("--error-type", choices=[e.value for e in ErrorType], help="Error type if rejected")
        p_lab_compare.add_argument("--error-detail", help="Details about the error")
        p_lab_compare.add_argument("--knowledge", help="Auto-extract knowledge statement from this comparison")
        p_lab_compare.add_argument("--knowledge-conditions", help="Conditions for auto-extracted knowledge")
        p_lab_compare.add_argument("--knowledge-scope", help="Scope for auto-extracted knowledge")
        p_lab_compare.add_argument("--knowledge-horizon", help="Time horizon for auto-extracted knowledge")
        p_lab_compare.add_argument("--knowledge-confidence", type=float, default=0.3, help="Confidence for auto-extracted knowledge")

        p_lab_knowledge = lab_sub.add_parser("knowledge", help="Manage knowledge items")
        k_sub = p_lab_knowledge.add_subparsers(dest="knowledge_command")

        k_list = k_sub.add_parser("list", help="List knowledge items")
        k_list.add_argument("--status", help="Filter by status")
        k_list.add_argument("--limit", type=int, default=20)

        k_show = k_sub.add_parser("show", help="Show knowledge details")
        k_show.add_argument("id", help="Knowledge ID")

        k_extract = k_sub.add_parser("extract", help="Extract new knowledge")
        k_extract.add_argument("--statement", required=True, help="The knowledge statement")
        k_extract.add_argument("--hypothesis-ids", help="Comma-separated hypothesis IDs")
        k_extract.add_argument("--outcome-ids", help="Comma-separated outcome comparison IDs")
        k_extract.add_argument("--evidence-summary", required=True, help="Summary of evidence")
        k_extract.add_argument("--conditions", required=True, help="When does this knowledge apply?")
        k_extract.add_argument("--scope", required=True, help="Domain: crypto, equities, general, etc.")
        k_extract.add_argument("--time-horizon", required=True, help="intraday, swing, position, secular")
        k_extract.add_argument("--confidence", type=float, default=0.3, help="Initial confidence (0-1)")

        k_transition = k_sub.add_parser("transition", help="Transition knowledge status")
        k_transition.add_argument("id", help="Knowledge ID")
        k_transition.add_argument("--to", required=True, help="Target status")
        k_transition.add_argument("--reason", default=None, help="Reason for transition")

        p_lab_criterion = lab_sub.add_parser("criterion", help="Manage criterion deltas")
        c_sub = p_lab_criterion.add_subparsers(dest="criterion_command")

        c_list = c_sub.add_parser("list", help="List criterion deltas")
        c_list.add_argument("--status", help="Filter by status (pending_review, applied, rejected)")
        c_list.add_argument("--dimension", help="Filter by dimension")
        c_list.add_argument("--limit", type=int, default=20)

        c_propose = c_sub.add_parser("propose", help="Propose a criterion delta")
        c_propose.add_argument("--knowledge-ids", help="Comma-separated knowledge IDs")
        c_propose.add_argument("--hypothesis-ids", help="Comma-separated hypothesis IDs")
        c_propose.add_argument("--outcome-ids", help="Comma-separated outcome IDs")
        c_propose.add_argument("--dimension", required=True, choices=sorted(VALID_DIMENSIONS), help="Criterion dimension")
        c_propose.add_argument("--change", required=True, help="Description of the proposed change")
        c_propose.add_argument("--confidence", type=float, default=0.5, help="Confidence in this delta (0-1)")

        c_apply = c_sub.add_parser("apply", help="Apply a pending criterion delta (requires human confirmation)")
        c_apply.add_argument("id", help="Criterion delta ID")

        c_reject = c_sub.add_parser("reject", help="Reject a pending criterion delta")
        c_reject.add_argument("id", help="Criterion delta ID")

        c_metrics = c_sub.add_parser("metrics", help="Compute and display criterion metrics")

        args = parser.parse_args()
        self.print_banner()
        
        if not args.command:
            parser.print_help()
            return
        
        command_map = {
            "collect": self.cmd_collect, "process": self.cmd_process,
            "opportunities": self.cmd_opportunities, "events": self.cmd_events,
            "status": self.cmd_status, "watch": self.cmd_watch,
            "export": self.cmd_export, "run": self.cmd_run,
            "council": self.cmd_council,
            "hypothesis": self.cmd_hypothesis,
            "evidence": self.cmd_evidence,
            "scientific": self.cmd_scientific_status,
            "lab": self.cmd_lab,
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"{Colors.RED}Comando desconocido: {args.command}{Colors.END}")


if __name__ == "__main__":
    cli = OMACLI()
    cli.run()
