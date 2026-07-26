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


@pytest.fixture(autouse=True)
def no_real_corpus(tmp_path, monkeypatch):
    """No test reads the harvest. Every test, by default.

    `compare` asks `frequencies()` for its rarity weights when a caller does not pass them,
    and `frequencies()` consults the persistent index — falling back to counting the corpus
    when the index is stale. So the moment a harvest ran without reindexing, the scoring
    tests started loading half a million real acts to assert a fact about two invented
    Candidates: the suite went from 0.2 seconds to 105.

    Speed is the visible half. The real problem is that it made the assertions depend on
    whichever acts happened to be on this machine, which is the opposite of what these
    tests are for. Pointed at nothing, the scorer uses its documented no-corpus constants
    and the results are the same everywhere.

    Tests that DO want a corpus build their own and override this — see `indexed_corpus`.
    """
    from familytree import corpus, store
    empty = tmp_path / "no-acts"
    empty.mkdir()
    monkeypatch.setattr(corpus, "ACTS_DIR", empty)
    monkeypatch.setattr(store, "ACTS_DIR", empty)
    monkeypatch.setattr(store, "DB", tmp_path / "absent.db")
    monkeypatch.setattr(corpus, "load_manifest", lambda: {"harvests": []})
    corpus.load_corpus.cache_clear()
    corpus.frequencies.cache_clear()
    store.close()
    yield
    corpus.load_corpus.cache_clear()
    corpus.frequencies.cache_clear()
    store.close()


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


# ---------- A2A as XML: the bulk and OAI routes ----------
# The whole case for reading whole archives instead of one act at a time rests on the
# claim that the XML and the JSON API carry the same record. If that ever stops being
# true, a bulk harvest silently fills the corpus with subtly different acts, and the
# scoring built on top of them moves for no visible reason. These pin the convention.


def test_a2a_xml_reproduces_the_json_apis_own_shape():
    """The API is this XML rendered by a fixed convention: attributes become `@name`, an
    element carrying both an attribute and a value becomes `{"@attr": …, "$": value}`, and
    a tag repeated inside its parent becomes a list. `corpus.unwrap_annotated` already
    depends on the middle one — Lommel's annotated place names forced it — so the reader
    has to reproduce the convention rather than invent a second one."""
    from xml.etree import ElementTree as ET
    from familytree.a2a import to_json
    elem = ET.fromstring(
        '<A2A xmlns="http://Mindbus.nl/A2A" Version="1.7">'
        '<Person pid="P1"><PersonName><PersonNameFirstName>Joanna</PersonNameFirstName></PersonName></Person>'
        '<Person pid="P2"><PersonName><PersonNameFirstName>Petrus</PersonNameFirstName></PersonName></Person>'
        '<Event><EventPlace><Place TranscriptionRemark="Lommel-Centrum">Lommel</Place></EventPlace></Event>'
        '<Source><SourcePlace></SourcePlace></Source>'
        "</A2A>"
    )
    got = to_json(elem)
    assert got["@Version"] == "1.7"
    # Repeated tag -> list; each keeps its attribute under an @ key.
    assert [p["@pid"] for p in got["Person"]] == ["P1", "P2"]
    # Text only -> a bare string, not a wrapper.
    assert got["Person"][0]["PersonName"]["PersonNameFirstName"] == "Joanna"
    # Text plus an attribute -> the annotated form unwrap_annotated knows.
    assert got["Event"]["EventPlace"]["Place"] == {"@TranscriptionRemark": "Lommel-Centrum", "$": "Lommel"}
    # Empty -> absent, so `(src.get("SourcePlace") or {})` reads it the way corpus.py does.
    assert got["Source"]["SourcePlace"] is None


def test_a2a_act_id_matches_the_apis_identifier():
    """The API's identifier is the record's own RecordGUID with the braces off and the
    case folded — checked against a full OAI page, 150 headers against 150 GUIDs. It is
    what lets a whole-archive export deduplicate against acts already fetched one at a
    time instead of storing everything twice."""
    from familytree.a2a import act_id
    assert act_id("den", {"Source": {"RecordGUID": "{4CC17044-D32A-ED11-A635-2D52D61F5E7A}"}}) == \
        "den:4cc17044-d32a-ed11-a635-2d52d61f5e7a"
    # No GUID: fall back to the OAI header, which already carries the archive prefix.
    assert act_id("den", {}, "den:abc") == "den:abc"
    assert act_id("den", {}, "abc") == "den:abc"
    # Neither: an act with no id cannot be deduplicated, so it is dropped, not guessed at.
    assert act_id("den", {}) is None


