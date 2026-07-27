"""The parts that are load-bearing and silent when they break.

A misread record does not raise — it produces a person with a missing field, and that
surfaces months later as a hole in the tree. Same for the date grammar and the scoring:
both fail by being quietly wrong rather than by stopping. These are the cases worth
pinning.

    uv run --group dev pytest
"""

from __future__ import annotations

import json

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


def test_a_date_says_one_thing_and_permits_another():
    """`point_year` is what a date ASSERTS, `year_span` what it PERMITS, and every veto in
    match.py asks the second question. Reading `year_of` instead flattened `1920..1929` to
    "1920" and made every other year in the range a conflict with it."""
    from familytree.people import APPROX_SLACK, point_year, year_span
    assert (point_year("1876-11-12"), year_span("1876-11-12")) == (1876, (1876, 1876))
    assert (point_year("1876"), year_span("1876")) == (1876, (1876, 1876))
    # About: asserts a year, permits a window either side.
    assert point_year("~1682") == 1682
    assert year_span("~1682") == (1682 - APPROX_SLACK, 1682 + APPROX_SLACK)
    # Bounds and ranges assert NO year — an open end means unknown, not zero.
    assert point_year("<1727") is None and year_span("<1727") == (None, 1727)
    assert point_year(">1900") is None and year_span(">1900") == (1900, None)
    assert point_year("1575..1587") is None and year_span("1575..1587") == (1575, 1587)
    assert year_span(None) == (None, None)


def test_a_range_does_not_disagree_with_a_year_inside_it():
    """Gustaaf's birth is recorded `1920..1929` — the grammar saying the decade is as much
    as is known. Acts stating 1923, 1925 and 1929 were REJECTED as conflicting with that
    range, so the one thing his record admits it does not know became a reason to refuse
    every record that would have told us. He is a person this project needs to find in a
    foreign register, and 81 of 434 records carry a non-point date."""
    from familytree.match import compare
    him = _cand(surname="De Keyser", given="Gustaaf", birth_date="1920..1929",
                birth_year=1920, stated_birth_year=True)
    for year in (1920, 1923, 1925, 1929):
        act = _cand(ref=f"act#{year}", surname="De Keyser", given="Gustaaf",
                    birth_date=f"{year}-06-01", birth_year=year, stated_birth_year=True)
        m = compare(him, act)
        assert not m.conflict, f"{year} is inside the range and must not conflict"
    # Outside the range, by more than the slack, it still vetoes.
    far = _cand(ref="act#far", surname="De Keyser", given="Gustaaf",
                birth_date="1880-06-01", birth_year=1880, stated_birth_year=True)
    assert compare(him, far).conflict

    # ...and a range earns no date bits: agreeing with its lower edge is arithmetic, not
    # evidence, so it must not be one of the two independent identifiers.
    edge = _cand(ref="act#edge", surname="De Keyser", given="Gustaaf",
                 birth_date="1920-06-01", birth_year=1920, stated_birth_year=True)
    assert "date" not in compare(him, edge).classes


def test_a_range_is_never_mistaken_for_a_day_level_date():
    """`len(date) == 10` was used three separate times to mean "is a day-level date", and
    `1920..1929` is exactly ten characters. A length is not a format.

    In `compare` it produced a 12-bit "same day" agreement between two people who each knew
    only their decade, and vetoed one of them against an act stating a real day. In
    `frontier.discriminability` it scored a decade-only birth as though a day-level date had
    been read, which raises P(resolvable) and promotes that frontier up the queue — ranked
    searchable on evidence it does not have.
    """
    from familytree.corpus import Frequencies
    from familytree.frontier import discriminability
    freq = Frequencies(n=0, surnames={}, givens={}, places={})
    day = _cand(surname="Bostyn", birth_date="1876-11-12", birth_year=1876)
    rng = _cand(surname="Bostyn", birth_date="1920..1929", birth_year=1920)
    assert len("1920..1929") == 10, "the whole trap in one line"
    assert discriminability(day, freq) > discriminability(rng, freq)


def test_an_open_bound_never_vetoes_the_side_it_leaves_open():
    """`<1673` means born at some unknown time before 1673, and `>1838` means died at some
    unknown time after 1838. Treating either as a measurement is what produced "mother at
    age -6" for a record in conflict with nothing."""
    from familytree.match import compare
    before = _cand(surname="Vanstechele", given="Joannes", birth_date="<1673",
                   birth_year=1673, stated_birth_year=True)
    early = _cand(ref="act#1", surname="Vanstechele", given="Joannes",
                  birth_date="1650-03-02", birth_year=1650, stated_birth_year=True)
    assert not compare(before, early).conflict, "1650 IS before 1673"
    later = _cand(ref="act#2", surname="Vanstechele", given="Joannes",
                  birth_date="1690-03-02", birth_year=1690, stated_birth_year=True)
    assert compare(before, later).conflict, "1690 is not before 1673"

    # A death known only as "after 1838" cannot rule out a child born in 1850.
    alive = _cand(surname="Haesaerts", given="Jan", death_date=">1838", death_year=1838)
    child = _cand(ref="act#3", surname="Haesaerts", given="Jan",
                  birth_date="1850-01-01", birth_year=1850, stated_birth_year=True)
    assert "born after the other died" not in compare(alive, child).conflict


def test_born_after_the_other_died_vetoes_whichever_way_round_it_is_asked():
    """This tested only a's death against b's birth, so compare(x, y) and compare(y, x)
    could disagree about whether the pair was even possible — and both orders are used:
    act_coverage compares (target, mention), missing_children compares (mention, target)."""
    from familytree.match import compare
    dead = _cand(surname="Bossin", given="Cornelius", death_date="1847", death_year=1847)
    born = _cand(ref="y", surname="Bossin", given="Cornelius", birth_date="1901-02-27",
                 birth_year=1901, stated_birth_year=True)
    assert compare(dead, born).conflict and compare(born, dead).conflict


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


def _x(surname):
    """The prefix blocking key for a surname."""
    return next(k for k in block_keys(Candidate(ref="_", name="", surname=surname, given="")) if k.startswith("x:"))


@pytest.mark.parametrize("a,b", [
    # The pair the prefix key exists for: same family, one name longer than the other.
    ("Vanstechele", "Vanstechelman"),
    # The pair that fixes the prefix LENGTH at four rather than five or six: these stems
    # are "felde" and "felden", so they part company at the fifth character. Six is 3.7x
    # faster and drops them, which is a true link never compared.
    ("Vandevelde", "Vandevelden"),
    ("Vandewalle", "Vandewalles"),
    # And the pair it used to MISS, because the particle ate the whole prefix: `fanden`
    # against `fanber` share nothing, though the family is the same.
    ("Vandenberghe", "Van Berghe"),
    ("Van der Varent", "Vervarent"),
])
def test_the_prefix_key_blocks_on_the_family_not_the_particle(a, b):
    assert _x(a) == _x(b), f"{a} and {b} must still be compared"


