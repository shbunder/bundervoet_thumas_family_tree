"""The parts that are load-bearing and silent when they break.

A misread record does not raise — it produces a person with a missing field, and that
surfaces months later as a hole in the tree. Same for the date grammar and the scoring:
both fail by being quietly wrong rather than by stopping. These are the cases worth
pinning.

    uv run --group dev pytest
"""

from __future__ import annotations

import pytest

from familytree import frontmatter
from familytree.match import Candidate, block_keys, compare, given_keys, phonetic
from familytree.people import (
    census, family_key, format_date, given_names, is_valid_date, point_year, year_of,
)


# ---------- frontmatter ----------


def test_parses_the_shapes_records_use():
    data, body = frontmatter.parse(
        "---\n"
        "id: anna_vc\n"
        "name: Anna Van Craenenbroeck\n"
        "birth:\n"
        "  date: 1937-01-04\n"
        "  place: Zaventem\n"
        "spouses:\n"
        "  - id: rene_j\n"
        "    name: René Janssens\n"
        "sources:\n"
        "  - tree-cisken\n"
        "  - family\n"
        "---\n"
        "\nThe prose body.\n"
    )
    assert data["id"] == "anna_vc"
    assert data["birth"] == {"date": "1937-01-04", "place": "Zaventem"}
    assert data["spouses"] == [{"id": "rene_j", "name": "René Janssens"}]
    assert data["sources"] == ["tree-cisken", "family"]
    assert body == "The prose body."


@pytest.mark.parametrize("text,fragment", [
    ("name: no fence\n", "does not start with"),
    ("---\nname: x\n", "never closed"),
    ("---\nname\n---\n", 'not "key: value"'),
    ("---\n  orphan: 1\n---\n", "belongs to nothing"),
    ("---\nbirth:\n---\n", "no value and no indented block"),
])
def test_refuses_rather_than_guesses(text, fragment):
    """A parser that guesses is worse than no parser: it lets a malformed record
    through, and the mistake surfaces as a missing person months later."""
    with pytest.raises(frontmatter.FrontmatterError, match=fragment):
        frontmatter.parse(text)


def test_round_trips_through_stringify():
    original = "---\nid: x\nname: Jan Van den Broucke\nbirth:\n  date: 1876\n---\n\nNote.\n"
    data, body = frontmatter.parse(original)
    assert frontmatter.parse(frontmatter.stringify(data, body, ["id", "name", "birth"])) == (data, body)


# ---------- the date grammar ----------


@pytest.mark.parametrize("value", ["1876-11-12", "1876-11", "1876", "~1682", "<1727", ">1900", "1575..1587"])
def test_accepts_the_whole_grammar(value):
    assert is_valid_date(value)


@pytest.mark.parametrize("value", ["probably March 1876", "1876-3-1", "March 1876", "18760101", ""])
def test_rejects_everything_else(value):
    """There is deliberately no syntax for a guess, because a format for one is an
    invitation to record one."""
    assert not is_valid_date(value)


def test_formats_for_display_only():
    assert format_date("1876-11-12") == "12 Nov 1876"
    assert format_date("~1682") == "~1682"
    assert format_date("<1727") == "before 1727"
    assert format_date("1575..1587") == "1575–1587"


def test_year_of_reads_every_form():
    assert [year_of(v) for v in ("1876-11-12", "~1682", "<1727", "1575..1587", None)] == [1876, 1682, 1727, 1575, None]


# ---------- names ----------


def test_given_names_removes_a_stated_surname_wherever_it_sits():
    assert given_names({"name": "Jan Van den Broucke", "surname": "Van den Broucke"}) == "Jan"
    # The surname is not always last: this one ends with a variant spelling.
    assert given_names({"name": "Marie Quinart (Kinart)", "surname": "Quinart"}) == "Marie (Kinart)"


def test_family_key_folds_spacing_and_accents_but_not_spelling():
    assert family_key("De Keyser") == family_key("Dekeyser")
    assert family_key("Van den Broucke") != family_key("Vandenberghe")


# ---------- phonetics ----------


