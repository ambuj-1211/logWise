# app.py - Flask backend server
import os
from typing import List, Optional

import docker
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.retrievers.document_compressors import (
    DocumentCompressorPipeline, EmbeddingsFilter, LLMReranker)
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import LiteLLM
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://litellm-proxy:4000/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/llama3-8b-8192")

def get_llm_response(messages):
    payload = {
        "model": GROQ_MODEL,
        "messages": messages
    }
    headers = {"Authorization": "Bearer fake-key"}
    response = requests.post(LITELLM_PROXY_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

app = Flask(__name__)
CORS(app)

client = docker.from_env()
container_vectorstores = {}

prompt = ChatPromptTemplate.from_template("""
Answer the following question about the Docker container logs based only on the provided context.
Think step by step before providing a detailed answer. If the information is not in the context,
respond that you don't have enough information from the logs to answer correctly.

<context>
{context}
</context>

Container: {container_name}
Question: {input}
""")

@app.route("/api/containers", methods=["GET"])
def get_containers():
    try:
        containers = client.containers.list(all=True)  # List all containers, not just running
        return jsonify([
            {
                "id": c.id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "state": c.status,
                "status": f"Up since {c.attrs['Created'][:10]}"
            } for c in containers
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<container_id>/logs", methods=["GET"])
def get_logs(container_id):
    tail = int(request.args.get("tail", 100))
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail).decode("utf-8")
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        container_id = data["containerId"]
        message = data["message"]
        container = client.containers.get(container_id)

        if container_id not in container_vectorstores:
            logs = container.logs().decode("utf-8")
            chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_text(logs)
            vectorstore = FAISS.from_texts(chunks, embedding_model)
            container_vectorstores[container_id] = vectorstore

        retriever = VectorStoreRetriever(vectorstore=container_vectorstores[container_id])
        multi_query_retriever = MultiQueryRetriever.from_llm(
            retriever=retriever,
            llm=None  # Not used, handled by get_llm_response
        )
        reranker = LLMReranker(llm=None)  # Not used, handled by get_llm_response
        compressor = DocumentCompressorPipeline(transformers=[reranker])

        docs = multi_query_retriever.get_relevant_documents(message)
        reranked_docs = compressor.compress_documents(docs, query=message)
        context = "\n".join([doc.page_content for doc in reranked_docs])

        # Prepare messages for LLM (OpenAI format)
        messages = [
            {"role": "system", "content": f"You are a helpful assistant for Docker container logs. Context: {context}"},
            {"role": "user", "content": message}
        ]
        answer = get_llm_response(messages)
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
