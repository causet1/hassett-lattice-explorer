# Repository import verification

Recorded on 2026-11-13 (America/Los_Angeles) while assembling this private repository.

## Source integrity

- Retrieved the existing website's source at commit `954196a7d8eec20105237b34afb831ce275775c6`, matching the source commit recorded for site version 2.
- Compared all 33 project files in the supplied ZIP with the retrieved source: all were byte-for-byte identical.
- Checked all 33 entries in the ZIP's release manifest: every byte length and SHA-256 hash matched.
- Preserved the supplied algorithm PDF, screenshot, and source ZIP unchanged; their hashes are listed in [references/README.md](references/README.md).
- Read all five pages of the supplied algorithm PDF and visually checked the rendered formulas, pseudocode, correctness argument, and example table when preparing [ALGORITHM.md](ALGORITHM.md).

## Checks run during this import

| Command | Observed result |
|---|---|
| `python3 -m unittest discover -s tests -v` | 19 test methods passed, including the five published component-count and determinant fixtures |
| `node tests/test_explorer.cjs` | 192 assertions passed against the actual embedded JavaScript using the existing simulated DOM harness |
| `python3 scripts/verify_certificates.py web/catalogue.json` | 66 pairs, 628 component certificates, and 640 construction origins passed; 986 independent root-box vectors checked |

The observed fixture counts were 5 for $(8,14)$, 8 for $(8,26)$, 10 for $(8,38)$, 6 for $(20,12)$, and 17 for $(20,38)$. The certificate checker has separate linear algebra and root enumeration code and does not import the engine.

## Verification limits

The checks above verify the source import, existing regression tests, browser-script behavior under a simulated DOM, and the bundled catalogue's certificates. They do not independently establish enumeration completeness or all pairwise nonisometry decisions. They do not constitute a new proof of the geometric theorems used by the algorithm, an exhaustive code audit, or a novelty claim.

The full generated catalogue through discriminant 500 was not recomputed or reverified during this import. Its retained reports in `docs/` belong to the original release. The simulated DOM tests do not verify browser layout, native clipboard behavior, or actual live-site downloads. No website source changes were deployed as part of this repository import.