def test_a_long_stem_is_not_truncated_into_an_unrelated_family():
    """The reason the prefix length adapts to the stem rather than being fixed at four.

    "Wittenheyns" has the stem "fitenheins". Cut to four characters that is "fite" — which is
    also what "De Witte" reduces to, so a surname with no exact match anywhere in the corpus
    was pulling 28,089 mentions of an unrelated family. A long stem has the characters to
    spare; a short one does not, which is why both lengths exist.
    """
    assert _x("Wittenheyns") != _x("Dewitte")
    assert _x("Wittenheyns") != _x("De Witte")
    # …while the short-stem pair it would break if the length were fixed at six still holds.
    assert _x("Vandevelde") == _x("Vandevelden")


@pytest.mark.parametrize("a,b", [
    ("Vandenberghe", "Vandenbroeck"),
    ("Vandenbemden", "Vandenberghe"),
    ("Van der Varent", "Van der Beken"),
])
def test_the_prefix_key_no_longer_buckets_every_van_den_together(a, b):
    """A quarter of Flemish surnames begin Van den / Van der / De, so a prefix taken from
    the whole name put 150,611 mentions under `x:fanden` — a sixth of the corpus in one
    bucket, which is a scan wearing a block's clothes. These are different families and
    must land in different buckets."""
    assert _x(a) != _x(b), f"{a} and {b} are different families"


@pytest.mark.parametrize("junk", [
    "de vader is de aangever",              # 128,958 mentions — the commonest "surname" held
    "De vader is de aangever.",
    "de aangever is de vader",
    "de moeder doet de aangifte van erkenning",
    "Gheeraerdts 2de in rang zijnde Schepen in afwezigheid van den Burgemeester",
    "De Smet - 71 j Aalst zonder",          # a name welded to an age and a commune
    "1) Verleysen + 2) Van den Broeck + 3) Vera",
    "1) 3 februari 1842 en 2) 30 mei 1850",
])
def test_a_sentence_in_the_name_field_is_not_a_name(junk):
    """Aalst writes transcription remarks where a name belongs, and one of them was the
    commonest surname in the corpus — ahead of De Smet. A remark that blocks as a surname
    puts 129,000 unrelated people in one bucket and skews every rarity weight measured
    against the corpus."""
    from familytree.corpus import real_name
    assert real_name(junk) == ""


@pytest.mark.parametrize("name", [
    "De Wolf - Coevoet",                    # 9,870 mentions, a real double surname
    "Van Pottelsberghe de la Potterie",
    "de Cocquéau des Mottes",
    "Baron Van der Noot",
    "Van der Noot de Vreckem",
    "de Neve de Roden",
    "Van op den Bosch",
    "Van Iseghem",                          # contains "Is" — inside a token, not a word
    "Vandewalle",
])
def test_the_rule_does_not_eat_a_real_name(name):
    """The reason this is not a word-count rule. Five-word surnames exist in this corpus and
    belong to real families; deleting them would be far worse than the bug being fixed."""
    from familytree.corpus import real_name
    assert real_name(name) == name


def test_a_nameless_participant_is_still_a_participant():
    """The act does record that somebody took part. It simply does not say who, and an absent
    name is the truthful representation of that — not a reason to drop the person."""
    from familytree.corpus import normalise_act
    act = normalise_act({
        "id": "aal:x", "archive": "aal",
        "record": {
            "Event": {"EventType": "Geboorte", "EventDate": {"Year": "1908"}},
            "Person": [
                {"@pid": "P1", "PersonName": {"PersonNameFirstName": "Romaan",
                                              "PersonNameLastName": "Sonck"}},
                {"@pid": "P2", "PersonName": {"PersonNameLastName": "de vader is de aangever"}},
            ],
            "RelationEP": [
                {"PersonKeyRef": "P1", "EventKeyRef": "E1", "RelationType": "Kind"},
                {"PersonKeyRef": "P2", "EventKeyRef": "E1", "RelationType": "Vader"},
            ],
        },
    })
    assert len(act.people) == 2, "the participant is not discarded"
    father = next(p for p in act.people if p.pid == "P2")
    assert (father.name, father.surname, father.given) == ("", "", "")
    # And with no name there is nothing to block on, so it cannot be matched to anybody.
    from familytree.match import block_keys, from_mention
    assert block_keys(from_mention(father)) == []


def test_a_name_that_is_almost_all_particle_keeps_its_whole_form():
    """Stripping "de" from Devos leaves "fos", which discriminates nothing. Below the floor
    the full phonetic form is kept instead."""
    from familytree.match import surname_stem, phonetic
    assert surname_stem(phonetic("Devos")) == phonetic("Devos")
    assert surname_stem(phonetic("Vandenberghe")) != phonetic("Vandenberghe")


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


def test_every_class_compare_emits_is_declared_strong_or_weak():
    """`CLASSES` and `WEAK_CLASSES` are the whole of "two independent identifiers": a class
    in the first counts towards the floor, one in the second adds bits and can never carry a
    graft alone. `WEAK_CLASSES` was declared and then read by nothing, so the distinction
    lived only in the string literals inside `compare` — and a typo there would have
    promoted a weak agreement to an independent identifier with nothing to notice.

    Exercised over the pairs elsewhere in this file that are built to trip each class.
    """
    from familytree.match import CLASSES, WEAK_CLASSES
    declared = set(CLASSES) | set(WEAK_CLASSES)
    assert not set(CLASSES) & set(WEAK_CLASSES), "a class cannot be both"

    kin = [("mother", "stockman", frozenset({"livina"}))]
    pairs = [
        _pair(),
        (_cand(surname="Dekeyser", given="Albert", places=["Oostende"]),
         _cand(ref="y", surname="Dekeyser", given="Albert", context_places=["Oostende"])),
        (_cand(surname="Dekeyser", given="Gustaaf", kin=kin),
         _cand(ref="y", surname="Dekeyser", given="Gustaaf", kin=list(kin))),
        (_cand(surname="Bostyn", given="Henricus", birth_year=1876),
         _cand(ref="y", surname="Mombaerts", given="Henricus", birth_year=1876)),
        (_cand(surname="Pardon", given="Maria", occupation="landbouwer"),
         _cand(ref="y", surname="Pardon", given="Maria", occupation="landbouwer")),
        (_cand(surname="Van Bergen", given="Maria", birth_year=1843),
         _cand(ref="y", surname="Van Bergen", given="Maria", birth_year=1844)),
    ]
    seen = set()
    for a, b in pairs:
        m = compare(a, b)
        seen.update(m.classes)
        undeclared = set(m.classes) - declared
        assert not undeclared, f"compare emitted an undeclared class: {undeclared}"
        # The point of the split: a weak class must never reach the two-identifier floor.
        assert m.independent == sum(1 for c in m.classes if c in CLASSES)
    assert seen & set(WEAK_CLASSES), "these pairs are supposed to exercise the weak classes"


