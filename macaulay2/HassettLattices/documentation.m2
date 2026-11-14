-- SPDX-License-Identifier: MIT
doc ///
  Key
    HassettLattices
  Headline
    exact reduced components of intersections of Hassett divisors
  Description
    Text
      Implements Yang--Yu Algorithm 7.6 for distinct labels greater than six
      and congruent to zero or two modulo six. The answer includes every
      retained saturation construction and exact integral certificates.
      Deduplication fixes the distinguished vector of square three.
      Scheme multiplicities and rationality are not computed.
    Example
      r = hassettIntersection(12,20)
      sort apply(hassettComponents r, c -> c#"determinant")
      verifyHassettResult(r, Classification => true)
    Text
      Arithmetic and matrix operations reuse Macaulay2's ZZ/QQ backend.
      GMP square roots are called through ForeignFunctions. LLLBases supplies
      an exact unimodular preconditioner; the rank-three marked enumeration
      and the saturation bookkeeping are specific to this algorithm.
      JSON handles serialization. No Python or Julia runtime is required.
      Requires Macaulay2 1.26.05 or later with libffi and GMP symbols available,
      on Linux or macOS. Gzip files require gzip; catalogue hashes require
      sha256sum or shasum. Search limits are cooperative.
    Text
      Mathematical reference:
      @HREF{"https://arxiv.org/abs/2103.09132", "Yang and Yu, On lattice polarized cubic fourfolds"}@.
      Source, installation instructions, independent validation, and CLI:
      @HREF{"https://github.com/causet1/hassett-lattice-explorer", "Hassett Lattice Explorer"}@.
  Subnodes
    hassettIntersection
    MarkedHassettLattice
    hassettLattice
    validHassettDiscriminant
    saturationIndices
    changeHassettBasis
    latticeK3Association
    hassettInvariants
    verifyHassettResult
    readHassettResult
    buildHassettCatalogue
    MaxWork
///

doc ///
  Key
    hassettIntersection
    (hassettIntersection, ZZ, ZZ)
  Headline
    enumerate the complete reduced intersection
  Usage
    hassettIntersection(d1,d2)
  Inputs
    d1:ZZ
    d2:ZZ
  Outputs
    :HassettResult
  Description
    Text
      Labels must be distinct valid Hassett discriminants. Mixed congruence
      pairs put the label congruent to two first; other pairs are ascending.
      All index-one origins precede proper saturations, giving stable IDs.
      Components are immutable hash tables containing a ZZ Gram matrix,
      determinant, K3 association, and all construction origins. Every origin
      records tau, index, residues a,b, base and overlattice Gram matrices,
      an h-fixed basis map to the representative, and an inclusion matrix.
      Coordinates are columns: E^t G E is the base Gram matrix and
      U^t G U is the constructed overlattice. Both original rank-two markings
      are primitive; their sum need not be saturated.
    Example
      r = hassettIntersection(8,24)
      r#"diagnostics"#"duplicate_count"
      c = first select(hassettComponents r,c->c#"determinant"==16);
      apply(c#"origins", o -> {o#"tau",o#"index"})
  SeeAlso
    MaxWork
    verifyHassettResult
///

doc ///
  Key
    MarkedHassettLattice
    HassettResult
  Headline
    native marked lattices and completed results
  Description
    Text
      Both are immutable HashTable subclasses. A MarkedHassettLattice stores
      its ZZ matrix under the string key "gram". Its constructor validates
      positivity, symmetry, rank three, square three for the first vector,
      and the distinguished-class parity condition. HassettResult contains
      schema 1.0 fields with native matrices. Use hassettResultData for JSON
      arrays, or hassettComponents to access component records. Result
      records are transparent research data: verify externally modified data
      before trusting it. Resource exhaustion never returns a partial result.
///

doc ///
  Key
    hassettLattice
    hassettGram
    hassettDiscriminant
    hassettComponents
  Headline
    construct and inspect marked lattice data
  Description
    Text
      hassettLattice accepts a 3 by 3 ZZ matrix, a nested integer list, a
      component record, or a marked lattice. hassettGram returns its matrix;
      hassettDiscriminant returns its determinant. This determinant is the
      rank-three lattice discriminant, not a Hassett divisor label.
      hassettComponents returns the component list of a completed result.
    Example
      l = hassettLattice matrix {{3,1,1},{1,3,0},{1,0,5}}
      hassettGram l
      hassettDiscriminant l
///

doc ///
  Key
    validHassettDiscriminant
    validHassettDiscriminants
    admissibleHassettDiscriminant
    (admissibleHassettDiscriminant, Thing)
    normalizeHassettPair
    positiveHassettParameters
    hassettBaseGram
  Headline
    labels and the exact starting-parameter interval
  Description
    Text
      validHassettDiscriminant(d) tests that d is an integer greater than six
      congruent to zero or two modulo six. validHassettDiscriminants(bound)
      lists those labels through a nonnegative bound.
      admissibleHassettDiscriminant(d) additionally applies the untwisted K3
      arithmetic condition: no divisibility by four, nine, or an odd prime
      congruent to two modulo three. Factorization reuses Core.
      normalizeHassettPair(d1,d2) returns the algorithm's ordering.
      positiveHassettParameters(d1,d2) lists all positive-definite starting
      parameters, including negative parameters in the two/two case.
      hassettBaseGram(d1,d2,tau) constructs the corresponding integral matrix;
      this helper does not assert positivity for an arbitrary tau.
    Example
      validHassettDiscriminants 20
      admissibleHassettDiscriminant 14
      normalizeHassettPair(12,20)
      positiveHassettParameters(8,14)
      hassettBaseGram(8,14,0)
///

doc ///
  Key
    saturationIndices
    (saturationIndices, ZZ)
    saturationResidues
    (saturationResidues, ZZ, ZZ, ZZ, ZZ)
  Headline
    enumerate possible saturation indices and residues
  Description
    Text
      saturationIndices(det) returns every positive n with n squared dividing
      the positive determinant. saturationResidues(d1,d2,tau,n) returns all
      lexicographically sorted pairs a,b in [0,n) with gcd(b,n)=1 and both
      linear integrality conditions. The eliminated congruence
      d1*b = p*q-3*tau modulo n avoids a quadratic residue scan.
      Norm integrality, parity, and root-freeness are separate subsequent
      tests performed by hassettIntersection.
    Example
      saturationIndices 144
      saturationResidues(20,12,0,2)
///

doc ///
  Key
    changeHassettBasis
    normTwoVector
    (normTwoVector, Thing)
    hFixedIsometry
    (hFixedIsometry, Thing, Thing)
  Headline
    change bases and compute exact root or marked-isometry witnesses
  Description
    Text
      changeHassettBasis(l,U) requires an integral unimodular column matrix
      fixing the first basis vector; it returns the lattice with Gram U^t G U.
      normTwoVector(G) returns an integer vector of norm two, or null after a
      complete search. hFixedIsometry(source,target) returns an integral U
      with U^t target U = source, U e1 = e1, and determinant plus or minus one,
      or null after a complete search. The latter two routines accept any
      positive integral symmetric rank-three Gram with first diagonal three,
      including inputs which do not satisfy the distinguished parity test.
    Text
      Exact binary Schur bounds reduce enumeration to a quadratic square
      test. Large shears are preconditioned by LLLBases using an integral
      triangular surrogate for the Schur form; LLL reduces Euclidean columns,
      not an input Gram metric. We certify its unimodular map and enumerate
      the transformed form exactly, so no reduction heuristic decides the
      answer. Basis changes are transported back to the supplied coordinates.
    Example
      g = hassettBaseGram(8,14,0);
      u = matrix {{1,2,-1},{0,1,4},{0,0,1}};
      l = changeHassettBasis(g,u);
      s = hFixedIsometry(g,l);
      transpose s*hassettGram l*s == g
      normTwoVector matrix {{3,0,0},{0,2,0},{0,0,4}}
///

doc ///
  Key
    latticeK3Association
    (latticeK3Association, Thing)
    primitiveHassettMarkings
    (primitiveHassettMarkings, Thing, ZZ)
    k3Witness
    (k3Witness, Thing, ZZ)
    k3Certificate
    (k3Certificate, Thing)
    AdmissibleOnly
  Headline
    whole-lattice K3 decisions and bounded primitive markings
  Description
    Text
      latticeK3Association(l) applies Yang--Yu Theorems 8.8--8.9, including
      the additional modulo-three condition when h splits orthogonally.
      It returns the binary discriminant form, its content and primitive
      part, split flag, modulo-three witness, obstructions, and decision.
      This is an untwisted K3 criterion, not a rationality decision.
    Text
      primitiveHassettMarkings(l,bound) lists all primitive rank-two markings
      through h whose valid label is at most bound, modulo sign and addition
      of h. Each record contains discriminant, vector (0,y,z), rank-two Gram,
      and admissibility. AdmissibleOnly => true filters this list.
      k3Witness(l,bound) returns its first admissible marking or null.
      A null bounded witness does not negate the whole-lattice criterion.
      k3Certificate(l) returns association, witness, and search_bound.
      A positive result includes an explicit primitive admissible marking;
      a negative result has null witness and exact arithmetic obstructions.
      Positive searches double their bound with one shared work/time budget.
      Exhausting that budget raises HassettResourceLimitError.
    Example
      l = hassettLattice hassettBaseGram(8,14,0);
      (latticeK3Association l)#"admissible"
      k3Witness(l,50)
      apply(primitiveHassettMarkings(l,30),m->m#"discriminant")
///

doc ///
  Key
    hassettInvariants
    (hassettInvariants, Thing)
  Headline
    determinant, discriminant group, divisibility, and K3 data
  Description
    Text
      hassettInvariants(l) returns rank, determinant, nontrivial positive
      Smith factors of the discriminant group, divisibility of h, and the
      whole-lattice K3 criterion. Smith normal form reuses Core.
    Example
      hassettInvariants hassettLattice hassettBaseGram(8,14,0)
///

doc ///
  Key
    verifyHassettResult
    (verifyHassettResult, HashTable)
    Classification
  Headline
    verify integral certificates and optionally rerun classification
  Description
    Text
      verifyHassettResult(r) checks exact Gram identities, positivity,
      distinguished parity, root-freeness, primitive markings, origin
      uniqueness, starting-parameter coverage, counts, and K3 decisions.
      Native records and decoded JSON hash tables are accepted.
      Returns true or raises an error; interrupted checks never succeed.
    Text
      Classification => true also re-enumerates all admissible origins and
      compares their entire partition and representative h-isometry classes.
      The same budget covers checking and re-enumeration. Certificate checks
      alone do not establish saturation completeness or pairwise nonisometry.
      The repository's Python validation tool provides an independent
      implementation and exhaustive small-case classification audit.
///

doc ///
  Key
    hassettResultData
    (hassettResultData, HashTable)
    readHassettResult
    (readHassettResult, String)
    writeHassettResult
    (writeHassettResult, String, HashTable)
    Timing
  Headline
    exact portable JSON and gzip certificates
  Description
    Text
      hassettResultData(r) converts native matrices to nested arrays in
      schema 1.0. Timing => false removes nondeterministic elapsed time.
      writeHassettResult(filename,r) writes atomically; a .gz suffix selects
      deterministic gzip. Timing defaults to false for writing.
      readHassettResult(filename) decodes exact integers and verifies every
      certificate before returning a HassettResult. Classification => true
      requests the additional complete re-enumeration check.
    Text
      JSON's published Parsing fallback preserves integers beyond Jansson's
      64-bit range. A private encoder wrapper supplies the leading zero for
      subunit reals required by JSON syntax. Integer mathematical data never
      pass through floating point. File replacement uses POSIX rename;
      shell filenames for gzip and hashing are quoted as literal arguments.
    Example
      filename = temporaryFileName() | ".json.gz";
      writeHassettResult(filename,hassettIntersection(8,14));
      readHassettResult filename
///

doc ///
  Key
    hassettCatalogueSummary
    buildHassettCatalogue
    (buildHassettCatalogue, String, ZZ)
    Compressed
    Resume
    StopAfter
    CheckpointEvery
  Headline
    resumable sharded catalogues compatible with the explorer
  Description
    Text
      hassettCatalogueSummary(r) returns component, origin, determinant,
      saturation, and K3 counts for one pair. buildHassettCatalogue(dir,bound)
      writes every distinct unordered label pair through bound as atomic
      schema 1.0 shards, with a schema 1.1 index, SHA-256 checksums, aggregate
      statistics, publication fixtures, failure ledger, and run state.
      Compressed defaults to true. Resume defaults to true: existing shards
      are certificate-checked and invalid files are recomputed. Classification
      also re-enumerates reused shards. Limits apply separately to each pair.
    Text
      StopAfter => n stops after n processed pairs, including reuse.
      CheckpointEvery => n controls index checkpoints (default ten).
      Interrupted runs and resource failures remain explicitly incomplete;
      rerun to resume. Existing pair files outside the requested bound or
      compression mode are refused. Use one writer per directory.
      Totals count component records across pairs, not globally distinct loci.
    Example
      directory = temporaryFileName() | "/";
      i = buildHassettCatalogue(directory,14,StopAfter=>1);
      i#"complete"
      i = buildHassettCatalogue(directory,14);
      i#"complete"
      i#"statistics"#"total_components"
///

doc ///
  Key
    MaxWork
    TimeLimit
    HassettResourceLimitError
  Headline
    cooperative search limits with explicit failure
  Description
    Text
      MaxWork defaults to 5000000 application iterations or backend calls.
      TimeLimit defaults to 60 elapsed seconds, measured by a monotonic clock.
      Either may be null to disable that limit. Values must otherwise be
      positive; MaxWork must be integral and TimeLimit finite.
      The budget counts application work, not GMP/NTL instructions.
      Backend calls are checked before and after and cannot be interrupted
      mid-call. Exceeding either bound raises HassettResourceLimitError and never returns a
      partial intersection or a successful incomplete verification.
///

-- Native help generates links to every (method, option) node. Document those
-- nodes explicitly, sharing the main option explanations above.
scan({admissibleHassettDiscriminant, saturationIndices, saturationResidues,
    hassettIntersection, normTwoVector, hFixedIsometry, latticeK3Association,
    primitiveHassettMarkings, k3Witness, k3Certificate, hassettInvariants, verifyHassettResult,
    readHassettResult, buildHassettCatalogue}, f -> (
    document {Key => [f,MaxWork], Headline => "limit application work",
        "Maximum application iterations/backend calls, or null. See ", TO MaxWork, "."};
    document {Key => [f,TimeLimit], Headline => "limit elapsed search time",
        "Cooperative monotonic elapsed-time bound in seconds, or null. See ", TO TimeLimit, "."}))
scan({verifyHassettResult,readHassettResult,buildHassettCatalogue}, f ->
    document {Key => [f,Classification], Headline => "rerun complete classification",
        "Also re-enumerate origins and compare marked classes. See ", TO Classification, "."})
scan({hassettResultData,writeHassettResult}, f ->
    document {Key => [f,Timing], Headline => "include elapsed timing in output",
        "Include elapsed time when true. See ", TO Timing, "."})
document {Key => [primitiveHassettMarkings,AdmissibleOnly],
    Headline => "retain only admissible labels", "See ", TO AdmissibleOnly, "."}
scan({Compressed,Resume,StopAfter,CheckpointEvery}, opt ->
    document {Key => [buildHassettCatalogue,opt], Headline => "control catalogue generation",
        "See ", TO opt, " and ", TO buildHassettCatalogue, "."})
