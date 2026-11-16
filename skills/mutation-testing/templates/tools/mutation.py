# Template from the mutation-testing skill (project-standard). Copy to backend/tools/mutation.py;
# config in [tool.mutmut] and [tool.mutation] of pyproject.toml (references/setup.md). Pin mutmut:
# this file calls its internals (_run, config(), SourceFileMutationData, get_diff_for_mutant).
"""Mutation testing on what a change touched: only the functions whose lines the diff changed.

Mutation testing breaks the code on purpose, one small edit at a time (`>` into `>=`, `True` into
`False`, a call into `None`), and runs the tests that cover that function. A mutant the tests do
not notice ("survived") is behaviour no test pins down. Mutating a whole backend is tens of
thousands of mutants (about an hour), so this tool mutates only the functions a diff touched — a few dozen
to a few hundred mutants — and runs them on every core.

Every mutant pays for the tests it runs, so those tests have a budget: the selection in
`[tool.mutation]` (the unit tests: a folder, or every test minus some markers) must finish in
`max-test-seconds` (5) in one process. The tool checks it before mutating and fails past it.

Usage:

    uv run python -m tools.mutation                  # functions changed since origin/main
    uv run python -m tools.mutation --base HEAD~3    # ... since another ref
    uv run python -m tools.mutation app/x/y.py         # every function of these files
    uv run python -m tools.mutation --survivors s.md app/x/*.py  # + every survivor's diff
    uv run python -m tools.mutation --check-speed     # only the 5 s budget of the tests

Only files matching `[tool.mutation].paths` (the pure code) are mutated. Each belongs to a
tier (domain rules 80%, heuristics 65%); the tool exits with 1 when the mutants of the changed functions
of some tier score below that tier's minimum, or when the tests pass their budget. The report
goes to stdout and, in GitHub Actions, to the job summary. mutmut's own config is
`[tool.mutmut]`; this tool narrows `only_mutate` to the files in play.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)
MAX_SHOWN = 40
PYTEST_TIME = re.compile(r" in ([\d.]+)s")


def changed_lines(base: str) -> dict[Path, set[int]]:
    """Lines added or changed under `app/` since the merge base with `base` (working tree included)."""
    merge_base = _git("merge-base", base, "HEAD").strip()
    out: dict[Path, set[int]] = {}
    for chunk in _git("diff", "-U0", "--relative", merge_base, "--", "app").split("\ndiff --git ")[1:]:
        name = re.search(r"^\+\+\+ b/(\S+)$", chunk, re.MULTILINE)
        if not name or not name.group(1).endswith(".py"):
            continue
        lines = out.setdefault(Path(name.group(1)), set())
        for start, count in HUNK.findall(chunk):
            lines.update(range(int(start), int(start) + int(count or 1)))
    return out


def _git(*args: str) -> str:
    cmd = ["git", *args]  # fixed executable, arguments built here
    return subprocess.run(cmd, cwd=BACKEND, check=True, capture_output=True, text=True).stdout  # noqa: S603


def mutant_globs(path: Path, lines: set[int] | None) -> list[str]:
    """mutmut name patterns of the functions in `path` that overlap `lines` (all when None).

    mutmut mutates module-level functions (`x_name`) and methods (`xǁClassǁname`).
    """
    module = ".".join(path.with_suffix("").parts)
    tree = ast.parse((BACKEND / path).read_text(encoding="utf-8"))
    globs = []
    for prefix, fn in _functions(tree):
        if lines is None or lines & set(range(fn.lineno, (fn.end_lineno or fn.lineno) + 1)):
            globs.append(f"{module}.{prefix}{fn.name}__mutmut_*")
    return globs


def _functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append(("x_", node))
        elif isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
            found += [(f"xǁ{node.name}ǁ", m) for m in methods]
    return found


def run_mutmut(files: list[Path], globs: list[str], marker_args: list[str]) -> None:
    """Run mutmut in this process with `only_mutate` narrowed to `files` (not settable from the CLI).

    `mutants/` starts empty: mutmut treats a file it copied unmutated on an earlier run as
    "unmodified" and would skip it now that it is in `only_mutate`.
    """
    from mutmut import configuration  # mutmut is imported only when there is work to do
    from mutmut.__main__ import _run

    os.chdir(BACKEND)
    shutil.rmtree(BACKEND / "mutants", ignore_errors=True)
    configuration.config().only_mutate = [str(f) for f in files]
    configuration.config().pytest_add_cli_args_test_selection += marker_args
    _run(globs, max_children=os.cpu_count())


@dataclass(frozen=True)
class Tier:
    """A group of files held to one minimum score (`[tool.mutation].tiers`)."""

    name: str
    min_score: int
    paths: tuple[str, ...]


@dataclass(frozen=True)
class Mutant:
    name: str
    path: Path
    survived: bool


@dataclass(frozen=True)
class Settings:
    """`[tool.mutation]` in `pyproject.toml`."""

    paths: tuple[str, ...]
    test_paths: list[str]  # [tool.mutmut].pytest_add_cli_args_test_selection
    test_selection: str  # a pytest -m expression; empty selects every test under test_paths
    max_test_seconds: float
    tiers: list[Tier]

    def marker_args(self) -> list[str]:
        return ["-m", self.test_selection] if self.test_selection else []


def load_settings() -> Settings:
    with open(BACKEND / "pyproject.toml", "rb") as fh:
        tool = tomllib.load(fh)["tool"]
    raw = tool["mutation"]
    tests = list(tool["mutmut"].get("pytest_add_cli_args_test_selection", ["tests/"]))
    tiers = [Tier(t["name"], int(t["min-score"]), tuple(t["paths"])) for t in raw["tiers"]]
    selection = raw.get("test-selection", "")
    return Settings(tuple(raw["paths"]), tests, selection, float(raw["max-test-seconds"]), tiers)


def test_seconds(settings: Settings) -> float:
    """How long the tests mutmut runs take in one process, by pytest's own clock."""
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:xdist", "-p", "no:cacheprovider"]
    cmd += ["-o", "addopts=", *settings.marker_args(), *settings.test_paths]
    done = subprocess.run(cmd, cwd=BACKEND, capture_output=True, text=True, timeout=300, check=False)  # noqa: S603
    last = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else ""
    found = PYTEST_TIME.search(last)
    if done.returncode != 0 or not found:
        raise SystemExit(f"The tests mutmut runs failed:\n{done.stdout[-3000:]}{done.stderr[-2000:]}")
    return float(found.group(1))


