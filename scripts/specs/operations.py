"""Work Packages L (quality controls), M (dashboards), N (developer handoff extras), O (pipeline),
P (access and governance), Q (change management), R (readiness scorecard) and the backlog."""

# ------------------------------------------------------------------ L: quality control framework
LAYERS = ["Application", "Data Collection", "Raw Data", "Transformation", "Analytics Layer", "Dashboard"]
# rule id, rule, layer(s), check logic, action on failure, owner, catches (DQ issue ids)
DQ_RULES = [
    ("QC-01", "ID validation", "Application; Data Collection", "IDs generated server-side; non-null; match agreed pattern; event_id generated once and reused on retry.", "Reject event at collection; alert engineering.", "Engineering", "DQ-M02, DQ-U01"),
    ("QC-02", "Primary key uniqueness", "Raw Data", "COUNT(*) = COUNT(DISTINCT pk) per load; duplicates moved to quarantine table.", "Quarantine duplicates; keep first by received_at_utc.", "Data/Analytics", "DQ-U01, DQ-M01"),
    ("QC-03", "Duplicate event / transaction", "Data Collection; Raw Data", "Dedup on event_id; wallet and reward writes protected by idempotency_key unique index.", "Drop duplicate events; block duplicate ledger rows.", "Engineering", "DQ-M12"),
    ("QC-04", "Allowed status values", "Application; Transformation", "Enum check against dictionary allowed values (case-sensitive at source, lower-case normalisation only in transformation with a mapping log).", "Reject at source; quarantine in transformation.", "Engineering", "DQ-M05, DQ-M06"),
    ("QC-05", "Timestamp format and timezone", "Application; Data Collection", "ISO 8601 UTC with Z; reject unparseable; flag event_timestamp_utc more than 5 min in the future or before account creation.", "Reject or quarantine; never guess.", "Engineering", "DQ-U02, DQ-M03, DQ-M04, DQ-C06"),
    ("QC-06", "Referential integrity", "Transformation", "Every FK resolves in its parent table (users, tasks, sessions, wallet).", "Hold orphan rows out of KPIs; daily orphan report.", "Data/Analytics", "DQ-M11"),
    ("QC-07", "Required and conditional fields", "Application; Transformation", "Required fields non-null; conditional rules (e.g. reason_category when rejected; last_login when sessions > 0).", "Reject at source; flag in transformation.", "Engineering", "DQ-U-MISS-*, DQ-U04, DQ-M10"),
    ("QC-08", "Numeric validity", "Application; Transformation", "Amounts numeric, > 0, integer for credits; direction carries sign.", "Reject; quarantine.", "Engineering", "DQ-M08, DQ-M09"),
    ("QC-09", "State machine transitions", "Application; Transformation", "Only allowed transitions (deliverable 06/05); status-history timestamps non-decreasing.", "Block invalid transition in backend; flag in transformation.", "Engineering", "DQ-M14"),
    ("QC-10", "Cross-field consistency", "Transformation", "e.g. active_days >= 1 when sessions > 0; marketing_opt_in only with consent accepted; final_amount = 0 when reversed.", "Flag; fix source logic.", "Data/Analytics", "DQ-C01, DQ-C02, DQ-C03, DQ-C04"),
    ("QC-11", "Event naming", "Application; Data Collection", "event_name in catalogue and matches ^[a-z]+(_[a-z]+)+$; schema_version known.", "Reject unknown events; alert.", "Engineering", "DQ-M13, DQ-M07"),
    ("QC-12", "Text hygiene", "Transformation", "Trim whitespace; normalise case for enums with mapping log.", "Auto-fix with log.", "Data/Analytics", "DQ-M07, DQ-M06"),
    ("QC-13", "Ledger reconciliation", "Analytics Layer", "Credited wallet-unit rewards = reward_credit rows; withdrawals = redemption_debit rows; balances = sum of ledger.", "Exception report (K-WAL-05); block money dashboards if exceptions > 0 unexplained.", "Data/Analytics + Finance", "S06, S07, S08"),
    ("QC-14", "Derived fields computed downstream", "Transformation", "No derived fields stored in source tables; as-of timestamp stored with every derived flag.", "Recompute.", "Data/Analytics", "DQ-U03, DQ-C05, DQ-C07"),
    ("QC-15", "Volume and freshness monitoring", "Raw Data; Dashboard", "Daily row counts vs trailing 7-day median; last event time per source; late-arrival share.", "Alert owner; show 'data delayed' banner on dashboard.", "Data/Analytics", "Pipeline failures"),
    ("QC-16", "Environment separation", "Data Collection; Dashboard", "data_environment = production enforced on every dashboard query.", "Block dashboard query.", "Data/Analytics", "DQ-C12, integrity rule 12"),
    ("QC-17", "Personal-data minimisation", "Transformation", "Analytics tables only contain dictionary-approved fields; no names, emails, payment details.", "Drop columns; alert.", "Data/Analytics", "DQ-C10"),
]

