# TASK-079-notepress 执行记录

开工时间：2026-10-22（本地执行方 Grok Build）
工作目录：E:\muse-bridge\in\TASK-079-notepress
临时目录：E:\muse-bridge\work\TASK-079-notepress
产物目录：E:\muse-bridge\out\TASK-079-notepress

状态：已开工。依赖已装上，准备跑测试。

## 1. 盘点

命令：`python --version`

```
Python 3.11.9
```

命令：`git status --porcelain`（开工时）

```
（无输出，工作区干净）
```

命令：`git rev-parse --is-inside-work-tree`

```
true
```

命令：`cmd /c "dir /s /-c"` 源码体积（不含 .git 的业务文件）：

| 文件 | 字节 |
|---|---|
| app.py | 41006 |
| static/index.html | 26567 |
| tests/test_app.py | 14343 |
| tests/test_acceptance.py | 7659 |
| README.md | 5734 |
| tests/live_selftest.py | 4745 |
| NOTES.md | 3470 |
| DECISIONS.md | 2396 |
| LICENSE | 1117 |
| data/banned_words.json | 845 |
| UPSTREAM.md | 713 |
| requirements.txt | 87 |
| .gitignore | 58 |
| requirements-dev.txt | 14 |

最大单文件 app.py = 41006 字节，低于 2MB。目录中无 ttf/otf/woff/woff2/ttc。

命令：`cmd /c "if exist C:\Windows\Fonts\msyh.ttc ..."` 与 msyhbd 分开复查

```
EXISTS msyh.ttc
EXISTS msyhbd.ttc
```

命令：`cmd /c "if defined NOTEPRESS_LLM_API_KEY (echo KEY_SET) else (echo KEY_UNSET)"`

```
KEY_UNSET
```

本机没有配置 NOTEPRESS_LLM_API_KEY。

## 2. 安装依赖

虚拟环境放在 `E:\muse-bridge\work\TASK-079-notepress\venv`，不放进仓库（仓库 .gitignore 虽忽略 .venv/，但临时文件按规定进 work 目录）。依赖文件与 README 相同。

命令：

```
python -m venv E:\muse-bridge\work\TASK-079-notepress\venv
E:\muse-bridge\work\TASK-079-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

结果：exit 0。装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。pip 末尾提示可升级 pip，未升级。

## 3. 全量 pytest

命令（在仓库根目录，临时目录指向 work，关闭字节码，清空 API key）：

```
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPYCACHEPREFIX=E:\muse-bridge\work\TASK-079-notepress\pycache
set TEMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
E:\muse-bridge\work\TASK-079-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-079-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
32 passed, 1 warning in 15.89s
```

32 项全过。警告来自依赖里的 TestClient，不是失败。

## 4. 真实流程自测

命令：

```
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set TEMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
E:\muse-bridge\work\TASK-079-notepress\venv\Scripts\python.exe tests\live_selftest.py 8155
```

输出（exit 0）：

```
  PASS health 200
  PASS 登录成功
  PASS 首次登录提示改密
  PASS 种子选题已预置
  PASS AI 扩题（演示模式）
  PASS 生成稿件（演示模式标注示例稿）
  PASS 标题合规 ≤20 字
  PASS 正文合规 ≤1000 字
  PASS 存入草稿箱
  PASS 违禁词自查命中「第一」
  PASS 生成卡片 ≥2 张
  PASS 封面卡是 PNG
  PASS 导出发布包
  PASS 发布包含编号图片+文案
  PASS 文案内容对得上
  PASS 状态流转到已发布并回填链接

ALL PASS · 16 个检查点
```

未配置 API key。脚本自己把数据库和媒体目录放进临时目录（本次 TMP/TEMP 指向 work）。

## 5. 按 README 端口起服务，查首页和健康检查，然后关掉

探针：`E:\muse-bridge\work\TASK-079-notepress\probe_server.py`（用 venv 的 Python 跑）。数据库与媒体目录设到 `work\svc`，监听 `NOTEPRESS_HOST=127.0.0.1`、`PORT=8000`。工作目录故意设成 work，而不是仓库根。

输出要点（exit 0，整段约 2.01 秒）：

```
CWD E:\muse-bridge\work\TASK-079-notepress
DB_PATH E:\muse-bridge\in\TASK-079-notepress\notepress.db
FONT_R C:/Windows/Fonts/msyh.ttc
FONT_B C:/Windows/Fonts/msyhbd.ttc
PORT8000_BEFORE False
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
INDEX_STATUS 200
INDEX_CT text/html; charset=utf-8
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
NOAUTH_DRAFTS 401 {"detail":"未登录"}
NOAUTH_CARD 401
DOCS 404
PORT8000_AFTER False
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:54304 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:54304 - "GET / HTTP/1.1" 200 OK
DB_IN_REPO False
MEDIA_IN_REPO False
DB_IN_SVC True
```

健康检查响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。进程 `terminate()` 后 8000 端口已关闭。仓库根目录没有留下 notepress.db 或 media。

## 6. 边界探针（工作目录脚本，不改仓库）

`probe_edges.py` 与 `probe_limits.py` 用 TestClient，数据库在 `work\edge` 与 `work\limits`。LLM 用进程内假函数，没有出网。

要点：

```
TOPIC100 200
TOPIC101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}
DIR51 400 {"detail":"方向词超过上限 50 字（当前 51 字）"}
STATUS_ONLY 后卡片仍在；改标题后 CARD_DIR_EXISTS False
EXPORT 200，文案含「换了标题」，封面 (1080, 1440)
UPLOAD1 200 {"cover_file":"1.png"}   （上传名是 ../../evil.png）
UPLOAD2_JPEG 200 {"cover_file":"1.jpg"}
COVER_FILES_AFTER ['1.jpg', '1.png']
UPLOAD_TOO_BIG 400 {"detail":"图片超过上限 10MB（当前 10.0MB）"}
DELETE 后卡片目录与封面文件都没了
TAGS11 400 标签超过上限 10 个（当前 11 个）
TAG21 400 标签超过上限 20 字（当前 21 字）
GEN_MIXED 200 返回了 21 个「好」的标签
EXPAND_FAIL 200 demo=true（上游函数抛错仍当演示成功）
写稿上游抛错：RuntimeError 从 app.py:362 冒出，TestClient 未转成 JSON
MIXED 200 {"titles":["正常标题"],...}   （21 字标题被丢掉，HTTP 仍是 200）
ALL_LONG 502 {"detail":"AI 返回的标题都超过 20 字，请重试"}
DIR_LEN 13，六条候选都不包含完整方向词（末字「丙」被截掉）
```

`probe_edges.py` 在写稿失败那一步 exit 1，因为异常没被应用捕获。前面的检查已经打印。

## 7. 收尾重跑

命令在仓库根目录先 `git status --porcelain`，再跑 pytest。porcelain 无输出。pytest：

```
32 passed, 1 warning in 15.35s
```

警告仍是 StarletteDeprecationWarning（httpx / TestClient）。未改仓库文件。





