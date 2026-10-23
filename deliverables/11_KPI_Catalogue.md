# 11 · KPI Catalogue

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

Spreadsheet: [`11_KPI_Catalogue.xlsx`](11_KPI_Catalogue.xlsx). It holds **53 KPIs** (the brief asks for 30+) across User, Engagement, Reward, Wallet, Withdrawal, Referral and Support.

**No targets.** Every entry is a definition such as "DAU = unique users generating a qualifying activity event within an IST calendar day". It never says what DAU should be.

| area | kpis |
| --- | --- |
| Engagement | 11 |
| Referral | 6 |
| Reward | 6 |
| Support | 4 |
| User | 11 |
| Wallet | 5 |
| Withdrawal | 10 |

### K-USR-01 · New Registrations
* **Definition:** Count of accounts created in the period.
* **Formula:** `COUNT(DISTINCT users.user_id) WHERE registration_at_utc in period (IST day boundaries)`
* **Required fields:** users.user_id, users.registration_at_utc
* **Data source:** users (backend) · **Frequency:** Daily · **Stakeholder:** Founder, Growth
* **Business purpose:** Tracks acquisition volume.
* **Interpretation:** Read alongside activation; registrations alone do not mean engaged users.
* **Limitation:** Includes accounts later suspended; fake or duplicate accounts inflate it until verification removes them.
* **Status:** Proposed definition

### K-USR-02 · Daily Active Users (DAU)
* **Definition:** Unique users generating at least one qualifying activity event within an IST calendar day.
* **Formula:** `COUNT(DISTINCT feature_events.user_id) WHERE event_name in qualifying set AND DATE_IST(event_timestamp_utc) = day`
* **Required fields:** feature_events.user_id, feature_events.event_name, feature_events.event_timestamp_utc
* **Data source:** feature_events · **Frequency:** Daily · **Stakeholder:** Founder, Product
* **Business purpose:** Core engagement size.
* **Interpretation:** Compare trend, not single days; weekends and campaigns move it.
* **Limitation:** Depends on agreed qualifying-event list; login-only users are excluded by design.
* **Status:** Proposed definition

### K-USR-03 · Weekly Active Users (WAU)
* **Definition:** Unique users with at least one qualifying activity event in the trailing 7 IST days.
* **Formula:** `COUNT(DISTINCT user_id) over [day-6, day]`
* **Required fields:** feature_events.user_id, feature_events.event_name, feature_events.event_timestamp_utc
* **Data source:** feature_events · **Frequency:** Daily (rolling) · **Stakeholder:** Product
* **Business purpose:** Weekly engagement size.
* **Interpretation:** Smoother than DAU.
* **Limitation:** Same as K-USR-02.
* **Status:** Proposed definition

### K-USR-04 · Monthly Active Users (MAU)
* **Definition:** Unique users with at least one qualifying activity event in the trailing 30 IST days.
* **Formula:** `COUNT(DISTINCT user_id) over [day-29, day]`
* **Required fields:** feature_events.user_id, feature_events.event_name, feature_events.event_timestamp_utc
* **Data source:** feature_events · **Frequency:** Daily (rolling) · **Stakeholder:** Founder
* **Business purpose:** Monthly engaged base.
* **Interpretation:** Denominator for stickiness.
* **Limitation:** Same as K-USR-02.
* **Status:** Proposed definition

### K-USR-05 · Stickiness (DAU/MAU)
* **Definition:** Average DAU in the period divided by MAU at period end.
* **Formula:** `AVG(K-USR-02 over period) / K-USR-04(period end)`
* **Required fields:** feature_events.user_id, feature_events.event_timestamp_utc
* **Data source:** Derived from K-USR-02, K-USR-04 · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** How often engaged users return.
* **Interpretation:** Higher means more habitual use.
* **Limitation:** Sensitive to MAU growth from new cohorts.
* **Status:** Proposed definition

### K-USR-06 · Returning Users
* **Definition:** Users active in the current period who were also active in an earlier period and are not new registrations of the current period.
* **Formula:** `COUNT(DISTINCT user_id active in period P AND active before P AND registration_at_utc < start(P))`
* **Required fields:** feature_events.user_id, feature_events.event_timestamp_utc, users.registration_at_utc
* **Data source:** feature_events, users · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** Separates retained base from new users.
* **Interpretation:** Rising share means retention improving.
* **Limitation:** Needs full event history; a snapshot field such as last_login cannot produce it.
* **Status:** Proposed definition

