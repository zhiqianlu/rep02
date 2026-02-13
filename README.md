# rep02 - Journey to the West RAG System

[English](#english) | [中文](#中文)

## English

### Overview
This repository contains a Retrieval-Augmented Generation (RAG) system designed to answer questions about the Chinese classical novel "Journey to the West" (西游记). The system uses vector embeddings and semantic search to provide accurate answers based on the text content.

### Repository Structure

```
rep02/
├── etl.py              # ETL script for text preprocessing
├── rag_agent.py        # RAG agent implementation
└── txt                 # Configuration file with credentials
```

### Components

#### 1. `etl.py` - ETL Pipeline
A data preprocessing script that:
- Reads text files from a source folder (`西游记白话文`)
- Strips whitespace from each line
- Renames files based on their first line content
- Outputs processed files to an `output` folder

**Key Features:**
- Automated batch processing of text files
- UTF-8 encoding support for Chinese characters
- Creates output directory if it doesn't exist

#### 2. `rag_agent.py` - RAG Agent
The main application implementing a question-answering system using:
- **Vector Database**: FAISS for similarity search
- **Embeddings**: HuggingFace embeddings (`thenlper/gte-small`)
- **LLM**: Google Gemini 2.0 Flash (via OpenRouter API)
- **Framework**: smolagents for agent orchestration

**Features:**
- Semantic search across Journey to the West text
- Retriever tool for fetching relevant passages
- Multi-query strategy for comprehensive answers
- Example query: "孙悟空有两个师傅,他们分别是谁?" (Who are Sun Wukong's two masters?)

**Architecture:**
1. User asks a question
2. Agent converts question to affirmative search queries
3. Retriever searches vector database for relevant passages
4. LLM generates answer based on retrieved context

#### 3. `txt` - Configuration File
Contains API credentials and authentication information.

### Technology Stack
- **Python 3.x**
- **FAISS**: Vector similarity search
- **HuggingFace Transformers**: Text embeddings
- **smolagents**: Agent framework
- **OpenRouter**: LLM API gateway
- **Google Gemini**: Large language model

### Usage

#### Running ETL Pipeline
```bash
python etl.py
```

Prerequisites:
- Source folder `西游记白话文` with text files
- Text files should have the target name as the first line

#### Running RAG Agent
```bash
python rag_agent.py
```

Prerequisites:
- Pre-built vector database in `vector_db/` directory
- API key set as environment variable
- FAISS vector database loaded from local storage

### ⚠️ Security Concerns

**CRITICAL**: This repository contains exposed credentials:
- API keys visible in source code (`rag_agent.py`)
- Credentials stored in plaintext (`txt` file)
- Username and password exposed

**Recommendations:**
1. Remove hardcoded credentials from source code
2. Use environment variables for sensitive data
3. Add `txt` and credential files to `.gitignore`
4. Rotate exposed API keys immediately
5. Use a secrets management system

### Use Case
This system is designed for:
- Literary analysis of Journey to the West
- Educational purposes for studying Chinese classical literature
- Demonstrating RAG architecture with Chinese language texts
- Question-answering about characters, plot, and themes

### Example Query
**Question**: "孙悟空有两个师傅,他们分别是谁?"  
**Translation**: "Who are Sun Wukong's two masters?"

The system retrieves relevant passages and provides an answer based on the text corpus.

---

## 中文

### 概述
本仓库包含一个检索增强生成（RAG）系统，专门用于回答有关中国古典小说《西游记》的问题。该系统使用向量嵌入和语义搜索来基于文本内容提供准确的答案。

### 仓库结构

```
rep02/
├── etl.py              # 文本预处理的ETL脚本
├── rag_agent.py        # RAG代理实现
└── txt                 # 包含凭证的配置文件
```

### 组件说明

#### 1. `etl.py` - ETL管道
数据预处理脚本，功能包括：
- 从源文件夹（`西游记白话文`）读取文本文件
- 去除每行的前后空格
- 根据第一行内容重命名文件
- 将处理后的文件输出到 `output` 文件夹

**主要特性：**
- 自动批量处理文本文件
- 支持UTF-8编码的中文字符
- 自动创建输出目录

#### 2. `rag_agent.py` - RAG代理
实现问答系统的主应用程序，使用：
- **向量数据库**: FAISS用于相似性搜索
- **嵌入模型**: HuggingFace嵌入（`thenlper/gte-small`）
- **大语言模型**: Google Gemini 2.0 Flash（通过OpenRouter API）
- **框架**: smolagents用于代理编排

**功能特性：**
- 对《西游记》文本进行语义搜索
- 检索工具用于获取相关段落
- 多查询策略以获得全面答案
- 示例查询："孙悟空有两个师傅,他们分别是谁？"

**架构：**
1. 用户提出问题
2. 代理将问题转换为肯定式搜索查询
3. 检索器在向量数据库中搜索相关段落
4. LLM基于检索的上下文生成答案

#### 3. `txt` - 配置文件
包含API凭证和身份验证信息。

### 技术栈
- **Python 3.x**
- **FAISS**: 向量相似性搜索
- **HuggingFace Transformers**: 文本嵌入
- **smolagents**: 代理框架
- **OpenRouter**: LLM API网关
- **Google Gemini**: 大语言模型

### 使用方法

#### 运行ETL管道
```bash
python etl.py
```

前置条件：
- 包含文本文件的源文件夹 `西游记白话文`
- 文本文件的第一行应为目标文件名

#### 运行RAG代理
```bash
python rag_agent.py
```

前置条件：
- `vector_db/` 目录中预构建的向量数据库
- 设置为环境变量的API密钥
- 从本地存储加载FAISS向量数据库

### ⚠️ 安全隐患

**严重问题**：本仓库包含暴露的凭证：
- 源代码中可见的API密钥（`rag_agent.py`）
- 以明文存储的凭证（`txt`文件）
- 暴露的用户名和密码

**建议：**
1. 从源代码中删除硬编码的凭证
2. 使用环境变量存储敏感数据
3. 将 `txt` 和凭证文件添加到 `.gitignore`
4. 立即轮换暴露的API密钥
5. 使用密钥管理系统

### 应用场景
本系统适用于：
- 《西游记》文学分析
- 学习中国古典文学的教育目的
- 演示中文文本的RAG架构
- 关于角色、情节和主题的问答

### 示例查询
**问题**: "孙悟空有两个师傅,他们分别是谁？"

系统会检索相关段落，并基于文本语料库提供答案。

---

### Contributing
Contributions are welcome! Please ensure that:
- No credentials are committed to the repository
- Code follows Python best practices
- Documentation is updated for new features

### License
Please refer to the repository owner for license information.
