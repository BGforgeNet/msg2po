# Profile msg2po workflows on real repos.
# Usage: uv run python tests/profile_workflow.py <workflow> [repo]
#
# Workflows: poify, unpoify, dir2msgstr, import
# Repos: fo2 (default), ascension
#
# Examples:
#   uv run python tests/profile_workflow.py poify
#   uv run python tests/profile_workflow.py unpoify ascension
#   uv run python tests/profile_workflow.py import

import cProfile
import os
import pstats
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
REPOS_DIR = os.path.join(SCRIPT_DIR, "repos")

PROFILE_LINES = 40

REPOS = {
    "fo2": {
        "dir": os.path.join(REPOS_DIR, "fo2_up"),
        "src": "data/text/english",
        "po_dir": "data/text/po",
    },
    "ascension": {
        "dir": os.path.join(REPOS_DIR, "ascension"),
        "src": "ascension/lang/english",
        "po_dir": "ascension/lang/po",
    },
}


def reset_repo(repo_dir):
    subprocess.run(["git", "checkout", "-q", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "clean", "-fd", "-q"], cwd=repo_dir, check=True)


def profile_import():
    print("=" * 60)
    print("IMPORT TIME BREAKDOWN")
    print("=" * 60)
    prof = cProfile.Profile()
    prof.enable()
    import msg2po.conversion  # noqa: F401

    prof.disable()
    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(PROFILE_LINES)


def profile_poify(repo):
    cfg = REPOS[repo]
    reset_repo(cfg["dir"])
    os.chdir(cfg["dir"])
    sys.argv = ["poify", cfg["src"]]

    import msg2po.poify

    prof = cProfile.Profile()
    prof.enable()
    msg2po.poify.main()
    prof.disable()

    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(PROFILE_LINES)


def profile_unpoify(repo):
    cfg = REPOS[repo]
    reset_repo(cfg["dir"])
    os.chdir(cfg["dir"])
    sys.argv = ["unpoify", cfg["po_dir"]]

    import msg2po.unpoify

    prof = cProfile.Profile()
    prof.enable()
    msg2po.unpoify.main()
    prof.disable()

    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(PROFILE_LINES)


def profile_dir2msgstr(repo):
    cfg = REPOS[repo]
    reset_repo(cfg["dir"])
    os.chdir(cfg["dir"])
    sys.argv = ["dir2msgstr", "--auto", "--overwrite"]

    import msg2po.dir2msgstr

    prof = cProfile.Profile()
    prof.enable()
    msg2po.dir2msgstr.main()
    prof.disable()

    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(PROFILE_LINES)


WORKFLOWS = {
    "poify": profile_poify,
    "unpoify": profile_unpoify,
    "dir2msgstr": profile_dir2msgstr,
    "import": lambda _: profile_import(),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in WORKFLOWS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(WORKFLOWS)}> [fo2|ascension]")
        sys.exit(1)

    workflow = sys.argv[1]
    repo = sys.argv[2] if len(sys.argv) > 2 else "fo2"

    if workflow != "import" and repo not in REPOS:
        print(f"Unknown repo: {repo}. Choose from: {', '.join(REPOS)}")
        sys.exit(1)

    if workflow != "import":
        cfg = REPOS[repo]
        if not os.path.isdir(cfg["dir"]):
            print(f"Repo not found at {cfg['dir']}. Run tests/e2e.sh first to clone.")
            sys.exit(1)

    WORKFLOWS[workflow](repo)


if __name__ == "__main__":
    main()
