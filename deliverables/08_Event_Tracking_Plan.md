# 08 · Event Tracking Plan

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

Spreadsheet: [`08_Event_Tracking_Plan.xlsx`](08_Event_Tracking_Plan.xlsx). It holds 46 events (the brief recommends at least 25) and 672 event-property rows, each with data type and validation.

## Naming standard: `object_action`

* Lowercase snake_case: `^[a-z]+(_[a-z]+)+$`. The object is the business noun and the action is a past-tense verb (`task_completed`, `withdrawal_requested`, `user_logged_in`).
* The feature or domain goes in the `feature` property, not in the name.
* **Why:** the brief's minimum list already uses this form; sorting by name groups each object's lifecycle; names stay short. A `domain_object_action` prefix would duplicate the `feature` property and would break whenever a feature moves between domains in a product that is still changing.
* The validator (`scripts/validate.py`) checks every event name against this rule and the approved verb list.

## Envelope carried by every event

Required: `event_id`, `event_name`, `user_id`, `event_timestamp_utc`, `received_at_utc`, `feature`, `platform`, `event_source`, `schema_version`, `data_environment`. Client events also need `session_id`.
Money, reward, status and referral events must be **server** events, because client events can be lost, delayed or tampered with.

## Qualifying activity events (used for DAU/WAU/MAU)

`task_started`, `task_submitted`, `task_completed`, `daily_reward_claimed`, `mission_started`, `spin_started`, `promo_code_redeemed`, `referral_created`, `currency_exchanged`, `withdrawal_requested`. Logins, screen views and server outcomes are excluded on purpose: a login alone is not product engagement.

## Catalogue

