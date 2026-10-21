# TASK-097 修复记录

只动了审查清单里的 P1-1。P1-2 修不动。P0 没有。P2 没改。

## P1-1 上传封面极端宽高比会放大整图

问题编号：P1-1

文件：`app.py:22`（补 `ImageOps` 导入）；原 `app.py:533-537` 的放大再裁剪，现为 `app.py:532-534`。

改法：上传封面不再按 `max(卡片边/源图边)` 把整图放大后再居中裁。改为 `ImageOps.fit(img, (1080, 1440))`，先在源图上取 3:4 区域，再直接缩放到卡片尺寸。居中方式与原来的中心裁剪一致。800×600 的纯色图中心像素仍是源图颜色。

验证命令与结果：

对应测试（`run_focus.py`，无 API key）：

```
5 passed, 1 warning in 3.77s
```

包含 `test_cover_upload_and_render`、`test_cover_upload_rejects_non_image`、`test_render_fixed_sample_size_and_no_overflow`、`test_long_tags_stay_inside_card`、`test_export_zip`。警告仍是 `StarletteDeprecationWarning: install httpx2 instead`，不是失败。

极端尺寸（`verify_cover.py`，修复前按旧公式 2000×10 会得到 288001×1441 的中间图，这次是改完后实跑）：

```
WIDE UPLOAD 200 {"ok":true,"cover_file":"1.png"} bytes 184
WIDE RENDER 200 {"cards":["/api/drafts/1/cards/1","/api/drafts/1/cards/2"],"count":2} 0.070s
WIDE CARD 200 (1080, 1440) png b'\x89PNG\r\n\x1a\n' bytes 15755
TALL RENDER 200 ... 0.057s
TALL CARD 200 (1080, 1440)
NORMAL CARD 200 (1080, 1440)
NORMAL CENTER (200, 80, 90)
```

2000×10 和 10×2000 都在 0.1 秒内得到 1080×1440 的 PNG。

## P1-2 测试里的假 key

问题编号：P1-2

文件：`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208`，字面量 `sk-test-not-real`。

改法：未改。

修不动的原因：本任务禁止改测试文件（不许改断言、不许加 skip，也不许改测试里的夹具数据）。`git status --porcelain` 只有 `app.py`，测试文件不在改动里。`app.py` 本身只从环境变量读 `NOTEPRESS_LLM_API_KEY`，没有写死密钥。这三条测试把 `llm_chat` 换成了桩，假 key 不会出网。`DECISIONS.md:35-36` 也把这项标成不许改测试。

## 全量测试

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\run_pytest.py`

该脚本在仓库目录执行 `python -m pytest tests -q -p no:cacheprovider --tb=short`，并去掉 `NOTEPRESS_LLM_API_KEY`。

```
32 passed, 1 warning in 14.79s
NOTEPRESS_LLM_API_KEY_SET False
```

退出码 0。没有失败用例。唯一警告是 Starlette 建议改用 httpx2，与本次改动无关，按清单 P2-5 不改依赖版本。

## git status --porcelain

命令：`git status --porcelain`

```
 M app.py
```
