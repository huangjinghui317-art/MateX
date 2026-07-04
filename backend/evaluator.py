# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
from pathlib import Path

from .utils import safe_float, structure_summary, to_jsonable


def evaluate_cif_text(text: str) -> dict:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "input.cif"
        path.write_text(text, encoding="utf-8", errors="ignore")
        structure = Structure.from_file(str(path))

    summary = structure_summary(structure)
    sym = {}
    try:
        sga = SpacegroupAnalyzer(structure, symprec=1e-3)
        dataset = sga.get_symmetry_dataset()
        sym = {
            "space_group_symbol": sga.get_space_group_symbol(),
            "space_group_number": sga.get_space_group_number(),
            "crystal_system": sga.get_crystal_system(),
            "point_group": sga.get_point_group_symbol(),
            "wyckoffs": list(dataset.get("wyckoffs", [])) if dataset else [],
        }
    except Exception as exc:
        sym = {"warning": str(exc)}

    result = {"structure": summary, "symmetry": sym, "chgnet": None, "mattersim": None}

    try:
        try:
            from chgnet.model import CHGNet
        except Exception:
            from chgnet.model.model import CHGNet

        model = CHGNet.load()
        pred = model.predict_structure(structure)
        # CHGNet returns a dict-like prediction containing energy, forces, stress and magmom.
        forces = pred.get("forces")
        stress = pred.get("stress")
        magmom = pred.get("magmom")
        result["chgnet"] = {
            "available": True,
            "status": "called",
            "energy_eV_per_atom": safe_float(pred.get("energy"), 6),
            "force_shape": list(getattr(forces, "shape", [])) or "array",
            "force_sample_eV_per_A": to_jsonable(forces[:5] if hasattr(forces, "__getitem__") else forces),
            "stress_GPa": to_jsonable(stress),
            "magmom_muB": to_jsonable(magmom),
            "message": "CHGNet prediction completed",
        }
    except Exception as exc:
        result["chgnet"] = {
            "available": False,
            "status": "failed",
            "message": "CHGNet 已配置为正式调用，但当前环境未安装完整依赖或模型加载失败",
            "detail": str(exc),
        }

    try:
        from pymatgen.io.ase import AseAtomsAdaptor
        from mattersim.forcefield import MatterSimCalculator
        atoms = AseAtomsAdaptor().get_atoms(structure)
        atoms.calc = MatterSimCalculator.load()
        result["mattersim"] = {
            "available": True,
            "energy_eV": safe_float(atoms.get_potential_energy(), 6),
            "forces_eV_per_A": to_jsonable(atoms.get_forces()[:5]),
            "stress": to_jsonable(atoms.get_stress()),
        }
    except Exception as exc:
        result["mattersim"] = {"available": False, "message": "MatterSim 未安装或调用失败", "detail": str(exc)}

    return result