### K-USR-07 · Inactive Users
* **Definition:** Registered, non-closed accounts with no qualifying activity in the last 30 IST days.
* **Formula:** `COUNT(user_id) WHERE account_status != 'closed' AND (last_activity_at_utc IS NULL OR last_activity_at_utc < day-29)`
* **Required fields:** users.user_id, users.account_status, users.last_activity_at_utc
* **Data source:** users (derived) · **Frequency:** Weekly · **Stakeholder:** Product, Growth
* **Business purpose:** Re-engagement audience sizing.
* **Interpretation:** Large and growing means activation or retention problems.
* **Limitation:** 30-day window is a proposed convention, to be approved.
* **Status:** Proposed definition

### K-USR-08 · Onboarding Completion Rate
* **Definition:** Share of users who started onboarding and completed it within 7 days.
* **Formula:** `COUNT(onboarding_completed within 7d of start) / COUNT(onboarding_started), by start cohort`
* **Required fields:** users.onboarding_started_at_utc, users.onboarding_completed_at_utc
* **Data source:** users / onboarding events · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** Onboarding quality.
* **Interpretation:** Low rate points to friction in specific steps (use step events).
* **Limitation:** Cohort needs 7 days to mature; recent cohorts are incomplete.
* **Status:** Proposed definition

### K-USR-09 · Email Verification Rate
* **Definition:** Share of new registrations that verified email within 7 days.
* **Formula:** `COUNT(email_verified_at_utc - registration_at_utc <= 7d) / COUNT(registrations in cohort)`
* **Required fields:** users.registration_at_utc, users.email_verified_at_utc
* **Data source:** users · **Frequency:** Weekly · **Stakeholder:** Product, Operations
* **Business purpose:** Verification funnel health.
* **Interpretation:** Drops can signal email delivery problems.
* **Limitation:** Google sign-in users may be verified by provider; definition must state how they count.
* **Status:** Proposed definition

### K-USR-10 · Day-7 Retention
* **Definition:** Share of a registration cohort with a qualifying activity on IST day 7 after registration (day 0 = registration day).
* **Formula:** `COUNT(users in cohort active on day 7) / COUNT(users in cohort)`
* **Required fields:** users.registration_at_utc, feature_events.user_id, feature_events.event_timestamp_utc
* **Data source:** users, feature_events · **Frequency:** Weekly · **Stakeholder:** Founder, Product
* **Business purpose:** Early retention.
* **Interpretation:** Compare cohorts, not absolute value.
* **Limitation:** Exact-day retention is noisy for small cohorts; report cohort size beside it.
* **Status:** Proposed definition

### K-USR-11 · Account Suspensions
* **Definition:** Count of status changes into 'suspended' in the period.
* **Formula:** `COUNT(user_status_history WHERE new_status = 'suspended' AND changed_at_utc in period)`
* **Required fields:** user_status_history.new_status, user_status_history.changed_at_utc
* **Data source:** user_status_history · **Frequency:** Weekly · **Stakeholder:** Operations, Trust & Safety
* **Business purpose:** Enforcement workload.
* **Interpretation:** Spikes need investigation, not automatic interpretation.
* **Limitation:** Requires status history, absent in supplied data (gap G04).
* **Status:** Proposed definition

### K-ENG-01 · Feature Adoption Rate
* **Definition:** Share of active users in the period who used a given feature at least once.
* **Formula:** `COUNT(DISTINCT user_id with qualifying event in feature F) / K-USR-04`
* **Required fields:** feature_events.user_id, feature_events.feature, feature_events.event_name
* **Data source:** feature_events · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** Which features matter to users.
* **Interpretation:** Compare across features and over time.
* **Limitation:** Feature attribution must be consistent across events.
* **Status:** Proposed definition