# ------------------------------------------------------------------ M: dashboards
# dashboard, visual, metric (KPI), calculation, source, visualization, filters, dimensions, date range, refresh, business question, decision supported
V = [
    ("1 Executive Overview", "Active users trend", "K-USR-02, K-USR-04", "DAU daily line with MAU overlay", "feature_events", "Line chart", "platform, acquisition_source", "IST day", "Last 90 days", "Daily", "Is engaged usage growing?", "Where to focus growth vs retention effort"),
    ("1 Executive Overview", "Engagement summary tiles", "K-ENG-04, K-ENG-09", "Current value + change vs previous period", "task_activity, feature_events", "Stat tiles", "date range", "-", "Last 7 days vs prior 7", "Daily", "Is earning activity healthy?", "Escalate funnel drops"),
    ("1 Executive Overview", "Reward activity", "K-RWD-02, K-RWD-03", "Credited volume per unit; reversal rate", "rewards", "Stacked bars per unit (no unit summing)", "unit, feature", "week", "Last 12 weeks", "Daily", "How much reward value is issued and how much reversed?", "Budget and quality review"),
    ("1 Executive Overview", "Wallet activity", "K-WAL-02, K-WAL-03, K-WAL-05", "Credits vs redemptions per unit; exception count", "wallet_transactions", "Paired bars + exception badge", "unit", "week", "Last 12 weeks", "Daily", "Is the ledger consistent and how fast is value redeemed?", "Block decisions if exceptions > 0"),
    ("1 Executive Overview", "Withdrawal activity", "K-WDR-01, K-WDR-03, K-WDR-06", "Requests, open queue, P90 processing hours", "withdrawals", "Tiles + line", "payout_method", "day", "Last 30 days", "Hourly", "Are payouts flowing within the published window?", "Staff review queue; contact payout partner"),
    ("1 Executive Overview", "Referral activity", "K-REF-02, K-REF-04", "Registrations vs conversions", "referrals", "Funnel", "referral_channel", "week", "Last 12 weeks", "Daily", "Do referrals bring genuine users?", "Adjust referral reward/rules"),
    ("2 User Analytics", "Registrations", "K-USR-01", "Daily count", "users", "Column chart", "acquisition_source, registration_method, signup_platform", "IST day", "Last 90 days", "Daily", "How many join and how?", "Channel spend"),
    ("2 User Analytics", "Active and returning users", "K-USR-03, K-USR-06", "WAU split new vs returning", "feature_events, users", "Stacked area", "acquisition_source", "week", "Last 26 weeks", "Daily", "Is growth from new or retained users?", "Retention programme"),
    ("2 User Analytics", "Cohort retention", "K-USR-10", "Day-7 retention by weekly cohort", "users, feature_events", "Cohort heatmap", "acquisition_source", "registration week", "Last 12 cohorts", "Weekly", "Are newer cohorts retaining better?", "Onboarding changes"),
    ("2 User Analytics", "Acquisition source mix", "K-USR-01", "Share by source", "users", "100% bar", "-", "month", "Last 6 months", "Weekly", "Which channels bring users?", "Channel focus"),
    ("2 User Analytics", "Device and platform", "K-USR-01, K-USR-02", "Users by signup_platform/device_type", "users, sessions", "Bar", "-", "month", "Last 90 days", "Weekly", "Which devices to prioritise?", "UX and app roadmap"),
    ("2 User Analytics", "Geographic distribution", "K-USR-02", "Active users by state_region (only if collected and approved)", "users", "Ranked bar (no map pins, no city)", "-", "month", "Last 90 days", "Weekly", "Where are users concentrated?", "Region support / language"),
    ("2 User Analytics", "User lifecycle", "K-USR-07, K-USR-11, K-USR-08", "Users by account_status; status transitions; onboarding funnel", "users, user_status_history", "Sankey or table + funnel", "-", "month", "Last 6 months", "Weekly", "Where do users get stuck or leave?", "Re-engagement and enforcement review"),
    ("3 Engagement", "Feature usage and adoption", "K-ENG-01", "Adoption % per feature", "feature_events", "Horizontal bar", "platform", "feature", "Last 30 days", "Daily", "Which features matter?", "Feature investment"),
    ("3 Engagement", "Task funnel", "K-ENG-02, K-ENG-04, K-ENG-05", "Viewed > opened > started > completed > credited", "feature_events, task_activity, rewards", "Funnel", "task_type, fulfilment_source", "-", "Last 30 days (3-day maturity)", "Daily", "Where does earning activity break?", "Fix UX or partner"),
    ("3 Engagement", "Failure breakdown", "K-ENG-06", "Failures by category and tracking_source", "task_activity", "Stacked bar", "task_type, provider", "week", "Last 12 weeks", "Daily", "Is failure ours or the partner's?", "Partner escalation"),
    ("3 Engagement", "Repeat usage", "K-ENG-07, K-ENG-08", "Repeat rate per feature; active days per user", "feature_events", "Bar + histogram", "feature", "-", "Last 30 days", "Weekly", "Which features build habit?", "Roadmap"),
    ("3 Engagement", "Activity trends", "K-ENG-09, K-ENG-10, K-ENG-11", "Daily claim rate, spin completion, mission completion", "feature_events, mission_progress", "Small multiples", "-", "IST day", "Last 90 days", "Daily", "Are engagement loops working?", "Tune mechanics"),
    ("4 Rewards", "Reward activity", "K-RWD-01", "Reward records by status", "rewards", "Stacked column", "unit", "IST day", "Last 90 days", "Daily", "How many reward decisions are made?", "Ops capacity"),
    ("4 Rewards", "Reward source", "K-RWD-05", "Credited volume by source_type/feature per unit", "rewards", "Treemap per unit", "unit", "-", "Last 30 days", "Daily", "Where does reward budget go?", "Rebalance rewards"),
    ("4 Rewards", "Reward status and backlog", "K-RWD-04, K-RWD-06", "Pending by age bucket; credit lag P50/P90", "rewards, task_activity", "Aged bar + line", "feature", "-", "Snapshot + last 30 days", "Hourly", "Are users waiting too long for rewards?", "Validation capacity, partner follow-up"),
    ("4 Rewards", "Reversal activity", "K-RWD-03", "Reversal rate by credit cohort and reason", "rewards", "Line + stacked bar", "reversal_reason_category, feature", "week", "Last 12 weeks", "Daily", "Is credited activity trustworthy?", "Quality controls"),
    ("5 Wallet", "Transactions", "K-WAL-01", "Rows by type and status", "wallet_transactions", "Stacked column", "unit", "IST day", "Last 90 days", "Daily", "What moves through wallets?", "Capacity"),
    ("5 Wallet", "Credits and redemptions", "K-WAL-02, K-WAL-03", "Credit vs redemption volume per unit", "wallet_transactions", "Paired bars", "unit", "week", "Last 12 weeks", "Daily", "Is value accumulating or being redeemed?", "Liability planning"),
    ("5 Wallet", "Reversals and reconciliation", "K-WAL-04, K-WAL-05", "Reversal volume; exception list", "wallet_transactions, rewards, withdrawals", "Bar + exception table", "transaction_type", "-", "Last 30 days", "Daily", "Can every balance be explained?", "Engineering fixes before reporting"),
    ("6 Withdrawals", "Requests and status", "K-WDR-01, K-WDR-02, K-WDR-04, K-WDR-05", "Count by status over time", "withdrawals", "Stacked column", "payout_method", "IST day", "Last 90 days", "Hourly", "How many payouts succeed?", "Ops staffing"),
    ("6 Withdrawals", "Processing duration", "K-WDR-06, K-WDR-10", "P50/P90 hours; share within 72 h", "withdrawals", "Line + reference line at published 72 h", "payout_method, review_type", "IST day", "Last 90 days", "Daily", "Are we meeting the published window?", "Escalation"),
    ("6 Withdrawals", "Pending queue", "K-WDR-03", "Open requests by age", "withdrawals", "Aged bar", "payout_method", "-", "Snapshot", "Hourly", "What needs action now?", "Daily ops triage"),
    ("6 Withdrawals", "Payout methods", "K-WDR-09", "Share by method; rejection rate by method", "withdrawals", "Bar", "-", "month", "Last 6 months", "Weekly", "Which methods cause problems?", "Partner decisions"),
    ("7 Referrals", "Referral funnel", "K-REF-01..K-REF-04", "Created > registered > activated > converted", "referrals", "Funnel", "referral_channel", "-", "Last 90 days", "Daily", "Where do referrals drop?", "Referral UX"),
    ("7 Referrals", "Conversion and rejection", "K-REF-05, K-REF-06", "Rates by registration cohort", "referrals", "Line", "referral_channel", "month cohort", "Last 6 cohorts", "Weekly", "Are referred users genuine?", "Referral reward policy"),
]
DASHBOARDS = [dict(zip(["dashboard", "visual", "metric", "calculation", "source", "visualization", "filters", "dimensions", "date_range",
                        "refresh", "business_question", "decision_supported"], v)) for v in V]

