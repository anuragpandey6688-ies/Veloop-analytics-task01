"""Work Package G: VELOOP analytics data dictionary (single source of truth).

Every field is PROPOSED. Nothing here has been verified against VELOOP production systems.
`basis` records why the field exists or where its allowed values came from.
Sensitivity: Public / Internal / Restricted (see deliverable 17 for handling rules).
"""
from . import enums as E

TS_VALID = "ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew"
ID_VALID = "Non-null; immutable; unique within entity"


def _al(values):
    return ", ".join(values)


# entity, field, type, definition, example, required, allowed, validation, source, sensitivity, use, basis
F = [
    # ---------------------------------------------------------------- common envelope / governance
    ("all_entities", "data_environment", "enum", "Marks whether a record is production, staging or simulated data. Required on every analytics table so simulated rows can never be mixed into production reporting silently.", "simulated", "Yes", "production, staging, simulated", "Must equal 'production' in any table feeding management dashboards", "Pipeline (load job)", "Internal", "Prevents simulated data from being reported as actual VELOOP results (integrity rule 12).", "Task 01 section 34 rule 12"),

    # ---------------------------------------------------------------- users
    ("users", "user_id", "string", "Stable, opaque identifier for one VELOOP account. Never reused, never derived from email or phone.", "VLUSR000001", "Yes", "", ID_VALID + "; pattern agreed with engineering (simulated: ^VLUSR\\d{6}$)", "Backend (auth/account service)", "Internal", "Join key across every user-level table; enables cross-feature analysis.", "B1 identity requirement"),
    ("users", "registration_at_utc", "timestamp", "Moment the account record was successfully created.", "2026-06-10T01:44:00Z", "Yes", "", TS_VALID + "; not before product launch date", "Backend", "Internal", "Registrations KPI, cohort assignment, time-to-activation.", "Supplied field registration_datetime has no timezone (gap G03)"),
    ("users", "registration_method", "enum", "How the account was created.", "google_sign_in", "Yes", _al(E.REGISTRATION_METHODS), "Must be in allowed list", "Backend", "Internal", "Compare activation by sign-up method.", "Supplied account_created_via; Google login named in privacy policy"),
    ("users", "acquisition_source", "enum", "Channel the user arrived from at registration, captured once and never overwritten.", "organic_search", "Yes", _al(E.ACQUISITION_SOURCES), "Must be in allowed list; 'referral' requires referral_id", "Frontend (UTM/referrer) + backend", "Internal", "Acquisition mix and channel quality.", "Supplied acquisition_source values, normalised to snake_case"),
    ("users", "acquisition_campaign", "string", "Campaign identifier from UTM or partner link, if any.", "seasonal_aug_2026", "No", "", "Max 100 chars; lowercase snake_case", "Frontend (UTM)", "Internal", "Campaign-level acquisition analysis.", "Gap: not present in supplied data"),
    ("users", "referral_id", "string", "Referral record that brought this user, when acquisition_source = referral.", "VLREF000123", "Conditional", "", "Must exist in referrals.referral_id when present", "Backend (referral service)", "Internal", "Links referred users to referrers (missing in supplied data, gap G02).", "E1 referral requirement"),
    ("users", "signup_platform", "enum", "Client platform used at registration.", "web", "Yes", _al(E.PLATFORMS), "Must be in allowed list", "Frontend", "Internal", "Platform mix; separates web from future app.", "Supplied platform is 'Web' for 100% of rows; official site says app is coming soon"),
    ("users", "signup_device_type", "enum", "Device class at registration, derived from user agent.", "mobile", "No", _al(E.DEVICE_TYPES), "Must be in allowed list", "Frontend", "Internal", "Device mix for UX prioritisation.", "Supplied primary_device mixes OS and class"),
    ("users", "country_code", "string", "ISO 3166-1 alpha-2 country of the account.", "IN", "Yes", "", "Two uppercase letters", "Backend (profile/region check)", "Internal", "Region eligibility reporting (official pages mention region support).", "Supplied country = India"),
    ("users", "state_region", "string", "Coarse region (Indian state) if collected for eligibility. Not city, not address.", "Odisha", "No", "", "Must match approved state list", "Backend", "Restricted", "Geographic distribution at state level only.", "Supplied state/city; city dropped as unnecessary (B2 minimisation)"),
    ("users", "account_status", "enum", "Current lifecycle status of the account.", "active", "Yes", _al(E.ACCOUNT_STATUSES), "Must be in allowed list; changes must create a user_status_history row", "Backend", "Internal", "Active base, suspensions, lifecycle reporting.", "Supplied values normalised; 'closed' proposed for deletion requests"),
    ("users", "account_status_updated_at_utc", "timestamp", "When account_status last changed.", "2026-07-02T09:00:00Z", "Yes", "", TS_VALID + "; >= registration_at_utc", "Backend", "Internal", "Freshness of status; joins to status history.", "Gap G04: no status history in supplied data"),
    ("users", "email_verification_status", "enum", "Whether the email address has been verified.", "verified", "Yes", _al(E.EMAIL_VERIFICATION_STATUSES), "Must be in allowed list", "Backend", "Internal", "Verification funnel.", "Supplied field"),
    ("users", "email_verified_at_utc", "timestamp", "When email verification succeeded.", "2026-06-10T02:10:00Z", "Conditional", "", TS_VALID + "; required when status = verified", "Backend", "Internal", "Time-to-verify.", "Gap: supplied data has status only"),
    ("users", "onboarding_status", "enum", "Furthest onboarding state reached.", "completed", "Yes", _al(E.ONBOARDING_STATUSES), "Must be in allowed list", "Backend (from onboarding events)", "Internal", "Onboarding completion rate.", "Supplied field"),
    ("users", "onboarding_started_at_utc", "timestamp", "First onboarding_started event time.", "2026-06-10T01:45:00Z", "Conditional", "", TS_VALID + "; >= registration_at_utc", "Derived from events", "Internal", "Time-to-onboard.", "B onboarding requirement"),
    ("users", "onboarding_completed_at_utc", "timestamp", "First onboarding_completed event time.", "2026-06-10T01:52:00Z", "Conditional", "", TS_VALID + "; >= onboarding_started_at_utc", "Derived from events", "Internal", "Time-to-onboard.", "B onboarding requirement"),
    ("users", "consent_status", "enum", "Status of acceptance of terms/privacy notice required to use the platform.", "accepted", "Yes", _al(E.CONSENT_STATUSES), "Must be in allowed list", "Backend", "Internal", "Governance: only consented users in analytics where required.", "Supplied field"),
    ("users", "marketing_opt_in", "boolean", "Whether the user opted in to marketing messages. Must be false unless consent_status = accepted.", "false", "Yes", "true, false", "false when consent_status != accepted", "Backend", "Internal", "Reachable audience sizing.", "Supplied data has 77 'Yes' with consent Pending (DQ issue)"),
    ("users", "last_activity_at_utc", "timestamp", "Timestamp of the user's most recent qualifying activity event (see KPI K-USR-02 definition).", "2026-09-12T10:00:00Z", "No", "", TS_VALID + "; >= registration_at_utc", "Derived (analytics layer)", "Internal", "Inactive users, recency segmentation.", "Supplied last_login_datetime is login-only"),
    ("users", "current_level", "integer", "Current level in the level system.", "4", "No", "", ">= 1", "Backend (progression service)", "Internal", "Progression distribution.", "Level System help page"),
    ("users", "age_band", "enum", "Age band, collected only if an approved business question needs it.", "25-34", "No", "18-24, 25-34, 35-44, 45+", "Must be in allowed list; never store date of birth in analytics", "Backend", "Restricted", "Optional segmentation; replaces exact age.", "Supplied dataset stores exact age (minimisation finding)"),

    # ---------------------------------------------------------------- user_status_history
    ("user_status_history", "status_change_id", "string", "Unique identifier of one account status change.", "VLUSC0000001", "Yes", "", ID_VALID, "Backend", "Internal", "Primary key; dedup.", "Gap G04"),
    ("user_status_history", "user_id", "string", "Account whose status changed.", "VLUSR000005", "Yes", "", "Must exist in users", "Backend", "Internal", "Join to users.", "B lifecycle requirement"),
    ("user_status_history", "previous_status", "enum", "Status before the change.", "active", "Yes", _al(E.ACCOUNT_STATUSES), "Must differ from new_status", "Backend", "Internal", "Transition analysis.", "B lifecycle requirement"),
    ("user_status_history", "new_status", "enum", "Status after the change.", "suspended", "Yes", _al(E.ACCOUNT_STATUSES), "Must be an allowed transition (deliverable 13 state rules)", "Backend", "Internal", "Suspension and reactivation counts.", "B lifecycle requirement"),
    ("user_status_history", "changed_at_utc", "timestamp", "When the change took effect.", "2026-08-01T12:00:00Z", "Yes", "", TS_VALID, "Backend", "Internal", "Lifecycle timing.", "B lifecycle requirement"),
    ("user_status_history", "change_reason_category", "enum", "High-level reason category. Not the internal enforcement rule or threshold.", "policy_enforcement", "Yes", _al(E.STATUS_CHANGE_REASONS), "Must be in allowed list", "Backend", "Restricted", "Explains lifecycle movement without exposing security controls.", "Integrity rule 4: no invented security rules"),
    ("user_status_history", "changed_by_type", "enum", "Type of actor that made the change.", "system", "Yes", _al(E.STATUS_CHANGE_ACTORS), "Must be in allowed list", "Backend", "Internal", "Separates automated from manual decisions.", "Official: manual and system-based validation"),

    # ---------------------------------------------------------------- sessions
    ("sessions", "session_id", "string", "Identifier of one continuous period of use, created at login or app open and closed after inactivity timeout.", "VLSES0000042", "Yes", "", ID_VALID + "; timeout rule To Be Verified (A-007)", "Frontend/backend session service", "Internal", "Session-level analysis; groups events.", "B1 identity requirement"),
    ("sessions", "user_id", "string", "Owner of the session.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key.", "B1"),
    ("sessions", "session_start_utc", "timestamp", "Start of the session.", "2026-06-10T04:00:00Z", "Yes", "", TS_VALID, "Frontend/backend", "Internal", "Sessions per user, returning users.", "B login requirement"),
    ("sessions", "session_end_utc", "timestamp", "End of the session (last event + timeout, or logout).", "2026-06-10T04:25:00Z", "No", "", TS_VALID + "; >= session_start_utc", "Derived", "Internal", "Session duration.", "Proposed"),
    ("sessions", "platform", "enum", "Platform of the session.", "web", "Yes", _al(E.PLATFORMS), "Must be in allowed list", "Frontend", "Internal", "Platform split.", "Proposed"),
    ("sessions", "device_type", "enum", "Device class of the session.", "mobile", "No", _al(E.DEVICE_TYPES), "Must be in allowed list", "Frontend", "Internal", "Device split.", "Proposed"),
    ("sessions", "app_version", "string", "Client build version.", "web-2026.09.1", "No", "", "Semantic or dated version string", "Frontend", "Internal", "Attributes data issues to releases.", "Proposed"),

    # ---------------------------------------------------------------- feature_events (event envelope)
    ("feature_events", "event_id", "string", "Globally unique identifier for one event occurrence, generated once at the producer and reused on every retry.", "VLEVT00000001", "Yes", "", ID_VALID + "; UUID in production; duplicates are dropped on ingestion", "Event producer (client SDK or server)", "Internal", "Deduplication and idempotent ingestion.", "B1 identity requirement"),
    ("feature_events", "event_name", "enum", "Name of the event from the approved catalogue (deliverable 08).", "task_completed", "Yes", "See deliverable 08", "Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue", "Event producer", "Internal", "Event filtering, KPI computation.", "Work Package F"),
    ("feature_events", "user_id", "string", "Account that performed or received the event.", "VLUSR000001", "Yes", "", "Must exist in users", "Event producer", "Internal", "Join key.", "B1"),
    ("feature_events", "session_id", "string", "Session in which a client event happened. Server events may carry the originating session when known.", "VLSES0000042", "Conditional", "", "Required for client events; must exist in sessions", "Client SDK / server", "Internal", "Session analysis.", "B1"),
    ("feature_events", "event_timestamp_utc", "timestamp", "When the event happened at the producer.", "2026-06-10T04:02:11Z", "Yes", "", TS_VALID, "Event producer", "Internal", "All time-based KPIs.", "Timestamp rule (L)"),
    ("feature_events", "received_at_utc", "timestamp", "When the collection layer received the event.", "2026-06-10T04:02:12Z", "Yes", "", TS_VALID + "; >= event_timestamp_utc - 5 min", "Collection layer", "Internal", "Late-arrival monitoring.", "Proposed"),
    ("feature_events", "feature", "enum", "Product feature the event belongs to.", "watch_ads", "Yes", _al(E.FEATURES), "Must be in allowed list", "Event producer", "Internal", "Feature usage and adoption.", "Feature list from official help center"),
    ("feature_events", "platform", "enum", "Platform where the event was produced.", "web", "Yes", _al(E.PLATFORMS), "Must be in allowed list", "Event producer", "Internal", "Platform split.", "Proposed"),
    ("feature_events", "event_source", "enum", "Whether the event was emitted by the client or the server.", "server", "Yes", _al(E.EVENT_SOURCES), "Must match the catalogue's declared source", "Event producer", "Internal", "Trust level: money-related events must be server events.", "Proposed"),
    ("feature_events", "schema_version", "integer", "Version of the event's property schema.", "1", "Yes", "", ">= 1; must match a version in the change log", "Event producer", "Internal", "Safe evolution of events (Work Package Q).", "Proposed"),
    ("feature_events", "app_version", "string", "Client build version for client events.", "web-2026.09.1", "No", "", "Version string", "Client SDK", "Internal", "Release attribution.", "Proposed"),

    # ---------------------------------------------------------------- event-only properties
    ("event_properties", "login_method", "enum", "Authentication method used for the login.", "google_sign_in", "Yes", _al(E.LOGIN_METHODS), "Must be in allowed list", "Backend", "Internal", "Login mix.", "Proposed"),
    ("event_properties", "logout_type", "enum", "How the session ended.", "user_initiated", "Yes", _al(E.LOGOUT_TYPES), "Must be in allowed list", "Client/backend", "Internal", "Session quality.", "Proposed"),
    ("event_properties", "onboarding_version", "string", "Identifier of the onboarding flow version shown.", "v1", "Yes", "", "Non-empty", "Frontend", "Internal", "Compare onboarding versions.", "Proposed"),
    ("event_properties", "step_key", "string", "Stable key of an onboarding step.", "choose_first_task", "Yes", "", "snake_case; from onboarding config", "Frontend", "Internal", "Step-level drop-off.", "Proposed"),
    ("event_properties", "step_index", "integer", "Position of the onboarding step (1-based).", "2", "Yes", "", ">= 1", "Frontend", "Internal", "Funnel ordering.", "Proposed"),
    ("event_properties", "list_position", "integer", "Position of a task card in the task list when viewed.", "3", "No", "", ">= 1", "Frontend", "Internal", "Placement effect on task starts.", "Proposed"),
    ("event_properties", "failure_stage", "enum", "Stage of the task lifecycle where failure happened.", "tracking", "Yes", _al(E.FAILURE_STAGES), "Must be in allowed list", "Backend", "Internal", "Locates funnel breakage.", "C2 proposed classification"),
    ("event_properties", "previous_amount", "integer", "Amount before a reward correction.", "60", "Yes", "", ">= 0", "Backend", "Internal", "Correction impact.", "C3"),
    ("event_properties", "claim_date_ist", "date", "IST calendar day the daily reward was claimed for.", "2026-07-14", "Yes", "", "YYYY-MM-DD; one claim per user per date", "Backend", "Internal", "Daily claim rate; dedup.", "Official: claim window 00:00-23:59 IST"),
    ("event_properties", "streak_length", "integer", "Consecutive-day streak after the update.", "5", "Yes", "", ">= 0", "Backend", "Internal", "Streak distribution.", "Official streak rules"),
    ("event_properties", "previous_streak_length", "integer", "Streak before the update.", "4", "Yes", "", ">= 0", "Backend", "Internal", "Reset detection.", "Proposed"),
    ("event_properties", "streak_action", "enum", "What happened to the streak.", "incremented", "Yes", _al(E.STREAK_ACTIONS), "Must be in allowed list", "Backend", "Internal", "Streak resets vs continuations.", "Proposed"),
    ("event_properties", "spin_id", "string", "Identifier of one spin attempt.", "VLSPN0000101", "Yes", "", ID_VALID, "Backend", "Internal", "Pairs spin_started with spin_completed.", "Proposed"),
    ("event_properties", "spin_cost_unit", "enum", "Credit consumed to spin.", "SPIN", "Yes", _al(E.REWARD_UNITS), "Must be in allowed list", "Backend", "Internal", "Spin economy.", "Official: Spins used for wheel features"),
    ("event_properties", "outcome_type", "enum", "Result class of the spin. The prize logic itself is not recorded here.", "reward", "Yes", _al(E.SPIN_OUTCOMES), "Must be in allowed list", "Backend", "Internal", "Spin completion and interruption rates.", "Official spin page mentions interruptions"),
    ("event_properties", "previous_level", "integer", "Level before a level change.", "3", "Yes", "", ">= 1", "Backend", "Internal", "Progression speed.", "Proposed"),
    ("event_properties", "new_level", "integer", "Level after a level change.", "4", "Yes", "", "> previous_level, unless a correction", "Backend", "Internal", "Progression speed.", "Official: level corrections possible"),
    ("event_properties", "promo_code_id", "string", "Internal identifier of the promo code (not the code text).", "VLPRM0007", "Yes", "", ID_VALID, "Backend", "Internal", "Promo usage without exposing codes.", "Official promo code page"),
    ("event_properties", "screen_name", "string", "Stable name of the screen viewed.", "wallet_overview", "Yes", "", "snake_case", "Frontend", "Internal", "Navigation analysis.", "Proposed"),
    ("event_properties", "from_unit", "enum", "Unit given up in an exchange.", "GEM", "Yes", _al(E.WALLET_UNITS), "Must differ from to_unit", "Backend", "Internal", "Exchange flows.", "Official Gems Exchange Center"),
    ("event_properties", "to_unit", "enum", "Unit received in an exchange.", "VE", "Yes", _al(E.WALLET_UNITS), "Must differ from from_unit", "Backend", "Internal", "Exchange flows.", "Official Gems Exchange Center"),
    ("event_properties", "from_amount", "integer", "Amount given up.", "10", "Yes", "", "> 0", "Backend", "Internal", "Exchange volume.", "Proposed"),
    ("event_properties", "to_amount", "integer", "Amount received.", "20", "Yes", "", "> 0", "Backend", "Internal", "Exchange volume.", "Proposed"),
    ("event_properties", "credit_transaction_id", "string", "Wallet transaction that credited the received unit.", "VLTXN0000456", "Yes", "", "Must exist in wallet_transactions", "Backend", "Internal", "Ledger linkage.", "Proposed"),
    ("event_properties", "refund_transaction_id", "string", "Wallet transaction that returned funds after a rejected or reversed withdrawal.", "VLTXN0000789", "Yes", "", "Must exist in wallet_transactions", "Backend", "Internal", "Refund reconciliation.", "Proposed"),

    # ---------------------------------------------------------------- tasks (catalogue)
    ("tasks", "task_id", "string", "Identifier of one configured task/offer.", "VLTSK0001", "Yes", "", ID_VALID, "Backend (task config)", "Internal", "Join key for task activity.", "C1"),
    ("tasks", "task_type", "enum", "Kind of task.", "watch_ad", "Yes", _al(E.TASK_TYPES), "Must be in allowed list", "Backend", "Internal", "Performance by task type.", "Official earning pages"),
    ("tasks", "feature", "enum", "Feature the task is shown in.", "watch_ads", "Yes", _al(E.FEATURES), "Must be in allowed list", "Backend", "Internal", "Feature attribution.", "Proposed"),
    ("tasks", "fulfilment_source", "enum", "Whether completion is decided by VELOOP or by an external partner (ads, surveys, offers).", "external_partner", "Yes", _al(E.FULFILMENT_SOURCES), "Must be in allowed list", "Backend", "Internal", "Separates third-party dependent outcomes (C4).", "C4"),
    ("tasks", "provider_id", "string", "Pseudonymous identifier of the external partner.", "PRV003", "Conditional", "", "Required when fulfilment_source = external_partner", "Backend", "Internal", "Partner-level tracking reliability.", "C4"),
    ("tasks", "reward_unit", "enum", "Unit the task pays in.", "VE", "Yes", _al(E.REWARD_UNITS), "Must be in allowed list", "Backend", "Internal", "Reward analysis.", "C1"),
    ("tasks", "reward_amount", "integer", "Configured reward amount for one valid completion.", "5", "Yes", "", ">= 0", "Backend", "Internal", "Expected reward cost.", "C1"),
    ("tasks", "task_config_status", "enum", "Whether the task is currently offered.", "active", "Yes", _al(E.TASK_CONFIG_STATUSES), "Must be in allowed list", "Backend", "Internal", "Inventory availability.", "Proposed"),

    # ---------------------------------------------------------------- task_activity
    ("task_activity", "activity_id", "string", "Identifier of one user's attempt at one task, created when the task is started.", "VLACT0000001", "Yes", "", ID_VALID, "Backend", "Internal", "Transaction-level task analysis; links rewards to activity.", "B1 transaction identifier"),
    ("task_activity", "user_id", "string", "User attempting the task.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key.", "C1"),
    ("task_activity", "task_id", "string", "Task attempted.", "VLTSK0001", "Yes", "", "Must exist in tasks", "Backend", "Internal", "Join key.", "C1"),
    ("task_activity", "task_type", "enum", "Copied from tasks at start time so history survives config changes.", "watch_ad", "Yes", _al(E.TASK_TYPES), "Must equal tasks.task_type at start", "Backend", "Internal", "Task type analysis.", "C1"),
    ("task_activity", "feature", "enum", "Feature where the task was started.", "watch_ads", "Yes", _al(E.FEATURES), "Must be in allowed list", "Backend", "Internal", "Feature attribution.", "C1"),
    ("task_activity", "session_id", "string", "Session in which the task was started.", "VLSES0000042", "No", "", "Must exist in sessions when present", "Backend", "Internal", "Session analysis.", "C1"),
    ("task_activity", "started_at_utc", "timestamp", "When the user started the task.", "2026-06-10T04:05:00Z", "Yes", "", TS_VALID + "; >= users.registration_at_utc", "Backend", "Internal", "Task starts, durations.", "C1"),
    ("task_activity", "completed_at_utc", "timestamp", "When the user finished the task action (before validation).", "2026-06-10T04:06:10Z", "Conditional", "", TS_VALID + "; >= started_at_utc", "Backend / partner callback", "Internal", "Duration, completion timing.", "C1"),
    ("task_activity", "validated_at_utc", "timestamp", "When validation reached a final result.", "2026-06-10T04:20:00Z", "Conditional", "", TS_VALID + "; >= completed_at_utc", "Backend", "Internal", "Validation lag (official: ad tracking may take ~15 min).", "C1"),
    ("task_activity", "activity_status", "enum", "Lifecycle status of the attempt. Describes the activity, not whether a reward was credited.", "completed", "Yes", _al(E.ACTIVITY_STATUSES), "Must be in allowed list; only forward transitions", "Backend", "Internal", "Completion, failure, abandonment rates.", "C1/C3"),
    ("task_activity", "validation_status", "enum", "Result of completion validation.", "passed", "Yes", _al(E.VALIDATION_STATUSES), "'passed' only with activity_status = completed", "Backend", "Internal", "Validation pass rate.", "C1"),
    ("task_activity", "failure_category", "enum", "Proposed failure classification. Not an internal error code.", "tracking_failed", "Conditional", _al(E.FAILURE_CATEGORIES), "Required when activity_status in (failed, abandoned)", "Backend", "Internal", "Failure analysis.", "C2 proposed classification"),
    ("task_activity", "tracking_source", "string", "Who reported the completion: 'veloop' or a registered partner code.", "veloop", "Yes", "", "'veloop' or a value in the partner register", "Backend", "Internal", "Third-party dependency analysis (C4).", "C4"),
    ("task_activity", "external_reference_id", "string", "Partner's own transaction reference for the completion (postback ID).", "pb_8f2c1", "Conditional", "", "Required for external_partner tasks; unique per partner", "Partner callback", "Restricted", "Reconciles VELOOP records with partner reports; dedups partner retries.", "C4"),
    ("task_activity", "reward_amount", "integer", "Expected reward amount for the attempt at the time of start.", "5", "Conditional", "", ">= 0", "Backend", "Internal", "Expected vs credited reward.", "C1"),
    ("task_activity", "reward_unit", "enum", "Unit of reward_amount.", "VE", "Conditional", _al(E.REWARD_UNITS), "Required when reward_amount present", "Backend", "Internal", "Reward analysis.", "C1"),

    # ---------------------------------------------------------------- rewards
    ("rewards", "reward_id", "string", "Identifier of one reward decision (pending, credited, reversed, corrected).", "VLRWD0000001", "Yes", "", ID_VALID, "Backend (reward service)", "Internal", "Reward-level analysis.", "C3"),
    ("rewards", "user_id", "string", "User receiving the reward.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key.", "C3"),
    ("rewards", "source_type", "enum", "What generated the reward.", "task", "Yes", _al(E.REWARD_SOURCE_TYPES), "Must be in allowed list", "Backend", "Internal", "Reward by source.", "C3"),
    ("rewards", "source_id", "string", "Identifier of the generating record (activity_id, event_id, referral_id...).", "VLACT0000001", "Yes", "", "Must resolve in the table implied by source_type", "Backend", "Internal", "Activity-to-reward reconciliation.", "C3"),
    ("rewards", "feature", "enum", "Feature credited for the reward.", "watch_ads", "Yes", _al(E.FEATURES), "Must be in allowed list", "Backend", "Internal", "Reward activity by feature.", "C3"),
    ("rewards", "amount", "integer", "Amount originally granted or expected.", "5", "Yes", "", "> 0", "Backend", "Internal", "Reward volume.", "C3"),
    ("rewards", "final_amount", "integer", "Amount that stands after corrections or reversal (0 if reversed).", "5", "Yes", "", ">= 0; = 0 when reward_status = reversed", "Backend", "Internal", "Net reward volume.", "C3"),
    ("rewards", "unit", "enum", "Unit of the reward.", "VE", "Yes", _al(E.REWARD_UNITS), "Must be in allowed list", "Backend", "Internal", "Volume by unit.", "Official currencies"),
    ("rewards", "reward_status", "enum", "Current reward state. Distinguishes 'activity occurred' from 'reward actually credited'.", "credited", "Yes", _al(E.REWARD_STATUSES), "Allowed transitions: pending->credited|rejected; credited->reversed|corrected", "Backend", "Internal", "Credited vs pending vs reversed.", "C3"),
    ("rewards", "created_at_utc", "timestamp", "When the reward record was created.", "2026-06-10T04:06:15Z", "Yes", "", TS_VALID, "Backend", "Internal", "Reward timing.", "C3"),
    ("rewards", "credited_at_utc", "timestamp", "When the reward was credited to the user.", "2026-06-10T04:20:01Z", "Conditional", "", TS_VALID + "; >= created_at_utc", "Backend", "Internal", "Activity-to-credit lag.", "C3"),
    ("rewards", "reversed_at_utc", "timestamp", "When a credited reward was reversed.", "2026-06-12T08:00:00Z", "Conditional", "", TS_VALID + "; >= credited_at_utc", "Backend", "Internal", "Reversal timing.", "C3"),
    ("rewards", "reversal_reason_category", "enum", "Reason category for reversal or correction. Not a fraud threshold.", "invalid_activity", "Conditional", _al(E.REVERSAL_REASONS), "Required when status in (reversed, corrected)", "Backend", "Restricted", "Reversal analysis.", "Official pages list these reason types"),
    ("rewards", "wallet_transaction_id", "string", "Wallet transaction created by crediting this reward (spendable units only).", "VLTXN0000001", "Conditional", "", "Required when credited in a wallet unit; must exist in wallet_transactions", "Backend", "Internal", "Reward-to-ledger reconciliation.", "D1"),
    ("rewards", "idempotency_key", "string", "Key that guarantees one reward per source event even if the request is retried.", "task:VLACT0000001", "Yes", "", "Unique; format <source_type>:<source_id>", "Backend", "Internal", "Prevents duplicate credits.", "Handoff dedup rule"),

    # ---------------------------------------------------------------- wallet_transactions
    ("wallet_transactions", "transaction_id", "string", "Identifier of one ledger movement. Never reused.", "VLTXN0000001", "Yes", "", ID_VALID, "Backend (wallet service)", "Internal", "Ledger deduplication and reconciliation.", "D1 (Critical, see backlog)"),
    ("wallet_transactions", "user_id", "string", "Wallet owner.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key.", "D1"),
    ("wallet_transactions", "transaction_type", "enum", "Business type of the movement.", "reward_credit", "Yes", _al(E.TRANSACTION_TYPES), "Must be in allowed list; exchange types Proposed", "Backend", "Internal", "Volume by type.", "D1"),
    ("wallet_transactions", "direction", "enum", "Whether the balance goes up (credit) or down (debit).", "credit", "Yes", _al(E.DIRECTIONS), "Must agree with transaction_type", "Backend", "Internal", "Net balance computation.", "D1"),
    ("wallet_transactions", "amount", "integer", "Absolute amount moved. Sign is carried by direction.", "5", "Yes", "", "> 0", "Backend", "Internal", "Credit and debit volume.", "D1"),
    ("wallet_transactions", "unit", "enum", "Wallet unit moved.", "VE", "Yes", _al(E.WALLET_UNITS), "Must be in allowed list", "Backend", "Internal", "Volume by unit.", "D1"),
    ("wallet_transactions", "transaction_status", "enum", "Current state of the movement.", "completed", "Yes", _al(E.TRANSACTION_STATUSES), "pending->completed|failed; completed->reversed", "Backend", "Internal", "Pending and reversed ledger value.", "D1"),
    ("wallet_transactions", "reference_type", "enum", "Kind of business record that caused the movement.", "reward", "Yes", _al(E.REFERENCE_TYPES), "Must be in allowed list", "Backend", "Internal", "Traceability.", "D1"),
    ("wallet_transactions", "reference_id", "string", "Identifier of the causing record (reward_id, withdrawal_id...).", "VLRWD0000001", "Conditional", "", "Must resolve in the table implied by reference_type", "Backend", "Internal", "Traceability.", "D1"),
    ("wallet_transactions", "related_transaction_id", "string", "Original transaction that this one reverses, corrects or pairs with.", "VLTXN0000001", "Conditional", "", "Required for reversal, adjustment, refund, exchange_credit; must exist", "Backend", "Internal", "Reversal/correction relationship.", "D1"),
    ("wallet_transactions", "created_at_utc", "timestamp", "When the movement was recorded.", "2026-06-10T04:20:01Z", "Yes", "", TS_VALID, "Backend", "Internal", "Timing.", "D1"),
    ("wallet_transactions", "completed_at_utc", "timestamp", "When the movement became final.", "2026-06-10T04:20:01Z", "Conditional", "", TS_VALID + "; >= created_at_utc", "Backend", "Internal", "Settlement lag.", "D1"),
    ("wallet_transactions", "balance_after", "integer", "Balance of this unit after the movement.", "125", "No", "", ">= 0 unless a documented correction", "Backend", "Restricted", "Balance reconciliation without recomputation.", "Proposed"),
    ("wallet_transactions", "idempotency_key", "string", "Key that prevents the same business action creating two ledger rows.", "reward:VLRWD0000001", "Yes", "", "Unique", "Backend", "Internal", "Duplicate transaction prevention.", "L: duplicate transaction rule"),

    # ---------------------------------------------------------------- withdrawals
    ("withdrawals", "withdrawal_id", "string", "Identifier of one withdrawal/redemption request.", "VLWDR000001", "Yes", "", ID_VALID, "Backend (payout service)", "Internal", "Withdrawal lifecycle analysis.", "D2"),
    ("withdrawals", "user_id", "string", "Requesting user.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key.", "D2"),
    ("withdrawals", "amount_inr", "decimal", "Requested payout value in Indian rupees.", "20.00", "Yes", "", ">= published minimum (Rs. 10 as of 2026-10-01)", "Backend", "Internal", "Withdrawal volume.", "Official: minimum Rs. 10"),
    ("withdrawals", "ve_debited", "integer", "VEs debited from the wallet for the request.", "40", "Yes", "", "> 0; equals linked redemption_debit amount", "Backend", "Internal", "Ledger reconciliation; conversion audit.", "Rate To Be Verified (A-010)"),
    ("withdrawals", "payout_method", "enum", "Requested payout method.", "UPI", "Yes", _al(E.PAYOUT_METHODS), "Must be in allowed list", "Backend", "Internal", "Method distribution.", "Official withdrawal page"),
    ("withdrawals", "withdrawal_status", "enum", "Current lifecycle state.", "completed", "Yes", _al(E.WITHDRAWAL_STATUSES), "requested->processing->completed|rejected; completed->reversed", "Backend", "Internal", "Status KPIs.", "D2"),
    ("withdrawals", "requested_at_utc", "timestamp", "When the user submitted the request.", "2026-07-01T10:00:00Z", "Yes", "", TS_VALID, "Backend", "Internal", "Request volume, processing time start.", "D2"),
    ("withdrawals", "processing_at_utc", "timestamp", "When review/processing started.", "2026-07-01T11:00:00Z", "Conditional", "", TS_VALID + "; >= requested_at_utc", "Backend", "Internal", "Queue wait time.", "D2"),
    ("withdrawals", "final_at_utc", "timestamp", "When the request reached completed, rejected or reversed.", "2026-07-02T09:00:00Z", "Conditional", "", TS_VALID + "; >= processing_at_utc", "Backend", "Internal", "Processing time.", "D2"),
    ("withdrawals", "reason_category", "enum", "Reason category for rejection or reversal.", "payout_details_invalid", "Conditional", _al(E.WITHDRAWAL_REASONS), "Required when status in (rejected, reversed)", "Backend", "Restricted", "Rejection analysis.", "Official withdrawal pages"),
    ("withdrawals", "review_type", "enum", "Whether the request went through system-only or manual review.", "manual", "No", _al(E.REVIEW_TYPES), "Must be in allowed list", "Backend", "Internal", "Explains processing time.", "Official verification page"),
    ("withdrawals", "debit_transaction_id", "string", "Wallet redemption_debit created for this request.", "VLTXN0000900", "Yes", "", "Must exist in wallet_transactions", "Backend", "Internal", "Ledger reconciliation.", "D1/D2"),
    ("withdrawals", "payout_reference_id", "string", "Payout partner's reference for the transfer. Never a UPI ID, account number or card number.", "po_77ab2", "Conditional", "", "Required when completed", "Payout partner", "Restricted", "Reconciliation with payout partner.", "Governance: no payment credentials"),

    # ---------------------------------------------------------------- withdrawal_status_history
    ("withdrawal_status_history", "status_history_id", "string", "Identifier of one withdrawal status transition.", "VLWSH0000001", "Yes", "", ID_VALID, "Backend", "Internal", "Primary key.", "D2"),
    ("withdrawal_status_history", "withdrawal_id", "string", "Withdrawal that changed status.", "VLWDR000001", "Yes", "", "Must exist in withdrawals", "Backend", "Internal", "Join key.", "D2"),
    ("withdrawal_status_history", "from_status", "enum", "Status before the transition (blank for creation).", "requested", "Conditional", _al(E.WITHDRAWAL_STATUSES), "Blank only for the first row", "Backend", "Internal", "Transition audit.", "D2"),
    ("withdrawal_status_history", "to_status", "enum", "Status after the transition.", "processing", "Yes", _al(E.WITHDRAWAL_STATUSES), "Must be an allowed transition", "Backend", "Internal", "Impossible-transition detection.", "D2"),
    ("withdrawal_status_history", "changed_at_utc", "timestamp", "When the transition happened.", "2026-07-01T11:00:00Z", "Yes", "", TS_VALID + "; non-decreasing per withdrawal", "Backend", "Internal", "Stage durations.", "D2"),

    # ---------------------------------------------------------------- referrals
    ("referrals", "referral_id", "string", "Identifier of one referral relationship.", "VLREF000001", "Yes", "", ID_VALID, "Backend (referral service)", "Internal", "Referral funnel.", "E1"),
    ("referrals", "referrer_user_id", "string", "User who referred.", "VLUSR000010", "Yes", "", "Must exist in users", "Backend", "Internal", "Referrer analysis.", "E1"),
    ("referrals", "referred_user_id", "string", "User who registered through the referral. Blank until registration.", "VLUSR000123", "Conditional", "", "Must exist in users; must differ from referrer_user_id", "Backend", "Internal", "Links to referred user's activity.", "E1"),
    ("referrals", "referral_code", "string", "Referrer's code used. Codes are public share codes, not secrets.", "VL850800", "Yes", "", "Must belong to referrer_user_id", "Backend", "Internal", "Attribution.", "Supplied referral_code"),
    ("referrals", "referral_channel", "enum", "Channel used to share the invite, when known.", "whatsapp", "No", _al(E.REFERRAL_CHANNELS), "Must be in allowed list", "Frontend share action", "Internal", "Channel effectiveness.", "Proposed"),
    ("referrals", "referral_status", "enum", "Furthest stage reached. Registration alone is NOT conversion.", "converted", "Yes", _al(E.REFERRAL_STATUSES), "created->registered->activated->converted; ->rejected|expired", "Backend", "Internal", "Funnel KPIs.", "Official: reward only after first eligible activity + validation"),
    ("referrals", "created_at_utc", "timestamp", "When the referral record was created.", "2026-06-01T10:00:00Z", "Yes", "", TS_VALID, "Backend", "Internal", "Referrals created.", "E1"),
    ("referrals", "registered_at_utc", "timestamp", "When the referred user registered.", "2026-06-02T10:00:00Z", "Conditional", "", TS_VALID + "; >= created_at_utc", "Backend", "Internal", "Referral registrations.", "E1"),
    ("referrals", "activated_at_utc", "timestamp", "When the referred user completed the first eligible activity.", "2026-06-02T12:00:00Z", "Conditional", "", TS_VALID + "; >= registered_at_utc", "Backend", "Internal", "Activations.", "E1"),
    ("referrals", "converted_at_utc", "timestamp", "When the referral passed validation and the referral reward was approved.", "2026-06-03T12:00:00Z", "Conditional", "", TS_VALID + "; >= activated_at_utc", "Backend", "Internal", "Conversions.", "E1"),
    ("referrals", "rejection_reason_category", "enum", "Why a referral was rejected.", "verification_failed", "Conditional", _al(E.REFERRAL_REJECTION_REASONS), "Required when status = rejected", "Backend", "Restricted", "Rejection analysis.", "Official referral page"),
    ("referrals", "reward_id", "string", "Referral reward issued on conversion.", "VLRWD0000999", "Conditional", "", "Required when converted; must exist in rewards", "Backend", "Internal", "Referral cost.", "E1"),

    # ---------------------------------------------------------------- missions / badges
    ("missions", "mission_id", "string", "Identifier of a configured mission.", "VLMSN0003", "Yes", "", ID_VALID, "Backend", "Internal", "Mission analysis.", "Official Missions page"),
    ("missions", "mission_type", "string", "Mission category (daily activity, referral, ads...).", "daily_activity", "Yes", "", "snake_case from mission config", "Backend", "Internal", "Mission mix.", "Official Missions page"),
    ("mission_progress", "mission_progress_id", "string", "One user's progress record on one mission.", "VLMPR0000001", "Yes", "", ID_VALID, "Backend", "Internal", "Primary key.", "Proposed"),
    ("mission_progress", "user_id", "string", "User working on the mission.", "VLUSR000001", "Yes", "", "Must exist in users", "Backend", "Internal", "Join key (users M:N missions).", "Proposed"),
    ("mission_progress", "mission_id", "string", "Mission being progressed.", "VLMSN0003", "Yes", "", "Must exist in missions", "Backend", "Internal", "Join key.", "Proposed"),
    ("mission_progress", "mission_status", "enum", "User's state on the mission.", "completed", "Yes", _al(E.MISSION_STATUSES), "Must be in allowed list", "Backend", "Internal", "Mission completion rate.", "Proposed"),
    ("mission_progress", "started_at_utc", "timestamp", "When the user started the mission.", "2026-07-01T05:00:00Z", "Yes", "", TS_VALID, "Backend", "Internal", "Mission timing.", "Proposed"),
    ("mission_progress", "completed_at_utc", "timestamp", "When all mission conditions were met.", "2026-07-01T09:00:00Z", "Conditional", "", TS_VALID + "; >= started_at_utc", "Backend", "Internal", "Time-to-complete.", "Proposed"),
    ("badges", "badge_id", "string", "Identifier of a configured badge.", "VLBDG0002", "Yes", "", ID_VALID, "Backend", "Internal", "Badge analysis.", "Official Badges page"),
    ("badges", "badge_type", "enum", "Whether the badge carries a reward or is recognition only.", "recognition_only", "Yes", _al(E.BADGE_TYPES), "Must be in allowed list", "Backend", "Internal", "Separates reward cost from recognition.", "Official Missions and Badges page"),
    ("user_badges", "user_id", "string", "Badge holder. Part of the composite primary key.", "VLUSR000001", "Yes", "", "Must exist in users; (user_id, badge_id) unique", "Backend", "Internal", "Join key (users M:N badges).", "Proposed"),
    ("user_badges", "badge_id", "string", "Badge earned. Part of the composite primary key.", "VLBDG0002", "Yes", "", "Must exist in badges", "Backend", "Internal", "Join key.", "Proposed"),
    ("user_badges", "earned_at_utc", "timestamp", "When the user earned the badge.", "2026-07-03T09:00:00Z", "Yes", "", TS_VALID, "Backend", "Internal", "Badge timing.", "Proposed"),

    # ---------------------------------------------------------------- support and content
    ("support_tickets", "ticket_id", "string", "Identifier of one support request.", "VLTKT000001", "Yes", "", ID_VALID, "Support tool", "Internal", "Support volume.", "I support KPIs"),
    ("support_tickets", "user_id", "string", "User who raised the request, if known.", "VLUSR000001", "Conditional", "", "Must exist in users when present", "Support tool", "Internal", "Join to user context.", "I"),
    ("support_tickets", "issue_category", "enum", "Agent-assigned issue category.", "withdrawal", "Yes", _al(E.ISSUE_CATEGORIES), "Must be in allowed list", "Support tool", "Internal", "Issue category KPI.", "Official help center 'most common issues'"),
    ("support_tickets", "ticket_status", "enum", "Ticket state.", "resolved", "Yes", _al(E.TICKET_STATUSES), "Must be in allowed list", "Support tool", "Internal", "Backlog.", "Proposed"),
    ("support_tickets", "created_at_utc", "timestamp", "When the request was received.", "2026-07-04T08:00:00Z", "Yes", "", TS_VALID, "Support tool", "Internal", "Volume over time.", "I"),
    ("support_tickets", "first_response_at_utc", "timestamp", "First support reply.", "2026-07-05T08:00:00Z", "Conditional", "", TS_VALID + "; >= created_at_utc", "Support tool", "Internal", "Response time vs published 24-72 h.", "Official reply time"),
    ("support_tickets", "resolved_at_utc", "timestamp", "When the ticket was resolved.", "2026-07-06T08:00:00Z", "Conditional", "", TS_VALID + "; >= created_at_utc", "Support tool", "Internal", "Resolution time.", "I"),
    ("support_tickets", "related_entity_type", "enum", "Business object the ticket is about.", "withdrawal", "No", "withdrawal, reward, referral, account, other", "Must be in allowed list", "Support tool", "Internal", "Links issues to product areas.", "Proposed"),
    ("support_tickets", "related_entity_id", "string", "ID of that object (withdrawal_id, reward_id...).", "VLWDR000001", "No", "", "Must resolve when present", "Support tool", "Internal", "Root-cause analysis.", "Proposed"),
    ("content", "content_id", "string", "Identifier of a help-center article.", "hc_withdrawals_how_withdrawals_work", "Yes", "", ID_VALID, "CMS / site", "Public", "Help-center engagement.", "Official help-center routes"),
    ("content", "content_category", "enum", "Help-center category.", "withdrawals", "Yes", _al(E.CONTENT_CATEGORIES), "Must be in allowed list", "CMS / site", "Public", "Engagement by topic.", "Official help-center categories"),
    ("content", "content_last_updated_date", "date", "Last updated date shown on the article.", "2026-05-23", "No", "", "YYYY-MM-DD", "CMS / site", "Public", "Content freshness.", "Official pages show 'Last updated'"),
]

FIELDS = [dict(zip(["entity", "field_name", "data_type", "definition", "example", "required",
                    "allowed_values", "validation", "source", "sensitivity", "analytical_use", "basis"], row))
          for row in F]
for f in FIELDS:
    f["status"] = "Proposed"

# Fields that exist only on link tables or that reuse a field defined elsewhere (FK columns).
# They are documented in the logical model, not repeated here, to avoid padding the count.
