# notepress 验收审查

结论：无 API key、不访问外网时，选题 → 写稿 → 草稿 → 成卡 → 导出可以跑通。pytest 32 项通过，真实流程自测 16 个检查点通过，`127.0.0.1:8000` 的 `/health` 与首页正常，服务已关掉。标题 20 字、正文 1000 字、标签最多 10 个且保存时每条最多 20 字、封面 1080×1440（3:4）与 README 一致。仓库无字体文件，最大源文件 41006 字节。

P0 无。P1 无。未改仓库源码。P2 是文档口径和边界行为，见分级清单。

## 本地跑通记录

环境：Python 3.11.9。开工时 `NOTEPRESS_LLM_API_KEY` 未设置。虚拟环境放在 `E:\muse-bridge\work\TASK-079-notepress\venv`（不在仓库里建 `.venv`，避免临时文件进仓库）。依赖文件与 README 相同。

安装（exit 0）：

```
python -m venv E:\muse-bridge\work\TASK-079-notepress\venv
venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。

全量测试（仓库根目录，`NOTEPRESS_LLM_API_KEY` 置空，`-p no:cacheprovider`）：

```
................................                                         [100%]
32 passed, 1 warning in 15.89s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自已安装的 fastapi/starlette，32 项仍然通过。

真实流程（`tests\live_selftest.py 8155`，脚本内去掉 API key，临时目录指到 work）：

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

按 README 的端口起服务（`PORT=8000`，`NOTEPRESS_HOST=127.0.0.1`，数据库和媒体目录在 `work\svc`，进程 cwd 故意不在仓库根）。约 2.01 秒后关掉。

```
PORT8000_BEFORE False
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
INDEX_STATUS 200
INDEX_CT text/html; charset=utf-8
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
NOAUTH_DRAFTS 401 {"detail":"未登录"}
NOAUTH_CARD 401
DOCS 404
PORT8000_AFTER False
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:54304 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:54304 - "GET / HTTP/1.1" 200 OK
DB_IN_REPO False
MEDIA_IN_REPO False
```

响应头有 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。本机字体：`C:\Windows\Fonts\msyh.ttc` 与 `msyhbd.ttc` 都在。导入后 `find_font` 返回这两条路径。

系统 `dir /s`：业务文件最大为 `app.py` 41006 字节，`static\index.html` 26567 字节。无 ttf/otf/woff/woff2/ttc。2MB 红线未破。

## README 与实际不符处

下列各项带文件行号。主规格（标题 20、正文 1000、标签个数、3:4 尺寸、16 个检查点、32 项测试）与代码一致，不列在这里。

1. 界面把无密钥模式叫「示例模式」，README 叫「演示模式」。`README.md:12`、`README.md:26` 写演示模式；`static/index.html:295` 为「示例模式：未配置 AI 接口，写稿为内置示例稿」，`static/index.html:337` 为「示例模式给出的候选」，`static/index.html:385` 为「这是示例稿」。响应字段 `demo` 与 README 一致。

2. 选题字数：`README.md:9` 只写「手动记选题」，没有上限。`app.py:34` `TOPIC_LIMIT = 100`，`app.py:768` 超过则 400。探针：100 字返回 200，101 字返回 `选题超过上限 100 字（当前 101 字）`。`static/index.html:111` 的输入框 `maxlength="120"`，101–120 字能输入、提交被接口拒绝。

3. 方向词：`README.md:9` 没有字数上限。`app.py:792` 超过 50 字返回 400。探针 51 字得到 `方向词超过上限 50 字（当前 51 字）`。`static/index.html:118` 的扩题输入框没有 maxlength。

4. 演示扩题把方向词切到 12 字。`app.py:268` `d = direction.strip()[:12]`。探针方向词「一二三四五六七八九十甲乙丙」（13 字）返回 200、`demo=true`，六条候选都不含完整方向词，末字「丙」被去掉。例如「用AI搞定一二三四五六七八九十甲乙，小白完整教程」。

5. 配了密钥但扩题调用失败时，接口仍返回 200 且 `demo=true`。`app.py:346` 到 `app.py:347` 捕获所有异常后走 `demo_expand`。探针让 `llm_chat` 抛 `RuntimeError`，得到与没配密钥相同的演示候选。`README.md:9` 写的是「接了 AI 接口时由 AI 扩题」。

