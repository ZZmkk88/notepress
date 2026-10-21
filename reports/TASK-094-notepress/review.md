# notepress 验收审查

结论：无密钥演示模式可以跑通。pytest 32 项全过，真实流程自测 16 个检查点全过，默认地址 `http://127.0.0.1:8000` 的 `/` 与 `/health` 均返回 200。标题 20 字、正文 1000 字、标签最多 10 个且每个不超过 20 字、封面 1080×1440（3:4）与代码一致。仓库内无字体文件，单文件均小于 2MB。P0、P1 为 0 条，本次未改仓库源码。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境在 `E:\muse-bridge\work\TASK-094-notepress\venv`，未放进仓库。`NOTEPRESS_LLM_API_KEY` 未设置。本机存在 HTTP(S)_PROXY（长度 21，具体值不记录）。自测客户端使用 `trust_env=False`。临时库、日志、pytest 临时目录都在 `E:\muse-bridge\work\TASK-094-notepress`。

### 安装依赖

```
E:\muse-bridge\work\TASK-094-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

退出码 0。钉死版本均安装成功：`fastapi-0.156.8`、`uvicorn-0.54.0`、`python-multipart-0.0.32`、`httpx-0.28.1`、`pillow-13.0.0`、`pytest-9.1.1`。输出为 `Using cached`，末行 `Successfully installed ... fastapi-0.156.8 ... pytest-9.1.1 ...`。

### 全量 pytest

```
python -m pytest tests -q -p no:cacheprovider
```

工作目录为仓库根。第一次：

```
32 passed, 1 warning in 17.10s
EXIT 0
ELAPSED_SEC 19.39
```

收尾再跑一次：

```
32 passed, 1 warning in 14.41s
EXIT 0
ELAPSED_SEC 15.50
```

警告原文（两次相同）：

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

32 项与 README.md:70 的「test_app.py 25 项 + test_acceptance.py 7 项」一致（`rg "^def test_"` 计得 25 与 7）。警告不导致失败。DECISIONS.md:36-37 已写明不为此改依赖版本。

无密钥与不打外网的证据：

- 跑测前 `NOTEPRESS_LLM_API_KEY` 为 unset（`audit_files.py` 输出）。
- `tests/test_acceptance.py:98` `test_demo_mode_does_not_call_httpx_post` 在这 32 项里通过：演示模式扩题和写稿时替换的 `httpx.post` 调用次数为 0。
- 固定样例 `tests/test_acceptance.py:122` `test_render_fixed_sample_size_and_no_overflow` 通过：输入为 `SAMPLE_TITLE = "用AI写周报教程"`、`SAMPLE_BODY`、`SAMPLE_TAGS`（同文件 17-19 行），断言 PNG 文件存在、大小在 500 字节到 2MB 之间、尺寸 1080×1440、`宽*4 == 高*3`、外缘非背景像素为 0。
- `test_missing_font_still_renders` 通过。本机未卸载系统字体；缺字体是该用例把 `find_font` 打成返回 None。

### 真实流程自测

```
venv\Scripts\python.exe tests\live_selftest.py 8155
```

退出码 0，耗时 2.12 秒。输出：

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

脚本内 `env.pop("NOTEPRESS_LLM_API_KEY")`（tests/live_selftest.py:42），客户端 `trust_env=False`（同文件 50 行）。流程覆盖选题扩写、写稿、草稿、成卡、导出。

### 服务拉起与关闭

默认端口（未设置 `PORT` / `NOTEPRESS_HOST`，数据库与媒体目录指向 work 目录）：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 text/html; charset=utf-8 notepress True
STOPPED 1
```

另一次显式 `PORT=8765`、`NOTEPRESS_HOST=127.0.0.1`：

```
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
INDEX_STATUS 200
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
```

响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。

两次都用进程句柄 `terminate()` 关掉（未使用 taskkill）。随后 `netstat -ano -p tcp` 过滤 `:8000`、`:8155`、`:8765` 且含 `LISTEN` 的行，结果为空。

### 体积、字体、规格探针

`audit_files.py` 列出仓库全部文件。最大源文件 `app.py` 41750 字节，`static/index.html` 26530 字节。含 `.git` 在内最大文件是对象包 39387 字节。没有 `.ttf` / `.otf` / `.woff` / `.woff2`。均小于 2MB（2×1024×1024 = 2097152 字节）。

本机字体：`C:\Windows\Fonts\msyh.ttc` 存在，`C:\Windows\Fonts\msyhbd.ttc` 存在。探针 `find_font` 结果：

