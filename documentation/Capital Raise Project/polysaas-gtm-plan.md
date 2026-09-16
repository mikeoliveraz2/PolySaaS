# PolySaaS Go-to-Market Plan

## Executive Summary

PolySaaS goes to market in three sequenced waves, each building on the credibility and infrastructure of the one before it:

1. **Direct SMB Subscribers** — operators running 2-3 SaaS tools who subscribe to PolySaaS directly, with or without adopting the bundled applications (Odoo, Nextcloud, Mattermost, WordPress, Liferay, Dolibarr).
2. **SaaS Vendors (Embedded/White-Label)** — vendors who deploy PolySaaS *under the covers* of their own product to give their subscribers self-service customization and integration, without PolySaaS being customer-visible.
3. **Application Development Platform** — PolySaaS repositions from integration/orchestration tool to a platform for building new multi-tenant applications, or converting existing single-tenant, on-premise applications into multi-tenant SaaS using Dynamic Orchestration and Atomic Services. The pairing of Liferay (portal/portlet framework) and WordPress (content/publishing) among the bundled apps gives this wave a concrete, demoable front-end layer rather than an abstract platform claim.

Each wave has a distinct buyer, a distinct proof point, and a distinct piece of content already live or in progress (the blog is currently doing double duty as both wave-1 proof and wave-3 thought leadership — see Content Strategy below).

---

## Wave 1: Direct SMB Subscribers (Now)

**Who:** Operators of small businesses running 2-3 SaaS applications (Slack, HubSpot, QuickBooks-adjacent tools, etc.), who may or may not adopt PolySaaS's own bundled apps (Odoo, Nextcloud, Mattermost, WordPress, Dolibarr, Liferay, Monitor Logger, PolySysMon).

**Why they buy:** They're priced out of enterprise iPaaS (MuleSoft, Boomi) and outgrowing point-tool automation (Zapier, Make) the moment they need more than trigger-action recipes — real customization, real orchestration, without hiring a developer.

**Proof point already live:** The pricing page itself is the pitch — Starter ($29/mo, one bundled app), Team ($49/mo, three bundled apps), Unlimited ($99/mo, all bundled apps + full orchestration), with external SaaS (BYOL) at $10/mo/ea. This tier structure is built for exactly this buyer: low commitment, expandable, self-serve.

**Primary offer:** Founders Beta Circle — restructured to $10/mo for six months, for any number of apps, bundled or not. This lowers the commitment bar even further than the original $100 one-year promo and removes the "which apps do I pick" friction entirely — a prospect can bring their whole stack in from day one. This is the wedge: low-risk trial that converts into a paid tenant once the buyer sees their own stack orchestrated.

**Channel motion:**
- Content-led: blog posts that show, not tell (the "One Event, Four Apps" and "Capture Once, Orchestrate Everywhere" posts are the right format — concrete before/after, not abstract platform claims)
- Demo-first funnel: every CTA on the site already routes to "Sign Up for a Demo" — keep that as the single conversion action rather than fragmenting into multiple CTAs
- Direct comparison content: posts like "The old way and the PolySaaS Way" (SAP/Salesforce/NetSuite point-to-point vs. Pub/Sub orchestration) work for this buyer if simplified — SMB operators don't run SAP, but they recognize "brittle point-to-point integrations" as their own pain

**What to watch:** This segment is price-sensitive and will churn fast if the bundled apps (Odoo, Dolibarr, etc.) feel like the product rather than the orchestration layer. Messaging should keep the emphasis on *unification and customization*, not on being "yet another app bundle."

---

## Wave 2: SaaS Vendors — Embedded / White-Label (Next)

**Who:** SaaS vendors who want to offer their own subscribers customization and integration capability, without building and maintaining that infrastructure themselves. PolySaaS runs *under the covers* — the vendor's subscribers may never see the PolySaaS name.

**Why they buy:** Every SaaS vendor eventually hits the same wall: subscribers want integrations and light customization, and building/maintaining a general-purpose integration layer is expensive, slow, and not the vendor's core competency. PolySaaS becomes their integration and customization engine, white-labeled.

**Positioning shift required:** Wave 1 messaging ("orchestrate your SaaS stack") speaks to an *operator*. Wave 2 needs to speak to a *vendor* — this is a build-vs-buy infrastructure decision made by a founder or CTO, not a workflow decision made by an ops person. This matches the existing GTM point paper's framing of this as the primary commercial path (referred to internally as Motion B), targeting CTO-level buyers around SaaS sprawl, composable architecture, RBAC/multi-tenancy, and vendor exit governance.

**Proof points to build/feature:**
- **PolySniffer** as the differentiator for this buyer specifically — passive discovery of protocols, cookies, headers, and integration surface across a vendor's own app and their customers' other tools, without demanding API access up front. This is a vendor-grade capability, not an SMB-facing one; lead with it in vendor-directed content.
- **Atomic Services + OpenAPI/Swagger** — every integration endpoint documented and testable, which is the language a vendor's engineering team needs to evaluate a build-vs-buy decision.
- The HubSpot integration post ("From Complex Proxy to Smart Passthrough + Popup") is a strong technical credibility piece for this exact audience — it's a war story about solving a hard multi-tenant integration problem, which is precisely what a vendor evaluating PolySaaS needs to see solved already.

**Channel motion:**
- Not blog-led the way Wave 1 is — this is a sales-assisted, technical-evaluation motion. The white paper ("The Composable Enterprise") and the GTM point paper / pitch deck materials are the right assets, pointed at CTOs and technical founders directly rather than discovered organically.
- Direct outreach to SaaS vendors who are visibly struggling with integration support load (support forums, G2/Capterra complaints about "no API," "can't customize," "no Zapier support")
- Partnership motion: the "external applications, BYOL" pricing model already proves the architecture supports vendor-owned licensing — this is worth turning into explicit partner/reseller terms once the first vendor design partner is signed.