6. 同一失败如果发生在写稿，异常不被捕获。`app.py:362` 直接调用 `llm_chat`。探针里 TestClient 把 `RuntimeError: upstream down` 原样抛出，栈顶在 `app.py:362`，没有 JSON 错误体。扩题失败和写稿失败的行为不一致。

7. 「超限明确报错不截断」只在草稿保存、以及全部标题都超限时成立。`README.md:11`。`app.py:368` 会丢掉超过 20 字的标题，只要还剩至少一条就返回 200。探针混合「正常标题」和 21 个「标」：`200 {"titles":["正常标题"],...}`，没有报错。全部超限时 `app.py:370` 返回 502「AI 返回的标题都超过 20 字，请重试」。正文超限在 `app.py:374` 返回 502，这条与 README 一致。草稿接口 `app.py` 的 `validate_title_body` 对 21 字标题、1001 字正文返回 400，pytest 已覆盖。

8. 话题标签「每个不超过 20 字」在保存时执行，在生成接口不执行。`README.md:14`。`app.py:845` 保存时超过 `TAG_LIMIT`（`app.py:35` 为 20）返回 400，探针 21 字标签得到 `标签超过上限 20 字（当前 21 字）`，11 个标签得到 `标签超过上限 10 个（当前 11 个）`。`app.py:377` 生成结果只做 `tags[:MAX_TAGS]`，不查单条长度。探针在假 LLM 返回 21 个「好」时，`/api/generate` 为 200，标签原样回到响应里。

9. 上传的封面不画话题标签。`README.md:15` 写封面底部最多画前 4 个标签。模板封面在 `app.py:556` 起绘制前 4 个标签。上传封面分支 `app.py:520` 到 `app.py:539` 只画标题，不画标签。

10. 默认路径写成当前目录，代码用的是 `app.py` 所在目录。`README.md:78` 默认 `./notepress.db`，`README.md:79` `./media`，`README.md:80` `./data/banned_words.json`。`app.py:24` 到 `app.py:29` 默认是 `BASE_DIR`（`Path(__file__).resolve().parent`）。探针 cwd 在 work 目录时，打印出的 `DB_PATH` 仍是 `E:\muse-bridge\in\TASK-079-notepress\notepress.db`。按 README 在仓库根启动时两条路径重合。

11. 测试小节单独看不完整。`README.md:55` 与 `README.md:61` 只写 `pip install -r requirements-dev.txt`。`requirements-dev.txt:1` 只有 `pytest==9.1.1`。`tests/test_app.py:15` 导入 fastapi。只执行测试小节、不先装 `requirements.txt`，导入会失败。本次是两个文件一起装的，没有另起一个只装 dev 依赖的环境去复现导入错误。

12. `NOTES.md:22` 写运行时依赖「只有 FastAPI/uvicorn/httpx/Pillow 四个」。`requirements.txt:3` 还有 `python-multipart==0.0.32`，封面上传依赖它。README 快速开始装的是 `requirements.txt`，这条是 NOTES 与依赖清单不一致。

13. 超过 10MB 的图片会被拒绝，但提示把大小四舍五入成上限本身。`app.py:975` 使用 `.1f`。探针发送 10MB+1 字节，返回 `图片超过上限 10MB（当前 10.0MB）`。拒绝行为成立，数字与「超过」矛盾。

14. 封面从 png 换成 jpg 后，旧文件留在磁盘上，直到删除草稿。`app.py:991` 直接写入新文件。探针先上传 png 再上传 jpeg，目录里同时有 `1.jpg` 和 `1.png`，接口记录的 `cover_file` 是 `1.jpg`。删除草稿后两个文件都没了（`app.py:488` 起的 `clear_cover_files` 会删两种扩展名）。上传文件名 `../../evil.png` 没有被采用，实际文件名是 `1.png`。

## 许可证与署名核查

本仓声明独立实现，同时保留两份上游署名。仓内没有上游源码树。本次按任务要求未访问 GitHub，**source_commit 是否真实存在未核实**，不能替 `NOTES.md:16`「HEAD 提交号经接口实查」背书。