@pytest.mark.parametrize("a,b", [
    ("Bostyn", "Bostin"),
    ("De Keyser", "Dekeyser"),
    ("Stroobandt", "Strobant"),
    ("Devriendt", "De Vriendt"),
    ("Van Craenenbroeck", "Vancranenbroek"),
])
def test_folds_the_variants_this_tree_actually_contains(a, b):
    assert phonetic(a) == phonetic(b)


@pytest.mark.parametrize("a,b", [
    ("Janssens", "Jansen"),
    ("Bundervoet", "Bundervoot"),
    ("Devriendt", "Devos"),
])
def test_does_not_fold_distinct_families(a, b):
    """Over-folding merges families, and a merged family is the failure this project is
    built around. These rules stay conservative on purpose."""
    assert phonetic(a) != phonetic(b)


def test_blocking_survives_a_surname_spelled_differently():
    """The given-name pass is what catches a pair the phonetic key would miss."""
    a = Candidate(ref="a", name="Amandus Vanstechele", surname="Vanstechele", given="Amandus", birth_year=1902)
    b = Candidate(ref="b", name="Amandus Vanstechelman", surname="Vanstechelman", given="Amandus", birth_year=1902)
    assert set(block_keys(a)) & set(block_keys(b))


# ---------- scoring ----------


def _pair(**overrides):
    base = dict(surname="Bundervoet", given="Petrus Franciscus", birth_year=1879,
                birth_date="1879-03-19", places=["Evergem"], birth_place="Evergem")
    return (Candidate(ref="tree", name="a", stated_birth_year=True, **base),
            Candidate(ref="act", name="b", stated_birth_year=True, **{**base, **overrides}))


def test_a_stated_conflict_vetoes_however_much_else_agrees():
    a, b = _pair(birth_year=1901, birth_date="1901-03-19")
    m = compare(a, b)
    assert m.conflict and m.bits == 0 and m.band == "rejected" and not m.graftable


def test_sex_disagreement_vetoes():
    a, b = _pair()
    a.sex, b.sex = "m", "f"
    assert compare(a, b).band == "rejected"


def test_the_name_alone_is_never_two_identifiers():
    """Never match on name alone — enforced as a floor, not as a threshold a big score
    can climb over."""
    a = Candidate(ref="a", name="x", surname="Schalandrijn", given="Octavia")
    b = Candidate(ref="b", name="y", surname="Schalandrijn", given="Octavia")
    m = compare(a, b)
    assert m.classes == ["name"]
    assert m.distinguishing == 0
    assert not m.graftable and m.band == "noise"


def test_agreement_beyond_the_name_is_what_promotes_a_candidate():
    a, b = _pair()
    m = compare(a, b)
    assert m.independent >= 2
    assert m.distinguishing >= 12
    assert m.band == "strong" and m.graftable


def test_an_implied_birth_year_never_vetoes():
    """A year derived from an age in an act carries a year or two of slack; letting it
    veto would kill true matches."""
    a, b = _pair(birth_year=1877, birth_date=None)
    b.stated_birth_year = False
    assert not compare(a, b).conflict


def test_kin_is_an_independent_identifier():
    """The rule always named parent names as a way to satisfy "two independent
    identifiers"; until the kin class existed the scorer could not honour it, and two
    people agreeing only on a surname and a mother scored as name-alone."""
    a = Candidate(ref="a", name="x", surname="Bundervoet", given="Petrus",
                  kin=[("mother", "stockman", frozenset({"livina"}))])
    b = Candidate(ref="b", name="y", surname="Bundervoet", given="Petrus",
                  kin=[("mother", "stockman", frozenset({"livina"}))])
    m = compare(a, b)
    assert "kin" in m.classes
    assert m.independent >= 2 and m.distinguishing > 0


def test_kin_only_compares_like_with_like():
    """Matching one person's father against another's husband is precisely the error
    the two-identifier rule exists to stop."""
    a = Candidate(ref="a", name="x", surname="Bundervoet", given="Petrus",
                  kin=[("father", "", frozenset({"joannes"}))])
    b = Candidate(ref="b", name="y", surname="Bundervoet", given="Petrus",
                  kin=[("spouse", "", frozenset({"joannes"}))])
    assert "kin" not in compare(a, b).classes


@pytest.mark.parametrize("name", ["Catharina van Hecke", "Elisabeth NN"])
def test_particles_and_placeholders_are_not_forenames(name):
    """"van" is a token in a large share of Flemish names and "NN" marks a name no
    record gave. Both matched everything and scored it as agreement."""
    assert "van" not in given_keys(name)
    assert "nn" not in given_keys(name)


