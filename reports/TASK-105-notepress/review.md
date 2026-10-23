# notepress 验收报告

结论：仓库能在无 API key、不调用大模型的条件下跑通。pytest 34 项通过，真实流程自测 16 个检查点通过，`127.0.0.1:8000` 的 `/health` 与首页返回 200。无 P0，无需要改代码的 P1。本轮不改仓库源码。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境在 `E:\muse-bridge\work\TASK-105-notepress\venv`（未在仓库内建 `.venv`）。依赖按 README 安装，钉版本全部装上，耗时约 61 秒，退出码 0。

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
Successfully installed ... fastapi-0.156.8 ... pillow-13.0.0 ... pytest-9.1.1 ... uvicorn-0.54.0
```

pytest（未设置 `NOTEPRESS_LLM_API_KEY`），耗时 17.43 秒，退出码 0：

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-105-notepress\pytest-tmp
34 passed, 1 warning in 17.43s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试本身通过。

`tests/live_selftest.py`（脚本内去掉 `NOTEPRESS_LLM_API_KEY`，临时目录改到工作目录），退出码 0，耗时 3.11 秒：

```text
ALL PASS · 16 个检查点
```

16 条均为 PASS，包括演示模式扩题、演示模式写稿、标题 ≤20、正文 ≤1000、成卡、导出 zip、状态回填。

按 README 在 8000 端口起了一次 `python app.py`（`NOTEPRESS_HOST=127.0.0.1`，数据库和媒体在工作目录）。启动约 0.68 秒后：

```text
GET /health 200 {"status":"ok","app_id":"notepress"}
GET / 200 bytes=26545 ctype=text/html; charset=utf-8
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:61182 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:61182 - "GET / HTTP/1.1" 200 OK
```

首页 26545 字节与 `static/index.html` 文件大小一致，正文含 `notepress`、`笔记工坊`、登录框。探测结束后对进程调用 `terminate()`，Windows 上退出码为 1，终止前请求已是 200。进程已退出。

同一次探测还确认：本机成卡字体是 `C:/Windows/Fonts/msyh.ttc` 与 `C:/Windows/Fonts/msyhbd.ttc`。10 条种子选题 × 3 种语气，演示正文 228–295 字，标题 3 条、最长 17 字。标题 20 字 + 正文 1000 字 + 4 个 20 字标签渲染出 5 张 1080×1440 的卡，外缘溢墨为 0。渲染后换封面再删草稿返回 200。

## README 与实际不符处

1. `README.md:71` 写 `tests/test_app.py`（25 项）+ `tests/test_acceptance.py`（7 项）共 32 项。`tests/test_app.py` 的 25 个测试函数从第 52 行到第 353 行，数量相符。`tests/test_acceptance.py` 实际有 9 个测试函数：第 88、98、122、153、173、197、216、233、255 行。合计 34。pytest 输出 `34 passed`。多出的两项是第 233 行 `test_update_null_fields_not_stored_as_none_string` 和第 255 行 `test_extreme_aspect_cover_renders`。`README.md:72` 的「16 个检查点」与自测输出一致，这一句相符。

2. `README.md:27` 与 `README.md:86` 写密钥只放环境变量、不要写进仓库。`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 有 `monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")`。`NOTES.md:31` 也写了密钥不进测试。源码侧 `app.py:241`、`app.py:247` 只读环境变量，没有写死密钥。`app.py:145` 的 `admin123` 是 `README.md:25` 写明的本地默认口令，不是 API key。

其余抽查过的规格与代码一致，不记为不符：标题 20（`app.py:32`，`README.md:11`）、正文 1000（`app.py:33`）、标签 10×20（`app.py:35`、`app.py:36`，`README.md:15`）、卡片 1080×1440（`app.py:38`，`README.md:13`）、不做 9:16（源码与前端都没有 9:16）、上传封面只画标题（`app.py:560-565`）、模板封面最多画 4 个标签（`app.py:584`）、字体回退链（`README.md:95-104` 与 `app.py:412-419`、`app.py:455`）、默认监听 `127.0.0.1:8000`（`app.py:1116-1117`）。

## 许可证与署名核查

`LICENSE:1-23` 是 MIT 全文。版权行三行：`LICENSE:3` Copyright 2025 xpzouying；`LICENSE:4` Copyright (c) 2023 dreammis；`LICENSE:5` Copyright (c) 2026 ZZmkk88。

`UPSTREAM.md` 两个参考都有 source_url / source_commit / license / attribution：

- `UPSTREAM.md:8-11`：https://github.com/xpzouying/xiaohongshu-mcp ，commit `7797fd375aba02dcd33afe143f6bee13e5870859`，Apache-2.0，attribution 与 `LICENSE:3` 相同。
- `UPSTREAM.md:15-18`：https://github.com/dreammis/social-auto-upload ，commit `28bb5bc20206c26d088311633540127402e4de56`，MIT，attribution 与 `LICENSE:4` 相同。

`README.md:4`、`UPSTREAM.md:3` 都写代码是独立实现或独立重写。`NOTES.md:3-16` 写的是读了上游 README 和字段模型后自己设计草稿与发布包，仓库里没有上游源码树。

