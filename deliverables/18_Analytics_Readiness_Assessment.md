# 18 · Analytics Readiness Assessment

Scorecard: [`18_Analytics_Readiness_Assessment.xlsx`](18_Analytics_Readiness_Assessment.xlsx). Scale: 0 = Not started / no evidence; 1 = Ad hoc; 2 = Defined (proposed, not implemented); 3 = Implemented, not monitored; 4 = Implemented and monitored.

The scores reflect what could be **verified** as of 2026-10-01. A low score means "no evidence available to the analyst", not "VELOOP has not built it". Engineering may already have some of these pieces (A-001).

| area | score_0_to_4 | score_meaning | evidence | biggest_gap | priority | reason |
| --- | --- | --- | --- | --- | --- | --- |
| Event coverage | 0 | Not started / no evidence | No evidence of any analytics events (A-001); supplied data is a user snapshot. | No events verified | Critical | Without events no engagement, funnel or retention KPI can be produced. |
| Data model | 1 | Ad hoc | Proposed 18-entity model (deliverable 10); not implemented. | No ledger, no status history verified | Critical | Wallet and reward reporting cannot be trusted without a ledger and stable transaction IDs. |
| Data dictionary | 2 | Defined (proposed, not implemented) | Supplied dictionary has 25 fields (2 columns undocumented); full proposed dictionary in deliverable 09. | Real system field names unknown | High | Engineers and analysts may use different names for the same thing. |
| KPI definitions | 2 | Defined (proposed, not implemented) | Reproducible definitions proposed in deliverable 11; none approved. | No approval or owners | High | Unapproved definitions lead to conflicting numbers in reports. |
| Data quality | 1 | Ad hoc | Audit of supplied data found duplicates, malformed dates, impossible field combinations and a consent conflict (deliverable 13). | No automated checks in place | High | Known defect types would reach dashboards unchecked. |
| Dashboard readiness | 0 | Not started / no evidence | Blueprint only (deliverable 14). | No production data | Medium | Dashboards depend on events and models first; building them now would show simulated or empty data. |
| Engineering instrumentation | 0 | Not started / no evidence | None verified. | No event_id/idempotency verified | Critical | Without a stable transaction ID, reliable wallet transaction deduplication cannot be guaranteed. |
| Access control | 1 | Ad hoc | Privacy policy exists; no analytics access model documented; supplied dataset contains PII. | PII in analytics extracts | High | Personal data is exposed beyond need. |
| Documentation | 2 | Defined (proposed, not implemented) | Help center is detailed; this submission adds the analytics documentation. | Internal docs on data unknown | Medium | Knowledge sits with individuals. |
| Reporting | 0 | Not started / no evidence | No reporting process known; homepage figures unverifiable (A-021). | No trusted source of truth | High | Public or management figures cannot be traced to data. |

**Overall: 9 / 40.** VELOOP has strong user-facing policy documentation (help center), but there is no verified analytics foundation behind it yet. Every priority above states its reason, as the brief requires.

## Gap list behind the scores

| gap_id | gap | evidence | impact | priority |
| --- | --- | --- | --- | --- |
| G01 | No event-level activity data | Supplied data is one snapshot row per user (last_login, lifetime_sessions, flags). | DAU/WAU/MAU, retention and funnels cannot be computed. | Critical |
| G02 | Referred users cannot be linked to referrers | Users has referral_source_detail = 'Friend/Family' only; no referral_id or referrer_user_id. | Referral funnel and referral cost cannot be measured. | Critical |
| G03 | Timestamps have no timezone | registration_datetime and last_login_datetime are naive. | Day boundaries can be wrong by 5.5 h; daily reward/streak KPIs misalign with the IST claim window. | High |
| G04 | No account status history | account_status is current state only. | Suspension trends and lifecycle timing cannot be measured. | High |
| G05 | Balances without a ledger | xp_balance is a stored balance; no transactions. | Balances cannot be reconciled or explained. | Critical |
| G06 | Undocumented derived fields | is_active_7d/30d and days_since_registration use an unstated reference date (inferred 2026-09-15 00:00) and login-based activity. | Flags are not reproducible; definitions conflict with qualifying-activity DAU. | Medium |
| G07 | Seven of eight expected datasets missing | Only Users supplied. | Relationship and KPI tests impossible on supplied data (J2/J3). | High |
| G08 | No session identifier | Only a lifetime counter. | Session-level and returning-user analysis impossible. | High |
| G09 | No event_id / idempotency key | No unique event or transaction identifiers in supplied structure. | Duplicate events/credits cannot be detected. | Critical |
| G10 | No third-party tracking fields | No provider_id, external_reference_id or validation status. | Partner tracking failures cannot be separated from VELOOP failures (C4). | High |
| G11 | No onboarding or verification timestamps | Status fields only. | Time-to-onboard and cohort-based rates impossible. | Medium |
| G12 | Personal data in analytics dataset | full_name, email, exact age, gender, city present. | Privacy risk with no analytical need. | High |
| G13 | Platform/device semantics unclear | platform = Web for all; primary_device mixes OS values; app status unknown. | Platform split unreliable. | Low |
| G14 | No currency conversion rates | Not published or supplied. | Reward liability in INR cannot be computed. | High |
| G15 | Consent and marketing opt-in conflict | 34 users opted in while consent pending. | Marketing audience may include non-consented users. | High |
| G16 | Supplied dictionary incomplete | platform and country undocumented; no allowed values for account_status beyond 'controlled list'. | Ambiguous fields. | Low |