### K-ENG-02 · Task Starts
* **Definition:** Count of task attempts started.
* **Formula:** `COUNT(task_activity.activity_id) WHERE started_at_utc in period`
* **Required fields:** task_activity.activity_id, task_activity.started_at_utc
* **Data source:** task_activity · **Frequency:** Daily · **Stakeholder:** Product
* **Business purpose:** Top of the earning funnel.
* **Interpretation:** Read with completion rate.
* **Limitation:** Abandoned starts are included by design.
* **Status:** Proposed definition

### K-ENG-03 · Validated Task Completions
* **Definition:** Count of task attempts whose completion passed validation.
* **Formula:** `COUNT(activity_id) WHERE activity_status = 'completed' AND validation_status = 'passed'`
* **Required fields:** task_activity.activity_status, task_activity.validation_status, task_activity.validated_at_utc
* **Data source:** task_activity · **Frequency:** Daily · **Stakeholder:** Product
* **Business purpose:** Successful earning activity.
* **Interpretation:** Activity, not reward: see K-RWD-02 for credits.
* **Limitation:** Late partner validation moves completions into later days.
* **Status:** Proposed definition

### K-ENG-04 · Task Completion Rate
* **Definition:** Validated completions divided by task starts, for attempts started in the period.
* **Formula:** `K-ENG-03 / K-ENG-02 (same start cohort)`
* **Required fields:** task_activity.activity_status, task_activity.validation_status, task_activity.started_at_utc
* **Data source:** task_activity · **Frequency:** Daily · **Stakeholder:** Product
* **Business purpose:** Funnel efficiency by task type.
* **Interpretation:** Break down by task_type and fulfilment_source.
* **Limitation:** Pending validations depress recent days; use a maturity window (e.g. 3 days).
* **Status:** Proposed definition

### K-ENG-05 · Task Abandonment Rate
* **Definition:** Share of started attempts that ended as abandoned.
* **Formula:** `COUNT(activity_status = 'abandoned') / COUNT(started)`
* **Required fields:** task_activity.activity_status, task_activity.started_at_utc
* **Data source:** task_activity · **Frequency:** Weekly · **Stakeholder:** Product, UX
* **Business purpose:** UX friction.
* **Interpretation:** High abandonment on one task type suggests UX or content issues.
* **Limitation:** Abandonment is derived from a timeout rule that engineering must define (A-013).
* **Status:** Proposed definition

### K-ENG-06 · Task Failure Rate by Category
* **Definition:** Share of started attempts that failed, split by failure_category.
* **Formula:** `COUNT(activity_status = 'failed' AND failure_category = c) / COUNT(started)`
* **Required fields:** task_activity.activity_status, task_activity.failure_category, task_activity.tracking_source
* **Data source:** task_activity · **Frequency:** Weekly · **Stakeholder:** Product, Engineering
* **Business purpose:** Separates partner tracking failures from VELOOP failures.
* **Interpretation:** Tracking failures concentrated on one partner point to that partner.
* **Limitation:** Classification is proposed; real failure codes unknown.
* **Status:** Proposed definition

### K-ENG-07 · Repeat Usage Rate
* **Definition:** Share of a feature's users in the period who used it on 2 or more distinct IST days.
* **Formula:** `COUNT(users with >= 2 active days in feature F) / COUNT(users of F)`
* **Required fields:** feature_events.user_id, feature_events.feature, feature_events.event_timestamp_utc
* **Data source:** feature_events · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** Habit formation per feature.
* **Interpretation:** Higher means the feature drives return visits.
* **Limitation:** Short periods understate it.
* **Status:** Proposed definition

### K-ENG-08 · Active Days per Active User
* **Definition:** Average count of distinct IST days with qualifying activity per active user in a 30-day window.
* **Formula:** `SUM(active days per user) / K-USR-04`
* **Required fields:** feature_events.user_id, feature_events.event_timestamp_utc
* **Data source:** feature_events · **Frequency:** Monthly · **Stakeholder:** Product
* **Business purpose:** Depth of engagement.
* **Interpretation:** Read with MAU.
* **Limitation:** Not comparable across windows of different length.
* **Status:** Proposed definition