def test_a_bare_birth_year_is_not_an_independent_identifier():
    """Neither an off-by-one year nor an exact one, and the second half of that is new.

    "Birth year ±1 is nearly free when the tree holds a bare year" — §59, before the gold
    standard could show it. Once the act-level rejections started scoring, both Van Bergen
    rivals turned out to reach graftable on exactly this: surname plus a ±1 year, wrong
    province and wrong parents in each case. That half is unchanged and still pinned here.

    THE EXACT YEAR FOLLOWED IT, and this test asserted the opposite until it did. The
    assumption was that an exact birth-year agreement is a full identifier; two false
    positives of precisely that shape, both settled by reading the act, say otherwise:

      appolonia_huyghebaert × aal:8e1db4bf-… — 19.3 bits, "2 independent (name+date)",
        being surname Huyghebaert + birth year 1830. The record is *Marie* Huyghebaert in
        an Aalst population-register residency row, 80km from Oudenburg.
      lucien_vincke × abb:f445f3e2-…#Person10355353 — 19.3 bits, the same shape on surname
        Vincke + birth year 1840. The record is the *witness* Gustave Vincke at a Brussels
        marriage of a different man entirely.

    In a corpus of four million mentions thousands of people share any one year, so this is
    the same statement as the ±1 case and not a weaker one. It still scores its six bits;
    it cannot be one of the two identifiers a graft needs. Demoting it cost no true match
    in the gold standard.

    A DAY-LEVEL agreement still is an identifier, which is the half that must not break."""
    from familytree.match import CLASSES, WEAK_CLASSES, compare
    near = compare(_cand(surname="Van Bergen", given="Maria", birth_year=1843),
                   _cand(ref="y", surname="Van Bergen", given="Maria", birth_year=1844))
    assert "date-near" in near.classes and "date" not in near.classes
    assert near.independent < 2 and not near.graftable
    assert near.distinguishing > 0, "a near miss is still worth noticing"

    exact = compare(_cand(surname="Van Bergen", given="Maria", birth_year=1843),
                    _cand(ref="y", surname="Van Bergen", given="Maria", birth_year=1843))
    assert "date-year" in exact.classes and "date" not in exact.classes
    assert exact.independent < 2 and not exact.graftable
    assert exact.distinguishing >= 6, "an exact year is still the strongest of the weak"

    day = compare(_cand(surname="Van Bergen", given="Maria", birth_date="1843-04-02",
                        birth_year=1843),
                  _cand(ref="y", surname="Van Bergen", given="Maria", birth_date="1843-04-02",
                        birth_year=1843))
    assert "date" in day.classes, "a day-level agreement is still an identifier"

    for weak in ("date-near", "date-year"):
        assert weak not in CLASSES and weak in WEAK_CLASSES


def test_one_commune_is_one_fact_however_many_fields_state_it():
    """An act's own commune and a participant's birthplace naming the same place is one
    statement, and it was being paid for twice — five bits for "place grezdoiceau" and four
    more for "birthplace Grez-Doiceau".

    Read directly (§68): `abb:202f2000-…` is the 1846 death of *Alexandre* Thumas, age 5,
    son of Charles Joseph Thumas × Josephine Latour — an unrelated Thumas household in a
    commune known to hold at least two. It scored 23 bits, "2 independent (name+place)",
    against FOUR people of this line at once: georgesjoseph_t, georges2_t, jbzenon_t and
    georges_cj. A locally common surname and the commune it lives in are one signal about a
    family, not two about a person, and the doubled weight was the whole of the second."""
    a = _cand(surname="Thumas", given="Georges Joseph", places=["Grez-Doiceau"],
              birth_place="Grez-Doiceau")
    b = _cand(ref="y", surname="Thumas", given="Alexandre", places=["Grez-Doiceau"],
              birth_place="Grez-Doiceau", context_places=["Grez-Doiceau"])
    m = compare(a, b)
    assert [cls for cls, _, _ in m.agree].count("place") == 1, "one commune, one weight"
    assert m.distinguishing < 6 and not m.graftable


def test_a_bare_year_and_a_bare_surname_are_not_two_identifiers():
    """The other two false positives of 2026-07-27, both settled by reading the act, both
    reaching graftable at 19.3 bits on "2 independent (name+date)".

    They are reconstructed here as the records actually read, rather than as bare
    Candidates, so the pin is against the shape of evidence the venue really produces."""
    appolonia = compare(
        _cand(surname="Huyghebaert", given="Appolonia Joanna", birth_date="1830-09-26",
              birth_year=1830, birth_place="Oudenburg", places=["Oudenburg", "Oostende"],
              stated_birth_year=True),
        # Aalst 1856 population register, a residency row 80km away: Marie Huyghebaert,
        # b.1830 Clemskerke, servante. No parents, no marriage, nothing else to test.
        _cand(ref="y", surname="Huyghebaert", given="Marie", birth_year=1830,
              birth_place="Clemskerke", places=["Clemskerke", "Aalst"],
              context_places=["Aalst"], stated_birth_year=True))
    assert appolonia.independent < 2 and not appolonia.graftable

    lucien = compare(
        _cand(surname="Vincke", given="Lucien Julianus", birth_date="1840-03-26",
              birth_year=1840, birth_place="Diksmuide", places=["Diksmuide"],
              occupation="metserdiener", stated_birth_year=True),
        # The WITNESS at a Brussels marriage of a different man: Gustave Vincke, 25,
        # menuisier — an age-implied year, a different trade, a different city.
        _cand(ref="y", surname="Vincke", given="Gustave", birth_year=1840,
              places=["Bruxelles"], context_places=["Brussel"], occupation="menuisier"))
    assert lucien.independent < 2 and not lucien.graftable


def test_a_parent_pair_names_a_sibship_not_a_person():
    """An act naming your father and your mother names every one of their children equally
    well, and this material is full of sibships: four Peremans siblings carry the identical
    held father+mother, so `abl:fa0664d5-…` — whose ten participants include exactly ONE
    Peremans, the bride Joanna Catharina Jacoba — scored graftable against her sister Maria
    Josephina, who appears in it nowhere (§69). The same shape put Georges Joseph Thumas on
    the 1851 death act of Charles Eugène, his infant brother: right parents, wrong child.

    Scoped to parent buckets, because a sibling does not share your spouse."""
    parents = [("father", "peremans", frozenset({"egidius"})),
               ("mother", "verelst", frozenset({"joanna", "theresia"}))]
    m = compare(_cand(surname="Peremans", given="Maria Josephina", kin=list(parents)),
                _cand(ref="y", surname="Peremans", given="Joanna Catharina Jacoba",
                      kin=list(parents)))
    assert "kin-sibship" in m.classes and "kin" not in m.classes
    assert not m.graftable
    assert m.distinguishing > 0, "the parents still agree, and that is worth noticing"

    spouse = [("spouse", "vandervarent", frozenset({"petrus"}))]
    shares_a_husband = compare(
        _cand(surname="Peremans", given="Maria Josephina", kin=parents + spouse),
        _cand(ref="y", surname="Peremans", given="Joanna Catharina Jacoba",
              kin=list(parents + spouse)))
    assert "kin" in shares_a_husband.classes, "a sibling does not share your spouse"


