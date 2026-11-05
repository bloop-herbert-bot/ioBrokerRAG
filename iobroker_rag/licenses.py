"""License policy: which SPDX ids may be indexed. The policy table lives in sources.json."""
from __future__ import annotations

import fnmatch
import re

DEFAULT_POLICY = {
    "allow": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense", "CC0-1.0", "CC-BY-4.0"],
    "review": ["GPL-*", "LGPL-*", "AGPL-*", "MPL-2.0", "EPL-*", "CC-BY-SA-*"],
    "deny": ["NOASSERTION", "none", "CC-BY-NC-*", "CC-BY-ND-*", "proprietary"],
}
UNKNOWN = "none"


CREATIVE_COMMONS = re.compile(r"^cc[ -]?by((?:[ -](?:nc|sa|nd))*)(?:[ -](\d\.\d))?$", re.I)
TEXTS = [  # standard clauses in a LICENSE file GitHub could not identify, e.g. because of extra copyright lines
    ("MIT", re.compile(r"permission is hereby granted, free of charge, to any person obtaining a copy", re.I)),
    ("Apache-2.0", re.compile(r"apache license,?\s+version 2\.0", re.I)),
    ("GPL-3.0", re.compile(r"gnu general public license(?:,)?\s+(?:as published by the free software foundation[,;]?\s+(?:either\s+)?)?version 3", re.I)),
    ("GPL-2.0", re.compile(r"gnu general public license(?:,)?\s+(?:as published by the free software foundation[,;]?\s+(?:either\s+)?)?version 2", re.I)),
    ("LGPL-3.0", re.compile(r"gnu lesser general public license.{0,80}version 3", re.I | re.S)),
    ("AGPL-3.0", re.compile(r"gnu affero general public license.{0,80}version 3", re.I | re.S)),
    ("BSD-3-Clause", re.compile(r"neither the name of .{0,120} nor the names of its contributors", re.I | re.S)),
    ("BSD-2-Clause", re.compile(r"redistributions in binary form must reproduce the above copyright", re.I)),
    ("ISC", re.compile(r"permission to use, copy, modify, and/or distribute this software for any purpose", re.I)),
]


def normalize(spdx: str | None) -> str:
    """GitHub returns NOASSERTION for custom texts and null for no file; io-package often writes 'Apache 2.0'."""
    if not spdx:
        return UNKNOWN
    s = spdx.strip()
    aliases = {"apache 2.0": "Apache-2.0", "apache-2": "Apache-2.0", "apache 2": "Apache-2.0", "apache": "Apache-2.0",
               "apache license 2.0": "Apache-2.0", "mit license": "MIT", "bsd": "BSD-3-Clause", "gplv3": "GPL-3.0",
               "gplv2": "GPL-2.0", "cc0": "CC0-1.0", "isc license": "ISC"}
    if s.lower() in aliases:
        return aliases[s.lower()]
    m = CREATIVE_COMMONS.match(s)
    if m:
        parts = "".join(f"-{p.upper()}" for p in re.split(r"[ -]", m.group(1)) if p)
        return f"CC-BY{parts}" + (f"-{m.group(2)}" if m.group(2) else "")
    return re.sub(r"-(only|or-later)$", "", s, flags=re.I)


def detect(text: str | None) -> str:
    """SPDX id from the standard clauses of a license text; 'none' if no known clause is found."""
    if not text:
        return UNKNOWN
    for spdx, pattern in TEXTS:
        if pattern.search(text):
            return spdx
    return UNKNOWN


def classify(spdx: str | None, policy: dict | None = None) -> str:
    """'allow', 'review' or 'deny'. Unknown ids are denied, the policy decides nothing by accident."""
    policy = policy or DEFAULT_POLICY
    s = normalize(spdx)
    for verdict in ("deny", "allow", "review"):
        if any(fnmatch.fnmatchcase(s, pattern) for pattern in policy.get(verdict, [])):
            return verdict
    return "deny"


def decide(github_spdx: str | None, package_license: str | None, policy: dict | None = None,
           license_text: str | None = None) -> tuple[str, str, bool]:
    """(license to record, verdict, mismatch). GitHub's detection wins; io-package.json is the author's claim.
    For a LICENSE file GitHub cannot identify (NOASSERTION, usually extra copyright lines) the standard clauses
    of the text decide; if they agree with the claim the entry counts as identified."""
    g, p = normalize(github_spdx), normalize(package_license)
    if g == "NOASSERTION":
        found = detect(license_text)
        if found != UNKNOWN and (p == UNKNOWN or found == p):
            g = found
        elif p != UNKNOWN:
            verdict = classify(p, policy)      # text unknown or contradicting the claim: a human looks
            return p, ("deny" if verdict == "deny" else "review"), True
    recorded = g if g != UNKNOWN else p
    mismatch = g != UNKNOWN and p != UNKNOWN and g != p
    verdict = classify(recorded, policy)
    if mismatch and classify(p, policy) != verdict:
        verdict = "review"     # the two sources disagree about the category, a human decides
    return recorded, verdict, mismatch