### K-ENG-09 · Daily Reward Claim Rate
* **Definition:** Share of DAU who claimed the daily reward that day.
* **Formula:** `COUNT(DISTINCT user_id with daily_reward_claimed on day) / K-USR-02`
* **Required fields:** feature_events.event_name, event_properties.claim_date_ist
* **Data source:** feature_events · **Frequency:** Daily · **Stakeholder:** Product
* **Business purpose:** Daily habit loop health.
* **Interpretation:** Low share means the check-in is not discovered or not valued.
* **Limitation:** Claim date must use IST window.
* **Status:** Proposed definition

### K-ENG-10 · Spin Completion Rate
* **Definition:** Share of spins started that completed.
* **Formula:** `COUNT(spin_completed) / COUNT(spin_started) joined on spin_id`
* **Required fields:** event_properties.spin_id, event_properties.outcome_type
* **Data source:** feature_events · **Frequency:** Weekly · **Stakeholder:** Product, Engineering
* **Business purpose:** Detects interrupted spins (technical issues).
* **Interpretation:** Gaps indicate crashes or connectivity issues.
* **Limitation:** Requires spin_id on both events.
* **Status:** Proposed definition

### K-ENG-11 · Mission Completion Rate
* **Definition:** Share of missions started that were completed before expiry.
* **Formula:** `COUNT(mission_status = 'completed') / COUNT(started)`
* **Required fields:** mission_progress.mission_status, mission_progress.started_at_utc
* **Data source:** mission_progress · **Frequency:** Weekly · **Stakeholder:** Product
* **Business purpose:** Mission design quality.
* **Interpretation:** Very low or very high suggests difficulty mis-set.
* **Limitation:** Mission rules vary by mission type.
* **Status:** Proposed definition

### K-RWD-01 · Reward Transactions
* **Definition:** Count of reward records created, by status.
* **Formula:** `COUNT(rewards.reward_id) GROUP BY reward_status`
* **Required fields:** rewards.reward_id, rewards.reward_status, rewards.created_at_utc
* **Data source:** rewards · **Frequency:** Daily · **Stakeholder:** Finance, Product
* **Business purpose:** Reward workload and mix.
* **Interpretation:** Split by status before interpreting.
* **Limitation:** Includes pending rewards that may never be credited.
* **Status:** Proposed definition

### K-RWD-02 · Rewards Credited (count and volume)
* **Definition:** Count and summed final_amount of rewards credited in the period, per unit.
* **Formula:** `COUNT(*), SUM(final_amount) WHERE reward_status in ('credited','corrected') AND credited_at_utc in period GROUP BY unit`
* **Required fields:** rewards.reward_status, rewards.final_amount, rewards.unit, rewards.credited_at_utc
* **Data source:** rewards · **Frequency:** Daily · **Stakeholder:** Finance, Founder
* **Business purpose:** Actual reward cost, distinct from activity.
* **Interpretation:** Never add units together without approved conversion rates.
* **Limitation:** VE to INR rate unknown (A-010).
* **Status:** Proposed definition

### K-RWD-03 · Reward Reversal Rate
* **Definition:** Share of credited rewards later reversed, by credit cohort.
* **Formula:** `COUNT(reward_status = 'reversed') / COUNT(credited in cohort)`
* **Required fields:** rewards.reward_status, rewards.credited_at_utc, rewards.reversed_at_utc
* **Data source:** rewards · **Frequency:** Weekly · **Stakeholder:** Trust & Safety, Finance
* **Business purpose:** Quality of credited activity.
* **Interpretation:** Rising rate is a quality signal, not proof of abuse.
* **Limitation:** Reversals can occur long after credit; recent cohorts are incomplete.
* **Status:** Proposed definition

### K-RWD-04 · Pending Reward Backlog
* **Definition:** Count and amount of rewards in 'pending' at snapshot time, with age buckets.
* **Formula:** `COUNT(*), SUM(amount) WHERE reward_status = 'pending' at snapshot GROUP BY age bucket`
* **Required fields:** rewards.reward_status, rewards.created_at_utc, rewards.amount
* **Data source:** rewards · **Frequency:** Daily · **Stakeholder:** Operations
* **Business purpose:** Validation backlog and user-facing delay.
* **Interpretation:** Old pending items drive 'rewards not updated' tickets.
* **Limitation:** Snapshot metric; needs daily snapshot or status history.
* **Status:** Proposed definition