```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
CARD 1080 1440 ratio_3_4 True
```

与 README.md:97 的微软雅黑路径一致。

演示稿三套语气（探针直接调用 `demo_generate`，未配密钥）：

| 语气 | 短选题标题字数 | 短选题正文字数 | 100 字选题正文字数 | 标签 |
|---|---|---|---|---|
| checklist | 13, 11, 12 | 281 | 375 | 5 个，字数 4/6/4/4/4 |
| experience | 13, 11, 12 | 233 | 327 | 同上 |
| pitfall | 13, 11, 12 | 221 | 315 | 同上 |

标题均为 3 条且不超过 20。正文不超过 1000。接口抽查：`tone=pitfall` 返回 200，`demo=true`，正文 219 字，标题 3 条。

接口限长（同一探针，登录后调用）：

```
TOPIC_100 200
TOPIC_101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}
DISTINCT_10 200
DISTINCT_11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
TAG_21 400 {"detail":"标签超过上限 20 字（当前 21 字）"}
TITLE_21 400 {"detail":"标题超过上限 20 字（当前 21 字）"}
BODY_1001 400 {"detail":"正文超过上限 1000 字（当前 1001 字）"}
```

11 个相同标签会去重成 1 个再保存（探针 `DUP_STORED ['同一个']`），与「最多 10 个不同标签」不冲突。

## README 与实际不符处

下列为对得上文件行号的不符。规格硬限制（标题 20、正文 1000、标签 10×20、封面 3:4、不做 9:16）已在上一节用探针与 app.py:32-38、app.py:694-698、app.py:849-858 核对，那些条款相符，不重复列成缺陷。

1. README.md:52 写「自动化测试在演示模式下运行，并断言不会调用 `httpx.post`」。tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208 把 `NOTEPRESS_LLM_API_KEY` 设为 `sk-test-not-real`，并在 tests/test_app.py:182（以及 200、214 行）替换 `llm_chat`。这三支用例走的是打桩路径。`httpx.post` 的断言只在 tests/test_acceptance.py:98 的 `test_demo_mode_does_not_call_httpx_post`。

2. README.md:26 与 README.md:85 写密钥只放环境变量、不要写进仓库。tests/test_app.py:173 等三处出现字符串 `sk-test-not-real`。app.py:236 与 app.py:242 只从 `NOTEPRESS_LLM_API_KEY` 读取。假密钥在测试文件里。

3. README.md:15 写封面底部最多画出前 4 个话题标签，放不下则换行并底对齐。模板封面在 app.py:565-585 按 `tags[:4]` 绘制。上传封面在 app.py:541-549 只画标题，没有标签循环。探针确认上传后封面仍是 1080×1440（`UPLOAD 200`，`UPLOAD_COVER_SIZE (1080, 1440)`）。

4. README.md:10 写生成 3 个标题候选。演示模式探针里三种语气都是 3 条。AI 分支 app.py:374 只做 `titles[:3]`，app.py:375-376 仅在一条都没有时返回 502，1 条或 2 条有效标题会原样成功。本次未配密钥，没有调用真实模型。

5. README.md:14 写话题标签最多 10 个。手填保存超过 10 个时 app.py:857-858 返回 400（探针 `DISTINCT_11` 已复现）。AI 分支 app.py:386 把超出的标签切掉，不报错。两条路径对「超过 10 个」的处理不同。演示模式固定返回 5 个标签，不走切片。

已核对相符的项：

- README.md:28 默认 `127.0.0.1:8000`。app.py:1089-1090 相同。本次未设端口时日志为 `Uvicorn running on http://127.0.0.1:8000`。
- README.md:70-71 的 32 项与 16 个检查点，与 pytest、live_selftest 输出一致。
- README.md:92-103 的字体查找顺序与 app.py:397-404 的 `_FONT_CANDIDATES` 一致，`NOTEPRESS_FONT_PATH` 在 app.py:413-416 优先。都找不到时 app.py:427-434 使用 `ImageFont.load_default()`。
- README.md:8 的 24 小时令牌对应 app.py:37 `TOKEN_TTL_HOURS = 24`。改密只提示不强制，与 DECISIONS.md:3-5 的 D-1 一致，tests 中 `test_hint_only_password_change` 已通过。
- 前端 static/index.html:295 文案为「演示模式」，与 README 用词一致。

另有一处前后端不一致，README 未写选题字数，故不放进「README 不符」，放进 P2：static/index.html:111 的 `maxlength="120"`，后端 app.py:34 与 app.py:777-778 的上限是 100。探针 `TOPIC_101` 返回 400。

