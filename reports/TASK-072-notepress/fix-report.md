# notepress 修复记录

结论：review.md 的 P0、P1 都是「无」。没有改仓库源码。P2 按任务要求不修。

## 未改的项

### P0

无条目。pytest、live_selftest、8000 端口首页和健康检查在审查阶段已经跑通，见 review.md「本地跑通记录」。没有需要修的阻断项。

### P1

无条目。删除草稿后的卡片、编辑后的导出、封面大小、未登录访问都在探针里核对过，现有实现已经挡住。不新增改动。

### 修不动或本次不修

- P2-3 假 key：tests/test_app.py:173、test_app.py:194、test_app.py:208 的 `sk-test-not-real`。修法是删掉测试里的假密钥字符串。任务禁止改测试文件，所以不动。
- 其余 P2（界面「示例模式」、演示稿超长正文、模型标题被静默丢掉、NOTES 依赖与字体顺序、选题 maxlength、不会出现的「AI 扩题」标签、requirements-dev 未包含运行时包、无效 topic_id 触发 IntegrityError）不在 P0/P1 范围内，按「最多修 P0/P1、宁可少修」不改。

没有对 LICENSE、UPSTREAM、requirements 里的版本号、测试断言做任何修改。

## 最终全量测试

源码未改之后重跑。命令在仓库根目录执行，`NOTEPRESS_LLM_API_KEY` 置空：

```
E:\muse-bridge\work\TASK-072-notepress\venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

真实输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-072-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-072-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.24s
```

退出码 0。32 项通过。警告来自依赖里的 `fastapi\testclient.py`，不是本仓库。没有失败项。

live_selftest 在审查阶段已是 `ALL PASS · 16 个检查点`。之后没有改代码，没有再跑第二遍。

## git status --porcelain

在 `E:\muse-bridge\in\TASK-072-notepress` 执行的命令与标准输出原样如下（退出码 0，标准输出为空，没有任何文件名）：

```
git status --porcelain
```

空输出是因为本次没有修改仓库文件，不是改动丢失。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`。
