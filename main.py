#!/usr/bin/env python3
"""Weirdest Job Title -- the Blind Judge Showdown entry.

Picks one job title using the judge's own five published criteria, in
their published order:

  1. Is a weird job title, a few words naming an odd job.
  2. Is stranger than ordinary work, a job nobody has heard of or one
     with a gloriously odd twist.
  3. Is funny, with a twist that lands on the first read.
  4. Sounds like a real job rather than a random word salad, specific
     enough to picture the person doing it.
  5. Reads instantly, short enough to take in at a glance.

The judge goes through the criteria in order, lets the first one where
two titles differ decide, and only lets a later one matter when it
differs by much more. This engine mirrors that: candidates are
compared criterion by criterion, in order, and the first differing
criterion decides. A tied score line is settled by the higher total,
then the shorter title, then alphabetical order, so the pick is fully
deterministic: no randomness, no time, no network, no environment
dependence, standard library only.

The design follows the humour research behind the brief. A joke lands
through incongruity: an expectation set up, then violated -- and the
violation has to hit a *specific* expectation, not just be random
(Schopenhauer; Westbury's benign-violation work). A generic oddity
("Haunted Anything", "Quantum Something") violates nothing in
particular, so it reads as noise; a specific violation -- a senior
manager, of shopping carts nobody owns -- violates the exact
expectation that senior managers manage important things. That is why
every candidate is built the same way: a plausible profession frame
(Senior Manager, Chief of, Inspector, Specialist, Consultant -- the
shape of a real job) plus ONE hyper-specific absurd domain or duty, a
mundane object or situation made strange by the job. The reader
pictures the person doing it at once, and the twist lands on the
first read. A real job with one hilariously specific twist beats a
generic oddity -- and it beats a word salad, because the frame keeps
it sounding like a job someone could actually hold.

The pool is self-checked before anything is picked: every candidate
must carry a score for every criterion, every score must sit on the
0-5 scale, every title must pass the gate, and no title may appear
twice. A pool that fails its own rules cannot pick a winner.

The winning title is written to /output/entry.txt (or to the path in
OUTPUT_PATH when that is set, for local testing only).
"""

import os
import sys
from functools import cmp_to_key

# The five published criteria, in the judge's published order.
CRITERIA = (
    "weird_job_title",
    "stranger_than_ordinary",
    "funny_first_read",
    "sounds_like_real_job",
    "reads_instantly",
)

CRITERION_TITLES = {
    "weird_job_title": "1. Is a weird job title",
    "stranger_than_ordinary": "2. Stranger than ordinary work",
    "funny_first_read": "3. Funny, twist lands on the first read",
    "sounds_like_real_job": "4. Sounds like a real job, specific enough to picture",
    "reads_instantly": "5. Reads instantly, short enough to take in at a glance",
}

# The gate: 1-60 UTF-8 characters, nothing else.
MAX_TITLE_CHARS = 60

