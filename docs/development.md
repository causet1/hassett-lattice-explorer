# Development checks and reproducible releases

The engine requires Python 3.10+ and no third-party Python packages. Install Node
22 or 24 for the JavaScript checks. CI uses Python 3.10 and 3.14 with Node 24.

From the repository root:

```sh
python scripts/validate_release.py
python scripts/audit_classification.py web/catalogue.json \
  --report build/validation/classification-audit.json
```

The first command runs the Python suite, independent certificate checks, five
published fixtures, and the actual application JavaScript in a simulated DOM.
Python integration tests generate a small catalogue through 44, interrupt and
resume it, verify and package it, build static assets, and test corruption
rejection and recovery. When Node is available, those generated assets also
exercise the hosted-data loader. The second command separately re-enumerates
all saturation origins and checks nonisometry in the embedded 66-pair catalogue.

Fresh reports are written under ignored `build/validation/`, with the actual
validation time, Git revision and working-tree state when available, and SHA-256
fingerprints of the tested implementation, tests, workflows, and web assets.
`--output-dir` selects another report directory. Original reports in `docs/`
and `IMPORT-VERIFICATION.md` are historical evidence and are not overwritten.
The JavaScript harness accepts `--report PATH`; legacy `--write-report` now writes
to `build/validation/web_validation.json`.

## Retrieve and verify the published catalogue

On 2026-11-14, source commit `aaedcfaf6273fd4d9f0a4e02b7312bf8dd50c771`
passed 28 Python tests and 208 UI assertions against the downloaded dataset.
The independent classification audit passed for all 66 embedded pairs and 640
origins. GitHub CI also passed on Python 3.10 and 3.14 with Node 24; the local
run used Python 3.12 and Node 22. Tests passed from the extracted Python source
distribution, and the installed wheel CLI worked outside the checkout.

The [fresh full-catalogue report](catalogue-verification-500-2026-11-14.json)
records successful verification of all 13,530 pair files, 1,636,925 component
certificates, 1,698,033 origins, and 3,077,975 independent root-box vectors.
Its pinned index digest matches the original release. This full-data check is
certificate and pair-coverage verification; the independent classification
audit above covers the embedded range only. The original reports remain intact.

```sh
python scripts/download_catalogue.py --output ../hassett-expanded-500
python scripts/verify_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --report build/validation/catalogue-verification-500.json
python scripts/validate_release.py --hosted-data ../hassett-expanded-500
```

The downloader pins the exact index SHA-256 in the committed original
`docs/catalogue-verification-500.json`. It checks every compressed shard's size
and hash, retries transient transport failures, writes atomically, and resumes
by reusing verified local files. The final index is installed only after all
shards pass. A changed index or bad shard fails explicitly. An existing output
with a different index is refused; select a new directory for another release.
`--base-url` selects an HTTPS mirror, and `--verification` selects another trusted
release report. Do not replace the pin merely to silence a checksum mismatch.

Downloads establish byte integrity against the recorded release. The separate
catalogue verifier establishes the documented certificate checks. Retrieval
depends on the existing website remaining available; generation from scratch
remains the independent fallback described in [expanded-catalogue.md](expanded-catalogue.md).
On Python.org macOS installations, install the bundled CA certificates if HTTPS
reports a missing certificate authority; do not disable TLS verification.

## Independent classification audit

`scripts/audit_classification.py` imports no engine code. It uses rational
matrix multiplication to enumerate integral overlattices, rather than the
engine's optimized entrywise congruence formulas. It compares the entire set of
admissible construction origins with the supplied result. It checks pairs of
equal-determinant representatives by an exhaustive three-coordinate vector
search, fixing the distinguished class explicitly, rather than the engine's
binary Schur-form search. Different determinants already rule out isometry.

The audit shares the documented finite parameterization and the independent
certificate checker. It is a second implementation of those classification
steps, not a new proof of the geometric theorems. A passing report applies only
to the specific supplied inputs. It is deliberately slower and intended for
regression-sized inputs, not an automatic audit of the entire catalogue through
500. `--max-work` bounds audit iterations and, separately, root-vector checks;
exhaustion is failure, never partial success.

Regression tests include a missing saturation component that passes ordinary
certificate validation but fails the audit, changed lattice bases, distinct
equal-determinant classes, published cases, and resource exhaustion.

## Package and prepare deployment assets

After the preceding checks:

```sh
python scripts/package_release.py --output build/deliverables \
  --validation-dir build/validation
python scripts/package_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --verification build/validation/catalogue-verification-500.json \
  --output build/deliverables
python scripts/build_hosted_site.py ../hassett-expanded-500 \
  --verification build/validation/catalogue-verification-500.json --output dist \
  --summary-csv build/deliverables/hassett-component-counts-500.csv \
  --source-archive build/deliverables/hassett-lattice-explorer.zip
```

The source ZIP includes problem and algorithm notes, provenance documents,
references, and CI workflows. Supplied reference materials retain their existing
terms as recorded in `references/README.md`. Optional fresh reports are included
under `validation/` only if the validation source fingerprints still match;
adding, changing or removing source files requires revalidation. Historical
reports remain under `docs/`. Both data packaging and site preparation reject
shards that changed after verification. Site preparation writes local assets;
publishing remains a separate operation.

The ordinary CI workflow runs on pushes and pull requests without downloading
the large catalogue. The manual **Verify pinned expanded catalogue** workflow
retrieves and verifies all published files, runs expanded UI checks, packages
source and data, and retains downloadable artifacts for 30 days. These are CI
artifacts, not permanent release hosting. Before a formal release, archive the
verified artifacts durably and associate them with a version tag and checksums.
Real-browser layout, native clipboard and live download checks remain separate
from the simulated-DOM harness.
