# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
from copy import deepcopy
from typing import Any

from .mock_data import MOCK_MATERIALS, PERIODIC_ELEMENTS
from .utils import to_jsonable, safe_float


class MPClient:
    def __init__(self):
        self.api_key = os.getenv("MP_API_KEY", "").strip()
        self.allow_mock = os.getenv("MATEX_ALLOW_MOCK", "1") != "0"

    def enabled(self) -> bool:
        return bool(self.api_key)

    def periodic_table(self) -> dict:
        return {"elements": [{"row": r, "col": c, "symbol": s, "category": cat} for r, c, s, cat in PERIODIC_ELEMENTS]}

    def _classify(self, elements: list[str]) -> str:
        # Materials Project mainly contains inorganic crystal structures; this is a UI-side helper.
        if "C" in elements and "H" in elements:
            return "organic-like"
        return "inorganic"

    def _ensure_mock_cif(self, m: dict) -> dict:
        """Attach a lightweight CIF to mock materials so every card can use the real Hofmann backend renderer."""
        out = deepcopy(m)
        if out.get("cif"):
            return out
        try:
            from pymatgen.core import Lattice, Structure
            species = [site.get("element", "X") for site in out.get("sites", [])]
            coords = [site.get("frac_coords", [0, 0, 0]) for site in out.get("sites", [])]
            if not species:
                return out
            # Mock structures are only for UI demonstration. Real MP queries return true CIF from MP structures.
            lattice_len = 5.40
            if out.get("formula_pretty") in {"BaTiO3", "TiO2"}:
                lattice = Lattice.tetragonal(4.05, 4.20)
            elif out.get("formula_pretty") == "GaN":
                lattice = Lattice.hexagonal(3.19, 5.19)
            elif out.get("formula_pretty") == "LiFePO4":
                lattice = Lattice.orthorhombic(10.33, 6.01, 4.69)
            else:
                lattice = Lattice.cubic(lattice_len)
            structure = Structure(lattice, species, coords, coords_are_cartesian=False, to_unit_cell=True)
            out["cif"] = structure.to(fmt="cif")
        except Exception:
            pass
        return out

    def _mock_search(self, query: str, mode: str, elements: list[str], material_class: str, limit: int) -> dict:
        q = (query or "").strip().lower()
        selected = set(elements or [])
        docs = []
        for m in MOCK_MATERIALS:
            m_e = set(m.get("elements", []))
            ok = True
            if q:
                ok = q in m["formula_pretty"].lower() or q in m["material_id"].lower() or all(x.lower() in m["formula_pretty"].lower() for x in re.findall(r"[A-Z][a-z]?", query))
            if selected:
                if mode == "only":
                    ok = ok and m_e.issubset(selected)
                elif mode == "atleast":
                    ok = ok and selected.issubset(m_e)
                elif mode == "formula":
                    ok = ok and (m["formula_pretty"].lower() == q)
            if material_class != "all":
                ok = ok and self._classify(list(m_e)) == material_class
            if ok:
                docs.append(self._ensure_mock_cif(m))
        if not docs:
            docs = [self._ensure_mock_cif(m) for m in MOCK_MATERIALS]
        return {"source": "mock", "total": len(docs), "materials": docs[:limit]}

    def search(self, query: str = "", mode: str = "formula", elements: list[str] | None = None, material_class: str = "all", limit: int = 20) -> dict:
        limit = max(1, min(int(limit or 20), 100))
        if not self.api_key:
            return self._mock_search(query, mode, elements or [], material_class, limit)
        try:
            from mp_api.client import MPRester
            fields = [
                "material_id", "formula_pretty", "elements", "structure", "symmetry",
                "density", "band_gap", "energy_above_hull", "formation_energy_per_atom",
                "is_stable", "volume", "nsites", "is_metal", "total_magnetization",
                "total_magnetization_normalized_vol", "total_magnetization_normalized_formula_units",
                "ordering", "efermi", "cbm", "vbm",
            ]
            q = (query or "").strip()
            kwargs: dict[str, Any] = {"fields": fields, "num_chunks": 1, "chunk_size": limit}
            if q.startswith("mp-"):
                kwargs["material_ids"] = [q]
            elif q:
                # Formula-like query or chemical system query.
                if "," in q or "-" in q:
                    chemsys = q.replace(",", "-").replace(" ", "")
                    kwargs["chemsys"] = chemsys
                else:
                    kwargs["formula"] = q
            elif elements:
                if mode == "only":
                    kwargs["elements"] = elements
                    kwargs["num_elements"] = (len(elements), len(elements))
                elif mode == "atleast":
                    kwargs["elements"] = elements
                elif mode == "formula":
                    kwargs["formula"] = "".join(elements)
            with MPRester(self.api_key) as mpr:
                docs = mpr.materials.summary.search(**kwargs)
            materials = [self._pack_summary_doc(d) for d in docs]
            if material_class != "all":
                materials = [m for m in materials if self._classify(m.get("elements", [])) == material_class]
            return {"source": "materials_project", "total": len(materials), "materials": materials[:limit]}
        except Exception as exc:
            if self.allow_mock:
                payload = self._mock_search(query, mode, elements or [], material_class, limit)
                payload["warning"] = f"MP API failed, fallback to mock: {exc}"
                return payload
            raise

    def _pack_summary_doc(self, doc: Any) -> dict:
        d = to_jsonable(doc)
        structure = getattr(doc, "structure", None)
        sites = []
        cif = None
        if structure is not None:
            try:
                cif = structure.to(fmt="cif")
                sites = [{"element": site.species_string, "frac_coords": [safe_float(v, 6) for v in site.frac_coords]} for site in structure]
            except Exception:
                pass
        symmetry = d.get("symmetry") or {}
        spacegroup = symmetry.get("symbol") if isinstance(symmetry, dict) else None
        crystal_system = symmetry.get("crystal_system") if isinstance(symmetry, dict) else None
        elements = d.get("elements") or []
        elements = [str(e) for e in elements]
        return {
            "material_id": str(d.get("material_id", "")),
            "formula_pretty": d.get("formula_pretty"),
            "elements": elements,
            "spacegroup": spacegroup,
            "crystal_system": crystal_system,
            "density": safe_float(d.get("density"), 4),
            "band_gap": safe_float(d.get("band_gap"), 4),
            "energy_above_hull": safe_float(d.get("energy_above_hull"), 5),
            "formation_energy_per_atom": safe_float(d.get("formation_energy_per_atom"), 5),
            "is_stable": d.get("is_stable"),
            "volume": safe_float(d.get("volume"), 4),
            "nsites": d.get("nsites"),
            "is_metal": d.get("is_metal"),
            "total_magnetization": safe_float(d.get("total_magnetization"), 4),
            "ordering": d.get("ordering"),
            "efermi": safe_float(d.get("efermi"), 4),
            "cbm": safe_float(d.get("cbm"), 4),
            "vbm": safe_float(d.get("vbm"), 4),
            "sites": sites,
            "cif": cif,
            "raw": d,
        }

    def get_material(self, material_id: str) -> dict:
        if not self.api_key:
            for m in MOCK_MATERIALS:
                if m["material_id"] == material_id:
                    return self._mock_detail(self._ensure_mock_cif(m))
            return self._mock_detail(self._ensure_mock_cif(MOCK_MATERIALS[0]))
        try:
            from mp_api.client import MPRester
            fields = [
                "material_id", "formula_pretty", "elements", "structure", "symmetry", "density",
                "band_gap", "energy_above_hull", "formation_energy_per_atom", "is_stable", "volume",
                "nsites", "is_metal", "total_magnetization", "total_magnetization_normalized_vol",
                "total_magnetization_normalized_formula_units", "ordering", "efermi", "cbm", "vbm",
                "dos", "bandstructure", "dielectric", "elasticity", "xas", "grain_boundaries", "origins",
            ]
            with MPRester(self.api_key) as mpr:
                docs = mpr.materials.summary.search(material_ids=[material_id], fields=fields)
            if not docs:
                return {"error": "not found"}
            base = self._pack_summary_doc(docs[0])
            return self._detail_from_base(base)
        except Exception as exc:
            if self.allow_mock:
                for m in MOCK_MATERIALS:
                    if m["material_id"] == material_id:
                        payload = self._mock_detail(self._ensure_mock_cif(m))
                        payload["warning"] = f"MP detail failed, fallback to mock: {exc}"
                        return payload
            raise

    def _mock_detail(self, m: dict) -> dict:
        return self._detail_from_base(m)

    def _detail_from_base(self, base: dict) -> dict:
        return {
            **base,
            "property_groups": {
                "Thermodynamic": {
                    "Formation energy / atom": base.get("formation_energy_per_atom"),
                    "Energy above hull": base.get("energy_above_hull"),
                    "Stable": base.get("is_stable"),
                },
                "Electronic": {
                    "Band gap": base.get("band_gap"),
                    "Metal": base.get("is_metal", base.get("band_gap", 1) == 0),
                    "CBM": base.get("cbm"),
                    "VBM": base.get("vbm"),
                    "Fermi level": base.get("efermi"),
                },
                "Magnetic": {
                    "Total magnetization": base.get("total_magnetization"),
                    "Ordering": base.get("ordering"),
                },
                "Structure": {
                    "Space group": base.get("spacegroup"),
                    "Crystal system": base.get("crystal_system"),
                    "Density": base.get("density"),
                    "Volume": base.get("volume"),
                    "Sites": base.get("nsites", len(base.get("sites", []))),
                },
                "Dielectric / Elastic / Phonon": {
                    "Dielectric object": "available if MP summary contains dielectric field",
                    "Elastic object": "available if MP summary contains elasticity field",
                    "Phonon object": "query with has_props / phonon endpoints when needed",
                }
            }
        }
