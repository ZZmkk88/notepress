# TASK-075-notepress 执行记录

开工时间：2026-10-22（本地）
工作目录：E:\muse-bridge\in\TASK-075-notepress
角色：本地验收（Grok Build），先审查再修 P0/P1。

## 步骤 0 · 环境与仓库盘点

命令：
```
python --version
git status --porcelain
Get-ChildItem -Force -Recurse -File | Select-Object Length, FullName
python -c "import os; print('msyh', os.path.exists(r'C:\Windows\Fonts\msyh.ttc')); print('msyhbd', os.path.exists(r'C:\Windows\Fonts\msyhbd.ttc')); print('key', bool(os.environ.get('NOTEPRESS_LLM_API_KEY','').strip()))"
```

输出摘要：
- Python 3.11.9
- git status --porcelain 无输出（工作区干净）
- 最大源文件 app.py 41006 字节、static/index.html 26567 字节，均远小于 2MB
- 仓库内无 ttf/otf/woff/woff2/ttc/png/jpg/zip/db
- 系统字体 C:\Windows\Fonts\msyh.ttc 与 msyhbd.ttc 均存在
- NOTEPRESS_LLM_API_KEY 未设置

## 步骤 1 · 安装依赖

venv 放在仓库外，避免把 `.venv` 写进待审仓库：
`E:\muse-bridge\work\TASK-075-notepress\venv`

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-075-notepress\requirements.txt -r E:\muse-bridge\in\TASK-075-notepress\requirements-dev.txt
```

结果：exit 0。已安装 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1（以及传递依赖 starlette、pydantic 等）。pip 提示可升级 24.0 → 26.2.2，未执行升级。

## 步骤 2 · 全量 pytest（审查阶段）

工作目录：E:\muse-bridge\in\TASK-075-notepress
未设置 NOTEPRESS_LLM_API_KEY。临时目录用 `--basetemp` 指到任务工作目录。`-B` 避免在仓库写 `__pycache__`。

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-075-notepress\pytest-tmp
```

输出：
```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-075-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.14s
```

exit 0。32 项全部通过。警告来自 Starlette 对 TestClient 的弃用提示，不是失败。

## 步骤 3 · 真实流程自测（16 个检查点）

脚本把 TEMP/TMP 设到 E:\muse-bridge\work\TASK-075-notepress，再跑 tests\live_selftest.py，端口 18765。未配置 API key。

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 E:\muse-bridge\work\TASK-075-notepress\run_live.py
```

输出：
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

exit 0。

## 步骤 4 · 起真实服务，检查健康与首页，然后关掉

数据库、媒体、违禁词都放在 E:\muse-bridge\work\TASK-075-notepress\server。监听 127.0.0.1:18766。未配置 API key。用 httpx（trust_env=False）请求，然后 proc.terminate()。未使用 curl / wget / taskkill。

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 E:\muse-bridge\work\TASK-075-notepress\run_server.py
```

输出：
```
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
HEALTH_CT application/json
HEALTH_HDR x-content-type-options=nosniff
HEALTH_HDR x-frame-options=DENY
HEALTH_HDR referrer-policy=same-origin
HEALTH_HDR server=uvicorn
INDEX_STATUS 200
INDEX_CT text/html; charset=utf-8
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
INDEX_LEN 25259
DOCS_STATUS 404
SERVER_EXIT 1
```

首页片段含 `<title>notepress · 笔记工坊</title>`。SERVER_EXIT 1 是 Windows 上主动 terminate 子进程的退出码，检查发生在退出之前。服务已停。

## 步骤 5 · 边界探针（不改仓库）

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 E:\muse-bridge\work\TASK-075-notepress\probe_edges.py
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 E:\muse-bridge\work\TASK-075-notepress\probe_500.py
git status --porcelain
```

探针输出片段：
```
DEMO_BODY_LEN 284
DEMO_HITS ['第一']
DEMO_HAS_STEP True
LONG_TOPIC_STATUS 200 BODY_LEN 1078
TOPIC_100 200 {"id":11}
TOPIC_101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}
TOPIC_120 400 {"detail":"选题超过上限 100 字（当前 120 字）"}
sqlite3.IntegrityError: FOREIGN KEY constraint failed
  File "...\app.py", line 868, in create_draft
PATH_JOIN C:\Windows\win.ini
STATUS 500
CT text/plain; charset=utf-8
BODY Internal Server Error
```

`git status --porcelain` 无输出，仓库未被测试或探针改脏。

## 步骤 6 · 端口已关闭

命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 E:\muse-bridge\work\TASK-075-notepress\probe_port.py
```

输出：
```
18765 CLOSED TimeoutError
18766 CLOSED TimeoutError
8000 CLOSED TimeoutError
```

exit 0。自测端口、验收端口和 README 默认端口都没有在监听。

## 步骤 7 · 清单确认后重跑全量测试

未改仓库源码。命令：
```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-075-notepress\pytest-tmp-final
```

输出：
```
32 passed, 1 warning in 15.52s
```

exit 0。警告仍是 Starlette TestClient / httpx2 弃用提示。

## 步骤 8 · 收尾 git status

命令：
```
git status --porcelain
```

标准输出为空，exit 0。报告写在 `E:\muse-bridge\out\TASK-075-notepress\`，没有写入待审仓库。

