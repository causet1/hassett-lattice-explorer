-- SPDX-License-Identifier: MIT
-- Reuse JSON's published exact Parsing implementation for integers which
-- exceed Jansson's signed 64-bit range. Keep this compatibility surface small.
importFrom("JSON", {"jsonTextP", "utf8Analyzer", "processJSON"})
exactJSONParser = processJSON @@ (jsonTextP : utf8Analyzer)
decodeJSON = text -> try fromJSON text else exactJSONParser text

-- JSON 0.7 formats subunit reals as .5, which RFC 8259 rejects. Extend its
-- encoder for a private wrapper, without replacing any upstream method.
JSONReal = new Type of List
toJSON JSONReal := o -> x -> (
    require(abs(x#0) < infinity, "JSON numbers must be finite");
    s := format_0(x#0);
    if match("^[.]", s) then "0" | s
    else if match("^-[.]", s) then "-0" | substring(1, #s-1, s)
    else s)

jsonData = x -> (
    if instance(x, Matrix) then entries x
    else if instance(x, HashTable) or instance(x, MutableHashTable) then
        new HashTable from apply(pairs x, kv -> kv#0 => jsonData kv#1)
    else if instance(x, List) then apply(x, jsonData)
    else x)
encodeReals = x -> (
    if instance(x, RR) then new JSONReal from {x}
    else if instance(x, HashTable) then applyValues(x, encodeReals)
    else if instance(x, List) then apply(x, encodeReals)
    else x)
jsonBytes = data -> toJSON(encodeReals jsonData data, Sort => true,
    NameSeparator => ":", ValueSeparator => ",") | newline

hassettResultData = method(Options => {Timing => true})
hassettResultData HashTable := o -> r -> (
    require(instance(o.Timing, Boolean), "Timing must be Boolean");
    data := new MutableHashTable from pairs jsonData r;
    if not o.Timing then data#"diagnostics" = new HashTable from
        select(pairs data#"diagnostics", kv -> kv#0 != "elapsed_seconds");
    new HashTable from pairs data)

hydrate = data -> (
    matrixFields := {"gram", "base_gram", "overlattice_gram",
        "basis_map_to_representative", "embedding"};
    if instance(data, Matrix) then data
    else if instance(data, HashTable) then new HashTable from apply(pairs data, kv ->
        kv#0 => if member(kv#0, matrixFields) then exactMatrix(kv#1, 3, 3)
        else hydrate kv#1)
    else if instance(data, List) then apply(data, hydrate) else data)

verifyResult = (r, classification, budget) -> (
    require(r#"schema_version" === "1.0" and r#"complete" === true,
        "unsupported schema or incomplete result");
    pair := normalizeHassettPair(r#"d1", r#"d2");
    require(pair == {r#"d1", r#"d2"} and
        normalizeHassettPair toSequence r#"input_pair" == pair,
        "incorrect normalized pair");
    candidates := r#"candidates";
    components := r#"components";
    require(instance(r#"component_count", ZZ) and
        r#"component_count" == #components, "incorrect component count");
    bounds := parameterBounds toSequence pair;
    require(#candidates == bounds#1-bounds#0+1 and
        all(0..(#candidates-1), i -> candidates#i#"tau" === bounds#0+i),
        "incorrect starting coverage");
    cache := newCache();
    records := new MutableHashTable;
    accepted := new MutableHashTable;
    expectedBases := {}; actualBases := {};
    allOrigins := new MutableHashTable;
    ids := new MutableHashTable; grams := new MutableHashTable;
    scan(candidates, c -> (
        tick budget;
        tau := integer c#"tau";
        g := exactMatrix(c#"gram", 3, 3);
        require(g == hassettBaseGram(pair#0, pair#1, tau) and
            integer c#"determinant" == det g, "incorrect starting lattice");
        require(instance(c#"root_free", Boolean), "root_free must be Boolean");
        if c#"root_free" then (
            require(c#"root_witness" === null and
                rootVector(g, budget, cache) === null, "undetected starting root");
            expectedBases = append(expectedBases, {tau,1,0,0}))
        else (
            v := transpose exactMatrix({c#"root_witness"}, 1, 3);
            require((transpose v*g*v)_(0,0) == 2, "invalid root witness"));
        records#tau = c; accepted#tau = 0));
    scan(components, c -> (
        tick budget;
        g := (hassettLattice c#"gram")#"gram";
        require(instance(c#"id", String) and not ids#?(c#"id") and
            not grams#?g, "repeated component ID or Gram matrix");
        ids#(c#"id") = true; grams#g = true;
        require(integer c#"rank" == 3 and c#"h" === {1,0,0} and
            integer c#"determinant" == det g, "incorrect component invariants");
        require(rootVector(g, budget, cache) === null, "component contains a root");
        k3 := k3Association(g, budget);
        scan({"admissible", "discriminant_form", "content", "primitive_form",
            "h_splits_orthogonally", "mod3_witness", "obstructions"}, key ->
            require(c#"k3_association"#key === k3#key, "incorrect K3 field: " | key));
        require(#(c#"origins") > 0, "component has no origins");
        require(integer c#"tau" == (first c#"origins")#"tau" and
            integer c#"index" == (first c#"origins")#"index",
            "incorrect primary origin");
        scan(c#"origins", origin -> (
            tick budget;
            key := apply({"tau", "index", "a", "b"}, k -> integer origin#k);
            (tau, n, a, b) := toSequence key;
            require(not allOrigins#?key and records#?tau,
                "repeated origin or parameter outside interval");
            allOrigins#key = true;
            require(records#tau#"root_free" and n > 0 and a >= 0 and a < n and
                b >= 0 and b < n and gcd(b,n) == 1, "invalid primitive origin");
            base := exactMatrix(origin#"base_gram", 3, 3);
            over := (hassettLattice origin#"overlattice_gram")#"gram";
            u := exactMatrix(origin#"basis_map_to_representative", 3, 3);
            e := exactMatrix(origin#"embedding", 3, 3);
            canonical := matrix {{1,0,-a},{0,1,-b},{0,0,n}};
            require(base == records#tau#"gram" and abs det u == 1 and
                flatten entries u_{0} == {1,0,0}, "invalid origin or h-fixed map");
            require(transpose u*g*u == over and e == u*canonical and
                transpose e*g*e == base and det g*n^2 == det base,
                "invalid isometry, inclusion, or index identity");
            if n == 1 then actualBases = append(actualBases, key)
            else accepted#tau = accepted#tau+1))));
    require(sort expectedBases == sort actualBases, "missing starting origin");
    scan(candidates, c -> require(integer c#"accepted_overlattices" ==
        accepted#(c#"tau"), "incorrect saturation count"));
    diagnostics := r#"diagnostics";
    require(integer diagnostics#"accepted_marked_lattices" == #allOrigins and
        integer diagnostics#"duplicate_count" == #allOrigins-#components,
        "incorrect origin diagnostics");
    require(diagnostics#"positive_definite_taus" == apply(candidates, c -> c#"tau") and
        diagnostics#"root_free_taus" == apply(select(candidates, c -> c#"root_free"),
            c -> c#"tau"), "incorrect parameter diagnostics");
    if classification then (
        expected := computeIntersection(pair#0, pair#1, budget);
        require(#(expected#"components") == #components, "incorrect classification count");
        partition := c -> sort apply(c#"origins", origin ->
            apply({"tau", "index", "a", "b"}, k -> origin#k));
        classes := new HashTable from apply(components, c -> partition c => c);
        scan(expected#"components", c -> (
            key := partition c;
            require(classes#?key, "incorrect classification of origins");
            require(fixedIsometry(c#"gram", classes#key#"gram", budget, cache) =!= null,
                "incorrect representative isometry class"))));
    checkTime budget;
    true)

verifyHassettResult = method(Options => {
    Classification => false, MaxWork => 5000000, TimeLimit => 60})
verifyHassettResult HashTable := o -> r -> (
    require(instance(o.Classification, Boolean), "Classification must be Boolean");
    verifyResult(hydrate r, o.Classification, newBudget o))

-- Native POSIX rename gives same-directory atomic replacement. Core moveFile
-- copies and removes files and therefore is not suitable for checkpoints.
renameFile = foreignFunction("rename", int, {charstar, charstar})
temporaryCounter = 0
siblingTemporary = filename -> (
    temporaryCounter = temporaryCounter + 1;
    filename | ".tmp-" | toString processID() | "-" | toString temporaryCounter)
safeFilename = filename -> (
    require(not member(0, ascii filename), "NUL is not allowed in a filename");
    filename)
parentDirectory = filename -> (
    parts := separate("/", filename);
    if #parts == 1 then "." else concatenate between("/", drop(parts,-1)) | "/")
shellQuote = filename -> "'" | concatenate apply(ascii safeFilename filename,
    c -> if c == 39 then "'\\''" else ascii {c}) | "'"
atomicWrite = (filename, bytes) -> (
    safeFilename filename;
    makeDirectory parentDirectory filename;
    temporary := siblingTemporary filename;
    temporary << bytes << close;
    if value renameFile(temporary, filename) != 0 then (
        removeFile temporary;
        error "atomic file replacement failed");
    filename)

gzipFile = (filename, bytes) -> (
    makeDirectory parentDirectory filename;
    source := siblingTemporary filename;
    target := siblingTemporary filename;
    source << bytes << close;
    status := run("gzip -n -c < " | shellQuote source | " > " | shellQuote target);
    removeFile source;
    if status != 0 then (
        if fileExists target then removeFile target;
        error "gzip compression failed");
    if value renameFile(target, filename) != 0 then (
        removeFile target; error "atomic gzip replacement failed");
    filename)

readBytes = filename -> (
    if not match("[.]gz$", filename) then return get filename;
    -- Reading a certificate must not require write access to its directory.
    temporary := temporaryFileName();
    status := run("gzip -d -c < " | shellQuote filename | " > " | shellQuote temporary);
    if status != 0 then (
        if fileExists temporary then removeFile temporary;
        error "gzip decompression failed");
    result := get temporary;
    removeFile temporary;
    result)

writeHassettResult = method(Options => {Timing => false})
writeHassettResult(String, HashTable) := o -> (filename, r) -> (
    bytes := jsonBytes hassettResultData(r, Timing => o.Timing);
    if match("[.]gz$", filename) then gzipFile(filename, bytes)
    else atomicWrite(filename, bytes))

readHassettResult = method(Options => {
    Classification => false, MaxWork => 5000000, TimeLimit => 60})
readHassettResult String := o -> filename -> (
    require(instance(o.Classification, Boolean), "Classification must be Boolean");
    budget := newBudget o;
    data := hydrate decodeJSON readBytes filename;
    verifyResult(data, o.Classification, budget);
    new HassettResult from pairs data)
