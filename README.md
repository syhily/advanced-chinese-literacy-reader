# 语文素养高级读本（Advanced Chinese Literacy Reader）

李瑞山 编撰 · 高等教育出版社 · 2006 年

本项目将扫描版《语文素养高级读本》PDF 经 OCR（[MinerU](https://github.com/opendatalab/MinerU)）识别、人工校对后排版为 Markdown，再由 [pandoc](https://pandoc.org) 工具链构建为 EPUB 3 电子书。全书 18 个单元、136 篇选文、279 条脚注（随所在章节分页，支持阅读器弹注）。

## 文件结构

| 文件 | 说明 |
| --- | --- |
| `manuscript/00-front-matter.md` | 前置部分（书名页、作者名录、前言等） |
| `manuscript/01-unit-01.md` … `18-unit-18.md` | 各单元正文（**所有修改都在对应单元文件里进行**） |
| `filter.lua` | pandoc Lua 过滤器（精简版）：只负责 `>` 诗行、`>>` 引文块的转换与合并、段内软换行合并、正文书名号标楷体——其余排版约定都已在稿件里写成 pandoc 原生标记 |
| `epub.css` | 样式表：字体回退链采用 [fonts.css](https://github.com/zenozeng/fonts.css)（MIT）的定义，按黑体/宋体/楷体/仿宋四种字形覆盖 Windows、macOS、Linux 常见字体（正文默认字体不设置，沿用阅读器默认），并细化各级标题、引文、诗歌、脚注、目录等排版 |
| `metadata.yaml` | EPUB 元数据（书名、编撰者、出版社、语种、ISBN 等），pandoc 据此生成书名页 |
| `cover.jpg` | 封面图（原书封面扫描件） |
| `Makefile` | `make` 构建，`make check` 校验，`make clean` 清理 |
| `advanced-chinese-literacy-reader.epub` | 构建产物（不入库，见 Releases） |

原始扫描 PDF 不入库，请自行准备。

## 下载

每次打 tag 都会由 GitHub Actions 自动构建 EPUB 并发布到 Releases：

- [下载最新版 EPUB](https://github.com/syhily/advanced-chinese-literacy-reader/releases/latest/download/advanced-chinese-literacy-reader.epub)
- [查看全部版本](https://github.com/syhily/advanced-chinese-literacy-reader/releases)

## 构建

```sh
make          # pandoc 一条命令生成 advanced-chinese-literacy-reader.epub
make check    # 校验 zip 完整性与脚注引用/注释一一对应
make clean    # 删除构建产物
```

依赖 pandoc（≥ 3.1，需 Lua filter 支持）。macOS 可 `brew install pandoc`，Debian/Ubuntu 可 `apt install pandoc`。

`make check` 依次做三件事：`unzip -t` 校验 zip 完整性、用 `unzip` + `grep` 核对脚注引用/注释数量一致、用 pandoc 读回 EPUB 确认可解析。

构建即一条 pandoc 命令：`--lua-filter=filter.lua --split-level=3 --toc-depth=4`，编 > 单元 > 选文三级分页与目录（每个单元另含「问题导引」条目）；脚注随章末为尾注（EPUB 3 `epub:type="footnote"`，Apple Books 等阅读器可弹注）。不加 `--toc`，故 `nav.xhtml` 目录文档仍生成供阅读器侧栏使用，但不会作为书页出现在翻页顺序里。

## 参与校对与修改

欢迎通过 Issue 或 Pull Request 指正 OCR 讹误与排版问题。修改对应单元的 `manuscript/NN-unit-NN.md` 后运行 `make` 重建即可。稿件采用 pandoc 原生 Markdown，绝大多数排版意图直接写在稿件的标记里；`filter.lua` 只兜底几件 Markdown 表达不了的事（见文末）。

### 标题层级

| 写法 | 用途 | 独立分页 | 入目录 |
| --- | --- | --- | --- |
| `# 上编 …` | 编（上 / 中 / 下） | 是 | 是 |
| `## 单元X …` | 单元 | 是 | 是 |
| `### x-y 标题[^n]` | 选文（带脚注引用） | 是 | 是 |
| `### 小结 {.xj}` | 单元小结 | 是 | 是 |
| `#### 问题导引 {.center}` | 问题导引栏目 | 否 | 是 |
| `#### 栏目名 {.unlisted}` | 编读札记、思考与讨论、各篇提要、要点提炼、争议聚焦、拓展阅读指引、注释 | 否 | 否 |
| `#### 文内小标题 {.center .unlisted}` | 选文内的居中小标题 | 否 | 否 |
| `# 前置章节 {.unlisted}` | 内容简介、作者名录、前言、电子版说明、郑重声明 | 是 | 否 |

分页与目录由 `--split-level=3 --toc-depth=4` 决定；`.unlisted` 表示该标题不进目录。

### 区块（fenced div）

| 写法 | 用途 |
| --- | --- |
| `::: tiyao` … `:::` | 各篇提要条目 |
| `::: daoyin` … `:::` | 问题导引的正文（卡片框） |
| `::: kwbox` … `:::` | 关键词语胶囊区（框内写 `[词]{.kw}`） |
| `::: notice` … `:::` | 电子版说明与免责声明的正文（卡片框） |
| `::: author` / `::: subtitle` / `::: right` | 作者行（居中楷体）/ 副题 / 居右落款 |
| `::: bib-entry` … `:::` | 拓展阅读指引的文献条目 |
| `::: namerow` … `:::` | 作者名录每行（`[姓名]{.name}` 分栏） |
| `::: note` / `::: thanks` | 名录内的括注 / 致谢行 |

### 行内

| 写法 | 效果 |
| --- | --- |
| `**文字**` | 加重（渲染为黑体） |
| `[文字]{.dot}` | 着重号（字下圆点） |
| `[词语]{.kw}` | 关键词语胶囊 |
| `[姓名]{.name}` | 名录分栏单元 |
| `《书刊名》` | 全书自动渲染为楷体（含引文与脚注） |
| `[^n]:` 定义 + 正文 `[^n]` | 脚注；编号全书连续、随章节分页 |

### 由 filter.lua 处理的四种情况

以下内容无法用 Markdown 表达，构建时由 `filter.lua` 转换：

1. `> 诗行` → `div.verse` 行块：行内换行保留、空行分节、整首居中；相邻诗节合并共享左缘；
2. `>> 文字` → `div.quote` 引文块：每行一段、楷体缩进；相邻引文块合并避免空行；
3. 段内软换行合并：两侧都是汉字则相连，一侧是数字/英文则补一个空格；
4. 正文书名号《…》标 `span.bt`（楷体）。

`>` / `>>` 保留 Markdown 引用块写法，是为了 GitHub 预览时仍能以引用块形式显示。

## 免责声明

本书著作权归原作者及高等教育出版社所有。本项目仅供个人学习与研究使用，不进行任何商业用途，不用于任何形式的再出版。OCR 识别与人工校对可能存在讹误，内容请以高等教育出版社纸质原书为准。若本仓库内容涉及侵权，请联系仓库所有者，核实后将立即删除。
