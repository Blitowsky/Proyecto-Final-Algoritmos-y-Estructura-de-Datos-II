import argparse

from experiments import heatmap
from experiments import search_bench
from experiments import search_report
from experiments import strategies_bench
from experiments import strategies_report

SEARCH = {"t3", "c1", "c2"}
SIM = {"t1", "c12"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", default=["all"])
    ap.add_argument("--reuse", action="store_true", help="reuse saved raw results")
    a = ap.parse_args()
    want = SEARCH | SIM if "all" in a.targets else {t.lower() for t in a.targets}

    if want & SEARCH:
        rows = search_bench.load() if a.reuse else search_bench.run()
        if "t3" in want: search_report.t3(rows)
        if "c1" in want: search_report.c1(rows)
        if "c2" in want: search_report.c2(rows)
    if want & SIM:
        res = strategies_bench.load() if a.reuse else strategies_bench.run()
        if "t1" in want: strategies_report.t1(res)
        if "c12" in want: heatmap.c12()


if __name__ == "__main__":
    main()
