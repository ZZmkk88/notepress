# notepress 验收报告

结论：无密钥、不访问大模型的演示模式可以走完「选题 → 写稿 → 草稿 → 成卡 → 导出」。pytest **34 passed**（18.90s），`live_selftest.py` **16/16**。README 默认端口 8000 被本机其他进程占用，服务改在 `PORT=8765` 拉起，`/health` 与首页正常，进程已退出。未发现 P0 / P1。本轮不改源码。

HEAD `cecf9b6`（作者 ZZmkk88）。Python 3.11.9。虚拟环境在 `E:\muse-bridge\work\TASK-101-notepress\venv`，未写入仓库。

## 本地跑通记录

依赖安装（退出码 0）：

```
E:\muse-bridge\work\TASK-101-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
Successfully installed ... fastapi-0.156.8 ... pillow-13.0.0 ... pytest-9.1.1 ... uvicorn-0.54.0
```

全量测试（未设置 `NOTEPRESS_LLM_API_KEY`，`PYTHONDONTWRITEBYTECODE=1`，临时目录改到工作目录）：

```
python -m pytest tests\ -q -p no:cacheprovider
..................................                                       [100%]
34 passed, 1 warning in 18.90s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自已安装的 `fastapi/testclient.py`，不是用例失败。

真实流程（另起 uvicorn，端口 8155，16 个检查点全过）：

```
python tests\live_selftest.py 8155
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

按 README 起服务。第一次用默认端口 8000，进程没有绑上，错误原文：

```
ERROR:    [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

当时对 `127.0.0.1:8000/health` 的 404 来自已经占着 8000 的其他进程，不是本仓库。按 README 的 `PORT` 改到 8765 后，本仓库进程日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
INFO:     127.0.0.1:64071 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:64071 - "GET / HTTP/1.1" 200 OK
```

`/health` 正文：`{"status":"ok","app_id":"notepress"}`。首页 200，长度 25242，含 `notepress` 与 `笔记工坊`。响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。同一进程登录后 `GET /api/me` 为 `{"username":"admin","must_change":true,"llm_configured":false}`，`POST /api/generate` 返回 `demo=true`，标题「用AI写周报，这样做超简单」，正文 281 字。数据库和媒体目录放在 `E:\muse-bridge\work\TASK-101-notepress\server`，避免在仓库里落下 `notepress.db`。`terminate` 之后 PID 5724 已不存在（`Get-Process -Id 5724` → `ObjectNotFound`）。8000 上的既有进程没有动。

无浏览器工具。首页与健康检查用本机 httpx（`trust_env=False`）核对；选题到导出的点击路径由 `live_selftest.py` 走同一套 API。

### 专项核对

1. 无密钥。运行前环境里没有 `NOTEPRESS_LLM_API_KEY`（脚本打印 `KEY_SET False`）。`tests/test_acceptance.py:98` `test_demo_mode_does_not_call_httpx_post` 在上述 34 通过里。`app.py:240-241` 只从该环境变量判断是否走演示模式；`app.py:247` 的密钥同样只读环境变量。源码里没有写死的 API key。测试里有假 key 字符串，见 P2-3。默认登录口令 `admin` / `admin123` 是 README.md:25 写明的本地单用户口令，`app.py:145` 用于空库播种，不是大模型密钥。

2. 体积与字体。仓库内最大源文件 `app.py` 42866 字节；无单文件超过 2MB；无 ttf/otf/woff/woff2/ttc（清点脚本末行 `OVER2MB []` / `FONTFILES []`）。本机 `find_font` 结果：`C:/Windows/Fonts/msyh.ttc` 与 `C:/Windows/Fonts/msyhbd.ttc`，与 README.md:98 一致。两条路径在磁盘上存在。找不到字体时 `app.py:455` 退回 `ImageFont.load_default()`，`test_missing_font_still_renders`（`tests/test_acceptance.py:216`）已通过。

3. 渲染可复现。固定样例在 `tests/test_acceptance.py:17-19`（标题「用AI写周报教程」、正文两段、标签 AI工具/周报）。`test_render_fixed_sample_size_and_no_overflow`（同文件 122 行起）断言：卡片文件存在、PNG 头、字节数在 500 与 2_000_000 之间、尺寸 `(1080, 1440)`、`宽*4 == 高*3`、外缘非背景像素为 0；有系统字体时标题区墨点 > 80。该用例在 34 通过之中。

4. 规格。README 与代码一致的部分：标题 20（README.md:11，`app.py:32`）、正文 1000（README.md:11，`app.py:33`）、标签最多 10 个且每个不超过 20 字（README.md:15，`app.py:35-36`）、封面 3:4 即 1080×1440、不做 9:16（README.md:13-14，`app.py:38`）。另测：11 个不同标签返回 400「标签超过上限 10 个（当前 11 个）」；21 字标签返回 400；10 个 20 字标签返回 200；100 字选题的三条演示正文长度为 375 / 327 / 315，均不超过 1000。不符项只在下面第 2 节，不在这四条规格上。

5. 溯源见第 3 节。

补充探针（工作目录脚本，未改仓库）：JPEG 封面渲染为 1080×1440；渲染后删除草稿，封面与卡片文件被清掉；删除被草稿引用的选题后 `topic_id` 变为空；未知用户登录 401；未登录访问导出/渲染/卡片/违禁词均为 401；`/media/covers/1.png` 与 `/docs` 为 404。

## README 与实际不符处

1. `README.md:71` 写 `tests/test_app.py`（25 项）+ `tests/test_acceptance.py`（7 项）共 32 项。`test_app.py` 的 25 项与文件一致。`test_acceptance.py` 实际有 9 个测试函数：88、98、122、153、173、197、216、233、255 行。多出的两条是 `test_update_null_fields_not_stored_as_none_string` 与 `test_extreme_aspect_cover_renders`。pytest 输出是 `34 passed`，不是 32。

