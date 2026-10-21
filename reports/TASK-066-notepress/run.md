# TASK-066-notepress 执行记录

开工时间：2026-10-21

第一步：写本文件首行后，开始清点仓库、阅读 README，再装依赖并跑测试。

## 1. 环境

- 工作区：`E:\muse-bridge\in\TASK-066-notepress`
- Python：3.11.9（命令 `python --version`，退出码 0）
- 虚拟环境：`E:\muse-bridge\work\TASK-066-notepress\venv`（不放进仓库）
- 命令：`python -m venv E:\muse-bridge\work\TASK-066-notepress\venv`，退出码 0

## 2. 安装依赖

命令（仓库根目录）：

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

耗时约 32.4 秒，退出码 0。输出摘要：

```
Successfully installed ... fastapi-0.156.8 ... httpx-0.28.1 ... pillow-13.0.0 ... pytest-9.1.1 ... python-multipart-0.0.32 ... uvicorn-0.54.0
```

版本与 requirements.txt / requirements-dev.txt 锁定值一致，无依赖冲突。

临时目录、数据库、脚本都在 `E:\muse-bridge\work\TASK-066-notepress`。测试进程已去掉 `NOTEPRESS_LLM_API_KEY`。

## 3. 自动化测试

包装脚本 `E:\muse-bridge\work\TASK-066-notepress\run_pytest.py` 设置 `TEMP`/`TMP` 到工作目录、`PYTHONDONTWRITEBYTECODE=1`，并弹出 API key 后执行：

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

工作目录：仓库根。退出码 0。输出：

```
................................                                         [100%]
tests/../fastapi/testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
32 passed, 1 warning in 11.80s
NOTEPRESS_LLM_API_KEY set: False
```

警告来自 FastAPI 自带的 TestClient 导入，32 项全部通过。

## 4. 真实流程自测

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-066-notepress\tests\live_selftest.py 8155
```

`NOTEPRESS_LLM_API_KEY set: False`。退出码 0。16 个检查点全部 PASS，末行：

```
ALL PASS · 16 个检查点
```

覆盖：health、登录、演示扩题、演示写稿、草稿、违禁词、成卡 PNG、导出 zip、状态回填。脚本自己起 uvicorn 并在结束时 terminate。

## 5. README 端口上的服务

`PORT=8000`、`NOTEPRESS_HOST=127.0.0.1`，数据库和媒体放在工作目录 `server\`。无 API key。

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-066-notepress\app.py
```

```
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
HOME_STATUS 200
HOME_CT text/html; charset=utf-8
HOME_HAS_NOTEPRESS True
HOME_HAS_TITLE True
HOME_HEAD <!DOCTYPE html> ... <title>notepress · 笔记工坊</title>
STOPPED 1
```

响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。进程已 terminate，包装脚本退出码 0。Windows 上被终止进程的返回码是 1。

## 6. 体积、字体、边界探针

`inspect_repo.py`：仓库单文件最大 `app.py` 39526 字节。无 ttf/otf/woff/woff2/ttc。本机解析字体：

```
regular C:/Windows/Fonts/msyh.ttc
bold C:/Windows/Fonts/msyhbd.ttc
```

`probe_edges.py`（无 API key）：

```
generate_800 200 body_len 1078 demo True
topic_101 400 选题超过上限 100 字（当前 101 字）
topic_100 200
draft_max 200（标题 20 字、正文 1000 字、标签 10 个）
render_max 200 count 5
card_1..5 (1080, 1440) outer_ink 0
jpeg_upload 200 cover_file 1.jpg
jpeg_cover (1080, 1440) PNG
tag_21 400
tags_11 400
```

种子选题三种语气的演示正文长度在 222–298 字，标题候选长度 11–17。

## 7. 审查结论之后的全量重跑

未改仓库源码（无 P0/P1）。再次执行：

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

退出码 0。`NOTEPRESS_LLM_API_KEY set: False`。

```
32 passed, 1 warning in 10.38s
```

警告仍是 StarletteDeprecationWarning（httpx / TestClient），无失败项。

随后 `git status --porcelain` 退出码 0，输出为空。
