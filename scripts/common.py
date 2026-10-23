"""Shared constants and helpers for the VELOOP Task 01 analytics pipeline."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_XLSX = ROOT / "data" / "raw" / "VELoop_Rewards_Data_01.xlsx"
SIM_DIR = ROOT / "data" / "simulated"
OUT_DIR = ROOT / "deliverables"
BUILD_DIR = ROOT / "build"

SEED = 20260915

# Mandatory label from Task 01, section 28, for every additional dataset.
SIM_LABEL = "SIMULATED DATA — CREATED FOR ANALYTICAL TESTING"
# Label used by the supplied workbook (Users_Messy_Audit.data_environment).
SUPPLIED_LABEL = "SIMULATED — NOT ACTUAL VELOOP DATA"

# Supplied README_Data_Status: period 01 Apr 2026 to 15 Sep 2026.
# Supplied timestamps carry no timezone. Assumption A-004: they are IST (Asia/Kolkata),
# because the official Daily Check-In page defines the claim window in IST.
IST = "Asia/Kolkata"
PERIOD_START_IST = pd.Timestamp("2026-04-01 00:00:00", tz=IST)
PERIOD_END_IST = pd.Timestamp("2026-09-15 23:59:59", tz=IST)
PERIOD_START_UTC = PERIOD_START_IST.tz_convert("UTC")
PERIOD_END_UTC = PERIOD_END_IST.tz_convert("UTC")

# Fictional conversion used ONLY to make simulated withdrawals internally consistent.
# The real VE to INR rate is unknown (Assumption A-010, To Be Verified).
SIM_VE_PER_INR = 2

PAYOUT_METHODS = ["UPI", "PayPal", "Amazon Gift Card", "Google Play Gift Card"]  # official help center, 2026-10-01


def load_supplied():
    """Read every sheet of the supplied workbook as strings, blanks kept as ''."""
    return pd.read_excel(RAW_XLSX, sheet_name=None, dtype=str, keep_default_na=False)


def ist_naive_to_utc(series):
    """Parse supplied naive datetimes (assumed IST) to UTC. Unparseable values become NaT."""
    parsed = pd.to_datetime(series.replace("", None), errors="coerce", format="%Y-%m-%d %H:%M:%S")
    return parsed.dt.tz_localize(IST).dt.tz_convert("UTC")


def iso(ts):
    """Format a UTC timestamp series as ISO 8601 with Z, keeping blanks for NaT."""
    return ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
