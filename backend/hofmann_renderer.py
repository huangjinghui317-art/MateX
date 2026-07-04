# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, List

import matplotlib
matplotlib.use("Agg")

from pymatgen.core import Structure
from pymatgen.core.periodic_table import Element

from .utils import structure_summary

try:
    from hofmann import StructureScene, BondSpec
    HOFMANN_AVAILABLE = True
except Exception:
    StructureScene = None
    BondSpec = None
    HOFMANN_AVAILABLE = False


def _bond_spec(sp1: str, sp2: str, max_len: float):
    """Compatible BondSpec constructor for different hofmann versions."""
    try:
        return BondSpec(species=(sp1, sp2), max_length=max_len)
    except TypeError:
        try:
            return BondSpec((sp1, sp2), max_len)
        except TypeError:
            return BondSpec(sp1, sp2, max_len)


def build_bonds_from_structure(structure: Structure, scale: float = 1.12):
    """
    Build Hofmann bonds exactly in the style provided by the user:
      - species are collected from structure.sites
      - radius uses Element(sp).covalent_radius
      - fallback radius is 1.25
      - cutoff = scale * (r1 + r2)
      - no bond_margin / bond_cap clipping is applied
    """
    if not HOFMANN_AVAILABLE:
        return []

    species = sorted({str(site.specie.symbol) for site in structure.sites})
    radii: dict[str, float] = {}

    for sp in species:
        try:
            r = getattr(Element(sp), "covalent_radius", None)
            radii[sp] = float(r) if r is not None else 1.25
        except Exception:
            radii[sp] = 1.25

    bonds = []
    for i, sp1 in enumerate(species):
        for sp2 in species[i:]:
            bonds.append(_bond_spec(sp1, sp2, scale * (radii[sp1] + radii[sp2])))
    return bonds


def render_three_views(
    structure: Structure,
    out_dir: Path,
    prefix: str,
    zoom: float = 1.20,
    bond_scale: float = 1.12,
) -> List[Path]:
    """
    Render three Hofmann views following the reference implementation:
      scene = StructureScene.from_pymatgen(structure, bonds)
      scene.view.look_along(direction)
      scene.view.zoom = zoom
      scene.view.perspective = 0.0
      scene.render_mpl(str(out))
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if not HOFMANN_AVAILABLE:
        return []

    bonds = build_bonds_from_structure(structure, scale=bond_scale)
    directions = {
        "view_100": (1, 0, 0),
        "view_010": (0, 1, 0),
        "view_001": (0, 0, 1),
    }

    paths: List[Path] = []
    for name, direction in directions.items():
        out = out_dir / f"{prefix}_{name}.png"
        scene = StructureScene.from_pymatgen(structure, bonds)
        scene.view.look_along(direction)
        scene.view.zoom = zoom
        scene.view.perspective = 0.0
        scene.render_mpl(str(out))
        paths.append(out)
    return paths


def _parse_structure(cif_text: str) -> Structure:
    return Structure.from_str(cif_text, fmt="cif")


def _spacegroup_payload(structure: Structure) -> dict[str, Any]:
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        sga = SpacegroupAnalyzer(structure, symprec=1e-2, angle_tolerance=5.0)
        ds = sga.get_symmetry_dataset()
        try:
            wyckoffs = list(ds.get("wyckoffs", []))
        except Exception:
            try:
                wyckoffs = list(ds["wyckoffs"])
            except Exception:
                wyckoffs = []
        return {
            "space_group_symbol": sga.get_space_group_symbol(),
            "space_group_number": sga.get_space_group_number(),
            "crystal_system": sga.get_crystal_system(),
            "lattice_type": sga.get_lattice_type(),
            "wyckoffs": wyckoffs,
        }
    except Exception as exc:
        return {"warning": str(exc)}


def render_hofmann_from_cif(
    cif_text: str,
    out_root: Path,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Web API wrapper around the exact Hofmann rendering logic requested by the user.
    Only zoom and bond_scale are accepted as meaningful rendering controls here.
    Perspective is intentionally fixed to 0.0 to match the reference code.
    """
    params = params or {}
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    structure = _parse_structure(cif_text)
    summary = structure_summary(structure)
    summary["cif"] = structure.to(fmt="cif")
    summary["formula_pretty"] = structure.composition.reduced_formula
    summary["sites"] = summary.get("sites", [])

    run_id = f"{int(time.time())}_{uuid.uuid4().hex[:10]}"
    out_dir = out_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    cif_path = out_dir / "normalized.cif"
    cif_path.write_text(structure.to(fmt="cif"), encoding="utf-8")

    zoom = float(params.get("zoom", 1.20))
    bond_scale = float(params.get("bond_scale", 1.12))

    if not HOFMANN_AVAILABLE:
        images: list[dict[str, str]] = []
        status = "fallback_required"
        warning = "Hofmann package is unavailable. Frontend fallback projection is used."
    else:
        try:
            paths = render_three_views(
                structure=structure,
                out_dir=out_dir,
                prefix="hofmann",
                zoom=zoom,
                bond_scale=bond_scale,
            )
            images = [
                {
                    "name": path.stem.replace("hofmann_", ""),
                    "url": f"/static/generated/hofmann/{run_id}/{path.name}",
                }
                for path in paths
            ]
            status = "rendered_with_hofmann"
            warning = None
        except Exception as exc:
            images = []
            status = "fallback_required"
            warning = f"Hofmann rendering failed: {exc}"

    return {
        "status": status,
        "warning": warning,
        "images": images,
        "material": {
            **summary,
            "spacegroup": _spacegroup_payload(structure),
            "material_id": "uploaded-cif",
            "elements": sorted({site.specie.symbol for site in structure}),
        },
        "params": {
            "zoom": zoom,
            "bond_scale": bond_scale,
            "perspective": 0.0,
            "bond_rule": "covalent_radius_sum_times_scale_no_margin_no_cap",
        },
    }
