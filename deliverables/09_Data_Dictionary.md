# 09 · Data Dictionary

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

Spreadsheet: [`09_Data_Dictionary.xlsx`](09_Data_Dictionary.xlsx). It defines **181 fields** (the brief's minimum is 75), each with all 12 required attributes plus a `basis` column.

**Why more than 75:** every event property and every field a KPI needs must be defined somewhere, or developers would have to guess. The validator fails the build if an event or KPI references an undefined field. Nothing was added just to reach the number.

**Fields deliberately excluded** from the analytics model even though the supplied dataset has them: `full_name`, `email`, exact `age` (replaced by an optional `age_band`), `gender` and `city`. They have no approved analytical use, and keeping them would breach the brief's rule against unnecessary personal information (see 17).

## Fields per entity

| entity | fields |
| --- | --- |
| all_entities | 1 |
| badges | 2 |
| content | 3 |
| event_properties | 25 |
| feature_events | 11 |
| mission_progress | 6 |
| missions | 2 |
| referrals | 12 |
| rewards | 15 |
| sessions | 7 |
| support_tickets | 9 |
| task_activity | 16 |
| tasks | 8 |
| user_badges | 3 |
| user_status_history | 7 |
| users | 22 |
| wallet_transactions | 14 |
| withdrawal_status_history | 5 |
| withdrawals | 13 |

## Full dictionary

| entity | field_name | data_type | required | allowed_values | sensitivity | definition |
| --- | --- | --- | --- | --- | --- | --- |
| all_entities | data_environment | enum | Yes | production, staging, simulated | Internal | Marks whether a record is production, staging or simulated data. Required on every analytics table so simulated rows can never be mixed into production reporting silently. |
| users | user_id | string | Yes |  | Internal | Stable, opaque identifier for one VELOOP account. Never reused, never derived from email or phone. |
| users | registration_at_utc | timestamp | Yes |  | Internal | Moment the account record was successfully created. |
| users | registration_method | enum | Yes | web_registration, google_sign_in | Internal | How the account was created. |
| users | acquisition_source | enum | Yes | organic_search, direct, social_media, referral, whatsapp, telegram, other | Internal | Channel the user arrived from at registration, captured once and never overwritten. |
| users | acquisition_campaign | string | No |  | Internal | Campaign identifier from UTM or partner link, if any. |
| users | referral_id | string | Conditional |  | Internal | Referral record that brought this user, when acquisition_source = referral. |
| users | signup_platform | enum | Yes | web, android, ios | Internal | Client platform used at registration. |
| users | signup_device_type | enum | No | mobile, tablet, desktop | Internal | Device class at registration, derived from user agent. |
| users | country_code | string | Yes |  | Internal | ISO 3166-1 alpha-2 country of the account. |
| users | state_region | string | No |  | Restricted | Coarse region (Indian state) if collected for eligibility. Not city, not address. |
| users | account_status | enum | Yes | pending_verification, active, inactive, suspended, closed | Internal | Current lifecycle status of the account. |
| users | account_status_updated_at_utc | timestamp | Yes |  | Internal | When account_status last changed. |
| users | email_verification_status | enum | Yes | pending, verified | Internal | Whether the email address has been verified. |
| users | email_verified_at_utc | timestamp | Conditional |  | Internal | When email verification succeeded. |
| users | onboarding_status | enum | Yes | not_started, started, completed | Internal | Furthest onboarding state reached. |
| users | onboarding_started_at_utc | timestamp | Conditional |  | Internal | First onboarding_started event time. |
| users | onboarding_completed_at_utc | timestamp | Conditional |  | Internal | First onboarding_completed event time. |
| users | consent_status | enum | Yes | pending, accepted, withdrawn | Internal | Status of acceptance of terms/privacy notice required to use the platform. |
| users | marketing_opt_in | boolean | Yes | true, false | Internal | Whether the user opted in to marketing messages. Must be false unless consent_status = accepted. |
| users | last_activity_at_utc | timestamp | No |  | Internal | Timestamp of the user's most recent qualifying activity event (see KPI K-USR-02 definition). |
| users | current_level | integer | No |  | Internal | Current level in the level system. |
| users | age_band | enum | No | 18-24, 25-34, 35-44, 45+ | Restricted | Age band, collected only if an approved business question needs it. |
| user_status_history | status_change_id | string | Yes |  | Internal | Unique identifier of one account status change. |
| user_status_history | user_id | string | Yes |  | Internal | Account whose status changed. |
| user_status_history | previous_status | enum | Yes | pending_verification, active, inactive, suspended, closed | Internal | Status before the change. |
| user_status_history | new_status | enum | Yes | pending_verification, active, inactive, suspended, closed | Internal | Status after the change. |
| user_status_history | changed_at_utc | timestamp | Yes |  | Internal | When the change took effect. |
| user_status_history | change_reason_category | enum | Yes | email_verified, inactivity_rule, policy_enforcement, user_request, appeal_upheld, other | Restricted | High-level reason category. Not the internal enforcement rule or threshold. |
| user_status_history | changed_by_type | enum | Yes | system, admin, user | Internal | Type of actor that made the change. |
| sessions | session_id | string | Yes |  | Internal | Identifier of one continuous period of use, created at login or app open and closed after inactivity timeout. |
| sessions | user_id | string | Yes |  | Internal | Owner of the session. |
| sessions | session_start_utc | timestamp | Yes |  | Internal | Start of the session. |
| sessions | session_end_utc | timestamp | No |  | Internal | End of the session (last event + timeout, or logout). |
| sessions | platform | enum | Yes | web, android, ios | Internal | Platform of the session. |
| sessions | device_type | enum | No | mobile, tablet, desktop | Internal | Device class of the session. |
| sessions | app_version | string | No |  | Internal | Client build version. |
| feature_events | event_id | string | Yes |  | Internal | Globally unique identifier for one event occurrence, generated once at the producer and reused on every retry. |
| feature_events | event_name | enum | Yes | See deliverable 08 | Internal | Name of the event from the approved catalogue (deliverable 08). |
| feature_events | user_id | string | Yes |  | Internal | Account that performed or received the event. |
| feature_events | session_id | string | Conditional |  | Internal | Session in which a client event happened. Server events may carry the originating session when known. |
| feature_events | event_timestamp_utc | timestamp | Yes |  | Internal | When the event happened at the producer. |
| feature_events | received_at_utc | timestamp | Yes |  | Internal | When the collection layer received the event. |
| feature_events | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Internal | Product feature the event belongs to. |
| feature_events | platform | enum | Yes | web, android, ios | Internal | Platform where the event was produced. |
| feature_events | event_source | enum | Yes | client, server | Internal | Whether the event was emitted by the client or the server. |
| feature_events | schema_version | integer | Yes |  | Internal | Version of the event's property schema. |
| feature_events | app_version | string | No |  | Internal | Client build version for client events. |
| event_properties | login_method | enum | Yes | password, google_sign_in | Internal | Authentication method used for the login. |
| event_properties | logout_type | enum | Yes | user_initiated, session_expired, forced | Internal | How the session ended. |
| event_properties | onboarding_version | string | Yes |  | Internal | Identifier of the onboarding flow version shown. |
| event_properties | step_key | string | Yes |  | Internal | Stable key of an onboarding step. |
| event_properties | step_index | integer | Yes |  | Internal | Position of the onboarding step (1-based). |
| event_properties | list_position | integer | No |  | Internal | Position of a task card in the task list when viewed. |
| event_properties | failure_stage | enum | Yes | start, in_task, tracking, validation | Internal | Stage of the task lifecycle where failure happened. |
| event_properties | previous_amount | integer | Yes |  | Internal | Amount before a reward correction. |
| event_properties | claim_date_ist | date | Yes |  | Internal | IST calendar day the daily reward was claimed for. |
| event_properties | streak_length | integer | Yes |  | Internal | Consecutive-day streak after the update. |
| event_properties | previous_streak_length | integer | Yes |  | Internal | Streak before the update. |
| event_properties | streak_action | enum | Yes | incremented, reset, started | Internal | What happened to the streak. |
| event_properties | spin_id | string | Yes |  | Internal | Identifier of one spin attempt. |
| event_properties | spin_cost_unit | enum | Yes | VE, GEM, XP, TOKEN, SPIN | Internal | Credit consumed to spin. |
| event_properties | outcome_type | enum | Yes | reward, no_reward, interrupted | Internal | Result class of the spin. The prize logic itself is not recorded here. |
| event_properties | previous_level | integer | Yes |  | Internal | Level before a level change. |
| event_properties | new_level | integer | Yes |  | Internal | Level after a level change. |
| event_properties | promo_code_id | string | Yes |  | Internal | Internal identifier of the promo code (not the code text). |
| event_properties | screen_name | string | Yes |  | Internal | Stable name of the screen viewed. |
| event_properties | from_unit | enum | Yes | VE, GEM, TOKEN, SPIN | Internal | Unit given up in an exchange. |
| event_properties | to_unit | enum | Yes | VE, GEM, TOKEN, SPIN | Internal | Unit received in an exchange. |
| event_properties | from_amount | integer | Yes |  | Internal | Amount given up. |
| event_properties | to_amount | integer | Yes |  | Internal | Amount received. |
| event_properties | credit_transaction_id | string | Yes |  | Internal | Wallet transaction that credited the received unit. |
| event_properties | refund_transaction_id | string | Yes |  | Internal | Wallet transaction that returned funds after a rejected or reversed withdrawal. |
| tasks | task_id | string | Yes |  | Internal | Identifier of one configured task/offer. |
| tasks | task_type | enum | Yes | watch_ad, survey, app_task, captcha, tap_earn, earning_session, game, social_follow | Internal | Kind of task. |
| tasks | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Internal | Feature the task is shown in. |
| tasks | fulfilment_source | enum | Yes | veloop_internal, external_partner | Internal | Whether completion is decided by VELOOP or by an external partner (ads, surveys, offers). |
| tasks | provider_id | string | Conditional |  | Internal | Pseudonymous identifier of the external partner. |
| tasks | reward_unit | enum | Yes | VE, GEM, XP, TOKEN, SPIN | Internal | Unit the task pays in. |
| tasks | reward_amount | integer | Yes |  | Internal | Configured reward amount for one valid completion. |
| tasks | task_config_status | enum | Yes | active, paused, retired | Internal | Whether the task is currently offered. |
| task_activity | activity_id | string | Yes |  | Internal | Identifier of one user's attempt at one task, created when the task is started. |
| task_activity | user_id | string | Yes |  | Internal | User attempting the task. |
| task_activity | task_id | string | Yes |  | Internal | Task attempted. |
| task_activity | task_type | enum | Yes | watch_ad, survey, app_task, captcha, tap_earn, earning_session, game, social_follow | Internal | Copied from tasks at start time so history survives config changes. |
| task_activity | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Internal | Feature where the task was started. |
| task_activity | session_id | string | No |  | Internal | Session in which the task was started. |
| task_activity | started_at_utc | timestamp | Yes |  | Internal | When the user started the task. |
| task_activity | completed_at_utc | timestamp | Conditional |  | Internal | When the user finished the task action (before validation). |
| task_activity | validated_at_utc | timestamp | Conditional |  | Internal | When validation reached a final result. |
| task_activity | activity_status | enum | Yes | in_progress, pending_validation, completed, failed, abandoned | Internal | Lifecycle status of the attempt. Describes the activity, not whether a reward was credited. |
| task_activity | validation_status | enum | Yes | pending, passed, failed, not_reached | Internal | Result of completion validation. |
| task_activity | failure_category | enum | Conditional | task_failed, tracking_failed, validation_failed, user_abandoned, system_error | Internal | Proposed failure classification. Not an internal error code. |
| task_activity | tracking_source | string | Yes |  | Internal | Who reported the completion: 'veloop' or a registered partner code. |
| task_activity | external_reference_id | string | Conditional |  | Restricted | Partner's own transaction reference for the completion (postback ID). |
| task_activity | reward_amount | integer | Conditional |  | Internal | Expected reward amount for the attempt at the time of start. |
| task_activity | reward_unit | enum | Conditional | VE, GEM, XP, TOKEN, SPIN | Internal | Unit of reward_amount. |
| rewards | reward_id | string | Yes |  | Internal | Identifier of one reward decision (pending, credited, reversed, corrected). |
| rewards | user_id | string | Yes |  | Internal | User receiving the reward. |
| rewards | source_type | enum | Yes | task, daily_reward, streak, spin, mission, badge, referral, promo_code, leaderboard, manual_adjustment | Internal | What generated the reward. |
| rewards | source_id | string | Yes |  | Internal | Identifier of the generating record (activity_id, event_id, referral_id...). |
| rewards | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Internal | Feature credited for the reward. |
| rewards | amount | integer | Yes |  | Internal | Amount originally granted or expected. |
| rewards | final_amount | integer | Yes |  | Internal | Amount that stands after corrections or reversal (0 if reversed). |
| rewards | unit | enum | Yes | VE, GEM, XP, TOKEN, SPIN | Internal | Unit of the reward. |
| rewards | reward_status | enum | Yes | pending, credited, rejected, reversed, corrected | Internal | Current reward state. Distinguishes 'activity occurred' from 'reward actually credited'. |
| rewards | created_at_utc | timestamp | Yes |  | Internal | When the reward record was created. |
| rewards | credited_at_utc | timestamp | Conditional |  | Internal | When the reward was credited to the user. |
| rewards | reversed_at_utc | timestamp | Conditional |  | Internal | When a credited reward was reversed. |
| rewards | reversal_reason_category | enum | Conditional | invalid_activity, tracking_dispute, duplicate_credit, technical_correction, policy_violation | Restricted | Reason category for reversal or correction. Not a fraud threshold. |
| rewards | wallet_transaction_id | string | Conditional |  | Internal | Wallet transaction created by crediting this reward (spendable units only). |
| rewards | idempotency_key | string | Yes |  | Internal | Key that guarantees one reward per source event even if the request is retried. |
| wallet_transactions | transaction_id | string | Yes |  | Internal | Identifier of one ledger movement. Never reused. |
| wallet_transactions | user_id | string | Yes |  | Internal | Wallet owner. |
| wallet_transactions | transaction_type | enum | Yes | reward_credit, reversal, adjustment, exchange_debit, exchange_credit, redemption_debit, redemption_refund | Internal | Business type of the movement. |
| wallet_transactions | direction | enum | Yes | credit, debit | Internal | Whether the balance goes up (credit) or down (debit). |
| wallet_transactions | amount | integer | Yes |  | Internal | Absolute amount moved. Sign is carried by direction. |
| wallet_transactions | unit | enum | Yes | VE, GEM, TOKEN, SPIN | Internal | Wallet unit moved. |
| wallet_transactions | transaction_status | enum | Yes | pending, completed, failed, reversed | Internal | Current state of the movement. |
| wallet_transactions | reference_type | enum | Yes | reward, withdrawal, exchange, manual_adjustment | Internal | Kind of business record that caused the movement. |
| wallet_transactions | reference_id | string | Conditional |  | Internal | Identifier of the causing record (reward_id, withdrawal_id...). |
| wallet_transactions | related_transaction_id | string | Conditional |  | Internal | Original transaction that this one reverses, corrects or pairs with. |
| wallet_transactions | created_at_utc | timestamp | Yes |  | Internal | When the movement was recorded. |
| wallet_transactions | completed_at_utc | timestamp | Conditional |  | Internal | When the movement became final. |
| wallet_transactions | balance_after | integer | No |  | Restricted | Balance of this unit after the movement. |
| wallet_transactions | idempotency_key | string | Yes |  | Internal | Key that prevents the same business action creating two ledger rows. |
| withdrawals | withdrawal_id | string | Yes |  | Internal | Identifier of one withdrawal/redemption request. |
| withdrawals | user_id | string | Yes |  | Internal | Requesting user. |
| withdrawals | amount_inr | decimal | Yes |  | Internal | Requested payout value in Indian rupees. |
| withdrawals | ve_debited | integer | Yes |  | Internal | VEs debited from the wallet for the request. |
| withdrawals | payout_method | enum | Yes | UPI, PayPal, Amazon Gift Card, Google Play Gift Card | Internal | Requested payout method. |
| withdrawals | withdrawal_status | enum | Yes | requested, processing, completed, rejected, reversed | Internal | Current lifecycle state. |
| withdrawals | requested_at_utc | timestamp | Yes |  | Internal | When the user submitted the request. |
| withdrawals | processing_at_utc | timestamp | Conditional |  | Internal | When review/processing started. |
| withdrawals | final_at_utc | timestamp | Conditional |  | Internal | When the request reached completed, rejected or reversed. |
| withdrawals | reason_category | enum | Conditional | verification_failed, payout_details_invalid, policy_violation, payout_partner_failure | Restricted | Reason category for rejection or reversal. |
| withdrawals | review_type | enum | No | system, manual | Internal | Whether the request went through system-only or manual review. |
| withdrawals | debit_transaction_id | string | Yes |  | Internal | Wallet redemption_debit created for this request. |
| withdrawals | payout_reference_id | string | Conditional |  | Restricted | Payout partner's reference for the transfer. Never a UPI ID, account number or card number. |
| withdrawal_status_history | status_history_id | string | Yes |  | Internal | Identifier of one withdrawal status transition. |
| withdrawal_status_history | withdrawal_id | string | Yes |  | Internal | Withdrawal that changed status. |
| withdrawal_status_history | from_status | enum | Conditional | requested, processing, completed, rejected, reversed | Internal | Status before the transition (blank for creation). |
| withdrawal_status_history | to_status | enum | Yes | requested, processing, completed, rejected, reversed | Internal | Status after the transition. |
| withdrawal_status_history | changed_at_utc | timestamp | Yes |  | Internal | When the transition happened. |
| referrals | referral_id | string | Yes |  | Internal | Identifier of one referral relationship. |
| referrals | referrer_user_id | string | Yes |  | Internal | User who referred. |
| referrals | referred_user_id | string | Conditional |  | Internal | User who registered through the referral. Blank until registration. |
| referrals | referral_code | string | Yes |  | Internal | Referrer's code used. Codes are public share codes, not secrets. |
| referrals | referral_channel | enum | No | whatsapp, telegram, copy_link, other | Internal | Channel used to share the invite, when known. |
| referrals | referral_status | enum | Yes | created, registered, activated, converted, rejected, expired | Internal | Furthest stage reached. Registration alone is NOT conversion. |
| referrals | created_at_utc | timestamp | Yes |  | Internal | When the referral record was created. |
| referrals | registered_at_utc | timestamp | Conditional |  | Internal | When the referred user registered. |
| referrals | activated_at_utc | timestamp | Conditional |  | Internal | When the referred user completed the first eligible activity. |
| referrals | converted_at_utc | timestamp | Conditional |  | Internal | When the referral passed validation and the referral reward was approved. |
| referrals | rejection_reason_category | enum | Conditional | verification_failed, policy_violation | Restricted | Why a referral was rejected. |
| referrals | reward_id | string | Conditional |  | Internal | Referral reward issued on conversion. |
| missions | mission_id | string | Yes |  | Internal | Identifier of a configured mission. |
| missions | mission_type | string | Yes |  | Internal | Mission category (daily activity, referral, ads...). |
| mission_progress | mission_progress_id | string | Yes |  | Internal | One user's progress record on one mission. |
| mission_progress | user_id | string | Yes |  | Internal | User working on the mission. |
| mission_progress | mission_id | string | Yes |  | Internal | Mission being progressed. |
| mission_progress | mission_status | enum | Yes | started, completed, expired | Internal | User's state on the mission. |
| mission_progress | started_at_utc | timestamp | Yes |  | Internal | When the user started the mission. |
| mission_progress | completed_at_utc | timestamp | Conditional |  | Internal | When all mission conditions were met. |
| badges | badge_id | string | Yes |  | Internal | Identifier of a configured badge. |
| badges | badge_type | enum | Yes | reward, recognition_only | Internal | Whether the badge carries a reward or is recognition only. |
| user_badges | user_id | string | Yes |  | Internal | Badge holder. Part of the composite primary key. |
| user_badges | badge_id | string | Yes |  | Internal | Badge earned. Part of the composite primary key. |
| user_badges | earned_at_utc | timestamp | Yes |  | Internal | When the user earned the badge. |
| support_tickets | ticket_id | string | Yes |  | Internal | Identifier of one support request. |
| support_tickets | user_id | string | Conditional |  | Internal | User who raised the request, if known. |
| support_tickets | issue_category | enum | Yes | withdrawal, missing_reward, account_access, account_restriction, referral, technical, privacy_request, other | Internal | Agent-assigned issue category. |
| support_tickets | ticket_status | enum | Yes | open, pending_user, resolved, closed | Internal | Ticket state. |
| support_tickets | created_at_utc | timestamp | Yes |  | Internal | When the request was received. |
| support_tickets | first_response_at_utc | timestamp | Conditional |  | Internal | First support reply. |
| support_tickets | resolved_at_utc | timestamp | Conditional |  | Internal | When the ticket was resolved. |
| support_tickets | related_entity_type | enum | No | withdrawal, reward, referral, account, other | Internal | Business object the ticket is about. |
| support_tickets | related_entity_id | string | No |  | Internal | ID of that object (withdrawal_id, reward_id...). |
| content | content_id | string | Yes |  | Public | Identifier of a help-center article. |
| content | content_category | enum | Yes | getting_started, earning, wallet, withdrawals, safety, future_features, legal | Public | Help-center category. |
| content | content_last_updated_date | date | No |  | Public | Last updated date shown on the article. |
