# notepress 修复报告

结论：审查清单里没有 P0，没有 P1。未改仓库源码，没有顺手改文档或测试。下面按清单编号说明。收尾重跑了 pytest 与 `tests/live_selftest.py`，结果仍是通过。

## 问题编号与处理

### P0

无条目。没有「跑不起来 / 阻断」项。

### P1

无条目。安全、数据、权限方面没有本轮要改的缺陷。默认口令、Pillow 像素上限、Windows 封面文件锁的核对写在 `review.md` 的 P1 节，结论是不改。

### P2（本轮不修）

P2-1。文件：`README.md:71`。改法：把「7 项 / 共 32 项」改成「9 项 / 共 34 项」。不修原因：文档计数错误，不阻断运行，不属于 P0/P1。

P2-2。文件：`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208`。改法：去掉假 key 字面量 `sk-test-not-real`。不修原因：禁止修改测试文件。这是测试桩里的假 key，请求被 `llm_chat` 打桩拦住，不会发到真实接口。

P2-3。文件：`app.py:401`（对照 `app.py:875-876`）。改法：AI 标签超过 10 个时返回 502，不再切片丢弃。不修原因：演示模式与现有用例都不走这条；属于两条接口口径不一致，不是阻断，也不是已发生的数据损坏。

P2-4。文件：`app.py:389-402`（对照 `README.md:10`）。改法：合规标题不足 3 条时返回 502。不修原因：演示模式实测始终返回 3 条，现有测试是绿的，不属于 P0/P1。

P2-5。文件：`index.html:53`、`index.html:365-368`、`index.html:444-447`。改法：让超限字数样式真正命中计数节点。不修原因：只影响红色提示，服务端仍按 20/1000 返回 400。

P2-6。文件：`index.html:470-476`。改法：保存失败时停止渲染。不修原因：超限正文不会写入草稿，属于提示不准确，不是数据写坏。

P2-7。文件：`requirements.txt`（警告来自已安装的 fastapi/starlette TestClient）。改法：不升级、不改版本号。不修原因：任务禁止改已有依赖版本，除非依赖冲突。本次安装没有冲突，测试通过。

P2-8。文件：`LICENSE:3`、`UPSTREAM.md:10`。改法：不改。不修原因：禁止在未证实事实错误时改 LICENSE / UPSTREAM。本次不能访问外网核对 commit，不能判定版权行是错的。

## 验证

没有代码改动，因此没有「逐项改完再跑」的中间测试。收尾按 README 重跑全量自动化测试和真实流程自测。

命令（工作目录 `E:\muse-bridge\in\TASK-105-notepress`）：

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-105-notepress\pytest-tmp2
```

输出：

```text
..................................                                       [100%]
============================== warnings summary ===============================
..\..\work\TASK-105-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-105-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 16.90s
```

退出码 0。34 项通过。唯一警告是依赖里的 `StarletteDeprecationWarning`，没有失败项。

```text
E:\muse-bridge\work\TASK-105-notepress\venv\Scripts\python.exe tests\live_selftest.py
```

输出：

```text
  PASS health 200
  PASS 登录成功
  PASS 首次登录提示改密
  PASS 种子选题已预置
  PASS AI 扩题（演示模式）
  PASS 生成稿件（演示模式标注示例稿）
  PASS 标题合规 ≤20 字
  PASS 正文合规 ≤1000 字
  PASS 存入草稿箱
  PASS 违禁词自查命中「第一」
  PASS 生成卡片 ≥2 张
  PASS 封面卡是 PNG
  PASS 导出发布包
  PASS 发布包含编号图片+文案
  PASS 文案内容对得上
  PASS 状态流转到已发布并回填链接

ALL PASS · 16 个检查点
```

退出码 0。无密钥，16 个检查点通过。没有失败需要归因。

## git status

收尾命令（工作目录 `E:\muse-bridge\in\TASK-105-notepress`）：

```text
git status --porcelain
```

输出原样（退出码 0，没有任何行）：

```text

```

空输出是预期：清单没有 P0/P1，仓库源码、测试、README、LICENSE、UPSTREAM 都没有改。没有需要找回来的改动。
