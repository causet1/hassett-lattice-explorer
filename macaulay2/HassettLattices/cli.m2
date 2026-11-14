-- SPDX-License-Identifier: MIT
-- Invoke with M2 --script .../cli.m2 COMMAND ARGS OPTIONS.
path = prepend(currentFileDirectory | "../", path);
needsPackage "HassettLattices";
needsPackage "JSON";

helpText = ///HassettLattices (Macaulay2)
  intersect D1 D2 [--output FILE[.gz]]
  verify FILE[.gz] [--classification]
  catalogue BOUND DIRECTORY [--plain] [--no-resume]
      [--stop-after N] [--checkpoint-every N] [--classification]
  summary FILE[.gz]
  invariants FILE[.gz] COMPONENT-ID
  markings FILE[.gz] COMPONENT-ID BOUND [--admissible-only]
  labels BOUND
Options: --max-work N|none --timeout SECONDS|none --output FILE[.gz]
Defaults: 5000000 work units, 60 seconds per operation/pair.
Exit codes: 0 success; 1 incomplete catalogue; 2 invalid input or failed search.
///;

-- Parse only a restricted decimal grammar; never evaluate arbitrary CLI input.
parseInteger = text -> (
    if not match("^[+-]?[0-9]+$", text) then error "expected an integer";
    value text);
parseSeconds = text -> (
    if not match("^[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$", text) then
        error "expected a positive number of seconds";
    value text);

main = args -> (
    if #args == 0 or member(first args, {"help", "--help", "-h"}) then (
        print helpText; return 0);
    command := first args;
    positional := {};
    output := null; maxWork := 5000000; timeout := 60;
    classification := false; compressed := true; resume := true;
    stopAfter := null; checkpointEvery := 10; admissibleOnly := false;
    i := 1;
    while i < #args do (
        arg := args#i;
        if member(arg, {"--output", "-o", "--max-work", "--timeout",
            "--stop-after", "--checkpoint-every"}) then (
            if i+1 >= #args then error("missing argument for " | arg);
            if member(arg,{"--stop-after","--checkpoint-every"}) and command != "catalogue"
            then error(arg | " is only valid for catalogue");
            if member(arg,{"--output","-o"}) and command == "catalogue"
            then error "catalogue writes to its DIRECTORY argument";
            i = i+1; val := args#i;
            if member(arg, {"--output", "-o"}) then output = val
            else if arg == "--max-work" then maxWork =
                if val == "none" then null else parseInteger val
            else if arg == "--timeout" then timeout =
                if val == "none" then null else parseSeconds val
            else if arg == "--stop-after" then stopAfter = parseInteger val
            else checkpointEvery = parseInteger val)
        else if arg == "--classification" then (
            if member(command,{"intersect","labels"}) then error "--classification requires stored results";
            classification = true)
        else if arg == "--plain" then (
            if command != "catalogue" then error "--plain is only valid for catalogue";
            compressed = false)
        else if arg == "--no-resume" then (
            if command != "catalogue" then error "--no-resume is only valid for catalogue";
            resume = false)
        else if arg == "--admissible-only" then (
            if command != "markings" then error "--admissible-only is only valid for markings";
            admissibleOnly = true)
        else if match("^--", arg) then error("unknown option: " | arg)
        else positional = append(positional, arg);
        i = i+1);
    need := n -> if #positional != n then error("wrong number of arguments for " | command);
    result := null;
    if command == "intersect" then (
        need 2;
        result = hassettIntersection(parseInteger positional#0, parseInteger positional#1,
            MaxWork => maxWork, TimeLimit => timeout);
        if output =!= null then writeHassettResult(output, result)
        else print toJSON hassettResultData(result, Timing => false);
        return 0);
    if command == "catalogue" then (
        need 2;
        result = buildHassettCatalogue(positional#1, parseInteger positional#0,
            Compressed => compressed, Resume => resume, StopAfter => stopAfter,
            CheckpointEvery => checkpointEvery, Classification => classification,
            MaxWork => maxWork, TimeLimit => timeout);
        print toJSON result;
        return if result#"complete" then 0 else 1);
    if command == "labels" then (need 1; result = validHassettDiscriminants parseInteger positional#0)
    else (
        if member(command, {"verify", "summary"}) then need 1
        else if command == "invariants" then need 2
        else if command == "markings" then need 3
        else error("unknown command: " | command);
        r := readHassettResult(positional#0, Classification => classification,
            MaxWork => maxWork, TimeLimit => timeout);
        if command == "verify" then result = new HashTable from {"passed" => true,
            "classification_recomputed" => classification,
            "component_count" => r#"component_count"}
        else if command == "summary" then result = hassettCatalogueSummary r
        else (
            matches := select(hassettComponents r, c -> c#"id" == positional#1);
            if #matches != 1 then error "unknown component ID";
            c := first matches;
            if command == "invariants" then result = hassettInvariants(c,
                MaxWork => maxWork, TimeLimit => timeout)
            else result = primitiveHassettMarkings(c, parseInteger positional#2,
                AdmissibleOnly => admissibleOnly, MaxWork => maxWork, TimeLimit => timeout)));
    -- Reuse the package encoder for matrices in marking records.
    encode := value first importFrom("HassettLattices", "jsonBytes");
    bytes := encode result;
    if output === null then << bytes else (
        save := value first importFrom("HassettLattices",
            if match("[.]gz$", output) then "gzipFile" else "atomicWrite");
        save(output, bytes));
    0);

exit try main drop(scriptCommandLine, 1) except err do (
    stderr << "HassettLattices: " << toString err << endl;
    2);