def test_an_implausible_lifespan_vetoes():
    """The recurring failure in this material is a forename returning every second
    generation, which grafts a grandfather onto his grandson."""
    a = Candidate(ref="a", name="x", surname="Bundervoet", given="Petrus", birth_year=1750)
    b = Candidate(ref="b", name="y", surname="Bundervoet", given="Petrus", death_year=1890)
    assert compare(a, b).band == "rejected"


# ---------- the date grammar's bounds ----------


@pytest.mark.parametrize("date,year", [
    ("1876-11-12", 1876), ("1876-11", 1876), ("1876", 1876), ("~1682", 1682),
])
def test_point_year_reads_the_dates_that_assert_one(date, year):
    assert point_year(date) == year


@pytest.mark.parametrize("date", ["<1727", ">1900", "1575..1587"])
def test_point_year_refuses_to_do_arithmetic_on_a_bound(date):
    """"<1673" bounds a birth without stating one. Treating it as a year reported a
    mother aged -6 for a record that was never in conflict with anything."""
    assert point_year(date) is None
    assert year_of(date) is not None      # still sortable, just not subtractable


# ---------- the census ----------
# Two pages state how big the tree is: the landing page has the numbers written into it
# by the build, the tree reads them from the bundle. Both come from `census`, so what is
# worth pinning is that it partitions the roster — a person counted twice, or in no
# group at all, makes a page state a number that is quietly wrong.


def _tree(**people):
    return {pid: {"id": pid, **rest} for pid, rest in people.items()}


def test_census_puts_everyone_in_exactly_one_group():
    people = _tree(
        kid={"father": "dad"},
        dad={"father": "grandad"},
        grandad={},
        aunt={"father": "grandad"},       # blood, off the direct line
        cousin={"father": "aunt"},        # blood, further off it
        inlaw={},                         # nobody's child and nobody's parent
    )
    c = census(people, {"meta": {"roots": ["kid"]}, "root": "kid"})
    assert c["ancestors"] == 2                                   # dad, grandad
    assert c["relatives"] == 3                                   # kid, aunt, cousin
    assert c["others"] == 1                                      # inlaw
    assert c["ancestors"] + c["relatives"] + c["others"] == c["total"] == len(people)


def test_census_counts_a_forest_from_every_root():
    """`roots` is a list — objective 3 expects disconnected families — so an ancestor of
    the second root is as much an ancestor as one of the first."""
    people = _tree(a={"father": "a_dad"}, a_dad={}, b={"mother": "b_mum"}, b_mum={})
    c = census(people, {"meta": {"roots": ["a", "b"]}, "root": "a"})
    assert (c["ancestors"], c["relatives"], c["others"]) == (2, 2, 0)


def test_census_dates_separate_the_oldest_from_the_oldest_documented():
    """"Documented" is a claim about evidence. The landing page said the tree was
    documented to the 1400s while the oldest act anyone had read was from 1649."""
    people = _tree(
        old={"birth": {"date": "~1440"}, "confidence": "sup"},
        read={"birth": {"date": "1649-03-07"}, "confidence": "doc"},
        recent={"birth": {"date": "1990"}, "confidence": "fam"},
    )
    c = census(people, {"meta": {"roots": ["recent"]}, "root": "recent"})
    assert c["earliest"] == 1440
    assert c["documented"] == 1649


# ---------- harvest coverage ----------
# Both of these are regressions. A partial harvest read as a complete one, and one
# surname filed under two ids, are the same class of mistake: the tools reported
# confidence they had not earned.


def _manifest(monkeypatch, harvests):
    from familytree import corpus
    monkeypatch.setattr(corpus, "load_manifest", lambda: {"harvests": harvests, "population": {"be": 1000}})


def test_a_partial_harvest_is_not_evidence_of_absence(monkeypatch):
    """5% of a surname fetched and nothing found is the corpus form of `blocked`, not
    of `miss` — the queue must not sink the frontier as though it had been searched."""
    from familytree.corpus import surname_coverage
    _manifest(monkeypatch, [
        {"id": "dekeyser", "query": {"name": "De Keyser"}, "found": 11795, "mentions": 600, "complete": False},
    ])
    assert surname_coverage("Dekeyser") == pytest.approx(600 / 11795, abs=1e-6)


