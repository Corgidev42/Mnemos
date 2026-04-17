# -*- coding: utf-8 -*-
import json
import os

from mnemos import config
from mnemos.domain import table as table_domain
from mnemos.paths import table_path


def load_table():
    path = table_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return table_domain.sort_table_pairs([tuple(row) for row in data])
        except (json.JSONDecodeError, TypeError):
            pass
    return list(config.TABLE_EMBEDDED)
