# Anti-Goals

*What O.M.A.-C.O.R.E. intentionally refuses to become, and why.*

---

## Purpose

A project is defined not only by what it pursues, but by what it rejects. Anti-goals provide clarity by establishing boundaries. Every proposed feature that moves the project toward an anti-goal must justify its existence with extraordinary evidence.

---

## Anti-Goal 1: NOT a Chatbot

**Description:** A conversational interface that answers user questions, generates text, or engages in dialogue.

**Why refuse:** Chatbots optimize for conversational engagement, not decision quality. They are evaluated by user satisfaction, not outcome improvement. The feedback loops are social, not operational — the system learns to please, not to judge.

**Confusion risk:** O.M.A.-C.O.R.E. may use language models as components. Using a language model does not make the project a chatbot. A language model used for hypothesis generation or evidence classification is a tool. A language model used as the primary user interface is an anti-goal.

**Boundary:** The system should explain its reasoning, not converse. Explanations serve learning. Conversation serves engagement. These are different objectives.

---

## Anti-Goal 2: NOT a Dashboard

**Description:** A visual interface displaying metrics, charts, and system state.

**Why refuse:** Dashboards optimize for visibility, not understanding. They display what is happening, not why it matters. They create the illusion of control without improving the underlying decision quality.

**Confusion risk:** The project may eventually have monitoring tools. Monitoring is not a dashboard. Monitoring answers "is the system functioning correctly?" A dashboard answers "what do the numbers look like?" These are different questions.

**Boundary:** The system should focus on improving decisions, not displaying them. If a visualization does not improve decision quality, it is decoration.

---

## Anti-Goal 3: NOT a Prediction Machine

**Description:** A system whose primary output is predictions about future prices, events, or outcomes.

**Why refuse:** Prediction is a means, not an end. The goal is better decisions, not better predictions. A system that predicts perfectly but acts poorly has failed. A system that predicts modestly but acts wisely has succeeded.

**Confusion risk:** The system will make predictions as part of its operation. Every hypothesis is a kind of prediction. But prediction is a component, not the output. The output is decisions.

**Boundary:** Evaluate the system by decision quality, not prediction accuracy. If prediction accuracy improves but decision quality does not, something is wrong.

---

## Anti-Goal 4: NOT an AI Wrapper

**Description:** A thin layer over a third-party AI model that adds minimal value beyond prompt engineering.

**Why refuse:** AI wrappers have no durable advantage. When the underlying model changes, the wrapper breaks or becomes obsolete. The model provider can always integrate the wrapper's functionality. The value is owned by the model, not the wrapper.

**Confusion risk:** O.M.A.-C.O.R.E. may use AI models as components. Using AI is not being an AI wrapper. The distinction is whether the project's core value depends on the specific model. If replacing the model with a different one would not change the system's fundamental capability, it is not a wrapper.

**Boundary:** The project's core value must be in its structure — memory, hypotheses, learning, criterion — not in any specific AI model. The model should be replaceable.

---

## Anti-Goal 5: NOT a Generic Agent Framework

**Description:** A platform for building any kind of autonomous agent, applicable to any domain.

**Why refuse:** Generic frameworks optimize for flexibility, not depth. They enable many use cases but excel at none. O.M.A.-C.O.R.E. should develop deep criterion in specific domains before considering generalization.

**Confusion risk:** The system uses agents (MarketAgent, RiskAgent). This does not make it a general agent framework. The agents are specialized for a specific architecture, not designed for arbitrary use.

**Boundary:** Every agent in the system must serve the consequence-to-criterion pipeline. Agents that could be removed without affecting criterion development are unnecessary.

---

## Anti-Goal 6: NOT a News Aggregator

**Description:** A system whose primary function is collecting, filtering, or summarizing news and information.

**Why refuse:** News aggregation is a commodity. The value is not in collecting information but in knowing what information matters. An aggregator that collects everything but understands nothing is noise multiplied.

**Confusion risk:** The system collects events. This is not aggregation. Events are inputs to consequence detection, not outputs for user consumption.

**Boundary:** Events should be processed, not presented. The system's output is decisions and explanations, not event summaries.

---

## Anti-Goal 7: NOT a Social Media Automation Platform

**Description:** A system that generates, schedules, or posts content to social media platforms.

**Why refuse:** Social media optimization is a shallow application of intelligence. It optimizes for engagement metrics that correlate poorly with real-world outcomes. It trains the system for attention, not criterion.

**Confusion risk:** A Creator profile may eventually produce content. Content production is not social media automation. The difference is whether the content serves a consequence-driven purpose or an engagement-driven purpose.

**Boundary:** Content should be produced because the system detected a consequence worth communicating, not because a schedule requires filling.

---

## Anti-Goal 8: NOT a Collection of Indicators

**Description:** A library of technical indicators, pattern recognizers, or signal generators that users can mix and match.

**Why refuse:** Indicators are tools, not intelligence. A system defined by its indicators is limited by its library. The intelligence is in knowing which indicators matter in which context, not in having the largest collection.

**Confusion risk:** The system uses technical indicators (RSI, SMA, ATR). This does not make it a collection of indicators. The indicators serve the agent architecture, not the other way around.

**Boundary:** Indicators should be invisible to the user. The user should interact with consequences and decisions, not with indicator values.

---

## Anti-Goal 9: NOT a Signal Spammer

**Description:** A system that generates high volumes of trading signals, alerts, or recommendations regardless of quality.

**Why refuse:** Signal volume is inversely correlated with signal value in most systems. A system that generates 100 signals per day trains the user to ignore signals. A system that generates one signal per week trains the user to pay attention.

**Confusion risk:** The OSIRIS system generates signals as part of its pipeline. Signal generation is internal, not external. The user should see decisions, not signals.

**Boundary:** The system should generate the minimum number of signals necessary for its learning process. Any signal that does not lead to a decision or a learning opportunity is waste.

---

## Anti-Goal 10: NOT an Enterprise ERP

**Description:** A comprehensive business management system covering operations, finance, HR, CRM, and other enterprise functions.

**Why refuse:** Enterprise systems are broad by design, shallow by necessity. O.M.A.-C.O.R.E. should be deep in specific domains before expanding. Premature breadth prevents depth.

**Confusion risk:** The Entrepreneur profile may eventually inform business decisions. This is not an ERP. An ERP manages operations. O.M.A.-C.O.R.E. would advise on strategic decisions — which market to enter, which product to build, which relationship to invest in.

**Boundary:** The system should advise, not administer. It should improve the quality of strategic decisions, not replace operational software.

---

## Anti-Goal 11: NOT "AI for Everything"

**Description:** Applying AI capabilities indiscriminately to any problem regardless of whether it serves the project's purpose.

**Why refuse:** "AI for everything" is not a strategy. It is an abdication of strategy. Every application of AI should be justified by the project's principles, not by the availability of AI capabilities.

**Confusion risk:** The project will explore new applications over time. Exploration should be guided by principles, not by technological opportunism.

**Boundary:** Ask: "Does this application help the user make better decisions?" If the answer is unclear, defer.

---

## Final Principle

*Every feature that moves the project toward these anti-goals must justify its existence with extraordinary evidence.*

The burden of proof is on the proposer. The default answer is no.
