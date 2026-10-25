"""Shared Unicode detection and redacted audit logging for tool inspections."""

import os
import re
import sys
from datetime import datetime, timezone

# Glassworm: invisible/bidi control chars that can hide malicious content.
# Built via chr() to avoid embedding actual invisible chars in this source file.
_INVISIBLE_CODEPOINTS = [
    0x061C,  # Arabic Letter Mark
    0x00AD,  # soft hyphen
    *range(0x200B, 0x2010),  # ZWSP, ZWNJ, ZWJ, LRM, RLM
    *range(0x202A, 0x202F),  # LRE, RLE, PDF, LRO, RLO (bidi overrides)
    *range(0x2060, 0x2065),  # word joiner, invisible operators
    *range(0x2066, 0x206A),  # LRI, RLI, FSI, PDI (bidi isolates)
    0xFEFF,  # BOM / ZWNBSP
]
INVISIBLE_CHAR_RE = re.compile('[' + ''.join(chr(cp) for cp in _INVISIBLE_CODEPOINTS) + ']')

_DEFAULT_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'audit.log')


def audit_log(phase: str, tool: str, result: str, detail: str = '') -> None:
    """Append one audit record. No-ops when HOOK_NO_LOG is set or write fails."""
    if os.environ.get('HOOK_NO_LOG'):
        return
    # Keep compatibility with Python versions before 3.11.
    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')  # noqa: UP017
    line = f'{ts} [{phase:<4}] {result:<8} {detail[:120]}\n'
    try:
        log_path = os.path.abspath(os.environ.get('HOOK_LOG_PATH') or _DEFAULT_LOG_FILE)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8', errors='backslashreplace') as f:
            f.write(line)
    except OSError:
        print('[audit_log] write failed: details redacted', file=sys.stderr)
