# notepress 修复记录

只改 review.md 里 P1-1、P1-2、P1-3。没有改测试，没有改依赖版本，没有改 LICENSE / UPSTREAM（这两份文件原本不存在）。

## P1-1 扩题与违禁词的 HTML 注入

文件：`static/index.html:338-352`（扩题列表）、`static/index.html:523-535`（违禁词列表）。

改法：不再用 `innerHTML` 拼接 `onclick`。候选标题用 `textContent`，违禁词用 `createTextNode`，点击用 `addEventListener` 调用 `window.addCandidate` / `window.delWord`。

验证命令：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-055-notepress\verify_p1_1.py`

退出码：0

输出：
```
SOURCE_OK
INDEX 200 text/html; charset=utf-8
SERVED_HAS_LISTENER True
SERVED_UNSAFE_EXPAND False
SERVED_UNSAFE_WORD False
SERVED_TEXTNODE True
SERVER_STOPPED True
```

源码中已不存在 `JSON.stringify(c)`、`onclick='addCandidate`、`onclick="delWord(`。首页 200 且下发的就是这份脚本。本环境没有浏览器自动化工具，没有在真实页面里点「生成候选 / 删除违禁词」。服务已退出。

## P1-2 封面标签画出卡片

文件：`app.py:456-472` 新增 `fit_line`；`app.py:531-541` 画标签前去掉 emoji，并按 `CARD_W - 168` 收成一行。

改法：超宽标签加省略号，不再从 x=84 一直画到画布外。

验证命令：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-055-notepress\verify_p1_2.py`

退出码：0

输出：
```
LONG_SIZE (1080, 1440) TAG_PIXELS 12662 PAST_X1000 0 FILES ['card_1.png', 'card_2.png']
DETERMINISTIC True
RAW_PX 1944.0 SHOWN #标签一二三四五六七八九十  #测测测测测测测… SHOWN_PX 910.0 MAX 912
SHORT_UNCHANGED True SHORT_PX 852.0
EMOJI_ONLY_TAG_PIXELS 0 EMOJI_PAST 0
EMOJI_SANITIZE 测试工具
BODY_EDGE 0 BODY_SIZE (1080, 1440)
PASS True
```

同一输入渲染两次，像素一致。超长标签宽 910 ≤ 912，x≥1000 的标签带像素为 0。短标签不截断。纯 emoji 标签不画出豆腐块。正文卡尺寸 1080×1440，左右边缘无非背景像素。

## P1-3 超过 10 个标签被静默丢掉

文件：`app.py:813-815`。

改法：唯一标签个数超过 `MAX_TAGS`（10）时返回 400，正文为 `标签超过上限 10 个（当前 N 个）`。重复项和 `#` 前缀仍先清洗，不计入重复。单标签超过 20 字的原有 400 保留。

验证命令：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-055-notepress\verify_p1_3.py`

退出码：0

输出：
```
LOGIN 200 must_change True
TAGS11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
TAGS10 200 {"id":1}
STORED10 10 ['标签0', '标签1', '标签2', '标签3', '标签4', '标签5', '标签6', '标签7', '标签8', '标签9']
DEDUP 200 {"id":2}
DEDUP_STORED 10 ['标签0', '标签1', '标签2', '标签3', '标签4', '标签5', '标签6', '标签7', '标签8', '标签9']
UPDATE11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
UPDATE10 200 {"ok":true}
UPDATE_STORED 10 ['改0', '改1', '改2', '改3', '改4', '改5', '改6', '改7', '改8', '改9']
TAG21 400 {"detail":"标签超过上限 20 字（当前 21 字）"}
PASS True
```

第一次执行时 TestClient 没有走进 lifespan，报 `sqlite3.OperationalError: no such table: users`。那是验证脚本的用法问题，不是业务代码。补上进入应用生命周期后，上面这条退出码为 0。

## 全量测试（修复后）

命令（工作目录 `E:\muse-bridge\in\TASK-055-notepress`）：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -B -m pytest --collect-only`

退出码：1

输出：
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: E:\muse-bridge\in\TASK-055-notepress
plugins: anyio-4.15.1
collected 0 items

========================= no tests collected in 0.01s =========================
```

失败原因：仓库里没有测试文件，pytest 收集到 0 条。修复前就是这个结果。没有改测试、没有加 skip。这不是外网限制。

修复后的无密钥全流程（`httpx.post` 已换成会抛 `BLOCKED_NETWORK_POST` 的桩，未触发）：

命令：
`E:\muse-bridge\work\TASK-055-notepress\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-055-notepress\probe_final.py`

退出码：0

输出：
```
LLM False
SERVER_STARTED True port 8000
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 loginView True
LOGIN 200 user admin must_change True
EXPAND 200 demo True n 6
GENERATE 200 demo True titles [17, 15, 16] body_len 296
DRAFT 200 {"id":1}
RENDER 200 {"cards":["/api/drafts/1/cards/1","/api/drafts/1/cards/2","/api/drafts/1/cards/3"],"count":3}
CARD 200 (1080, 1440) bytes 66829
EXPORT 200 ['01.png', '02.png', '03.png', '文案.txt']
TAGS11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}
SERVER_STOPPED True
OVERFLOW (1080, 1440) past 0 shown_px 910.0 files ['card_1.png', 'card_2.png'] exists True
NETWORK_BLOCK_ARMED True
PASS True
```

服务已退出。P2 未改：README 仍是 0 字节，仍无测试、无 LICENSE、无 UPSTREAM.md，示例稿仍会命中「第一」，默认口令仍是 admin123。

## git status

命令：`git status --porcelain`

输出：
```
 M app.py
 M static/index.html
?? __pycache__/
```

`app.py` 与 `static/index.html` 仍在工作区。`__pycache__/` 是修复前导入 `app.py` 生成的字节码，不是清单里的改动，没有删除。`git diff --stat`：`app.py` 34 行、`static/index.html` 33 行。
