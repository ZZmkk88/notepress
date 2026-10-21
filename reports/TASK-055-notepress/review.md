# notepress 验收审查

结论：依赖能按 `requirements.txt` 装上，无 API key、且阻断 `httpx.post` 时，选题扩写、示例文案、1080×1440 卡片、导出 zip 都能跑完。`/health` 与 `/` 在 `127.0.0.1:8000` 返回 200，服务已关掉。pytest 收集 0 条，退出码 1。README 是 0 字节。无 LICENSE、无 UPSTREAM.md。没有 P0。本次按清单修 3 个 P1（见文末）。

审查时提交为 `ebdb9b8a389e3cf49004a8d02677b318fcd19c15`（作者 ZZmkk88，说明 `feat(notepress): 单页前端工作台（选题库/写稿台/草稿箱/设置）`）。工作区当时干净。证据命令在 `run.md`。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境 `E:\muse-bridge\work\TASK-055-notepress\venv`。数据库、媒体、违禁词副本都在该 work 目录，没有写进仓库。

安装：

```
python -m venv E:\muse-bridge\work\TASK-055-notepress\venv
...\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

退出码 0。装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。没有依赖冲突，没有改版本号。

测试：

```
...\python.exe -m pytest --collect-only
```

退出码 1。原文：

```
collected 0 items
========================= no tests collected in 0.01s =========================
```

仓库跟踪文件只有 README.md、app.py、data/banned_words.json、requirements.txt、requirements-dev.txt、static/index.html。没有测试模块，所以没有「全绿」的测试结果。这不是外网失败，不标环境限制。

服务（脚本 `probe_flow.py`，无 `NOTEPRESS_LLM_API_KEY`，`httpx.post` 被换成会抛错的桩）：

```
SERVER_STARTED True port 8000
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 ... has_login True ctype text/html; charset=utf-8
ME_NOAUTH 401 {"detail":"未登录"}
LOGIN 200 {"username":"admin","must_change":true}
EXPAND 200 ... "demo":true
GENERATE_STATUS 200
GENERATE_DEMO True ... body_len 296 ... hits [{'word': '第一', 'in_title': 0, 'in_body': 1}]
CREATE_DRAFT 200 {"id":1}
RENDER 200 ... "count":3
CARD_SIZE card_1.png (1080, 1440) RGB
GET_CARD1 200 image/png
EXPORT 200 application/zip
ZIP_NAMES ['01.png', '02.png', '03.png', '文案.txt']
CARD_NOAUTH 401
SERVER_STOPPED True
```

未出现 `BLOCKED_NETWORK_POST`，说明示例模式没有调用大模型。登录令牌已从记录里截断。服务在同一进程内退出。

像素与越权（`probe_pixels.py`，退出码 0）：正文卡左右最外 3 像素无非背景点；封面标签区（y=1100–1359，x≥996）有 1736 个非背景像素；标签行 `textlength` 1944，安全宽度 912。未登录访问草稿列表、渲染、上传封面均为 401。

## README 与实际不符处

`README.md` 长度为 0 字节，没有任何句子。下面每条都是「文档没写或与代码不一致」。

1. `README.md` 无内容。启动代码在 `app.py:989-994`：`python app.py` 走 uvicorn，`NOTEPRESS_HOST` 默认 `127.0.0.1`，`PORT` 默认 `8000`。文档没有安装和启动步骤。实测只能靠 `requirements.txt` 和源码把服务跑起来。
2. 依赖不在 README。运行依赖是 `requirements.txt:1-5`（fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0）。开发依赖是 `requirements-dev.txt:1`（pytest==9.1.1）。
3. 模拟模式不在 README。未设置 `NOTEPRESS_LLM_API_KEY` 时 `app.py:235-236` 的 `llm_configured()` 为假，扩题走 `app.py:333-334`，写稿走 `app.py:351-352`，文案来自 `app.py:280-329`。实测 `LLM_CONFIGURED False` 且 `demo:true`。
4. 标题上限不在 README。常量 `app.py:32` `TITLE_LIMIT = 20`，校验 `app.py:625-626`。前端计数在 `static/index.html:160` 与 `static/index.html:163`。实测 21 字返回 400：`标题超过上限 20 字（当前 21 字）`。
5. 正文上限不在 README。常量 `app.py:33` `BODY_LIMIT = 1000`，校验 `app.py:627-628`，前端 `static/index.html:163`。同一文件的模型提示词 `app.py:357` 写「正文不超过 950 字」，和常量 1000 不一致。
6. 标签规则不在 README。`app.py:35` 单标签最多 20 字，`app.py:36` `MAX_TAGS = 10`。`app.py:787` 把超出的标签直接丢掉，不返回错误。实测提交 11 个标签，响应 200，库存 10 个。
7. 封面比例不在 README。`app.py:38` `CARD_W, CARD_H = 1080, 1440`（注释写 3:4）。没有 9:16。实测三张 PNG 都是 1080×1440。
8. 系统字体和降级不在 README。候选在 `app.py:388-395`：Noto Sans CJK、文泉驿正黑、`C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`、苹方、华文黑体。找不到时 `app.py:425` 使用 `ImageFont.load_default()`。本机实测命中 `C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`。仓库内没有字体文件。
9. 默认账号不在 README，登录页也不提示。`app.py:145` 写入用户 `admin`、口令 `admin123`。`static/index.html:101` 写「不改也能正常用」。`static/index.html:74-80` 只有空的用户名和密码框。
10. 选题长度前后端不一致。输入框 `static/index.html:111` `maxlength="120"`。后端 `app.py:34` 与 `app.py:707-708` 上限 100。实测 101 字返回 400，100 字返回 200。
11. 扩题字数提示没有落地。`app.py:337` 要求模型「每个不超过 40 字」。`app.py:267-277` 的 `demo_expand` 和 `app.py:340-347` 的返回值都不按 40 字截断。
12. README 没写怎么跑测试。`requirements-dev.txt:1` 有 pytest，但仓库没有测试文件，`pytest --collect-only` 收集 0 项。没有「固定输入 → 期望输出」的断言。

## 许可证与署名核查

- 仓库根目录没有 `LICENSE`，没有 `UPSTREAM.md`。`git ls-tree -r --name-only HEAD` 的 6 个文件里没有这两份。
- `app.py:1-5` 只有功能说明，没有版权行，没有上游项目名、`source_url`、`source_commit`。
- `static/index.html`、`data/banned_words.json` 同样没有第三方署名。`banned_words.json` 的 comment 写「来源：广告法极限词与各平台公开规则的通行整理」，没有具体仓库地址或 commit。
- 本地 git：`origin` = `https://github.com/ZZmkk88/notepress.git`，浅克隆，唯一提交 `ebdb9b8a389e3cf49004a8d02677b318fcd19c15`，作者 `ZZmkk88`。这是本仓库自己的 remote，不是 UPSTREAM 四字段。
- 按任务要求没有访问 GitHub 页面，因此不能用网页上的许可证来补结论。
- 结论：本地材料既没有「保留上游版权行」，也没有「独立实现」的明文声明。四字段 `source_url` / `source_commit` / `license` / `attribution` 都不存在。不能在没有依据时新写 LICENSE 或 UPSTREAM 的事实性声明，所以这两份文件不在修复范围内。

