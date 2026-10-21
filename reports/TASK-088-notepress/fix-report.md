# notepress 修复记录

只改了审查清单里的 P1-1。P0 没有。P2 未改。

## P1-1 演示写稿可以返回超限正文

- 问题编号：P1-1
- 文件：`app.py:350-357`（原 `app.py:351-352` 直接 `return demo_generate(...)`）
- 改法：未配置密钥时仍用内置模板，返回前对每个标题和正文调用已有的 `validate_title_body`。超过 20 字或 1000 字时 HTTP 400，详情带上限和当前字数，不截断正文。正好 1000 字仍允许。

验证命令：

```
E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-088-notepress\probe_fix_p1.py
```

真实输出：

```
SHORT 200 demo True body_len 284
EDGE722 200 body_len 1000
OVER723 400 {"detail":"正文超过上限 1000 字（当前 1001 字）"}
LONG800 400 {"detail":"正文超过上限 1000 字（当前 1028 字）"}
```

短选题「用AI写周报」仍是演示模式，正文 284 字。选题 722 字时正文正好 1000，返回 200。723 字与亲身体验 800 字返回 400。

## 未改项

- P0：无。
- P2-1 至 P2-3、P2-5 至 P2-9：清单里的加固项，本次只修 P0/P1，没有改。
- P2-4 假密钥 `sk-test-not-real`（`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208`）：修不动。本任务禁止改测试文件。该字符串只用于打桩，`llm_chat` 被替换，不会发出真实请求。

## 全量测试

命令：

```
E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-088-notepress\run_pytest.py
```

结果行：

```
32 passed, 1 warning in 14.89s
```

警告仍是 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 没有失败用例。`KEY_SET False`。

同一轮还跑了真实流程自测（端口 8156）：

```
ALL PASS · 16 个检查点
LIVE_EXIT 0 SECONDS 2.11
```

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-088-notepress status --porcelain
```

输出：

```
 M app.py
```
