# TASK-055-notepress 执行记录

开工：2026-10-21 本地验收 notepress。工作目录 E:\muse-bridge\in\TASK-055-notepress。

## 1. 仓库清点

命令：`git status --porcelain`
输出：（空，工作区干净）

命令：`git log -1 --format=%H`
输出：`ebdb9b8a389e3cf49004a8d02677b318fcd19c15`

命令：`git log -1 --format=%an`
输出：`ZZmkk88`

命令：`git log -1 --format=%s`
输出：`feat(notepress): 单页前端工作台（选题库/写稿台/草稿箱/设置）`

命令：`git ls-tree -r --name-only HEAD`
输出：
```
README.md
app.py
data/banned_words.json
requirements-dev.txt
requirements.txt
static/index.html
```

命令：`python --version`
输出：`Python 3.11.9`

命令：`cmd /c dir /s /-c`（仓库内非 .git 文件）
输出摘要：
- README.md = 0 字节
- app.py = 38067
- requirements.txt = 87
- requirements-dev.txt = 14
- data/banned_words.json = 845
- static/index.html = 25969
无 ttf/otf/woff/woff2。单文件均小于 2MB。

无 LICENSE、无 UPSTREAM.md、无测试文件、无 pytest.ini。

## 2. 安装依赖

命令：
`python -m venv E:\muse-bridge\work\TASK-055-notepress\venv`
退出码：0

命令：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-055-notepress\requirements.txt -r E:\muse-bridge\in\TASK-055-notepress\requirements-dev.txt`
退出码：0
输出摘要：Successfully installed fastapi-0.156.8 uvicorn-0.54.0 python-multipart-0.0.32 httpx-0.28.1 pillow-13.0.0 pytest-9.1.1（及传递依赖 starlette、pydantic 等）。版本号按 requirements 原样安装成功，无依赖冲突。

## 3. 全量测试（修复前）

工作目录：`E:\muse-bridge\in\TASK-055-notepress`
命令：`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -m pytest -q`
退出码：1
输出：
```
no tests ran in 0.01s
```

命令：`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -m pytest --collect-only`
退出码：1
输出：
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: E:\muse-bridge\in\TASK-055-notepress
plugins: anyio-4.15.1
collected 0 items

========================= no tests collected in 0.01s =========================
```
仓库内没有测试文件。pytest 本身能启动，收集结果为 0。

## 4. 起服务并跑模拟流程（无 API key，不访问外网）

