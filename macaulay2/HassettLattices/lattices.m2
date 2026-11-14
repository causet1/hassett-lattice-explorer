-- SPDX-License-Identifier: MIT
MarkedHassettLattice = new Type of HashTable
HassettResult = new Type of HashTable

exactMatrix = (g, rows, cols) -> (
    if instance(g, List) then (
        require(#g == rows and all(g, r -> instance(r, List) and #r == cols
            and all(r, x -> instance(x, ZZ))), "expected an integral matrix");
        g = matrix g);
    require(instance(g, Matrix) and ring g === ZZ and
        numRows g == rows and numColumns g == cols,
        "incorrect integral matrix dimensions");
    g)

gram = g -> (
    if instance(g, HashTable) and not instance(g, Matrix) then g = g#"gram";
    g = exactMatrix(g, 3, 3);
    require(g == transpose g and g_(0,0) == 3,
        "expected a symmetric Gram matrix with first vector of square 3");
    require(3*g_(1,1)-g_(0,1)^2 > 0 and det g > 0,
        "Gram matrix must be positive definite");
    g)

hassettLattice = g -> (
    g = gram g;
    require(all(0..2, i -> (g_(i,i)-g_(0,i)) % 2 == 0),
        "the first vector is not distinguished");
    new MarkedHassettLattice from {"gram" => g})

hassettGram = l -> gram l
hassettDiscriminant = l -> det gram l
hassettComponents = r -> r#"components"

changeHassettBasis = (l, u) -> (
    g := (hassettLattice l)#"gram";
    u = exactMatrix(u, 3, 3);
    require(abs det u == 1 and flatten entries u_{0} == {1,0,0},
        "basis change must be unimodular and fix h");
    hassettLattice(transpose u*g*u))

schurForm = g -> (
    p := g_(0,1); q := g_(0,2);
    matrix {{3*g_(1,1)-p^2, 3*g_(1,2)-p*q},
        {3*g_(1,2)-p*q, 3*g_(2,2)-q^2}})

newCache = () -> new MutableHashTable from {
    "roots" => new MutableHashTable, "binary" => new MutableHashTable}

-- An integral triangular surrogate reuses Euclidean LLL without pretending
-- its input is a Gram matrix. If t=floor(sqrt(det H)), then for every v,
-- (A/4)*v^t H v <= ||[[A,B],[0,t]]v||^2 <= A*v^t H v.
-- Certify the change map and enumerate the exact transformed H afterwards.
binaryData = (g, budget, cache) -> (
    if cache#"binary"#?g then return cache#"binary"#g;
    h := schurForm g;
    u := id_(ZZ^2);
    if h_(0,0)*h_(1,1) > 4*det h then (
        tick budget;
        surrogate := matrix {{h_(0,0),h_(0,1)},{0,integerSqrt det h}};
        (reduced, candidate) := LLL(surrogate, ChangeMatrix => true, Strategy => NTL);
        checkTime budget;
        require(abs det candidate == 1 and reduced == surrogate*candidate,
            "LLLBases returned an invalid change matrix");
        transformed := transpose candidate*h*candidate;
        if transformed_(0,0)*transformed_(1,1) < h_(0,0)*h_(1,1)
        then (u = candidate; h = transformed));
    -- Enumerate the coordinate with the smaller exact dual bound.
    if h_(0,0) > h_(1,1) then (
        swap := matrix {{0,1},{1,0}};
        u = u*swap; h = transpose swap*h*swap);
    result := {u, h_(0,0), h_(0,1), h_(1,1), det h};
    cache#"binary"#g = result;
    result)

