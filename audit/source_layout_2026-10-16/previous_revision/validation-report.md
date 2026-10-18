# 验收记录

本文件依据实际JSON、编译日志和人工页面检查填写。验证版本为maintenance-editorial-2026-10-16-v1。

| 检查 | 实际结果 | 证据 |
|---|---|---|
| 基线身份 | M/S哈希与方案一致；47份快照 | input_manifest.json |
| 保护文件 | 1,025文件哈希不变，含独立论文与全部旧实验 | validation.json |
| 活跃结构 | 主文7节、补充13节；旧专属分析和旧图无编译输入 | validation.json actual_inputs |
| 引用与文献 | 源label/ref可解析、无重复；独立bbl只显示实际引用 | validation.json；build/*.log |
| 编译 | 两份PDF成功；最终TeX日志无未定义引用、重复citation或版面警告 | build-console.log；build/*.log |
| 独立源码包构建 | 25个白名单文件在独立目录构建成功，两份PDF抽取文本与已审阅稿完全一致 | source-package-validation.json；build-record.json；submission-source.zip |
| 保留公式 | 补充72个展示式中71个相同，另一式合并已有熵下界；正文17式规范化相同 | proof_math_preservation.json；main_theory_audit.md |
| 数值 | 5,760记录、主表24行、allocation及成对差异核对通过 | experiments_validation.json |
| 代码语义 | 六个短场景721轮；不改变代码，与原接口逐轮一致 | experiments_validation.json；check_experiments.py |
| PDF渲染 | 全部页面渲染；文本无空页、越界或未解引用 | pdf_review/render_checks.json |
| 人工视觉 | 算法、长式、两端结论、主表、九方法图及全部附录页已查看；修正三项分解被float割裂和引理跨页 | visual_review.md |
| Markdown公式 | 本轮所有新建/修改Markdown按单美元和独占行双美元检查 | validation.json markdown_checked |
| 文本清理 | humanizer复核叙事；18份活跃TeX调用技能检查，BibTeX不受工具支持并另作只读Unicode检查 | prose-edit-audit.md；watermark_inspection.json |

两份最终PDF页数分别为 20、20。最终hash和实际输入图记录于validation.json；PDF内容与快照的差异属于本轮授权编辑。旧根目录的编译日志不代表本轮构建。

## 检查的边界

本轮未开展新比较实验、历史20,000轮parity重跑、完整独立证明复核、文献创新性重评分或现行期刊规则的实时核查。有限模拟零误报不验证全环境、全时间可靠性。统计文本水印未使用对应检测器与密钥核验；不声称已验证去除。
