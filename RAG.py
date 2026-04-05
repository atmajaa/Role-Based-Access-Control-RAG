import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Load embedding model once — reused for all departments
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)

system_prompt = """You are a helpful assistant.
Answer ONLY using the context provided below.
If the answer is not found in the context, respond with exactly:
'I don't have access to that information.'
Do not use any outside knowledge.

Context: {context}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])


def ask_question(query: str, department: str) -> str:
    db_path = f"./dept_dbs/{department}"

    # Check the dept DB exists
    if not os.path.exists(db_path):
        return f"No documents found for the {department} department yet."

    # LOAD the existing vector DB 
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embedding_model
    )

    # Build the chain for this department
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(vector_db.as_retriever(), question_answer_chain)

    response = rag_chain.invoke({"input": query})
    return response["answer"]