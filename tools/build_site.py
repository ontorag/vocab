"""Build the documentation site into _site/ from the vocabulary, dataset schemas and examples.

    uv run --with rdflib tools/build_site.py
"""
import html
import json
import shutil
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, SKOS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
ORP = Namespace("https://ontorag.org/vocab#")
ONTOLOGY = URIRef("https://ontorag.org/vocab")

ont = Graph().parse(ROOT / "orag.ttl")
nm = ont.namespace_manager


def local(term):
    return str(term)[len(str(ORP)):]


def link(term):
    """Link an IRI: orag: terms to their anchor, others to their IRI, shown as a prefixed name."""
    if isinstance(term, URIRef) and str(term).startswith(str(ORP)):
        return f'<a href="#{anchor(term)}"><code>orag:{local(term)}</code></a>'
    try:
        name = term.n3(nm)
    except Exception:
        name = str(term)
    return f'<a href="{html.escape(str(term))}"><code>{html.escape(name)}</code></a>'


def anchor(term):
    return f"vocab-{local(term)}" if term in schemes else local(term)


def links(terms):
    return ", ".join(link(t) for t in sorted(terms, key=str))


def text(value):
    return " ".join(html.escape(str(value)).split())


def rows(pairs):
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in pairs if v)
    return f"<dl>{body}</dl>" if body else ""


def orp_terms(kind):
    return sorted((s for s in ont.subjects(RDF.type, kind) if str(s).startswith(str(ORP))), key=local)


schemes = {c for c in orp_terms(OWL.Class) if (c, RDFS.subClassOf, SKOS.Concept) in ont}
classes = [c for c in orp_terms(OWL.Class) if c not in schemes]
properties = sorted(set(orp_terms(OWL.ObjectProperty)) | set(orp_terms(OWL.DatatypeProperty)), key=local)


def render_class(c):
    subclasses = set(ont.subjects(RDFS.subClassOf, c))
    used_by = set(ont.subjects(RDFS.domain, c))
    targeted_by = set(ont.subjects(RDFS.range, c))
    return f"""
<article class="term" id="{local(c)}">
  <h4>orag:{local(c)} <span class="label">{text(ont.value(c, RDFS.label))}</span><span class="kind">Class</span></h4>
  <p class="iri">{html.escape(str(c))}</p>
  <p>{text(ont.value(c, RDFS.comment))}</p>
  {rows([
      ("Sub-class of", links(ont.objects(c, RDFS.subClassOf))),
      ("Super-class of", links(subclasses)),
      ("Close match", links(ont.objects(c, SKOS.closeMatch))),
      ("Properties", links(used_by)),
      ("Value of", links(targeted_by)),
  ])}
</article>"""


def render_property(p):
    kinds = {OWL.ObjectProperty: "Object property", OWL.DatatypeProperty: "Datatype property"}
    kind = next(v for k, v in kinds.items() if (p, RDF.type, k) in ont)
    trait_text = ", ".join(label for t, label in ((OWL.FunctionalProperty, "functional"),
                                                  (OWL.TransitiveProperty, "transitive"))
                           if (p, RDF.type, t) in ont)
    chain = ont.value(p, OWL.propertyChainAxiom)
    chain_text = " ∘ ".join(link(t) for t in Collection(ont, chain)) if chain else ""
    inverse = set(ont.objects(p, OWL.inverseOf)) | set(ont.subjects(OWL.inverseOf, p))
    return f"""
<article class="term" id="{local(p)}">
  <h4>orag:{local(p)} <span class="label">{text(ont.value(p, RDFS.label))}</span><span class="kind">{kind}</span></h4>
  <p class="iri">{html.escape(str(p))}</p>
  <p>{text(ont.value(p, RDFS.comment))}</p>
  {rows([
      ("Domain", links(ont.objects(p, RDFS.domain))),
      ("Range", links(ont.objects(p, RDFS.range))),
      ("Sub-property of", links(ont.objects(p, RDFS.subPropertyOf))),
      ("Super-property of", links(ont.subjects(RDFS.subPropertyOf, p))),
      ("Inverse", links(inverse)),
      ("Property chain", chain_text),
      ("Characteristics", trait_text),
  ])}
</article>"""


