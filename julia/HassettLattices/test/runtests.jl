using Test
using Random
using HassettLattices
import Nemo
import Hecke
import JSON
import Aqua

const ZZ = Nemo.ZZ
const UNLIMITED = Limits(; max_work = nothing, timeout_seconds = nothing)

@testset "HassettLattices" begin
  @testset "Input and arithmetic" begin
    @test valid_discriminants(20) == [8, 12, 14, 18, 20]
    @test normalize_pair(12, 8) == (8, 12)
    @test normalize_pair(20, 14) == (14, 20)
    for d in (true, 8.0, 6, -8, 9)
      @test !valid_discriminant(d)
      @test_throws ArgumentError intersection_components(d, 14)
    end
    @test_throws ArgumentError intersection_components(8, 8)
    @test_throws ArgumentError Limits(; max_work = true)
    @test_throws ArgumentError Limits(; timeout_seconds = NaN)
    @test_throws ArgumentError saturation_indices(0)
    @test_throws ArgumentError saturation_residues(8, 14, 0, 0)
    @test saturation_indices(144) == [1, 2, 3, 4, 6, 12]
    @test all(admissible_discriminant, [14, 26, 38, 42, 62, 74, 78])
    @test all(
      !admissible_discriminant(d) for d in [6, 8, 12, 18, 20, 30, 44, 50, 54]
    )
    # Independent exhaustive residue boxes, especially noninvertible 3 mod n.
    for (d1, d2) in [(8, 14), (8, 12), (12, 18), (30, 54)]
      p, q = Int(d1 % 6 == 2), Int(d2 % 6 == 2)
      aa = div(d1 + p, 3)
      for tau in -5:5, n in 1:24
        expected = [
          (a, b) for a in 0:(n - 1) for b in 0:(n - 1) if gcd(b, n) == 1 &&
            mod(3a + p * b + q, n) == 0 &&
            mod(p * a + aa * b + tau, n) == 0
        ]
        @test saturation_residues(d1, d2, tau, n) == expected
      end
    end
  end

  @testset "Published classifications and certificates" begin
    for (pair, (_, _, determinants)) in HassettLattices.PUBLISHED
      r = intersection_components(pair...; limits = UNLIMITED)
      @test sort([discriminant(c) for c in r]) == determinants
      @test verify_result(r; classification = true, limits = UNLIMITED)
      swapped = intersection_components(reverse(pair)...; limits = UNLIMITED)
      @test [gram_matrix(c) for c in r] == [gram_matrix(c) for c in swapped]
      @test component_count(r) == length(components(r)) == length(r)
      @test eltype(r) == Component
    end
    r = intersection_components(8, 24)
    c = only(filter(c -> discriminant(c) == 16, components(r)))
    @test Set((o.tau, o.index) for o in origins(c)) == Set([(4, 1), (0, 2)])
    same_det = filter(
      c -> discriminant(c) == 64,
      components(intersection_components(8, 96)),
    )
    @test length(same_det) == 2
    @test h_fixed_isometry(
      gram_matrix(same_det[1]),
      gram_matrix(same_det[2]),
    ) === nothing
    @test_throws ResourceLimitError intersection_components(
      8,
      14;
      limits = Limits(; max_work = 1),
    )
    @test_throws ResourceLimitError intersection_components(
      8,
      14;
      limits = Limits(; timeout_seconds = 1e-12),
    )
  end

  @testset "Hecke interoperation, marked bases and K3" begin
    boundary = ZZ[3 0 0; 0 2 0; 0 0 4]
    witness = norm_two_vector(boundary)
    @test witness !== nothing
    column = Nemo.matrix(ZZ, 3, 1, witness)
    @test (transpose(column) * boundary * column)[1, 1] == 2
    @test norm_two_vector(ZZ[3 0 0; 0 3 0; 0 0 3]) === nothing
    rng = MersenneTwister(20261114)
    gs = [ZZ[3 0 0; 0 4 0; 0 0 6], ZZ[3 0 0; 0 4 0; 0 0 10]]
    append!(gs, [gram_matrix(c) for c in intersection_components(8, 12)])
    @test !lattice_k3_association(gs[1]).admissible
    @test lattice_k3_association(gs[2]).admissible
    for g in gs
      l = MarkedLattice(g)
      @test rank(l) == 3
      @test Hecke.gram_matrix(hecke_lattice(l)) == g
      copy = gram_matrix(l)
      copy[1, 1] = 999
      @test gram_matrix(l)[1, 1] == 3
      invs = lattice_invariants(l)
      @test prod(invs.discriminant_group; init = ZZ(1)) == discriminant(l)
      for _ in 1:12
        a, b, c, d = rand(rng, -2:2, 4)
        u = ZZ[1 a b; 0 1 c; 0 d 1 + c * d]
        changed = change_basis(l, u)
        iso = h_fixed_isometry(changed, l; limits = UNLIMITED)
        @test iso !== nothing
        @test transpose(iso) * g * iso == gram_matrix(changed)
        @test iso[:, 1] == Nemo.ZZRingElem[1, 0, 0]
        @test abs(Nemo.det(iso)) == 1
        @test norm_two_vector(changed) === nothing
        @test lattice_k3_association(changed).admissible ==
              lattice_k3_association(l).admissible
      end
    end
    l = intersection_components(8, 14)[1]
    markings = primitive_markings(l, 100)
    @test all(
      m.discriminant <= 100 && gcd(m.vector[2], m.vector[3]) == 1 for
      m in markings
    )
    @test Set([ZZ(8), ZZ(14)]) <= Set(m.discriminant for m in markings)
    # Independent binary box bounds suffice here; compare every primitive marking.
    g = gram_matrix(l)
    expected = Set{Tuple{BigInt, Int, Int}}()
    for y in -10:10, z in -10:10
      (y > 0 || (y == 0 && z > 0)) && gcd(y, z) == 1 || continue
      d =
        3 * (g[2, 2] * y^2 + 2 * g[2, 3] * y * z + g[3, 3] * z^2) -
        (g[1, 2] * y + g[1, 3] * z)^2
      valid_discriminant(d) && d <= 100 && push!(expected, (BigInt(d), y, z))
    end
    @test Set(
      (BigInt(m.discriminant), Int(m.vector[2]), Int(m.vector[3])) for
      m in markings
    ) == expected
    @test k3_witness(l, 100).admissible
    @test k3_witness(l, 7) === nothing
    @test_throws ArgumentError MarkedLattice([3 0 0; 0 3 0; 0 0 4])
    @test_throws ArgumentError change_basis(l, [1 0 0; 0 2 0; 0 0 1])
  end

  @testset "Persistence, corruption and exact integers" begin
    r = intersection_components(12, 20)
    mktempdir() do directory
      for suffix in (".json", ".json.gz")
        path = joinpath(directory, "pair" * suffix)
        write_result(path, r)
        restored = read_result(path; classification = true, limits = UNLIMITED)
        @test result_dict(restored; timing = false) ==
              result_dict(r; timing = false)
        old = read(path)
        write_result(path, r)
        @test read(path) == old
      end
      path = joinpath(directory, "bad.json")
      for mutate in (
        d -> d["components"][1]["determinant"] += 1,
        d -> pop!(d["candidates"]),
        d -> d["complete"] = false,
        d -> d["components"][1]["origins"][1]["embedding"][3][3] += 1,
        d ->
          d["components"][1]["k3_association"]["admissible"] =
            !d["components"][1]["k3_association"]["admissible"],
      )
        data = result_dict(r)
        mutate(data)
        write(path, JSON.json(data))
        @test_throws VerificationError read_result(path)
      end
      huge = big(10)^40
      @test JSON.parse(JSON.json(Dict("n" => huge)))["n"] == huge
      @test HassettLattices.json_value(ZZ(huge)) == huge
      changed = change_basis(r[1], [big(1) huge 0; 0 1 0; 0 0 1])
      @test discriminant(changed) == discriminant(r[1])
      # Exercise the package's complete JSON path with Gram entries beyond Int64.
      inverse = ZZ[1 -huge 0; 0 1 0; 0 0 1]
      c = r[1]
      os = [
        ConstructionOrigin(
          o.tau,
          o.index,
          o.a,
          o.b,
          o.base_gram,
          o.overlattice_gram,
          inverse * o.basis_map_to_representative,
          inverse * o.embedding,
        ) for o in origins(c)
      ]
      cs = copy(components(r))
      cs[1] = Component(
        c.id,
        changed,
        c.determinant,
        os,
        lattice_k3_association(changed),
      )
      large = IntersectionResult(
        r.input_pair,
        r.pair,
        cs,
        r.candidates,
        r.diagnostics,
      )
      path = joinpath(directory, "large.json")
      write_result(path, large)
      @test gram_matrix(read_result(path; limits = UNLIMITED)[1]) ==
            gram_matrix(changed)

      # Valid remaining certificates alone do not prove complete enumeration.
      incomplete = result_dict(r)
      removed = pop!(incomplete["components"])
      @test removed["determinant"] == 20
      incomplete["component_count"] -= 1
      incomplete["diagnostics"]["accepted_marked_lattices"] -= 1
      tau = only(removed["origins"])["tau"]
      only(filter(c -> c["tau"] == tau, incomplete["candidates"]))["accepted_overlattices"] -=
        1
      path = joinpath(directory, "incomplete.json")
      write(path, JSON.json(incomplete))
      @test length(read_result(path)) == 5
      @test_throws VerificationError read_result(path; classification = true)
    end
  end

  @testset "Resumable catalogues and CLI" begin
    mktempdir() do directory
      partial = build_catalogue(directory, 14; stop_after = 1)
      @test !partial["complete"] && partial["pair_count"] == 1
      complete = build_catalogue(directory, 14)
      @test complete["complete"] && complete["pair_count"] == 3
      original = read(joinpath(directory, "catalogue-index.json"))
      @test build_catalogue(directory, 14; recheck_classification = true)["complete"]
      @test read(joinpath(directory, "catalogue-index.json")) == original
      path = joinpath(directory, "pairs", "8-14.json.gz")
      write(path, "corrupt")
      @test build_catalogue(directory, 14)["complete"]
      @test read(joinpath(directory, "catalogue-index.json")) == original
      @test JSON.parsefile(joinpath(directory, "run-state.json"))["invalid_existing_files"] ==
            1
      low_budget =
        build_catalogue(directory, 14; limits = Limits(; max_work = 1))
      @test !low_budget["complete"] && low_budget["failed_pair_count"] == 3
      @test build_catalogue(directory, 14)["complete"]
      @test_throws ArgumentError build_catalogue(directory, 12)
      io, errors = IOBuffer(), IOBuffer()
      @test main(
        ["verify", path, "--classification"];
        out = io,
        err = errors,
      ) == 0
      @test JSON.parse(String(take!(io)))["verified"]
      @test main(
        ["intersect", "8", "14", "--max-work", "1"];
        out = io,
        err = errors,
      ) == 2
      @test isempty(take!(io))
      @test occursin("limit", String(take!(errors)))
      @test main(["admissible", "14"]; out = io, err = errors) == 0
      @test JSON.parse(String(take!(io)))["admissible"]
    end
    mktempdir() do directory
      failed = build_catalogue(directory, 12; limits = Limits(; max_work = 1))
      @test !failed["complete"] && failed["failed_pair_count"] == 1
      @test build_catalogue(directory, 12)["complete"]
    end
  end

  @testset "Package quality" begin
    Aqua.test_all(HassettLattices; ambiguities = false)
    # Dependencies have their own cross-package ambiguities; check our methods.
    @test isempty(Test.detect_ambiguities(HassettLattices; recursive = true))
  end
end
