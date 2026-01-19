# 西游记 RAG 问答系统

基于 RAG (Retrieval-Augmented Generation) 技术的《西游记》智能问答系统，使用 Gradio 提供友好的 Web 界面。

## 功能特点

- 🎨 **现代化 UI**: 使用 Gradio 构建的美观、易用的 Web 界面
- 🔍 **智能检索**: 基于 FAISS 向量数据库的语义搜索
- 🤖 **AI 驱动**: 使用 Gemini 大语言模型生成准确答案
- 📚 **专业知识库**: 包含《西游记》相关内容的向量数据库
- 💡 **示例问题**: 预置常见问题，方便快速体验

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python rag_agent.py
```

应用将在 `http://localhost:7860` 启动。

## 使用说明

1. 在输入框中输入您关于《西游记》的问题
2. 点击"🔍 提交问题"按钮
3. 系统将在知识库中检索相关信息并生成答案
4. 答案将显示在下方的输出框中

### 示例问题

- 孙悟空是谁？
- 唐僧师徒四人分别是谁？
- 孙悟空有什么本领？
- 唐僧为什么要去西天取经？

## 技术栈

- **smolagents**: Agent 框架
- **Gradio**: Web UI 框架
- **LangChain**: RAG 工具链
- **FAISS**: 向量数据库
- **HuggingFace Embeddings**: 文本嵌入模型

## 项目结构

- `rag_agent.py`: 主应用文件，包含 RAG agent 逻辑和 Gradio UI
- `etl.py`: ETL 脚本，用于处理和转换文本数据
- `requirements.txt`: Python 依赖列表

## 注意事项

- 需要预先准备好向量数据库 (`vector_db` 目录)
- 需要配置 OpenRouter API 密钥作为环境变量
