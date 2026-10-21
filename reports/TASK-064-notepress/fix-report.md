# notepress 修复记录

只修 review.md 分级清单里的 P1。P2 不改。测试文件未改。

## P1-1 编辑后导出仍用旧卡片

问题：改标题后导出，`01.png` 仍是旧图，`文案.txt` 已是新标题。

文件与行号：

- `app.py:481-491` 新增 `clear_card_files`，删除该草稿的 `card_*.png`。
- `app.py:887-908` 更新草稿时，标题、正文、标签或模板有变化才清卡片。只改状态不清。
- `app.py:984` 封面上传成功后清卡片。
- `app.py:1038` 导出改为始终 `render_cards(draft)`，不再复用磁盘上的旧图。

改法：导出按当前数据库里的草稿重画；内容或封面变了就先删旧卡，避免预览继续显示上一版。

验证命令：

```
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-p11
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-064-notepress\verify_p1_1.py
```

真实输出：

```
25 passed, 1 warning in 10.14s
UPDATE 200
CARD_CLEARED True
EXPORT 200
PNG_CHANGED True
TEXT_NEW True
TEXT_OLD False
STATUS_ONLY 200
STATUS_KEEPS_CARD True
```

改标题后旧卡被删，导出的 PNG 与旧图哈希不同，文案只有新标题。只改状态时卡片保留。原有 25 项测试仍通过。警告仍是 FastAPI TestClient 的 StarletteDeprecationWarning。

## P1-2 删除草稿后卡片仍可下载

问题：删除接口只删数据库行，卡片文件还在，下载接口不检查草稿是否存在。

文件与行号：

- `app.py:494-502` 新增 `clear_cover_files`，删除 `{id}.png`、`{id}.jpg` 以及记录里的封面文件名（只取文件名，不跟路径）。
- `app.py:913-922` `delete_draft` 在删除行之后调用 `clear_card_files` 和 `clear_cover_files`。
- `app.py:947-951` `get_card` 先查草稿，不存在则 404「草稿不存在」，不再只看文件在不在。

改法：删除草稿时同步删卡片和封面；即使有人把图片文件放回去，没有草稿行也不再提供下载。

验证命令：

```
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-p12
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-064-notepress\verify_p1_2.py
```

真实输出：

```
25 passed, 1 warning in 10.37s
COVER 200 {'ok': True, 'cover_file': '1.png'}
RENDER 200 2
BEFORE True True
DELETE 200
AFTER_CARD False AFTER_COVER False
GET_AFTER_DELETE 404 草稿不存在
GET_ORPHAN_FILE 404 草稿不存在
```

删除后卡片和封面文件都不在。把卡片文件手动放回原路径，下载仍是 404。原有 25 项测试仍通过。

## P1-3 封面上传超限仍整包读入内存

问题：`await file.read()` 不带长度，10MB 判断发生在整包进入 `raw` 之后。

文件与行号：`app.py:961-967`。

改法：先看 `file.size`，大于 10MB 直接 400，错误里带当前大小，此时不调用 `read`。`size` 不可用时最多 `read(10MB+1)`，多出来的 1 字节即拒绝。正好 10MB 仍进入原来的图片解码。

残留：Starlette 在进入处理函数之前仍会把文件部件写入临时文件。这一步在依赖库里，没有改依赖版本。本修复去掉的是超限后再复制进 `raw` 的那一次整包内存占用。

验证命令：

```
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-p13
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-064-notepress\verify_p1_3.py
```

真实输出：

```
25 passed, 1 warning in 10.54s
SMALL 200 {"ok":true,"cover_file":"1.png"}
OVER 400 {"detail":"图片超过上限 10MB（当前 10.0MB）"}
EXACT 400 {"detail":"这不是一张能打开的图片"}
```

超限走的是带「当前」的 size 分支。正好 10MB 的非图片被解码拒绝，没有被当成超限。小图仍 200。原有 25 项测试仍通过。

## 全量重跑

三条 P1 都落地之后再跑一遍。未改测试，未改 requirements 版本，未改 LICENSE / UPSTREAM。P2 未动。

命令：

```
set TEMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-064-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
set HTTP_PROXY=http://127.0.0.1:9
set HTTPS_PROXY=http://127.0.0.1:9
set NO_PROXY=127.0.0.1,localhost
cd /d E:\muse-bridge\in\TASK-064-notepress
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-final
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe tests\live_selftest.py 8156
```

真实输出：

```
25 passed, 1 warning in 10.27s
ALL PASS · 16 个检查点
```

没有失败项。警告仍是 FastAPI TestClient 的 StarletteDeprecationWarning，与改动前相同。

## git status

命令（工作目录 `E:\muse-bridge\in\TASK-064-notepress`）：

```
git status --porcelain
```

输出：

```
 M app.py
```

`git diff --stat`：`app.py | 58 +++++++++++++++++++++++++++++++++++++++++++++++++++-------`，1 file changed, 51 insertions(+), 7 deletions(-)。改动仍在工作区。
