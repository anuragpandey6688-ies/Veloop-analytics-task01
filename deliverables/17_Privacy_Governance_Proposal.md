# 17 · Data Access, Privacy & Governance Proposal

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

VELOOP's own privacy policy (SRC-13) says it collects identity data, device identifiers, IP address, approximate location, login signals, reward and withdrawal records, and ad-tracking data, and shares some of it with ad, offerwall and payout partners. The analytics layer should use **as little of that as possible**.

## Principles

1. **Pseudonymous analytics.** Analytics tables are keyed on `user_id` only. Identity data (name, email, phone) stays in the account/auth system.
2. **Minimisation.** A field enters analytics only if the dictionary (09) names its analytical use. This removes `full_name`, `email`, exact `age`, `gender` and `city` from the supplied structure (DQ-C10).
3. **Consent respected in data.** `marketing_opt_in` can only be true when `consent_status = accepted` (DQ-C04, QC-10).
4. **Environment separation.** Simulated, staging and production data are labelled (`data_environment`) and never mixed (brief rule 12).
5. **No security internals in analytics.** Reason categories are allowed. Fraud thresholds, detection rules and device-fingerprint logic are not (brief rule 4).
6. **Retention.** Raw events and personal data are kept only as long as VELOOP's legal and operational needs require. The periods must be set by VELOOP (A-024). The analyst does not invent them.

## Access model

| role | access | purpose | restriction |
| --- | --- | --- | --- |
| Engineering | Raw events, business tables, quarantine | Technical event implementation and debugging | Restricted fields only in production systems, never in exports |
| Data Analyst | Approved analytical datasets (pseudonymous) + quarantine summaries | KPI computation, quality monitoring | No names, emails, payout details |
| Product / Operations | Dashboards and aggregated tables; operations queue views for withdrawals with withdrawal_id only | Business reporting and operations | Aggregates; record-level only where operationally needed |
| Finance | Wallet, withdrawal and reward aggregates; reconciliation exceptions | Liability and payout tracking | No credentials or payout account details |
| Content Team | Aggregated help-center and feature engagement | Content performance | Aggregates only, minimum group size 10 |
| Intern | Only approved, sanitised or simulated datasets | Learning and analysis tasks | No production personal data |
| Partners (ad/offer/payout) | Nothing from the analytics layer | n/a | Data sharing only through engineering integrations under the privacy policy |

## Sensitivity classes

| Class | Examples | Rule |
| --- | --- | --- |
| Public | Help-center content IDs and categories | No restriction |
| Internal | user_id, events, statuses, amounts | Role-based access; pseudonymous |
| Restricted | state_region, age_band, reason categories, external/payout reference IDs, balance_after | Named roles only; aggregated outputs with a minimum group size of 10 |
| Never in analytics | See list below | Must not leave the source system |

## Information that must never be exposed in analytics

* Passwords and password hashes
* Authentication secrets, session tokens, OAuth tokens
* API keys and partner secrets
* Payment credentials: UPI IDs, bank account numbers, card numbers, PayPal login
* Private credentials of staff or users
* Sensitive security controls: fraud thresholds, detection rules, device-fingerprint logic
* Full names and email addresses in analytics tables
* Precise location and IP addresses in analytics tables
* Government ID or KYC documents (if ever collected)

## Requests from users

The privacy policy offers access, correction and deletion (SRC-13). Analytics must support deletion: a deleted `user_id` is removed from, or irreversibly anonymised in, analytics tables within the same retention cycle, and the action is logged in the change log.

## Work Package Q: analytics change management

| when | what_to_do | owner |
| --- | --- | --- |
| A feature changes | Update coverage matrix row; add/retire events; bump schema_version of affected events; note affected KPIs. | Product |
| An event changes | New schema_version; old and new versions accepted in parallel for a transition window; transformation maps both. | Engineering |
| A reward mechanic changes | Log effective date; KPIs compare only like-for-like periods; annotate dashboards. | Product + Finance |
| A withdrawal method changes | Update payout_method allowed values with effective date; historic values kept. | Operations |
| A field is renamed | Add new field, backfill, deprecate old after one release; never rename in place. | Engineering + Data |
| A KPI definition changes | New KPI version (e.g. K-USR-02 v2); restate history or show break line; founder approval. | Data/Analytics + Founder |
| A dashboard changes | Change log entry; screenshot before/after; notify stakeholders. | Data/Analytics |

### Metric/Event Change Log

| date | change | old_definition | new_definition | reason | affected_kpis | affected_dashboards | affected_reports | owner | version |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-01 | Initial analytics specification v1.0 (this submission) | None (no documented tracking plan) | 46 proposed events, 53 KPIs, 17-entity model, 181-field dictionary | Task 01 foundation | All | All (blueprint) | None yet | Data Analyst (intern) | 1.0.0 |
| 2026-10-01 | EXAMPLE: DAU definition | Supplied is_active flags: login within N days of 2026-09-15 00:00 | K-USR-02: qualifying activity event per IST day | Logins without activity overstate engagement; reference date undocumented | K-USR-02, K-USR-03, K-USR-04, K-USR-05 | 1, 2 | Weekly founder update | Data/Analytics | 1.0.0 |
| YYYY-MM-DD | TEMPLATE: event field renamed | old_field | new_field (old kept until vX) | reason | list | list | list | owner | x.y.z |

Process: proposer fills a change-log row, the data owner reviews the impact on KPIs and dashboards, the founder approves KPI definition changes, engineering ships with a new `schema_version`, and the dashboards are annotated on the effective date.