def test_a2a_xml_and_json_normalise_to_the_same_act():
    """The claim the bulk route rests on, end to end. Verified against real data too —
    all 1,361 Kortrijk acts held from the JSON API normalise identically to the same acts
    read out of the bulk export — but that needs the network, so this pins the same
    equivalence on a record small enough to write down."""
    import io
    from familytree.a2a import read_acts
    from familytree.corpus import normalise_act
    xml = (
        '<?xml version="1.0"?><A2ACollection xmlns:a2a="http://Mindbus.nl/A2A">'
        '<a2a:A2A xmlns:a2a="http://Mindbus.nl/A2A">'
        '<a2a:Person pid="P1"><a2a:PersonName><a2a:PersonNameFirstName>Alida</a2a:PersonNameFirstName>'
        "<a2a:PersonNameLastName>Van Iseghem</a2a:PersonNameLastName></a2a:PersonName></a2a:Person>"
        '<a2a:Person pid="P2"><a2a:PersonName><a2a:PersonNameFirstName>Jacobus</a2a:PersonNameFirstName>'
        "<a2a:PersonNameLastName>Van Iseghem</a2a:PersonNameLastName></a2a:PersonName></a2a:Person>"
        "<a2a:Event><a2a:EventType>Overlijden</a2a:EventType>"
        "<a2a:EventDate><a2a:Year>1861</a2a:Year></a2a:EventDate>"
        "<a2a:EventPlace><a2a:Place>Brugge</a2a:Place></a2a:EventPlace></a2a:Event>"
        "<a2a:RelationEP><a2a:PersonKeyRef>P1</a2a:PersonKeyRef>"
        "<a2a:RelationType>Overledene</a2a:RelationType></a2a:RelationEP>"
        "<a2a:RelationEP><a2a:PersonKeyRef>P2</a2a:PersonKeyRef>"
        "<a2a:RelationType>Vader</a2a:RelationType></a2a:RelationEP>"
        "<a2a:Source><a2a:RecordGUID>{AAAAAAAA-0000-0000-0000-000000000001}</a2a:RecordGUID>"
        "</a2a:Source></a2a:A2A></A2ACollection>"
    )
    rows = list(read_acts(io.BytesIO(xml.encode()), "t", "Test"))
    assert len(rows) == 1
    act = normalise_act(rows[0])
    assert act.id == "t:aaaaaaaa-0000-0000-0000-000000000001"
    assert (act.type, act.date, act.place) == ("Overlijden", "1861", "Brugge")
    assert [(p.name, p.role) for p in act.people] == [
        ("Alida Van Iseghem", "overledene"), ("Jacobus Van Iseghem", "vader")]
    # The parent edge the whole harvest exists to find.
    assert {"type": "father", "parent": "P2", "child": "P1"} in act.edges


# ---------- the persistent index ----------
# The index exists to make a question about one person cheap. What must never happen is
# that it makes it DIFFERENT: a candidate found through the index and one found by
# scanning have to be the same candidate, or the tools quietly disagree about what the
# corpus says depending on which one was asked.


@pytest.fixture
def indexed_corpus(tmp_path, monkeypatch):
    """A three-act corpus on disk, indexed. Small enough to reason about, real enough to
    go through exactly the code the harvest does."""
    import json as _json
    from familytree import corpus, store

    def act(n, given, surname, year, place):
        return {
            "id": f"t:{n}", "archive": "t", "archive_org": "Test",
            "record": {
                "Event": {"EventType": "Geboorte", "EventDate": {"Year": str(year)},
                          "EventPlace": {"Place": place}},
                "Person": [
                    {"@pid": "P1", "PersonName": {"PersonNameFirstName": given,
                                                  "PersonNameLastName": surname},
                     "BirthDate": {"Year": str(year)}, "BirthPlace": {"Place": place}},
                    {"@pid": "P2", "PersonName": {"PersonNameFirstName": "Vader",
                                                  "PersonNameLastName": surname}},
                ],
                "RelationEP": [
                    {"PersonKeyRef": "P1", "RelationType": "Kind"},
                    {"PersonKeyRef": "P2", "RelationType": "Vader"},
                ],
            },
        }

    acts_dir = tmp_path / "acts"
    acts_dir.mkdir()
    (acts_dir / "t.jsonl").write_text(
        "".join(_json.dumps(a) + "\n" for a in (
            act(1, "Petrus", "Bundervoet", 1879, "Evergem"),
            act(2, "Petrus", "Bundervoet", 1912, "Evergem"),
            act(3, "Joanna", "Schalandrijn", 1880, "Hamme"),
        )), encoding="utf-8")

    monkeypatch.setattr(corpus, "ACTS_DIR", acts_dir)
    monkeypatch.setattr(store, "ACTS_DIR", acts_dir)
    monkeypatch.setattr(store, "DB", tmp_path / "corpus.db")
    monkeypatch.setattr(corpus, "load_manifest", lambda: {"harvests": [], "population": {"be": 1000}})
    corpus.load_corpus.cache_clear()
    corpus.frequencies.cache_clear()
    store.close()
    store.build()
    yield store
    store.close()
    corpus.load_corpus.cache_clear()
    corpus.frequencies.cache_clear()


