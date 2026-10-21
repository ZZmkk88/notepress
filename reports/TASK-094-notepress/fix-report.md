# notepress 修复报告

结论：review.md 分级清单里 P0 为 0 条、P1 为 0 条。没有修改仓库源码。P2 共 7 条，按任务只修 P0/P1，这些都不改。下面逐条写原因。收尾重跑了全量 pytest，32 项通过。

## 问题编号

### P0

无条目。依据见 review.md「本地跑通记录」：pytest `32 passed`，live_selftest `ALL PASS · 16 个检查点`，`http://127.0.0.1:8000/health` 与 `/` 均为 200。

没有对应的文件改动。

### P1

无条目。认证、SQL 占位符、封面 basename、上传 10MB 限制、密钥只读环境变量、默认绑定 127.0.0.1 已在审查中核对，见 review.md「分级修复清单」P1 段。

没有对应的文件改动。

### P2-1 测试中的假密钥

- 文件:行号：tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208
- 改法（未执行）：删除 `sk-test-not-real` 这三处赋值。
- 未改原因：任务禁止改测试文件、禁止改断言。DECISIONS.md:35-36 已把此项永久关闭。该字符串只用于让 `llm_configured()` 为真，同用例已替换 `llm_chat`（tests/test_app.py:182 等），请求不会发到模型接口。
- 验证：未改代码。全量测试结果见文末。

### P2-2 上传封面不画标签

- 文件:行号：app.py:541-549；声明在 README.md:15；模板封面画标签的实现在 app.py:565-585
- 改法（未执行）：上传封面的暗带按同样规则绘制前 4 个标签。
- 未改原因：P2。主流程已跑通。现有 `test_cover_upload_and_render` 只断言 1080×1440。
- 验证：未改代码。

### P2-3 选题框字数与后端上限不一致

- 文件:行号：static/index.html:111（`maxlength="120"`），app.py:34 与 app.py:777-778（上限 100）
- 改法（未执行）：maxlength 改为 100。
- 未改原因：P2。探针 `TOPIC_101` 已是 400，超长选题不会入库。
- 验证：未改代码。探针输出：`TOPIC_101 400 {"detail":"选题超过上限 100 字（当前 101 字）"}`。

### P2-4 AI 标签超限静默切片

- 文件:行号：app.py:386；对照手填路径 app.py:857-858
- 改法（未执行）：超过 10 个时返回 502，并去掉 app.py:386 的切片。
- 未改原因：P2。无密钥时不进入该分支。改它不影响本次验收的演示模式。
- 验证：未改代码。

### P2-5 AI 标题可以少于 3 条

- 文件:行号：app.py:374-376；声明在 README.md:10
- 改法（未执行）：有效标题不足 3 个时返回 502。
- 未改原因：P2。演示模式探针三种语气都返回 3 条标题。
- 验证：未改代码。

### P2-6 README 对测试的描述过宽

- 文件:行号：README.md:52；对照 tests/test_app.py:173 与 tests/test_acceptance.py:98
- 改法（未执行）：改 README 那一句，写明 3 个用例是打桩。
- 未改原因：P2 文案。测试命令本身按 README 能跑绿。
- 验证：未改代码。

### P2-7 TestClient 弃用警告

- 文件:行号：安装后的 `venv\Lib\site-packages\fastapi\testclient.py:1`（不在仓库源码内）。仓库决定见 DECISIONS.md:36-37。
- 改法（未执行）：改依赖以使用 httpx2。
- 未改原因：任务禁止改 requirements 里已有依赖的版本号，除非是依赖冲突。这里没有冲突，测试退出码为 0。DECISIONS 已关闭此项。
- 验证：未改依赖。警告仍在，见下方 pytest 输出。

## 最终全量测试

命令（工作目录 `E:\muse-bridge\in\TASK-094-notepress`，解释器为 work 目录里的 venv，`NOTEPRESS_LLM_API_KEY` 已从子进程环境移除，临时目录指向 `E:\muse-bridge\work\TASK-094-notepress\tmp`）：

```
python -m pytest tests -q -p no:cacheprovider
```

真实输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-094-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-094-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 14.41s
EXIT 0
ELAPSED_SEC 15.50
```

没有失败项。警告是 P2-7，不计入失败。

## git status

仓库源码没有改动。`git status --porcelain` 为空，因为没有 P0/P1 需要落盘。本次没有执行 `git checkout`、`git restore`、`git stash`、`git clean`。

收尾命令在写完本段后立刻再执行一次，输出附在文件末尾。

## 收尾 git status 原文

```
git -C E:\muse-bridge\in\TASK-094-notepress status --porcelain
```

退出码：0

输出为空（命令没有任何 stdout）：

```
```
