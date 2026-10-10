# 语文素养高级读本（Advanced Chinese Literacy Reader）

李瑞山 编撰 · 高等教育出版社 · 2006 年

本项目将扫描版《语文素养高级读本》PDF 经 OCR（[MinerU](https://github.com/opendatalab/MinerU)）识别、人工校对后排版为 Markdown，再由构建脚本生成 EPUB 3 电子书。全书 18 个单元、136 篇选文、281 条脚注，脚注按单元拆分、每单元重新编号。

## 文件结构

| 文件 | 说明 |
| --- | --- |
| `manuscript.md` | 全书正文中间稿（Markdown），**所有修改都在这里进行** |
| `build_epub.py` | 构建脚本：Markdown → EPUB 3（纯 Python 标准库，无第三方依赖） |
| `cover.jpg` | 封面图（原书封面扫描件） |
| `Makefile` | `make` 构建，`make check` 校验，`make clean` 清理 |
| `advanced-chinese-literacy-reader.epub` | 构建产物（不入库，见 Releases） |

原始扫描 PDF 不入库，请自行准备。

## 构建

```sh
make          # 生成 advanced-chinese-literacy-reader.epub
make check    # 校验 zip 完整性与脚注引用/注释一一对应
make clean    # 删除构建产物
```

只依赖 Python 3（标准库），无需安装任何包。

## 参与校对与修改

欢迎通过 Issue 或 Pull Request 指正 OCR 讹误与排版问题。修改 `manuscript.md` 后运行 `make` 重建即可。Markdown 中的排版约定：

- `## x-y 标题`：选文标题；其下短行带 `[^n]` 的为作者行（居中楷体）
- `## [编读札记]`、`## [思考与讨论]`、`## [问题导引]` 等：固定栏目，方括号写法
- `> 诗行`：诗歌（行内换行保留，连续行合为一个诗节，空行分节）
- `>> 文字`：选文/引文（blockquote，楷体缩进），每行一段
- `[^n]:`：脚注定义；正文 `[^n]` 引用；构建时按单元拆分并重新编号
- 文内小标题（居中）在 `build_epub.py` 的 `IN_ARTICLE_SUBHEADS` 集合中登记
- 文末日期（`2001-07-30` 或 `2006 年 6 月` 单独一行）自动居右
- 段内换行不渲染为空格；数字/英文与汉字之间的空格由构建脚本自动处理

## 免责声明

本书著作权归原作者及高等教育出版社所有。本项目仅供个人学习与研究使用，不进行任何商业用途，不用于任何形式的再出版。OCR 识别与人工校对可能存在讹误，内容请以高等教育出版社纸质原书为准。若本仓库内容涉及侵权，请联系仓库所有者，核实后将立即删除。
