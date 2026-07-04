# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any


def safe_float(x: Any, ndigits: int = 4):
    try:
        if x is None:
            return None
        return round(float(x), ndigits)
    except Exception:
        return None


def to_jsonable(obj: Any):
    """Best-effort conversion for pymatgen / pydantic / numpy objects."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return to_jsonable(obj.model_dump())
    if hasattr(obj, "as_dict"):
        return to_jsonable(obj.as_dict())
    if hasattr(obj, "tolist"):
        return obj.tolist()
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def structure_summary(structure):
    lattice = structure.lattice
    a, b, c = lattice.abc
    alpha, beta, gamma = lattice.angles
    sites = []
    for idx, site in enumerate(structure):
        sites.append({
            "index": idx,
            "element": site.species_string,
            "frac_coords": [safe_float(v, 6) for v in site.frac_coords],
            "cart_coords": [safe_float(v, 6) for v in site.coords],
        })
    return {
        "formula": structure.composition.reduced_formula,
        "nsites": len(structure),
        "volume": safe_float(structure.volume, 6),
        "density": safe_float(structure.density, 6),
        "lattice": {
            "a": safe_float(a, 6), "b": safe_float(b, 6), "c": safe_float(c, 6),
            "alpha": safe_float(alpha, 6), "beta": safe_float(beta, 6), "gamma": safe_float(gamma, 6),
            "matrix": [[safe_float(v, 6) for v in row] for row in lattice.matrix],
        },
        "sites": sites,
    }