`UPSTREAM.md` 四字段齐全：

| 项 | 参考一 | 参考二 |
|---|---|---|
| source_url | `UPSTREAM.md:8` https://github.com/xpzouying/xiaohongshu-mcp | `UPSTREAM.md:15` https://github.com/dreammis/social-auto-upload |
| source_commit | `UPSTREAM.md:9` 7797fd375aba02dcd33afe143f6bee13e5870859 | `UPSTREAM.md:16` 28bb5bc20206c26d088311633540127402e4de56 |
| license | `UPSTREAM.md:10` Apache-2.0 | `UPSTREAM.md:17` MIT |
| attribution | `UPSTREAM.md:11` Copyright 2025 xpzouying | `UPSTREAM.md:18` Copyright (c) 2023 dreammis |

`LICENSE:3` 到 `LICENSE:5`：

```
Copyright 2025 xpzouying
Copyright (c) 2023 dreammis
Copyright (c) 2026 ZZmkk88
```

前两行与 `UPSTREAM.md` 的 attribution 一致。第三行 `ZZmkk88` 只出现在 LICENSE，README 与 UPSTREAM 没有说明这个名字。LICENSE 正文是 MIT。

`README.md:3` 与 `UPSTREAM.md:3` 都写代码为独立实现 / 独立重写。参考一的 license 字段是 Apache-2.0，本仓 LICENSE 没有附带 Apache-2.0 全文。在「独立重写 + 保留上游版权行」这个口径下，版权行本身与任务要求一致。没有对照上游文件，不能认定版权行是事实错误，因此不改 `LICENSE` 和 `UPSTREAM.md`。

源码里的密钥只读环境变量：`app.py:235` `llm_configured()`，`app.py:242` 从 `NOTEPRESS_LLM_API_KEY` 取值。仓库业务文件里没有可用的真实密钥。`tests/test_app.py:173`、`:194`、`:208` 有字符串 `sk-test-not-real`，只用来把「已配置密钥」打开，同时替换 `llm_chat`，pytest 未出网。这与「测试里不得出现假 key」的字面要求不完全一致。测试文件按任务禁止修改，所以这条不改。

默认口令 `admin` / `admin123` 写在 `README.md:24` 和 `app.py:145`。`DECISIONS.md:3` 的 D-1 规定首次改密只提示、不强制，并写明审查不得把强制改密加回去。pytest `test_hint_only_password_change` 已通过。此项按已定决策关闭，不列入修复。

## 分级修复清单

### P0

无。无密钥安装、32 项测试、16 个检查点、8000 端口首页和 `/health` 均已跑通。

### P1

无。未发现可经接口到达的越权、密钥泄露、或已入库数据被静默写坏。上传文件名不能路径穿越（落盘名是 `{草稿id}.png` / `.jpg`）。未登录访问草稿和卡片均为 401。`/docs` 为 404。封面大小超过 10MB 被拒绝。改标题会删掉旧卡片，只改状态不会删；导出使用新标题，尺寸 1080×1440。这些与 `DECISIONS.md` D-10 一致。

### P2

