# TASK-059 notepress 验收运行记录

- 开工时间：2026-10-21
- 工作目录：E:\muse-bridge\in\TASK-059-notepress-tests
- 执行方：Grok Build（本地验收）
- 状态：开工，开始盘点仓库。

## 1. 盘点（未改文件）

- 解释器：`E:\muse-bridge\env\TASK-059-notepress-tests\Scripts\python.exe` Python 3.11.9
- HEAD：`bb4e5bdb6bb9ea193d5bd308512121a3a913c9d2` 作者 ZZmkk88 \<927675399@qq.com\> 唯一提交 `docs(notepress): README、调研笔记、上游溯源、许可证与决定记录`
- `git status --porcelain` 开工时为空（干净）
- `git ls-files`：.gitignore、DECISIONS.md、LICENSE、NOTES.md、README.md、UPSTREAM.md、app.py、data/banned_words.json、requirements.txt、requirements-dev.txt、static/index.html、tests/live_selftest.py、tests/test_app.py
- 扫描脚本 `E:\muse-bridge\work\TASK-059-notepress-tests\scan_repo.py`：排除 .venv 后无 >2MB、无 ttf/otf/woff/woff2/ttc、无 __pycache__/*.pyc、无 zip/db 产物。file_count_excluding_venv=42（含 .git）
- pytest 未安装：`python -m pytest --version` → No module named pytest
- fastapi 未安装：ModuleNotFoundError

## 2. 安装依赖

命令：`python -m pip install -r requirements.txt -r requirements-dev.txt`
耗时：32.41s，退出码 0。已装 fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1。

## 3. 跑现有 pytest

命令：`python -m pytest tests\test_app.py -q --tb=short`
退出码 0。结果行：`25 passed, 1 warning in 5.97s`
警告：StarletteDeprecationWarning（fastapi testclient 建议 httpx2），不失败。
当时环境：`NOTEPRESS_LLM_API_KEY` 未设置，`NOTEPRESS_FONT_PATH` 未设置。
本机字体：`C:\Windows\Fonts\msyh.ttc` 存在（19704352 字节，在仓库外），`msyhbd.ttc` 存在。

## 4. 真实流程与服务

命令：`python tests\live_selftest.py`
退出码 0。`ALL PASS · 16 个检查点`（health、登录、扩题 demo、写稿 demo、标题≤20、正文≤1000、草稿、违禁词命中「第一」、成卡、PNG、导出 zip、文案、状态流转）。

命令：`python app.py`（后台）
输出：`Uvicorn running on http://127.0.0.1:8000`
随后用 httpx（trust_env=False）访问本机：
- GET /health → 200 `{"status":"ok","app_id":"notepress"}`
- POST /api/login admin → 200 must_change true
- GET /api/me → `llm_configured: false`
- POST /api/topics/expand `写邮件` → demo true，candidates 6
- POST /api/generate → demo true，标题「用AI写邮件，这样做超简单」，正文 284 字，标签 5
- 存草稿、违禁词自查命中「第一」「全国第一」、渲染 3 张、封面 PNG 魔数、导出 zip 含 01.png 02.png 03.png 文案.txt
服务随后已停。该次启动在仓库里留下被 .gitignore 挡住的 `notepress.db` 与 `media/`（未跟踪）。

## 5. 渲染边界探针（改代码前）

工作目录外脚本 `probe_edges.py` / `probe_render.py`：
- 短标签封面与内容卡：外缘 8px（y≥400）非背景像素 = 0，尺寸 (1080, 1440)
- 4 个 20 字标签：`textlength=2532`，bbox 右端 x=2616（画布宽 1080）；封面外缘非背景像素 = 183，采样点 (1072,1210) 颜色接近副文本色 (140,130,124)
- 内容卡即使正文 400 字，外缘像素 = 0
- 三套演示稿正文都命中违禁词「第一」（正文 222–284 字，标题均 ≤20）
- 去掉字体（find_font 返回 None）时短样例仍输出 1080×1440，外缘像素 = 0

## 6. 改代码前 git status

`git status --porcelain` 为空。
