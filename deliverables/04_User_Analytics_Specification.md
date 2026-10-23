# 04 · User & Account Analytics Specification

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

## Requirements by lifecycle stage

| Stage | Required data | Events |
| --- | --- | --- |
| Registration | user_id, registration_at_utc, acquisition_source (+ campaign, referral_id), signup_platform, signup_device_type, registration_method | `user_registered` |
| Login | login event, timestamp, session_id, device/platform | `user_logged_in`, `user_logged_out` (where a logout exists) |
| Onboarding | started, completed, step milestones | `onboarding_started`, `onboarding_step_completed`, `onboarding_completed` |
| Account lifecycle | account created, current status, every status change with timestamp and reason category, last activity | `account_status_changed`, `email_verified`; `users.last_activity_at_utc` derived |

## B1 Identity requirements

| identifier | field | why_needed |
| --- | --- | --- |
| Stable user identifier | user_id | Joins every table; must survive email change, re-login and device change. Never email or phone (they change, and they are personal data). |
| Event identifier | event_id | Makes each event unique so retries and duplicate deliveries can be removed (DQ-M12 shows what happens without it). |
| Session identifier | session_id | Groups events into visits; needed for returning users, session length and funnels inside one visit. Proposed, because current implementation needs engineering verification. |
| Transaction identifier | transaction_id (wallet), activity_id (task), reward_id, withdrawal_id, referral_id | Uniquely identifies each business transaction so money can be deduplicated, reversed with a link to the original, and reconciled across tables. |

## B2 User analytics specification

| entity | field | type | required? | purpose | source | validation | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| users | user_id | string | Yes | Join key across every user-level table; enables cross-feature analysis. | Backend (auth/account service) | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Proposed |
| users | registration_at_utc | timestamp | Yes | Registrations KPI, cohort assignment, time-to-activation. | Backend | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; not before product launch date | Proposed |
| users | registration_method | enum | Yes | Compare activation by sign-up method. | Backend | Must be in allowed list | Proposed |
| users | acquisition_source | enum | Yes | Acquisition mix and channel quality. | Frontend (UTM/referrer) + backend | Must be in allowed list; 'referral' requires referral_id | Proposed |
| users | acquisition_campaign | string | No | Campaign-level acquisition analysis. | Frontend (UTM) | Max 100 chars; lowercase snake_case | Proposed |
| users | referral_id | string | Conditional | Links referred users to referrers (missing in supplied data, gap G02). | Backend (referral service) | Must exist in referrals.referral_id when present | Proposed |
| users | signup_platform | enum | Yes | Platform mix; separates web from future app. | Frontend | Must be in allowed list | Proposed |
| users | signup_device_type | enum | No | Device mix for UX prioritisation. | Frontend | Must be in allowed list | Proposed |
| users | country_code | string | Yes | Region eligibility reporting (official pages mention region support). | Backend (profile/region check) | Two uppercase letters | Proposed |
| users | state_region | string | No | Geographic distribution at state level only. | Backend | Must match approved state list | Proposed |
| users | account_status | enum | Yes | Active base, suspensions, lifecycle reporting. | Backend | Must be in allowed list; changes must create a user_status_history row | Proposed |
| users | account_status_updated_at_utc | timestamp | Yes | Freshness of status; joins to status history. | Backend | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= registration_at_utc | Proposed |
| users | email_verification_status | enum | Yes | Verification funnel. | Backend | Must be in allowed list | Proposed |
| users | email_verified_at_utc | timestamp | Conditional | Time-to-verify. | Backend | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; required when status = verified | Proposed |
| users | onboarding_status | enum | Yes | Onboarding completion rate. | Backend (from onboarding events) | Must be in allowed list | Proposed |
| users | onboarding_started_at_utc | timestamp | Conditional | Time-to-onboard. | Derived from events | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= registration_at_utc | Proposed |
| users | onboarding_completed_at_utc | timestamp | Conditional | Time-to-onboard. | Derived from events | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= onboarding_started_at_utc | Proposed |
| users | consent_status | enum | Yes | Governance: only consented users in analytics where required. | Backend | Must be in allowed list | Proposed |
| users | marketing_opt_in | boolean | Yes | Reachable audience sizing. | Backend | false when consent_status != accepted | Proposed |
| users | last_activity_at_utc | timestamp | No | Inactive users, recency segmentation. | Derived (analytics layer) | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= registration_at_utc | Proposed |
| users | current_level | integer | No | Progression distribution. | Backend (progression service) | >= 1 | Proposed |
| users | age_band | enum | No | Optional segmentation; replaces exact age. | Backend | Must be in allowed list; never store date of birth in analytics | Proposed |
| user_status_history | status_change_id | string | Yes | Primary key; dedup. | Backend | Non-null; immutable; unique within entity | Proposed |
| user_status_history | user_id | string | Yes | Join to users. | Backend | Must exist in users | Proposed |
| user_status_history | previous_status | enum | Yes | Transition analysis. | Backend | Must differ from new_status | Proposed |
| user_status_history | new_status | enum | Yes | Suspension and reactivation counts. | Backend | Must be an allowed transition (deliverable 13 state rules) | Proposed |
| user_status_history | changed_at_utc | timestamp | Yes | Lifecycle timing. | Backend | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Proposed |
| user_status_history | change_reason_category | enum | Yes | Explains lifecycle movement without exposing security controls. | Backend | Must be in allowed list | Proposed |
| user_status_history | changed_by_type | enum | Yes | Separates automated from manual decisions. | Backend | Must be in allowed list | Proposed |
| sessions | session_id | string | Yes | Session-level analysis; groups events. | Frontend/backend session service | Non-null; immutable; unique within entity; timeout rule To Be Verified (A-007) | Proposed |
| sessions | user_id | string | Yes | Join key. | Backend | Must exist in users | Proposed |
| sessions | session_start_utc | timestamp | Yes | Sessions per user, returning users. | Frontend/backend | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Proposed |
| sessions | session_end_utc | timestamp | No | Session duration. | Derived | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= session_start_utc | Proposed |
| sessions | platform | enum | Yes | Platform split. | Frontend | Must be in allowed list | Proposed |
| sessions | device_type | enum | No | Device split. | Frontend | Must be in allowed list | Proposed |
| sessions | app_version | string | No | Attributes data issues to releases. | Frontend | Semantic or dated version string | Proposed |

