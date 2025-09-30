# tools/rag.py
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.llm = Ollama(model="qwen2:7b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")

try:
    documents = SimpleDirectoryReader("./rag/data").load_data()
    index = VectorStoreIndex.from_documents(documents)
except Exception as e:
    print(f"Erro ao carregar documentos para o RAG: {e}")
    index = None

def buscar_informacao(query_usuario: str) -> tuple[str, float]:
    """
    Busca na base de conhecimento e retorna o contexto E o score de confiança.
    """
    if index is None:
        return "Desculpe, minha base de conhecimento não está disponível.", 0.0
    
    # ALTERADO DE 1 para 2    
    retriever = index.as_retriever(similarity_top_k=2)
    nodes = retriever.retrieve(query_usuario)
    
    # Se encontrou algum resultado E o score é bom...
    if nodes and nodes[0].score > 0.7: # Usamos um threshold de 0.7
        return nodes[0].get_content(), nodes[0].score

    # Se não, retorna contexto vazio e score baixo
    return "", 0.0