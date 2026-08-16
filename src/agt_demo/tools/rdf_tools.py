"""Governed RDF tools (generation, validation, visualization, critique)."""
from __future__ import annotations
from pathlib import Path
from typing import Any, List
from langchain_core.tools import tool
from agt_demo.config import repo_root
from agt_demo.governance import check_policy

SAMPLE_TEXT_FALLBACK = """
The Microsoft Agent Governance Toolkit provides runtime security for AI agents.
Agent OS intercepts actions. Agent Mesh provides identity. Agent Runtime uses privilege rings.
Agent SRE applies reliability practices. Agent Compliance maps to regulatory frameworks.
Agent Marketplace secures the plugin supply chain. Agent Lightning governs RL training.
""".strip()

def _out(cfg) -> Path:
    p = repo_root() / cfg.get("artifacts", {}).get("output_dir", "output")
    p.mkdir(parents=True, exist_ok=True)
    return p

def build_knowledge_tools(cfg: dict[str, Any], governor, agent_id: str = "knowledge") -> List:
    def _check(action: str) -> None:
        check_policy(governor, cfg, action, agent_id=agent_id, acs=cfg.get("_acs"))

    @tool
    def generate_rdf_kg(text: str = "", slug: str = "agt-demo") -> str:
        """Generate an RDF Turtle knowledge graph from text."""
        _check("generate_rdf_kg")
        from rdflib import Graph, Namespace, Literal, URIRef
        from rdflib.namespace import RDF, RDFS, XSD
        g = Graph()
        EX = Namespace("https://example.org/kg/")
        SCHEMA = Namespace("https://schema.org/")
        PROV = Namespace("http://www.w3.org/ns/prov#")
        g.bind("ex", EX)
        g.bind("schema", SCHEMA)
        g.bind("prov", PROV)
        subj = EX[slug]
        g.add((subj, RDF.type, SCHEMA.SoftwareApplication))
        g.add((subj, RDFS.label, Literal("Agent Governance Toolkit Demo")))
        g.add((subj, SCHEMA.description, Literal((text or SAMPLE_TEXT_FALLBACK)[:500])))
        g.add((subj, PROV.wasGeneratedBy, EX["agent-control-lab"]))
        for i, name in enumerate(["AgentOS", "AgentMesh", "AgentRuntime", "AgentSRE", "AgentCompliance", "AgentMarketplace", "AgentLightning"]):
            n = EX[name.lower()]
            g.add((n, RDF.type, SCHEMA.SoftwareComponent))
            g.add((n, RDFS.label, Literal(name)))
            g.add((subj, SCHEMA.hasPart, n))
        out = _out(cfg) / f"{slug}-kg.ttl"
        g.serialize(destination=str(out), format="turtle")
        msg = f"Generated RDF with {len(g)} triples.\nPrimary subject: {subj}\nWritten to: {out}"
        print(msg)
        return msg

    @tool
    def validate_rdf(ttl_path: str) -> str:
        """Validate a Turtle RDF file and report triple counts."""
        _check("validate_rdf")
        from rdflib import Graph
        p = Path(ttl_path)
        if not p.exists():
            p = _out(cfg) / ttl_path
        g = Graph()
        g.parse(str(p), format="turtle")
        subjects = set(g.subjects())
        msg = f"VALID. {len(g)} triples, {len(subjects)} subjects. File: {p}"
        print(msg)
        return msg

    @tool
    def create_rdf_infographic(ttl_path: str) -> str:
        """Create a simple interactive HTML explorer for the RDF graph."""
        _check("create_rdf_infographic")
        from rdflib import Graph
        p = Path(ttl_path)
        if not p.exists():
            p = _out(cfg) / ttl_path
        g = Graph()
        g.parse(str(p), format="turtle")
        nodes = {}
        edges = []
        for s, pred, o in g:
            nodes[str(s)] = str(s).split("/")[-1][:40]
            if hasattr(o, "n3") and not str(o).startswith('"'):
                nodes[str(o)] = str(o).split("/")[-1][:40]
                edges.append((str(s), str(pred).split("#")[-1].split("/")[-1], str(o)))
        html_path = p.with_name(p.stem.replace("-kg", "") + "-kg-explorer.html")
        if not str(html_path).endswith("-explorer.html"):
            html_path = _out(cfg) / (p.stem + "-explorer.html")
        node_js = ",".join(f"{{id:'{k}',label:'{v}'}}" for k, v in list(nodes.items())[:40])
        edge_js = ",".join(f"{{from:'{a}',to:'{c}',label:'{b}'}}" for a, b, c in edges[:60])
        html = f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>RDF Explorer</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{{font-family:sans-serif;margin:0}}#m{{height:90vh;border:1px solid #ccc}}</style></head>