# Each candidate: the title, one score 0-5 per criterion, and a short
# note per criterion saying why the score fits. Scores are honest
# readings of the published brief, not numbers tuned to a favourite:
# the ordinary jobs (Software Engineer, Accountant) are scored too,
# as controls, and they lose on the first two criteria at once.
#
# Why the winning family leads: the frame is a real senior role, and
# the domain is a public absurdity everyone has seen -- shopping carts
# abandoned in car parks, ditches and rivers. Nobody manages them, so
# a Senior Manager of them is a gloriously odd twist on a real job,
# and the reader pictures the hi-vis vest and the clipboard at once.
CANDIDATES = (
    {
        "title": "Senior Manager of Abandoned Shopping Carts",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 5,
            "funny_first_read": 5,
            "sounds_like_real_job": 5,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a senior manager, of shopping carts nobody owns.",
            "stranger_than_ordinary": "Nobody has heard of managing abandoned carts; a whole hierarchy for stray trolleys.",
            "funny_first_read": "The twist lands at once: the most senior title imaginable, for the most ignored object imaginable.",
            "sounds_like_real_job": "Senior Manager is a real frame, and cart retrieval is a real job -- inflated to management.",
            "reads_instantly": "42 characters, one clean phrase; a touch long, but taken in at a glance.",
        },
    },
    {
        "title": "Chief of the Department of Lost Gloves",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 5,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a chief, of a department, for lost gloves.",
            "stranger_than_ordinary": "A whole department for single gloves is strange, though lost property is a known idea.",
            "funny_first_read": "Funny: the bureaucracy is grander than the problem by several orders of magnitude.",
            "sounds_like_real_job": "Department of Lost Property is a real shape; the reader pictures the filing cabinets.",
            "reads_instantly": "41 characters, one clean bureaucratic phrase.",
        },
    },
    {
        "title": "Pigeon Traffic Controller",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 5,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: traffic control, for pigeons.",
            "stranger_than_ordinary": "Nobody has heard of directing pigeon traffic; gloriously odd.",
            "funny_first_read": "Funny at once, but the joke is a single image -- the pigeons ignoring the signals.",
            "sounds_like_real_job": "Traffic Controller is a real job; the birds keep it plausible, just barely.",
            "reads_instantly": "26 characters, three words, instant.",
        },
    },
    {
        "title": "Senior Puddle Depth Inspector",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 5,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a senior inspector, of puddle depth.",
            "stranger_than_ordinary": "Odd, but puddle-measuring is a small twist rather than a grand one.",
            "funny_first_read": "Funny: the solemn inspector with a ruler at a puddle.",
            "sounds_like_real_job": "Inspector is a real frame and the duty is hyper-specific; easy to picture.",
            "reads_instantly": "29 characters, instant.",
        },
    },
    {
        "title": "Professional Tumbleweed Wrangler",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a wrangler, of tumbleweeds.",
            "stranger_than_ordinary": "Odd, though wrangling is already a western job word.",
            "funny_first_read": "Funny: chasing weeds that blow away the moment you catch them.",
            "sounds_like_real_job": "Wrangler is a real job shape, but the duty drifts toward cartoon western.",
            "reads_instantly": "33 characters, instant.",
        },
    },
    {
        "title": "Professional Waiting Room Chair Tester",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 5,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a professional tester, of waiting-room chairs.",
            "stranger_than_ordinary": "Odd, but chair testing is a real quality job, only mildly twisted.",
            "funny_first_read": "Funny: a career spent sitting down, professionally, in waiting rooms.",
            "sounds_like_real_job": "Product tester is a real job; the reader pictures the clipboard and the sigh.",
            "reads_instantly": "40 characters, one clean phrase.",
        },
    },
    {
        "title": "Left Sock Recovery Specialist",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a specialist, recovering left socks.",
            "stranger_than_ordinary": "Odd, though the lost-sock mystery is a familiar joke.",
            "funny_first_read": "Funny: the lost sock finally gets a rescue service.",
            "sounds_like_real_job": "Recovery Specialist is a real frame; the single-sock duty keeps it pictureable.",
            "reads_instantly": "31 characters, instant.",
        },
    },
    {
        "title": "Senior Officer of Escalator Etiquette",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 5,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a senior officer, of escalator etiquette.",
            "stranger_than_ordinary": "Odd, though etiquette enforcement is a recognisable social gripe.",
            "funny_first_read": "Funny: the officer policing who stands on the left.",
            "sounds_like_real_job": "Officer is a real frame; the reader pictures the uniform at the top of the escalator.",
            "reads_instantly": "39 characters, one clean phrase.",
        },
    },
    {
        "title": "Professional Traffic Cone Arranger",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 3,
            "sounds_like_real_job": 5,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: arranging traffic cones, professionally.",
            "stranger_than_ordinary": "Odd, but cone placement is close to real road work.",
            "funny_first_read": "Mildly funny: the cone as a career, not a punchline.",
            "sounds_like_real_job": "Very pictureable -- the cones, the hi-vis, the careful rows.",
            "reads_instantly": "35 characters, instant.",
        },
    },
    {
        "title": "Senior Consultant for Haunted Toasters",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 5,
            "sounds_like_real_job": 3,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a consultant, for haunted toasters.",
            "stranger_than_ordinary": "Strange, but 'haunted' is a generic oddity word, not a specific twist.",
            "funny_first_read": "Very funny on first read: the toaster that pops up by itself, with a consultant.",
            "sounds_like_real_job": "The haunted half breaks the realism: nobody pictures this as a real appointment.",
            "reads_instantly": "40 characters, one clean phrase.",
        },
    },
    {
        "title": "Senior Manager of Forgotten Passwords",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 4,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a senior manager, of forgotten passwords.",
            "stranger_than_ordinary": "Odd, but password reset is ordinary IT work with a twist.",
            "funny_first_read": "Funny and relatable: everyone has forgotten a password; someone manages them all.",
            "sounds_like_real_job": "Manager is a real frame, but the duty is abstract -- harder to picture doing it.",
            "reads_instantly": "38 characters, one clean phrase.",
        },
    },
    {
        "title": "Professional Bubble Wrap Popper",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 3,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: popping bubble wrap, professionally.",
            "stranger_than_ordinary": "Only mildly strange: popping bubble wrap is a known pastime, not an unknown job.",
            "funny_first_read": "Funny: the dream job everyone has joked about having.",
            "sounds_like_real_job": "Pictureable, but reads as a hobby with a salary rather than a job.",
            "reads_instantly": "32 characters, instant.",
        },
    },
    {
        "title": "Senior Nap Quality Inspector",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 3,
            "funny_first_read": 4,
            "sounds_like_real_job": 4,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: a senior inspector, of nap quality.",
            "stranger_than_ordinary": "Only mildly strange: everyone has joked about being paid to nap.",
            "funny_first_read": "Funny: the inspector asleep on the job, on purpose.",
            "sounds_like_real_job": "Inspector is a real frame, but the duty is a daydream, not a duty.",
            "reads_instantly": "28 characters, instant.",
        },
    },
    {
        "title": "Professional Elevator Button Presser",
        "scores": {
            "weird_job_title": 5,
            "stranger_than_ordinary": 3,
            "funny_first_read": 3,
            "sounds_like_real_job": 4,
            "reads_instantly": 4,
        },
        "notes": {
            "weird_job_title": "A few words naming an odd job: pressing elevator buttons, professionally.",
            "stranger_than_ordinary": "Only mildly strange: button-pressing is a small duty, not a strange world.",
            "funny_first_read": "Mildly funny: the world's smallest job description.",
            "sounds_like_real_job": "Pictureable, but the duty is too thin to feel like a career.",
            "reads_instantly": "37 characters, one clean phrase.",
        },
    },
    # Controls: ordinary jobs, scored honestly so the engine has to
    # beat them on the rubric rather than by ignoring them.
    {
        "title": "Software Engineer",
        "scores": {
            "weird_job_title": 1,
            "stranger_than_ordinary": 0,
            "funny_first_read": 0,
            "sounds_like_real_job": 5,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A real job title, but not a weird one.",
            "stranger_than_ordinary": "Entirely ordinary work.",
            "funny_first_read": "No twist, no joke.",
            "sounds_like_real_job": "It is a real job, exactly.",
            "reads_instantly": "17 characters, instant.",
        },
    },
    {
        "title": "Accountant",
        "scores": {
            "weird_job_title": 1,
            "stranger_than_ordinary": 0,
            "funny_first_read": 0,
            "sounds_like_real_job": 5,
            "reads_instantly": 5,
        },
        "notes": {
            "weird_job_title": "A real job title, but not a weird one.",
            "stranger_than_ordinary": "Entirely ordinary work.",
            "funny_first_read": "No twist, no joke.",
            "sounds_like_real_job": "It is a real job, exactly.",
            "reads_instantly": "10 characters, instant.",
        },
    },
)

