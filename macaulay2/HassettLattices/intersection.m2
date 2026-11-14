-- SPDX-License-Identifier: MIT
computeIntersection = (d1, d2, budget) -> (
    pair := normalizeHassettPair(d1, d2);
    cache := newCache();
    candidates := {};
    found := {};
    buckets := new MutableHashTable;
    counts := new MutableHashTable from apply({
        "overlattice_parameter_candidates", "integral_overlattices",
        "rejected_parity", "rejected_roots", "accepted_marked_lattices",
        "duplicate_count"}, key -> key => 0);
    increment := key -> counts#key = counts#key + 1;
    accept := (g, base, tau, n, a, b) -> (
        increment "accepted_marked_lattices";
        determinant := det g;
        embedding := matrix {{1,0,-a},{0,1,-b},{0,0,n}};
        bucket := if buckets#?determinant then buckets#determinant else {};
        change := id_(ZZ^3);
        origin := u -> new HashTable from {
            "tau" => tau, "index" => n, "a" => a, "b" => b,
            "base_gram" => base, "overlattice_gram" => g,
            "basis_map_to_representative" => u, "embedding" => u*embedding};
        for c in bucket do (
            tick budget;
            change = fixedIsometry(g, c#"gram", budget, cache);
            if change =!= null then (
                c#"origins" = append(c#"origins", origin change);
                increment "duplicate_count";
                return null));
        ordinal := toString(#found + 1);
        if #ordinal == 1 then ordinal = "0" | ordinal;
        c := new MutableHashTable from {
            "id" => toString pair#0 | "-" | toString pair#1 | "-c" | ordinal,
            "gram" => g, "determinant" => determinant, "rank" => 3,
            "h" => {1,0,0}, "tau" => tau, "index" => n,
            "origins" => {origin id_(ZZ^3)},
            "k3_association" => k3Association(g, budget)};
        found = append(found, c);
        buckets#determinant = append(bucket, c));
    -- All index-one origins precede proper saturations: stable historic IDs.
    bounds := parameterBounds(d1,d2);
    tau := bounds#0;
    while tau <= bounds#1 do (
        tick budget;
        g := hassettBaseGram(d1, d2, tau);
        root := rootVector(g, budget, cache);
        candidates = append(candidates, new MutableHashTable from {
            "tau" => tau, "gram" => g, "determinant" => det g,
            "root_free" => root === null, "root_witness" => root,
            "accepted_overlattices" => 0});
        if root === null then accept(g, g, tau, 1, 0, 0);
        tau = tau+1);
    scan(candidates, record -> if record#"root_free" then (
        base := record#"gram"; tau := record#"tau";
        p := base_(0,1); q := base_(0,2);
        aa := base_(1,1); bb := base_(2,2);
        scan(squareDivisorIndices(record#"determinant", budget), n -> if n > 1 then (
            scan(residues(pair#0, pair#1, tau, n, budget), ab -> (
                tick budget;
                increment "overlattice_parameter_candidates";
                (a,b) := toSequence ab;
                wn := 3*a^2+aa*b^2+bb+2*p*a*b+2*q*a+2*tau*b;
                if wn % n^2 == 0 then (
                    hp := (3*a+p*b+q)//n;
                    up := (p*a+aa*b+tau)//n;
                    wp := wn//n^2;
                    increment "integral_overlattices";
                    if (wp-hp) % 2 != 0 then increment "rejected_parity"
                    else (
                        g := matrix {{3,p,hp},{p,aa,up},{hp,up,wp}};
                        if rootVector(g, budget, cache) =!= null then
                            increment "rejected_roots"
                        else (
                            require(det g*n^2 == record#"determinant",
                                "index/discriminant identity failed");
                            record#"accepted_overlattices" = record#"accepted_overlattices"+1;
                            accept(g, base, tau, n, a, b))))))))));
    checkTime budget;
    counts#"positive_definite_taus" = apply(candidates, c -> c#"tau");
    counts#"root_free_taus" = apply(select(candidates, c -> c#"root_free"), c -> c#"tau");
    counts#"work_units" = budget#"work";
    counts#"elapsed_seconds" = wallTime()-budget#"started";
    new HassettResult from {
        "schema_version" => "1.0", "algorithm" => "Yang--Yu Algorithm 7.6",
        "reference" => "https://arxiv.org/abs/2103.09132",
        "input_pair" => {d1,d2}, "d1" => pair#0, "d2" => pair#1,
        "complete" => true, "component_count" => #found,
        "components" => apply(found, c -> new HashTable from pairs c),
        "candidates" => apply(candidates, c -> new HashTable from pairs c),
        "diagnostics" => new HashTable from pairs counts,
        "scope" => "Reduced irreducible components; scheme multiplicities are not computed."})

hassettIntersection = method(Options => {MaxWork => 5000000, TimeLimit => 60})
hassettIntersection(ZZ, ZZ) := o -> (d1, d2) -> computeIntersection(d1, d2, newBudget o)

net MarkedHassettLattice := l -> net("Marked rank-three lattice of determinant " |
    toString hassettDiscriminant l)
net HassettResult := r -> net("C_" | toString r#"d1" | " intersect C_" |
    toString r#"d2" | ": " | toString r#"component_count" |
    " reduced components (complete)")
