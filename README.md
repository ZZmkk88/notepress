# notepress · 笔记工坊

给个人新号用的小红书图文内容工作台：选题 → AI 写稿 → 排版成图 → 草稿管理 → 导出发布包人工发布。
设计上学习了开源社区同类工具的通行思路，代码为独立实现。

## 功能清单（均已实测）

- 登录：单用户，登录令牌 24 小时有效；默认账号见下方，首次登录会提示改密（只提示、不强制）
- 选题库：手动记选题、删选题；给一个方向词可生成一批候选选题（接了 AI 接口时由 AI 扩题）
- AI 写稿：选一个选题，生成 3 个标题候选 + 正文 + 话题标签；三套语气（干货清单 / 亲身体验 / 避坑故事）；
  标题 20 字、正文 1000 字按平台规矩硬校验，超限明确报错不截断
- 演示模式：没配 AI 接口密钥时，用内置模板生成标注清楚的示例稿，全流程照样可跑
- 图文成卡：把标题和正文排成 3:4（1080×1440）卡片图，封面卡 + 内容分页卡，三套配色模板；
  也可以上传自己的图片当封面。不做 9:16。话题标签最多 10 个，每个不超过 20 字；
  封面底部最多画出前 4 个，单行放不下会换行、底对齐在页脚上方，不画出卡片外
- 违禁词自查：内置常见违禁/极限词表，编辑时一键自查、命中标出；词表可在设置页增删
- 草稿箱：草稿增删改查，状态流转（草稿 → 待发布 → 已发布），已发布可回填笔记链接
- 发布包导出：一键导出「按顺序编号的图片 + 文案 .txt」的 zip，拿去人工发布

不做：自动发布、自动点赞/评论/关注、多账号、爬虫、视频。

## 快速开始

默认账号：`admin` / `admin123`（首次登录后请到设置页改密；只提示不强制）

不设置 `NOTEPRESS_LLM_API_KEY` 就是演示模式：选题扩写和写稿用内置模板，响应里 `demo` 为 true，不会请求大模型。密钥只放在这个环境变量里，不要写进仓库。

默认只监听 `127.0.0.1`，端口 `8000`（用环境变量 `PORT` 修改）。

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后打开 http://127.0.0.1:8000

## 测试

不需要 API key。自动化测试在演示模式下运行，并断言不会调用 `httpx.post`。

```bat
pip install -r requirements-dev.txt
python -m pytest tests\ -q -p no:cacheprovider
python tests\live_selftest.py
```

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:cacheprovider
python tests/live_selftest.py
```

`tests/test_app.py`（25 项）+ `tests/test_acceptance.py`（7 项）共 32 项；
真实流程自测 16 个检查点（起真服务走完 选题→写稿→草稿→成卡→导出 全流程）。

覆盖：登录与会话、选题扩写、写稿（打桩与演示模式）、标题 20 字 / 正文 1000 字上限、
违禁词命中、成卡 1080×1440 与文字不溢出、缺字体降级、封面上传、发布包 zip。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| NOTEPRESS_HOST | 127.0.0.1 | 监听地址。默认只监听本机；要对外放开先改掉默认密码再改这个值 |
| PORT | 8000 | 监听端口 |
| NOTEPRESS_DB | ./notepress.db | 数据库文件路径 |
| NOTEPRESS_MEDIA | ./media | 卡片与封面图的存放目录 |
| NOTEPRESS_BANNED_WORDS | ./data/banned_words.json | 违禁词表文件 |
| NOTEPRESS_LLM_API_KEY | （空） | AI 写稿的接口密钥；为空时走演示模式。只放本地环境变量，不要写进任何文件提交 |
| NOTEPRESS_LLM_BASE_URL | https://api.deepseek.com/v1 | OpenAI 兼容接口地址 |
| NOTEPRESS_LLM_MODEL | deepseek-chat | 写稿模型名 |
| NOTEPRESS_FONT_PATH | （空） | 指定成卡用的字体文件路径；为空时按系统回退链查找 |

## 字体说明

成卡只用系统字体。仓库不提交 ttf、otf、woff、woff2。查找顺序：

1. 环境变量 `NOTEPRESS_FONT_PATH`（字体文件完整路径）
2. Linux Noto Sans CJK：`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，粗体 `NotoSansCJK-Bold.ttc`
3. Linux 文泉驿正黑：`/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`
4. Windows 微软雅黑：`C:/Windows/Fonts/msyh.ttc`，粗体 `C:/Windows/Fonts/msyhbd.ttc`
5. macOS 苹方：`/System/Library/Fonts/PingFang.ttc`
6. macOS 华文黑体：`/System/Library/Fonts/STHeiti Medium.ttc`

前面的文件不存在就继续往后找。Windows 上通常用到微软雅黑，macOS 上是苹方或华文黑体，Linux 上是 Noto Sans CJK 或文泉驿正黑。Linux 缺少中文字体时，安装发行版里的 `fonts-noto-cjk`。Noto 的 `.ttc` 取第一个字形面，个别汉字可能偏日文字形，可以把 `NOTEPRESS_FONT_PATH` 指到简体字体。

若一条都找不到，退回 Pillow 的 `ImageFont.load_default()`。这时仍然输出 1080×1440 的 PNG，但该位图字体没有中文字形，不能当正式卡片。装上表中的任一系统字体，或设置 `NOTEPRESS_FONT_PATH`。

## 使用节奏建议

新号建议每天发 1–2 篇即可；AI 生成的内容发布时请按平台要求做好 AI 标识；
发之前用工具里的违禁词自查过一遍。

## 目录

- app.py —— 后端（接口、写稿、成卡、导出都在这一个文件）
- static/index.html —— 单页前端
- data/banned_words.json —— 违禁词表
- tests/ —— 自动化测试与真实流程自测
- NOTES.md —— 调研与取舍记录
- UPSTREAM.md —— 设计参考来源与许可证溯源
- DECISIONS.md —— 本项目的决定记录
