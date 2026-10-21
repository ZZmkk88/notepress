# notepress 验收审查

结论：无 API key、不访问大模型时，选题 → 写稿 → 草稿 → 成卡 → 导出可以跑通。pytest **32 passed**（14.64s）。`live_selftest` **16 项全过**（2.07s）。`127.0.0.1:8000` 的 `/health` 与首页均为 200。无 P0。P1 一条：演示写稿在选题够长时仍返回超过 1000 字的正文。

## 本地跑通记录

环境：Python 3.11.9。依赖按 `requirements.txt` 与 `requirements-dev.txt` 装进 `E:\muse-bridge\work\TASK-088-notepress\venv`（fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1）。未设置 `NOTEPRESS_LLM_API_KEY`（脚本打印 `KEY_SET False`）。

pytest 命令与结果（`run_pytest.py`，cwd 为仓库，`-p no:cacheprovider`）：

```
32 passed, 1 warning in 14.64s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 这是依赖弃用提示，32 项断言通过。未当失败重试。

`tests/live_selftest.py 8155` 输出末行：

```
ALL PASS · 16 个检查点
LIVE_EXIT 0 SECONDS 2.07
```

按 README 启动 `python app.py`（数据库和媒体目录放在工作目录，`PORT=8000`）。服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
GET /health HTTP/1.1" 200 OK
GET / HTTP/1.1" 200 OK
```

响应片段：`HEALTH 200 {"status":"ok","app_id":"notepress"}`；`HOME 200`，标题为 `<title>notepress · 笔记工坊</title>`。未登录 `GET /api/drafts` 为 401。登录后 `GET /api/me` 为 `{"username":"admin","must_change":true,"llm_configured":false}`。短选题「用AI写周报」写稿：`demo True`，3 个标题，`body_len 284`。跑完已 `terminate` 子进程。

同一次服务探测里，选题 `"题"*800` 的写稿结果是 `GEN_LONG 200 body_len 1078`。`topic_id=999999` 创建草稿时，访问日志为 `POST /api/drafts 500`。客户端随后 `httpx.ReadTimeout`：探测脚本把服务 stdout 接到管道且当时没有读，不能把这次超时记成产品挂死。TestClient 复现为 `app.py:868` 的 `sqlite3.IntegrityError: FOREIGN KEY constraint failed`。

字体解析（`probe_font.py`，未设置 `NOTEPRESS_FONT_PATH`）：

```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
```

体积扫描：43 个文件，`OVER_2MB []`，`FONTS []`，最大 `app.py` 41006 字节。

## README 与实际不符处

1. **README.md:11** 写「标题 20 字、正文 1000 字按平台规矩硬校验，超限明确报错不截断」。**app.py:351-352** 在未配置密钥时直接 `return demo_generate(topic, tone)`，不再检查长度。**app.py:298** 把完整选题拼进正文。实测：干货清单、选题 722 字时正文正好 1000；723 字时正文 1001；800 字时接口 HTTP 200、正文 1078（`run_live.py` 的 `GEN_LONG`）。亲身体验 800 字选题正文 1028，避坑故事 1016。草稿保存路径 **app.py:685-689** 有 `validate_title_body`，与写稿返回不是同一道闸。

2. **README.md:14** 写「话题标签最多 10 个，每个不超过 20 字」。个数在 **app.py:36** `MAX_TAGS = 10` 与 **app.py:848-849**、**app.py:377** 有上限。单条 20 字只在草稿 **app.py:845-846** 拒绝。模型写稿 **app.py:376-377** 只取前 10 条，不检查单条长度。

3. **README.md:52** 写「自动化测试在演示模式下运行，并断言不会调用 `httpx.post`」。断言在 **tests/test_acceptance.py:98** `test_demo_mode_does_not_call_httpx_post`，该用例通过。另外三处测试设置了假密钥：**tests/test_app.py:173**、**tests/test_app.py:194**、**tests/test_app.py:208** 为 `NOTEPRESS_LLM_API_KEY=sk-test-not-real`，并打桩 `llm_chat`，不会发出真实请求。

