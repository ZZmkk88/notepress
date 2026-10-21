# TASK-082-notepress 执行记录

开工: 2026-10-22 本地验收 notepress。先读仓库结构与 README，再装依赖、跑测试、起服务。

虚拟环境与临时文件：`E:\muse-bridge\work\TASK-082-notepress`。仓库：`E:\muse-bridge\in\TASK-082-notepress`。

## 步骤 0 · 环境与仓库体积

命令：

```
python --version
python E:\muse-bridge\work\TASK-082-notepress\audit_env.py
git -C E:\muse-bridge\in\TASK-082-notepress status --porcelain
```

输出摘要：

- `Python 3.11.9`
- `KEY_SET False`（`NOTEPRESS_LLM_API_KEY` 未设置）
- `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` = `http://127.0.0.1:7890`
- 字体：`msyh.ttc` 19704352 字节，`msyhbd.ttc` 16883552 字节；无 `msyh.ttf`
- 仓库 14 个文件（不含 `.git`），合计 108754 字节。无单文件超过 2MB。无 ttf/otf/woff/woff2
- `git status --porcelain` 空，退出码 0

文件字节：`.gitignore` 58，`app.py` 41006，`DECISIONS.md` 2396，`LICENSE` 1117，`NOTES.md` 3470，`README.md` 5734，`requirements-dev.txt` 14，`requirements.txt` 87，`UPSTREAM.md` 713，`data/banned_words.json` 845，`static/index.html` 26567，`tests/live_selftest.py` 4745，`tests/test_acceptance.py` 7659，`tests/test_app.py` 14343。

## 步骤 1 · 安装依赖

```
python -m venv E:\muse-bridge\work\TASK-082-notepress\venv
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-082-notepress\requirements.txt -r E:\muse-bridge\in\TASK-082-notepress\requirements-dev.txt
```

venv 创建退出码 0。pip 退出码 0。摘要：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.19 click-8.5.0 colorama-0.4.6 fastapi-0.156.8 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pillow-13.0.0 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 python-multipart-0.0.32 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

## 步骤 2 · pytest（审查前）

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

工作目录仓库根。环境去掉 `NOTEPRESS_LLM_API_KEY`，`TMP`/`TEMP` 指向工作目录，`PYTHONDONTWRITEBYTECODE=1`。

```
................................                                         [100%]
32 passed, 1 warning in 15.30s
```

退出码 0。耗时 16.31 秒。警告：

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## 步骤 3 · 真实流程自测

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-082-notepress\tests\live_selftest.py
```

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

退出码 0。耗时 2.08 秒。

## 步骤 4 · 按 README 起服务并关闭

数据库、媒体、违禁词副本放在 `E:\muse-bridge\work\TASK-082-notepress\smoke-run`。`NOTEPRESS_HOST=127.0.0.1`，`PORT=8000`，无 API key。

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-082-notepress\app.py
```

日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:57788 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:57788 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:57788 - "GET / HTTP/1.1" 200 OK
```

`/health`：200 `{"status":"ok","app_id":"notepress"}`

`/`：200 `text/html; charset=utf-8`，长度 25259，含 `notepress` 与 `笔记工坊`。

响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。Date 头：`Wed, 21 Oct 2026 16:41:42 GMT`。

`terminate()` 返回码 1。`tasklist /FI "PID eq 30952"` 无匹配进程。之后 `GET /health` 为 404 `{"detail":"Not Found"}`（另一个 uvicorn，不是 notepress）。耗时 4.29 秒。

## 步骤 5 · 探针

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-082-notepress\probe.py
```

```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
DEMO_TITLES ['用AI写周报，这样做超简单', '用AI写周报保姆级教程', '亲测！用AI写周报真的香'] [13, 11, 12]
DEMO_BODY_LEN 284 DEMO True
TONE checklist body 301 max_title 17
TONE experience body 251 max_title 17
TONE pitfall body 239 max_title 17
UNKNOWN_USER 401
TOPIC_100 200
TOPIC_101 400 选题超过上限 100 字（当前 101 字）
TAG_21 400 标签超过上限 20 字（当前 21 字）
NULL_URL_PUT 200
URL_AFTER_NULL 'None'
RENDER_COUNT 2 PNG_BYTES 40834 BYTE_IDENTICAL True
SIZE (1080, 1440)
TITLE_INK 29067
```

## 步骤 6 · 全量测试（收尾重跑）

与步骤 2 同一条命令。

```
32 passed, 1 warning in 15.27s
```

退出码 0。耗时 16.16 秒。没有失败。

## 步骤 7 · git status

```
git -C E:\muse-bridge\in\TASK-082-notepress status --porcelain
```

输出为空，退出码 0。仓库源码未改。
