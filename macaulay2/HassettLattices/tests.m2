-- SPDX-License-Identifier: MIT
TEST ///
assert(validHassettDiscriminants 20 == {8,12,14,18,20})
assert(not validHassettDiscriminant 6)
assert(not validHassettDiscriminant 14.0)
assert(normalizeHassettPair(12,20) == {20,12})
assert(positiveHassettParameters(8,14) == {-3,-2,-1,0,1,2,3})
assert(saturationIndices 144 == {1,2,3,4,6,12})
assert(saturationIndices 1 == {1})
assert(admissibleHassettDiscriminant 14)
assert(not admissibleHassettDiscriminant 8)
assert((try hassettIntersection(14,14) else null) === null)
assert((try hassettIntersection(8,14,MaxWork=>1) else null) === null)
assert(instance((try hassettIntersection(8,6*10^50+2,MaxWork=>1)
    except err do err),HassettResourceLimitError))
assert((try hassettIntersection(8,14,TimeLimit=>1e-12) else null) === null)
assert((try hassettIntersection(8,14,TimeLimit=>0) else null) === null)
-- Independent exhaustive residue boxes, including negative parameters,
-- noninvertible coefficients, and indices divisible by three.
scan({{8,14},{8,12},{12,18},{20,42}}, pair -> (
    p = if pair#0 % 6 == 2 then 1 else 0;
    q = if pair#1 % 6 == 2 then 1 else 0;
    aa = (pair#0+p)//3;
    for tau from -5 to 5 do for n from 1 to 18 do (
        expected = {};
        for a from 0 to n-1 do for b from 0 to n-1 do
            if gcd(b,n) == 1 and (3*a+p*b+q) % n == 0 and
                (p*a+aa*b+tau) % n == 0 then expected = append(expected,{a,b});
        assert(saturationResidues(pair#0,pair#1,tau,n) == expected))))
///

TEST ///
fixtures = {
    {{8,14},{21,29,32,36,37}},
    {{8,26},{29,36,48,53,61,64,68,69}},
    {{8,38},{36,45,61,68,80,85,93,96,100,101}},
    {{12,20},{20,32,53,68,77,80}},
    {{20,38},{45,77,92,120,133,157,168,188,197,213,220,232,237,245,248,252,253}}}
scan(fixtures, fixture -> (
    r = hassettIntersection toSequence fixture#0;
    assert(sort apply(hassettComponents r,c->c#"determinant") == fixture#1);
    assert verifyHassettResult(r,Classification=>true)))
r = hassettIntersection(8,24)
assert(r#"component_count" == 5 and r#"diagnostics"#"duplicate_count" == 1)
assert verifyHassettResult r
r = hassettIntersection(8,96)
classes = select(hassettComponents r,c->c#"determinant"==64)
assert(#classes == 2)
assert(hFixedIsometry(classes#0,classes#1) === null)
assert verifyHassettResult(r,Classification=>true)
///

TEST ///
g = matrix {{3,0,0},{0,2,0},{0,0,4}}
v = transpose matrix {normTwoVector g}
assert((transpose v*g*v)_(0,0) == 2)
g = hassettGram first hassettComponents hassettIntersection(8,14)
assert(normTwoVector g === null)
-- Both ordinary changes and huge shears exercise LLL preconditioning and
-- all-integer arithmetic. Every returned witness is checked directly.
scan({-7,-3,0,2,9,10^30}, k -> (
    u = matrix {{1,k,-2*k},{0,1,k},{0,0,1}};
    changed = changeHassettBasis(g,u);
    assert(normTwoVector changed === null);
    s = hFixedIsometry(g,changed,MaxWork=>null,TimeLimit=>30);
    assert(s =!= null and abs det s == 1);
    assert(transpose s*hassettGram changed*s == g);
    assert(flatten entries s_{0} == {1,0,0});
    back = hFixedIsometry(changed,g,MaxWork=>null,TimeLimit=>30);
    assert(transpose back*g*back == hassettGram changed);
    assert((latticeK3Association changed)#"admissible" ==
        (latticeK3Association g)#"admissible")))
assert((try hassettLattice matrix {{3,0,0},{0,3,0},{0,0,3}} else null) === null)
assert((try changeHassettBasis(g,2*id_(ZZ^3)) else null) === null)
inv = hassettInvariants g
assert(product inv#"discriminant_group" == det g)
marks = primitiveHassettMarkings(g,100)
assert(any(marks,m->m#"discriminant"==14 and m#"admissible"))
scan(marks,m->(
    assert(gcd drop(m#"vector",1) == 1);
    assert(det m#"gram" == m#"discriminant")))
-- Independent box: Schur inverse diagonal bounds for this particular Gram.
h = matrix {{8,-7},{-7,14}}
expected = {}
for y from -5 to 5 do for z from -4 to 4 do (
    d = 8*y^2-14*y*z+14*z^2;
    if (y>0 or (y==0 and z>0)) and gcd(y,z)==1 and
        d<=100 and validHassettDiscriminant d then expected=append(expected,{d,y,z}))
assert(apply(marks,m->{m#"discriminant",m#"vector"#1,m#"vector"#2}) == sort expected)
assert((k3Witness(g,100))#"admissible")
assert(k3Witness(g,7) === null)
assert((latticeK3Association matrix {{3,0,0},{0,4,0},{0,0,4}})#"admissible" == false)
///

TEST ///
needsPackage "JSON"
r = hassettIntersection(12,20)
assert(instance((hassettResultData r)#"diagnostics"#"elapsed_seconds",RR))
directory = temporaryFileName() | "/"
makeDirectory directory
filename = directory | "quote ' ; dollar $ and spaces.json.gz"
writeHassettResult(filename,r)
s = readHassettResult(filename,Classification=>true)
assert(hassettResultData(s,Timing=>false) === hassettResultData(r,Timing=>false))
-- Core get/open interprets leading ! as a pipe; our file APIs must not.
previousDirectory = currentDirectory()
changeDirectory directory
literal = "!touch HASSETT-UNEXPECTED-COMMAND"
writeHassettResult(literal,r)
assert(fileExists("./" | literal))
assert(not fileExists "HASSETT-UNEXPECTED-COMMAND")
assert verifyHassettResult readHassettResult literal
changeDirectory previousDirectory
-- Jansson rejects this integer: the package must use JSON's exact fallback.
data = new MutableHashTable from pairs r
diag = new MutableHashTable from pairs r#"diagnostics"
diag#"large_integer" = 10^100+123
data#"diagnostics" = new HashTable from pairs diag
writeHassettResult(filename,new HashTable from pairs data)
assert((readHassettResult filename)#"diagnostics"#"large_integer" == 10^100+123)
data#"component_count" = 999
assert((try verifyHassettResult new HashTable from pairs data else null) === null)
data = new MutableHashTable from pairs r
cs = r#"components"
c = new MutableHashTable from pairs first cs
origins = c#"origins"
origin = new MutableHashTable from pairs first origins
origin#"embedding" = id_(ZZ^3)
-- Pick a proper saturation, so the identity cannot certify the inclusion.
c = first select(cs,c->any(c#"origins",o->o#"index">1))
origin = new MutableHashTable from pairs first c#"origins"
origin#"embedding" = 2*origin#"embedding"
changed = new MutableHashTable from pairs c
changed#"origins" = prepend(new HashTable from pairs origin,drop(c#"origins",1))
data#"components" = apply(cs,x->if x#"id"==c#"id" then new HashTable from pairs changed else x)
assert((try verifyHassettResult new HashTable from pairs data else null) === null)
///

TEST ///
needsPackage "JSON"
directory = temporaryFileName() | "/"
i = buildHassettCatalogue(directory,20,StopAfter=>2,CheckpointEvery=>1)
assert(not i#"complete" and i#"pair_count" == 2)
i = buildHassettCatalogue(directory,20,Classification=>true)
assert(i#"complete" and i#"pair_count" == 10)
state = fromJSON get(directory | "run-state.json")
assert(state#"reused_this_run" == 2)
damaged = directory | (first i#"pairs")#"path"
damaged << "not gzip" << close
i = buildHassettCatalogue(directory,20)
assert(i#"complete")
assert((fromJSON get(directory | "run-state.json"))#"invalid_existing_files" == 1)
limited = temporaryFileName() | "/"
i = buildHassettCatalogue(limited,14,MaxWork=>1)
assert(not i#"complete" and i#"failed_pair_count" == 3 and i#"pair_count" == 0)
i = buildHassettCatalogue(limited,14)
assert(i#"complete")
assert((try buildHassettCatalogue(directory,14) else null) === null)
assert((try buildHassettCatalogue(directory,20,Compressed=>false) else null) === null)
empty = buildHassettCatalogue(temporaryFileName() | "/",8)
assert(empty#"complete" and empty#"pair_count" == 0)
///
