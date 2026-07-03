"""Model code generation service.

Takes a React Flow graph (nodes + edges) and generates a PyTorch nn.Module
subclass.  When a Gemini API key is available the generated skeleton is
refined by the LLM; otherwise a clean template-only output is returned.
"""

from __future__ import annotations

import logging
import os
import re
import textwrap
from pathlib import Path
from typing import Any

from rbccps_dashboard.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in component templates
# ---------------------------------------------------------------------------

_BUILTIN_TEMPLATES: dict[str, dict[str, str]] = {
    "Input": {
        "init": "",
        "forward": "# x is the raw input tensor",
    },
    "Backbone": {
        "init": "self.backbone = CSPDarknet53()  # Replace with chosen variant",
        "forward": "x = self.backbone(x)",
    },
    "PAN/FPN": {
        "init": "self.neck = PANet(SPPF())",
        "forward": "x = self.neck(x)",
    },
    "CSE": {
        "init": "self.cse = ChannelSpatialExcitation(reduction_ratio=16)",
        "forward": "x = self.cse(x)",
    },
    "Geometry Attention": {
        "init": "self.geom_attn = GeometryAttention(kernel_size=3)",
        "forward": "x = self.geom_attn(x)",
    },
    "Negative Attention": {
        "init": "self.neg_attn = NegativeAttention()",
        "forward": "x = self.neg_attn(x)",
    },
    "Detection Head": {
        "init": "self.head = YOLODetectionHead(num_classes=num_classes)",
        "forward": "x = self.head(x)",
    },
    "Tracking": {
        "init": "self.tracker = ObjectTracker()",
        "forward": "x = self.tracker(x)",
    },
}


def _snake(name: str) -> str:
    """Convert a label to a valid Python identifier."""
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return s or "layer"


def _topo_sort(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Topological sort of nodes using Kahn's algorithm."""
    id_to_node = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}

    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if src in adj and tgt in in_degree:
            adj[src].append(tgt)
            in_degree[tgt] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    ordered: list[dict] = []
    while queue:
        nid = queue.pop(0)
        ordered.append(id_to_node[nid])
        for child in adj.get(nid, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Append any remaining (cycle or disconnected)
    visited = {n["id"] for n in ordered}
    for n in nodes:
        if n["id"] not in visited:
            ordered.append(n)

    return ordered


def _generate_template_code(graph: dict[str, Any]) -> str:
    """Generate a PyTorch nn.Module from the graph using templates only."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    sorted_nodes = _topo_sort(nodes, edges)

    # Gather user components
    settings = get_settings()
    user_comp_dir = settings.project_root / "user_components"
    user_imports: list[str] = []
    init_lines: list[str] = []
    forward_lines: list[str] = []

    seen_labels: dict[str, int] = {}

    for node in sorted_nodes:
        label = node.get("data", {}).get("label", node.get("type", "Unknown"))
        # Deduplicate labels
        if label in seen_labels:
            seen_labels[label] += 1
            suffix = f"_{seen_labels[label]}"
        else:
            seen_labels[label] = 0
            suffix = ""

        attr_name = _snake(label) + suffix

        if label in _BUILTIN_TEMPLATES:
            tpl = _BUILTIN_TEMPLATES[label]
            if tpl["init"]:
                init_lines.append(f"        {tpl['init']}")
            if tpl["forward"]:
                forward_lines.append(f"        {tpl['forward']}")
        else:
            # Check for user component
            snake_name = _snake(label)
            class_name = label.replace(" ", "")
            user_py = user_comp_dir / f"{snake_name}.py"
            if user_py.exists():
                user_imports.append(
                    f"from user_components.{snake_name} import {class_name}"
                )
            init_lines.append(f"        self.{attr_name} = {class_name}()")
            forward_lines.append(f"        x = self.{attr_name}(x)")

    # Assemble code
    imports_section = "\n".join(user_imports)
    if imports_section:
        imports_section = "\n" + imports_section + "\n"

    init_block = "\n".join(init_lines) if init_lines else "        pass"
    forward_block = "\n".join(forward_lines) if forward_lines else "        pass"

    lines = [
        '"""Auto-generated model from Architecture Builder."""',
        "",
        "import torch",
        "import torch.nn as nn",
    ]
    if imports_section:
        lines.append(imports_section)
    lines += [
        "",
        "",
        "class CustomYOLOModel(nn.Module):",
        '    """Custom YOLO-like detection model."""',
        "",
        "    def __init__(self, num_classes: int = 80):",
        "        super().__init__()",
        init_block,
        "",
        "    def forward(self, x: torch.Tensor) -> torch.Tensor:",
        forward_block,
        "        return x",
        "",
    ]
    return "\n".join(lines) + "\n"


def _refine_with_gemini(template_code: str, graph: dict[str, Any]) -> str:
    """Use Gemini API to refine the generated model code."""
    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.info("No Gemini API key found — returning template-only code")
            return template_code

        from google import genai

        client = genai.Client(api_key=api_key)

        node_labels = [n.get("data", {}).get("label", "?") for n in graph.get("nodes", [])]
        edge_desc = [
            f"{e.get('source')} → {e.get('target')}"
            for e in graph.get("edges", [])
        ]

        prompt = textwrap.dedent(f"""\
            You are a PyTorch expert. I have a visual architecture graph for a YOLO-like
            object detection model. The graph nodes (in order) are:
            {', '.join(node_labels)}

            The edges are: {'; '.join(edge_desc) if edge_desc else 'sequential'}

            Here is a template code skeleton that was auto-generated:

            ```python
            {template_code}
            ```

            Please refine this code into a complete, runnable PyTorch nn.Module.
            - Keep the class name `CustomYOLOModel`.
            - Use realistic layer definitions (Conv2d, BatchNorm2d, etc.) where placeholders exist.
            - Only output the Python code, no explanations.
            - Keep all user_components imports intact.
            - The model should be for object detection only (no segmentation).
        """)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        refined = response.text
        # Strip markdown fences if present
        if "```python" in refined:
            refined = refined.split("```python", 1)[1]
            if "```" in refined:
                refined = refined.rsplit("```", 1)[0]
        return refined.strip() + "\n"

    except Exception:
        logger.warning("Gemini refinement failed — returning template code", exc_info=True)
        return template_code


def generate_model_code(graph: dict[str, Any]) -> str:
    """Generate model code from an architecture graph.

    Tries Gemini refinement first; falls back to template-only output.
    """
    template = _generate_template_code(graph)
    return _refine_with_gemini(template, graph)