体积：上述 6 个文件最大为 `app.py` 38067 字节，`static/index.html` 25969 字节，均小于 2MB。没有 ttf/otf/woff/woff2。

密钥：源码里没有写死的 LLM key。密钥只读 `NOTEPRESS_LLM_API_KEY`（`app.py:236`、`app.py:242`）。默认 base URL `app.py:240` 只在配置了密钥之后才会被 `llm_chat` 使用。无密钥路径已实测跑通。`admin123` 是本地登录口令，不是第三方 API key，见 P2-4。

## 专项验收对照

1. 无密钥可跑通：通过（见上，`demo:true`，网络桩未触发）。自动化测试全绿：不通过，收集 0 条，退出码 1。源码无写死 API key：通过。
2. 单文件体积与禁字体：通过。README 写明字体名和缺字降级：不通过（README 0 字节；降级代码在 `app.py:425`）。
3. 渲染可复现且测试断言文件、尺寸、不溢出：不通过。仓库没有这种测试。本地一次固定输入得到 1080×1440 PNG，但标签行会画出安全区（`TAG_PX 1944` > `912`）。
4. 标题/正文/标签/封面比例以 README 为准：不通过。README 未声明。代码内部还有 950 对 1000、前端 120 对后端 100。
5. 溯源与许可：不通过。见上一节。

## 分级修复清单

### P0

无。服务能起，健康检查和首页正常，无密钥主流程能跑完。pytest 能执行，只是没有用例。

### P1

1. 安全：扩题候选和违禁词被拼进 HTML 事件属性，可执行注入。`static/index.html:339-340` 使用 `onclick='addCandidate(this, ${JSON.stringify(c)})'`，`JSON.stringify` 不转义单引号，方向词前 12 字会进候选标题（`app.py:268-271`）。`static/index.html:511-512` 把 `esc()` 后的词放进 `onclick="delWord('...')"`，`innerHTML` 会把 `&#39;` 解回引号。令牌在 `static/index.html:260` 的 `localStorage`。修法：改成 `textContent` 加 `addEventListener`，不再把不可信字符串拼进 HTML。
2. 数据：封面标签不换行，画出卡片右边界。`app.py:512-515` 把最多 4 个标签画在 x=84。实测字符串宽 1944px，安全宽 912px，标签带越过右边距 1736 像素。正文卡有换行，实测没有越界。修法：画之前按 `CARD_W - 168` 截成一行（放不下加省略号），并先去掉 emoji。
3. 数据：超过 10 个标签被静默丢掉。`app.py:778-787` 末尾 `return tags[:MAX_TAGS]`。实测 11 个标签返回 200，只存前 10 个。修法：超过 `MAX_TAGS` 时返回 400，写明当前个数。

### P2

1. `README.md` 为 0 字节，字体、字数、比例、启动方式都没写。不在本次修改：属于文档，不是跑不通，也不是安全或数据损坏。行号：`README.md` 无内容行；对照 `app.py:32-38`、`app.py:388-425`、`app.py:989-994`。
2. 没有自动化测试，也没有固定样例断言。`requirements-dev.txt:1`。本次不新增测试文件（任务禁止改测试）。
3. 示例稿三条语气都命中违禁词「第一」。`app.py:301`「第一步」、`app.py:313`「第一版」、`app.py:322`「第一版」。`check_banned`（`app.py:222-229`）是子串匹配，只提示不拦截。不改匹配器，避免把真正的「第一」漏掉。
4. 默认口令写死且不强制修改。`app.py:145` 的 `admin123`，`must_change` 不拦截接口；`static/index.html:101` 写明可以不改。默认只绑 `app.py:992` 的 `127.0.0.1`。保持演示登录，不改口令逻辑。
5. 模型提示词正文 950 字（`app.py:357`）与常量 1000（`app.py:33`）不一致。扩题「不超过 40 字」（`app.py:337`）没有强制。前端选题 120（`static/index.html:111`）与后端 100（`app.py:34`）不一致。
6. 无 LICENSE、无 UPSTREAM.md。没有确凿上游材料，不补写事实性声明。

本次只改 P1 的三处：`static/index.html`、`app.py` 的标签绘制、`app.py` 的 `_clean_tags`。
