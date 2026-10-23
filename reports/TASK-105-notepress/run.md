# TASK-105-notepress 执行记录

开工时间：2026-10-24。工作目录 `E:\muse-bridge\in\TASK-105-notepress`。先审查再修 P0/P1。

## 0. 环境探测

命令（工作目录 `E:\muse-bridge\in\TASK-105-notepress`）：

```text
python --version
Get-ChildItem -Recurse -File | Select-Object Length, FullName
```

输出摘要：

```text
Python 3.11.9
```

单文件体积（字节）均远小于 2MB，无 ttf/otf/woff/woff2：

```text
58        .gitignore
42866     app.py
6518      DECISIONS.md
1117      LICENSE
3699      NOTES.md
6098      README.md
14        requirements-dev.txt
87        requirements.txt
713       UPSTREAM.md
845       data\banned_words.json
26545     static\index.html
4745      tests\live_selftest.py
10132     tests\test_acceptance.py
14343     tests\test_app.py
```

虚拟环境放到 `E:\muse-bridge\work\TASK-105-notepress\venv`，避免在仓库里生成 `.venv`。

## 1. 安装依赖

命令（工作目录 `E:\muse-bridge\in\TASK-105-notepress`）：

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

耗时约 61 秒，退出码 0。关键行：

```text
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.23 click-8.5.0 colorama-0.4.6 fastapi-0.156.8 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pillow-13.0.0 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 python-multipart-0.0.32 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

requirements.txt 与 requirements-dev.txt 的钉版本均能装上，无依赖冲突。

## 2. 全量 pytest（审查时）

命令（工作目录 `E:\muse-bridge\in\TASK-105-notepress`，未设置 `NOTEPRESS_LLM_API_KEY`）：

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-105-notepress\pytest-tmp
```

耗时 17.43 秒，退出码 0。输出：

```text
..................................                                       [100%]
============================== warnings summary ===============================
..\..\work\TASK-105-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-105-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 17.43s
```

收集到 34 项，不是 README 写的 32 项。警告来自依赖，不是失败。

## 3. 真实流程自测 + 8000 端口

脚本：`E:\muse-bridge\work\TASK-105-notepress\smoke.py`（临时文件，不在仓库内）。
自测默认端口是 `tests/live_selftest.py:20` 的 8155；另外按 README 在 8000 起了一次 `app.py`。
数据库、媒体、违禁词副本都放在 `E:\muse-bridge\work\TASK-105-notepress`。子进程环境里去掉了 `NOTEPRESS_LLM_API_KEY`。

命令：

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-105-notepress\smoke.py
```

live_selftest 退出码 0，耗时 3.11 秒。输出：

```text
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

8000 端口（启动约 0.68 秒后探测）：

```text
GET /health 200 {"status":"ok","app_id":"notepress"}
GET / 200 bytes=26545 ctype=text/html; charset=utf-8
home_has_notepress True
home_has_workshop True
home_has_login True
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:61182 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:61182 - "GET / HTTP/1.1" 200 OK
server_stopped exit=1
```

`server_stopped exit=1` 是探测脚本调用 `process.terminate()` 之后 Windows 上的退出码，不是启动失败。终止前两次请求都是 200，日志有 `Uvicorn running on http://127.0.0.1:8000`。进程已退出。

同一次脚本里的额外探测（无密钥，本机微软雅黑）：

```text
font_regular C:/Windows/Fonts/msyh.ttc
font_bold C:/Windows/Fonts/msyhbd.ttc
expand50 count 6 maxlen 62
draft1000 200 {"id":1}
render1000 200 ... "count":5
card 1 size=(1080, 1440) bytes=37932 outer_ink=0
card 2 size=(1080, 1440) bytes=17153 outer_ink=0
card 3 size=(1080, 1440) bytes=17249 outer_ink=0
card 4 size=(1080, 1440) bytes=16880 outer_ink=0
card 5 size=(1080, 1440) bytes=15376 outer_ink=0
upload1 200 {"ok":true,"cover_file":"1.png"}
render_upload 200 ... "count":5
reupload 200 {"ok":true,"cover_file":"1.jpg"}
delete_after_render 200 {"ok":true}
```

10 条种子选题 × 3 种语气，演示正文长度 228–295，标题都是 3 条且最长 17 字。50 字方向词扩出的选题最长 62 字，低于选题上限 100。1000 字正文 + 20 字标题 + 4 个 20 字标签渲染 5 张卡，外缘溢墨为 0。Windows 上渲染后再次上传封面并删除草稿成功，没有文件锁错误。

## 4. 收尾重跑（未改源码）

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-105-notepress\pytest-tmp2
```

```text
34 passed, 1 warning in 16.90s
```

退出码 0。

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe tests\live_selftest.py
```

```text
ALL PASS · 16 个检查点
```

退出码 0。

## 5. git status

```text
git status --porcelain
```

退出码 0，输出为空。仓库工作区没有改动。

