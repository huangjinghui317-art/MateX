# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import random


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def run_design_workflow(payload: dict) -> dict:
    """A replaceable design workflow stub: retrieval -> perturb -> reshape -> GA score."""
    target = payload.get("target", {}) or {}
    query = str(payload.get("base_formula") or "Auto") + str(target) + str(payload.get("constraints") or "")
    random.seed(_seed(query))
    k = max(1, min(int(payload.get("k", 6)), 20))
    steps = [
        {"name": "RAG Retrieval", "desc": "召回与目标约束相近的结构先验", "status": "done"},
        {"name": "Local Perturbation", "desc": "在元素占位、晶格尺度和局部坐标上生成扰动", "status": "done"},
        {"name": "LLM Reshape", "desc": "使用结构编辑 Prompt 对扰动结构重塑", "status": "done"},
        {"name": "Genetic Iteration", "desc": "按多目标评分保留高分候选并继续变异", "status": "done"},
        {"name": "Post-filter", "desc": "格式校验、稳定性预筛和重复结构去除", "status": "done"},
    ]
    formulas = ["BaTiO3", "LiFePO4", "SrTiO3", "Fe3O4", "GaN", "ZnO", "NaTaO3", "CaZrO3"]
    candidates = []
    for i in range(k):
        score = round(0.72 + random.random() * 0.25, 4)
        candidates.append({
            "rank": i + 1,
            "formula": formulas[i % len(formulas)],
            "edit_action": random.choice(["Wyckoff-site shift", "lattice rescale", "cation substitution", "local coordinate reshape"]),
            "predicted_band_gap": round(float(target.get("bandgap", 2.0)) + random.uniform(-0.35, 0.35), 3),
            "predicted_bulk_modulus": round(float(target.get("bulk", 120.0)) + random.uniform(-18, 18), 2),
            "predicted_density": round(float(target.get("density", 5.0)) + random.uniform(-0.6, 0.6), 3),
            "score": score,
            "risk": random.choice(["low", "medium", "needs DFT"]),
        })
    return {"steps": steps, "candidates": candidates, "note": "Replace this stub with real vLLM + LoRA + evaluator service."}
