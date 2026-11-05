# Contributing

- **New source:** add it to `sources.json`. Only public repositories whose license is in the `allow` list of the policy below. `tools/check_sources.py` must pass.
- **Adapter sources:** do not edit `sources.adapters.json` by hand. Run `GITHUB_TOKEN=$(gh auth token) tools/sync_adapters.py` and commit the result; the pull request shows what changed.
- **Test questions:** add them to `eval/questions.jsonl`. Write them yourself. Do not copy forum posts or private data.
- **Code:** run `pytest`, keep changes small, explain the reason in the pull request.
- **Sign-off:** contributions are MIT licensed. Sign your commits with `git commit -s` ([Developer Certificate of Origin](https://developercertificate.org/)).
- **Measure it:** changes to chunking or ranking need the result of `eval/run.py` before and after.

Text from AI services may not be allowed as model training data. Mark such questions in the pull request.

## License policy

Every indexed chunk carries repository, commit and license, and every result shows them. The index is built locally and never distributed; indexed text stays under the license of its source. The policy table in `sources.json` (`license_policy`, SPDX ids, `fnmatch` patterns) decides what gets in:

| Verdict | Licenses | Effect |
|---|---|---|
| `allow` | MIT, Apache-2.0, BSD-2/3-Clause, ISC, 0BSD, Unlicense, CC0-1.0, CC-BY-4.0 | indexed |
| `review` | GPL-*, LGPL-*, AGPL-*, MPL-2.0, EPL-*, CC-BY-SA-* | listed in `sources.adapters.json`, indexed only with `"index_review": true` |
| `deny` | NOASSERTION, no license, CC-BY-NC-*, proprietary, anything not listed | listed under `skipped` with a link, nothing of it is indexed |

Rules the generator applies:
- The license comes from the GitHub API (`license.spdx_id`). `io-package.json` (`common.licenseInformation.license`, older `common.license`) is the author's claim. If both exist and differ, the entry gets `license_claimed`; if they fall into different verdicts, the verdict is `review`.
- A `LICENSE` file GitHub cannot identify (`NOASSERTION`) plus a claim in `io-package.json` is `review`; without a claim it is `deny`.
- Archived repositories are skipped.
- Hand-made entries in `sources.json` must be `allow`; `sources.json` wins over the generated file.

Copyleft documentation (`review`) is only read locally for search when `index_review` is set, nothing is redistributed. The default is off; whoever operates an index decides for their installation.