def test_the_index_counts_the_same_frequencies_as_a_scan(indexed_corpus):
    """Every rarity weight in the scorer is measured against these tables, so a
    divergence here would move every score in the project without changing a single
    visible threshold."""
    from familytree import corpus
    scanned, indexed = corpus.count_frequencies(), indexed_corpus.frequencies()
    assert (indexed.n, indexed.surnames, indexed.givens, indexed.places) == \
        (scanned.n, scanned.surnames, scanned.givens, scanned.places)


def test_the_index_finds_the_same_candidates_as_a_scan(indexed_corpus):
    from familytree.corpus import corpus_mentions
    from familytree.match import build_index, candidates_for, from_mention
    from familytree.match import Candidate
    me = Candidate(ref="me", name="Petrus Bundervoet", surname="Bundervoet",
                   given="Petrus", birth_year=1879, places=["Evergem"])
    scan = {c.ref for c in candidates_for(me, build_index(from_mention(m) for m in corpus_mentions()))}
    assert scan == {c.ref for c in indexed_corpus.candidates_for(me)}
    assert indexed_corpus.candidate_count(me) == len(scan)
    # And it did find something, so the assertion above is not two empty sets agreeing.
    assert scan


def test_coverage_counts_what_is_HELD_not_what_was_asked_for(indexed_corpus, monkeypatch):
    """A surname's coverage is a fact about the corpus, not about the query log.

    It used to read the manifest's `mentions` — how many that surname's own search
    returned — which was the same number right up until acts began arriving by routes that
    never mentioned a surname. After nine whole-archive harvests the manifest still claimed
    600 De Keyser mentions held of 11,795 while the corpus held 3,512, and 600 of 2,370 for
    Damman while it held 2,334, which is essentially finished.

    Understating coverage is not a harmless conservatism: it sinks the frontier's P and it
    makes the queue recommend "finish the harvest" as the cheapest route to records already
    on disk. Reporting held as not-held is reporting blocked as miss, pointed the other way.
    """
    from familytree import corpus
    # The manifest remembers a capped search: 1 mention of 100. The corpus holds 4,
    # because two Bundervoet birth acts each name a Bundervoet father as well.
    monkeypatch.setattr(corpus, "load_manifest", lambda: {
        "population": {"be": 1000},
        "harvests": [{"id": "bundervoet", "query": {"name": "Bundervoet"},
                      "found": 100, "mentions": 1, "complete": False}],
    })
    assert corpus.mentions_held("Bundervoet") == 4
    assert corpus.surname_coverage("Bundervoet") == pytest.approx(4 / 100)
    # And the honest floor still applies where there is no index to count with.
    monkeypatch.setattr(indexed_corpus, "is_current", lambda: False)
    assert corpus.surname_coverage("Bundervoet") == pytest.approx(1 / 100)


def test_the_index_notices_the_harvest_moving_underneath_it(indexed_corpus, tmp_path):
    """A stale index answering "no candidates" for an act fetched an hour ago is the
    corpus form of reporting `blocked` as `miss` — the failure this project is arranged
    against. So staleness is detected, not assumed away."""
    import json as _json
    assert indexed_corpus.is_current()
    with (tmp_path / "acts" / "t.jsonl").open("a", encoding="utf-8") as f:
        f.write(_json.dumps({"id": "t:4", "archive": "t", "record": {}}) + "\n")
    assert not indexed_corpus.is_current()


