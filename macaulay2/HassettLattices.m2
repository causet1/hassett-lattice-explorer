-- SPDX-License-Identifier: MIT
newPackage("HassettLattices",
    Version => "0.1.0",
    Date => "November 14, 2026",
    Authors => {{Name => "Michael R. Zeng",
        HomePage => "https://github.com/causet1/hassett-lattice-explorer"}},
    Headline => "exact intersections of Hassett divisors",
    HomePage => "https://github.com/causet1/hassett-lattice-explorer",
    Keywords => {"Algebraic Geometry", "Algebraic Number Theory"},
    PackageImports => {"LLLBases", "JSON", "Parsing", "ForeignFunctions"},
    AuxiliaryFiles => true,
    DebuggingMode => false)

if take(join(apply(separate("\\.", version#"VERSION"), value), {0,0,0}),3) <
    {1,26,5} then error "HassettLattices requires Macaulay2 1.26.05 or later"

export {
    "k3Certificate",
    "MarkedHassettLattice", "HassettResult", "HassettResourceLimitError", "hassettLattice",
    "hassettGram", "hassettDiscriminant", "hassettComponents",
    "validHassettDiscriminant", "validHassettDiscriminants",
    "admissibleHassettDiscriminant", "normalizeHassettPair",
    "positiveHassettParameters", "hassettBaseGram", "saturationIndices",
    "saturationResidues", "hassettIntersection", "changeHassettBasis",
    "normTwoVector", "hFixedIsometry", "latticeK3Association",
    "primitiveHassettMarkings", "k3Witness", "hassettInvariants",
    "verifyHassettResult", "hassettResultData", "readHassettResult",
    "writeHassettResult", "hassettCatalogueSummary", "buildHassettCatalogue",
    "MaxWork", "TimeLimit", "Classification", "Timing", "AdmissibleOnly",
    "Compressed", "Resume", "StopAfter", "CheckpointEvery"
    }

load "./HassettLattices/arithmetic.m2"
load "./HassettLattices/lattices.m2"
load "./HassettLattices/intersection.m2"
load "./HassettLattices/certificates.m2"
load "./HassettLattices/catalogue.m2"

beginDocumentation()
load "./HassettLattices/documentation.m2"
load "./HassettLattices/tests.m2"

end--of package
