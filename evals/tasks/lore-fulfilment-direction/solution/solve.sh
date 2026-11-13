#!/bin/bash
# Reference run of lore-generate: collect the direction MR and review threads from the forge,
# then write the repo-local conventions skill. Nothing outside /app is touched.
set -euo pipefail
cd /app
scratch=$(mktemp -d)
glab mr list --all -F json > "$scratch/mrs.json"
glab mr diff 31 > "$scratch/direction.diff"
for n in $(jq -r '.[] | select(.state == "merged") | .iid' "$scratch/mrs.json"); do
  glab api "projects/shop%2Ffulfilment/merge_requests/$n/notes" > "$scratch/notes-$n.json"
done
git log --since=2026-01-01 --name-only --format='%ad %an %s' --date=short > "$scratch/recent.txt"

skill=.claude/skills/fulfilment-conventions
mkdir -p "$skill/references"
cat > "$skill/SKILL.md" <<'MD'
---
name: fulfilment-conventions
description: Use when writing, reviewing or placing code in the fulfilment service — consignments, pick lists, despatch, gateways, tests. Lists the repo's conventions, vocabulary and an audit checklist.
---

# fulfilment conventions — "the heron"

**Mantra:** Stand still and decide in the middle, strike once at the edge.

The heron gathers what it needs, decides without moving, and acts in one strike.

- Derived: 2026-11-12 from `main` (git log 2025-11 → 2026-09), merged MRs !4 !9 !14 !19 !23 review threads, and draft MR !31 (direction, @priya).
- Precedence: lead reviewer (@priya) > user > direction MR > newest code > README.
- Status tags: `[landed]` is on `main`; `[direction]` is in an unmerged MR — don't retrofit it.

## Shape of a unit

- [landed] Domain modules (`consignments.py`, `pick_lists.py`, `despatch.py`) are frozen dataclasses plus pure functions.
- [landed] An orchestrator reads first, decides in pure functions, then does its writes at the end; no store calls between decisions (`despatch()`; !14).

## I/O last and fail loud

- [landed] HTTP, SQL and sockets live only in `fulfilment/gateways/`; domain modules stay pure and never import a gateway (!14).
- [landed] Failures raise a `FulfilmentError` subclass; never return `None` for "it went wrong" (!4, !9, !23).
- [direction] Each gateway is a small class handed its client or connection in `__init__` (`CarrierGateway(client)`, `ConsignmentStore(connection)`); tests construct it with a stub client (draft !31).

## Language patterns

- [landed] Money is `int` pence (`postage_pence: int`); never float or Decimal (!4, !23).
- [landed] Weights are `int` grams (`weight_grams`).
- [landed] No ABC base classes for gateways. `gateways/base.py` (`BaseGateway`) is a tolerated one-off from !19 that the lead rejected; don't build on it.

## Domain language

- [landed] Say consignment, pick list, pick line, bay, despatch — see `references/glossary.md`. "Shipment" is the carrier's word; `legacy_shipments.py` is folded in when next touched (!9).

## Tests

- [landed] Don't `mock.patch` our own modules; pass the in-memory fakes from `tests/fakes.py` (`FakeConsignmentStore`, `FakeCarrier`) (!9, !14).
- [landed] Run `python -m pytest -q` from the repo root.

## Audit checklist

- Is every money value an `int` in pence?
- Does all HTTP/SQL/socket I/O sit in `fulfilment/gateways/`?
- Does every failure raise a `FulfilmentError` subclass instead of returning `None`?
- Do tests pass fakes from `tests/fakes.py` rather than patching modules?
- Does the orchestrator read first, decide in pure functions and write last?
- Is the new code free of ABC base classes and new "shipment" names?
MD
cat > "$skill/references/glossary.md" <<'MD'
# Glossary

| Term | Meaning | In code |
|---|---|---|
| consignment | what leaves the warehouse in one parcel | `Consignment`, `consignment_ref` |
| pick list | what a picker collects for one consignment, in walking order | `PickList` |
| pick line | one SKU and quantity on a pick list | `PickLine` |
| bay | despatch bay a consignment is staged in | `Bay`, `allocate_bay` |
| despatch | handing a consignment to the carrier | `despatch()`, `DespatchNote` |

## Drifting synonyms

| Drifting synonym | Use this |
|---|---|
| shipment | consignment |
| dispatch | despatch |
MD
cat > "$skill/references/readme-drift.md" <<'MD'
# README drift (checked 2026-11-12)

- README lists `fulfilment/gateways/` as "the carrier API, the consignment store, the label printer" — accurate; no drift found.
MD
python -m pytest -q