### K-RWD-05 · Reward Activity by Feature
* **Definition:** Credited reward count and volume split by feature and source_type.
* **Formula:** `K-RWD-02 GROUP BY feature, source_type, unit`
* **Required fields:** rewards.feature, rewards.source_type, rewards.unit, rewards.final_amount
* **Data source:** rewards · **Frequency:** Weekly · **Stakeholder:** Product, Finance
* **Business purpose:** Where reward budget goes.
* **Interpretation:** Compare to feature adoption.
* **Limitation:** Same unit caveat as K-RWD-02.
* **Status:** Proposed definition

### K-RWD-06 · Activity-to-Credit Lag
* **Definition:** Median and P90 time between validated completion and reward credit.
* **Formula:** `PERCENTILE(credited_at_utc - task_activity.completed_at_utc)`
* **Required fields:** rewards.credited_at_utc, task_activity.completed_at_utc, rewards.source_id
* **Data source:** rewards + task_activity · **Frequency:** Weekly · **Stakeholder:** Product, Engineering
* **Business purpose:** User-facing reward delay.
* **Interpretation:** Compare with official guidance of ~15 minutes for ad tracking.
* **Limitation:** Only for task-sourced rewards.
* **Status:** Proposed definition

### K-WAL-01 · Wallet Transactions
* **Definition:** Count of ledger rows created, by transaction_type and status.
* **Formula:** `COUNT(transaction_id) GROUP BY transaction_type, transaction_status`
* **Required fields:** wallet_transactions.transaction_id, wallet_transactions.transaction_type, wallet_transactions.transaction_status
* **Data source:** wallet_transactions · **Frequency:** Daily · **Stakeholder:** Finance, Engineering
* **Business purpose:** Ledger activity.
* **Interpretation:** Mix shifts show behaviour change.
* **Limitation:** Ledger completeness must be reconciled first (K-WAL-05).
* **Status:** Proposed definition

### K-WAL-02 · Credit Volume
* **Definition:** Sum of completed credit amounts per unit in the period.
* **Formula:** `SUM(amount) WHERE direction = 'credit' AND transaction_status = 'completed' GROUP BY unit`
* **Required fields:** wallet_transactions.direction, wallet_transactions.amount, wallet_transactions.unit, wallet_transactions.transaction_status
* **Data source:** wallet_transactions · **Frequency:** Daily · **Stakeholder:** Finance
* **Business purpose:** Value entering wallets.
* **Interpretation:** Per unit only.
* **Limitation:** Refunds count as credits; split by type when needed.
* **Status:** Proposed definition

### K-WAL-03 · Redemption Activity
* **Definition:** Count and volume of redemption_debit transactions.
* **Formula:** `COUNT(*), SUM(amount) WHERE transaction_type = 'redemption_debit'`
* **Required fields:** wallet_transactions.transaction_type, wallet_transactions.amount
* **Data source:** wallet_transactions · **Frequency:** Daily · **Stakeholder:** Finance
* **Business purpose:** Value leaving through redemptions.
* **Interpretation:** Compare to withdrawal requests.
* **Limitation:** Includes debits later refunded; net with K-WAL-04.
* **Status:** Proposed definition

### K-WAL-04 · Wallet Reversals and Refunds
* **Definition:** Count and volume of reversal, adjustment and redemption_refund rows.
* **Formula:** `COUNT(*), SUM(amount) WHERE transaction_type in ('reversal','adjustment','redemption_refund')`
* **Required fields:** wallet_transactions.transaction_type, wallet_transactions.amount, wallet_transactions.related_transaction_id
* **Data source:** wallet_transactions · **Frequency:** Weekly · **Stakeholder:** Finance, Trust & Safety
* **Business purpose:** Corrections to the ledger.
* **Interpretation:** Every row must link to an original transaction.
* **Limitation:** Unlinked rows are a data-quality defect.
* **Status:** Proposed definition

