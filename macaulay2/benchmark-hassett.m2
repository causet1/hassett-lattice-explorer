-- SPDX-License-Identifier: MIT
-- The name avoids shadowing the distributed Benchmark package on macOS.
path = prepend(currentFileDirectory,path);
needsPackage "HassettLattices";
args = drop(scriptCommandLine,1);
output = if #args == 0 then "build/macaulay2-benchmark.json" else args#0;
repeats = 7;
rows = apply({{8,26},{8,96},{446,494},{456,488},{498,500}}, pair -> (
    hassettIntersection(pair#0,pair#1,MaxWork=>null,TimeLimit=>null);
    samples := {};
    r := null;
    for i from 1 to repeats do (
        measured := elapsedTiming hassettIntersection(pair#0,pair#1,
            MaxWork=>null,TimeLimit=>null);
        samples = append(samples,measured#0);
        r = measured#1);
    new HashTable from {"pair"=>pair, "components"=>r#"component_count",
        "median_seconds"=>(sort samples)#(repeats//2), "samples_seconds"=>samples,
        "work_units"=>r#"diagnostics"#"work_units"}));
report = new HashTable from {"macaulay2"=>version#"VERSION", "repeats"=>repeats,
    "operating_system"=>version#"operating system", "architecture"=>version#"architecture",
    "scope"=>"Warm native M2 engine medians; excludes startup, Docker, and serialization.",
    "measurements"=>rows};
encode = value first importFrom("HassettLattices","jsonBytes");
save = value first importFrom("HassettLattices","atomicWrite");
save(output,encode report);
print("Wrote " | output);