# ------------------------------------------------------------------ N: handoff extras for important events
# event: (dedup rule, acceptance tests)
HANDOFF = {
    "user_registered": ("One per user_id; dedup on user_id.", ["Creating an account emits exactly one user_registered with the new user_id.",
                        "Failed sign-up (validation error) emits nothing.", "acquisition_source is captured once and is not overwritten by later visits."]),
    "account_status_changed": ("One per status_change_id.", ["Suspending a test account emits one event with previous_status=active, new_status=suspended.",
                               "Setting the same status again emits nothing.", "A matching user_status_history row exists with the same timestamp."]),
    "task_started": ("One per activity_id.", ["Starting a task creates exactly one activity_id and one task_started.",
                     "Re-opening the same in-progress task does not create a second activity_id (within the timeout)."]),
    "task_completed": ("One per activity_id; dedup on activity_id + event_name.", ["When a valid task completion occurs, exactly one analytically usable completion event is recorded for the task/user transaction, subject to the final engineering implementation and idempotency design.",
                       "A partner callback retried 3 times produces one task_completed.", "A completion that fails validation produces task_failed (validation_failed), not task_completed."]),
    "task_failed": ("One per activity_id.", ["A simulated partner tracking timeout produces task_failed with failure_category=tracking_failed, failure_stage=tracking.",
                    "No activity has both task_completed and task_failed."]),
    "reward_pending": ("One per reward_id; reward idempotency_key = <source_type>:<source_id>.", ["A task awaiting partner validation shows one reward_pending and no reward_credited."]),
    "reward_credited": ("One per reward_id; idempotency_key unique.", ["Crediting a reward emits one reward_credited and creates one wallet reward_credit row (wallet units) with matching amount and unit.",
                        "Retrying the credit API with the same idempotency_key does not create a second credit.", "XP rewards emit reward_credited without a wallet row (until A-012 is resolved)."]),
    "reward_reversed": ("One per reward_id.", ["Reversing a credited reward emits reward_reversed and one wallet reversal row whose related_transaction_id is the original credit.",
                        "final_amount becomes 0; amount keeps the original value."]),
    "referral_registered": ("One per referral_id.", ["A sign-up with a valid code emits referral_registered with both user IDs; referral_status = registered (not converted).",
                            "Self-referral attempt: referrer_user_id = referred_user_id is rejected."]),
    "referral_converted": ("One per referral_id.", ["Conversion only after first eligible activity and validation; emits reward_id that exists in rewards.",
                           "A referral that is registered but never activated never emits referral_converted."]),
    "wallet_transaction_created": ("One per transaction_id; idempotency_key unique.", ["Every balance change produces exactly one ledger row.",
                                   "Reversal rows always carry related_transaction_id.", "Sum of ledger per user/unit equals displayed balance in a test account."]),
    "wallet_transaction_completed": ("One per transaction_id.", ["Pending redemption debit emits completed only when the withdrawal completes."]),
    "wallet_transaction_reversed": ("One per transaction_id.", ["Reversed row status becomes 'reversed' and a linked reversing row exists."]),
    "withdrawal_requested": ("One per withdrawal_id.", ["A request emits withdrawal_requested and one pending redemption_debit with ve_debited.",
                             "A request below the published minimum is rejected by the API and emits nothing.", "Double-tapping submit creates one withdrawal_id."]),
    "withdrawal_processing": ("One per withdrawal_id per transition.", ["Moving to review emits one event; processing timestamp >= requested timestamp."]),
    "withdrawal_completed": ("One per withdrawal_id.", ["Partner confirmation emits withdrawal_completed; redemption debit becomes completed; final timestamp >= processing."]),
    "withdrawal_rejected": ("One per withdrawal_id.", ["Rejection emits reason_category and creates one redemption_refund ledger row of equal amount."]),
    "withdrawal_reversed": ("One per withdrawal_id.", ["Only a completed withdrawal can be reversed; emits refund row."]),
    "daily_reward_claimed": ("One per user_id + claim_date_ist.", ["Two claims on the same IST day: the second is refused and no event is emitted.",
                             "A claim at 23:59 IST and one at 00:01 IST count for two different claim dates."]),
}

