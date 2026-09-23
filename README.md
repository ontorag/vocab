# OntoRAG Build Vocabulary (`orag:`) and Dataset Format

This repository defines two things:

- **The build vocabulary.** It describes what an OntoRAG pipeline produces and how: datasets, schema cards, exported ontologies, instance graphs, indexes, build runs, baseline ontologies, alignment decisions and governance status.
- **The dataset format.** These are the JSON Schemas for a published dataset's `manifest.json` and its chunk, embedding and entity records.

**Documentation:** https://ontorag.org/vocab/
**Namespace:** `https://ontorag.org/vocab#` · **Prefix:** `orag:` · **Version:** 0.2.0 · **Dataset format:** 0.1

Evidence and composition are covered by the companion [OntoRAG Provenance and Citation Ontology](https://ontorag.org/provenance/) (`orp:`): where a resource comes from, how to cite it, and how per-source packs compose. The two specifications share PROV-O, and an `orag:Dataset` is a `void:Dataset` whose subsets are `orp:Pack`s.

## Repository

| Path | Contents |
|---|---|
| `orag.ttl` | The vocabulary |
| `dataset/0.1/*.schema.json` | Dataset format: `manifest`, `chunk`, `embedding`, `entity` (served at `https://ontorag.org/vocab/dataset/0.1/`) |
| `examples/` | A governed build lineage, the Ars Magica dataset's build metadata, and sample dataset records |
| `tools/check.py` | Validates the vocabulary, the schemas and the samples |
| `tools/build_site.py` | Builds the documentation site into `_site/` |

```sh
uv run --with rdflib --with jsonschema tools/check.py            # add --remote to verify external terms exist
uv run --with rdflib tools/build_site.py
```

## Changes from 0.1.0

Version 0.2.0 changes the namespace from `https://www.ontorag.org/vocab#` to `https://ontorag.org/vocab#`. It removes the terms that overlapped with `orp:`, drops store and entitlement terms (these belong to the serving application), and adds datasets, schema cards, stages, baselines and alignment. The documentation has a [full migration table](https://ontorag.org/vocab/#changes). This repository was previously named `ontorag/schemas`.

## Licence

[CC0 1.0](LICENSE). The sample dataset records in `examples/dataset/` come from the Ars Magica Open License and are CC-BY-SA 4.0.