## From the supplied Users structure to the proposed one

The supplied structure asks for more personal data than analytics needs and less behavioural data than it needs.

| supplied_field | proposed | reason |
| --- | --- | --- |
| user_id | user_id | Keep |
| full_name | (removed) | Not needed for analytics; identity store only |
| email | (removed) | Not needed; identity store only |
| age | age_band (optional) | Exact age unnecessary |
| gender | (removed) | No approved business question |
| state | state_region (optional) | Coarse region only |
| city | (removed) | Too granular |
| registration_datetime | registration_at_utc | Add timezone |
| acquisition_source | acquisition_source | Normalise to snake_case |
| referral_source_detail | referral_id | Link to referrer instead of free text |
| primary_device | signup_device_type + sessions.device_type | Separate device class from OS |
| platform | signup_platform | Document meaning |
| account_status | account_status + user_status_history | Add history |
| email_verification_status | email_verification_status + email_verified_at_utc | Add timestamp |
| onboarding_status | onboarding_status + started/completed timestamps | Add timestamps |
| last_login_datetime | sessions + last_activity_at_utc | Login is not activity |
| lifetime_sessions | (derived from sessions) | Do not store counters in source |
| active_days | (derived from events) | Inconsistent in supplied data (DQ-C01) |
| xp_balance | (derived from rewards, unit XP) | Balance needs a ledger |
| referral_code | referrals.referral_code | Public share code |
| days_since_registration | (derived downstream) | Stale / negative values |
| is_active_7d / is_active_30d | K-USR-03 / K-USR-04 | Recomputed, documented |
| consent_status | consent_status | Keep |
| marketing_opt_in | marketing_opt_in | Must respect consent |
| account_created_via | registration_method | Rename |
| country | country_code | ISO code |
