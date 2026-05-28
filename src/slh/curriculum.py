"""Curriculum under test: 7th-grade rational-number (fraction) arithmetic.

The subject domain is chosen because fraction reasoning has the deepest
documented-misconception literature in mathematics education. Every
misconception and distractor below is grounded in a real, cited error pattern,
which is what lets the synthetic learners behave like real students rather than
random noise generators.

References (see docs/research_notes.md for full discussion):
  - Ashlock, R. (2010). *Error Patterns in Computation*. (systematic error
    patterns such as "add across".)
  - Siegler, R. et al. (2011). *Early predictors of high-school math
    achievement*. (fraction magnitude understanding predicts later success.)
  - Ni, Y. & Zhou, Y. (2005). *Teaching and learning fraction and rational
    numbers: the origins and implications of whole number bias.*
  - NCTM (2014). *Principles to Actions.* (comparison and equivalence
    progressions.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd

# --- Concepts taught and assessed -----------------------------------------

CONCEPTS: tuple[str, ...] = (
    "equivalence",       # 1/2 == 2/4
    "comparison",        # order two fractions
    "addition_like",     # a/b + c/b
    "addition_unlike",   # a/b + c/d
)


# --- Misconception catalog (each grounded in documented student behavior) --


@dataclass(frozen=True)
class Misconception:
    """A documented, named student error pattern."""

    id: str
    name: str
    description: str
    affected_concepts: tuple[str, ...]
    citation: str


MISCONCEPTIONS: dict[str, Misconception] = {
    m.id: m
    for m in [
        Misconception(
            id="add_across",
            name="Add Across",
            description="Adds numerators and denominators separately: "
            "a/b + c/d = (a+c)/(b+d).",
            affected_concepts=("addition_like", "addition_unlike"),
            citation="Ashlock (2010), Error Patterns in Computation",
        ),
        Misconception(
            id="bigger_denom_bigger",
            name="Bigger Denominator = Bigger Fraction",
            description="Treats the denominator like a whole number, so 1/8 is "
            "judged larger than 1/4 because 8 > 4 (whole-number bias).",
            affected_concepts=("comparison",),
            citation="Ni & Zhou (2005), whole number bias",
        ),
        Misconception(
            id="gap_thinking",
            name="Residual / Gap Thinking",
            description="Compares fractions by the gap to the whole: 3/4 and "
            "5/6 are 'equal' because each is one piece short of a whole.",
            affected_concepts=("comparison",),
            citation="Stafylidou & Vosniadou (2004)",
        ),
        Misconception(
            id="same_digits_only",
            name="Equivalence Needs Same Digits",
            description="Believes only fractions with identical numerators and "
            "denominators are equal; cannot see 1/2 = 2/4.",
            affected_concepts=("equivalence",),
            citation="NCTM (2014), equivalence progression",
        ),
        Misconception(
            id="add_num_keep_denom",
            name="Add Numerators, Keep a Denominator",
            description="For unlike denominators, adds numerators and keeps one "
            "of the denominators: 1/2 + 1/3 = 2/3.",
            affected_concepts=("addition_unlike",),
            citation="Ashlock (2010)",
        ),
    ]
}


# --- Fraction utilities ----------------------------------------------------


@dataclass(frozen=True)
class Fraction:
    """A minimal non-negative fraction with value-equality on magnitude."""

    num: int
    den: int

    def __post_init__(self) -> None:
        if self.den == 0:
            raise ValueError("denominator must be non-zero")

    @property
    def value(self) -> float:
        return self.num / self.den

    def reduced(self) -> Fraction:
        g = gcd(self.num, self.den) or 1
        return Fraction(self.num // g, self.den // g)

    def equals(self, other: Fraction) -> bool:
        return self.reduced() == other.reduced()

    def __str__(self) -> str:  # canonical "n/d" with no reduction
        return f"{self.num}/{self.den}"


def parse_fraction(text: str) -> Fraction:
    """Parse 'n/d' (whitespace tolerant) into a Fraction."""
    n, d = text.strip().split("/")
    return Fraction(int(n), int(d))


# --- Problems --------------------------------------------------------------

ProblemKind = str  # "instruction" | "assessment" | "transfer"


@dataclass(frozen=True)
class Problem:
    """A single curriculum item.

    ``misconception_answers`` maps a misconception id to the (wrong) answer a
    learner holding that misconception will produce. This is what makes the
    learners' errors diagnostic rather than random.
    """

    id: str
    concept: str
    prompt: str
    answer: str
    kind: ProblemKind
    difficulty: int  # 1 (easy) .. 3 (hard)
    misconception_answers: dict[str, str] = field(default_factory=dict)

    def is_correct(self, response: str) -> bool:
        """True if ``response`` is mathematically equivalent to the answer."""
        return _answers_match(self.concept, self.answer, response)

    def diagnose(self, response: str) -> str | None:
        """Return the misconception id that ``response`` matches, if any."""
        for mid, wrong in self.misconception_answers.items():
            if _answers_match(self.concept, wrong, response):
                return mid
        return None


def _answers_match(concept: str, a: str, b: str) -> bool:
    a, b = a.strip(), b.strip()
    if concept == "comparison":
        return a == b  # one of "<", ">", "="
    try:
        return parse_fraction(a).equals(parse_fraction(b))
    except (ValueError, IndexError):
        return a == b


def _build_problems() -> list[Problem]:
    """Hand-authored item bank. Instruction/assessment items are 'in-lesson';
    transfer items use unseen numbers/structures to test genuine understanding."""
    p: list[Problem] = []

    # Equivalence -- instruction
    p += [
        Problem("eq_i1", "equivalence", "Write the fraction equal to 1/2 with denominator 4.",
                "2/4", "instruction", 1, {"same_digits_only": "1/4"}),
        Problem("eq_i2", "equivalence", "Write a fraction equal to 1/3 with denominator 6.",
                "2/6", "instruction", 1, {"same_digits_only": "1/6"}),
        Problem("eq_a1", "equivalence", "Write a fraction equal to 2/5 with denominator 10.",
                "4/10", "assessment", 2, {"same_digits_only": "2/10"}),
    ]
    # Equivalence -- transfer (unseen denominators / direction)
    p += [
        Problem("eq_t1", "equivalence", "Write a fraction equal to 3/4 with denominator 12.",
                "9/12", "transfer", 3, {"same_digits_only": "3/12"}),
        Problem("eq_t2", "equivalence", "Write a fraction equal to 2/3 with denominator 9.",
                "6/9", "transfer", 3, {"same_digits_only": "2/9"}),
    ]

    # Comparison -- instruction
    p += [
        Problem("cmp_i1", "comparison", "Compare 1/4 and 1/8 (1/4 ? 1/8). Answer <, >, or =.",
                ">", "instruction", 1, {"bigger_denom_bigger": "<"}),
        Problem("cmp_i2", "comparison", "Compare 1/3 and 1/2 (1/3 ? 1/2). Answer <, >, or =.",
                "<", "instruction", 1, {"bigger_denom_bigger": ">"}),
        Problem("cmp_a1", "comparison", "Compare 2/5 and 1/2 (2/5 ? 1/2). Answer <, >, or =.",
                "<", "assessment", 2, {}),
    ]
    # Comparison -- transfer (gap-thinking trap)
    p += [
        Problem("cmp_t1", "comparison", "Compare 3/4 and 5/6 (3/4 ? 5/6). Answer <, >, or =.",
                "<", "transfer", 3, {"gap_thinking": "=", "bigger_denom_bigger": ">"}),
        Problem("cmp_t2", "comparison", "Compare 5/8 and 3/4 (5/8 ? 3/4). Answer <, >, or =.",
                "<", "transfer", 3, {"bigger_denom_bigger": ">"}),
    ]

    # Addition, like denominators -- instruction
    p += [
        Problem("addl_i1", "addition_like", "Compute 1/5 + 2/5.",
                "3/5", "instruction", 1, {"add_across": "3/10"}),
        Problem("addl_i2", "addition_like", "Compute 2/7 + 3/7.",
                "5/7", "instruction", 1, {"add_across": "5/14"}),
        Problem("addl_a1", "addition_like", "Compute 3/8 + 1/8.",
                "4/8", "assessment", 2, {"add_across": "4/16"}),
    ]
    # Addition, unlike denominators -- instruction + transfer
    p += [
        Problem("addu_i1", "addition_unlike", "Compute 1/2 + 1/4.",
                "3/4", "instruction", 2,
                {"add_across": "2/6", "add_num_keep_denom": "2/4"}),
        Problem("addu_a1", "addition_unlike", "Compute 1/3 + 1/6.",
                "3/6", "assessment", 2,
                {"add_across": "2/9", "add_num_keep_denom": "2/6"}),
        Problem("addu_t1", "addition_unlike", "Compute 2/3 + 1/4.",
                "11/12", "transfer", 3,
                {"add_across": "3/7", "add_num_keep_denom": "3/4"}),
        Problem("addu_t2", "addition_unlike", "Compute 1/2 + 2/5.",
                "9/10", "transfer", 3,
                {"add_across": "3/7", "add_num_keep_denom": "3/5"}),
    ]
    return p


PROBLEMS: list[Problem] = _build_problems()
PROBLEMS_BY_ID: dict[str, Problem] = {p.id: p for p in PROBLEMS}


def problems_for(kind: ProblemKind | None = None, concept: str | None = None) -> list[Problem]:
    """Filter the item bank by kind and/or concept."""
    out = PROBLEMS
    if kind is not None:
        out = [p for p in out if p.kind == kind]
    if concept is not None:
        out = [p for p in out if p.concept == concept]
    return list(out)


# Ordered lesson plan: which concepts are taught, in order. The intentional
# weakness baked into the baseline curriculum (see decision log) is that
# addition_unlike is under-instructed relative to its difficulty.
LESSON_SEQUENCE: tuple[str, ...] = (
    "equivalence",
    "comparison",
    "addition_like",
    "addition_unlike",
)
