-- SPDX-License-Identifier: MIT
path = prepend(currentFileDirectory, path);
needsPackage "HassettLattices";
args = drop(scriptCommandLine,1);
if #args != 2 then error "expected output directory and maximum discriminant";
if not match("^[0-9]+$",args#1) then error "invalid bound";
catalogue = buildHassettCatalogue(args#0,value args#1,Resume=>false,TimeLimit=>180);
assert catalogue#"complete";
scan({{8,96},{446,494},{456,488},{498,500}}, pair -> (
    r := hassettIntersection(pair#0,pair#1,TimeLimit=>180);
    assert verifyHassettResult(r,TimeLimit=>180);
    writeHassettResult(args#0 | "/stress/" | toString pair#0 | "-" |
        toString pair#1 | ".json.gz",r)));
print("Macaulay2 " | version#"VERSION" | ": catalogue and stress certificates complete");