def test_the_index_holds_offsets_not_a_second_copy_of_the_evidence(indexed_corpus):
    """The JSONL files stay the only copy of the acts. An index that duplicated them
    could drift from the harvest, and deleting it would lose evidence rather than a
    derived file."""
    import sqlite3
    with sqlite3.connect(indexed_corpus.DB) as db:
        cols = {r[1] for r in db.execute("PRAGMA table_info(acts)")}
        rows = db.execute("SELECT id, path, offset, length FROM acts ORDER BY id").fetchall()
    assert cols == {"id", "path", "offset", "length"}
    assert [r[0] for r in rows] == ["t:1", "t:2", "t:3"]
    assert all(isinstance(r[2], int) and r[3] > 0 for r in rows)


def test_an_act_with_two_events_takes_the_one_it_is_about():
    """A2A allows several events in one record, and Lommel uses that: 1,620 marriages
    carrying both the wedding and the `Ondertrouw` — the banns, three weeks earlier — as
    two events with two dates for one union.

    `Act` holds a single event, so it has to choose, and the choice is read off the record:
    `RelationEP` ties each participant to an event, so the event the participants are
    attached to is the one the act is about. Picking the banns would date every one of those
    marriages three weeks early.

    This was a crash, not a wrong answer — `'list' object has no attribute 'get'` — and it
    took a whole-archive harvest to find, because every surname-filtered harvest before it
    had missed those records entirely. Worth remembering about coverage: the code had been
    wrong all along and the data had never said so.
    """
    from familytree.corpus import normalise_act
    act = normalise_act({
        "id": "sla:two", "archive": "sla", "archive_org": "Test",
        "record": {
            "Event": [
                {"@eid": "Event1", "EventType": "Trouwen",
                 "EventDate": {"Year": "1807", "Month": "07", "Day": "07"},
                 "EventPlace": {"Place": "Lommel"}},
                {"@eid": "Event2", "EventType": "Ondertrouw",
                 "EventDate": {"Year": "1807", "Month": "06", "Day": "20"},
                 "EventPlace": {"Place": "Lommel"}},
            ],
            "Person": [
                {"@pid": "P1", "PersonName": {"PersonNameFirstName": "Jan",
                                              "PersonNameLastName": "Geboers"}},
                {"@pid": "P2", "PersonName": {"PersonNameFirstName": "Anna",
                                              "PersonNameLastName": "Dingenen"}},
            ],
            "RelationEP": [
                {"PersonKeyRef": "P1", "EventKeyRef": "Event1", "RelationType": "Bruidegom"},
                {"PersonKeyRef": "P2", "EventKeyRef": "Event1", "RelationType": "Bruid"},
            ],
        },
    })
    assert act.type == "Trouwen"
    assert act.date == "1807-07-07", "the banns are not the wedding"
    # And the couple edge still forms, which is the whole reason a marriage act is worth
    # more than any other record.
    assert {"type": "couple", "a": "P1", "b": "P2"} in act.edges


def test_a_source_published_as_a_list_does_not_crash():
    """Nothing guarantees an archive publishes exactly one Source, and a record that will
    not parse takes the whole validator down mid-run rather than degrading."""
    from familytree.corpus import normalise_act
    act = normalise_act({
        "id": "t:src", "archive": "t",
        "record": {
            "Event": {"EventType": "Geboorte", "EventDate": {"Year": "1880"}},
            "Person": [{"@pid": "P1", "PersonName": {"PersonNameLastName": "Test"}}],
            "Source": [{"SourceType": "BS Geboorte"}, {"SourceType": "duplicate"}],
        },
    })
    assert act.source_type == "BS Geboorte"


def _cand(**kw):
    from familytree.match import Candidate
    base = dict(ref="x", name="", surname="", given="")
    base.update(kw)
    return Candidate(**base)


def test_the_commune_an_act_was_drawn_up_in_cannot_anchor_a_graft():
    """A marriage held at Oostende says where the wedding was, not where either party
    lived. Treating the act's commune as the person's own matched Edouard Dekeyser, who
    died in 1951, to a 1963 Oostende death, and Hubert De Vriese, born 1665 at Tielt, to a
    1911 Brussels marriage. It still counts for something — hence the bits — but it can
    never be one of the two independent identifiers."""
    from familytree.match import compare
    a = _cand(surname="Dekeyser", given="Eduardus", places=["Oostende"])
    b = _cand(ref="y", surname="Dekeyser", given="Albert", context_places=["Oostende"])
    m = compare(a, b)
    assert "context" in m.classes
    assert "place" not in m.classes
    assert m.independent < 2, "the act's commune must not supply a second identifier"