def test_a_day_level_date_with_a_place_is_still_two_identifiers():
    """The half the demotions above must not break. Deduplicating the commune and demoting
    the bare year are both about what an agreement is worth; a day-level birth date and the
    commune it happened in remain the two identifiers CLAUDE.md rule 1 names first."""
    m = compare(*_pair())
    assert "date" in m.classes and "place" in m.classes
    assert m.independent >= 2 and m.graftable and m.band == "strong"


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


def test_the_stored_candidate_is_the_whole_comparable_candidate():
    """The index stores each mention as the Candidate the scorer compares, so that scoring
    never has to rebuild the act it came from. That only holds while the stored fields are
    ALL the compared fields — a field added to `Candidate` and forgotten in `_CAND_FIELDS`
    would come back absent, which reads as a weaker match rather than as a bug.

    So this asserts the two lists agree, and that a Candidate survives the round trip.
    """
    from dataclasses import fields
    from familytree import store
    from familytree.match import Candidate

    compared = {f.name for f in fields(Candidate)} - {"mention", "person_id"}
    stored = set(store._CAND_FIELDS) | {"kin"}
    assert compared == stored, (
        f"stored but not compared: {stored - compared}; "
        f"compared but not stored: {compared - stored}")

    original = Candidate(
        ref="t:1#P1", name="Petrus Bundervoet", surname="Bundervoet", given="Petrus",
        sex="m", birth_year=1879, birth_date="1879-03-19", birth_place="Evergem",
        death_year=1950, places=["Evergem", "Gent"], context_places=["Aalst"],
        event_year=1901, occupation="landbouwer", stated_birth_year=True,
        kin=[("mother", "stockman", frozenset({"livina", "maria"}))],
    )
    back = store._load(store._dump(original))
    for f in store._CAND_FIELDS:
        assert getattr(back, f) == getattr(original, f), f
    assert back.kin == original.kin, "a frozenset of forenames must survive JSON"


def test_the_index_notices_the_CODE_changing_not_only_the_harvest(monkeypatch, tmp_path):
    """The staleness guard covered the harvest files and nothing else, so an index built by
    yesterday's `block_keys` reported itself current. Both of the last two changes to what
    is derived would have shipped a stale index — the particle-stripped prefix key changed
    which pairs are comparable, and `death_date` changed what a stored candidate carries."""
    from familytree import store
    acts = tmp_path / "acts"
    acts.mkdir()
    (acts / "t.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(store, "ACTS_DIR", acts)
    before = store.signature()
    monkeypatch.setattr(store, "FORMAT", store.FORMAT + 1)
    assert store.signature() != before, "a format bump must invalidate the index"


def test_a_refuted_pair_is_not_offered_to_the_queue_again(monkeypatch, tmp_path):
    """The gap `docs/autopilot-log.md` ends on: "the refutations are recorded, with
    reasoning, and nothing reads them back. Left as it is, the next unattended run
    re-grafts the wrong Appolonia — and the run after that."

    An act-level refutation covers every mention in that act, which is broader than the
    label strictly says and is the right way round: too broad costs one label a re-point,
    too narrow costs the re-graft loop.
    """
    from familytree import labels
    path = tmp_path / "labels.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in [
        {"person": "coekelberghs", "ref": "abl:2c0d#Person1", "match": False,
         "basis": "act", "why": "the act names Vandenhoven, not Coekelberghs"},
        {"person": "hendrik_vdb", "ref": "abl:9999", "match": False,
         "basis": "act", "why": "a rival couple in the same commune"},
        {"person": "anna_vc", "ref": "abl:5555#Person2", "match": True,
         "basis": "act", "why": "act names both parents"},
    ]) + "\n", encoding="utf-8")
    monkeypatch.setattr(labels, "LABELS", path)
    labels.reset_cache()
    try:
        r = labels.refutations()
        # The precise ruling suppresses exactly its own mention.
        assert r.of("coekelberghs", "abl:2c0d#Person1") is not None
        assert r.of("coekelberghs", "abl:2c0d#Person9") is None
        # An act-level ruling covers every participant of that act, for that person only.
        assert r.of("hendrik_vdb", "abl:9999#Person4") is not None
        assert r.of("someone_else", "abl:9999#Person4") is None
        # An ACCEPT is not a refutation — suppressing it would hide the corroboration.
        assert r.of("anna_vc", "abl:5555#Person2") is None
    finally:
        labels.reset_cache()


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


def test_the_same_name_in_another_language_still_agrees():
    """Flanders wrote its registers in Latin, then French, then Dutch, so one man is Joannes
    at his baptism, Jean at his marriage and Jan at his death — three unrelated names until
    `data/forenames.json` existed. It is not a small effect: joannes + jan + jean is 353,553
    mentions, 8% of every person the corpus names.

    The tree records him as Henricus Augustinus Vandenbemden and every act calls him Hendrik
    August, which is why three of his labels had to be resolved on a stated role instead.
    """
    from familytree.match import canonical_given, given_keys, given_overlap
    for latin, vernacular in [("Henricus", "Hendrik"), ("Joannes", "Jan"), ("Joannes", "Jean"),
                              ("Ludovicus", "Lodewijk"), ("Guilielmus", "Willem"),
                              ("Joanna", "Jeanne"), ("Maria", "Marie")]:
        exact, folded = given_overlap(given_keys(latin), given_keys(vernacular))
        assert folded and not exact, f"{latin} should fold to {vernacular}, not match exactly"

    # A name in no group is its own canonical form, so nothing unrelated is unified.
    assert canonical_given("schalandrijn") == "schalandrijn"
    assert not any(given_overlap(given_keys("Judocus"), given_keys("Petrus")))


def test_every_validator_check_at_least_runs():
    """A smoke test, and it exists because one was needed. `_check_forenames` imported
    `normalise_key` from `people` where it lives in `corpus`, so `check_data.py` crashed on
    every invocation — and the suite stayed green, because nothing here calls the validator's
    own functions. Worse, the crash was invisible: the run that should have caught it was
    piped through `grep -E "^warn|^error|OK"`, which matches no line of a traceback. Silence is
    not success.

    This asserts only that each check is callable against the real tree, not what it concludes;
    the conclusions have their own tests. An ImportError or a signature change fails here.

    THE ARGUMENTS HAVE TO BE THE REAL ONES. `_check_links` takes the set of registered source
    ids and reports a citation to anything outside it, so passing `set()` here — as this did —
    quietly asserts that no link anywhere cites a source. That held only while no link ever
    did. The moment one carried a `source:`, which README documents as the whole point of
    link-level citation, this failed with a list of sources that are in fact registered. A
    smoke test stubbed with an empty collection is not testing the check; it is testing the
    stub, which is the same mistake the docstring above already warns about.
    """
    import check_data
    from familytree.people import children_index, load_config, load_people
    from familytree.sources import load_sources
    people = load_people(load_config()["roster"])
    sites, pages = load_sources()
    source_ids = {s["id"] for s in [*sites, *pages]}
    report = check_data.Report()
    check_data._check_forenames(report)
    check_data._check_plausibility(report, people, children_index(people))
    check_data._check_labels(report, people)
    check_data._check_links(report, people, load_config()["meta"], source_ids)
    assert not report.errors, report.errors


