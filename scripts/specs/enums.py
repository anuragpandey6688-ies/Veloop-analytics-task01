"""Controlled vocabularies shared by the dictionary, event catalogue, simulated data and validator.

Every list here is PROPOSED unless a comment cites an official source. Values marked
"official" were published on velooprewards.in (checked 2026-10-01); their implementation in
VELOOP systems is still To Be Verified.
"""

FEATURES = [
    # earning
    "watch_ads", "surveys", "app_tasks", "captcha", "tap_earn", "earning_session", "games",
    "follow_earn", "tasks",
    # engagement
    "daily_rewards", "spin", "missions", "badges", "level_dashboard", "leaderboard", "promo_codes",
    # money movement
    "wallet", "exchange", "withdrawals", "referrals",
    # account and support
    "account", "onboarding", "home", "help_center", "support",
]
PLATFORMS = ["web", "android", "ios"]
EVENT_SOURCES = ["client", "server"]
TASK_TYPES = ["watch_ad", "survey", "app_task", "captcha", "tap_earn", "earning_session", "game", "social_follow"]
FULFILMENT_SOURCES = ["veloop_internal", "external_partner"]
ACTIVITY_STATUSES = ["in_progress", "pending_validation", "completed", "failed", "abandoned"]
VALIDATION_STATUSES = ["pending", "passed", "failed", "not_reached"]
FAILURE_CATEGORIES = ["task_failed", "tracking_failed", "validation_failed", "user_abandoned", "system_error"]
FAILURE_STAGES = ["start", "in_task", "tracking", "validation"]
REWARD_UNITS = ["VE", "GEM", "XP", "TOKEN", "SPIN"]  # official currency names
WALLET_UNITS = ["VE", "GEM", "TOKEN", "SPIN"]
REWARD_SOURCE_TYPES = ["task", "daily_reward", "streak", "spin", "mission", "badge", "referral", "promo_code",
                       "leaderboard", "manual_adjustment"]
REWARD_STATUSES = ["pending", "credited", "rejected", "reversed", "corrected"]
REVERSAL_REASONS = ["invalid_activity", "tracking_dispute", "duplicate_credit", "technical_correction",
                    "policy_violation"]
TRANSACTION_TYPES = ["reward_credit", "reversal", "adjustment", "exchange_debit", "exchange_credit",
                     "redemption_debit", "redemption_refund"]
DIRECTIONS = ["credit", "debit"]
TRANSACTION_STATUSES = ["pending", "completed", "failed", "reversed"]
REFERENCE_TYPES = ["reward", "withdrawal", "exchange", "manual_adjustment"]
WITHDRAWAL_STATUSES = ["requested", "processing", "completed", "rejected", "reversed"]
WITHDRAWAL_REASONS = ["verification_failed", "payout_details_invalid", "policy_violation", "payout_partner_failure"]
PAYOUT_METHODS = ["UPI", "PayPal", "Amazon Gift Card", "Google Play Gift Card"]  # official
REVIEW_TYPES = ["system", "manual"]  # official: "Manual and system-based validation"
REFERRAL_STATUSES = ["created", "registered", "activated", "converted", "rejected", "expired"]
REFERRAL_CHANNELS = ["whatsapp", "telegram", "copy_link", "other"]
REFERRAL_REJECTION_REASONS = ["verification_failed", "policy_violation"]
ACCOUNT_STATUSES = ["pending_verification", "active", "inactive", "suspended", "closed"]
STATUS_CHANGE_ACTORS = ["system", "admin", "user"]
STATUS_CHANGE_REASONS = ["email_verified", "inactivity_rule", "policy_enforcement", "user_request",
                         "appeal_upheld", "other"]
REGISTRATION_METHODS = ["web_registration", "google_sign_in"]  # supplied data + privacy policy (Google login)
ACQUISITION_SOURCES = ["organic_search", "direct", "social_media", "referral", "whatsapp", "telegram", "other"]
EMAIL_VERIFICATION_STATUSES = ["pending", "verified"]
ONBOARDING_STATUSES = ["not_started", "started", "completed"]
CONSENT_STATUSES = ["pending", "accepted", "withdrawn"]
DEVICE_TYPES = ["mobile", "tablet", "desktop"]
LOGIN_METHODS = ["password", "google_sign_in"]
LOGOUT_TYPES = ["user_initiated", "session_expired", "forced"]
STREAK_ACTIONS = ["incremented", "reset", "started"]
SPIN_OUTCOMES = ["reward", "no_reward", "interrupted"]
BADGE_TYPES = ["reward", "recognition_only"]  # official Missions and Badges page
MISSION_STATUSES = ["started", "completed", "expired"]
TICKET_STATUSES = ["open", "pending_user", "resolved", "closed"]
ISSUE_CATEGORIES = ["withdrawal", "missing_reward", "account_access", "account_restriction", "referral",
                    "technical", "privacy_request", "other"]
CONTENT_CATEGORIES = ["getting_started", "earning", "wallet", "withdrawals", "safety", "future_features", "legal"]
TASK_CONFIG_STATUSES = ["active", "paused", "retired"]
