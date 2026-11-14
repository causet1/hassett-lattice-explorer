-- SPDX-License-Identifier: MIT
publishedCases = new HashTable from {
    {8,14} => {"Auel et al., Theorem 4", "https://arxiv.org/abs/1205.0237v4",
        {21,29,32,36,37}},
    {8,26} => {"Awada, Proposition 3.2", "https://arxiv.org/abs/1910.10182v2",
        {29,36,48,53,61,64,68,69}},
    {8,38} => {"Awada, Theorem 1.1(2)", "https://arxiv.org/abs/1910.10182v2",
        {36,45,61,68,80,85,93,96,100,101}},
    {12,20} => {"Yang--Yu, Theorem 7.11", "https://arxiv.org/abs/2103.09132",
        {20,32,53,68,77,80}},
    {20,38} => {"Yang--Yu, Theorem 7.9", "https://arxiv.org/abs/2103.09132",
        {45,77,92,120,133,157,168,188,197,213,220,232,237,245,248,252,253}}}

pairKey = pair -> concatenate between("-", apply(sort pair, toString))
publicationValidation = r -> (
    pair := sort {r#"d1", r#"d2"};
    if not publishedCases#?pair then return new HashTable from {
        "status" => "computed",
        "reference" => "Exact algorithm; not an independent published fixture"};
    (reference, url, expected) := toSequence publishedCases#pair;
    require(sort apply(r#"components", c -> c#"determinant") == expected,
        "published fixture mismatch");
    new HashTable from {"status" => "matched", "reference" => reference,
        "url" => url, "expected_count" => #expected,
        "expected_discriminants" => expected})

hassettCatalogueSummary = r -> (
    cs := r#"components";
    ds := apply(cs, c -> c#"determinant");
    ns := flatten apply(cs, c -> apply(c#"origins", origin -> origin#"index"));
    admissible := #select(cs, c -> c#"k3_association"#"admissible");
    new HashTable from {
        "key" => pairKey {r#"d1",r#"d2"}, "d1" => r#"d1", "d2" => r#"d2",
        "component_count" => #cs, "marked_origin_count" => #ns,
        "duplicate_count" => #ns-#cs,
        "determinants" => new HashTable from {
            "min" => min ds, "max" => max ds, "distinct" => #unique ds, "sum" => sum ds},
        "k3" => new HashTable from {"admissible" => admissible,
            "nonadmissible" => #cs-admissible},
        "saturation" => new HashTable from {
            "components" => #select(cs, c -> any(c#"origins", origin -> origin#"index" > 1)),
            "origins" => #select(ns, n -> n > 1), "max_index" => max ns}})

aggregateRows = rows -> (
    total := key -> sum apply(rows, row -> row#key);
    nested := (key, field) -> sum apply(rows, row -> row#key#field);
    new HashTable from {
        "total_components" => total "component_count",
        "total_component_records" => total "component_count",
        "total_marked_origins" => total "marked_origin_count",
        "total_k3_admissible_components" => nested("k3", "admissible"),
        "total_k3_nonadmissible_components" => nested("k3", "nonadmissible"),
        "total_components_with_saturation" => nested("saturation", "components"),
        "total_proper_overlattice_origins" => nested("saturation", "origins"),
        "total_duplicate_routes" => total "duplicate_count",
        "max_saturation_index" => max prepend(0, apply(rows, r -> r#"saturation"#"max_index")),
        "min_component_determinant" => if #rows == 0 then null
            else min apply(rows, r -> r#"determinants"#"min"),
        "max_component_determinant" => if #rows == 0 then null
            else max apply(rows, r -> r#"determinants"#"max"),
        "total_bytes" => total "bytes",
        "total_uncompressed_bytes" => total "uncompressed_bytes"})

fileSHA256 = filename -> (
    temporary := temporaryFileName();
    command := "if command -v sha256sum >/dev/null 2>&1; then sha256sum; " |
        "else shasum -a 256; fi < " | shellQuote filename | " > " | shellQuote temporary;
    status := run command;
    if status != 0 then (removeFile temporary; error "SHA-256 command failed");
    result := first separate(" ", get temporary);
    removeFile temporary;
    require(match("^[0-9a-f]{64}$", result), "invalid SHA-256 output");
    result)

buildHassettCatalogue = method(Options => {
    Compressed => true, Resume => true, StopAfter => null, CheckpointEvery => 10,
    Classification => false, MaxWork => 5000000, TimeLimit => 60})
buildHassettCatalogue(String, ZZ) := o -> (directory, bound) -> (
    require(bound >= 8, "catalogue bound must be at least 8");
    require(instance(o.Compressed, Boolean) and instance(o.Resume, Boolean) and
        instance(o.Classification, Boolean), "catalogue flags must be Boolean");
    require(integer o.CheckpointEvery > 0, "CheckpointEvery must be positive");
    require(o.StopAfter === null or integer o.StopAfter > 0,
        "StopAfter must be positive or null");
    newBudget o;
    safeFilename directory;
    directory = directory | "/";
    makeDirectory(directory | "pairs/");
    labels := validHassettDiscriminants bound;
    pairList := subsets(labels, 2);
    extension := if o.Compressed then ".json.gz" else ".json";
    allowed := set apply(pairList, pair -> pairKey pair | extension);
    scan(readDirectory(directory | "pairs/"), name -> (
        if match("[.]json([.]gz)?$", name) then require(member(name, allowed),
            "existing shards use another bound or compression; use a new directory")));
    rows := {}; failures := {};
    processed := 0; computed := 0; reused := 0; repaired := 0;
    started := wallTime();
    checkpoint := stage -> (
        statistics := aggregateRows rows;
        index := new HashTable from {
            "schema_version" => "1.1", "title" => "Hassett Lattice Explorer",
            "catalogue_version" => "1.1.0", "algorithm" => "Yang--Yu Algorithm 7.6",
            "reference" => "https://arxiv.org/abs/2103.09132", "license" => "MIT",
            "max_discriminant" => bound, "discriminants" => labels,
            "expected_pair_count" => #pairList, "pair_count" => #rows,
            "component_count" => statistics#"total_components",
            "component_records" => statistics#"total_components",
            "failed_pair_count" => #failures,
            "pending_pair_count" => #pairList-#rows-#failures,
            "complete" => #rows == #pairList and #failures == 0,
            "scope" => "Finite range of distinct label pairs; component records across pairs are not globally distinct loci. Reduced components only.",
            "pairs" => rows, "statistics" => statistics, "failures" => failures};
        atomicWrite(directory | "catalogue-index.json", jsonBytes index);
        atomicWrite(directory | "failures.json", jsonBytes new HashTable from {
            "schema_version" => "1.0", "failures" => failures});
        atomicWrite(directory | "run-state.json", jsonBytes new HashTable from {
            "stage" => stage, "updated_at" => currentTime(),
            "elapsed_seconds" => wallTime()-started,
            "processed_this_run" => processed, "computed_this_run" => computed,
            "reused_this_run" => reused, "invalid_existing_files" => repaired});
        index);
    for pair in pairList do (
        if o.StopAfter =!= null and processed >= o.StopAfter then break;
        key := pairKey pair;
        relative := "pairs/" | key | extension;
        filename := directory | relative;
        result := null;
        budget := newBudget o;
        if o.Resume and fileExists filename then (
            result = try (
                existing := hydrate decodeJSON readBytes filename;
                verifyResult(existing, o.Classification, budget);
                require(sort {existing#"d1",existing#"d2"} == pair, "wrong shard pair");
                publicationValidation existing;
                existing) else null;
            if result =!= null then reused = reused+1
            else if budget#"failure" === null then repaired = repaired+1);
        if result === null and budget#"failure" === null then (
            budget = newBudget o;
            result = try computeIntersection(pair#0, pair#1, budget) except err do (
                if budget#"failure" === null then (
                    checkpoint "error";
                    error err);
                null);
            if result =!= null then computed = computed+1
            else if budget#"failure" === null then (
                checkpoint "error";
                error("unexpected computation failure for " | key)));
        if result === null then failures = append(failures, new HashTable from {
            "key" => key, "d1" => pair#0, "d2" => pair#1, "error" => budget#"failure"})
        else (
            data := new MutableHashTable from pairs hassettResultData(result, Timing => false);
            data#"input_pair" = pair;
            data#"validation" = publicationValidation result;
            raw := jsonBytes data;
            if o.Compressed then gzipFile(filename, raw) else atomicWrite(filename, raw);
            rawFile := siblingTemporary filename;
            rawFile << raw << close;
            row := new MutableHashTable from pairs hassettCatalogueSummary result;
            row#"path" = relative;
            row#"compression" = if o.Compressed then "gzip" else "none";
            row#"sha256" = fileSHA256 filename;
            row#"uncompressed_sha256" = fileSHA256 rawFile;
            removeFile rawFile;
            row#"bytes" = #get filename;
            row#"uncompressed_bytes" = #raw;
            row#"validation" = data#"validation"#"status";
            rows = append(rows, new HashTable from pairs row));
        processed = processed+1;
        if processed % o.CheckpointEvery == 0 then checkpoint "running");
    checkpoint "finished")
