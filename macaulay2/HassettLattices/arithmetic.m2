-- SPDX-License-Identifier: MIT
HassettResourceLimitError = new SelfInitializingType of Error
-- The documented ForeignFunctions interface calls GMP; no square-root
-- implementation or floating-point bound is duplicated here.
gmpSqrt = foreignFunction("__gmpz_sqrt", void, {mpzT, mpzT})
integerSqrt = n -> (
    if n < 0 then error "negative integer square root";
    out := mpzT 0;
    gmpSqrt(out, n);
    value out)

-- CLOCK_MONOTONIC on the supported POSIX platforms; backend calls are
-- cooperative (checked before/after), never forcibly interrupted.
timespecType = foreignStructType("HassettTimespec",
    {"seconds" => long, "nanoseconds" => long})
clockGettime = foreignFunction("clock_gettime", int, {int, voidstar})
monotonicClock = if version#"operating system" == "Darwin" then 6 else 1
wallTime = () -> (
    stamp := timespecType {"seconds" => 0, "nanoseconds" => 0};
    if value clockGettime(monotonicClock, address stamp) != 0 then
        error "clock_gettime failed";
    value stamp_"seconds" + (value stamp_"nanoseconds")/1.0e9)

require = (condition, message) -> if not condition then error message
-- M2's // and % truncate toward zero; use QQ for signed floor/ceiling.
ceilingQuotient = (a, b) -> ceiling(a/b)
floorQuotient = (a, b) -> floor(a/b)
integer = x -> (
    require(instance(x, ZZ), "expected an exact integer");
    x)

newBudget = o -> (
    require(o.MaxWork === null or
        (instance(o.MaxWork, ZZ) and o.MaxWork > 0),
        "MaxWork must be a positive integer or null");
    require(o.TimeLimit === null or
        (instance(o.TimeLimit, Number) and o.TimeLimit > 0 and
            o.TimeLimit < infinity), "TimeLimit must be positive and finite or null");
    new MutableHashTable from {
        "max" => o.MaxWork, "timeout" => o.TimeLimit,
        "started" => wallTime(), "work" => 0, "failure" => null})

checkTime = budget -> (
    if budget#"timeout" =!= null and
        wallTime() - budget#"started" > budget#"timeout" then (
        budget#"failure" = "time limit exceeded; no complete result";
        error HassettResourceLimitError(budget#"failure")))

tick = budget -> (
    if budget#"max" =!= null and budget#"work" >= budget#"max" then (
        budget#"failure" = "work limit exceeded; no complete result";
        error HassettResourceLimitError(budget#"failure"));
    budget#"work" = budget#"work" + 1;
    checkTime budget)

factorPairs = (n, budget) -> (
    tick budget;
    ans := if n == 1 then {} else apply(toList factor n, toList);
    checkTime budget;
    ans)

validHassettDiscriminant = d -> instance(d, ZZ) and d > 6 and
    member(d % 6, {0, 2})

validHassettDiscriminants = bound -> (
    require(integer bound >= 0, "bound must be nonnegative");
    select(toList(8..bound), validHassettDiscriminant))

arithmeticObstructions = (d, budget) -> (
    out := {};
    if d % 4 == 0 then out = append(out, "divisible by 4");
    if d % 9 == 0 then out = append(out, "divisible by 9");
    scan(sort factorPairs(d, budget), pe -> (
        p := pe#0;
        if p != 2 and p % 3 == 2 then out = append(out,
            "divisible by the odd prime " | toString p |
            ", congruent to 2 modulo 3")));
    out)

admissibleHassettDiscriminant = method(Options => {
    MaxWork => 5000000, TimeLimit => 60})
admissibleHassettDiscriminant Thing := o -> d ->
    validHassettDiscriminant d and
    #arithmeticObstructions(d, newBudget o) == 0

normalizeHassettPair = (d1, d2) -> (
    require(validHassettDiscriminant d1 and validHassettDiscriminant d2,
        "labels must be integers > 6, congruent to 0 or 2 modulo 6");
    require(d1 != d2, "self-intersection is not a rank-three problem");
    if d1 % 6 == d2 % 6 then sort {d1, d2}
    else if d1 % 6 == 2 then {d1, d2} else {d2, d1})

parameterBounds = (d1, d2) -> (
    pair := normalizeHassettPair(d1, d2);
    eps := if pair#0 % 6 == 2 and pair#1 % 6 == 2 then 1 else 0;
    radius := integerSqrt(pair#0 * pair#1 - 1);
    lower := ceilingQuotient(eps - radius, 3);
    if eps == 0 then lower = max(0, lower);
    {lower, (eps + radius)//3})

positiveHassettParameters = (d1, d2) -> (
    bounds := parameterBounds(d1,d2);
    toList(bounds#0..bounds#1))

hassettBaseGram = (d1, d2, tau) -> (
    pair := normalizeHassettPair(d1, d2);
    integer tau;
    p := if pair#0 % 6 == 2 then 1 else 0;
    q := if pair#1 % 6 == 2 then 1 else 0;
    matrix {{3, p, q}, {p, (pair#0+p)//3, tau},
        {q, tau, (pair#1+q)//3}})

squareDivisorIndices = (d, budget) -> (
    require(integer d > 0, "determinant must be positive");
    result := {1};
    scan(factorPairs(d, budget), pe -> (
        result = flatten apply(toList(0..(pe#1//2)), k ->
            apply(result, n -> n*pe#0^k))));
    sort result)

saturationIndices = method(Options => {MaxWork => 5000000, TimeLimit => 60})
saturationIndices ZZ := o -> d -> squareDivisorIndices(d, newBudget o)

linearResidueData = (c, rhs, n) -> (
    (g, u, v) := gcdCoefficients(c, n);
    if rhs % g != 0 then return null;
    period := n//g;
    start := (u*(rhs//g)) % period;
    if start < 0 then start = start + period;
    {start, period})

residues = (d1, d2, tau, n, budget) -> (
    require(integer n > 0, "index must be positive");
    integer tau;
    p := if d1 % 6 == 2 then 1 else 0;
    q := if d2 % 6 == 2 then 1 else 0;
    aa := (d1+p)//3;
    result := {};
    bs := linearResidueData(d1, p*q-3*tau, n);
    if bs === null then return {};
    b := bs#0;
    while b < n do (
        tick budget;
        if gcd(b, n) == 1 then (
            as := linearResidueData(3, -p*b-q, n);
            if as =!= null then (
                a := as#0;
                while a < n do (
                    tick budget;
                    if (p*a+aa*b+tau) % n == 0 then result = append(result, {a,b});
                    a = a+as#1)));
        b = b+bs#1);
    sort result)

saturationResidues = method(Options => {MaxWork => 5000000, TimeLimit => 60})
saturationResidues(ZZ, ZZ, ZZ, ZZ) := o -> (d1, d2, tau, n) -> (
    pair := normalizeHassettPair(d1, d2);
    residues(pair#0, pair#1, tau, n, newBudget o))
