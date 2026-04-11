# FoodBankHub — Stabex International interview rehearsal (business narrative)

Use this document to rehearse a **business-first** story: what problem you solved, who benefits, and how it maps to **supply-chain and operations** thinking relevant to an oil marketing and retail company.

**Official Stabex context (for alignment):** [Who We Are — Stabex International Ltd](https://stabexinternational.com/about/who-we-are/) describes Stabex as a fast-growing oil marketing company in East Africa with **200+ retail stations**, **bulk petroleum** and **14 depots** supplying commercial customers and other stations in landlocked markets; energy solutions including **LPG**; and **ISO 9001 / 14001 / 45001** certifications. Their **mission** emphasizes **teamwork, creativity, innovation, integrity, and reliable service delivery**. Their **core values** include **Performance** (effective and efficient quality delivery), **Environment**, **People** (trust, respect, accountability, teamwork), **Integrity**, **Safety** (first consideration), and **Mutual Advantage** (society through education, employment, enterprise).

---

## 1. Opening hook (30–45 seconds)

“I built **FoodBankHub** — a web platform that coordinates **donors**, **food banks**, and **recipients**. On the surface it’s about food aid; from a **business and operations** angle it’s about fixing **supply chain fragmentation**: matching **supply** (donations and inventory) to **demand** (requests and need), with **visibility** across the chain and fewer manual handoffs. That’s the same class of problem energy companies solve every day: **getting the right product to the right place at the right time**, with **traceability** and **accountability** — whether the product is fuel or food.”

---

## 2. The business problem (plain language)

- **Fragmentation:** Donations, requests, allocations, and delivery status often live in spreadsheets, messages, and ad hoc calls — hard to audit and slow to scale.
- **Poor visibility:** Hard to see what is **promised**, **in transit**, **received**, and **allocated** to final demand (recipients).
- **Inefficient matching:** **Demand signals** (e.g. food bank requests) and **supply** (donations) are easier to align when they’re in **one system** with clear status and roles.
- **Risk of waste / misallocation:** Without a single chain of record, you get delays, duplicate effort, and uncertainty — analogous to **stockouts**, **surplus**, or **unreconciled movements** in physical distribution.

**Interview line:** “I framed it as a **multi-echelon supply network**: upstream suppliers (donors), hub operations (food banks), downstream demand (recipients). The product digitizes that flow.”

---

## 3. What FoodBankHub does (business capabilities — stay factual)

Speak to what the system actually supports (adjust if your demo branch differs):

| Business concept | How you can describe it in the interview |
|------------------|----------------------------------------|
| **Demand** | Food banks / recipients express **need** (e.g. requests); the system captures quantity and status. |
| **Supply** | Donors offer **inventory** (donations) tied to a food bank; types and delivery modes can be categorized. |
| **Matching & fulfillment** | Donations can be linked to **requests**; food banks **allocate** stock to recipients with quantity checks and audit trail. |
| **Logistics state** | **Delivery status** (e.g. pending → in transit → delivered) gives **operational visibility** — similar in spirit to shipment / trip status in fuel logistics. |
| **Governance & reporting** | Role-based access (donor / food bank / recipient / admin), **reports and analytics** for impact and operations — supports **performance** and **accountability**. |

**Honest caveat (builds credibility):** “I did not build a full **forecasting engine** or IoT tank-level telemetry. I built **workflow digitization**, **clear states**, and **reporting** so operators can plan and explain outcomes — the same layer many enterprises implement before advanced optimization.”

---

## 4. Mapping to Stabex (without forcing a false analogy)

You are **not** claiming fuel chemistry or OTS tender expertise. You **are** claiming transferable **operations thinking**:

| Stabex theme (from their public messaging) | How your project echoes it |
|---------------------------------------------|----------------------------|
| **Performance — effective and efficient delivery** | System reduces manual coordination; clear paths from request → donation → allocation → status. |
| **Integrity & accountability** | Actions tied to users and records; less ambiguity than informal channels. |
| **People & teamwork** | Multiple roles (donor, food bank, recipient, admin) must **collaborate through one platform** — like cross-functional ops in retail + supply. |
| **Environment** (careful wording) | In food chains, **waste reduction** and **better allocation** support sustainability; in energy, **efficiency** and **loss reduction** matter similarly — you’re showing you think about **resource efficiency**. |
| **Safety** | Acknowledge Stabex puts safety first; for your domain: **data safety**, **access control**, and **clear processes** reduce operational errors (different industry, same discipline). |
| **Reliable service delivery** | Mirrors their mission language — you built a system aimed at **dependable** fulfillment and communication. |

**One sentence bridge:** “Stabex optimizes **energy** from depots and stations to customers; FoodBankHub optimizes **aid and inventory** from donors through food banks to recipients — same **supply chain discipline**, different product.”

---

## 5. Your draft narrative — polished version (60–90 seconds, memorize loosely)

“During my recent project I built **FoodBankHub**. At its core it’s not only about food distribution — it’s about **supply chain inefficiency**: fragmented information, weak visibility between upstream supply and downstream demand, and manual coordination.

I approached it the way **large distribution businesses** think about logistics: **who has inventory**, **who needs it**, **what’s in motion**, and **what was delivered**. In my domain the nodes are **donors**, **food banks**, and **recipients**; in oil marketing you have **supply points**, **depots**, **retail**, and **customers** — but the **problems rhyme**: fragmentation, delays, and need for **real-time operational truth**.

FoodBankHub **digitizes the chain**: requests and donations, allocation with controls, delivery status, and reporting so organizations can see **throughput**, reduce **misallocation and waste**, and lower **coordination cost**.

Technically I delivered a **production-style web application** with authentication, role-based workflows, data models for the lifecycle, and deployment considerations — but the **story** is **enterprise-style logistics and service delivery**, which applies anywhere **timing, tracking, and efficiency** matter — including industries like yours.”

---

## 6. Likely panel questions — short answers

**Q: Why should an oil company care about a food bank app?**  
**A:** “Because I’m demonstrating **how I analyze a supply network** and build systems for **visibility, matching, and accountability** — skills that transfer to **retail, depot, and bulk** operations where the same patterns appear.”

**Q: What metric would you use to prove success?**  
**A:** “**Cycle time** from request to fulfillment, **fill rate** on requests, **waste / spoilage proxy** (unallocated or expired flow if tracked), **admin hours saved**, and **audit completeness** — all standard ops KPIs.”

**Q: What would you add next with more time/budget?**  
**A:** “**Deeper analytics** (forecasting from history), **integrations** (SMS, payments, inventory devices), **SLA alerts** for stalled deliveries, and **stronger resilience** for scale — same roadmap as maturing a logistics platform.”

**Q: Biggest technical challenge?**  
**A:** “Balancing **flexibility** (many donation types and roles) with **data integrity** and **clear state machines** so operations stay trustworthy.”

**Q: How do you ensure integrity of data?**  
**A:** “Role-based access, validations on allocation quantities, status transitions, and **traceability** of who did what — aligned with how regulated operations expect **controls**.”

---

## 7. Closing (15 seconds)

“I’m excited about Stabex because you combine **scale**, **operational excellence**, and **regional growth** — I want to contribute to systems that make **supply and service delivery** more **reliable, visible, and efficient**, and FoodBankHub is my concrete example of how I approach that class of problem.”

---

## 8. Rehearsal checklist

- [ ] Say **FoodBankHub** once clearly up front; then “the platform / the system.”
- [ ] Name **three actors**: donor → food bank → recipient (maps to any hub-and-spoke network).
- [ ] Mention **one technical anchor** (e.g. web app, roles, database lifecycle) without drifting into a code tutorial.
- [ ] Include **one honest limitation** (no ML forecasting yet) — panels trust that.
- [ ] Tie **one** Stabex value by name (**Performance**, **Integrity**, or **Reliable service delivery**).
- [ ] End with **curiosity about them** (one question): e.g. “How does your team prioritize **visibility** across depots and retail today?”

Good luck with Stabex International.