2. `README.md:18` 写状态流转「草稿 → 待发布 → 已发布」。`app.py:939-941` 只检查状态属于 `draft` / `ready` / `published`，允许跳过和回退。`tests/live_selftest.py:107-111` 从草稿直接设为已发布并要求 200，且本次自测该检查点 PASS。实现与测试一致，README 的箭头容易读成必须按序。

以下抽查与代码一致，不列入缺陷：监听地址与 `PORT`（`app.py:1116-1117`）、数据库/媒体/违禁词默认路径（`app.py:25-28`）、LLM 默认地址与模型（`app.py:245-246`）、字体回退顺序（README.md:95-100 与 `app.py:412-420`）、演示模式不请求大模型（README.md:27、`app.py:339-340`）、上传封面只画标题（README.md:14、`app.py:559-568`）、模板封面最多 4 个标签并在放不下时换行底对齐（README.md:15-16、`app.py:583-603`）、选题 100 字与方向词 50 字（README.md:9、`app.py:34` 与 `app.py:819`、`static/index.html:111` 与 `static/index.html:118`）。`README.md:72` 的 16 个自测检查点与本次输出一致。

## 许可证与署名核查

`LICENSE:3-5` 三行版权：`Copyright 2025 xpzouying`、`Copyright (c) 2023 dreammis`、`Copyright (c) 2026 ZZmkk88`。正文是 MIT。

`UPSTREAM.md:8-11` 参考一四字段齐全：`source_url` https://github.com/xpzouying/xiaohongshu-mcp ，`source_commit` `7797fd375aba02dcd33afe143f6bee13e5870859`，`license` Apache-2.0，`attribution` `Copyright 2025 xpzouying`。

`UPSTREAM.md:15-18` 参考二四字段齐全：`source_url` https://github.com/dreammis/social-auto-upload ，`source_commit` `28bb5bc20206c26d088311633540127402e4de56`，`license` MIT，`attribution` `Copyright (c) 2023 dreammis`。

`README.md:4` 与 `UPSTREAM.md:3` 都写代码为独立实现，设计上参考同类工具。`git log -1` 为 `cecf9b6`，作者 `ZZmkk88`，与 `LICENSE:5` 的本地版权行一致。两条上游版权行与 UPSTREAM 的 attribution 逐字相同。

本任务禁止抓取外部页面，因此 **source_commit 是否仍是上游仓库上的真实提交，未核实**。`app.py` 是单文件 FastAPI 笔记工坊（选题、写稿、Pillow 成卡、SQLite），结构上不是 MCP 发布器，也不是多平台自动上传脚本；在仓库内没有看到整段搬入的上游源码。在「独立重写、LICENSE 保留上游版权行」这个前提下，MIT 正文加上两条上游版权行与 UPSTREAM 四字段是对齐的。参考一的许可证是 Apache-2.0，本仓没有另附 Apache 许可证全文；没有抄录证据，所以不把这点记成已证实的许可错误，也不改 `LICENSE` / `UPSTREAM.md`。

## 分级修复清单

### P0

无。安装、34 项测试、16 项真服务自测、8765 上的健康检查与首页均已通过。8000 绑定失败是本机端口占用，不是仓库缺陷。

### P1

无。未登录不能导出、渲染、读卡片或改违禁词（探针均为 401）。封面路径取文件名（`app.py:551`）。删除草稿会删卡片和封面文件（探针在渲染 JPEG 封面后删除，目录为空）。极端宽高比封面已有 `ImageOps.fit`（`app.py:555`）和回归测试，本次通过。

### P2

本轮额度只修 P0/P1，下列各项不改。

1. `README.md:71` 测试计数写成 7 项、共 32 项。修法：改成 `test_acceptance.py` 9 项、合计 34 项，并写上 null 字段与极端宽高比这两条。不要改测试。

2. `README.md:18` 状态箭头像必须按序。修法：改成三种状态可互相切换，建议顺序是草稿、待发布、已发布。不要改 `app.py:939-941`，自测依赖从草稿直接到已发布。

3. `tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 有 `monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")`。这是打桩用的假 key，`llm_chat` 被替换，不会出网。修法：本任务禁止改测试文件，不改。`DECISIONS.md:35-37` 已把同类项标成测试红线关闭。

4. `app.py:401` 在 `app.py:398-400` 已经拒绝超长标签之后，仍用 `tags[:MAX_TAGS]` 丢掉第 11 个及以后的 AI 标签，不报错。用户手填超过 10 个会 400（`app.py:875-876`，探针已证实）。修法：AI 返回超过 10 个时与超长标签一样返回 502。只影响配置了密钥的路径；演示模式固定 5 个标签（`app.py:335`）。

5. pytest 的 `StarletteDeprecationWarning`（建议安装 `httpx2`）。修法：不改 `requirements.txt` 的版本号。测试已通过，`DECISIONS.md:37` 已关闭此项。

6. `app.py:267-269` 把选题硬切到 10 个码位再套标题模板。种子选题「不会写周报？让 AI 先帮你打个草稿」生成的标题是「不会写周报？让 AI，这样做超简单」（探针，长度仍 ≤ 20）。修法：在标点或空格处截断，避免切在「AI」中间。演示流程仍然可用，不挡验收。

7. `README.md:111-119` 目录没有列出 `requirements.txt`、`requirements-dev.txt`、`LICENSE`、`.gitignore`。修法：补上这四行。这是遗漏，不是行为冲突。
