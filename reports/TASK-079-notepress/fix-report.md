# notepress 修复记录

结论：`review.md` 分级清单里的 P0、P1 都是空的。没有改仓库源码，也没有改测试、依赖版本、`LICENSE`、`UPSTREAM.md`。P2 共 15 条，按任务只修 P0/P1，所以未动。

## 条目

无 P0、无 P1 条目。下面没有「问题编号 / 文件:行号 / 改法」的代码改动。

修不动的相关项（不是 P0/P1，写在这里避免看起来像漏修）：

- P2-14 `tests/test_app.py:173`、`:194`、`:208` 的字符串 `sk-test-not-real`。任务禁止改测试，未改。该字符串只配合 monkeypatch，pytest 未出网。
- `LICENSE`、`UPSTREAM.md` 未改。上游 commit 未联网核实，没有确凿事实错误。

## 全量测试（审查结束后重跑）

命令（仓库根目录，空 API key，不写 pytest 缓存）：

```
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set PYTHONPYCACHEPREFIX=E:\muse-bridge\work\TASK-079-notepress\pycache
set TEMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set TMP=E:\muse-bridge\work\TASK-079-notepress\tmp
set NOTEPRESS_LLM_API_KEY=
E:\muse-bridge\work\TASK-079-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-079-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-079-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.35s
```

32 项通过。警告来自依赖里的 TestClient，没有失败项。

## git status --porcelain

这条和上面的 pytest 在同一次命令里执行，porcelain 在 `GIT_STATUS_DONE` 之前没有任何行：

```
cd /d E:\muse-bridge\in\TASK-079-notepress && git status --porcelain && echo GIT_STATUS_DONE
```

```
GIT_STATUS_DONE
```

工作区是空的。原因是本轮没有改仓库文件，不是改动被还原。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`。

收尾单独再执行一次（在仓库根目录）：

```
git status --porcelain
```

输出为空（exit 0，无行）。与上面一致。
