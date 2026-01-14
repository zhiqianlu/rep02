from smolagents import ToolCallingAgent, OpenAIServerModel, tool, GradioUI
import os
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logger.info("正在初始化嵌入模型...")
embedding_model = HuggingFaceEmbeddings(model_name="thenlper/gte-small")

# 加载本地存储的向量数据库
logger.info("正在加载向量数据库...")
vectordb = FAISS.load_local("vector_db", embeddings=embedding_model, allow_dangerous_deserialization=True)
logger.info("向量数据库加载成功")

model = OpenAIServerModel(
    # model_id="google/gemini-2.0-flash-001",
    model_id="google/gemini-2.0-flash-lite-preview-02-05:free",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("dfdfdfdfdfdf99erefddfd"),  # 从环境变量中获取 API 密钥
)


@tool   
def retriever(query:str)->str:
    """
    根据用户的查询，执行向量数据库的相似性搜索，并返回结果的字符串表示形式。

    Args:
        query: 要查询的字符串。此字符串将用于在向量数据库中进行相似性搜索。

    """
    logger.info(f"正在查询: {query}")
    results = vectordb.similarity_search(query, k=5)  # k 是返回的结果数量
    logger.info("查询完成")

    # 将结果组合成一个字符串
    combined_results = "\n\n".join([f"资料{i+1}: {result.page_content}" for i, result in enumerate(results)])
    return combined_results


agent = ToolCallingAgent(tools=[retriever], model=model, add_base_tools=False)


def answer_question(question: str) -> str:
    """
    使用 RAG agent 回答用户问题
    
    Args:
        question: 用户的问题
        
    Returns:
        agent 的回答
    """
    if not question or question.strip() == "":
        return "请输入一个有效的问题。"
    
    rag_agent_prompt = f"""
根据你的知识库，回答以下问题。
请只回答问题，回答应该简洁且与问题相关。
如果你无法找到信息，不要放弃，尝试使用不同的参数再次调用你的 retriever 工具。
确保通过多次使用语义不同的查询来完全覆盖问题。
你的查询不应是问题，而是肯定形式的句子：例如，与其问"如何从 Hub 加载 bf16 模型？"，不如问"从 Hub 加载 bf16 权重"。

Question:
{question}"""
    
    try:
        result = agent.run(rag_agent_prompt)
        return result
    except Exception as e:
        logger.error(f"处理问题时出错: {e}")
        return f"抱歉，处理您的问题时出现错误: {str(e)}"


# 创建 Gradio UI
if __name__ == "__main__":
    import gradio as gr
    
    # 创建带有自定义样式的 Gradio 界面
    with gr.Blocks(title="西游记问答系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 📚 西游记 RAG 问答系统
            
            欢迎使用基于 RAG 技术的西游记智能问答系统！
            
            本系统使用向量数据库和 AI 模型，能够回答关于《西游记》的各种问题。
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                question_input = gr.Textbox(
                    label="💬 请输入您的问题",
                    placeholder="例如：孙悟空是谁？唐僧师徒四人都有谁？",
                    lines=3
                )
                
                with gr.Row():
                    submit_btn = gr.Button("🔍 提交问题", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ 清空", size="lg")
        
        with gr.Row():
            answer_output = gr.Textbox(
                label="📖 回答",
                lines=10,
                placeholder="答案将显示在这里..."
            )
        
        gr.Markdown(
            """
            ---
            ### 📌 使用提示
            - 问题要具体明确，以便获得更准确的答案
            - 系统会自动从知识库中检索相关信息
            - 如果第一次没有得到满意的答案，可以尝试换个方式提问
            """
        )
        
        # 设置按钮功能
        submit_btn.click(
            fn=answer_question,
            inputs=question_input,
            outputs=answer_output
        )
        
        clear_btn.click(
            fn=lambda: ("", ""),
            inputs=None,
            outputs=[question_input, answer_output]
        )
        
        # 添加示例问题
        gr.Examples(
            examples=[
                ["孙悟空是谁？"],
                ["唐僧师徒四人分别是谁？"],
                ["孙悟空有什么本领？"],
                ["唐僧为什么要去西天取经？"]
            ],
            inputs=question_input
        )
    
    # 启动 Gradio 界面
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


