# notepress 验收审查（改代码前）

结论：无密钥演示模式能跑通。现有 pytest `25 passed`，`live_selftest.py` 16 项全过，默认端口 8000。阻断项没有。要修的是封面长标签被裁出画布（P1），以及验收资产还没盖住「文字不溢出」和「无密钥不发外网」。

上游仓库的 URL 与 commit 本机未访问外网，**未核实**。git 作者已核实：`bb4e5bd`，ZZmkk88 \<927675399@qq.com\>。

## 跑通记录

解释器：`E:\muse-bridge\env\TASK-059-notepress-tests\Scripts\python.exe`（Python 3.11.9）。`NOTEPRESS_LLM_API_KEY` 未设置。

```
python -m pip install -r requirements.txt -r requirements-dev.txt
```
退出码 0，32.41s。fastapi 0.156.8、uvicorn 0.54.0、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1。

```
python -m pytest tests\test_app.py -q --tb=short
```
`25 passed, 1 warning in 5.97s`（仅 StarletteDeprecationWarning）。

```
python tests\live_selftest.py
```
`ALL PASS · 16 个检查点`。

```
python app.py
```
`Uvicorn running on http://127.0.0.1:8000`。本机探测：`/api/me` 为 `llm_configured: false`；扩题 `demo: true` 且 6 条；写稿 `demo: true`；渲染 3 张 PNG；导出 zip 含 `01.png` 与 `文案.txt`。

## 与验收标准对照

| 项 | 结论 | 证据 |
|---|---|---|
| 无密钥全流程 | 通过 | live_selftest 16 项；`/api/me` 的 `llm_configured` 为 false。密钥只从 `NOTEPRESS_LLM_API_KEY` 读，`app.py:235-242` |
| 选题扩写有测试 | 已有 | `tests/test_app.py:146` `test_expand_demo_mode` |
| 成卡尺寸 | 已有 | 同文件 `:301` 断言 `(1080, 1440)`，与 `app.py:38`、README 第 13 行 3:4 一致 |
| 文字不溢出 | **未测，且长标签会溢出** | 见 P1-1。短样例外缘像素为 0 |
| 导出 zip | 已有 | `tests/test_app.py:337`；本机导出含 `01.png`…`文案.txt` |
| 违禁词 | 自查命中，不拦截保存 | `tests/test_app.py:266`；页面 `static/index.html:246`「只提示、不拦截」；`app.py:217` 注释同口径。与 README 第 15 行一致，不改成拒绝保存 |
| 无密钥不发外网 | **没有断言** | `llm_chat` 只在配了密钥后走 `httpx.post`（`app.py:243`）。演示分支在 `app.py:333`、`app.py:351` 提前返回。现有用例未打桩 `httpx.post` |
| README | 4098 字节 / 96 行，不是 0 字节 | 安装段写了 `python -m venv .venv` 和 Linux `source .venv/bin/activate`（README 第 27-40 行）。本机未执行这两条。字体顺序与代码不符 |
| 字数与比例 | 标题 20、正文 1000、封面 3:4 一致 | README 第 11、13 行；`app.py:32-38`。标签上限 README 未写，代码 `TAG_LIMIT=20`、`MAX_TAGS=10`（`app.py:35-36`） |
| LICENSE / UPSTREAM | 文件都在，版权行不齐 | 见下方许可证节 |
| 体积与字体 | 通过 | 扫描无 >2MB、无 ttf/otf/woff/woff2/ttc、无 __pycache__。跟踪文件 13 个，无字体 |
| .gitignore | 已挡住要求的产物 | `.gitignore:1-8`：`.venv/` `__pycache__/` `*.pyc` `.env` `*.db` `*.sqlite` `media/` `*.zip`。改代码前 `git status --porcelain` 为空 |

## README 与实际不符