def render_scheme(c):
    members = sorted(ont.subjects(RDF.type, c), key=local)
    rows_html = "".join(
        f'<tr id="{local(m)}"><td><code>orag:{local(m)}</code></td>'
        f'<td>{text(ont.value(m, SKOS.prefLabel))}</td><td>{text(ont.value(m, SKOS.definition) or "")}</td></tr>'
        for m in members)
    return f"""
<article class="scheme" id="vocab-{local(c)}">
  <h4><code>orag:{local(c)}</code> <span class="label">{text(ont.value(c, RDFS.label))}</span></h4>
  <p>{text(ont.value(c, RDFS.comment))} Used by {links(ont.subjects(RDFS.range, c))}.</p>
  <table><thead><tr><th>Value</th><th>Label</th><th>Definition</th></tr></thead><tbody>{rows_html}</tbody></table>
</article>"""


def manifest_fields():
    schema = json.loads((ROOT / "dataset" / "0.1" / "manifest.schema.json").read_text())
    out = []

    def walk(node, prefix, required, depth):
        for key, spec in node.get("properties", {}).items():
            req = '<span class="req">*</span>' if key in required else ""
            kind = spec.get("type", "")
            out.append(f"<tr><td>{prefix}{key}{req}</td><td>{kind}</td><td>{text(spec.get('description', ''))}</td></tr>")
            if kind == "object" and depth == 0:
                walk(spec, f"{prefix}{key}.", spec.get("required", []), 1)

    walk(schema, "", schema.get("required", []), 0)
    return ('<table class="fields"><thead><tr><th>Field</th><th>Type</th><th>Meaning</th></tr></thead><tbody>'
            + "".join(out) + "</tbody></table>")


def build():
    version = str(ont.value(ONTOLOGY, OWL.versionInfo))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    toc = "".join(f'<li><a href="#{anchor(t)}">{local(t)}</a></li>' for t in classes + properties)
    page = (ROOT / "site" / "template.html").read_text()
    page = (page.replace("{{VERSION}}", version)
                .replace("{{TOC_TERMS}}", toc)
                .replace("{{CLASSES}}", "".join(render_class(c) for c in classes))
                .replace("{{PROPERTIES}}", "".join(render_property(p) for p in properties))
                .replace("{{SCHEMES}}", "".join(render_scheme(c) for c in sorted(schemes, key=local)))
                .replace("{{MANIFEST_FIELDS}}", manifest_fields())
                .replace("{{EXAMPLE_PIPELINE}}", html.escape((ROOT / "examples" / "governed-pipeline.ttl").read_text()))
                .replace("{{EXAMPLE_AMOL}}", html.escape((ROOT / "examples" / "amol-build.ttl").read_text())))
    assert "{{" not in page, "unfilled placeholder in template"
    (OUT / "index.html").write_text(page)
    shutil.copy(ROOT / "site" / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("")

    # serialisations, current and versioned (the owl:versionIRI resolves to the versioned folder)
    versioned = OUT / version
    versioned.mkdir()
    for fmt, ext in (("turtle", "ttl"), ("json-ld", "jsonld"), ("nt", "nt"), ("xml", "rdf")):
        data = ont.serialize(format=fmt) if fmt != "turtle" else (ROOT / "orag.ttl").read_text()
        for folder in (OUT, versioned):
            (folder / f"orag.{ext}").write_text(data)
    (versioned / "index.html").write_text(
        f'<!doctype html><meta charset="utf-8"><title>OntoRAG Build Vocabulary {version}</title>'
        f'<link rel="alternate" type="text/turtle" href="orag.ttl">'
        f'<p>OntoRAG Build Vocabulary, version {version}: '
        f'<a href="orag.ttl">Turtle</a> · <a href="orag.jsonld">JSON-LD</a> · '
        f'<a href="orag.rdf">RDF/XML</a> · <a href="orag.nt">N-Triples</a>. '
        f'Documentation: <a href="../">latest</a>.</p>')

    for folder in ("examples", "dataset"):
        shutil.copytree(ROOT / folder, OUT / folder)
    print(f"built {OUT} (version {version}, {len(classes)} classes, {len(properties)} properties)")


if __name__ == "__main__":
    build()