def check_speed(settings: Settings) -> bool:
    """True when the selected tests fit their budget; prints the measure either way."""
    took = test_seconds(settings)
    ok = took <= settings.max_test_seconds
    verdict = "ok" if ok else "OVER: make them faster or move the slow ones out of the selection"
    budget = f"{took:.2f} s of {settings.max_test_seconds:g} s"
    which = " ".join([*settings.marker_args(), *settings.test_paths])
    print(f"Tests for mutation ({which}): {budget}, {verdict}")
    return ok


def tier_of(path: Path, tiers: list[Tier]) -> Tier | None:
    """The first tier whose paths match `path` (fnmatch: `*` also crosses `/`)."""
    return next((t for t in tiers if any(fnmatch.fnmatch(str(path), p) for p in t.paths)), None)


def collect(globs: list[str]) -> list[Mutant]:
    """Every tested mutant of the functions in `globs`, read from `mutants/`."""
    from mutmut.mutation.data import SourceFileMutationData
    from mutmut.stats import status_by_exit_code
    from mutmut.utils.file_utils import walk_mutatable_files

    found = []
    for path in walk_mutatable_files():
        data = SourceFileMutationData(path=path)
        data.load()
        for name, code in data.exit_code_by_key.items():
            if code is not None and _matches(name, globs):
                found.append(Mutant(name, Path(path), status_by_exit_code[code] == "survived"))
    return found


def score(mutants: list[Mutant]) -> int:
    """Share of mutants killed, in whole percent (100 when there is nothing to kill)."""
    killed = sum(1 for m in mutants if not m.survived)
    return 100 * killed // len(mutants) if mutants else 100