-- Solve a quadratic by an exact discriminant square test. This replaces
-- the two-dimensional rectangle search with a single coordinate loop.
vectorsWithPairing = (g, norm, pairing, budget, cache) -> (
    target := 3*norm-pairing^2;
    if target < 0 then return {};
    (u, aa, bb, cc, delta) := toSequence binaryData(g, budget, cache);
    bound := integerSqrt((target*aa)//delta);
    result := {};
    z := -bound;
    while z <= bound do (
        tick budget;
        square := aa*target-delta*z^2;
        root := integerSqrt square;
        if root^2 == square then scan(unique {root, -root}, k -> (
            if (k-bb*z) % aa == 0 then (
                y := (k-bb*z)//aa;
                yy := u_(0,0)*y+u_(0,1)*z;
                zz := u_(1,0)*y+u_(1,1)*z;
                x := pairing-g_(0,1)*yy-g_(0,2)*zz;
                if x % 3 == 0 then result = append(result, {x//3,yy,zz}))));
        z = z+1);
    result)

rootVector = (g, budget, cache) -> (
    tick budget;
    if cache#"roots"#?g then return cache#"roots"#g;
    h := schurForm g;
    result := null;
    if min(h_(0,0), h_(1,1))-abs h_(0,1) <= 6 then (
        for s from -2 to 2 do (
            vectors := vectorsWithPairing(g, 2, s, budget, cache);
            if #vectors > 0 then (result = first vectors; break)));
    cache#"roots"#g = result;
    result)

normTwoVector = method(Options => {MaxWork => 5000000, TimeLimit => 60})
normTwoVector Thing := o -> g -> rootVector(gram g, newBudget o, newCache())

markedBasis = (g, budget, cache) -> (
    p := first binaryData(g, budget, cache);
    u := matrix {{1,0,0},{0,p_(0,0),p_(0,1)},{0,p_(1,0),p_(1,1)}};
    pairing := g^{0}*u;
    shift := matrix {{1,-floorQuotient(pairing_(0,1)+1,3),
        -floorQuotient(pairing_(0,2)+1,3)},{0,1,0},{0,0,1}};
    u = u*shift;
    {u, transpose u*g*u})

fixedIsometry = (source, target, budget, cache) -> (
    if source == target then return id_(ZZ^3);
    if det source != det target then return null;
    (sourceBasis, reducedSource) := toSequence markedBasis(source, budget, cache);
    (targetBasis, reducedTarget) := toSequence markedBasis(target, budget, cache);
    us := vectorsWithPairing(reducedTarget, reducedSource_(1,1), reducedSource_(0,1), budget, cache);
    vs := vectorsWithPairing(reducedTarget, reducedSource_(2,2), reducedSource_(0,2), budget, cache);
    for u in us do for v in vs do (
        tick budget;
        if abs(u#1*v#2-u#2*v#1) == 1 then (
            change := transpose matrix {{1,0,0},u,v};
            if transpose change*reducedTarget*change == reducedSource then (
                answer := targetBasis*change*sub(inverse sourceBasis,ZZ);
                require(transpose answer*target*answer == source and abs det answer == 1,
                    "invalid transported isometry");
                return answer)));
    null)

hFixedIsometry = method(Options => {MaxWork => 5000000, TimeLimit => 60})
hFixedIsometry(Thing, Thing) := o -> (source, target) ->
    fixedIsometry(gram source, gram target, newBudget o, newCache())

k3Association = (g, budget) -> (
    h := schurForm g;
    form := {h_(0,0), 2*h_(0,1), h_(1,1)};
    content := gcd form;
    primitive := apply(form, x -> x//content);
    split := g_(0,1) % 3 == 0 and g_(0,2) % 3 == 0;
    obstructions := arithmeticObstructions(content, budget);
    witness := null;
    for y from 0 to 2 do (
        for z from 0 to 2 do (
            if (primitive#0*y^2+primitive#1*y*z+primitive#2*z^2) % 3 == 1
            then (witness = {y,z}; break));
        if witness =!= null then break);
    if split and witness === null then obstructions = append(obstructions,
        "primitive discriminant form does not represent 1 modulo 3");
    new HashTable from {
        "admissible" => #obstructions == 0, "discriminant_form" => form,
        "content" => content, "primitive_form" => primitive,
        "h_splits_orthogonally" => split, "mod3_witness" => witness,
        "obstructions" => obstructions,
        "criterion" => if split then "Yang--Yu Theorem 8.9"
            else "Yang--Yu Theorem 8.8",
        "interpretation" => "Whole-lattice untwisted K3 criterion; not a rationality decision."})

latticeK3Association = method(Options => {MaxWork => 5000000, TimeLimit => 60})
latticeK3Association Thing := o -> l ->
    k3Association((hassettLattice l)#"gram", newBudget o)

markings = (g, bound, admissibleOnly, budget) -> (
    require(integer bound >= 0, "bound must be nonnegative");
    (u, aa, bb, cc, delta) := toSequence binaryData(g, budget, newCache());
    result := {};
    zBound := integerSqrt((bound*aa)//delta);
    z := -zBound;
    while z <= zBound do (
        tick budget;
        radius := integerSqrt(aa*bound-delta*z^2);
        y := ceilingQuotient(-bb*z-radius, aa);
        yMax := floorQuotient(-bb*z+radius, aa);
        while y <= yMax do (
            tick budget;
            yy := u_(0,0)*y+u_(0,1)*z;
            zz := u_(1,0)*y+u_(1,1)*z;
            if gcd(yy, zz) == 1 and (yy > 0 or (yy == 0 and zz > 0)) then (
                d := aa*y^2+2*bb*y*z+cc*z^2;
                if validHassettDiscriminant d then (
                    admissible := #arithmeticObstructions(d, budget) == 0;
                    if not admissibleOnly or admissible then (
                        e := matrix {{1,0},{0,yy},{0,zz}};
                        result = append(result, {d, yy, zz,
                            new HashTable from {"discriminant" => d,
                                "vector" => {0,yy,zz},
                                "gram" => transpose e*g*e,
                                "admissible" => admissible}}))));
            y = y+1);
        z = z+1);
    apply(sort result, last))

primitiveHassettMarkings = method(Options => {
    AdmissibleOnly => false, MaxWork => 5000000, TimeLimit => 60})
primitiveHassettMarkings(Thing, ZZ) := o -> (l, bound) -> (
    require(instance(o.AdmissibleOnly, Boolean), "AdmissibleOnly must be Boolean");
    markings((hassettLattice l)#"gram", bound, o.AdmissibleOnly, newBudget o))

k3Witness = method(Options => {MaxWork => 5000000, TimeLimit => 60})
k3Witness(Thing, ZZ) := o -> (l, bound) -> (
    found := markings((hassettLattice l)#"gram", bound, true, newBudget o);
    if #found == 0 then null else first found)

hassettInvariants = method(Options => {MaxWork => 5000000, TimeLimit => 60})
hassettInvariants Thing := o -> l -> (
    g := (hassettLattice l)#"gram";
    budget := newBudget o;
    tick budget;
    smith := smithNormalForm(g, ChangeMatrix => {false, false});
    checkTime budget;
    new HashTable from {"rank" => 3, "determinant" => det g,
        "discriminant_group" => select(apply(toList(0..2), i -> abs smith_(i,i)), n -> n != 1),
        "h_divisibility" => gcd flatten entries g^{0},
        "k3_association" => k3Association(g, budget)})
