# notepress 验收报告

结论：无 API key、未抓取外网页面的条件下，本机可以按 README 把服务跑通。pytest 32 项通过，真实流程自测 16 个检查点通过，`127.0.0.1:18766` 的 `/health` 与首页均为 200，检查后进程已退出。没有 P0。没有要改代码的 P1。规格和健壮性上有 P2，按本次边界不改。

运行环境：Python 3.11.9；venv 在 `E:\muse-bridge\work\TASK-075-notepress\venv`；`NOTEPRESS_LLM_API_KEY` 未设置。依赖按 `requirements.txt` 与 `requirements-dev.txt` 的锁定版本安装成功（fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1）。

## 本地跑通记录

### 安装

```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-075-notepress\requirements.txt -r E:\muse-bridge\in\TASK-075-notepress\requirements-dev.txt
```

exit 0。venv 放在仓库外，避免把 `.venv` 写进待审目录。

### 自动化测试

```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-075-notepress\pytest-tmp
```

```
32 passed, 1 warning in 15.14s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自 Starlette 的 `testclient.py`，32 项断言都过了。清单确认后又重跑一次：`32 passed, 1 warning in 15.52s`（见 fix-report.md）。

`tests/test_app.py` 中 `def test_` 25 个，`tests/test_acceptance.py` 中 7 个，与 README.md:66 的「25 + 7 = 32」一致。

### 真实流程自测

`run_live.py` 把 TEMP/TMP 指到 `E:\muse-bridge\work\TASK-075-notepress`，执行 `tests\live_selftest.py`，端口 18765，并去掉 `NOTEPRESS_LLM_API_KEY`。

```
ALL PASS · 16 个检查点
```

16 行均为 `PASS`：health、登录、首次改密提示、种子选题、演示扩题、演示写稿、标题 ≤20、正文 ≤1000、存草稿、违禁词「第一」、成卡 ≥2、封面 PNG、导出 zip、编号图片加文案、文案内容、已发布回填。与 README.md:67 的 16 个检查点一致。

### 真实服务

`run_server.py` 在 `127.0.0.1:18766` 启动 `app.py`。数据库、媒体、违禁词都在 `E:\muse-bridge\work\TASK-075-notepress\server`。请求用 httpx，`trust_env=False`。

```
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
INDEX_STATUS 200
INDEX_CT text/html; charset=utf-8
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
DOCS_STATUS 404
```

响应头含 `x-content-type-options=nosniff`、`x-frame-options=DENY`、`referrer-policy=same-origin`。首页片段含 `<title>notepress · 笔记工坊</title>`。随后 `proc.terminate()`，子进程退出码 1（Windows 上主动结束进程的结果）。复查 18765、18766、8000 均为 `CLOSED TimeoutError`。

## README 与实际不符处

下列几条对不上。抽查过且与代码一致的，不记入本清单：默认 `127.0.0.1:8000`（app.py:1075-1077）、草稿标题 20 / 正文 1000（app.py:32-33、app.py:685-689）、标签落库最多 10 个且每个不超过 20 字（app.py:35-36、app.py:845-849）、卡片 1080×1440（app.py:38）、字体回退链（app.py:388-396 与 README.md:90-96）、测试数量与 16 个检查点（见上）。

1. README.md:11 写「标题 20 字、正文 1000 字按平台规矩硬校验，超限明确报错不截断」。演示模式在 app.py:351-352 直接 `return demo_generate(...)`，正文用完整选题拼进模板（app.py:298）。实测选题 800 个「题」时，`POST /api/generate` 返回 200，正文长度 1078。同一函数的模型分支在 app.py:374-375 会对超限正文返回 502。落库路径仍会拒绝：`validate_title_body`（app.py:685-689）对超限草稿返回 400。
2. README.md:11 的「超限明确报错」也盖到标题。模型标题在 app.py:368 被滤成「不超过 20 字的那些」；只要还剩至少一条，接口就 200，超长的那几条被丢掉，文本没有被裁成 20 字。全部超长才在 app.py:369-370 返回 502。`tests/test_app.py:193` 只锁住「全部超长 → 502」。
3. README.md:14 写「话题标签最多 10 个，每个不超过 20 字」。保存草稿的 `_clean_tags`（app.py:845-849）会拒绝。模型生成只做 `tags[:MAX_TAGS]`（app.py:376-377），不检查单条长度。成卡之前必须先过保存，所以卡片路径本身有闸；`/api/generate` 的返回值可以先带上超长标签。
4. README.md:12、README.md:26 称「演示模式」。界面徽章是「示例模式」（static/index.html:295）。同一状态两套说法。

## 许可证与署名核查

UPSTREAM.md 写了两条参考，四字段都在：

| 条目 | source_url | source_commit | license | attribution |
|---|---|---|---|---|
| 参考一 UPSTREAM.md:8-11 | https://github.com/xpzouying/xiaohongshu-mcp | 7797fd375aba02dcd33afe143f6bee13e5870859 | Apache-2.0 | Copyright 2025 xpzouying |
| 参考二 UPSTREAM.md:15-18 | https://github.com/dreammis/social-auto-upload | 28bb5bc20206c26d088311633540127402e4de56 | MIT | Copyright (c) 2023 dreammis |

LICENSE 正文是 MIT。版权行三条（LICENSE:3-5）：`Copyright 2025 xpzouying`、`Copyright (c) 2023 dreammis`、`Copyright (c) 2026 ZZmkk88`。前两行与 UPSTREAM 的 attribution 一致。`ZZmkk88` 是本仓版权行，UPSTREAM 只要求写上游，不缺字段。

README.md:4 与 UPSTREAM.md:3 都写代码为独立实现 / 独立重写。独立实现与「把上游作者写进本仓 MIT 版权块」可以同时成立（只保留署名、不把上游代码并进来），本次没有外证能证明哪一句是假的。参考一的许可证是 Apache-2.0，仓库里没有 Apache-2.0 全文或 NOTICE。若只是设计参考、没有复制代码，缺 Apache 全文说得通；若实际复制了 Apache-2.0 代码，仅有版权行不够。按任务约束，没有联网核对 `source_commit`，也没有对照上游树，**source_commit 与「是否复制代码」均未核实**。LICENSE 与 UPSTREAM 的事实性声明本次不改。

## 分级修复清单

### P0

无。安装、32 项测试、16 个检查点、健康检查和首页都跑通。

### P1

无。抽查过的安全面没有达到「要改代码」的程度，依据如下。

- 密钥只从环境变量读：app.py:236-242。仓库源码里没有写死的真实 key。`NOTEPRESS_LLM_API_KEY` 本次未设置。
- 草稿、选题、导出、上传、违禁词接口都带 `get_current_user`。`/docs`、`/redoc`、`/openapi.json` 关闭（实测 `/docs` 为 404）。
- 默认口令 `admin` / `admin123` 写在 README.md:24，并且 DECISIONS.md:3-5（D-1）规定只提示、不强制改密。这是既定行为，不改。
- 不存在的 `topic_id` 会 500，但响应正文是 `Internal Server Error`，没有把 SQL 或路径回给客户端（见 P2-5）。事务在异常时回滚（app.py:74-80），没有半条草稿留下。
- 封面路径拼接有绝对路径替换问题（见 P2-6）。上传接口只把 `cover_file` 写成 `{草稿id}.png` 或 `{草稿id}.jpg`（app.py:985-994），当前请求到不了任意路径。

### P2

1. P2-1 演示模式正文可以超过 1000 字仍返回 200。位置：app.py:351-352（拼接在 app.py:298）。修法：返回前若正文长度大于 `BODY_LIMIT`，用与 app.py:688 相同的口径返回 400，写明上限和当前字数，不截断正文。
2. P2-2 模型标题只有一部分超长时被静默丢掉，接口仍 200。位置：app.py:368-370。修法：只要有一条标题超过 `TITLE_LIMIT` 就返回 502，不要滤掉后继续成功。
3. P2-3 模型返回的单个标签不校验 20 字。位置：app.py:376-377。修法：超过 `TAG_LIMIT` 的标签直接 502，或在返回前去掉并在响应里说明。
4. P2-4 选题输入框 `maxlength="120"`，接口上限是 100。实测 100 字返回 200，101 字与 120 字返回 400，文案为「选题超过上限 100 字」。位置：static/index.html:111，app.py:34，app.py:768-769。修法：把 `maxlength` 改成 100。
5. P2-5 草稿带上不存在的 `topic_id`（实测 99999）抛出 `sqlite3.IntegrityError: FOREIGN KEY constraint failed`（app.py:868），客户端收到 500 和纯文本 `Internal Server Error`。位置：app.py:867-873。修法：插入前确认选题存在，不存在则 400。
6. P2-6 `render_cards` 用 `MEDIA_DIR / "covers" / draft["cover_file"]` 拼路径（app.py:521）。实测 `Path(r"E:\media") / "covers" / r"C:\Windows\win.ini"` 的结果是 `C:\Windows\win.ini`。删除封面时已经取 basename（app.py:490）。修法：渲染处同样只取 `Path(cover_file).name`。当前上传写不进绝对路径，所以不升为 P1。
7. P2-7 干货清单模板含「第一步」（app.py:301），词表含「第一」（data/banned_words.json:1）。实测选题「用AI写周报」、语气 checklist：正文 284 字，`banned_hits` 为 `['第一']`，正文里有「第一步」。匹配是子串（app.py:225-226）。修法：保持子串匹配，因为 `tests/test_app.py:270-271` 要求「全国第一」命中「第一」。若只想去掉示例稿误报，改模板用词，避开「第一」。
8. P2-8 界面写「示例模式」，README 写「演示模式」。位置：static/index.html:295，README.md:12。修法：界面改成「演示模式」。属于文案，本次不动。
9. P2-9 NOTES.md:22 写运行时依赖只有 FastAPI、uvicorn、httpx、Pillow 四个包。requirements.txt:3 还有 `python-multipart==0.0.32`（封面上传需要）。修法：把 NOTES 改成与 requirements.txt 一致的五个包。
10. P2-10 测试里写死假 key `sk-test-not-real`。位置：tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208。修法：改成不会被认成 key 的测试开关。禁止改测试文件，修不动。这三处都先 `monkeypatch` 了 `llm_chat`，字符串不会发到网络。
11. P2-11 全量测试有一条 Starlette 弃用警告，提示 TestClient 改用 httpx2。修法：现在测试能过，不是依赖冲突。禁止为这条去改 requirements 里的版本号。

## 专项验收

1. 无密钥跑通：本次环境没有 `NOTEPRESS_LLM_API_KEY`。pytest 32 项通过，其中 `tests/test_acceptance.py:98` 断言演示模式不调用 `httpx.post`。live_selftest 16 个检查点通过，覆盖选题、写稿、草稿、成卡、导出。真实密钥只在 app.py:236-242 从环境变量读取。源码没有写死的 key。测试里有假 key，见 P2-10，修不动。
2. 体积与字体：`Get-ChildItem -Force -Recurse -File` 列举到的最大文件是 app.py，41006 字节；static/index.html 26567 字节。没有 ttf、otf、woff、woff2、ttc，也没有 png、jpg、zip、db。成卡字体链在 README.md:88-99，与 app.py:388-425 一致：环境变量、Noto Sans CJK、文泉驿正黑、微软雅黑、苹方、华文黑体，都没有则 `ImageFont.load_default()`。本机 `C:\Windows\Fonts\msyh.ttc` 与 `msyhbd.ttc` 存在。`test_missing_font_still_renders` 与固定样例的墨点断言都在 32 项通过里。
3. 渲染可复现：`tests/test_acceptance.py:122` 的 `test_render_fixed_sample_size_and_no_overflow` 使用固定标题「用AI写周报教程」、固定正文和标签（test_acceptance.py:17-19）。`_open_card`（test_acceptance.py:74-85）断言 PNG 文件存在、大小在 500 字节到 2MB 之间、尺寸 1080×1440、外缘无多余墨点。有系统字体时还断言标题区有墨点（test_acceptance.py:148-150）。该项包含在已通过的 32 项里。
4. 规格：README 声明标题 20、正文 1000、标签最多 10 个且每个不超过 20 字、封面 3:4（1080×1440）、不做 9:16。草稿校验与成卡尺寸与声明一致，测试通过。不一致的是演示模式正文上限和模型标题/标签的返回口径，见上文不符第 1–3 条，等级 P2。
5. 溯源：有参考项目。LICENSE 保留了两条上游版权行。UPSTREAM.md 四字段齐全。`source_commit` 是否真实存在：未核实（本次不访问外网）。Apache-2.0 全文未附，见许可证一节。