| event_name | domain | event_source | trigger | required | kpis | priority |
| --- | --- | --- | --- | --- | --- | --- |
| user_registered | Account | server | Account record committed successfully in the backend. | registration_method, acquisition_source, signup_platform | K-USR-01, K-USR-10, K-REF-02 | Critical |
| user_logged_in | Account | server | Authentication succeeded and a session was created. | login_method, session_id | K-USR-06 | High |
| user_logged_out | Account | client | User taps log out, or the server expires the session. | logout_type |  | Low |
| onboarding_started | Account | client | First onboarding screen is displayed to a newly registered user. | onboarding_version | K-USR-08 | High |
| onboarding_step_completed | Account | client | User completes one onboarding step. | onboarding_version, step_key, step_index | K-USR-08 | Medium |
| onboarding_completed | Account | server | Backend marks onboarding complete for the user. | onboarding_version | K-USR-08 | High |
| email_verified | Account | server | Email verification link/code accepted. |  | K-USR-09 | Medium |
| account_status_changed | Account | server | account_status value changes in the backend. | previous_status, new_status, change_reason_category, changed_by_type | K-USR-11, K-USR-07 | Critical |
| task_viewed | Tasks | client | Task card is at least 50% visible in the viewport for 1 second. | task_id, task_type | K-ENG-01 | Medium |
| task_opened | Tasks | client | User taps a task card to open its detail or provider screen. | task_id, task_type |  | Medium |
| task_started | Tasks | server | Backend creates the task_activity record (activity_id issued). | activity_id, task_id, task_type, tracking_source | K-ENG-02, K-ENG-04 | Critical |
| task_submitted | Tasks | client | User finishes the task action and returns to VELOOP; validation not yet complete. | activity_id, task_id | K-RWD-06 | Medium |
| task_completed | Tasks | server | Task completion has passed the applicable validation process. | activity_id, task_id, task_type, activity_status, validation_status, reward_amount, reward_unit | K-ENG-03, K-ENG-04, K-RWD-06 | Critical |
| task_failed | Tasks | server | Attempt reaches a final failed state, including validation failure, tracking failure, system error, or abandonment timeout. | activity_id, task_id, task_type, failure_category, failure_stage | K-ENG-05, K-ENG-06 | Critical |
| reward_pending | Rewards | server | Reward record created but awaiting validation. | reward_id, source_type, source_id, amount, unit | K-RWD-01, K-RWD-04 | Critical |
| reward_credited | Rewards | server | Reward committed to the user's balance. | reward_id, source_type, source_id, amount, unit | K-RWD-01, K-RWD-02, K-RWD-05, K-RWD-06 | Critical |
| reward_rejected | Rewards | server | A pending reward is not granted after validation. | reward_id, reversal_reason_category | K-RWD-01 | High |
| reward_reversed | Rewards | server | A previously credited reward is fully reversed. | reward_id, amount, unit, reversal_reason_category | K-RWD-03, K-WAL-04 | Critical |
| reward_corrected | Rewards | server | A credited reward's amount is changed by a correction. | reward_id, previous_amount, final_amount, unit, reversal_reason_category | K-RWD-02, K-WAL-04 | High |
| daily_reward_claimed | Engagement | server | Valid daily claim accepted within the IST claim window. | claim_date_ist, streak_length | K-ENG-09 | High |
| streak_updated | Engagement | server | Streak counter changes (increment, reset or start). | streak_length, previous_streak_length, streak_action | K-ENG-09 | Medium |
| mission_started | Engagement | server | User joins or is enrolled in a mission. | mission_id, mission_progress_id | K-ENG-11 | Medium |
| mission_completed | Engagement | server | All mission conditions verified complete. | mission_id, mission_progress_id | K-ENG-11 | Medium |
| badge_earned | Engagement | server | Badge awarded to the user. | badge_id, badge_type | K-ENG-01 | Low |
| level_reached | Engagement | server | User's level changes. | previous_level, new_level | K-ENG-08 | Low |
| spin_started | Engagement | server | Spin request accepted and spin cost deducted. | spin_id, spin_cost_unit | K-ENG-10 | Medium |
| spin_completed | Engagement | server | Spin outcome recorded by the backend. | spin_id, outcome_type | K-ENG-10 | Medium |
| promo_code_redeemed | Engagement | server | Promo code accepted and benefit granted. | promo_code_id | K-RWD-05 | Low |
| feature_viewed | Engagement | client | A product screen becomes visible. | screen_name | K-ENG-01 | Low |
| referral_created | Referrals | server | Referrer shares an invite through an in-app share action, or a referral record is created at registration for a code used without a tracked share. | referral_id, referrer_user_id, referral_code | K-REF-01 | High |
| referral_registered | Referrals | server | A new account is created with a valid referral code. | referral_id, referrer_user_id, referred_user_id | K-REF-02, K-REF-05 | Critical |
| referral_activated | Referrals | server | Referred user completes the first eligible activity. | referral_id, referred_user_id, activity_id | K-REF-03 | High |
| referral_converted | Referrals | server | Referral passes validation and the referral reward is approved. | referral_id, referrer_user_id, reward_id | K-REF-04, K-REF-05 | Critical |
| referral_rejected | Referrals | server | Referral fails validation. | referral_id, rejection_reason_category | K-REF-06 | High |
| wallet_transaction_created | Wallet | server | Ledger row inserted. | transaction_id, transaction_type, direction, amount, unit, transaction_status, reference_type | K-WAL-01, K-WAL-05 | Critical |
| wallet_transaction_completed | Wallet | server | Ledger row reaches 'completed'. | transaction_id, transaction_type, direction, amount, unit | K-WAL-02, K-WAL-03 | Critical |
| wallet_transaction_reversed | Wallet | server | Ledger row is reversed by a linked reversing row. | transaction_id, related_transaction_id, amount, unit | K-WAL-04 | Critical |
| currency_exchanged | Wallet | server | Exchange request completed in the Gems Exchange / Swap Center. | from_unit, to_unit, from_amount, to_amount, transaction_id, credit_transaction_id | K-WAL-01 | Medium |
| withdrawal_requested | Withdrawals | server | Withdrawal request accepted by the backend and redemption debit created. | withdrawal_id, amount_inr, ve_debited, payout_method, debit_transaction_id | K-WDR-01, K-WDR-03, K-WDR-09 | Critical |
| withdrawal_processing | Withdrawals | server | Request moves into review/processing. | withdrawal_id | K-WDR-03 | High |
| withdrawal_completed | Withdrawals | server | Payout partner confirms the transfer. | withdrawal_id, amount_inr, payout_method | K-WDR-02, K-WDR-06, K-WDR-07, K-WDR-10 | Critical |
| withdrawal_rejected | Withdrawals | server | Request rejected during review. | withdrawal_id, reason_category | K-WDR-04, K-WDR-06 | Critical |
| withdrawal_reversed | Withdrawals | server | A completed payout is reversed (e.g. partner failure). | withdrawal_id, reason_category | K-WDR-05 | High |
| help_article_viewed | Support | client | Help-center article becomes visible. | content_id, content_category | K-SUP-03 | Low |
| support_ticket_created | Support | server | Support request logged in the support tool. | ticket_id, issue_category | K-SUP-01, K-SUP-02 | Medium |
| support_ticket_resolved | Support | server | Ticket marked resolved. | ticket_id, ticket_status | K-SUP-04 | Low |

Abandonment is **not** a client event. It is derived when a started task has no completion within the timeout (A-013), and recorded as `task_failed` with `failure_category = user_abandoned`.
