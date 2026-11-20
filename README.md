# AI 视频工作流工程包

把自己的素材和想法交给 Agent，做真人口播、产品短片或音乐 MV。本次将可复用能力整理为 7 个项目 Skill，附本地脚本、Remotion 工程和三套可改提示词。它们不绑定某一家模型，也不要求复刻文章里的片子。

## 第一步：让 Agent 把工程跑起来

下载并解压，用你平时的 Agent 打开本目录，把 `prompts/00-启动.txt` 发给它。Skills 按项目内文件读取，不要求修改全局配置。环境检查、缺项说明与试跑由 Agent 执行。

```text
先读 README.md 和 skills/ai-video-workflow/SKILL.md，使用这个工程里的 7 个视频 Skill。先运行 python3 scripts/env_check.py --task basic，告诉我当前环境缺什么，只安装这次任务需要的依赖。环境就绪后运行 npm ci，再运行 python3 scripts/repro_demo.py talk，检查六秒测试片能解码、有音轨。这个测试片只验证环境。然后根据我接下来提供的任务，检查对应依赖，读取 input/material/ 中的素材，在 runs/ 下新建任务目录，先做一段带声音的预览。原素材不要覆盖，不要上传到代码仓库。
```

| Skill | 做什么 |
| --- | --- |
| `ai-video-workflow` | 统筹视频任务、检查环境并调度工程中的其他视频 Skill |
| `media-understanding` | 整理视频、音频、图片的规格与代表帧，供 Agent 判断画面含义、素材用途和剪辑入点 |
| `speech-transcription` | 把真人口播转成带时间戳和逐词信息的文本，校对术语后交给剪辑 |
| `talking-head-edit` | 按口播语义删留片段，并把字幕、关键词和辅助画面合成可编辑视频 |
| `product-video` | 从产品资料和可追溯素材制作产品短片，包括素材查找、功能分镜和可编辑动效 |
| `music-video` | 分析音乐节拍、对齐歌词并安排镜头与动作，制作短段音乐 MV |
| `video-review` | 检查导出视频的解码、音视频时长和交付完整性，并指导实际观看和试听 |

## 第二步：放自己的素材，选一份提示词

| 任务 | 放入 input/material/ 的内容 | 发给 Agent | 先看什么 |
| --- | --- | --- | --- |
| 真人口播 | 原声视频、讲稿；辅助镜头放 broll/ | prompts/01-口播.txt | 字幕、人声和辅助画面是否对上 |
| 产品短片 | 产品名和功能资料，有图/实拍/参考风格就一起放 | prompts/02-产品片.txt | 素材是否说明功能，再看短样 |
| 音乐 MV | 音乐；有歌词、角色图、场景参考就一起放 | prompts/03-音乐MV.txt | 副歌、歌词、角色动作与转场 |

把【】换成自己的需求。拿到预览后说出具体修改点，调顺后让 Agent 导出 MP4 与可编辑工程。工程包包含工具与方法，不附文章中的原始素材、成片、写作 Skill 或账号信息。

## 运行说明

需要 Python 3.10+、Node.js 22+、npm、FFmpeg/ffprobe。Node 依赖由 package-lock.json 锁定；在本目录执行 npm ci。口播转写按需安装 requirements-talk.txt，音乐分析按需安装 requirements-mv.txt。建议用项目虚拟环境，环境检查和正式脚本使用同一个 Python。Remotion 首次渲染可能下载浏览器，Whisper 首次转写可能下载权重。

```sh
python3 scripts/env_check.py --task basic
npm ci
npm run typecheck
python3 scripts/repro_demo.py talk
python3 scripts/repro_demo.py product
python3 scripts/repro_demo.py mv
```

三个 demo 的画面和测试声音在本机由程序生成，仅验证渲染、合成、字幕和时间表；不含真人口播，也不证明正式创作效果。产品片和 MV 的正式场景由 Agent 根据你的要求编写或调用你已有的生成工具。本包不附图像/视频生成 API，也不会自动获得联网或多模态能力。动画质量仍需看短样、反馈调整。

口播完整操作和字段见 docs/data-contracts.md。脚本涉及软链接；本次验证环境为 macOS，Windows 使用前需自行解决软链接权限和字体差异，不声称已做跨平台完整验证。Remotion 及各依赖遵循各自许可证。

## 公开打包

`release-files.json` 是唯一发布白名单。运行 `python3 scripts/build_release.py ../ai-video-workflow-kit.zip` 可生成干净 ZIP；input/material/、public/、runs/ 运行中新增的素材均不自动打包。不要将原项目的 Git 历史或 node_modules 搬进新仓库。