### K-WAL-05 · Ledger Reconciliation Exceptions
* **Definition:** Count of credited wallet-unit rewards without a wallet credit, plus wallet reward credits without a reward, plus withdrawals without a debit.
* **Formula:** `Anti-join counts across rewards, wallet_transactions, withdrawals`
* **Required fields:** rewards.wallet_transaction_id, wallet_transactions.reference_id, withdrawals.debit_transaction_id
* **Data source:** rewards, wallet_transactions, withdrawals · **Frequency:** Daily · **Stakeholder:** Engineering, Finance
* **Business purpose:** Trust in every money KPI.
* **Interpretation:** Expected value is 0; any exception needs a ticket.
* **Limitation:** Requires transaction IDs on all three tables.
* **Status:** Proposed definition

### K-WDR-01 · Withdrawal Requests
* **Definition:** Count and INR value of withdrawal requests submitted.
* **Formula:** `COUNT(withdrawal_id), SUM(amount_inr) WHERE requested_at_utc in period`
* **Required fields:** withdrawals.withdrawal_id, withdrawals.requested_at_utc, withdrawals.amount_inr
* **Data source:** withdrawals · **Frequency:** Daily · **Stakeholder:** Finance, Operations
* **Business purpose:** Payout demand.
* **Interpretation:** Read with completion and queue.
* **Limitation:** Requests later rejected are included.
* **Status:** Proposed definition

### K-WDR-02 · Completed Withdrawals
* **Definition:** Count and INR value reaching 'completed' in the period.
* **Formula:** `COUNT(*), SUM(amount_inr) WHERE withdrawal_status = 'completed' AND final_at_utc in period`
* **Required fields:** withdrawals.withdrawal_status, withdrawals.final_at_utc, withdrawals.amount_inr
* **Data source:** withdrawals · **Frequency:** Daily · **Stakeholder:** Finance, Founder
* **Business purpose:** Payout delivered.
* **Interpretation:** A completed payout can still be reversed later.
* **Limitation:** Partner-side failures after completion need payout_reference_id reconciliation.
* **Status:** Proposed definition

### K-WDR-03 · Pending Withdrawal Queue
* **Definition:** Count, INR value and age of requests in 'requested' or 'processing' at snapshot time.
* **Formula:** `COUNT(*), SUM(amount_inr), MAX(now - requested_at_utc) WHERE status in ('requested','processing')`
* **Required fields:** withdrawals.withdrawal_status, withdrawals.requested_at_utc, withdrawals.amount_inr
* **Data source:** withdrawals · **Frequency:** Hourly / Daily · **Stakeholder:** Operations
* **Business purpose:** Operational load and user waiting time.
* **Interpretation:** Aging items beyond the published window need action.
* **Limitation:** Snapshot; requires status history for trends.
* **Status:** Proposed definition

### K-WDR-04 · Rejected Withdrawals and Rejection Rate
* **Definition:** Count of rejected requests and share of resolved requests that were rejected, by reason_category.
* **Formula:** `COUNT(rejected) / COUNT(rejected + completed + reversed) for requests resolved in period`
* **Required fields:** withdrawals.withdrawal_status, withdrawals.reason_category
* **Data source:** withdrawals · **Frequency:** Weekly · **Stakeholder:** Operations, Trust & Safety
* **Business purpose:** Payout friction and abuse handling.
* **Interpretation:** Reason mix shows whether users or partners cause rejections.
* **Limitation:** Reason taxonomy is proposed (A-015).
* **Status:** Proposed definition

### K-WDR-05 · Reversed Withdrawals
* **Definition:** Count and INR value of withdrawals reversed after completion.
* **Formula:** `COUNT(*), SUM(amount_inr) WHERE withdrawal_status = 'reversed'`
* **Required fields:** withdrawals.withdrawal_status, withdrawals.amount_inr, withdrawals.reason_category
* **Data source:** withdrawals · **Frequency:** Weekly · **Stakeholder:** Finance
* **Business purpose:** Payout failures after completion.
* **Interpretation:** Each case needs a partner-side cause review.
* **Limitation:** Reversal can occur after reporting period closes.
* **Status:** Proposed definition

### K-WDR-06 · Withdrawal Processing Time
* **Definition:** Median and P90 hours from request to final status, for resolved requests.
* **Formula:** `PERCENTILE(final_at_utc - requested_at_utc, 0.5 / 0.9)`
* **Required fields:** withdrawals.requested_at_utc, withdrawals.final_at_utc
* **Data source:** withdrawals · **Frequency:** Daily · **Stakeholder:** Operations, Founder
* **Business purpose:** Payout speed vs published expectation (24 h, up to 72 h).
* **Interpretation:** P90 matters more than median for user trust.
* **Limitation:** Excludes open requests; pair with K-WDR-03.
* **Status:** Proposed definition

