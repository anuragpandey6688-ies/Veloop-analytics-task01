# 02 · Product Data Readiness Audit

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

## What was reviewed

* The task brief (SRC-01) and the assignment email (SRC-02).
* The supplied dataset `VELoop_Rewards_Data_01.xlsx` (SRC-03), profiled and audited in 12 and 13.
* Public official VELOOP pages, all checked on 2026-10-01: the help center, withdrawal, verification, currency, earning, referral, missions/badges and exchange pages, the privacy policy and the homepage (SRC-04 to SRC-16).

## What VELOOP is, according to official pages

An online rewards and engagement platform operated from Ramgarh, Jharkhand, India. It has five virtual credits: VEs (main reward credits), XP (progression), Gems (exchangeable), Tokens (selected purchases) and Spins (wheel) (SRC-04). Earning features include watch ads, surveys, app tasks, captcha, tap & earn, a 1.5-hour earning session ("Mine & earn", explicitly not crypto mining, SRC-10), games and follow & earn. Engagement features include daily check-in (IST window, SRC-08), streaks, spin, missions, badges, levels, leaderboard and promo codes. The money features are a wallet dashboard, Gems Exchange / Swap Center, and withdrawals from Rs. 10 by UPI, PayPal or gift cards, with system and manual review (SRC-05, SRC-06). Six features are officially "coming soon" and are not instrumented now (SRC-11).

**Caution:** a published help page is evidence that a feature is *intended* and described, not that it is live or tracked. Every implementation question is in the register (A-001, A-002).

## Conflicts found between sources (not resolved by guessing)

| Topic | Source A | Source B | Treatment |
| --- | --- | --- | --- |
| Production scale | Homepage: "Registered Users 1 570 253+", "Total Paid Out 1 500 470+" (SRC-14) | Brief: VELOOP "currently does not have the volume of production data required" | Homepage figures are **not used**; flagged A-021 |
| Payout methods | Homepage: transfers to "crypto wallet", footer "Staking" | Withdrawal page: UPI, PayPal, gift cards; mining page: "does not perform ... staking" | Official withdrawal page used for allowed values; A-022 |
| App | Homepage: "Get Soon The App" | Supplied data: platform = Web for 100% | `platform` enum keeps android/ios for later; A-018 |
| Support | velooprewardsteam@gmail.com, 24–48 h (pages) and 24–72 h (header) | Email: velooprewardsofficial@gmail.com; homepage business@veloop.com | A-027; K-SUP-04 notes both windows |
| Brief structure | Sections 1, 3, 4 missing; duration "22–24 days" and "22–25 days" | n/a | Recorded in SRC-01 |

## A1–A4 Product data map

The coverage matrix (03) maps 32 product areas and features. The lifecycles show which steps become events:

| lifecycle | step | stage | measured_by | how |
| --- | --- | --- | --- | --- |
| Task | 1 | Task viewed | task_viewed | Client event |
| Task | 2 | Task opened | task_opened | Client event |
| Task | 3 | Task started | task_started | Server event; creates activity_id |
| Task | 4 | User finishes task action | task_submitted | Client event (task types with a finish step) |
| Task | 5 | Completion validated | task_completed / task_failed | Server event after validation (task_completed is emitted only when validation passes) |
| Task | 6 | Reward credited | reward_pending -> reward_credited | Server events in reward service |
| Task | 7 | Abandoned | (derived) | Not emitted by the client; derived when no completion within the timeout (A-013), recorded as task_failed with failure_category = user_abandoned |
| Withdrawal | 1 | Requested | withdrawal_requested | Server |
| Withdrawal | 2 | Under review / processing | withdrawal_processing | Server |
| Withdrawal | 3 | Completed | withdrawal_completed | Server (partner confirmation) |
| Withdrawal | 4 | Rejected | withdrawal_rejected | Server; refund ledger row |
| Withdrawal | 5 | Reversed | withdrawal_reversed | Server; refund ledger row |
| Referral | 1 | Referral created | referral_created | Server |
| Referral | 2 | User registered | referral_registered | Server |
| Referral | 3 | User activated | referral_activated | Server |
| Referral | 4 | Referral converted | referral_converted | Server; registration alone never counts |

### A3 User event vs system event vs business outcome

| class | meaning | examples |
| --- | --- | --- |
| User event | Something the user does, observed by client or server. | task_opened, task_started, daily_reward_claimed, withdrawal_requested, spin_started |
| System event | Something VELOOP's systems decide or record without a direct user action. | task_completed (after validation), reward_credited, reward_reversed, withdrawal_completed, account_status_changed, referral_converted |
| Business outcome | A measured result computed from events; never emitted directly. | Task completion rate, credited reward volume, withdrawal completion rate, referral conversion rate |

## Analytics gaps (16)

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