# ------------------------------------------------------------------ O: pipeline
PIPELINE = [
    ("Source systems", "VELOOP web app (frontend), backend services (accounts, tasks, rewards, wallet, withdrawals, referrals), ad/survey/offer partner callbacks, payout partner, support mailbox/tool.", "Engineering"),
    ("Event producers", "Server: all money, reward, status and referral events (trusted). Client: views, opens, onboarding steps (untrusted, for UX analysis only).", "Engineering"),
    ("Collection", "Server events written to an append-only events table in the existing application database inside the same transaction as the business write (transactional outbox). Client events sent to one backend endpoint that validates schema and stamps received_at_utc.", "Engineering"),
    ("Storage / raw layer", "Stage 1 (now): raw_events table + existing business tables in the app's Postgres/MySQL read replica. Stage 2 (when volume or query load justifies): daily export to object storage (Parquet) and a warehouse (e.g. BigQuery or ClickHouse).", "Engineering"),
    ("Validation", "Schema check at the collection endpoint (QC-01, QC-04, QC-05, QC-11); quarantine table for rejected rows with reason.", "Engineering"),
    ("Transformation", "Scheduled SQL models (e.g. dbt Core, free) build clean tables: users, sessions, task_activity, rewards, wallet_transactions, withdrawals, referrals; dedup, normalisation, derived fields with as-of timestamp.", "Data/Analytics"),
    ("Quality checks", "SQL tests per model (uniqueness, not-null, accepted values, relationships, reconciliation QC-13), run after every transformation; failures block the dashboard refresh.", "Data/Analytics"),
    ("Analytical layer", "KPI tables (daily grain, IST day) built only from data_environment = 'production'.", "Data/Analytics"),
    ("Dashboard", "Free/low-cost BI on the analytical layer (e.g. Metabase open source or Looker Studio). Seven dashboards per deliverable 14.", "Data/Analytics"),
    ("Refresh", "Daily 02:00 IST full refresh for most KPIs; hourly incremental for withdrawal queue and pending rewards.", "Data/Analytics"),
    ("Monitoring", "Freshness, volume anomalies, test failures and quarantine counts posted to a team channel; dashboard banner when data is stale.", "Data/Analytics"),
    ("Failure handling", "Producers retry with the same event_id (idempotent); collection is at-least-once and dedup is by event_id; failed transformation keeps yesterday's dashboard and shows a stale banner; backfills re-run models for a date range.", "Engineering + Data"),
    ("Ownership", "Engineering owns producers, collection and raw layer; Data/Analytics owns transformations, tests, KPIs and dashboards; Product owns definitions; Founder approves KPI changes.", "Founder"),
]