### K-WDR-07 · Withdrawal Completion Rate
* **Definition:** Share of resolved requests (requested in the cohort) that completed and were not reversed.
* **Formula:** `COUNT(completed) / COUNT(completed + rejected + reversed)`
* **Required fields:** withdrawals.withdrawal_status, withdrawals.requested_at_utc
* **Data source:** withdrawals · **Frequency:** Weekly · **Stakeholder:** Founder, Finance
* **Business purpose:** Payout reliability.
* **Interpretation:** Report with cohort size and open count.
* **Limitation:** Open requests excluded; recent cohorts immature.
* **Status:** Proposed definition

### K-WDR-08 · Withdrawal Volume (INR)
* **Definition:** Sum of amount_inr by status for the period.
* **Formula:** `SUM(amount_inr) GROUP BY withdrawal_status`
* **Required fields:** withdrawals.amount_inr, withdrawals.withdrawal_status
* **Data source:** withdrawals · **Frequency:** Daily · **Stakeholder:** Finance
* **Business purpose:** Cash liability and payout spend.
* **Interpretation:** Completed volume is actual payout.
* **Limitation:** INR only; VE liability needs a confirmed conversion rate.
* **Status:** Proposed definition

### K-WDR-09 · Payout Method Distribution
* **Definition:** Share of requests and completed volume by payout_method.
* **Formula:** `COUNT(*) GROUP BY payout_method / COUNT(*)`
* **Required fields:** withdrawals.payout_method, withdrawals.withdrawal_status
* **Data source:** withdrawals · **Frequency:** Weekly · **Stakeholder:** Operations, Finance
* **Business purpose:** Partner capacity planning.
* **Interpretation:** Rejection rate per method shows method-specific issues.
* **Limitation:** Method availability varies by user eligibility (official).
* **Status:** Proposed definition

### K-WDR-10 · Share Resolved Within 72 Hours
* **Definition:** Share of resolved requests whose processing time was 72 hours or less.
* **Formula:** `COUNT(final_at_utc - requested_at_utc <= 72h) / COUNT(resolved)`
* **Required fields:** withdrawals.requested_at_utc, withdrawals.final_at_utc
* **Data source:** withdrawals · **Frequency:** Daily · **Stakeholder:** Operations, Founder
* **Business purpose:** Checks delivery against the publicly stated processing window. This is a published policy reference, not an internal target.
* **Interpretation:** Breaches need case review.
* **Limitation:** Policy window may change; read from config, not hard-coded.
* **Status:** Proposed definition

### K-REF-01 · Referrals Created
* **Definition:** Count of referral records created.
* **Formula:** `COUNT(referral_id) WHERE created_at_utc in period`
* **Required fields:** referrals.referral_id, referrals.created_at_utc
* **Data source:** referrals · **Frequency:** Weekly · **Stakeholder:** Growth
* **Business purpose:** Referral intent.
* **Interpretation:** Top of referral funnel.
* **Limitation:** Depends on when a referral record is created (A-016).
* **Status:** Proposed definition

### K-REF-02 · Referral Registrations
* **Definition:** Count of referrals where the referred user registered.
* **Formula:** `COUNT(*) WHERE registered_at_utc in period`
* **Required fields:** referrals.registered_at_utc, referrals.referred_user_id
* **Data source:** referrals · **Frequency:** Weekly · **Stakeholder:** Growth
* **Business purpose:** Referral sign-ups.
* **Interpretation:** Registration is NOT conversion.
* **Limitation:** Requires referred_user_id link (missing in supplied data).
* **Status:** Proposed definition

### K-REF-03 · Referral Activations
* **Definition:** Count of referred users who completed a first eligible activity.
* **Formula:** `COUNT(*) WHERE activated_at_utc in period`
* **Required fields:** referrals.activated_at_utc
* **Data source:** referrals · **Frequency:** Weekly · **Stakeholder:** Growth
* **Business purpose:** Quality of referred users.
* **Interpretation:** Low activation means low-intent sign-ups.
* **Limitation:** 'Eligible first activity' must be defined by VELOOP (A-017).
* **Status:** Proposed definition