def test_the_table_is_checked_for_the_mistake_that_was_actually_made(tmp_path, monkeypatch):
    """A cross-block token is the one error that matters, and the first draft of the table
    contained it: `corneille` is the French masculine Cornelius and it had been put into the
    feminine `cornelia` group as well. The sex partition makes a fold safe only if nothing
    appears on both sides of it.

    This calls the VALIDATOR. The version before it reimplemented the cross-block scan in its
    own body and asserted on that, so it would have passed with `_check_forenames` deleted —
    which is the failure mode of a test written against a check that had nowhere to report to
    but a module global. `Report` is what makes asking "what does it say about a bad file"
    possible.

    Against a temp file rather than the real one: the first attempt to verify this mutated
    `data/forenames.json` in place, and when the validator outran its timeout the restore never
    ran and left the table minified with the bad group still in it.
    """
    import json
    import check_data
    from familytree import people as ppl
    bad = {"m": [["cornelius", "corneille"]], "f": [["cornelia", "corneille"]]}
    (tmp_path / "forenames.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(ppl, "DATA", tmp_path)

    report = check_data.Report()
    check_data._check_forenames(report)
    assert any("corneille" in e for e in report.errors), (
        f"a token on both sides of the partition must be an error, got {report.errors}")


def test_a_good_forename_table_passes_the_same_check(tmp_path, monkeypatch):
    """The other half of the pair. A check that never passes is as useless as one that never
    fails, and only a Report can tell the two apart."""
    import json
    import check_data
    from familytree import people as ppl
    good = {"m": [["cornelius", "corneille"]], "f": [["cornelia", "cornelie"]]}
    (tmp_path / "forenames.json").write_text(json.dumps(good), encoding="utf-8")
    monkeypatch.setattr(ppl, "DATA", tmp_path)

    report = check_data.Report()
    check_data._check_forenames(report)
    assert not report.errors, report.errors


def test_the_fold_can_never_cross_the_sexes():
    """The whole reason the table is split by sex, and the reason it cannot be learned.
    Measured over the obvious candidates, the Latin masculine/feminine pairs that must NEVER
    fold are MORE similar than the Latin/vernacular pairs that should — Ludovicus~Ludovica
    0.82 against Ludovicus~Lodewijk 0.35 — so any similarity threshold merges a brother with
    his sister first, in a tree that leans on a sex veto. The partition makes that impossible
    by construction rather than by a check."""
    from familytree.match import given_keys, given_overlap
    for m, f in [("Ludovicus", "Ludovica"), ("Franciscus", "Francisca"),
                 ("Henricus", "Henrica"), ("Josephus", "Josepha"),
                 ("Joannes", "Joanna"), ("Jean", "Jeanne"), ("Augustinus", "Augustina")]:
        exact, folded = given_overlap(given_keys(m), given_keys(f))
        assert not exact and not folded, f"{m} must never fold to {f}"


def test_a_folded_forename_is_worth_less_than_an_exact_one():
    """A fold is a claim that could be wrong, so it is discounted exactly as a phonetic
    surname variant is."""
    from familytree.match import compare
    exact = compare(_cand(surname="Bostyn", given="Joannes"),
                    _cand(ref="y", surname="Bostyn", given="Joannes"))
    folded = compare(_cand(surname="Bostyn", given="Joannes"),
                     _cand(ref="y", surname="Bostyn", given="Jan"))
    assert folded.bits < exact.bits
    assert folded.bits > compare(_cand(surname="Bostyn", given="Joannes"),
                                 _cand(ref="y", surname="Bostyn", given="Petrus")).bits


def test_a_parent_cannot_be_born_after_their_own_child():
    """An act that says "X is the father of Y" and dates Y has bounded X's birth, and nothing
    read it. That let a Brussels 1888 marriage — Charles Thomas Jean Van Iseghem, father of a
    groom born 1856 — reach graftable against a Joannes Van Iseghem born 1852, at 29.7 bits on
    surname, forename and commune. The act states both halves.

    It vetoes without `stated_birth_year`, and that is deliberate: the flag exists to stop a
    year computed from a claimed age from vetoing, and this is the record asserting a
    relationship instead. The mentions it catches carry no date of their own at all.
    """
    from familytree.corpus import normalise_act
    from familytree.match import compare, from_mention, from_person
    act = normalise_act({
        "id": "t:1", "archive": "t", "archive_org": "T",
        "record": {
            "Event": {"EventType": "Huwelijk", "EventDate": {"Year": "1888"},
                      "EventPlace": {"Place": "Brussel"}},
            "Person": [
                {"@pid": "P1", "PersonName": {"PersonNameFirstName": "Alphonse",
                                              "PersonNameLastName": "Van Iseghem"},
                 "BirthDate": {"Year": "1856"}},
                {"@pid": "P2", "PersonName": {"PersonNameFirstName": "Charles Thomas Jean",
                                              "PersonNameLastName": "Van Iseghem"}},
            ],
            "RelationEP": [
                {"PersonKeyRef": "P1", "EventKeyRef": "E1", "RelationType": "Bruidegom"},
                {"PersonKeyRef": "P2", "EventKeyRef": "E1",
                 "RelationType": "Vader van de bruidegom"},
            ],
        },
    })
    dad = from_mention(next(m for m in act.people if m.pid == "P2"))
    assert dad.birth_before == 1856 - 13, "the bound comes off the child the act dates"

    ours = from_person({"id": "x", "name": "Joannes Van Iseghem", "surname": "Van Iseghem",
                        "birth": {"date": "1852", "place": "Oostende"}})
    assert compare(ours, dad).conflict, "born 1852 is not the father of a man born 1856"

    # The half that must not break: a father comfortably older than the child he is named for.
    older = from_person({"id": "y", "name": "Joannes Van Iseghem", "surname": "Van Iseghem",
                         "birth": {"date": "1820", "place": "Oostende"}})
    assert not compare(older, dad).conflict


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


def test_disagreeing_surnames_are_never_graftable_however_the_relatives_agree():
    """The veto that had no test, which is how it came to be switched off by a variable
    name. The kin loop reused `same_surname`, so by the time the surname veto read it, it
    meant "this relative's surname agrees" — and a pair whose OWN surnames plainly
    disagreed became graftable whenever any one relative matched.

    Over the tree's first 100 people and 298,816 compared pairs it fired exactly once, on
    the worst pair available: Maria Anna Vandenhoven scored as Maria Theresia
    Coekelberghs at 21.6 bits, which is the identification a verifier had already refuted
    in writing and retracted a person record over.

    Both halves are asserted, because a veto that always fires is as wrong as one that
    never does.
    """
    from familytree.match import compare
    kin = [("father", "vandenbemden", frozenset({"willem"}))]
    disagree = dict(given="Maria", birth_year=1841, birth_place="Kraainem",
                    places=["Kraainem"], stated_birth_year=True, kin=kin)
    a = _cand(surname="Coekelberghs", **disagree)
    b = _cand(ref="y", surname="Vandenhoven", **dict(disagree, kin=list(kin)))
    m = compare(a, b)
    assert m.independent >= 2 and m.distinguishing >= 6, "otherwise this proves nothing"
    assert not m.graftable, "disagreeing surnames must veto, whatever the relatives say"

    # And the surname agreeing still grafts, so the veto has not simply been nailed shut.
    c = _cand(ref="z", surname="Coekelberghs", **dict(disagree, kin=list(kin)))
    assert compare(a, c).graftable


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


# ---------- links as facts: confidence and sources on edges ----------
#
# `father`, `mother` and each spouse carry their own confidence and citation, on the same
# scale a person does, because it is the same question asked of a different object. The
# whole arrangement rests on one property — the scorer cannot see an `asm` link — and that
# property is invisible when it breaks: nothing raises, the graft simply scores as
# well-supported because the tree's own guess came back to it as evidence.


def _records(*records):
    """Like `_tree` above, but taking whole records: these tests need `name` and nested link
    blocks, which the keyword form cannot express. Records go through `normalise_links` so
    they arrive in the shape every reader actually sees."""
    from familytree.people import normalise_links
    return {r["id"]: normalise_links(dict(r)) for r in records}


def test_the_scalar_and_the_block_form_are_one_shape_in_memory():
    """The scalar stays legal in the files — 646 links are simply known and a three-line
    block to say so would add two thousand lines of ceremony for no fact gained. But two
    shapes in memory is how this goes quietly wrong: `if p.get("father")` is truthy for
    both, and `p["father"] == pid` silently goes False against a dict, so a missed reader
    would not raise, it would just stop finding parents."""
    from familytree.people import edge_confidence, normalise_links, parent_id
    plain = normalise_links({"id": "a", "name": "A", "father": "dad", "confidence": "doc"})
    block = normalise_links({"id": "b", "name": "B", "confidence": "doc",
                             "father": {"id": "dad", "confidence": "asm", "note": "one id"}})
    assert parent_id(plain, "father") == parent_id(block, "father") == "dad"
    # An unqualified link states no confidence and does not borrow the person's. Inheriting
    # would invent a grade no source gave, and on a marriage — one link written on two
    # records — it made his `doc` and her `sup` disagree about the same act.
    assert edge_confidence(plain, "father") is None
    assert edge_confidence(block, "father") == "asm"


def test_an_assumed_parent_is_not_evidence():
    """The property the whole feature rests on.

    A parent is an independent identifier *because* the tree is sure of them. Put a guess in
    that slot and the two-identifier floor stops being a floor: this project's own unverified
    conclusion comes back as corroboration, and the next graft is reasoned about as if the
    first were settled. It compounds — every link in the chain scores well — which is why it
    is pinned rather than left to the reading of one function.
    """
    from familytree.match import from_person
    dad = {"id": "dad", "name": "Joannes Van Iseghem", "surname": "Van Iseghem"}
    firm = {"id": "kid", "name": "Emma Van Iseghem", "surname": "Van Iseghem", "father": "dad"}
    guess = dict(firm, father={"id": "dad", "confidence": "asm", "note": "commune only"})

    assert any(k[0] == "father" for k in from_person(*_two(firm, dad)).kin)
    assert not any(k[0] == "father" for k in from_person(*_two(guess, dad)).kin)


def _two(subject, other):
    people = _records(subject, other)
    return people[subject["id"]], people


def test_a_doc_link_to_a_sup_person_is_still_evidence():
    """The two axes really are independent, in the direction that matters for recall.

    Grading the LINK must not quietly re-grade the person or vice versa. A well-attested
    marriage act can establish a parent link to somebody whose own dates are barely known,
    and that link is still one of the two identifiers.
    """
    from familytree.match import from_person
    dad = {"id": "dad", "name": "Joannes Van Iseghem", "surname": "Van Iseghem",
           "confidence": "unk"}
    kid = {"id": "kid", "name": "Emma Van Iseghem", "surname": "Van Iseghem",
           "confidence": "doc", "father": {"id": "dad", "confidence": "doc",
                                           "source": "oostende-1907"}}
    assert any(k[0] == "father" for k in from_person(*_two(kid, dad)).kin)


def test_a_child_attached_by_an_assumed_link_is_not_evidence_for_the_parent():
    """The same link, read from the other end.

    Excluding it upward only would have left the hole open: the child still names the parent,
    so `children_index` still lists them, and the parent's candidate would quietly regain the
    very kin evidence the child's own record declined to assert.
    """
    from familytree.match import from_person
    people = _records(
        {"id": "dad", "name": "Joannes Van Iseghem", "surname": "Van Iseghem"},
        {"id": "kid", "name": "Emma Van Iseghem", "surname": "Van Iseghem",
         "father": {"id": "dad", "confidence": "asm", "note": "commune only"}},
    )
    children = {"dad": ["kid"]}
    assert not any(k[0] == "child" for k in from_person(people["dad"], people, children).kin)
    # And the sex the role would have implied does not leak in either — one rule, no
    # exceptions to remember.
    assert from_person(people["dad"], people, children).sex is None


def test_what_an_assumed_link_carries_is_measured_not_counted():
    """`at_stake` is who would leave with the link, not who sits above it.

    Counting the parent's own ancestors is the obvious implementation and it is wrong
    wherever the tree folds back on itself: a shared ancestor reached by both of a couple's
    lines is not at risk from either one, and reporting them inflates the price of every
    guess in a collapsed pedigree — the tree this project is building.
    """
    from familytree.people import weak_edges
    people = _records(
        {"id": "kid", "name": "Kid", "mother": "mum",
         "father": {"id": "dad", "confidence": "asm", "note": "one identifier"}},
        {"id": "dad", "name": "Dad", "father": "shared"},
        {"id": "mum", "name": "Mum", "father": "shared"},
        {"id": "shared", "name": "Shared Ancestor"},
    )
    edge, = weak_edges(people, ["kid"])
    assert edge["at_stake"] == ["dad"]   # not ["dad", "shared"] — mum still reaches shared

    # Break the other route and the very same link is suddenly carrying the shared ancestor
    # too. Same guess, same record, unchanged note: what it costs to be wrong is a fact about
    # the tree around it, which is why it is derived on every run and never stored.
    del people["mum"]["father"]
    edge, = weak_edges(people, ["kid"])
    assert edge["at_stake"] == ["dad", "shared"]


def test_unk_is_refused_on_a_link():
    """On a person `unk` means "not researched yet". A link has no such state — one whose
    existence is unknown is an absent link — so allowing the code would put a drawn edge and
    a nonexistent one in the same bucket."""
    import check_data
    people = _records({"id": "kid", "name": "Kid",
                       "father": {"id": "dad", "confidence": "unk"}},
                      {"id": "dad", "name": "Dad"})
    report = check_data.Report()
    check_data._check_links(report, people, {"roots": ["kid"]}, set())
    assert any("not a link" in e for e in report.errors), report.errors


def test_an_assumed_link_must_say_what_it_rests_on():
    """An assumption nobody explained cannot be checked by anyone later, including whoever
    made it. The note IS the finding; the link is only its consequence, and it is what the
    page shows beside the red mark."""
    import check_data
    people = _records({"id": "kid", "name": "Kid",
                       "father": {"id": "dad", "confidence": "asm"}},
                      {"id": "dad", "name": "Dad"})
    report = check_data.Report()
    check_data._check_links(report, people, {"roots": ["kid"]}, set())
    assert any("says nothing about why" in e for e in report.errors), report.errors


def test_a_link_cites_a_registered_source_or_none_at_all():
    """Rule 2 — "every new parent link cites a source" — made checkable for the first time.
    While `sources` was a person-level list it could not be verified by anything: the
    citation and the claim sat in the same file without being attached to each other."""
    import check_data
    people = _records({"id": "kid", "name": "Kid",
                       "father": {"id": "dad", "source": "not-registered"}},
                      {"id": "dad", "name": "Dad"})
    report = check_data.Report()
    check_data._check_links(report, people, {"roots": ["kid"]}, {"oostende-1907"})
    assert any("not in research/sources.json" in e for e in report.errors), report.errors


def test_the_cost_of_a_guess_warns_and_never_fails():
    """Stacking and blast radius are warnings, and that is a deliberate line.

    Each is repaired by research nobody can do on demand, and the project's rule is that the
    validator is green before a commit. Failing on them would make the cheapest way back a
    deletion of the record of the guess — the tree would get LESS honest under pressure,
    which is exactly backwards.
    """
    import check_data
    people = _records(
        {"id": "kid", "name": "Kid",
         "father": {"id": "dad", "confidence": "asm", "note": "one identifier"}},
        {"id": "dad", "name": "Dad",
         "father": {"id": "granddad", "confidence": "asm", "note": "one identifier"}},
        {"id": "granddad", "name": "Granddad"},
    )
    report = check_data.Report()
    check_data._check_links(report, people, {"roots": ["kid"]}, set())
    assert not report.errors, report.errors
    assert any("guess on a guess" in w for w in report.warnings), report.warnings


def test_the_page_is_told_why_a_link_is_red_and_only_when_it_is():
    """The reason travels with the mark, and ordinary links say nothing about themselves.

    Shipping every link's confidence would put a badge on almost every card, which is how a
    warning stops being read; shipping none would leave a red edge whose warrant lives in a
    research log nobody reading the tree will open.
    """
    from familytree.people import to_browser_record
    firm = to_browser_record(_records(
        {"id": "kid", "name": "Kid", "confidence": "sup",
         "father": {"id": "dad", "confidence": "doc", "source": "oostende-1907"}})["kid"])
    assert firm["father"] == "dad" and "links" not in firm

    weak = to_browser_record(_records(
        {"id": "kid", "name": "Kid", "confidence": "sup",
         "father": {"id": "dad", "confidence": "asm",
                    "note": "1907 act, commune agrees; no birth act"}})["kid"])
    assert weak["father"] == "dad"          # still a plain id — the renderer is unchanged
    assert weak["links"]["father"]["confidence"] == "asm"
    assert "commune agrees" in weak["links"]["father"]["note"]


# ---------- siblings: the one relationship that is stored ----------
#
# `siblings` is a deliberate exception to "a relationship is never a field", and it is only
# safe because it is fenced to the case where there is nothing to be a second copy OF. The
# fence is the tests below; without them the field is just the duplication the data model
# spent its whole design avoiding.


def test_a_derivable_sibship_is_written_out_and_kept_in_step():
    """Redundancy is the point, and it is safe because it is checked.

    Sibling edges duplicate what the parent links already say — 994 of them across the tree.
    A copy nothing verifies is exactly the failure the data model is built to avoid, so this
    one is generated by `familytree.edges.planned` and the validator fails on any record that
    disagrees with it. Correct a parent link and the sibling edges resting on it go stale
    loudly, on the next build, rather than quietly describing a family that changed.
    """
    from familytree.edges import planned
    people = _records(
        {"id": "a", "name": "A", "father": "dad"},
        {"id": "b", "name": "B", "father": "dad"},
        {"id": "dad", "name": "Dad"},
    )
    plan = planned(people)
    assert [s["id"] for s in plan["a"]["siblings"]] == ["b"]
    assert [s["id"] for s in plan["b"]["siblings"]] == ["a"]

    # Move B to another father and the plan changes with it — which is what "cannot drift"
    # means in practice: the edge is never a second opinion about who B's father was.
    people["b"]["father"] = {"id": "other"}
    people["other"] = {"id": "other", "name": "Other"}
    assert "siblings" not in planned(people)["a"]


def test_a_stated_sibship_the_parent_links_contradict_is_refused():
    """The one thing redundancy must not be allowed to hide. Two people whose parents are
    both fully recorded and share nobody are not siblings, whatever an entry says — one of
    the two facts is wrong and the build should say so. Only fully-known pairs are judged: a
    missing parent is the ordinary case the field exists to serve."""
    import check_data
    people = _records(
        {"id": "a", "name": "A", "father": "d1", "mother": "m1",
         "siblings": [{"id": "b"}]},
        {"id": "b", "name": "B", "father": "d2", "mother": "m2",
         "siblings": [{"id": "a"}]},
        *[{"id": x, "name": x.upper()} for x in ("d1", "m1", "d2", "m2")],
    )
    report = check_data.Report()
    check_data._check_siblings(report, "a", people["a"], people, set())
    assert any("cannot both be right" in e for e in report.errors), report.errors


def test_a_sibship_the_parent_links_cannot_state_is_allowed():
    """The case the field exists for, and it is a real one. `antoine_vanald` records a
    probable elder sister named by a third act giving the same parent pair, and had to give
    the fact up — "she cannot be linked as a sibling while the parents themselves are only a
    frontier", because the father's forename disagrees across all three acts."""
    import check_data
    people = _records(
        {"id": "a", "name": "A", "siblings": [
            {"id": "b", "confidence": "asm", "note": "same parent pair in three acts; "
             "neither parent graftable"}]},
        {"id": "b", "name": "B", "siblings": [
            {"id": "a", "confidence": "asm", "note": "same parent pair in three acts; "
             "neither parent graftable"}]},
    )
    report = check_data.Report()
    for pid in ("a", "b"):
        check_data._check_siblings(report, pid, people[pid], people, set())
    assert not report.errors, report.errors


def test_a_sibling_link_is_mutual_and_agrees_with_itself():
    """Siblinghood is symmetric, so a one-sided entry makes the tree answer differently
    depending on whose record is read — the same failure the marriage invariant exists for,
    and it is checked the same way: one relationship, one set of facts."""
    import check_data
    one_sided = _records({"id": "a", "name": "A", "siblings": [{"id": "b"}]},
                         {"id": "b", "name": "B"})
    report = check_data.Report()
    check_data._check_siblings(report, "a", one_sided["a"], one_sided, set())
    assert any("does not list" in e for e in report.errors), report.errors

    disagree = _records(
        {"id": "a", "name": "A", "siblings": [{"id": "b", "confidence": "doc"}]},
        {"id": "b", "name": "B", "siblings": [{"id": "a", "confidence": "asm",
                                              "note": "one identifier"}]},
    )
    report = check_data.Report()
    check_data._check_siblings(report, "a", disagree["a"], disagree, set())
    assert any("disagree about being siblings" in e for e in report.errors), report.errors


def test_a_sibling_needs_a_record_not_a_name():
    """Unlike a spouse. A spouse with no record still belongs on the card as a name; a
    sibling with no record connects nothing in the graph, which is the only reason to state
    one — and prose already holds an unlinked name better than a field can."""
    import check_data
    people = _records({"id": "a", "name": "A", "siblings": [{"note": "his brother Willem"}]})
    report = check_data.Report()
    check_data._check_siblings(report, "a", people["a"], people, set())
    assert any('no "id"' in e for e in report.errors), report.errors


def test_a_stated_sibling_of_a_blood_relative_is_blood():
    """Objective 2, through the door the parent links could not open. An ancestor's sibling
    and that sibling's descendants are in scope because they are blood — and the tree only
    knows a stated sibling from a derived one because the derived one happened to have a
    parent that could be grafted."""
    from familytree.people import census
    people = _records(
        {"id": "kid", "name": "Kid", "father": "dad"},
        {"id": "dad", "name": "Dad", "siblings": [{"id": "uncle", "confidence": "asm",
                                                   "note": "same act"}]},
        {"id": "uncle", "name": "Uncle", "siblings": [{"id": "dad", "confidence": "asm",
                                                       "note": "same act"}]},
        {"id": "cousin", "name": "Cousin", "father": "uncle"},
    )
    c = census(people, {"meta": {"roots": ["kid"]}, "root": "kid"})
    # dad is the one ancestor; uncle and cousin are blood through the stated link.
    assert (c["ancestors"], c["relatives"], c["others"]) == (1, 3, 0)


def test_siblings_derived_and_stated_arrive_as_one_list():
    """A reader does not care which mechanism knew it. The two cannot overlap — a stated
    link between two people who already share a parent fails the build — so one list is
    both simpler and unambiguous."""
    from familytree.people import siblings_of
    people = _records(
        {"id": "a", "name": "A", "father": "dad", "siblings": [{"id": "c"}]},
        {"id": "b", "name": "B", "father": "dad"},
        {"id": "c", "name": "C", "siblings": [{"id": "a"}]},
        {"id": "dad", "name": "Dad"},
    )
    assert sorted(siblings_of(people, "a")) == ["b", "c"]


# ---------- the rendered docs, which nothing used to check ----------


def test_docs_signature_tracks_its_inputs(tmp_path, monkeypatch):
    """A docs edit must change the signature, and a revert must change it back.

    `dist/docs/` is committed like the bundle, and it was the one generated artefact with
    no staleness check — the validator cannot import MkDocs to regenerate it, so it
    compares a signature over the inputs instead. This pins that the signature is actually
    sensitive to the thing it claims to cover.
    """
    from familytree import docsite
    docs = tmp_path / "docs"
    (docs / "method").mkdir(parents=True)
    (docs / "index.md").write_text("# hello\n", encoding="utf-8")
    (docs / "method" / "linkage.md").write_text("# linkage\n", encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: t\n", encoding="utf-8")
    monkeypatch.setattr(docsite, "ROOT", tmp_path)
    monkeypatch.setattr(docsite, "DOCS_DIR", docs)
    monkeypatch.setattr(docsite, "CONFIG", config)

    before = docsite.signature()
    (docs / "method" / "linkage.md").write_text("# linkage, edited\n", encoding="utf-8")
    assert docsite.signature() != before, "editing a docs page must change the signature"
    (docs / "method" / "linkage.md").write_text("# linkage\n", encoding="utf-8")
    assert docsite.signature() == before, "reverting must restore it — content, not mtime"

    # mkdocs.yml is an input too: the nav decides which pages exist at all.
    config.write_text("site_name: t\nnav: [index.md]\n", encoding="utf-8")
    assert docsite.signature() != before, "mkdocs.yml must be covered"


def test_docs_signature_ignores_os_droppings(tmp_path, monkeypatch):
    """A .DS_Store landing next to the docs must not report the whole site as stale."""
    from familytree import docsite
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# hello\n", encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: t\n", encoding="utf-8")
    monkeypatch.setattr(docsite, "ROOT", tmp_path)
    monkeypatch.setattr(docsite, "DOCS_DIR", docs)
    monkeypatch.setattr(docsite, "CONFIG", config)

    before = docsite.signature()
    (docs / ".DS_Store").write_bytes(b"\x00\x01")
    assert docsite.signature() == before


def test_docs_staleness_is_reported_for_each_way_it_goes_wrong(tmp_path, monkeypatch):
    """The three states, and the message each gets. The middle one is why the signature
    file has no leading dot: MkDocs's clean skips dotfiles (site_dir may hold .git), so a
    dotted name SURVIVED a bare `mkdocs build` and a freshly-rendered site was reported
    stale — fail-closed, but with a message that sent you looking for the wrong thing."""
    from familytree import docsite
    docs, site = tmp_path / "docs", tmp_path / "dist" / "docs"
    docs.mkdir()
    site.mkdir(parents=True)
    (docs / "index.md").write_text("# hello\n", encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: t\n", encoding="utf-8")
    monkeypatch.setattr(docsite, "ROOT", tmp_path)
    monkeypatch.setattr(docsite, "DOCS_DIR", docs)
    monkeypatch.setattr(docsite, "CONFIG", config)
    monkeypatch.setattr(docsite, "SITE_DIR", site)
    monkeypatch.setattr(docsite, "SIGNATURE", site / "build-signature")

    assert "has not been built" in docsite.stale_reason()

    (site / "index.html").write_text("<html></html>", encoding="utf-8")
    assert "without recording" in docsite.stale_reason()

    docsite.record()
    assert docsite.stale_reason() is None

    (docs / "index.md").write_text("# hello, edited\n", encoding="utf-8")
    assert "out of date" in docsite.stale_reason()

    docsite.record()
    assert docsite.stale_reason() is None
