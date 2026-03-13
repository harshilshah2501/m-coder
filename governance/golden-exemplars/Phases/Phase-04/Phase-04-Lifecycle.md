# Phase-04 (MIX) — Lifecycle of an Exemplar

This note defines the **authoring and governance lifecycle** of a Phase-04 (MIX) exemplar. It is normative and applies to all MIX-xx artifacts.

---

## 1. Interactive Draft State

**Labeling:**

* Document title may include *“Interactive Draft”*
* Sections may include guidance markers such as *(DRAFT)* or *(Skeleton Only)*

**Allowed actions:**

* Sections may be authored, revised, or unlocked deliberately
* Control-plane sections (A–C) may be unlocked only with explicit intent

**Disallowed actions:**

* No claims of canonical or reference status
* No downstream reuse as precedent

---

## 2. Control-Plane Lock

**Trigger:**

* Sections A (Five-Layer Declaration), B (Collision Surface), and C (Irreversible Boundary) are agreed and locked

**Effect:**

* Situation framing, collision definition, and stopping boundary become immutable
* All subsequent reasoning and output must conform strictly

---

## 3. Full Exemplar Lock

**Trigger:**

* Sections D–H are completed
* D.N.A Validation passes

**Required hygiene changes:**

* Remove *“Interactive Draft”* from the title
* Remove instructional markers such as *(Skeleton Only)*
* Mark all sections as *(LOCKED)*

**Resulting status:**

* The exemplar becomes a **Canonical Phase-04 Exemplar**
* No edits permitted without a Phase-04 schema version bump

---

## 4. Canonical Usage

A locked Phase-04 exemplar:

* Serves as a reference for future MIX-xx authoring
* May be used for reviewer calibration and training
* Must not be semantically modified retroactively

---

## 5. Versioning Rule

Any change to a locked exemplar requires:

* A Phase-04 schema version increment, or
* Explicit deprecation of the exemplar

Silent or partial edits are invalid.

---

**End of Phase-04 Lifecycle**