### K-REF-04 · Referral Conversions
* **Definition:** Count of referrals that passed validation and earned the referral reward.
* **Formula:** `COUNT(*) WHERE referral_status = 'converted' AND converted_at_utc in period`
* **Required fields:** referrals.referral_status, referrals.converted_at_utc
* **Data source:** referrals · **Frequency:** Weekly · **Stakeholder:** Growth, Finance
* **Business purpose:** Successful referrals and their cost.
* **Interpretation:** Pair with reward cost.
* **Limitation:** Later reversals of referral rewards must update status.
* **Status:** Proposed definition

### K-REF-05 · Referral Conversion Rate
* **Definition:** Conversions divided by registrations for a registration cohort.
* **Formula:** `COUNT(converted) / COUNT(registered) per cohort`
* **Required fields:** referrals.referral_status, referrals.registered_at_utc
* **Data source:** referrals · **Frequency:** Monthly · **Stakeholder:** Growth
* **Business purpose:** Funnel efficiency.
* **Interpretation:** Compare cohorts.
* **Limitation:** Cohort maturity needed.
* **Status:** Proposed definition

### K-REF-06 · Referral Rejection Rate
* **Definition:** Share of registered referrals rejected at validation.
* **Formula:** `COUNT(rejected) / COUNT(registered)`
* **Required fields:** referrals.referral_status, referrals.rejection_reason_category
* **Data source:** referrals · **Frequency:** Monthly · **Stakeholder:** Trust & Safety
* **Business purpose:** Referral abuse handling.
* **Interpretation:** Rising rate needs review.
* **Limitation:** Does not reveal or set any fraud threshold.
* **Status:** Proposed definition

### K-SUP-01 · Support Requests
* **Definition:** Count of support tickets created.
* **Formula:** `COUNT(ticket_id) WHERE created_at_utc in period`
* **Required fields:** support_tickets.ticket_id, support_tickets.created_at_utc
* **Data source:** support tool · **Frequency:** Daily · **Stakeholder:** Operations
* **Business purpose:** Support load.
* **Interpretation:** Normalise by active users for comparisons.
* **Limitation:** Email-only support may not create structured tickets (A-019).
* **Status:** Proposed definition

### K-SUP-02 · Issue Category Distribution
* **Definition:** Share of tickets by issue_category.
* **Formula:** `COUNT(*) GROUP BY issue_category / COUNT(*)`
* **Required fields:** support_tickets.issue_category
* **Data source:** support tool · **Frequency:** Weekly · **Stakeholder:** Operations, Product
* **Business purpose:** Which product areas cause contacts.
* **Interpretation:** Withdrawal and missing-reward share are key signals.
* **Limitation:** Depends on consistent agent tagging.
* **Status:** Proposed definition

### K-SUP-03 · Help-Center Engagement
* **Definition:** Article views and unique viewers per content_category.
* **Formula:** `COUNT(help_article_viewed), COUNT(DISTINCT user_id) GROUP BY content_category`
* **Required fields:** feature_events.event_name, content.content_category, feature_events.user_id
* **Data source:** feature_events, content · **Frequency:** Weekly · **Stakeholder:** Content, Operations
* **Business purpose:** Self-service usage.
* **Interpretation:** High views on withdrawal pages before tickets suggests unclear content.
* **Limitation:** Logged-out viewers are not attributable to user_id.
* **Status:** Proposed definition

### K-SUP-04 · Support Response Time
* **Definition:** Median and P90 hours from ticket creation to first response.
* **Formula:** `PERCENTILE(first_response_at_utc - created_at_utc)`
* **Required fields:** support_tickets.created_at_utc, support_tickets.first_response_at_utc
* **Data source:** support tool · **Frequency:** Weekly · **Stakeholder:** Operations
* **Business purpose:** Checks support against published reply time.
* **Interpretation:** Published reply time differs between pages (24-48 h vs 24-72 h); clarify.
* **Limitation:** Needs ticket timestamps.
* **Status:** Proposed definition
