# TASK-094-notepress 执行记录

开工时间：2026-10-22
工作目录：E:\muse-bridge\in\TASK-094-notepress
执行方：Grok Build（本地验收）
临时目录：E:\muse-bridge\work\TASK-094-notepress
产物目录：E:\muse-bridge\out\TASK-094-notepress

## 步骤 0：开工

已创建本文件。后续命令输出按步骤追加。

## 步骤 1：环境勘察

命令：

```
python --version
git -C E:\muse-bridge\in\TASK-094-notepress status --porcelain
git -C E:\muse-bridge\in\TASK-094-notepress rev-parse --is-inside-work-tree
python E:\muse-bridge\work\TASK-094-notepress\audit_files.py
```

输出摘要：

- `Python 3.11.9`
- `git status --porcelain` 无输出；`rev-parse` 为 `true`
- 最大源文件 `app.py` 41750 字节；`static/index.html` 26530 字节
- `.git` 对象包 39387 字节，仍小于 2MB
- 无 ttf/otf/woff/woff2
- `C:\Windows\Fonts\msyh.ttc exists=True`
- `C:\Windows\Fonts\msyhbd.ttc exists=True`
- `NOTEPRESS_LLM_API_KEY=unset`，`NOTEPRESS_HOST=unset`，`PORT=unset`，`NOTEPRESS_DB=unset`，`NOTEPRESS_FONT_PATH=unset`
- `HTTP_PROXY` / `HTTPS_PROXY` / `http_proxy` / `https_proxy` / `ALL_PROXY` 均为 SET，长度 21（值不记录）

## 步骤 2：虚拟环境与依赖

```
python -m venv E:\muse-bridge\work\TASK-094-notepress\venv
```

退出码 0。

```
venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-094-notepress\requirements.txt -r E:\muse-bridge\in\TASK-094-notepress\requirements-dev.txt
```

退出码 0。关键行：`Successfully installed ... fastapi-0.156.8 ... httpx-0.28.1 ... pillow-13.0.0 ... pytest-9.1.1 ... python-multipart-0.0.32 ... uvicorn-0.54.0`。轮子来自 pip 缓存（`Using cached`）。未执行 pip 升级。

## 步骤 3：全量 pytest（审查中）

```
venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

cwd：`E:\muse-bridge\in\TASK-094-notepress`。`TEMP`/`TMP`/`TMPDIR` 指向 work\tmp。已去掉 `NOTEPRESS_LLM_API_KEY`。`PYTHONDONTWRITEBYTECODE=1`。

```
32 passed, 1 warning in 17.10s
EXIT 0
ELAPSED_SEC 19.39
```

警告：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## 步骤 4：live_selftest

```
venv\Scripts\python.exe E:\muse-bridge\in\TASK-094-notepress\tests\live_selftest.py 8155
```

退出码 0，`ELAPSED_SEC 2.12`。16 行 `PASS`，末行 `ALL PASS · 16 个检查点`。脚本把数据库放到 TEMP（已改到 work\tmp），并 pop 掉 API 密钥。

## 步骤 5：服务 8765 与默认 8000

8765（显式 HOST/PORT，库和媒体在 work\server）：

```
PID 7392
LISTENING True
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
INDEX_STATUS 200
INDEX_CT text/html; charset=utf-8
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
STOPPED_POLL 1
ELAPSED_SEC 2.06
```

日志：`Uvicorn running on http://127.0.0.1:8765`。响应头含 nosniff、DENY、same-origin。

这次包装脚本在 `netstat` 的文本解码上报了 `UnicodeDecodeError` / `AttributeError`（Windows 输出不是 UTF-8），发生在健康检查和首页已经打印之后。服务进程已 `terminate()`，`STOPPED_POLL 1`。

默认端口（不设置 PORT 与 NOTEPRESS_HOST）：

```
LISTENING_8000 True
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 text/html; charset=utf-8 notepress True
STOPPED 1
```

日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:52130 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52130 - "GET / HTTP/1.1" 200 OK
```

关闭后再查端口：

```
python E:\muse-bridge\work\TASK-094-notepress\check_ports.py
```

`netstat -ano -p tcp` 退出码 0。过滤 `:8000`、`:8155`、`:8765` 且含 LISTEN 的行没有输出。

## 步骤 6：规格探针

```
venv\Scripts\python.exe E:\muse-bridge\work\TASK-094-notepress\probe_specs.py
venv\Scripts\python.exe E:\muse-bridge\work\TASK-094-notepress\probe_tags.py
```

字体与比例：

```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
TITLE_LIMIT 20 BODY_LIMIT 1000 MAX_TAGS 10 TAG_LIMIT 20
CARD 1080 1440 ratio_3_4 True
```

演示稿（短选题 / 100 字选题）正文字数：checklist 281 / 375，experience 233 / 327，pitfall 221 / 315。标题都是 3 条，字数在 11 到 17。标签 5 个。

限长：

```
API_PITFALL 200 body_len 219 demo True ntitles 3
TOPIC_100 200
TOPIC_101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}
TAGS_10x20 200
TAG_21 400 {"detail":"标签超过上限 20 字（当前 21 字）"}
TITLE_21 400 {"detail":"标题超过上限 20 字（当前 21 字）"}
BODY_1001 400 {"detail":"正文超过上限 1000 字（当前 1001 字）"}
DISTINCT_11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
DISTINCT_10 200
DUP_11 200
DUP_STORED ['同一个']
UPLOAD 200 {"ok":true,"cover_file":"3.png"}
UPLOAD_COVER_SIZE (1080, 1440)
```

第一次 `probe_specs.py` 因 f-string 语法错误退出码 1，未产生业务结果。改的是 work 目录里的探针脚本，已重跑成功。仓库源码未动。

## 步骤 7：收尾全量测试

与步骤 3 同一命令。

```
32 passed, 1 warning in 14.41s
EXIT 0
ELAPSED_SEC 15.50
```

同一步执行：

```
git -C E:\muse-bridge\in\TASK-094-notepress status --porcelain
```

无输出，退出码 0。

审查结论写在 review.md。未做 P0/P1 源码修改，原因写在 fix-report.md。

## 步骤 8：报告落盘后的 git status

```
git -C E:\muse-bridge\in\TASK-094-notepress status --porcelain
```

退出码 0。stdout 为空。
