# Hassett Atlas browser explorer · 1.1.0

Use the [interactive website](https://hassett-lattice-explorer.causetpatrick.chatgpt.site) in a browser. The hosted page downloads a catalogue index and loads the exact certificate for a selected pair on demand. The downloaded `explorer.html` also works directly in a modern browser: its original 66-pair catalogue is embedded, with no server, build step, CDN, external font, or internet connection required for those pairs.

A document preview can suppress JavaScript. In that case, the page shows a clear notice, a link to the interactive website, and the genuine five-component example for C8 ∩ C14. Controls remain disabled until initialization succeeds, so a static preview is not presented as an active application.

## Catalogue scope

The offline catalogue contains every pair of distinct valid discriminants from 8 through 42: 66 pairs in total. On HTTPS, the page checks `./data/catalogue-index.json` for the expanded collection. The displayed bound and pair count come from this index, not from a hardcoded claim about what has been computed.

A complete index must enumerate every pair in its stated discriminant range. A partial index is explicitly labeled incomplete and shows its completed, failed, and pending counts. The viewer validates these counts and the discriminant list before using the index. It also verifies each selected result against its index entry.

The browser explores previously computed results; it does not run the Python lattice algorithm. A pair outside the available entries remains uncomputed in the interface and shows the exact Python/import route. A download failure is distinguished from an unavailable computation. The 66 embedded pairs remain usable while the larger index is loading or unavailable.

The incidence graph displays at most 12 divisor nodes, including the selected pair and a sample spanning the available range. Its caption states how many of the catalogue's divisors are shown. Use the discriminant fields to select any other available pair. Graph positions have no geometric meaning in the 20-dimensional moduli space; an absent edge does not assert an empty geometric intersection.

## What the interface displays

- Exact component Gram matrices and discriminants, normalized mixed-product parameters, extension indices, and all retained construction routes.
- The finite positive-definite parameter scan, with norm-two rejection witnesses and accepted overlattice routes.
- Hassett's arithmetic K3 test for the selected rank-two labels, and the separate whole-lattice K3 criterion for each generic rank-three algebraic lattice.
- A table view, component inspector, matrix copying, local JSON import, and JSON export.

Negative K3-admissibility of a rank-three lattice describes its generic locus; higher-rank specializations can have further admissible markings. No K3 result is presented as an automatic rationality verdict.

## Add or inspect a pair offline

From the repository root:

```sh
python -m hassett_lattices intersect 8 50 --output intersection.json
```

Choose **Import JSON** and select the plain individual result. A catalogue object `{"pairs": [...]}` containing full results is also accepted. The lightweight online index is not a substitute for these full result objects. Imported data remain in your browser; use **Export pair** to retain a result. Imported results and the original 66 pairs take precedence over a remote download for the same pair.

The viewer checks integer Gram matrices, symmetry, stored determinants, and component counts. It does not independently rerun the full lattice algorithm. Incomplete imported results do not display a component count.

## Hosted data layout

Place the index and certificate shards next to the hosted page as follows:

```text
index.html
data/catalogue-index.json
data/pairs/8-50.json.gz
...
```

Index schema 1.1 includes `max_discriminant`, `discriminants`, `expected_pair_count`, `pair_count`, `component_count`, `complete`, `failed_pair_count`, `pending_pair_count`, and a `pairs` array. Each pair entry supplies:

```json
{
  "key": "8-50",
  "d1": 8,
  "d2": 50,
  "component_count": 12,
  "path": "pairs/8-50.json.gz",
  "compression": "gzip",
  "sha256": "SHA-256 of the stored gzip bytes",
  "bytes": 0,
  "uncompressed_sha256": "SHA-256 of the exact plain JSON bytes",
  "uncompressed_bytes": 0
}
```

The values above describe field meanings; the runner supplies the actual hashes and positive byte lengths. Paths must have exactly the relative form `pairs/min-max.json.gz`, or `pairs/min-max.json` for `compression: "none"`. Absolute URLs, parent-directory traversal, query strings, and mismatched pair names are rejected.

The normal gzip path is:

1. Download the selected stored shard and check its byte length and SHA-256 digest.
2. Decompress it with the browser's native `DecompressionStream('gzip')`, enforcing a bound while reading the output.
3. Check the uncompressed byte length, parse the JSON, and validate its pair identity, component count, completeness, and Gram determinants.

If a CDN transparently decodes gzip before the response reaches JavaScript, the page accepts the returned plain bytes only when both their length and `uncompressed_sha256` match the index. This fallback never skips integrity checks.

Modern HTTPS browsers provide the required WebCrypto and stream APIs. A browser missing gzip support shows an explicit error and retains the embedded catalogue and plain JSON imports. Local `file://`, HTTP, and other unsupported modes do not request the online index. The data assets must stay on the same origin as the hosted page.

Selecting another pair cancels the obsolete download and invalidates its request generation. A late response cannot replace the newer selection or overwrite an imported result. If a pair is selected before the index arrives, its selection is retained and loading starts automatically once the index is available.

## Resource limits

The browser enforces 20 MiB limits for the downloaded index, each stored certificate, each decompressed certificate, and each imported file. An imported result supports at most 20,000 components and 10,000 candidates; an imported full-result catalogue supports at most 3,000 pairs. The hosted index supports at most 200,000 pair entries and 10,000 listed discriminants. Network requests time out after 30 seconds and expose a retry action.

Discriminants must be at most 10,000,000 in the browser, and Gram entries/determinants must fit exact JavaScript integers. The Python engine uses arbitrary-precision integers and its own explicit work/time limits.

## Embedded fallback

The original 66 full results are stored in:

```html
<script id="catalogue-data" type="application/json">...</script>
```

This block is unchanged by online loading. Escape `<` as `\u003c` when embedding arbitrary text to prevent an accidental closing script tag.

## Integration and verification

`window.HassettAtlas` exposes `loadData(json)`, `choosePair(d1, d2)`, `refreshCatalogue()`, `whenIdle()`, and `getState()`. The state includes startup status, the selected pair, its loading phase, online-index status, the available bound, and whether finite-range coverage is complete. `admissible(d)` checks the elementary factorization condition; `determinant(gram)` returns an exact decimal string.

Run:

```sh
node tests/test_explorer.cjs --write-report
```

The 192-assertion suite executes the actual embedded JavaScript. It covers startup and static-preview behavior, form and keyboard events, imports/exports, clipboard fallbacks, online-index validation, real native gzip decompression and SHA-256 calculations, both selection races, corruption rejection, safe paths, byte limits, retries, and offline behavior. HTTP responses and the DOM are test doubles; these are not browser-layout or actual-network tests.

To additionally validate the viewer against a real runner output directory, use:

```sh
node tests/test_explorer.cjs --hosted-data /path/to/data --write-report
```

This reads the real index and loads three representative shards through the same hashing, decompression, parsing, and rendering logic. It adds 16 assertions when all three samples are available. A native browser remains necessary to verify visual layout, native clipboard behavior, and real downloads in a particular environment.
