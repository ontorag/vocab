# OntoRAG Vocabulary (`orag:`)

**Namespace:**  
`https://www.ontorag.org/vocab#`

OntoRAG (`orag:`) is a lightweight metadata vocabulary designed to describe:

- Source artifacts (PDF, HTML, Markdown, repositories, etc.)
- Derived RDF knowledge graphs
- Index artifacts (LlamaIndex, PageIndex, embedding stores, etc.)
- Build and ingestion runs
- Content-type-agnostic citation spans for RAG explainability

The goal is to provide a structured, interoperable layer for managing ingestion, graph construction, indexing, licensing, and provenance in Retrieval-Augmented Generation (RAG) systems.

---

## Design Goals

OntoRAG is built around a few core principles:

- **Artifact-centric modeling** — Everything is an `orag:Artifact` (source, graph, index, report).
- **Pipeline traceability** — All transformations are modeled with `orag:BuildRun` (based on PROV-O).
- **Named-graph awareness** — `orag:GraphArtifact` explicitly references its `contentGraph` and `manifestGraph`.
- **Index abstraction** — Different indexing strategies are described uniformly as `orag:IndexArtifact`.
- **RAG explainability** — `orag:SourceSpan` enables content-type-agnostic citation and anchoring.
- **Licensing support** — Artifacts can declare required products and access policies.
- **Content neutrality** — The model does not assume PDFs, text, HTML, audio, etc. Everything is abstracted.

The ontology reuses standard vocabularies where possible:

- **PROV-O** for provenance
- **Dublin Core (dcterms)** for bibliographic metadata
- **SKOS** for controlled vocabularies
- **OWL/RDFS** for schema definition

---

# Core Concepts

## 1. Artifact Model

All managed objects derive from:

```ttl
orag:Artifact
````

Subclasses:

* `orag:SourceArtifact` — Original source material
* `orag:GraphArtifact` — RDF knowledge graph build
* `orag:IndexArtifact` — Retrieval index
* `orag:QualityReport` — Validation or metrics artifact

### Identity & Versioning

Each artifact can declare:

* `orag:contentHash`
* `orag:hashAlgorithm`
* `orag:status` (Staging / Certified / Deprecated / Revoked)
* `orag:accessPolicy` (Public / Protected / Internal)
* `orag:dependsOn` (artifact dependencies)

This allows deterministic builds and reproducibility.

---

## 2. GraphArtifact

A `GraphArtifact` represents a versioned RDF build.

Key properties:

* `orag:contentGraph` — Named graph IRI containing RDF data
* `orag:manifestGraph` — Named graph IRI containing metadata
* `orag:hasIndex` — Associated `IndexArtifact`
* `orag:dependsOn` — Other graph artifacts (e.g., SRD base)

This supports modular graph composition (e.g., enabling/disabling manuals per session).

---

## 3. IndexArtifact

An `IndexArtifact` describes a retrieval layer built on top of a source or graph.

It abstracts over:

* LlamaIndex
* PageIndex
* Embedding stores
* BM25 / keyword search
* Hybrid retrieval systems

Key properties:

* `orag:indexMethod`
* `orag:indexScope` (Document / Section / Page / Chunk)
* `orag:embeddingModel`
* `orag:storesAt`
* `orag:params` (JSON configuration)
* `orag:citationPolicy`
* `orag:coverage`

This allows multiple indexes per artifact and dynamic routing strategies.

---

## 4. BuildRun (Pipeline Execution)

Each ingestion or transformation step is modeled as:

```ttl
orag:BuildRun
```

Properties:

* `orag:producedArtifact`
* `orag:consumedArtifact`
* `orag:pipelineVersion`

This enables full provenance tracking of transformations from source to graph to index.

---

# RAG Explainability: `orag:SourceSpan`

One of the most important components is `orag:SourceSpan`.

It models a content-type-agnostic span inside a source.

A span:

* Belongs to a `orag:SourceArtifact`
* Has one or more `orag:SpanSelector`
* May contain an `orag:excerpt`
* May declare `orag:confidence`
* Can support a graph or index

Example use cases:

* Page 42–43 in a PDF
* Character offsets in extracted text
* XPath node in HTML
* Time range in audio transcript
* Section path in Markdown

## SpanSelector

Selectors are abstract and flexible:

* `orag:selectorType` (pageRange, charRange, byteRange, timeRange, sectionPath, fragment, domPath)
* `orag:start`
* `orag:end`
* `orag:path`
* `orag:fragment`
* `orag:unit`
* `orag:inclusiveEnd`

This allows spans to remain independent from file formats.

## SpanRepresentation

Because a source may have multiple representations (original PDF, extracted text, HTML snapshot), selectors can attach to:

```ttl
orag:SpanRepresentation
```

This ensures alignment between different ingestion layers.

---

# Licensing & Access Control

Artifacts may declare:

* `orag:accessPolicy`
* `orag:requiresProduct`
* `orag:Product`

  * `orag:store`
  * `orag:productId`

This allows entitlement-aware graph composition without embedding runtime state into the ontology.

Activation (enabled/disabled graphs per session) is modeled conceptually via:

```ttl
orag:ActivationProfile
```

but typically managed at application level.

---

# Controlled Vocabularies

The ontology includes controlled concepts for:

* `orag:ArtifactStatus`
* `orag:AccessPolicy`
* `orag:IndexMethod`
* `orag:IndexScope`
* `orag:CitationPolicy`
* `orag:AnchorScheme`

These are modeled as SKOS-style individuals to allow extension.

---

# Typical Architecture Pattern

A typical OntoRAG-based system may:

1. Ingest a `SourceArtifact`
2. Execute a `BuildRun`
3. Produce:

   * A `GraphArtifact` (named graph RDF)
   * One or more `IndexArtifact`
4. Validate via SHACL
5. Promote artifact status to `orag:Certified`
6. Serve read-only via API or sandboxed SPARQL

`SourceSpan` objects provide explainability for RAG answers and graph assertions.

---

# Why This Matters

OntoRAG is not a domain ontology.

It is **infrastructure ontology**.

It enables:

* Deterministic knowledge graph builds
* Multi-index RAG strategies
* Entitlement-aware graph composition
* Explainable AI outputs
* Reproducible ingestion pipelines
* Format-agnostic citation systems

It treats RAG not as a black box, but as a traceable, inspectable knowledge production system.

---

# Status

Version: `0.1.0`
Namespace: `https://www.ontorag.org/vocab#`

This vocabulary is expected to evolve alongside OntoRAG ingestion and retrieval pipelines.

Contributions and extensions are welcome.
