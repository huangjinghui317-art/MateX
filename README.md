# MateX Web v7

一个面向 **MateX: 第五范式驱动的新物质研发搭档** 的科研工作台式 Web 原型。

## 界面特点

- 顶部磨砂半透明导航栏：Messages / API / About / User
- 左侧窄侧栏：默认只显示图标，悬浮展开英文功能名
- 深蓝低饱和侧栏，高亮色为蓝青色
- 白色、灰色主界面，无圆角，偏工作台风格
- 开场 Logo 动效
- 材料探索：搜索框、周期表筛选、材料卡片、详情页、3D/Hofmann/实时图表
- 材料设计、文献解读：暂未开放，占位页面
- 材料渲染：支持上传自有 CIF，后端按指定 Hofmann 函数逻辑渲染三视图，同时提供 3D 交互视图
- 材料评估：上传 CIF，调用 Pymatgen 解析，并尝试调用 CHGNet / MatterSim

## 运行方式

```bash
cd matex_web_v7
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MP_API_KEY="你的 Materials Project API Key"
export MATEX_ALLOW_MOCK=1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

没有 MP_API_KEY 时，系统会自动启用 demo 数据，方便先看界面。

## 后续接入点

- `backend/mp_client.py`：Materials Project API 检索与详情接口
- `backend/evaluator.py`：CIF 上传评估，CHGNet / MatterSim 接入点
- `backend/designer.py`：可替换为真实 RAG + vLLM + LoRA + 遗传迭代服务
- `static/app.js`：材料卡片、周期表、Hofmann 渲染、详情页、渲染上传、上传评估交互
- `backend/hofmann_renderer.py`：复用之前 Hofmann 脚本的 `StructureScene.from_pymatgen + BondSpec + look_along + render_mpl` 渲染逻辑


## v3 更新

- 材料检索主界面改为单列纵向布局：Hero / Search / Periodic Table / Results Cards。
- 去除 Materials Explore 中周期表与结果区的左右分栏，降低排版拥挤与错位风险。
- 保留窄侧栏、顶部磨砂导航、卡片式结果、材料详情、渲染和评估模块。


## v4 更新说明

- 材料卡片点击后进入独立的 `Material Detail` 工作区，不再把详情面板嵌入检索结果页，避免检索页被撑乱。
- 元素周期表补全镧系与锕系元素，La-Lu / Ac-Lr 保留为主表占位，实际元素在 f-block 区域可点击筛选。
- 3D 交互视图增加 Auto Rotate、Supercell、Atom Scale、Bond Radius、Background 等参数，便于查看不同晶胞倍数和渲染风格。


## v5 修复内容

- 修复 3Dmol 画布定位问题：3D 交互视图现在固定在对应容器内，不会漂到页面左上角。
- Materials Evaluation 正式安装并调用 CHGNet：requirements.txt 已加入 `chgnet>=0.3.8`，后端会调用 `CHGNet.load().predict_structure(structure)`。
- 移除元素周期表中央的 Select elements 提示遮罩。
- Materials Render 页面新增 3D Interactive View，支持 style、supercell、background、auto rotate，并保留 Hofmann 三视图。


## v6 修复内容

- Materials Render 支持上传自己的 CIF，上传后显示 `Uploaded: 文件名`，并可直接渲染 Hofmann 三视图和 3D 交互结构。
- Hofmann 渲染改为后端 Python 渲染：新增 `/api/render_hofmann`，使用之前脚本中的 `StructureScene.from_pymatgen(structure, bonds)`、`scene.view.look_along(...)`、`scene.view.zoom`、`scene.view.perspective`、`scene.render_mpl(...)` 方式生成 PNG。
- 材料详情页的 Hofmann 区域也会优先尝试使用真实 Hofmann PNG；如果本地未安装 `hofmann` 包，则自动回退到前端 SVG 投影。
- 渲染页增加 Hofmann 参数：Zoom、Perspective、Bond Scale、Bond Margin、Bond Cap、Hide Bonds。
- 渲染页增加视觉参数：Image Contrast、Image Shadow、Palette、Atom Size、Bond Width、Projection Jitter。
- 3D 渲染增加 Atom Scale、Bond Radius、Supercell、Background、Auto Rotate 等控制。
- Materials Evaluation 上传 CIF 后会立刻显示上传成功状态，避免用户不知道文件是否已经被选中。

> 注意：真实 Hofmann PNG 渲染依赖你本地已有的 `hofmann` Python 包；如果没有安装，页面不会崩溃，会自动使用 fallback projection。


## v7 修复内容

- `backend/hofmann_renderer.py` 已按你最新给出的 Hofmann 代码重写：`matplotlib.use("Agg")`、`StructureScene.from_pymatgen(structure, bonds)`、`scene.view.look_along(...)`、`scene.view.zoom`、`scene.view.perspective = 0.0`、`scene.render_mpl(str(out))`。
- BondSpec 生成逻辑改为只使用元素共价半径：`cutoff = scale * (r1 + r2)`，默认 `scale = 1.12`，不再使用旧版的 `bond_margin` 和 `bond_cap`。
- Hofmann 三视图固定为 `[100] / [010] / [001]`，默认 `zoom = 1.20`，文件命名为 `hofmann_view_100.png`、`hofmann_view_010.png`、`hofmann_view_001.png`。
- 前端 Hofmann 参数区同步简化为 `Zoom` 与 `Bond Scale`，并提示透视固定为 `0.0`，避免旧参数影响渲染效果。

## v8 update

- Material result cards now request `/api/render_hofmann` and use the same backend Hofmann PNG workflow as the Materials Render page.
- Materials Render automatically re-renders the currently selected material with the backend Hofmann renderer when the render workspace is opened.
- Mock materials now include lightweight CIF strings so the card-level Hofmann renderer can be demonstrated even without a Materials Project API key.