4. **README.md:12** 称「演示模式」。页面文案是「示例模式」：**static/index.html:295**（另有 **static/index.html:337**、**static/index.html:385**）。接口字段仍是 `demo`。

抽查后与代码一致的 README 说法：默认账号 `admin`/`admin123`（**app.py:145**）；令牌 24 小时（**app.py:37** `TOKEN_TTL_HOURS = 24`）；只监听 `127.0.0.1:8000`（**app.py:1075-1077**，日志已印出该地址）；卡片 1080×1440（**app.py:38**）；三套模板 berry/mint/ink（**app.py:382-386**）；不做 9:16；封面最多画 4 个标签（**app.py:557**）；字体查找顺序与 **README.md:90-95** 对得上 **app.py:388-396**，找不到时 `ImageFont.load_default()`（**app.py:425**）；pytest 25+7=32 与 `32 passed` 一致；自测 16 个检查点与 `ALL PASS · 16` 一致。

附带（不是 README）：**NOTES.md:22** 写运行时只有 FastAPI/uvicorn/httpx/Pillow 四个包。**requirements.txt:3** 还有 `python-multipart==0.0.32`，封面上传依赖它。

## 许可证与署名核查

- **LICENSE:1** 为 MIT。版权行三条：**LICENSE:3** `Copyright 2025 xpzouying`，**LICENSE:4** `Copyright (c) 2023 dreammis`，**LICENSE:5** `Copyright (c) 2026 ZZmkk88`。
- **UPSTREAM.md:8-11** 参考一：`source_url` https://github.com/xpzouying/xiaohongshu-mcp ，`source_commit` `7797fd375aba02dcd33afe143f6bee13e5870859`，`license` Apache-2.0，`attribution` Copyright 2025 xpzouying。四字段齐全，与 LICENSE:3 的版权行一致。
- **UPSTREAM.md:16-19** 参考二：`source_url` https://github.com/dreammis/social-auto-upload ，`source_commit` `28bb5bc20206c26d088311633540127402e4de56`，`license` MIT，`attribution` Copyright (c) 2023 dreammis。四字段齐全，与 LICENSE:4 一致。
- **README.md:3** 与 **UPSTREAM.md:3** 都写代码为独立实现/独立重写。ZZmkk88 只出现在 LICENSE:5，仓库里没有第三条 `source_url`。按本仓作者行理解，和「两份上游 + 作者」是对得上的。
- 本次禁止访问外网，没有打开上述 GitHub 页面，也没有对照 commit 内容。因此不能证明仓库里拷进了上游源码，也不能改写 LICENSE / UPSTREAM 里的 commit、许可证名称或版权句。参考一在 UPSTREAM 中记为 Apache-2.0，本仓 LICENSE 文本是 MIT，同时保留了上游版权行。这是许可文本并列，不是已核实的事实错误，本次不改 LICENSE 与 UPSTREAM。

源码与页面里没有写死的大模型密钥。密钥只从环境变量读取：**app.py:236**、**app.py:242**。默认口令 `admin123` 写在 **app.py:145** 和 **README.md:24**，**DECISIONS.md:3** D-1 规定只提示不强制改密，不列入待修。

## 分级修复清单

### P0

无。服务能起，首页与 `/health` 为 200，pytest 32 项与 live 16 项通过。

### P1

1. **演示写稿可以返回超限正文。** 文件：**app.py:351-352**（直接返回 `demo_generate`），拼接点 **app.py:298**。修法：演示结果返回前用与 **app.py:685-689** 相同的规则检查每个标题和正文，超过 20/1000 字抛 HTTP 400，带上限和当前字数，不截断正文。

### P2