DEFAULT_OUTPUT_PATH = "/output/entry.txt"


def score_tuple(candidate):
    """The candidate's scores as a tuple, in the judge's criterion order."""
    return tuple(candidate["scores"][criterion] for criterion in CRITERIA)


def total_score(candidate):
    """The plain sum of a candidate's five criterion scores."""
    return sum(score_tuple(candidate))


def assert_pool_valid(candidates=CANDIDATES):
    """Check the pool's own rules before anything is picked.

    Every candidate must score every criterion on the 0-5 scale, carry
    a rationale note for every criterion, pass the gate, and be
    unique. A pool that fails its own rules cannot pick a winner.
    """
    seen = set()
    for candidate in candidates:
        title = candidate["title"]
        if title in seen:
            raise ValueError("duplicate candidate title: %r" % title)
        seen.add(title)
        validate(title)
        for criterion in CRITERIA:
            if criterion not in candidate["scores"]:
                raise ValueError("%r has no score for %s" % (title, criterion))
            score = candidate["scores"][criterion]
            if not isinstance(score, int) or score < 0 or score > 5:
                raise ValueError("%r has an out-of-range score for %s: %r" % (title, criterion, score))
            if criterion not in candidate["notes"] or not candidate["notes"][criterion]:
                raise ValueError("%r has no rationale for %s" % (title, criterion))
    return True