## 许可证与署名核查

仓库内声明彼此对得上，本次未改 LICENSE 与 UPSTREAM.md。

- LICENSE:1 为 MIT License。
- LICENSE:3 `Copyright 2025 xpzouying` 与 UPSTREAM.md:11 的 attribution 相同。
- LICENSE:4 `Copyright (c) 2023 dreammis` 与 UPSTREAM.md:18 相同。
- LICENSE:5 `Copyright (c) 2026 ZZmkk88` 是本仓库版权行。
- UPSTREAM.md:3 写代码为独立重写。README.md:4 写代码为独立实现。NOTES.md:5-16 写的是读了参考项目的字段模型和发布流程。仓库内实现是独立的 app.py。
- 参考一四字段齐：UPSTREAM.md:8-11，`source_url` https://github.com/xpzouying/xiaohongshu-mcp ，`source_commit` `7797fd375aba02dcd33afe143f6bee13e5870859`，`license` Apache-2.0，`attribution` Copyright 2025 xpzouying。
- 参考二四字段齐：UPSTREAM.md:15-18，`source_url` https://github.com/dreammis/social-auto-upload ，`source_commit` `28bb5bc20206c26d088311633540127402e4de56`，`license` MIT，`attribution` Copyright (c) 2023 dreammis。
- 两枚 commit 都是 40 位十六进制。任务禁止抓取外网，本次没有联网核对它们是否为上游仓库的真实提交，也不把「未核实」写成 LICENSE 事实错误。
- 参考一的许可证名称是 Apache-2.0，本仓库发出的许可证正文是 MIT。UPSTREAM 写明独立重写，仓库里没有附 Apache-2.0 全文。在独立实现这个前提下，保留上游版权行符合本任务的溯源要求，看不到需要改 LICENSE 的确凿错误。

源码里没有第二个项目的目录或照搬文件。app.py 是单一后端文件。

## 分级修复清单

### P0

无。服务能起，pytest 32 项通过，live_selftest 16 项通过。

### P1

无。变更接口都带 `get_current_user`（抽查 app.py:705 登录公开，其余 `/api` 写接口均有 `Depends(get_current_user)`）。SQL 使用占位符。封面路径取 `Path.name`（app.py:530、app.py:499）。上传先看 `file.size` 再读最多 10MB+1 字节（app.py:986-992）。API 密钥只读环境变量（app.py:236、app.py:242）。默认绑定 127.0.0.1（app.py:1089，日志已证实）。演示模式单测断言未调用 `httpx.post`。

默认口令 `admin` / `admin123` 写在 README.md:24 和 app.py:145，是本机单用户的公开初始口令，测试依赖它。D-1 规定只提示改密。该项留在说明里，不进入修复清单。

### P2

1. tests/test_app.py:173、194、208 的假密钥字符串 `sk-test-not-real`。修法：删掉这三处 `setenv`，只保留对 `llm_chat` 的打桩。不修：禁止改测试；DECISIONS.md:35-36 已将该项永久关闭。字符串不会发出去，因为同用例替换了 `llm_chat`。
2. app.py:541-549 上传封面不画话题标签，与 README.md:15 不一致。修法：在暗带上按 app.py:565-585 的规则画前 4 个标签并做换行。不修：不阻断主流程，现有上传测试只检查尺寸。
3. static/index.html:111 `maxlength="120"` 与 app.py:34 `TOPIC_LIMIT = 100` 不一致。修法：把 maxlength 改成 100。不修：服务端已返回 400，不会写入超长选题。
4. app.py:386 对 AI 标签超过 10 个做切片，app.py:857-858 对手填标签返回 400。修法：AI 结果超过 10 个时返回 502。不修：演示模式不走该分支。
5. app.py:374-376 允许 AI 只返回 1 到 2 个标题，README.md:10 写的是 3 个。修法：有效标题不足 3 个时返回 502。不修：演示模式实测始终 3 个。
6. README.md:52 对测试方式的描述宽于实际用例。修法：改成「演示模式用例断言不调用 httpx.post；另有 3 个用例打桩 llm_chat」。不修：文档问题，测试本身是绿的。
7. 全量测试的 `StarletteDeprecationWarning`（安装后的 `fastapi/testclient.py:1`，建议改用 httpx2）。修法：更换 TestClient 的依赖。不修：DECISIONS.md:36-37 写明不改 requirements 里的版本号；警告不影响通过。
