# 财报输出 → 来源核对 → 修正后的分析

下载整个 ZIP 并解压，进入 `earnings-review-skill` 文件夹。需要 Python 3.9+。
不要只下载 SKILL.md。内附 Python 包，无需 pip、API key、付费模型或账户。

## 1. 先运行三个离线例子

```sh
python3 scripts/run.py earnings-demo --out demo-results
python3 scripts/selftest.py
```

预期输出：

- correct：SUPPORTED，保留正确的收入、营业利润、净利润和两项利润率。
- wrong：CORRECTION_REQUIRED，把错误的单季营业亏损改为营业利润 19,209,000 美元，利润率改为 1.6%。其他正确数字保留。
- insufficient：UNKNOWN，营业利润不能证明同额经营现金流。

打开 `demo-results/correct.md`、`wrong.md`、`insufficient.md`，或把对应 JSON
交给 AI 解释。离线证据级别为 REVIEWED_ANNOTATIONS_ONLY：使用已审阅事实，
没有在本次运行重新打开原文。例子基于真实财报；错误/不足输入是人为构造，
不是上游错误率或大模型测试。`selftest` 还会回放 Microsoft 历史截止结果。

## 2. 重新核验原始财报

```sh
python3 scripts/run.py fetch-claim-source --out private-source
python3 scripts/run.py earnings-demo --source private-source/source.html --out original-results
```

成功后证据级别为 REVIEWED_ORIGINAL_REEXTRACTED。源文件哈希、CIK、期间、单位、
符号和三个实际 iXBRL 数值均检查。SEC 拒绝访问或文件改变时保持 UNKNOWN，
不把离线记录说成本次原文核验成功。原始财报仅保存在你的电脑。

## 3. 接入已有工具

在单独下载的 day-trader-skill 仓库中，用自己的 SEC User-Agent 运行：

```sh
python3 trader-analyst/facts.py CRWV --json > earnings.json
```

兼容测试固定上游提交 `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`。
把 `earnings.json` 和可选 `analysis.txt` 放到本 Skill 文件夹，再运行：

```sh
python3 scripts/run.py review-export --input earnings.json --cutoff 2026-11-03T00:00:00Z --analysis analysis.txt --out my-review
```

使用你的实际研究截止时间。没有分析文本时省略 `--analysis`。
可加 `--source private-source/source.html` 重新提取已有审阅原文。
完整的上游输出含有其他季度、指标和 TTM 时，这些项会明确标 UNKNOWN。
本版本不是任意公司、任意财报的通用核验器，也不解析自由文本的全部含义。
`metrics.json` 丢失期间和逐行上下文，因此不能替代完整 JSON。

离线完整输入与报告可从 `examples/` 查看。正确输入由真实上游函数处理三个
已审阅数字而成；重建的 Company Facts 形状不冒充完整 SEC API 下载。

## 4. 在 AI 中使用

有 Python 工具的宿主：加载 SKILL.md，提供 JSON 和原分析，要求实际执行上述
命令，再解释 report。没有执行权限的聊天：先在本机运行，上传输出 JSON。

可以直接问：

> 使用 earnings-review-skill 检查附件。保留正确数字，给出必要修正和原文位置。
> 区分已审阅注释与本次原文提取。不要把未知现金流、其他季度或后续推论写成事实。
> 告诉我实际执行了哪个命令；不能执行就标记 NOT RUN。

本地 stdio MCP 配置：

```json
{"mcpServers":{"earnings-review":{"command":"python3","args":["/ABSOLUTE/PATH/earnings-review-skill/scripts/run.py","mcp"]}}}
```

把占位路径改成真实解压路径，按宿主的 MCP 配置方式设置。
工具 `review_earnings_export` 接收 payload、cutoff，可选 analysis、sourceText、mode。
不读取用户本地路径、不访问网络、不取凭证、不下单。

## 5. 如何理解结果

每项有独立来源、期间、单位、事实 ID、申报和采集时钟。revisedAnalysis 是核验
范围内的数字陈述；原始 analysis 保留为未作语义核验的文本。不要把摘要的
SUPPORTED 解读成整篇分析正确。旧版本包和 Microsoft 历史截止记录保持不变。

软件 MIT，AhaSignals 注释 CC BY 4.0，原始财报未打包。AhaSignals 为独立、
AI-assisted single-operator 研究，与所提及公司、项目和平台无隶属或背书关系。
