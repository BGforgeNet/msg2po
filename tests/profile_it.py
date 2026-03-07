# Profile msg2po import breakdown.
# Usage: python tests/profile_it.py

import cProfile
import pstats

PROFILE_LINES = 25


def main():
    print("=" * 60)
    print("IMPORT TIME BREAKDOWN")
    print("=" * 60)

    prof = cProfile.Profile()
    prof.enable()
    import msg2po.core  # noqa: F401

    prof.disable()

    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(PROFILE_LINES)


if __name__ == "__main__":
    main()
