<!--
  Staging copy guide — replace GCP claims with current Hostinger reality.
  App stack: Hostinger VPS + Dokploy (Django, Mattermost, Odoo, Postgres, Redis).
  Marketing site: Hostinger WordPress (polysaas.online / azure staging).
  Do NOT claim GKE, Cloud SQL, Cloud Run, or “built on GCP” as current production.
-->

<!-- Preferred short blurbs -->

HOME / FEATURES Architecture card:
Built on Hostinger with Dokploy-managed containers, microservices, and multi-tenant isolation. Enterprise-grade infrastructure that scales with your business.

PRICING intro:
…and get enterprise-grade, multi-tenant infrastructure on Hostinger. No vendor lock-in, no hidden fees.

PRICING footer line:
All plans include core PolySaaS features: multi-tenant isolation, Hostinger hosting, atomic orchestration, and no hidden fees.

ARCHITECTURE intro:
PolySaaS runs on Hostinger VPS infrastructure with Dokploy orchestration, containerized services, and full multi-tenant isolation. Enterprise-grade hosting that scales with your business.

ARCHITECTURE card “Hostinger Platform” (was Google Cloud Platform):
Hosted on Hostinger for reliable production workloads, with Dokploy managing deploys, TLS, and service orchestration across the PolySaaS app stack.

ARCHITECTURE card “Containerized Services” (was Kubernetes Orchestration):
Bundled applications run in containers managed via Dokploy. Rolling updates and service isolation keep the platform operable without tying you to a single hyperscaler control plane.

ABOUT Mike bio:
…cloud-native architecture on modern VPS hosting. Driving the vision…

ABOUT timeline Q1 title:
Platform Foundation & Hostinger Deployment

ABOUT timeline items:
- Hostinger / Dokploy Deployment — Production infrastructure rollout
- (remove or reword “Google Cloud Startup Application” → “Cloud partner / startup programs — Evaluating”)

EXTERNAL APPLICATIONS lead:
The only difference between Bundled Applications and External SaaS Applications is where the external app is hosted — outside the PolySaaS Hostinger environment. Every subscriber can add any SaaS application to their Passthrough Applications and get the same benefits.

Message bus wording:
…publish it once into a message bus (RabbitMQ or equivalent)…
(Keep RabbitMQ; avoid implying GCP Pub/Sub is required.)