def test_a_complete_harvest_reports_full_coverage(monkeypatch):
    from familytree.corpus import surname_coverage
    _manifest(monkeypatch, [
        {"id": "bundervoet", "query": {"name": "Bundervoet"}, "found": 396, "mentions": 396, "complete": True},
    ])
    assert surname_coverage("Bundervoet") == 1.0


def test_an_unharvested_surname_is_unknown_not_empty(monkeypatch):
    from familytree.corpus import surname_coverage
    _manifest(monkeypatch, [])
    assert surname_coverage("Schalandrijn") is None


def test_a_commune_harvest_never_counts_as_surname_coverage(monkeypatch):
    """It covers one commune, so it says nothing about the surname as a whole — and its
    `found` is not a population figure either."""
    from familytree.corpus import surname_coverage, surname_population_count
    _manifest(monkeypatch, [
        {"id": "dekeyser-oostende", "query": {"name": "De Keyser", "eventplace": "Oostende"},
         "found": 40, "mentions": 40, "complete": True},
    ])
    assert surname_coverage("De Keyser") is None
    assert surname_population_count("De Keyser") is None


def test_the_slug_collision_no_longer_hides_a_harvest(monkeypatch):
    """"De Keyser" was filed once as `de-keyser` and once as `dekeyser`, so a lookup by
    either id found only one of them. Matching on the query, not the id, sees both and
    prefers whichever actually holds more."""
    from familytree.corpus import surname_coverage
    _manifest(monkeypatch, [
        {"id": "de-keyser", "query": {"name": "De Keyser"}, "found": 11795, "mentions": 600, "complete": False},
        {"id": "dekeyser", "query": {"name": "Dekeyser"}, "found": 11907, "mentions": 4000, "complete": False},
    ])
    assert surname_coverage("De Keyser") == pytest.approx(4000 / 11907, abs=1e-6)


def test_one_surname_mints_one_harvest_id():
    import harvest
    assert harvest.surname_harvest_id("De Keyser") == harvest.surname_harvest_id("Dekeyser")
    assert harvest.surname_harvest_id("De Keyser", "Oostende") != harvest.surname_harvest_id("De Keyser")


def test_an_annotated_value_is_unwrapped_wherever_it_appears():
    """A2A renders XML as JSON, so any element carrying an attribute arrives as
    `{"@Remark": ..., "$": value}` instead of a scalar. Lommel does it to places; nothing
    stops an archive doing it to a name, a date or an age.

    This was twice patched at the field that happened to break, and twice the crash simply
    moved to the next field. The record is now unwrapped whole before anything reads it, so
    this test annotates one of every kind at once — if the fix ever regresses to guarding
    individual read sites, the field it forgets will fail here."""
    from familytree.corpus import normalise_act
    act = normalise_act({
        "id": "sla:test", "archive": "sla", "archive_org": "Test",
        "record": {
            "Event": {
                "EventType": "Overlijden",
                "EventDate": {"Year": {"@Cert": "low", "$": "1712"},
                              "Month": {"$": "8"}, "Day": {"$": "8"}},
                "EventPlace": {"Place": {"@TranscriptionRemark": "Lommel-Centrum", "$": "Lommel"}},
            },
            "Person": [{
                "@pid": "P1",
                "PersonName": {"PersonNameFirstName": {"$": "Joanna"},
                               "PersonNameLastName": {"@Alt": "Willems", "$": "Willems"}},
                "BirthPlace": {"Place": {"$": "Overpelt"}},
                "Residence": {"Place": {"$": "Lommel"}},
                "Profession": {"$": "landbouwster"},
                "Age": {"PersonAgeYears": {"$": "42"}},
            }],
            "RelationEP": [{"PersonKeyRef": "P1", "EventKeyRef": "E1", "RelationType": "Overledene"}],
        },
    })
    assert act.place == "Lommel"
    assert act.date == "1712-08-08"
    person = act.people[0]
    assert person.name == "Joanna Willems"
    assert person.birth_place == "Overpelt"
    assert person.residence == "Lommel"
    assert person.occupation == "landbouwster"
    assert person.age == 42