1. **模型标题超限被丢掉，调用方看不到报错。** **app.py:368-370**。修法：只要有一条标题超过 20 字就返回 502，保留现有「一条合法标题都没有」的拒绝，不要先过滤再当成功。
2. **模型返回的标签不检查 20 字。** **app.py:376-377**。修法：单条超长时 502，与草稿接口 **app.py:845-846** 同一上限。
3. **不存在的选题 id 创建草稿会 500。** **app.py:866-874**，异常原文 `sqlite3.IntegrityError: FOREIGN KEY constraint failed`（**app.py:868**）。修法：插入前确认 `topic_id` 存在，不存在则 400。
4. **测试里有假密钥 `sk-test-not-real`。** **tests/test_app.py:173**、**tests/test_app.py:194**、**tests/test_app.py:208**。修法：本任务禁止改测试，不改。该值只用于让 `llm_configured()` 为真，同用例已打桩 `llm_chat`。
5. **页面写「示例模式」，README 写「演示模式」。** **static/index.html:295**。修法：页面三处改成「演示模式」。
6. **选题输入框允许 120 字，接口上限 100。** **static/index.html:111** 的 `maxlength="120"`，上限在 **app.py:34** `TOPIC_LIMIT = 100`。修法：输入框 `maxlength` 改为 100。
7. **NOTES 少写了 python-multipart。** **NOTES.md:22**。修法：改成与 **requirements.txt:1-5** 一致的五个运行时包。
8. **渲染封面时拼路径没有取文件名。** **app.py:521**。删除封面 **app.py:490** 已用 `Path.name`。修法：打开封面前同样只取 basename，避免库里的 `cover_file` 被写成 `..` 时读出目录外文件。当前上传接口只写入 `{草稿id}.png/.jpg`（**app.py:986**），接口本身写不进任意路径。
9. **未知用户登录的耗时补偿和注释不一致。** **app.py:702-705** 每次调用 `hash_password("placeholder")` 生成新盐，再做一次校验，未知用户比密码错误更慢。修法：启动时准备一份固定假哈希，失败分支只做一次 `verify_password`。

默认口令只提示不强制（**DECISIONS.md:3-5** D-1）不修。`llm_chat`（**app.py:243**）使用 httpx 默认信任代理；本机代理变量存在，但演示模式不调用 `httpx.post`（验收测试已通过）。不改为 `trust_env=False`，以免影响必须走代理的真实写稿。

## 专项验收证据

1. **无密钥可跑通。** `KEY_SET False`。短选题写稿 `demo True`、`llm_configured false`。pytest 32 passed，live 16 项全过，覆盖扩题、写稿、草稿、成卡、导出。真实密钥只读环境变量（**app.py:236**、**app.py:242**）。假密钥见 P2-4，位于测试且被打桩。没有「把 key 填进源码就能跑」的分支。
2. **体积与字体。** 单文件最大 41006 字节，无字体文件。成卡字体为本机微软雅黑 `msyh.ttc` / `msyhbd.ttc`。README 写明的回退链与 **app.py:388-425** 一致，最后退回 `ImageFont.load_default()`。
3. **渲染可复现。** **tests/test_acceptance.py:17-19** 固定标题「用AI写周报教程」、正文与标签；**tests/test_acceptance.py:122-150** 断言卡片文件存在、大小在 500 字节到 2MB 之间、尺寸 1080×1440、宽高比 3:4、外缘墨点为 0，字体可用时标题区墨点大于 80。该用例包含在 `32 passed` 里。本机 `find_font` 返回了雅黑路径，墨点断言会执行。
4. **规格。** 草稿创建对标题 20、正文 1000 有 400 报错（**tests/test_app.py:246** 已通过）。封面比例为 3:4，代码与 README 都声明不做 9:16。标签个数上限 10 已实现。不一致处是演示写稿正文可超过 1000（P1-1）以及模型标签字数未校验（P2-2）。
5. **溯源。** 两份参考的 source_url / source_commit / license / attribution 都在 UPSTREAM.md。LICENSE 保留了对应版权行，并另有 ZZmkk88。未改 LICENSE 与 UPSTREAM。
