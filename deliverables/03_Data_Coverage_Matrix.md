# 03 · Data Coverage Matrix

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

Spreadsheet: [`03_Data_Coverage_Matrix.xlsx`](03_Data_Coverage_Matrix.xlsx). It has 32 rows covering every product area found on official pages, plus 16 analytics gaps.

## A4 Coverage matrix

| product_area | feature | user_action | system_action | proposed_events | business_question | status | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Account | Registration | Submits sign-up (web form or Google sign-in) | Creates account, assigns user_id | user_registered | How many users join, from which channels? | Confirmed | Critical |
| Account | Login | Signs in | Authenticates, creates session | user_logged_in; user_logged_out | How often do users come back? | Confirmed | High |
| Account | Onboarding | Goes through first-run steps | Records onboarding progress | onboarding_started; onboarding_step_completed; onboarding_completed | Where do new users drop before their first task? | To Be Verified | High |
| Account | Email verification | Clicks verification link | Marks email verified | email_verified | How long does verification take; does it block activation? | Confirmed | Medium |
| Account | Account status | (none: system/admin action) or requests deletion | Changes status (active, inactive, suspended, closed) | account_status_changed | How many accounts are suspended or closed, and when? | Confirmed | Critical |
| Earning | Task list / discovery | Browses and opens tasks | Renders task inventory | task_viewed; task_opened | Which tasks attract attention but are not started? | Proposed | Medium |
| Earning | Watch Ads | Starts and watches an ad | Partner tracks view; VELOOP validates; reward credited | task_started; task_submitted; task_completed; task_failed; reward_pending; reward_credited | What share of ad starts end in a credited reward, and where do they fail? | Confirmed | Critical |
| Earning | Surveys | Starts and completes a survey | Partner reports completion; validation | task_started; task_completed; task_failed | Which survey partners fail tracking most? | Confirmed | High |
| Earning | App Tasks / Offers | Installs or signs up for a partner app | Partner postback; validation (can take long) | task_started; task_completed; task_failed | How long do offer validations take and how many never return? | Confirmed | High |
| Earning | Captcha | Solves captchas | Validates answers | task_started; task_completed; task_failed | Is captcha a meaningful earning source? | Confirmed | Medium |
| Earning | Tap & Earn | Taps within limits | Counts valid taps, applies limits | task_started; task_completed; task_failed | How many users use Tap & Earn repeatedly? | Confirmed | Medium |
| Earning | Earning Session (Mine & earn) | Starts a session (up to 1 h 30 min) | Accrues credits, applies boosts | task_started; task_completed; task_failed | Do users restart sessions; what share complete? | Confirmed | Medium |
| Earning | Play & Earn (games) | Plays a game (Tokens may be spent) | Records result and rewards | task_started; task_completed | Do games drive engagement or only cost? | To Be Verified | Low |
| Earning | Follow & Earn (social) | Follows a social account | Validates follow where possible | task_started; task_completed; task_failed | Can social follows be validated at all? | Confirmed | Low |
| Engagement | Daily Check-In | Claims daily reward | Validates one claim per IST day; credits reward | daily_reward_claimed | What share of active users claim daily? | Confirmed | High |
| Engagement | Streaks | (implicit: consecutive claims) | Increments or resets streak | streak_updated | How often do streaks reset and at what length? | Confirmed | Medium |
| Engagement | Spin the Wheel | Spends a Spin and spins | Determines outcome, credits reward | spin_started; spin_completed | How many spins are interrupted? | Confirmed | Medium |
| Engagement | Missions | Joins and completes mission conditions | Tracks progress, verifies completion | mission_started; mission_completed | Which missions are completed and which abandoned? | Confirmed | Medium |
| Engagement | Badges | (earned by progress) | Awards badge | badge_earned | Do badges correlate with retention? | Confirmed | Low |
| Engagement | Levels / XP | (earned by activity) | Adds XP, changes level, may correct | level_reached; reward_credited | How fast do users progress? | Confirmed | Low |
| Engagement | Leaderboard | Views leaderboard / enters weekly leaderboard | Ranks users, may reward | feature_viewed; reward_credited | Does the leaderboard motivate activity? | To Be Verified | Low |
| Engagement | Promo Codes | Enters a promo code | Validates and grants benefit | promo_code_redeemed | Which promos are redeemed, by whom? | Confirmed | Low |
| Rewards | Reward lifecycle (all sources) | (none) | Creates pending reward, credits, rejects, reverses or corrects | reward_pending; reward_credited; reward_rejected; reward_reversed; reward_corrected | How much activity actually turns into credited rewards, and how much is reversed? | Confirmed | Critical |
| Wallet | Wallet ledger | Views balances | Writes ledger rows for every movement | wallet_transaction_created; wallet_transaction_completed; wallet_transaction_reversed | Can every balance be explained by its transactions? | Confirmed | Critical |
| Wallet | Gems Exchange / Swap Center | Converts Gems (or other units) to VEs | Debits one unit, credits another | currency_exchanged | How much value moves through exchange, at what rate? | Confirmed | Medium |
| Withdrawals | Withdrawal request | Requests payout (min Rs. 10) by UPI, PayPal or gift card | Debits VEs, queues for review | withdrawal_requested | How much payout demand is there and by which method? | Confirmed | Critical |
| Withdrawals | Review and payout | (waits) | Reviews (system/manual), pays, rejects or reverses; refunds VEs if needed | withdrawal_processing; withdrawal_completed; withdrawal_rejected; withdrawal_reversed | Are payouts processed within the published 24-72 h? | Confirmed | Critical |
| Referrals | Refer & Earn | Shares referral code/link | Creates referral record, links referred user, validates, rewards | referral_created; referral_registered; referral_activated; referral_converted; referral_rejected | How many referred sign-ups become genuine, rewarded referrals? | Confirmed | High |
| Support | Help Center | Reads help articles | Serves content | help_article_viewed | Which topics do users read before contacting support? | Confirmed | Low |
| Support | Support requests | Emails support / requests manual review | Logs and resolves request | support_ticket_created; support_ticket_resolved | What drives support load and how fast is it handled? | To Be Verified | Medium |
| Navigation | Screens | Opens screens | Renders screen | feature_viewed | Which features are discovered? | Proposed | Low |
| Future | Lucky Draw, Team Battle, Referral Milestones, Collect Cards, Surprise/Mystery Rewards | n/a | n/a | None now | n/a | Not live | Low |

## Analytics gaps (16; the brief asks for at least 10)

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
