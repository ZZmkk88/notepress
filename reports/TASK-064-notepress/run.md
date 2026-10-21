# TASK-064-notepress 执行记录

开始时间：2026-10-21
工作目录：E:\muse-bridge\in\TASK-064-notepress
执行方：Grok Build（本地验收）

临时文件、虚拟环境、探测数据库都在 `E:\muse-bridge\work\TASK-064-notepress`。未把 `.venv`、数据库、媒体目录写进待审仓库。

## 步骤 0：开工

已创建本文件作为执行记录。后续每完成一步立刻追加命令与输出。

## 步骤 1：环境探测

命令：

```
python --version
```

输出：

```
Python 3.11.9
```

命令：

```
cmd /c dir /s /-c E:\muse-bridge\in\TASK-064-notepress
```

工作区文件（不含 .git）体积：最大 `app.py` 38913 字节，`static\index.html` 26567，`tests\test_app.py` 14343，其余更小。未见 ttf/otf/woff/woff2，未见渲染缓存。全部单文件远小于 2MB。

字体：

```
cmd /c "if exist C:\Windows\Fonts\msyh.ttc (echo MSYH_YES) else (echo MSYH_NO)"
→ MSYH_YES

cmd /c "if exist C:\Windows\Fonts\msyhbd.ttc (echo MSYHBD_YES) else (echo MSYHBD_NO)"
→ MSYHBD_YES
```

## 步骤 2：安装依赖

虚拟环境放在工作目录，等价于 README 的 `python -m venv` + `pip install -r requirements.txt`，并加装 `requirements-dev.txt`。

命令：

```
python -m venv E:\muse-bridge\work\TASK-064-notepress\venv
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-064-notepress\requirements.txt -r E:\muse-bridge\in\TASK-064-notepress\requirements-dev.txt
```

输出摘要（exit 0）：

```
Successfully installed ... fastapi-0.156.8 ... uvicorn-0.54.0 ... python-multipart-0.0.32 ... httpx-0.28.1 ... pillow-13.0.0 ... pytest-9.1.1 ...
```

版本与 requirements 钉死的版本一致，无依赖冲突。墙钟未另记。

## 步骤 3：全量 pytest（无密钥、外网代理指向无效端口）

命令：

```
set TEMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set http_proxy=http://127.0.0.1:9
set https_proxy=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-tmp
```

输出（exit 0，pytest 自报 11.10s）：

```
PYTEST_START 22:56:36.99
.........................                                                [100%]
============================== warnings summary ===============================
..\..\work\TASK-064-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 11.10s
PYTEST_END 22:56:36.99
```

`%TIME%` 在同一条 cmd 里被提前展开，开始/结束时钟相同；耗时以 pytest 的 11.10s 为准。警告来自 FastAPI 自带 TestClient，不导致失败。25 项与 README 声明一致。

## 步骤 4：真实流程自测（无密钥）

命令：

```
set TEMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe tests\live_selftest.py 8155
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

脚本自己拉起 uvicorn，检查完后 `terminate`。16 个检查点与 README 一致。数据库在系统临时目录变量指向的 work\tmp 下。墙钟未另记。

## 步骤 5：按 README 起服务，查首页和健康检查，然后关掉

脚本：`E:\muse-bridge\work\TASK-064-notepress\smoke_server.py`
环境：`NOTEPRESS_HOST=127.0.0.1`，`PORT=8000`，`NOTEPRESS_DB` 与 `NOTEPRESS_MEDIA` 指向 work 目录，`NOTEPRESS_LLM_API_KEY` 已去掉，`HTTP(S)_PROXY=http://127.0.0.1:9`。进程命令为 `venv\Scripts\python.exe app.py`。

输出（脚本 exit 0）：

```
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 len 25259
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
INDEX_SNIP <!DOCTYPE html> <html lang="zh-CN"> ... <title>notepress · 笔记工坊</title> ...
EXIT 1
SERVER_LOG_BEGIN
INFO:     Started server process [4280]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:59472 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:59472 - "GET / HTTP/1.1" 200 OK
SERVER_LOG_END
```

`EXIT 1` 是主动 `terminate` 后 uvicorn 的退出码，不是启动失败。随后：

```
netstat -ano | findstr :8000
  TCP    127.0.0.1:59472        127.0.0.1:8000         TIME_WAIT       0
```

没有 LISTENING。8000 上的服务已关。仓库目录下没有 `*.db`，也没有 `media`。

## 步骤 6：渲染边界、旧图导出、删除残留（修复前）

命令：

```
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-064-notepress\probe.py
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-064-notepress\probe_topic.py
```

`probe.py` 关键输出（exit 0）：

```
FONT_REG C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
LLM False
DEMO 6 titles [13, 11, 12] body 284 over False
CREATE_MAX 200 {"id":1}
RENDER 200 {'cards': ['/api/drafts/1/cards/1', ...], 'count': 5}
TEXT_DRAW_COUNT 57
OVERFLOW_COUNT 0
BBOX_EXTENTS minx 84 miny 94 maxx 994 maxy 1374
CARD_SIZE (1080, 1440) MODE RGB
TITLE_REGION_NONEMPTY 108928
UPDATE 200
STALE_PNG_SAME True
EXPORT_HAS_NEW_TITLE True
EXPORT_HAS_OLD_TITLE False
DELETE 200
AFTER_DELETE_DIR True
GET_CARD_AFTER_DELETE 200 46516
TAGS_11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
```

`probe_topic.py` 关键输出（exit 0）：

```
checklist 100 body 378 over False
checklist 722 body 1000 over False
checklist 800 body 1078 over True
experience 800 body 1028 over True
pitfall 800 body 1016 over True
```

样例是标题 20 个「测」、正文 1000 字、10 个标签，三套绘制全部落在 1080×1440 内。改标题后导出的 `01.png` 与旧图哈希相同，`文案.txt` 已是新标题。删除草稿后卡片接口仍返回 200。

## 步骤 7：按清单修 P1 并复测

只改了 `app.py`。每条修完都重跑 `tests\test_app.py`，并加一条针对该缺陷的探测脚本（脚本在 work 目录，不在仓库里）。明细和原始输出见 `fix-report.md`。

- P1-1 后：`25 passed, 1 warning in 10.14s`；`PNG_CHANGED True`，`TEXT_NEW True`，`CARD_CLEARED True`。
- P1-2 后：`25 passed, 1 warning in 10.37s`；删除后 `AFTER_CARD False AFTER_COVER False`，孤儿文件下载 `404 草稿不存在`。
- P1-3 后：`25 passed, 1 warning in 10.54s`；超限 `400` 且 detail 为「图片超过上限 10MB（当前 10.0MB）」；正好 10MB 的非图片返回「这不是一张能打开的图片」。

三条都落地后的全量重跑（无密钥，代理 `http://127.0.0.1:9`，live 端口 8156）：

```
25 passed, 1 warning in 10.27s
ALL PASS · 16 个检查点
```

收尾：

```
git status --porcelain
 M app.py
```
