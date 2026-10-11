import os
import uuid

import chromadb
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

# pdf 짤라서 백터db저장 , 답변시 검색전달

load_dotenv()

# 사용모델과 api값
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

if not api_key:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")


client = genai.Client(
    api_key=api_key,
)


chroma_client = chromadb.PersistentClient(
    path="chroma_db",
)


collection = chroma_client.get_or_create_collection(
    name="lecture_materials",
)


def extract_text_from_pdf(pdf_path):
    # pdf에서 텍스트 읽어서 문자열만듬

    reader = PdfReader(pdf_path)

    page_texts = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            page_texts.append(text)

    return "\n\n".join(page_texts)


def split_text(text, chunk_size=1000, overlap=150):
    # 텍스트 조각화

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def clear_previous_documents():
    #백터db 초기화 (전에꺼삭제)

    old_data = collection.get(
        include=[],
    )

    old_ids = old_data["ids"]

    if old_ids:
        collection.delete(
            ids=old_ids,
        )


def save_pdf_to_vector_db(pdf_path, original_filename):

   # 백터db에 저장 

    pdf_text = extract_text_from_pdf(pdf_path)

    if not pdf_text.strip():
        return {
            "success": False,
            "message": "PDF에서 텍스트를 읽지 못했습니다. 스캔 이미지 PDF일 수 있습니다.",
        }

    chunks = split_text(pdf_text)

    if not chunks:
        return {
            "success": False,
            "message": "PDF에서 저장할 텍스트 조각을 만들지 못했습니다.",
        }

    clear_previous_documents()

    document_ids = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        document_ids.append(str(uuid.uuid4()))

        metadatas.append({
            "filename": original_filename,
            "chunk_index": index,
        })

    collection.add(
        ids=document_ids,
        documents=chunks,
        metadatas=metadatas,
    )

    return {
        "success": True,
        "message": f"'{original_filename}' 자료를 저장했습니다. 총 {len(chunks)}개 조각으로 분석되었습니다.",
    }


def search_documents(question, n_results=6):
    # db 검색

    stored_data = collection.get(
        include=[],
    )

    if not stored_data["ids"]:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )

    return results["documents"][0]


def ask_rag(question):
    # 백터db 자료로 ai 답변시키기 

    documents = search_documents(
        question=question,
        n_results=3,
    )

    if not documents:
        return "먼저 강의자료 PDF를 업로드해주세요."

    context = "\n\n---\n\n".join(documents)

    # 프롬포트
    prompt = f"""
너는 업로드된 강의자료를 바탕으로 답변하는 학습 도우미다.

반드시 아래 CONTEXT에 있는 내용만 근거로 답변하라.
CONTEXT에 답이 없거나 근거가 부족하면
"업로드된 강의자료에서 해당 내용을 찾지 못했습니다."라고 답하라.

그리고 구글에서 관련 주제로 추가 탐색한 후, 비교하라
단, 강의자료와 구글의 출처 구분을 명확하게 나눈다.

CONTEXT:
{context}

질문:
{question}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    return response.text