def verdicts(mutants: list[Mutant], tiers: list[Tier]) -> list[tuple[Tier, int, int]]:
    """(tier, score, mutant count) of every tier that has mutants in this run."""
    out = []
    for tier in tiers:
        own = [m for m in mutants if tier_of(m.path, tiers) == tier]
        if own:
            out.append((tier, score(own), len(own)))
    return out


def report(mutants: list[Mutant], tiers: list[Tier]) -> str:
    """Markdown: score per tier against its minimum, survivors per function, the first diffs."""
    from mutmut.mutation.diff_apply import get_diff_for_mutant

    lost = [m for m in mutants if m.survived]
    out = [f"## Mutation testing: {score(mutants)}% killed ({len(mutants) - len(lost)}/{len(mutants)})", ""]
    for tier, got, count in verdicts(mutants, tiers):
        mark = "ok" if got >= tier.min_score else "BELOW"
        out.append(f"- **{tier.name}**: {got}% of {count} (minimum {tier.min_score}%) {mark}")
    per_fn = Counter(m.name.split("__mutmut_")[0] for m in lost)
    out += ["", "### Survivors per function", ""]
    out += [f"- `{fn}`: {n}" for fn, n in per_fn.most_common()]
    out += ["", f"### First {min(MAX_SHOWN, len(lost))} survivors", ""]
    for m in lost[:MAX_SHOWN]:
        out += [f"`{m.name}`", "```diff", get_diff_for_mutant(m.name, path=m.path).strip(), "```"]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path, help="mutate every function of these files")
    parser.add_argument("--base", default="origin/main", help="diff against the merge base with REF")
    parser.add_argument("--survivors", type=Path, help="also write every survivor's diff to this file")
    parser.add_argument("--check-speed", action="store_true", help="only check the tests' time budget")
    args = parser.parse_args(argv)
    settings = load_settings()
    if not check_speed(settings):
        return 1
    if args.check_speed:
        return 0
    targets = _targets(args.files, args.base, settings.paths)
    globs = [g for path, lines in targets.items() for g in mutant_globs(path, lines)]
    if not globs:
        print("No function in [tool.mutation].paths changed: nothing to mutate.")
        return 0
    print(f"Mutating {len(globs)} function(s) in {len(targets)} file(s).", flush=True)
    run_mutmut(list(targets), globs, settings.marker_args())
    mutants = collect(globs)
    if args.survivors:
        write_survivors(mutants, args.survivors)
    return _publish(mutants, settings.tiers)


def _targets(files: list[Path], base: str, paths: tuple[str, ...]) -> dict[Path, set[int] | None]:
    """Whole files given on the command line, or the changed lines of the files under `paths`."""
    if files:
        return dict.fromkeys(files)
    changed = changed_lines(base)
    return {f: lines for f, lines in changed.items() if any(fnmatch.fnmatch(str(f), p) for p in paths)}


def write_survivors(mutants: list[Mutant], target: Path) -> None:
    """Every survivor's diff, grouped by file: the to-do list for whoever writes the missing tests."""
    from mutmut.mutation.diff_apply import get_diff_for_mutant

    out = [f"# {sum(m.survived for m in mutants)} surviving mutants of {len(mutants)}", ""]
    for m in sorted((m for m in mutants if m.survived), key=lambda m: (str(m.path), m.name)):
        out += [f"## `{m.name}`", "```diff", get_diff_for_mutant(m.name, path=m.path).strip(), "```", ""]
    target.write_text("\n".join(out), encoding="utf-8")


def _publish(mutants: list[Mutant], tiers: list[Tier]) -> int:
    """Print the report (and append it to the GitHub job summary); 1 when a tier is below its minimum."""
    text = report(mutants, tiers)
    print(text)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 1 if any(got < tier.min_score for tier, got, _ in verdicts(mutants, tiers)) else 0


def _matches(name: str, globs: list[str]) -> bool:
    return any(name.startswith(g.removesuffix("*")) for g in globs)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
