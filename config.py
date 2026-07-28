#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py
Loads settings from environment variables (preferred) or a local config.json.
Never commit real API keys to source control.
"""

import os
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config():
    config = {
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "model": os.environ.get("SCIBOT_MODEL", "gemini-2.0-flash"),
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                file_config = json.load(f)
            for key in config:
                if not config[key] and key in file_config:
                    config[key] = file_config[key]
        except Exception as e:
            print(f"Warning: could not read config.json: {e}")

    return config
