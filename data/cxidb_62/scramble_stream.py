#!/usr/bin/env python
"""
Scramble the indexing setting of a CrystFEL stream, for testing indexing-ambiguity resolution.

cxidb_62 (P 6_5) has a merohedral indexing ambiguity, but the deposited all-amb.stream has nearly every crystal in
one setting already, so it does not test whether a program can resolve the ambiguity. This writes a copy in which
each crystal is independently reindexed by the twin operator (h, k, l) -> (k, h, -l) with probability 1/2, from a
fixed seed, and a sidecar CSV with which crystals were flipped (the ground truth, up to the global choice of
setting).

A flipped crystal stays internally consistent: its reflections' Miller indices are reindexed; its reciprocal
basis follows (a*' = b*, b*' = a*, c*' = -c*, so every reflection keeps its scattering vector); and its cell
parameters swap a with b and alpha with beta. Everything else in the stream is copied byte for byte.

usage: scramble_stream.py in.stream out.stream [--seed 2026] [--labels out.labels.csv]
Standard library only.
"""
import argparse
import csv
import random
import sys


def _vec(line):
    """The three numbers of an 'astar = x y z nm^-1' line."""
    return [float(v) for v in line.split("=", 1)[1].split()[:3]]


def _fmt(name, v):
    return f"{name} = {v[0]:+.7f} {v[1]:+.7f} {v[2]:+.7f} nm^-1\n"


def scramble(src, dst, labels, seed):
    rng = random.Random(seed)
    image = event = ""
    crystal = 0
    flip = in_refl = False
    astar = None
    nflip = 0
    with open(src) as fin, open(dst, "w") as fout, open(labels, "w", newline="") as flab:
        out = csv.writer(flab)
        out.writerow(["crystal", "image", "event", "flipped"])
        for line in fin:
            if line.startswith("Image filename:"):
                image = line.split(":", 1)[1].strip()
            elif line.startswith("Event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("--- Begin crystal"):
                flip = rng.random() < 0.5
                out.writerow([crystal, image, event, int(flip)])
                crystal += 1
                nflip += flip
            elif line.startswith("--- End crystal"):
                flip = in_refl = False
            elif flip:
                if line.startswith("Cell parameters"):
                    # Cell parameters a b c nm, al be ga deg
                    w = line.split()
                    a, b, c = w[2], w[3], w[4]
                    al, be, ga = w[6], w[7], w[8]
                    line = f"Cell parameters {b} {a} {c} nm, {be} {al} {ga} deg\n"
                elif line.startswith("astar ="):
                    astar = _vec(line)
                    continue  # written after bstar, swapped
                elif line.startswith("bstar ="):
                    fout.write(_fmt("astar", _vec(line)))
                    line = _fmt("bstar", astar)
                elif line.startswith("cstar ="):
                    line = _fmt("cstar", [-x for x in _vec(line)])
                elif line.startswith("Reflections measured after indexing"):
                    in_refl = True
                elif line.startswith("End of reflections"):
                    in_refl = False
                elif in_refl and not line.lstrip().startswith("h"):
                    # "%4i %4i %4i ..." : the indices are the first 14 characters.
                    h, k, l = int(line[0:4]), int(line[5:9]), int(line[10:14])
                    line = f"{k:4d} {h:4d} {-l:4d}" + line[14:]
            fout.write(line)
    return crystal, nflip


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--labels", default=None, help="sidecar CSV (default: dst with .labels.csv)")
    a = p.parse_args(argv)
    labels = a.labels or (a.dst[:-7] if a.dst.endswith(".stream") else a.dst) + ".labels.csv"
    n, f = scramble(a.src, a.dst, labels, a.seed)
    print(f"{a.dst}: {f} of {n} crystals reindexed by (k, h, -l); labels in {labels}", file=sys.stderr)


if __name__ == "__main__":
    main()
