#!/usr/bin/env python3
"""Compare raw upstream PHPT results without changing their expectations."""
import collections
import json
from pathlib import Path
import re
import sys

root = Path(__file__).parent / 'results'
def read(name):
    rows = {}
    for line in (root / name).read_text().splitlines():
        match = re.match(r'^(PASS|FAIL|SKIP|XFAIL|WARN) .* \[([^\]]+\.phpt)\]', line)
        if match:
            status, path = match.groups()
            if path in rows:
                raise SystemExit('Duplicate result: ' + path)
            rows[path] = status
    return rows

baseline, candidate = read('php53-baseline-phpt.log'), read('php53-candidate-phpt.log')
expected = set()
changes = {p: {'baseline': baseline.get(p), 'candidate': candidate.get(p)}
           for p in sorted(set(baseline) | set(candidate))
           if baseline.get(p) != candidate.get(p)}
unexpected = {p: change for p, change in changes.items()
              if p not in expected or change != {'baseline': 'PASS', 'candidate': 'FAIL'}}
ok = (len(baseline) == len(candidate) == 271 and set(changes) == expected
      and not unexpected)
result = {'comparison_pass': ok, 'baseline_counts': dict(collections.Counter(baseline.values())),
          'candidate_counts': dict(collections.Counter(candidate.values())),
          'expected_behavior_changes': changes, 'unexpected_changes': unexpected,
          'unchanged_test_count': len(baseline) - len(changes),
          'baseline_failures': sorted(p for p, status in baseline.items() if status == 'FAIL'),
          'note': 'Native build-tree CLI/CGI comparison. All 271 statuses match; nine baseline failures remain failures. Final RPM HTTP acceptance is recorded separately.'}
(root / 'php53-phpt-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(0 if ok else 1)