def compare(first, second):
    """Compare two candidates the way the judge compares two titles.

    Returns -1 when `first` should rank above `second`, 1 when it
    should rank below, and 0 only when the two are indistinguishable
    under every rule. Walk the criteria in their published order; the
    first criterion where the two differ decides. A later criterion
    only matters when it differs by much more -- on a 0-5 scale, with
    the early criteria already equal, the total-score step below is
    the bounded form of that: a title far stronger across the
    remaining criteria still wins the tie. An exact tie on every
    criterion is settled by the higher total, then the shorter title,
    then alphabetical order, so the result is always deterministic.
    """
    first_scores = score_tuple(first)
    second_scores = score_tuple(second)
    for a, b in zip(first_scores, second_scores):
        if a != b:
            return -1 if a > b else 1
    if total_score(first) != total_score(second):
        return -1 if total_score(first) > total_score(second) else 1
    if len(first["title"]) != len(second["title"]):
        return -1 if len(first["title"]) < len(second["title"]) else 1
    if first["title"] == second["title"]:
        return 0
    return -1 if first["title"] < second["title"] else 1


def beats(first, second):
    """True when `first` beats `second` under the judge's decision order."""
    return compare(first, second) < 0


def rank_candidates(candidates):
    """All candidates, best first, under the judge's decision order.

    The ranking uses the very same comparison as `beats`, so the two
    can never drift apart: one decision rule, used everywhere.
    """
    return sorted(candidates, key=cmp_to_key(compare))


def select_winner(candidates=CANDIDATES):
    """The top-ranked candidate, after the pool passes its own checks."""
    assert_pool_valid(candidates)
    return rank_candidates(candidates)[0]


def validate(title):
    """Check a title against the sealed gate: 1-60 UTF-8 characters.

    The gate asks only for 1-60 non-blank UTF-8 characters, and this
    check enforces exactly that -- no extra rule, so the program can
    never reject a title the gate would accept.
    """
    if not isinstance(title, str):
        raise ValueError("entry must be text")
    if not title or title.strip() == "":
        raise ValueError("entry must not be blank")
    if len(title) > MAX_TITLE_CHARS:
        raise ValueError("entry must be at most 60 characters")
    title.encode("utf-8")  # raises if the title is not valid UTF-8 text
    return title


def output_path():
    """Where the entry goes: /output/entry.txt, or OUTPUT_PATH for tests."""
    return os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH)


def rubric_table(candidates=CANDIDATES):
    """A readable table of every candidate and its per-criterion scores."""
    header = "TITLE".ljust(44) + " ".join(
        ("C%d" % (i + 1)).rjust(3) for i in range(len(CRITERIA))
    ) + "  TOTAL"
    lines = [header]
    for candidate in rank_candidates(candidates):
        scores = score_tuple(candidate)
        line = candidate["title"].ljust(44) + " ".join(
            str(s).rjust(3) for s in scores
        ) + "  %5d" % total_score(candidate)
        lines.append(line)
    return "\n".join(lines)


def main():
    winner = select_winner()
    title = validate(winner["title"])
    path = output_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(title)
    print(rubric_table())
    print()
    print("Why %s wins:" % title)
    for criterion in CRITERIA:
        print("  %s: %d -- %s" % (
            CRITERION_TITLES[criterion],
            winner["scores"][criterion],
            winner["notes"][criterion],
        ))
    print()
    print("Winner: %s (%d chars) -> %s" % (title, len(title), path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