**What to watch:** This wave depends on Wave 1 generating enough live orchestration examples and uptime history to be credible to a vendor's engineering team. Don't start vendor outreach until there's a track record to point to.

---

## Wave 3: Application Development Platform (Later This Year)

**Who:** Enterprise architects, CTOs, and digital leaders — the audience the "Composable Enterprise" white paper already names directly — who need to either build new multi-tenant applications or convert existing single-tenant, on-premise applications into multi-tenant SaaS.

**Why they buy:** This is the most ambitious and highest-value positioning: PolySaaS stops being "the orchestration layer on top of your SaaS stack" and becomes the platform you build *on*. Dynamic Orchestration and Atomic Services — already built for connecting existing apps — become the engine for standing up new ones, and for taking a legacy single-tenant application and wrapping it in multi-tenancy without a rewrite.

**Proof point already in motion:** "THE COMPOSABLE ENTERPRISE" white paper blog post already stakes this claim publicly (subtitled "Leveraging PolySaaS as an Application Development Engine"). This wave isn't starting from zero — it's a matter of sequencing the rest of the GTM motion to catch up to a claim already made.

**A specific accelerant for this wave:** Liferay and WordPress are both already bundled applications, and their pairing is a meaningfully stronger Wave 3 asset than either alone. Liferay brings enterprise portal/portlet architecture — personalized, role-based, multi-tenant presentation — while WordPress brings flexible, fast-to-build content and front-end publishing. Coupled together under PolySaaS's orchestration, they give a prospective Wave 3 customer a ready-made front-end layer for whatever new multi-tenant application or converted legacy app they're building, without having to build a portal/UI framework from scratch. This is worth calling out explicitly in Wave 3 materials as a concrete "here's what you get on day one" answer to the otherwise abstract pitch of "build applications on PolySaaS" — it turns the platform claim into a specific, demoable solution set (portal + CMS + orchestration + the rest of the bundled stack underneath).

**What needs to exist before this wave launches for real:**
- A concrete, demoable example of a single-tenant app converted to multi-tenant SaaS via PolySaaS — this wave lives or dies on one strong case study, the same way Wave 1 leans on the four-app orchestration demo video.
- Clear articulation of where PolySaaS's Machine Learning/Mapping Engine (already positioned for cross-app data mapping like Dolibarr → Odoo) extends to net-new application logic, not just data sync — this is the technical leap this wave's buyer will interrogate hardest.
- Updated pricing/packaging: the current three-tier pricing (Starter/Team/Unlimited, priced per user per bundled app) is built for Wave 1 subscribers, not for a platform-licensing or dev-platform pricing model. Wave 3 likely needs its own pricing motion (e.g., platform license + usage, or per-application-built pricing) before it can be sold, not just marketed.

**Channel motion:**
- Continued white paper / thought-leadership content aimed at enterprise architects — this is a long sales-cycle, high-trust motion, not a self-serve one
- Conference/analyst-style positioning (the "AI Isn't Killing SaaS" response post is the right register — reacting to and reframing an industry conversation rather than only talking about the product)
- This wave should be seeded with warm relationships from Wave 2 vendor partners — a vendor who has already trusted PolySaaS as their embedded integration layer is a natural first candidate for "let's convert your on-prem product to multi-tenant SaaS" once that capability is real.

---

## How the Three Waves Reinforce Each Other

- Wave 1 generates the live orchestration examples, uptime history, and case-study content that Wave 2 needs to be credible to vendor engineering teams.
- Wave 2 generates vendor relationships and multi-tenant, white-label deployment experience that Wave 3 needs before it can credibly claim "we'll turn your app into multi-tenant SaaS."
- Wave 3 is the highest ceiling but has the longest sales cycle and currently the least proof — it should be marketed now (the white paper is already doing that) but not sold hard until Wave 2 produces at least one real embedded-vendor deployment to point to.

## Content Strategy Alignment

The blog is currently serving two waves at once, which is fine as long as it's intentional:

| Post type | Wave it serves |
|---|---|
| Concrete demo walkthroughs ("One Event, Four Apps," "Capture Once, Orchestrate Everywhere") | Wave 1 — operator-legible, shows the product working |
| Technical war stories (HubSpot proxy-to-passthrough post) | Wave 2 — vendor engineering credibility |
| Industry-reaction and strategic framing (Jason Lemkin response, "old way vs. PolySaaS way") | Wave 2/3 — CTO and architect-level framing |
| White paper content ("The Composable Enterprise") | Wave 3 — staking the platform claim ahead of the capability |

Going forward, tag or otherwise track which wave each new post is written for — it will keep the blog from reading like it's talking to three different buyers in the same voice.

## Immediate Next Steps

1. Keep Wave 1 running as-is — Founders Beta Circle + demo-first CTA is working infrastructure; don't disrupt it while building Wave 2 assets.
2. Draft vendor-specific landing content (separate from the SMB homepage) that leads with PolySniffer and Atomic Services/OpenAPI, not with the bundled-app pricing grid — a vendor evaluating build-vs-buy doesn't want to see "$29/mo per user."
3. Identify 3-5 target SaaS vendors for direct outreach once Wave 1 has a few months of live orchestration history to reference.
4. Scope the pricing/packaging question for Wave 3 now, even though the wave itself launches later — platform-usage pricing takes longer to design than to announce.
5. Start tracking one concrete single-tenant-to-multi-tenant conversion candidate to serve as the Wave 3 proof point when that capability ships.