def test_a_relatives_forename_alone_cannot_anchor_a_graft():
    """Gustaaf Dekeyser's wife was a Simonne; so was Andre Dekeyser's, seventy years later.
    A shared forename among relatives is a coincidence in this material — Simonne, Maria
    and Joanna are each a large share of the women. A relative's SURNAME agreeing is the
    classic second identifier; a forename is not."""
    from familytree.match import compare
    kin_a = [("spouse", "vandewalle", frozenset({"simonne"}))]
    kin_b = [("spouse", "barbier", frozenset({"simonne"}))]
    a = _cand(surname="Dekeyser", given="Gustaaf", kin=kin_a)
    b = _cand(ref="y", surname="Dekeyser", given="Andre", kin=kin_b)
    m = compare(a, b)
    assert "kin-forename" in m.classes
    assert "kin" not in m.classes
    assert m.independent < 2, "a shared forename must not supply a second identifier"


def test_a_relatives_surname_still_anchors():
    """The counterpart: two Simonne Vandewalles is not a coincidence, and the mother's
    maiden name remains the strongest second identifier this material offers."""
    from familytree.match import compare
    kin = [("spouse", "vandewalle", frozenset({"simonne"}))]
    a = _cand(surname="Dekeyser", given="Gustaaf", kin=kin)
    b = _cand(ref="y", surname="Dekeyser", given="Gustaaf", kin=list(kin))
    m = compare(a, b)
    assert "kin" in m.classes
    assert m.independent >= 2


def test_only_the_deceased_gets_a_death_year_from_a_death_act():
    """A death act names the dead person's parents, spouse and informants, and all of
    them are alive to be named. Giving every participant the act's year as their own
    death year made anyone in this tree who died in 1861 match the living father in an
    1861 death act — Joannes Josephus Van Iseghem to a Jacobus, on nothing but a surname
    and that phantom date."""
    from familytree.corpus import normalise_act
    from familytree.match import from_mention
    act = normalise_act({
        "id": "t:1", "archive": "t", "archive_org": "T",
        "record": {
            "Event": {"EventType": "Overlijden", "EventDate": {"Year": "1861"},
                      "EventPlace": {"Place": "Brugge"}},
            "Person": [
                {"@pid": "P1", "PersonName": {"PersonNameFirstName": "Alida",
                                              "PersonNameLastName": "Van Iseghem"}},
                {"@pid": "P2", "PersonName": {"PersonNameFirstName": "Jacobus",
                                              "PersonNameLastName": "Van Iseghem"}},
            ],
            "RelationEP": [
                {"PersonKeyRef": "P1", "EventKeyRef": "E1", "RelationType": "Overledene"},
                {"PersonKeyRef": "P2", "EventKeyRef": "E1", "RelationType": "Vader"},
            ],
        },
    })
    by_name = {p.given: p for p in act.people}
    assert from_mention(by_name["Alida"]).death_year == 1861, "the deceased did die that year"
    assert from_mention(by_name["Jacobus"]).death_year is None, "the father was alive to be named"


def test_an_unparseable_date_part_is_dropped_not_guessed():
    """Archives write "ca" into a year they are unsure of and leave dashes or blanks in a
    month or day they could not read. int() on those killed the validator mid-run. A part
    that will not parse is dropped — never rounded, never defaulted to 1 — because the
    date grammar has no syntax for a guess and this is where one would get invented."""
    from familytree.corpus import _api_date
    assert _api_date({"Year": "1902", "Month": "8", "Day": "8"}) == "1902-08-08"
    assert _api_date({"Year": "1902", "Month": "8", "Day": "ca"}) == "1902-08"
    assert _api_date({"Year": "1902", "Month": "-", "Day": "8"}) == "1902"
    assert _api_date({"Year": "ca", "Month": "8", "Day": "8"}) is None
    assert _api_date({"Year": "1902", "Month": "13", "Day": "8"}) == "1902"
    assert _api_date({"Year": " 1902 "}) == "1902"
