-- Development integration: native certificates for the small embedded catalogue.
path = prepend(currentFileDirectory, path);
needsPackage "HassettLattices";
needsPackage "JSON";
args = drop(scriptCommandLine,1);
if #args != 2 then error "expected embedded catalogue and absolute output path";
if substring(0,1,args#0) != "/" or substring(0,1,args#1) != "/" then error "expected absolute file paths";
data = fromJSON get args#0;
plain = x -> (
    if instance(x,Matrix) then entries x
    else if instance(x,HashTable) then applyValues(x,plain)
    else if instance(x,List) then apply(x,plain) else x);
records = flatten apply(data#"pairs", r -> apply(r#"components", c ->
    new HashTable from {"id" => c#"id", "gram" => c#"gram",
        "certificate" => plain k3Certificate matrix c#"gram"}));
args#1 << toJSON(records,Sort=>true) << close;
print("Exported " | toString(#records) | " native Macaulay2 K3 certificates.");
