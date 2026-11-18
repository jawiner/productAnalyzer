"""Run the Reelkit Gemini kit's voiceover tool for this project with the WAT root's Gemini key.

The kit (wat-framework/internal/reelkit-gemini-kit) reads its own .env; this wrapper loads the key
from the WAT root .env into the environment first (never printed), then runs the kit tool for
English: --language en with an English faster-whisper model for the word times.

Usage (speech venv):
  C:/Users/97254/wat-framework/.tmp/venv-speech/Scripts/python.exe -X utf8 tools/voiceover.py [kit args]
"""
import os
import runpy
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT_ENV = Path("C:/Users/97254/wat-framework/.env")
KIT_TOOL = Path("C:/Users/97254/wat-framework/internal/reelkit-gemini-kit/tools/reelkit_gemini_voiceover.py")
PROJECT = Path(__file__).resolve().parent.parent

key = dotenv_values(ROOT_ENV).get("GEMINI_API_KEY")
if not key:
    sys.exit("GEMINI_API_KEY is missing from the WAT root .env")
os.environ["GEMINI_API_KEY"] = key

args = sys.argv[1:]
if "--language" not in args:
    args += ["--language", "en"]
if "--asr-model" not in args:
    args += ["--asr-model", "small.en"]
sys.argv = [str(KIT_TOOL), "--project", str(PROJECT), *args]
runpy.run_path(str(KIT_TOOL), run_name="__main__")
