# Website and source provenance

**Existing website:** [Hassett Lattice Explorer](https://hassett-lattice-explorer.causetpatrick.chatgpt.site).

This repository includes the actual source retrieved from the existing site, together with the project ZIP supplied by the user. It preserves the existing website; creating this private GitHub repository does not redeploy the site or change its audience.

## Snapshot

| Item | Value |
|---|---|
| Website title | Hassett Lattice Explorer |
| Retrieved site version | 2 |
| Source release | 1.1.0 |
| Source commit | `954196a7d8eec20105237b34afb831ce275775c6` |
| Site project identifier | `appgprj_6af795a05da881919fd102695f63d249` |
| Import date | 2026-11-13, America/Los_Angeles |
| GitHub repository | Private |

The 33 ordinary project files in the supplied ZIP are byte-for-byte identical to the retrieved site source. The site additionally supplies `.openai/hosting.json`; the ZIP additionally supplies `release-manifest.json`, retained as [references/original-release-manifest.json](references/original-release-manifest.json). The unchanged ZIP is [references/original-source-release.zip](references/original-source-release.zip).

## Included website and implementation

- [web/explorer.html](web/explorer.html): standalone interactive explorer, with the original 66-pair catalogue embedded for offline use.
- [web/catalogue.json](web/catalogue.json): exact embedded catalogue through discriminant 42.
- [web/README.md](web/README.md): interface, data-format, and hosting details.
- [hassett_lattices/](hassett_lattices/): Python algorithm and CLI.
- [scripts/](scripts/): catalogue construction, independent certificate checking, packaging, and website build tools.
- [tests/](tests/): existing Python and JavaScript checks.
- [docs/](docs/): mathematical explanation, implementation notes, bibliography, and retained release reports.

Open `web/explorer.html` in a modern browser for the embedded offline catalogue. To compute another pair and import its JSON into the explorer, run from the repository root:

```sh
python3 -m hassett_lattices intersect 8 26 --output intersection.json
```

## Expanded hosted data

The live site serves a larger generated catalogue through discriminant 500: its index and compressed per-pair data are deployed assets, not files in the retrieved Git source or the supplied source ZIP. This repository contains the standalone 66-pair fallback, the generation tools, the existing verification reports, and the link to the live expanded explorer. It does not contain a full copy of the generated 13,530-pair data directory.

For reproduction and deployment asset construction, use [docs/expanded-catalogue.md](docs/expanded-catalogue.md) and `scripts/build_hosted_site.py`. The original `.openai/hosting.json` identifies the existing site and expects a generated `dist/` directory. A GitHub push alone does not build or deploy that directory.

## Import verification

The source snapshot was retrieved without publishing a new site version. The original code, data, mathematical notes, and license were preserved. Repository-specific additions are the problem brief, algorithm adaptation, this website record, import verification, and the supplied originals in `references/`. The root README adds navigation to those materials.

Local verification and its limitations are recorded in [IMPORT-VERIFICATION.md](IMPORT-VERIFICATION.md). Existing `docs/*validation*.json` and the expanded-catalogue verification report are inherited release records; their presence does not mean the entire expanded catalogue was recomputed during this import.