1. `static/index.html:111` 选题框 maxlength 120，与 `app.py:34`、`app.py:768` 的 100 字上限不一致，`README.md:9` 也没写上限。修法：maxlength 改为 100，并在 README 写明选题最多 100 字。
2. `app.py:792` 方向词最多 50 字，`static/index.html:118` 与 `README.md:9` 都没写。修法：输入框加上 maxlength 50，README 补一句。
3. `app.py:268` 演示扩题把方向词切到 12 字，13 字方向词的候选不含全文。修法：候选里保留完整方向词（仍受 50 字上限约束），标题放不下时再缩短并在文案里标明截断。
4. `app.py:346` 扩题失败伪装成 `demo:true` 的 200；`app.py:362` 写稿失败则异常直接冒泡。修法：两处都捕获上游错误并返回 502，响应里不要把失败说成演示稿。
5. `app.py:368` 只丢掉超长标题并返回 200，与 `README.md:11`「超限明确报错」不一致。修法：只要有一条标题超过 20 字就 502，不要悄悄丢掉。
6. `app.py:377` 生成接口不检查单条标签长度，与 `README.md:14` 和 `app.py:845` 的保存校验不一致。修法：超过 20 字的标签按 502 拒绝，或在返回前剔除并在响应里说明。
7. `app.py:520` 上传封面不画前 4 个标签，与 `README.md:15` 的封面描述不一致。修法：上传封面底栏按模板封面同一套换行规则画标签，或把 README 改成「仅模板封面画标签」。
8. `app.py:991` 更换封面扩展名时不删除另一种扩展名的旧文件。修法：写入前调用已有的 `clear_cover_files`。
9. `README.md:78` 到 `README.md:80` 把默认路径写成 `./`，`app.py:25` 实际相对 `app.py` 所在目录。修法：README 改成「与 app.py 同目录」。
10. `README.md:12` 的「演示模式」与 `static/index.html:295` 的「示例模式」用词不同。修法：界面统一写成「演示模式」。
11. `README.md:55` 测试步骤只安装 `requirements-dev.txt`。修法：写成先装 `requirements.txt` 再装 `requirements-dev.txt`。
12. `NOTES.md:22` 漏了 `requirements.txt:3` 的 python-multipart。修法：改成五个运行时包，并点名 python-multipart（封面上传需要它）。
13. `app.py:975` 把 10MB+1 字节显示成「当前 10.0MB」。修法：用整数字节或保留足够小数，避免四舍五入后等于上限。
14. `tests/test_app.py:173`（以及 `:194`、`:208`）写了假 key 字符串 `sk-test-not-real`。修法：本任务禁止改测试，不改。它不会发出真实请求。
15. `app.py:521` 用 `MEDIA_DIR / "covers" / cover_file` 拼路径，没有取 basename。当前上传接口写不进 `..`。修法：渲染前对 `cover_file` 取 basename，与删除草稿时的处理对齐。

不修 P2。依赖版本号不改，`LICENSE` 与 `UPSTREAM.md` 不改。

## 专项验收

1. 无密钥可跑通。`NOTEPRESS_LLM_API_KEY` 未设置。pytest 32 passed；`tests/test_acceptance.py` 的 `test_demo_mode_does_not_call_httpx_post` 在这 32 项内，suite 无失败。live_selftest 16/16，响应 `demo` 为 true。真实密钥只从环境变量读取（`app.py:235`、`app.py:242`）。假 key 字符串仅在 `tests/test_app.py:173` 等三处，见 P2-14。没有「填上 key 才能跑」的未验证路径：本次全程没有密钥。

2. 体积与字体。`app.py` 41006 字节，小于 2MB。目录中无 ttf/otf/woff/woff2。`README.md:88` 起写明查找顺序：`NOTEPRESS_FONT_PATH`、Noto Sans CJK、文泉驿正黑、微软雅黑（`msyh.ttc` / `msyhbd.ttc`）、苹方、华文黑体；都没有时用 Pillow `ImageFont.load_default()`，并说明该位图字体没有中文、不能当正式卡片。本机走微软雅黑。`test_missing_font_still_renders` 在已通过的 32 项内。

3. 渲染可复现。`tests/test_acceptance.py:17` 固定标题「用AI写周报教程」、正文「第一段内容。…」、标签「AI工具」「周报」。`tests/test_acceptance.py:74` 起断言 PNG 文件存在、大小在 500 字节到 2MB 之间、尺寸 1080×1440、宽高比 3:4、外缘 8 像素无非背景墨点；有字体时标题区有墨。suite 通过，不是只看截图。另有 `test_long_tags_stay_inside_card` 用 4 个 20 字标签检查不溢出。

4. 规格。README 声明的标题 20、正文 1000、标签最多 10 个、每条最多 20 字、封面 3:4 且不做 9:16，与 `app.py:32` 到 `app.py:38` 以及草稿校验一致，pytest 覆盖了上限与恰好卡线。不一致处是生成接口的标签长度（P2-6）、部分超长标题被静默丢掉（P2-5）、上传封面不画标签（P2-7）。

5. 溯源。有两份参考，`UPSTREAM.md` 四字段齐全，`LICENSE` 保留对应版权行。详见上一节。未联网，commit 未核实。
