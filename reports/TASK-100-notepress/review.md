# notepress 轻量核验

14 条声称修复都成立。无密钥下 pytest 32 项通过，真实流程自测 16 个检查点通过。

历史里只有一笔提交 `2f5b7e781e8846a60506bf965df044c34925efd1`，说明是 TASK-072。TASK-059、TASK-064 没有单独提交对象，对应改动在当前树和 `DECISIONS.md` 里，按代码与复现结果判定。

## 环境与测试实况

环境：Python 3.11.9。依赖装在 `E:\muse-bridge\work\TASK-100-notepress\venv`，版本与 `requirements.txt` / `requirements-dev.txt` 一致（fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1）。未设置 `NOTEPRESS_LLM_API_KEY`。没有往仓库写 `.venv`、缓存或数据库。

pytest（README 命令，`-p no:cacheprovider`）：

```
32 passed, 1 warning in 15.97s
EXIT 0
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。

真实流程（`python tests\live_selftest.py 8155`，只打 127.0.0.1，脚本去掉了 LLM 密钥）：

```
ALL PASS · 16 个检查点
ELAPSED_SEC 2.87
EXIT 0
```

覆盖登录 → 选题扩写（demo）→ 写稿（demo）→ 草稿 → 违禁词 → 成卡 PNG → 导出 zip → 回填已发布。

最小复现脚本 `E:\muse-bridge\work\TASK-100-notepress\probe_claims.py` 退出码 0。下面逐条引用它的输出。

## 逐条核验结论

### 1. TASK-059 封面长标签先截断再换行、底对齐 — 已修

`app.py:565-585`：最多取前 4 个标签；单行放得下时画在 `CARD_H - 240`；放不下时走 `wrap_text` 再 `fit_line`（`app.py:578-579`），整块从页脚上方往上排（`app.py:581-585`）。

复现（4 个 20 字标签，标题 20 字）：换行 4 行，宽度 891 / 891 / 891 / 867，均小于 912，`FIT_EQ_WRAP True`（这一例上省略号截断没有改字）。`BOTTOM_ALIGN_TY 1050`，末行顶 `1218`，页脚 `1290`。封面 `COVER_SIZE (1080, 1440)`。验收测试 `tests/test_acceptance.py:153` `test_long_tags_stay_inside_card` 在 32 项里通过，外缘墨点断言在 `tests/test_acceptance.py:84`。

### 2. TASK-059 新增验收测试 7 项 — 已修

`tests/test_acceptance.py` 七个测试函数：`88`、`98`、`122`、`153`、`173`、`197`、`216` 行。`tests/test_app.py` 另有 25 个 `def test_`。pytest 结果 `32 passed`，与 25+7 一致。

### 3. TASK-059 README 去重，并同步 32 项与字体顺序 — 已修

`README.md` 全文 118 行。测试次数只写在 `README.md:70`：`test_app.py` 25 项 + `test_acceptance.py` 7 项，共 32 项。真实流程 16 个检查点写在 `README.md:71`，与 live 输出 `16 个检查点` 一致。

字体顺序只写在 `README.md:94-99`：`NOTEPRESS_FONT_PATH` → Noto Sans CJK → 文泉驿正黑 → 微软雅黑 → 苹方 → 华文黑体。代码回退链是 `app.py:413-418` 先读环境变量，再按 `app.py:397-405` 的 `_FONT_CANDIDATES`。本机实际用到 `C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`（probe：`FIND_FONT`）。

### 4. TASK-059 LICENSE 补上游署名 — 已修

`LICENSE:3-5`：

```
Copyright 2025 xpzouying
Copyright (c) 2023 dreammis
Copyright (c) 2026 ZZmkk88
```

与 `UPSTREAM.md:11`、`UPSTREAM.md:18` 的 attribution 相同。`UPSTREAM.md:8-11` 与 `14-18` 写了 source_url / source_commit / license / attribution。上游提交号未联网核对。

### 5. TASK-064 导出始终重画，编辑内容删旧卡 — 已修

导出入口 `app.py:1063` 每次调用 `render_cards`。`render_cards` 在 `app.py:519-520` 先删掉旧的 `card_*.png` 再画。

编辑在 `app.py:920-933`：标题、正文、标签、模板变了才 `clear_card_files`；只改状态不删。

复现：只改状态后，被写成 `STALE-CARD` 的 `card_1.png` 还在（`STALE_KEPT True`）。接着导出，zip 里的 `01.png` 魔数是 PNG，不再是 `STALE-CARD`，文案仍是「标题：旧标题」。再改标题，`CARD_EXISTS_AFTER_EDIT False`。再次导出文案为「标题：新标题」，卡片重新生成。

### 6. TASK-064 删除同步清卡片和封面，下载先查草稿 — 已修

`app.py:937-946` 删除草稿时调用 `clear_card_files` 和 `clear_cover_files`。封面文件名经 `app.py:499` 的 `Path.name` 取 basename。

下载在 `app.py:972-977` 先查草稿行，没有草稿直接 404，然后才找 png。

复现：接口删除后 `cover False`、`card False`、目录不存在。另一次只从 sqlite 删掉草稿行、磁盘上的 png 还在，`GET /cards/1` 返回 `404 {"detail":"草稿不存在"}`。

### 7. TASK-064 封面上传先判 size 再读 — 已修

`app.py:986-992`：`limit = 10MB`；`file.size` 超过上限立刻 400，文案带「当前 …MB」；否则 `read(limit + 1)`，读到的字节数超过上限再 400，这条文案没有「当前」。

复现：上传 10485761 字节，`400 {"detail":"图片超过上限 10MB（当前 10.0MB）"}`。这是 size 分支的文案，发生在读入内容之前。小图上传返回 200，`cover_file` 为 `4.png`。

### 8. TASK-072 前端演示模式文案统一 — 已修

全仓库「示例模式」只出现在 `DECISIONS.md:27` 的改动说明里。前端三处用的是演示模式 / 演示稿：

- `static/index.html:295` 徽章「演示模式：未配置 AI 接口，写稿为内置示例稿」
- `static/index.html:337` 「演示模式给出的候选」
- `static/index.html:385` 「这是演示稿（未配置 AI 接口时的内置模板）」

选题行的来源标签在 `static/index.html:319`，只给种子选题加「· 种子选题」，没有「AI 扩题」来源字样。`static/index.html:116` 的标题「AI 扩题」与 `README.md:9` 的功能名一致，是功能标题。

### 9. TASK-072 演示正文超限返回 400 — 已修

`app.py:33` `BODY_LIMIT = 1000`。未配置密钥时 `app.py:350-355` 在正文超过 1000 字时 `raise HTTPException(400, ...)`，不返回截断稿。

正常三套语气：checklist 281 字、experience 233 字、pitfall 221 字，都是 `demo True`、HTTP 200。把 900 字选题塞进模板后：`400 {"detail":"演示稿正文 1175 字，超过 1000 字上限"}`。

### 10. TASK-072 标题或标签超限返回 502 — 已修

`app.py:371-373` 任一标题超过 20 字即 502。`app.py:383-385` 任一标签超过 `TAG_LIMIT`（`app.py:35` 为 20）即 502。超限项不会被丢掉后继续返回 200。

复现（`llm_chat` 打桩，密钥只在复现进程的环境变量里，没有打外网）：一条超长标题夹在短标题中间，`502`，detail 含「标题超过 20 字」。一条 22 字标签夹着正常标签，`502`，detail 含「标签超过 20 字」。仓库内已有用例 `tests/test_app.py:193`、`207` 覆盖超长标题和超长正文，都在本次 32 项通过里。

### 11. TASK-072 无效 topic 返回 400 — 已修

`app.py:875-880`：`topic_id` 在库里查不到就 `HTTPException(400, "选题不存在")`。

复现：`topic_id` 999999 → `400 {"detail":"选题不存在"}`；`topic_id` 为 `"abc"` → 同样 400。不带 `topic_id` 可以建草稿，返回 200。

### 12. TASK-072 封面路径取 basename — 已修

渲染时 `app.py:530`：`MEDIA_DIR / "covers" / Path(draft["cover_file"]).name`。上传落盘名是 `{draft_id}.png|jpg`（`app.py:999-1000`），不用用户原始路径。

复现：数据库里 `cover_file` 写成工作目录下一张绿色 PNG 的绝对路径；`covers` 目录里放同名红色 PNG。渲染后面中心像素 `(255, 0, 0)`，用的是目录内 basename，没有打开外面的绿图。

### 13. TASK-072 模板避开「第一」 — 已修

演示稿模板在 `app.py:280-329`，三套语气的标题、正文、标签都不含「第一」「最佳」「100%」。给模型的约束写在 `app.py:362`（不要使用这类极限词）。

复现三个 tone 的 `needle_hits` 都是 `[]`。违禁词表里的「第一」仍用于自查（`data/banned_words.json`），live 检查点「违禁词自查命中第一」通过。

### 14. TASK-072 NOTES / README 写实 — 已修

`NOTES.md:22-23` 写运行时五个包，并点出 python-multipart。`requirements.txt` 五行就是 fastapi、uvicorn、python-multipart、httpx、pillow。

`NOTES.md:35-37` 的字体顺序与 `app.py:397-405`、`README.md:94-99` 一致。`README.md:55-56`、`62-63` 先装 `requirements.txt` 再装 `requirements-dev.txt`，`README.md:68` 又写了一遍这个顺序。第 70–71 行的 32 项和 16 个检查点与本次命令输出一致。

`NOTES.md:20` 的「2 核 / 约 7.7G / Python 3.12」是云端环境自述，本机是 Python 3.11.9，未再核实那组机器数字。

## 遗留风险

本轮只记录，没有改仓库。

**P1。测试里有假密钥字符串。** `tests/test_app.py:173`、`194`、`208` 写着 `sk-test-not-real`，用来把 `NOTEPRESS_LLM_API_KEY` 设成非空，同时 monkeypatch 了 `llm_chat`。专项要求测试里不得出现假 key。`DECISIONS.md:35-37` 把这项标成不采纳（不许改测试）。三笔提交没有声称删掉它，所以不计入上面的「未修」。演示模式路径不读这个字符串；本次 pytest 与 live 都是在未设置该环境变量时跑的。

专项抽查（其余项与本次命令、文件一致）：

- 无密钥全流程：上面 pytest 与 live 的输出。`app.py:235-236`、`242` 密钥只读环境变量。源码里没有写死的可用 key。
- 体积与字体：工作区扫描 `OVER_2MB 0`，最大文件 103113 字节（gitignore 的 pyc）。`git ls-files` 14 个路径，无 ttf/otf/woff/woff2/ttc。本机成卡字体是微软雅黑，缺失时 `app.py:427-434` 退回 `ImageFont.load_default()`，`README.md:103` 写了这条降级。
- 渲染断言：`tests/test_acceptance.py:122-150` 固定标题/正文/标签，断言 PNG 存在、500 字节到 2MB、1080×1440、3:4、外缘无墨点；有字体时标题区有墨。该测试在 32 项通过里。没有像素级哈希。
- 规格：`README.md:11-15` 与 `app.py:32-38` 一致（标题 20、正文 1000、标签最多 10 个且每个 20 字、卡片 1080×1440，不做 9:16）。封面最多画前 4 个标签，见 `app.py:566`。
- 溯源：`LICENSE:3-4` 有两条上游版权行；`UPSTREAM.md` 两组四字段齐全。source_commit 未联网核对。

已修 14 / 未修 0 / 无法判定 0