<body><h3>Agent Control Lab · RDF Explorer</h3><div id=m></div>
<script>
const nodes=new vis.DataSet([{node_js}]);
const edges=new vis.DataSet([{edge_js}]);
new vis.Network(document.getElementById('m'),{{nodes,edges}},{{physics:{{enabled:true}}}});
</script></body></html>"""
        html_path.write_text(html, encoding="utf-8")
        msg = f"Interactive HTML written to: {html_path} ({len(nodes)} nodes, {len(edges)} edges)"
        print(msg)
        return msg

    @tool
    def list_artifacts() -> str:
        """List files in the output directory."""
        _check("list_artifacts")
        files = sorted(_out(cfg).glob("*"))
        msg = "\n".join(f"- {f.name} ({f.stat().st_size} bytes)" for f in files) or "No artifacts."
        print(msg)
        return msg

    @tool
    def delete_file(path: str) -> str:
        """Delete a file (expected to be denied by policy)."""
        _check("delete_file")
        Path(path).unlink(missing_ok=True)
        return f"Deleted {path}"

    return [generate_rdf_kg, validate_rdf, create_rdf_infographic, list_artifacts, delete_file]

def build_critic_tools(cfg: dict[str, Any], governor, agent_id: str = "critic") -> List:
    def _check(action: str) -> None:
        check_policy(governor, cfg, action, agent_id=agent_id, acs=cfg.get("_acs"))

    @tool
    def validate_rdf(ttl_path: str) -> str:
        """Validate a Turtle RDF file."""
        _check("validate_rdf")
        from rdflib import Graph
        p = Path(ttl_path)
        if not p.exists():
            p = _out(cfg) / ttl_path
        g = Graph()
        g.parse(str(p), format="turtle")
        msg = f"VALID. {len(g)} triples, {len(set(g.subjects()))} subjects. File: {p}"
        print(msg)
        return msg

    @tool
    def critique_rdf(ttl_path: str) -> str:
        """Grade RDF quality (labels, types, provenance, schema.org)."""
        _check("critique_rdf")
        from rdflib import Graph, RDF, RDFS
        from rdflib.namespace import Namespace
        p = Path(ttl_path)
        if not p.exists():
            p = _out(cfg) / ttl_path
        g = Graph()
        g.parse(str(p), format="turtle")
        subjects = list(set(g.subjects()))
        score = 70
        notes = []
        labeled = sum(1 for s in subjects if list(g.objects(s, RDFS.label)))
        typed = sum(1 for s in subjects if list(g.objects(s, RDF.type)))
        if labeled >= len(subjects) * 0.5:
            score += 10
            notes.append("- Most subjects have rdfs:label.")
        if typed >= len(subjects) * 0.5:
            score += 10
            notes.append("- Most subjects have rdf:type.")
        if any("prov" in str(pred).lower() for pred in g.predicates()):
            score += 5
            notes.append("- Provenance present (prov:).")
        if any("schema.org" in str(o) for o in g.objects()):
            score += 5
            notes.append("- Good schema.org usage.")
        grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D"
        msg = f"Critique of {p.name}: grade={grade} (score={score}/100)\nSubjects={len(subjects)}, triples={len(g)}\n" + "\n".join(notes)
        print(msg)
        return msg

    @tool
    def list_artifacts() -> str:
        """List output artifacts."""
        _check("list_artifacts")
        files = sorted(_out(cfg).glob("*"))
        msg = "\n".join(f"- {f.name}" for f in files) or "No artifacts."
        print(msg)
        return msg

    @tool
    def read_artifact(path: str) -> str:
        """Read first 40 lines of an artifact."""
        _check("read_artifact")
        p = Path(path)
        if not p.exists():
            p = _out(cfg) / path
        if not p.exists():
            return f"Not found: {path}"
        return "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:40])

    return [validate_rdf, critique_rdf, list_artifacts, read_artifact]
