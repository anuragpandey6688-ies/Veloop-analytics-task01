"""Download the supplied VELOOP Task 01 workbook from the Google Drive folder given in the brief."""
import subprocess
import sys

from common import RAW_XLSX

FOLDER = "https://drive.google.com/drive/folders/1dNHyeqGMNLPhND4Ty0Sj0Ca8BgftKeS4"
RAW_XLSX.parent.mkdir(parents=True, exist_ok=True)
if RAW_XLSX.exists():
    print("already present:", RAW_XLSX)
else:
    subprocess.run([sys.executable, "-m", "gdown", FOLDER, "-O", str(RAW_XLSX.parent)], check=True)
    print("downloaded to", RAW_XLSX.parent)