# ------------------------------------------------------------------ P: access and governance
ACCESS = [
    ("Engineering", "Raw events, business tables, quarantine", "Technical event implementation and debugging", "Restricted fields only in production systems, never in exports"),
    ("Data Analyst", "Approved analytical datasets (pseudonymous) + quarantine summaries", "KPI computation, quality monitoring", "No names, emails, payout details"),
    ("Product / Operations", "Dashboards and aggregated tables; operations queue views for withdrawals with withdrawal_id only", "Business reporting and operations", "Aggregates; record-level only where operationally needed"),
    ("Finance", "Wallet, withdrawal and reward aggregates; reconciliation exceptions", "Liability and payout tracking", "No credentials or payout account details"),
    ("Content Team", "Aggregated help-center and feature engagement", "Content performance", "Aggregates only, minimum group size 10"),
    ("Intern", "Only approved, sanitised or simulated datasets", "Learning and analysis tasks", "No production personal data"),
    ("Partners (ad/offer/payout)", "Nothing from the analytics layer", "n/a", "Data sharing only through engineering integrations under the privacy policy"),
]
NEVER_EXPOSE = ["Passwords and password hashes", "Authentication secrets, session tokens, OAuth tokens", "API keys and partner secrets",
                "Payment credentials: UPI IDs, bank account numbers, card numbers, PayPal login", "Private credentials of staff or users",
                "Sensitive security controls: fraud thresholds, detection rules, device-fingerprint logic", "Full names and email addresses in analytics tables",
                "Precise location and IP addresses in analytics tables", "Government ID or KYC documents (if ever collected)"]

