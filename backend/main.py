# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .designer import run_design_workflow
from .evaluator import evaluate_cif_text
from .hofmann_renderer import render_hofmann_from_cif
from .mp_client import MPClient

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"

app = FastAPI(title="MateX", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
mp_client = MPClient()


class SearchRequest(BaseModel):
    query: str = ""
    mode: str = "formula"  # only / atleast / formula
    elements: list[str] = Field(default_factory=list)
    material_class: str = "all"
    limit: int = 24


class DesignRequest(BaseModel):
    base_formula: str = ""
    constraints: str = ""
    k: int = 6
    target: dict = Field(default_factory=dict)


class HofmannRenderRequest(BaseModel):
    cif_text: str
    zoom: float = 1.20
    perspective: float = 0.0
    bond_scale: float = 1.12
    bond_margin: float = 0.20
    bond_cap: float = 3.20
    no_bonds: bool = False


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "name": "MateX", "mp_api_enabled": mp_client.enabled()}


@app.get("/api/periodic_table")
def periodic_table() -> dict:
    return mp_client.periodic_table()


@app.post("/api/search_mp")
def search_mp(req: SearchRequest) -> dict:
    return mp_client.search(req.query, req.mode, req.elements, req.material_class, req.limit)


@app.get("/api/material/{material_id}")
def get_material(material_id: str) -> dict:
    return mp_client.get_material(material_id)


@app.post("/api/design")
def design(req: DesignRequest) -> dict:
    return run_design_workflow(req.model_dump())



@app.post("/api/render_hofmann")
def render_hofmann(req: HofmannRenderRequest) -> dict:
    try:
        return render_hofmann_from_cif(req.cif_text, STATIC_DIR / "generated" / "hofmann", req.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Hofmann 渲染失败：{exc}") from exc

@app.post("/api/evaluate_cif")
async def evaluate_cif(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith((".cif", ".txt")):
        raise HTTPException(status_code=400, detail="请上传 .cif 文件。")
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    try:
        return evaluate_cif_text(text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CIF 解析或评估失败：{exc}") from exc
