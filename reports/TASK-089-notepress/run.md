# TASK-089-notepress 执行记录

开工：2026-10-22。工作目录 `E:\muse-bridge\in\TASK-089-notepress`。先审查再按清单修 P0/P1。

## 环境

命令：`python --version`

```
Python 3.11.9
```

`py -3 --version` 失败：`Unable to create process using 'E:\python.exe --version'`。后续一律用 `python` 与工作目录虚拟环境。

系统字体：`C:\Windows\Fonts\msyh.ttc` 存在，`C:\Windows\Fonts\msyhbd.ttc` 存在。仓库内单文件最大 `app.py` 41750 字节，无 ttf/otf/woff/woff2，无超过 2MB 的文件。

## 装依赖

虚拟环境：`E:\muse-bridge\work\TASK-089-notepress\venv`（不放进仓库）。

命令：

```
python -m venv E:\muse-bridge\work\TASK-089-notepress\venv
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-089-notepress\requirements.txt -r E:\muse-bridge\in\TASK-089-notepress\requirements-dev.txt
```

结果：exit 0。装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。

## 跑测试

工作目录设 `TEMP`/`TMP` 为 `E:\muse-bridge\work\TASK-089-notepress`，`PYTHONDONTWRITEBYTECODE=1`，并去掉 `NOTEPRESS_LLM_API_KEY`（当时环境里本来就没有这个变量）。

命令（cwd = 仓库根）：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

32 passed, 1 warning in 15.58s
```

exit 0。警告与改断言无关，未重跑第二次。

## 真实流程自测

命令（cwd = 仓库根，同样去掉密钥，临时目录改到工作目录）：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe tests\live_selftest.py
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

exit 0。默认端口 8155。脚本自己起进程并在结束时 terminate。

## 按 README 起服务（端口 8000）

数据库、媒体、违禁词文件放到 `E:\muse-bridge\work\TASK-089-notepress\server`，避免在仓库里生成 `notepress.db` 和 `media/`。`NOTEPRESS_LLM_API_KEY` 未设置。`NOTEPRESS_HOST=127.0.0.1`，`PORT=8000`。

命令：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe app.py
```

结果：

```
Uvicorn running on http://127.0.0.1:8000
GET /health -> 200 {"status":"ok","app_id":"notepress"}
GET / -> 200 text/html; charset=utf-8 ，正文长度 25227，含 notepress 与「笔记工坊」
响应头 x-content-type-options: nosniff ，x-frame-options: DENY
首页 HTML 中没有 http:// 或 https:// 外链
POST /api/login -> 200
GET /api/me -> 200 {"username":"admin","must_change":true,"llm_configured":false}
POST /api/topics/expand 方向「写邮件」-> 200 demo=true 候选 6 条
POST /api/generate -> 200 demo=true 标题「用AI写邮件，这样做超简单」正文 233 字
POST /api/drafts -> 200
POST /api/drafts/1/render -> 200 count=3
GET /api/drafts/1/cards/1 -> 200 PNG 59289 字节
```

检查完成后对子进程调用 terminate 并 wait。进程退出码 1，这是 Windows 上终止进程的常见结果；访问日志在终止前全部是 200。

复查：再次请求 `http://127.0.0.1:8000/health` 失败，原文 `URLError ... [WinError 10061] 由于目标计算机积极拒绝，无法连接。` `netstat -ano` 里 `127.0.0.1:8000` 只有 `TIME_WAIT`，没有 `LISTEN`。服务没有留在后台。

## 收尾重跑测试

命令与第一次相同（cwd = 仓库根，无 `NOTEPRESS_LLM_API_KEY`）：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

```
................................                                         [100%]
32 passed, 1 warning in 16.12s
```

exit 0。警告仍是 StarletteDeprecationWarning（httpx2），没有失败项。

## 额外探针（工作目录脚本，未改仓库）

- 11 个不同标签：400，`标签超过上限 10 个（当前 11 个）`。10 个 20 字标签可以保存。
- 21 字标签：400。100 字选题：200。101 字选题：400。50 字方向词：200。51 字：400。
- 演示稿三套语气在选题 0–500 字时正文都小于 1000。checklist 在 100 字选题时正文 375，500 字选题时正文 775。
- 无令牌 `POST /api/drafts`：401。`/docs` `/redoc` `/openapi.json`：404。
- 封面上传文件名 `..\..\evil.png` 实际落盘为 `covers/1.png`，仓库根下没有 `evil.png`。
- 删除违禁词 `100%`：200。
- 本机成卡字体：`C:/Windows/Fonts/msyh.ttc`，粗体 `C:/Windows/Fonts/msyhbd.ttc`。
- 20 字标题、4 条 20 字标签的文字包围盒都在 1080×1440 内。模板封面边缘的非背景像素只有强调色 `(255, 36, 66)`（顶栏），没有正文字色。
- `Image.MAX_IMAGE_PIXELS` = 89478485。