临时库与媒体目录在 `E:\muse-bridge\work\TASK-055-notepress\`。脚本 `probe_flow.py` 在导入前删除环境变量 `NOTEPRESS_LLM_API_KEY`，并把 `httpx.post` 换成会抛 `BLOCKED_NETWORK_POST` 的函数。进程内启动 uvicorn，检查后 `server.should_exit = True` 退出，未使用 taskkill。

命令：`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-055-notepress\probe_flow.py`
退出码：0
输出片段：
```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
LLM_CONFIGURED False
TITLE_LIMIT 20 BODY_LIMIT 1000 MAX_TAGS 10
CARD 1080 1440 ratio 0.75
DEMO_TITLES [('不会写周报？让 AI，这样做超简单', 17), ('不会写周报？让 AI保姆级教程', 15), ('亲测！不会写周报？让 AI真的香', 16)]
DEMO_BODY_LEN 296
DEMO_TAGS ['AI工具', '普通人用AI', '效率提升', '职场干货', 'AI教程'] N 5
DEMO_FLAG True
SERVER_STARTED True port 8000
HEALTH 200 {"status":"ok","app_id":"notepress"}
HEALTH_HEADERS {'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'referrer-policy': 'same-origin'}
INDEX 200 len 24661 has_login True ctype text/html; charset=utf-8
ME_NOAUTH 401 {"detail":"未登录"}
LOGIN 200 {"token":"sUXkWr-...(已截断)","username":"admin","must_change":true}
EXPAND 200 {"candidates":["用AI搞定写周报，小白完整教程",...],"demo":true}
GENERATE_STATUS 200
GENERATE_DEMO True title0 不会写周报？让 AI，这样做超简单 body_len 296 tags ['AI工具', '普通人用AI', '效率提升', '职场干货', 'AI教程'] hits [{'word': '第一', 'in_title': 0, 'in_body': 1}]
CREATE_DRAFT 200 {"id":1}
RENDER 200 {"cards":["/api/drafts/1/cards/1","/api/drafts/1/cards/2","/api/drafts/1/cards/3"],"count":3}
CARD_SIZE card_1.png (1080, 1440) RGB bytes 66829
CARD_SIZE card_2.png (1080, 1440) RGB bytes 152980
CARD_SIZE card_3.png (1080, 1440) RGB bytes 145759
GET_CARD1 200 image/png bytes 66829
GET_CARD1_SIZE (1080, 1440)
EXPORT 200 application/zip bytes 339012
ZIP_NAMES ['01.png', '02.png', '03.png', '文案.txt']
LONG_DRAFT 200 {"id":2}
LONG_RENDER 200 {"cards":[...],"count":2}
LONG_COVER_SIZE (1080, 1440) bg (255, 249, 245) right_edge_rows 35
TAG_LINE_LEN_CHARS 52 TAG_LINE_PX 1944.0 SAFE_WIDTH 912
TAGS11_CREATE 200 {"id":3}
TAGS11_STORED 10 ['标签0', '标签1', '标签2', '标签3', '标签4', '标签5', '标签6', '标签7', '标签8', '标签9']
TOPIC101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}
TOPIC100 200 {"id":11}
TITLE21 400 {"detail":"标题超过上限 20 字（当前 21 字）"}
CARD_NOAUTH 401
SERVER_STOPPED True
```
说明：`right_edge_rows 35` 含封面右上角装饰椭圆（画出画布后被裁切），不能单独当成文字溢出。文字溢出见下一节像素统计。全程没有触发 `BLOCKED_NETWORK_POST`。服务已退出。

## 5. 卡片像素与示例稿违禁词

命令：`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-055-notepress\probe_pixels.py`
退出码：0
输出：
```
TITLE_LEN 13
FILES ['card_1.png', 'card_2.png']
card_1.png size (1080, 1440) edge_nongb 215 tagband_past_margin 1736
card_2.png size (1080, 1440) edge_nongb 0 tagband_past_margin 0
TAG_PX 1944.0 MAX 912
TONE checklist body 296 title_lens [17, 15, 16] hits ['第一']
TONE experience body 246 title_lens [17, 15, 16] hits ['第一']
TONE pitfall body 234 title_lens [17, 15, 16] hits ['第一']
DRAFTS_NOAUTH 401
RENDER_NOAUTH 401
COVER_NOAUTH 401
```
`tagband_past_margin` 统计封面 y=1100..1359 且 x≥996（右边距 84px）的非背景像素。封面 1736，正文卡 0。标签字符串像素宽度 1944，安全宽度 912。

未单独用秒表计时。pytest 自报 0.01s。pip 安装与两次探测均在当次命令内退出码 0 返回（等待上限分别为 180s 与 90s/60s）。

## 6. 修复后复核

P1-1 命令：`...\python.exe -B E:\muse-bridge\work\TASK-055-notepress\verify_p1_1.py` 退出码 0。`SOURCE_OK`，`INDEX 200`，`SERVED_UNSAFE_EXPAND False`，`SERVED_UNSAFE_WORD False`，`SERVER_STOPPED True`。

P1-2 命令：`...\python.exe -B E:\muse-bridge\work\TASK-055-notepress\verify_p1_2.py` 退出码 0。`PAST_X1000 0`，`SHOWN_PX 910.0`，`MAX 912`，`DETERMINISTIC True`，`PASS True`。

P1-3 第一次命令同上 `verify_p1_3.py` 未进入 lifespan，异常原文 `sqlite3.OperationalError: no such table: users`。改正脚本后退出码 0。`TAGS11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}`，`TAGS10 200`，`PASS True`。

全量 pytest：
```
...\python.exe -B -m pytest --collect-only
```
退出码 1，`collected 0 items`，`no tests collected in 0.01s`。

全流程：`...\python.exe -B E:\muse-bridge\work\TASK-055-notepress\probe_final.py` 退出码 0。`HEALTH 200`，`INDEX 200`，`GENERATE 200 demo True`，`CARD 200 (1080, 1440)`，`TAGS11 400`，`SERVER_STOPPED True`，`PASS True`。

`git status --porcelain`：
```
 M app.py
 M static/index.html
?? __pycache__/
```
