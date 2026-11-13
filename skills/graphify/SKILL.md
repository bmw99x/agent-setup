---
name: graphify
description: Use when exploring, mapping, or understanding unfamiliar code — onboarding to a new module/bounded context, tracing data flow across layers, reviewing a multi-file MR, or answering "how does X work" — to produce a Mermaid diagram plus narrative of nodes, edges, and layer boundaries before making edits.
---

# graphify.md

> Skill: build mental graph of unfamiliar code before edit. Trigger: "explore", "understand", "map", "where does X flow", new bounded context, onboarding to module.

## Goal

Produce structured map: nodes (modules / classes / functions / tables), edges (calls / imports / data flow), boundaries (layers / contexts). Output = Mermaid diagram + short narrative. No edits.

## When use

- New repo, new module, or unfamiliar bounded context
- Before refactor touching >3 files
- Tracing bug across layers
- Reviewing MR that spans many files
- Answering "how does X work" with high confidence

Skip for: single-file fixes, trivial edits, areas already mapped in `docs/`.

## Steps

1. **Anchor.** Pick entry point: route, CLI cmd, job, public function. Note file:line from the file you just read, never from memory.
1. **Outward sweep.** Follow imports + calls outward 1-2 hops. Track each hop: caller → callee + reason.
1. **Inward sweep.** `grep` for references to anchor. Who invokes it. Why.
1. **Data flow.** Identify DTOs / models / DB tables touched. Note schema crossings (DTO ↔ domain ↔ ORM).
1. **Side effects.** External calls, DB writes, queue publishes, log emits.
1. **Boundaries.** Tag every node by layer (route / service / repo / adapter / domain) in the diagram itself: `subgraph`, `box`, or label suffix like `OrderRepository (repo)`. Layer named only in prose doesn't count. Draw + flag every edge that skips a layer (e.g. route → repo).
1. **Render.** Mermaid `flowchart` or `sequenceDiagram`. Save under `docs/diagrams/explore/<topic>.md` or paste inline.
1. **Narrative.** 5-10 bullets: entry, key collaborators, data shape transitions, surprises, open questions.

## Tools to use

- `Explore` subagent for broad search (multi-file, naming-convention spread)
- `grep` / `rg` for targeted symbol lookup
- Claude LSP for "find references" / "go to definition" when index warm
- `git log -p -- <file>` for intent behind non-obvious code
- `git blame` to find author for follow-up question

## Output templates

### Flowchart

```mermaid
flowchart LR
  subgraph route
    Route[POST /things]
  end
  subgraph service
    Svc[ThingService.create]
  end
  subgraph repo
    Repo[ThingRepository.add]
  end
  subgraph adapter
    Pub[EventBus.publish ThingCreated]
  end
  Route --> Svc
  Svc --> Repo
  Svc --> Pub
  Repo --> DB[(things table)]
  Pub --> Worker[NotifyWorker]
```

### Sequence

```mermaid
sequenceDiagram
  participant Client
  box route
    participant Route
  end
  box service
    participant Svc
  end
  box repo
    participant Repo
  end
  box adapter
    participant Bus
  end
  participant DB
  Client->>Route: POST /things {dto}
  Route->>Svc: create(cmd)
  Svc->>Repo: add(entity)
  Repo->>DB: INSERT
  Svc->>Bus: publish(ThingCreated)
  Svc-->>Route: ThingResponse
  Route-->>Client: 201
```

### Narrative skeleton

```
Entry: <file:line>
Layer path: route → service → repo
Touched tables: <list>
Touched DTOs: <list>
External calls: <list>
Side effects: <list>
Open questions: <list>
Suspect smells: <list>
```

## Anti-patterns

- Mapping whole repo. Stay scoped to topic.
- Diagram for trivial 2-file path. Narrative suffice.
- Stop at imports - miss runtime dispatch (registries, plugin loaders, DI containers).
- Ignore tests - tests reveal intended contract fastest.
- Lie about uncertainty. Mark unknown edges with `?`.

## Checklist before edit

- [ ] Entry point identified
- [ ] Callers + callees mapped 1-2 hops
- [ ] Data shape transitions noted
- [ ] Side effects listed
- [ ] Layer violations flagged
- [ ] Open questions logged
- [ ] Diagram saved or pasted