1. README 第 27-31 行要求先建 `.venv` 再 `pip install`。本次直接用任务环境的 Python 安装并启动成功。建仓库内 `.venv` 会留下大文件，且本任务禁止 `del`/`rm`，所以不按原文建虚拟环境。
2. README 第 36-40 行的 `source .venv/bin/activate` 是 bash，本机 PowerShell 不能执行。
3. README 第 79-81 行字体顺序写成「微软雅黑 → 苹方 → Noto / 文泉驿」。代码 `_FONT_CANDIDATES`（`app.py:388-396`）顺序是 Noto Sans CJK → 文泉驿正黑 → 微软雅黑 `msyh.ttc`/`msyhbd.ttc` → 苹方 `PingFang.ttc` → 华文黑体 `STHeiti Medium.ttc`，前面还有 `NOTEPRESS_FONT_PATH`（`app.py:404-407`）。本机实际用到 `C:/Windows/Fonts/msyh.ttc`。
4. 全部找不到时，`app.py:425` 退回 `ImageFont.load_default()`。README 没写这条降级。探针：无字体时仍输出 1080×1440，中文不能当正式成卡。
5. README 第 59 行「自动化测试 25 项」与本次 `25 passed` 一致；「16 个检查点」与 live_selftest 一致。补测试后这两句要改成新的实测数字。
6. 话题标签数量 README 未声明。代码最多 10 个、每个 20 字，封面只画前 4 个（`app.py:513`）。

默认端口 8000（`app.py:993`，README 第 43、68 行）与本次启动一致。演示模式说明（README 第 12、72 行）与 `llm_configured()` 为空则走模板一致。

## 许可证与署名

- LICENSE 是 MIT，版权行只有 `Copyright (c) 2026 ZZmkk88`（LICENSE 第 3 行）。与 `git log` 作者 ZZmkk88 一致，不是审查时新编的名字。
- UPSTREAM.md 写明代码为独立重写，并给了两个设计参考的四字段：
  - source_url `https://github.com/xpzouying/xiaohongshu-mcp`，source_commit `7797fd375aba02dcd33afe143f6bee13e5870859`，license Apache-2.0，attribution `Copyright 2025 xpzouying`
  - source_url `https://github.com/dreammis/social-auto-upload`，source_commit `28bb5bc20206c26d088311633540127402e4de56`，license MIT，attribution `Copyright (c) 2023 dreammis`
- 上述 URL 与 commit **未核实**（禁止外网抓取）。代码结构是单文件 FastAPI，看不出整段复制。按「参考了开源项目则 LICENSE 保留上游版权行」，现有 LICENSE 少了 UPSTREAM 里已经写下的两行版权。不新编第三来源。
- 无密钥路径没有写死的真实 key。已有测试 `tests/test_app.py:173`、`:194`、`:208` 使用假字符串 `sk-test-not-real`。禁止改已有测试，本轮不动。

## 分级修复清单

### P0（跑不起来 / 阻断）

无。

### P1（本轮修，仅 1 项）

1. **封面话题标签超宽被裁切。** `app.py:513-515` 把最多 4 个标签画成一行，不测量宽度。实测 4×20 字时 `textlength=2532`，bbox 右端 x=2616，画布只有 1080；外缘 8px 内有 183 个非背景像素，颜色是副文本色。短标签（演示稿）右端 x=936，不溢出。内容卡正文换行后外缘像素为 0。  
   修法：一行放得下时仍画在 `y=CARD_H-240`；放不下则按 `CARD_W-168` 换行，整块放在页脚上方。不改接口。

### 验收资产（允许路径，本轮补；不计入上面的 5 项上限）

1. 新增 `tests/test_acceptance.py`（不改 `tests/test_app.py` 的断言）：选题扩写、固定输入成卡（文件存在、1080×1440、3:4、外缘无字）、超长标签不溢出、导出 zip、违禁词命中且不拦截保存、无密钥时 `httpx.post` 未被调用、缺字体仍能出图。
2. 改 `README.md`：安装/启动/测试只留本次会真实执行并成功的命令；写明默认端口 8000、空密钥演示模式；字体名与 `app.py:388-425` 一致，并写明 `load_default` 降级；声明标题 20、正文 1000、标签最多 10 个且每个 20 字、封面仅 3:4。
3. 改 `LICENSE`：在 ZZmkk88 行之上保留 UPSTREAM 已声明的两行版权。不改 UPSTREAM 四字段，避免编造 commit。

### P2（不修）

1. 三套演示正文都含「第一」（`第一步` / `第一版`，`app.py:300` 附近与 `:313`、`:322`）。自查必命中。口径是提示不是拦截，不改文案。
2. `tests/test_app.py:173` 假密钥字符串。禁止改已有测试。
3. `static/index.html:111` 选题 `maxlength="120"`，服务端 `TOPIC_LIMIT=100`（`app.py:34`）。超限会 400，不改前端。
4. `.gitignore` 未写 `.pytest_cache/`。要求的 `__pycache__`、`*.pyc`、数据库、`media/`、`*.zip` 已忽略。改代码前 status 为空，不改。
5. 违禁词按子串计数，`app.py:222-228`。「第一」会命中「第一步」。与词表一致。