自洽判断：独立重写同时在 LICENSE 保留上游版权行，符合本任务对「有参考则保留版权行并写全四字段」的要求。张力在参考一的许可证是 Apache-2.0，版权行却放在 MIT 正文里。仓库若确实没有复制该项目代码，xpzouying 并不是本软件的版权人，归属写宽了；若复制了代码，单份 MIT 覆盖不了 Apache-2.0 的 NOTICE 和专利条款。本次禁止访问外网，`source_url` 与 `source_commit` 是否真实存在未核实，因此不改 `LICENSE` 与 `UPSTREAM.md`。

FastAPI、Pillow、httpx 等只出现在 `requirements.txt`，作为依赖声明，不记为缺署名。

## 专项验收

1. 无密钥跑通。pytest 与 live_selftest 都在未配置 `NOTEPRESS_LLM_API_KEY` 时通过。`tests/test_acceptance.py:98` 的 `test_demo_mode_does_not_call_httpx_post` 在 34 项通过之中，断言演示模式不调用 `httpx.post`。自测走完选题扩写、写稿、草稿、成卡、导出。真实密钥只在 `app.py:241`、`app.py:247` 从环境变量读取。不符处是测试里的假 key，见上文第 2 条，测试文件禁止修改。

2. 体积与字体。目录列举的最大文件是 `app.py` 42866 字节、`static/index.html` 26545 字节，没有超过 2MB 的文件，没有 ttf/otf/woff/woff2。成卡使用系统字体；本机命中微软雅黑。`README.md:91-104` 写了查找顺序，以及全部缺失时退回 `ImageFont.load_default()`。`tests/test_acceptance.py:216` 覆盖缺字体仍输出 1080×1440。

3. 渲染可复现。`tests/test_acceptance.py:17-19` 固定标题「用AI写周报教程」、固定正文和标签。`tests/test_acceptance.py:122-150` 断言卡片文件存在、大小在 500 字节到 2MB 之间、尺寸 1080×1440、3:4、外缘无溢墨，有字体时标题区有墨。该项在 34 项通过之中。另一次 1000 字正文探测的 5 张卡外缘溢墨都是 0。

4. 规格一致。见「README 与实际不符处」末段。标题、正文、标签、封面比例与 README 声明一致。测试计数那一条是文档数字过期，不改变这些上限。

5. 溯源。有参考，四字段齐全，LICENSE 保留了两行上游版权，并有本仓版权行 `ZZmkk88`。详见上一节。commit 未联网核实。

## 分级修复清单

### P0

无。安装、pytest、真实流程自测、8000 端口首页和健康检查都已跑通。

### P1

无。下列项看过，不升为 P1，也不改代码：

- 默认口令 `admin` / `admin123`（`app.py:145`，`README.md:25`）是既定产品行为：只提示改密，不强制。强制改密会破坏现有测试和 `DECISIONS.md` 的 D-1。
- 上传图片的像素上限由 Pillow 处理。`Image.open` 在像素数超过 `2 * MAX_IMAGE_PIXELS` 时抛 `DecompressionBombError`，`app.py:1018-1023` 捕获后返回 400。极端宽高比已改为 `ImageOps.fit`（`app.py:555`），`tests/test_acceptance.py:255` 通过。
- 渲染后再次上传封面并删除草稿，在本机 Windows 上返回 200，没有文件锁错误。

### P2

1. `README.md:71` 测试总数写成 32，验收文件写成 7 项。实际 34 与 9。修法：把该句改成 `test_app.py` 25 项 + `test_acceptance.py` 9 项，共 34 项。本轮只修 P0/P1，不改文档。

2. `tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 写死假 key `sk-test-not-real`。修法：删掉这三处字面量，改用非密钥占位或直接打桩 `llm_configured`。测试文件禁止修改，本轮不改。`DECISIONS.md:71` 已把同类项标成测试红线关闭。

3. `app.py:401` 对 AI 返回的标签条数做 `tags[:MAX_TAGS]`，多出来的直接丢掉。`app.py:875-876` 对草稿保存的超个数标签返回 400。修法：生成路径在条数超过 10 时返回 502，与单条超长的处理一致。演示模式固定 5 条（`app.py:335`），现有测试不覆盖这条。不阻断运行。

4. `app.py:389-402` 在至少有 1 条合规标题时原样返回，不要求恰好 3 条。`README.md:10` 写的是生成 3 个标题候选。修法：不足 3 条时返回 502。演示模式实测始终是 3 条，现有用例是绿的。

5. `index.html:53` 的超限样式是 `.count.over`。`index.html:365-368` 把 `over` 加在父级 `label` 上，计数用的 `span` 没有 `count` 类。修法：给 `#titleCount` 和 `#bodyCount` 加上 `count`，或把选择器改成 `label.over`。编辑区 `index.html:444-447` 也没有超限样式。纯界面，服务端仍会 400。

6. `index.html:470-476` 点「生成卡片」时先保存；保存函数在失败时自己吞掉异常，渲染仍会继续并提示成功。修法：保存失败时返回，不再调用 render。草稿内容不会被超限文本覆盖，提示不准确。

7. `fastapi/testclient.py` 的 `StarletteDeprecationWarning` 要求换 `httpx2`。修法：不动 `requirements.txt` 的版本号。测试是通过的，警告不影响结果。

8. `LICENSE:3` 与 `UPSTREAM.md:10` 的 Apache-2.0 归属张力见许可证一节。修法：在能核对上游仓库之前不改 `LICENSE` 与 `UPSTREAM.md`。