# ------------------------------------------------------------------ Q: change management
CHANGE_TRIGGERS = [
    ("A feature changes", "Update coverage matrix row; add/retire events; bump schema_version of affected events; note affected KPIs.", "Product"),
    ("An event changes", "New schema_version; old and new versions accepted in parallel for a transition window; transformation maps both.", "Engineering"),
    ("A reward mechanic changes", "Log effective date; KPIs compare only like-for-like periods; annotate dashboards.", "Product + Finance"),
    ("A withdrawal method changes", "Update payout_method allowed values with effective date; historic values kept.", "Operations"),
    ("A field is renamed", "Add new field, backfill, deprecate old after one release; never rename in place.", "Engineering + Data"),
    ("A KPI definition changes", "New KPI version (e.g. K-USR-02 v2); restate history or show break line; founder approval.", "Data/Analytics + Founder"),
    ("A dashboard changes", "Change log entry; screenshot before/after; notify stakeholders.", "Data/Analytics"),
]
# date, change, old, new, reason, affected KPIs, dashboards, reports, owner, version
CHANGE_LOG = [
    ("2026-10-01", "Initial analytics specification v1.0 (this submission)", "None (no documented tracking plan)", "{n_events} proposed events, {n_kpis} KPIs, {n_entities}-entity model, {n_fields}-field dictionary", "Task 01 foundation", "All", "All (blueprint)", "None yet", "Data Analyst (intern)", "1.0.0"),
    ("2026-10-01", "EXAMPLE: DAU definition", "Supplied is_active flags: login within N days of 2026-09-15 00:00", "K-USR-02: qualifying activity event per IST day", "Logins without activity overstate engagement; reference date undocumented", "K-USR-02, K-USR-03, K-USR-04, K-USR-05", "1, 2", "Weekly founder update", "Data/Analytics", "1.0.0"),
    ("YYYY-MM-DD", "TEMPLATE: event field renamed", "old_field", "new_field (old kept until vX)", "reason", "list", "list", "list", "owner", "x.y.z"),
]

# ------------------------------------------------------------------ R: readiness scorecard
# area, score 0-4, evidence, biggest gap, priority, reason
READINESS = [
    ("Event coverage", 0, "No evidence of any analytics events (A-001); supplied data is a user snapshot.", "No events verified", "Critical", "Without events no engagement, funnel or retention KPI can be produced."),
    ("Data model", 1, "Proposed 18-entity model (deliverable 10); not implemented.", "No ledger, no status history verified", "Critical", "Wallet and reward reporting cannot be trusted without a ledger and stable transaction IDs."),
    ("Data dictionary", 2, "Supplied dictionary has 25 fields (2 columns undocumented); full proposed dictionary in deliverable 09.", "Real system field names unknown", "High", "Engineers and analysts may use different names for the same thing."),
    ("KPI definitions", 2, "Reproducible definitions proposed in deliverable 11; none approved.", "No approval or owners", "High", "Unapproved definitions lead to conflicting numbers in reports."),
    ("Data quality", 1, "Audit of supplied data found duplicates, malformed dates, impossible field combinations and a consent conflict (deliverable 13).", "No automated checks in place", "High", "Known defect types would reach dashboards unchecked."),
    ("Dashboard readiness", 0, "Blueprint only (deliverable 14).", "No production data", "Medium", "Dashboards depend on events and models first; building them now would show simulated or empty data."),
    ("Engineering instrumentation", 0, "None verified.", "No event_id/idempotency verified", "Critical", "Without a stable transaction ID, reliable wallet transaction deduplication cannot be guaranteed."),
    ("Access control", 1, "Privacy policy exists; no analytics access model documented; supplied dataset contains PII.", "PII in analytics extracts", "High", "Personal data is exposed beyond need."),
    ("Documentation", 2, "Help center is detailed; this submission adds the analytics documentation.", "Internal docs on data unknown", "Medium", "Knowledge sits with individuals."),
    ("Reporting", 0, "No reporting process known; homepage figures unverifiable (A-021).", "No trusted source of truth", "High", "Public or management figures cannot be traced to data."),
]
SCORE_SCALE = {0: "Not started / no evidence", 1: "Ad hoc", 2: "Defined (proposed, not implemented)", 3: "Implemented, not monitored", 4: "Implemented and monitored"}

