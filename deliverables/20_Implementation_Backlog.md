# 20 · Implementation Backlog

Spreadsheet: [`20_Implementation_Backlog.xlsx`](20_Implementation_Backlog.xlsx). Priorities come from the gaps (02), the readiness assessment (18) and the quality audit (13).

| id | priority | requirement | reason | dependency | owner | stage |
| --- | --- | --- | --- | --- | --- | --- |
| BL-01 | Critical | Confirm current logging and live feature list (A-001, A-002) | All later work depends on what exists | None | Engineering + Product | Pre-launch |
| BL-02 | Critical | Stable opaque user_id on every record | Required for cross-event analysis | Authentication | Engineering | Pre-launch |
| BL-03 | Critical | Append-only wallet ledger with transaction_id, related_transaction_id and idempotency_key | Required for wallet analytics and reconciliation; prevents duplicate credits | Wallet service | Engineering | Pre-launch |
| BL-04 | Critical | Reward table separating pending/credited/rejected/reversed/corrected with idempotency_key | Distinguishes activity from actual credit (C3) | Reward service | Engineering | Pre-launch |
| BL-05 | Critical | Withdrawal status history + reason categories + debit/refund links | Withdrawal KPIs and trust | Payout flow | Engineering + Operations | Pre-launch |
| BL-06 | Critical | Store all timestamps in UTC; report on IST day | Daily KPIs and streaks align with claim window | Database | Engineering | Pre-launch |
| BL-07 | High | Server-side events for the Critical events in deliverable 15 (event_id, schema_version) | Product measurement | BL-02 | Engineering | Pre-launch |
| BL-08 | High | task_activity with activity_id, validation_status, failure_category, external_reference_id | Earning funnel and partner reliability | Task service, partner callbacks | Engineering | Pre-launch |
| BL-09 | High | Referral table linking referrer and referred user with stage timestamps | Referral funnel (gap G02) | Referral service | Engineering | Pre-launch |
| BL-10 | High | Account status history table | Lifecycle KPIs (gap G04) | Account service | Engineering | Pre-launch |
| BL-11 | High | Data quality checks QC-01 to QC-17 | Prevent unreliable reporting | Data layer | Data/Engineering | Pre-launch |
| BL-12 | High | Remove names/emails/exact age/gender/city from analytics extracts; consent rule for marketing_opt_in | Privacy (DQ-C04, DQ-C10) | Governance approval | Engineering + Founder | Pre-launch |
| BL-13 | High | Publish VE/Gem/Token conversion rate table with effective dates | Reward liability in INR (A-010) | Finance decision | Founder / Finance | Pre-launch |
| BL-14 | Medium | Client events (views, opens, onboarding steps) and sessions | UX funnels and returning users | BL-07 | Engineering | Launch |
| BL-15 | Medium | Transformation models + KPI tables (dbt Core or scheduled SQL) | Reproducible KPIs | BL-07, BL-11 | Data/Analytics | Launch |
| BL-16 | Medium | Approve KPI catalogue v1 and owners | Single source of truth | None | Founder + Data | Launch |
| BL-17 | Medium | Support ticket categories and timestamps (tool or structured inbox) | Support KPIs | A-019 | Operations | Launch |
| BL-18 | Medium | Advanced dashboards (7 dashboards in deliverable 14) | Management reporting | Production data, BL-15 | Data/Analytics | Post-launch |
| BL-19 | Low | Warehouse migration (object storage + columnar warehouse) | Only when DB load or volume justifies | Volume evidence | Engineering | Post-launch |
| BL-20 | Low | Instrument future features (Lucky Draw etc.) through change log | Not live yet | Feature launch | Product | Post-launch |

**Sequencing logic:** identity and money integrity come first (BL-01 to BL-06), because an error there corrupts every later KPI and directly affects users' money. Event tracking and quality checks follow. Dashboards come last, because a dashboard built before the data is trustworthy would show confident but wrong numbers.
