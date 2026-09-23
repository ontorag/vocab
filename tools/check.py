"""Validate the vocabulary, its examples and the dataset format schemas.

    uv run --with rdflib --with jsonschema tools/check.py            # offline checks
    uv run --with rdflib --with jsonschema tools/check.py --remote   # also verify external terms exist
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

ROOT = Path(__file__).resolve().parent.parent
ORAG = Namespace("https://ontorag.org/vocab#")
SPEC = ROOT / "dataset" / "0.1"
SAMPLE = ROOT / "examples" / "dataset"

EXTERNAL = {
    "https://ontorag.org/provenance#": "https://ontorag.org/provenance/provenance.ttl",
    "http://www.w3.org/ns/prov#": "https://www.w3.org/ns/prov.ttl",
    "http://rdfs.org/ns/void#": "https://raw.githubusercontent.com/cygri/void/master/rdfs/void.ttl",
    "http://purl.org/dc/terms/": "https://www.dublincore.org/specifications/dublin-core/dcmi-terms/dublin_core_terms.ttl",
    "http://www.w3.org/2004/02/skos/core#": "https://www.w3.org/2009/08/skos-reference/skos.rdf",
}

failures = []


def check(ok, message):
    print(("  ok    " if ok else "  FAIL  ") + message)
    if not ok:
        failures.append(message)


def used_terms(graph, namespace):
    return {n for t in graph for n in t
            if isinstance(n, URIRef) and str(n).startswith(namespace) and str(n) != namespace}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", action="store_true", help="dereference external vocabularies")
    args = ap.parse_args()

    print("vocabulary")
    ont = Graph().parse(ROOT / "orag.ttl")
    examples = Graph()
    for path in sorted((ROOT / "examples").glob("*.ttl")):
        examples.parse(path)
    check(len(ont) > 0 and len(examples) > 0, "vocabulary and examples parse")

    declared = {s for s in ont.subjects(RDF.type, None) if str(s).startswith(str(ORAG))}
    for label, graph in (("vocabulary", ont), ("examples", examples)):
        missing = used_terms(graph, str(ORAG)) - declared
        check(not missing, f"every orag: term used in {label} is declared {sorted(missing) or ''}")
    undocumented = sorted(
        t for t in declared
        if not ((ont.value(t, RDFS.label) and ont.value(t, RDFS.comment))
                or (ont.value(t, SKOS.prefLabel) and ont.value(t, SKOS.definition))))
    check(not undocumented, f"every term has a label and a definition {undocumented or ''}")

    print("dataset format")
    schemas = {}
    for path in sorted(SPEC.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        Draft7Validator.check_schema(schema)
        expected_id = f"https://ontorag.org/vocab/dataset/0.1/{path.name}"
        check(schema["$id"] == expected_id, f"{path.name} is a valid JSON Schema with $id {expected_id}")
        schemas[path.name.split(".")[0]] = schema

    def conforms(kind, instance, what):
        errors = sorted(Draft7Validator(schemas[kind]).iter_errors(instance), key=lambda e: e.path)
        check(not errors, f"{what} conforms to {kind}.schema.json "
                          f"{[f'{list(e.path)}: {e.message}' for e in errors[:3]] or ''}")

    conforms("manifest", json.loads((SAMPLE / "manifest.json").read_text()), "sample manifest.json")
    for kind in ("chunk", "entity", "embedding"):
        for i, line in enumerate((SAMPLE / f"{kind}.jsonl").read_text().splitlines()):
            conforms(kind, json.loads(line), f"sample {kind}.jsonl line {i + 1}")

    if args.remote:
        print("external terms")
        combined = ont + examples
        for ns, url in EXTERNAL.items():
            try:
                vocab = Graph().parse(url, format="xml" if url.endswith(".rdf") else "turtle")
            except Exception as e:
                check(False, f"fetch {url}: {e}")
                continue
            defined = set(vocab.subjects())
            missing = sorted(t for t in used_terms(combined, ns) if t not in defined)
            check(not missing, f"all terms used from {ns} exist {missing or ''}")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