# ------------------------------------------------------------------ Backlog
# id, priority, requirement, reason, dependency, owner, stage
BACKLOG = [
    ("BL-01", "Critical", "Confirm current logging and live feature list (A-001, A-002)", "All later work depends on what exists", "None", "Engineering + Product", "Pre-launch"),
    ("BL-02", "Critical", "Stable opaque user_id on every record", "Required for cross-event analysis", "Authentication", "Engineering", "Pre-launch"),
    ("BL-03", "Critical", "Append-only wallet ledger with transaction_id, related_transaction_id and idempotency_key", "Required for wallet analytics and reconciliation; prevents duplicate credits", "Wallet service", "Engineering", "Pre-launch"),
    ("BL-04", "Critical", "Reward table separating pending/credited/rejected/reversed/corrected with idempotency_key", "Distinguishes activity from actual credit (C3)", "Reward service", "Engineering", "Pre-launch"),
    ("BL-05", "Critical", "Withdrawal status history + reason categories + debit/refund links", "Withdrawal KPIs and trust", "Payout flow", "Engineering + Operations", "Pre-launch"),
    ("BL-06", "Critical", "Store all timestamps in UTC; report on IST day", "Daily KPIs and streaks align with claim window", "Database", "Engineering", "Pre-launch"),
    ("BL-07", "High", "Server-side events for the Critical events in deliverable 15 (event_id, schema_version)", "Product measurement", "BL-02", "Engineering", "Pre-launch"),
    ("BL-08", "High", "task_activity with activity_id, validation_status, failure_category, external_reference_id", "Earning funnel and partner reliability", "Task service, partner callbacks", "Engineering", "Pre-launch"),
    ("BL-09", "High", "Referral table linking referrer and referred user with stage timestamps", "Referral funnel (gap G02)", "Referral service", "Engineering", "Pre-launch"),
    ("BL-10", "High", "Account status history table", "Lifecycle KPIs (gap G04)", "Account service", "Engineering", "Pre-launch"),
    ("BL-11", "High", "Data quality checks QC-01 to QC-17", "Prevent unreliable reporting", "Data layer", "Data/Engineering", "Pre-launch"),
    ("BL-12", "High", "Remove names/emails/exact age/gender/city from analytics extracts; consent rule for marketing_opt_in", "Privacy (DQ-C04, DQ-C10)", "Governance approval", "Engineering + Founder", "Pre-launch"),
    ("BL-13", "High", "Publish VE/Gem/Token conversion rate table with effective dates", "Reward liability in INR (A-010)", "Finance decision", "Founder / Finance", "Pre-launch"),
    ("BL-14", "Medium", "Client events (views, opens, onboarding steps) and sessions", "UX funnels and returning users", "BL-07", "Engineering", "Launch"),
    ("BL-15", "Medium", "Transformation models + KPI tables (dbt Core or scheduled SQL)", "Reproducible KPIs", "BL-07, BL-11", "Data/Analytics", "Launch"),
    ("BL-16", "Medium", "Approve KPI catalogue v1 and owners", "Single source of truth", "None", "Founder + Data", "Launch"),
    ("BL-17", "Medium", "Support ticket categories and timestamps (tool or structured inbox)", "Support KPIs", "A-019", "Operations", "Launch"),
    ("BL-18", "Medium", "Advanced dashboards (7 dashboards in deliverable 14)", "Management reporting", "Production data, BL-15", "Data/Analytics", "Post-launch"),
    ("BL-19", "Low", "Warehouse migration (object storage + columnar warehouse)", "Only when DB load or volume justifies", "Volume evidence", "Engineering", "Post-launch"),
    ("BL-20", "Low", "Instrument future features (Lucky Draw etc.) through change log", "Not live yet", "Feature launch", "Product", "Post-launch"),
]
