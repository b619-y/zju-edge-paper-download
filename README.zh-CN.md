# zju-edge-paper-download

面向 OpenClaw 的学术论文下载 skill 仓库，用于 `浙江大学机构访问 + 固定输出目录 + 出版商适配下载`。

[English README](./README.md)

## 这个仓库解决什么问题

- 把当前流程包装成 OpenClaw 可以直接消费的 skill 仓库，而不是只适合 Codex 本地使用。
- 复用已经登录好的浙江大学机构访问会话。
- 默认在出版商机构选择页面优先选择 `Zhejiang University`。
- 保留 ACS 的快速通道。
- 提供 Nature、Science、ScienceDirect 的出版商适配下载逻辑。
- 固定 PDF 输出目录，避免文件散落。
- 把实际下载实现隔离在独立浏览器配置里，不污染主浏览器。

## OpenClaw 适配说明

这个公开仓库现在是 OpenClaw-first 的：

- `SKILL.md` 按 OpenClaw 的 skill 触发方式来写。
- 仓库结构可以直接放进 OpenClaw 的本地 skill 集合里。
- 公开仓库面向 OpenClaw 使用场景组织文档和入口说明。

但需要明确一点：

- 这个仓库里打包的实际下载实现，当前仍然是已经验证过的 `Edge + 持久登录态 + 固定下载目录` 链路。
- 也就是说，skill 入口是 OpenClaw 友好的，底层运行实现不是“纯 OpenClaw 浏览器自动化重写版”。

## 已验证的固定路径

- 持久浏览器 profile：
  `/Users/b/Downloads/browser-use-local/persistent-edge/zju-edge-profile`
- PDF 输出目录：
  `/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`
- 远程调试端口：
  `62777`

## 环境要求

- macOS
- OpenClaw 或任何能调用本地 shell / Python 脚本的兼容 skill 运行环境
- Microsoft Edge，安装在 `/Applications/Microsoft Edge.app`
- 已经可用的浙江大学机构访问流程
- Python 3

## 用法

### 1. 安装到 OpenClaw skill 目录

把这个仓库 clone 或复制到 OpenClaw 的本地 skill 集合目录中。

### 2. 启动或复用专用浏览器会话

```bash
./scripts/launch_edge.sh
```

如果要只重启这套专用 profile：

```bash
./scripts/launch_edge.sh --restart
```

### 3. 必要时刷新 ACS 机构登录

```bash
./scripts/login_acs.sh "10.1021/acs.est.6c01242"
```

如果会话有效，会直接打开文章页；如果失效，就在浏览器里完成一次浙江大学登录。

### 4. 下载论文 PDF

自动识别出版商：

```bash
python3 ./scripts/download.py \
  10.1021/acs.est.6c01242 \
  10.1038/ncomms14183
```

强制指定出版商：

```bash
python3 ./scripts/download.py \
  --publisher science \
  10.1126/science.ada1091
```

从文件批量输入：

```bash
python3 ./scripts/download.py \
  --from-file ./dois.txt
```

兼容旧入口：

```bash
python3 ./scripts/download_dois.py \
  10.1021/acs.est.6c01242
```

## 当前固定行为

- ACS 走已验证的快速 PDF 通道。
- Nature 适配器支持新版页面常见的 `_reference.pdf` 链路。
- Science 仍属于探索型支持，但已多次实测成功。
- ScienceDirect 仍然是最不稳定的一家。
  推荐做法：
  - 保持专用浏览器 profile 处于热状态
  - 默认机构选择浙江大学
  - 优先传入 ScienceDirect article URL
  - 如果落到 challenge / download 页面，允许在当前会话里继续完成

## 输出文件

PDF 默认写入：

`/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`

成功后会重命名为稳定文件名，例如：

- `10.1021_acs.est.6c01242.pdf`
- `10.1038_ncomms14183.pdf`
- `www.sciencedirect.com_science_article_pii_S0013935126005669.pdf`

## 安全与发布说明

- 仓库不存储校园账号密码。
- 机构登录态只保存在独立浏览器 profile 中。
- 不要把真实浏览器 profile、下载得到的 PDF、或其他本地运行产物提交到 GitHub。
- 如果以后需要真正改成纯 OpenClaw 浏览器执行栈，应当在文档里明确说明，不要把当前实现误写成完全不同的运行方式。
