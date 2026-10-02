# 代码审查 Agent

一个基于 LLM 的代码审查 Agent，能自动发现代码中的 Bug、代码质量问题、性能问题，并给出改进建议。支持 Python 及 JavaScript / TypeScript / Java / C / C++ / Go / Rust 等语言。

## GitHub 仓库

https://github.com/fxliu926/code-review-agent-fxliu

## 功能特性

- 用 `ast` 解析 Python 代码，精确定位函数/类
- 支持**代码执行工具**：实际运行代码，捕获运行时错误（除零、越界、类型错误等）
- 调用 LLM 从四个维度审查代码：潜在 Bug、代码质量、性能问题、改进建议
- 输出结构化 Markdown 报告，按 Critical/Major/Minor 分级
- **多语言支持**：Python 走「结构化解析 + 代码执行」的完整路径；其他语言没有对应的
  解析器与执行环境，自动降级为「整文件 → LLM 直接审查」，报告里会注明审查模式
- 支持重试、错误处理、边界情况
- 模块化设计，易于扩展

## 安装

```bash
git clone https://github.com/fxliu926/code-review-agent-fxliu.git
cd code-review-agent-fxliu
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

> 默认使用 DeepSeek，兼容 OpenAI SDK。也可换成其他兼容 OpenAI 的服务。

## 使用

### 命令行

```bash
# 审查文件，直接打印报告（.py 走结构化解析）
python main.py examples/bad_code.py

# 非 Python 文件走 LLM 直接审查
python main.py examples/bad_code.js

# 审查文件，保存到 report.md
python main.py examples/bad_code.py -o report.md
```

支持的文件后缀：`.py` / `.js` / `.ts` / `.java` / `.c` / `.cpp` / `.go` / `.rs`。

### Web 界面（Gradio）

```bash
python app.py
```

启动后浏览器打开 http://127.0.0.1:7860 ，在左侧选择语言（默认 Python）、在 `input.py` 编辑器中粘贴代码，点击「运行审查」，右侧 `report.md` 面板即可看到 Markdown 格式的审查报告（面板右上角会显示 READY → DONE 状态）。`examples/` 目录下提供了可直接粘贴的示例代码。

## 测试

```bash
pytest tests/ -v
```

## 项目结构

```
code-review-agent/
├── agent/
│   ├── parser.py        # ast 解析
│   ├── tools.py         # 工具（代码执行）
│   ├── prompt.py        # Prompt 模板
│   ├── llm_client.py    # LLM 调用
│   └── reporter.py      # 报告生成
├── tests/               # 单元测试
├── examples/            # 示例代码
├── main.py              # 命令行入口
├── app.py               # Gradio Web 界面入口
├── requirements.txt
├── README.md
├── Design.md
└── PSP.md
```

## 架构

```
输入代码
   │
   ├─ Python ──► CodeParser(ast) ──► CodeRunner(工具) ──► 逐单元审查
   │
   └─ 其他语言 ─► 整文件作为一个单元 ──────────────────► LLM 直接审查
                    │
                    ▼
        PromptBuilder ──► LLMClient ──► Reporter（Markdown 报告）
```

详见 [Design.md](Design.md)。

## PSP 数据

详见 [PSP.md](PSP.md)。