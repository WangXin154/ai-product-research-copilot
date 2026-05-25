# MCP Client Setup Guide

本文档说明如何将本项目的标准 MCP Server 接入 MCP Client，例如 Claude Desktop、Cursor 或其他支持 MCP 的 Agent 工具。

## 1. MCP Server 说明

本项目已经实现标准 MCP Server：

```text
src/mcp_server/server.py
```

它基于 MCP Python SDK：

```python
from mcp.server.fastmcp import FastMCP
```

Server 名称：

```text
ai-product-research-copilot
```

MCP Server 的作用是让 Agent 通过标准协议调用本项目能力，包括：

- GitHub Issues / Comments 获取
- 数据库查询
- Topic / Pain Point / Opportunity 查询
- 竞品矩阵查询
- AI Evaluation
- 调研报告和 CSV 导出

注意：MCP Server 不是网页应用，不会像 Streamlit 一样提供 localhost 页面。它通常通过 stdio 等待 MCP Client 调用。

## 2. 本地启动验证

在项目根目录运行：

```powershell
cd C:\Users\wangxinxin\Documents\GitHub\ai-product-research-copilot
python -m compileall src\mcp_server
python -c "from src.mcp_server.server import mcp; print(mcp.name)"
```

预期输出：

```text
ai-product-research-copilot
```

启动 MCP Server：

```powershell
python src\mcp_server\server.py
```

如果终端没有报错，并且停在那里等待，就是正常状态。

## 3. 环境变量要求

请先复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

然后填写：

```env
GITHUB_TOKEN=
GITHUB_API_BASE=https://api.github.com
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
DATABASE_PATH=database/product_research.db
```

说明：

- `GITHUB_TOKEN`：用于提高 GitHub API rate limit。
- `OPENAI_API_KEY`：用于 OpenAI Embedding 和 LLM topic labeling。
- `DATABASE_PATH`：默认指向本地 SQLite 数据库。

不要提交真实 `.env` 到 GitHub。

## 4. 暴露的 MCP Tools

当前 MCP Server 暴露以下 tools：

### Database Tools

```text
database_stats
database_repo_summary
database_comment_summary
database_query_raw_feedback
database_query_cleaned_feedback
database_feedback_samples
database_topic_summary
database_topic_samples
database_competitor_summary
database_competitor_matrix
database_opportunity_summary
database_latest_prd
database_latest_evaluation
```

### GitHub Tools

```text
github_fetch_repo_issues
github_fetch_issue_comments
github_fetch_repo_feedback_tool
github_fetch_release_notes
```

### Evaluation Tools

```text
evaluation_score_output
```

### Export Tools

```text
export_cleaned_feedback
export_repo_summary
export_research_summary
```

## 5. Claude Desktop 配置示例

Claude Desktop 的 MCP 配置文件通常位于：

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Windows 示例配置：

```json
{
  "mcpServers": {
    "ai-product-research-copilot": {
      "command": "python",
      "args": [
        "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot\\src\\mcp_server\\server.py"
      ],
      "cwd": "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot"
    }
  }
}
```

如果你的虚拟环境里安装了依赖，也可以使用 `.venv` 中的 Python：

```json
{
  "mcpServers": {
    "ai-product-research-copilot": {
      "command": "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot\\src\\mcp_server\\server.py"
      ],
      "cwd": "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot"
    }
  }
}
```

配置后重启 Claude Desktop。

## 6. Cursor MCP 配置示例

Cursor 支持 MCP 时，可在 MCP 配置中添加类似 server：

```json
{
  "mcpServers": {
    "ai-product-research-copilot": {
      "command": "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot\\src\\mcp_server\\server.py"
      ],
      "cwd": "C:\\Users\\wangxinxin\\Documents\\GitHub\\ai-product-research-copilot"
    }
  }
}
```

实际配置入口可能随 Cursor 版本变化，以 Cursor 当前 MCP 设置页面为准。

## 7. 推荐测试 Prompt

连接 MCP Client 后，可以测试这些问题：

```text
请调用 database_stats，告诉我当前 AI 产品调研数据库里每张核心表有多少数据。
```

```text
请调用 database_topic_summary，总结当前用户反馈中最高频的 3 个主题。
```

```text
请调用 database_competitor_summary，告诉我当前竞品功能覆盖情况。
```

```text
请调用 database_latest_prd 和 database_latest_evaluation，判断最近一次 PRD 是否需要人工审核。
```

```text
请调用 export_research_summary，导出当前调研摘要。
```

## 8. 常见问题

### 1. 启动后没有网页地址，是否正常？

正常。

MCP Server 不是 Web App，不会提供网页。它通过 stdio 等待 MCP Client 调用。

### 2. 终端停在那里是否正常？

正常。

这说明 MCP Server 正在运行并等待客户端请求。

### 3. 报 `ModuleNotFoundError: mcp` 怎么办？

运行：

```powershell
pip install -r requirements.txt
```

确认 `requirements.txt` 里包含：

```text
mcp
```

### 4. 报 `OPENAI_API_KEY` 或 `GITHUB_API_BASE` 相关错误怎么办？

确认 `src/utils/config.py` 包含：

```python
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

并确认 `.env` 已正确填写。

### 5. MCP Client 找不到工具怎么办？

检查：

- MCP 配置里的 `command` 是否指向正确 Python
- `args` 是否指向 `src/mcp_server/server.py`
- `cwd` 是否是项目根目录
- 依赖是否安装在同一个 Python 环境里
- Server 手动启动是否无报错

## 9. 作品集表达方式

可以在 README 或面试中这样描述：

```text
I upgraded the MCP-style Python tool wrappers into a standard MCP Server using the MCP Python SDK and FastMCP. The server exposes GitHub, database, evaluation, and export tools so that external MCP clients can query product research data, retrieve evidence, evaluate AI-generated PRDs, and export research reports through a standardized tool protocol.
```
