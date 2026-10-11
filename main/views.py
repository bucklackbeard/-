# 웹에서 입출력, pdf저장, db생성 호출 등 척추 담당

import os
import uuid

from django.conf import settings
from django.shortcuts import render

from .rag_service import ask_rag, save_pdf_to_vector_db


def home(request):
    return render(
        request,
        "main/home.html",
    )


def upload_pdf(request):
    if request.method != "POST":
        return render(
            request,
            "main/home.html",
            {
                "message": "PDF 업로드는 POST 방식으로만 가능합니다.",
            },
        )

    pdf_file = request.FILES.get("pdf_file")

    if not pdf_file:
        return render(
            request,
            "main/home.html",
            {
                "message": "업로드할 PDF 파일을 선택해주세요.",
            },
        )

    # 보안취약점 : 내부 스크립트 공격 검사불가 
    if not pdf_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "main/home.html",
            {
                "message": "PDF 파일만 업로드할 수 있습니다.",
            },
        )

    upload_folder = os.path.join(
        settings.MEDIA_ROOT,
        "uploads",
    )

    os.makedirs(
        upload_folder,
        exist_ok=True,
    )

    # 파일중복방지
    saved_filename = f"{uuid.uuid4()}_{pdf_file.name}"

    saved_path = os.path.join(
        upload_folder,
        saved_filename,
    )

    with open(saved_path, "wb+") as destination:
        for chunk in pdf_file.chunks():
            destination.write(chunk)

    result = save_pdf_to_vector_db(
        pdf_path=saved_path,
        original_filename=pdf_file.name,
    )

    return render(
        request,
        "main/home.html",
        {
            "message": result["message"],
            "upload_success": result["success"],
        },
    )


def ask_question(request):
    if request.method != "POST":
        return render(
            request,
            "main/home.html",
            {
                "message": "질문은 POST 방식으로만 보낼 수 있습니다.",
            },
        )

    question = request.POST.get(
        "question",
        "",
    ).strip()

    if not question:
        return render(
            request,
            "main/home.html",
            {
                "message": "질문을 입력해주세요.",
            },
        )

    try:
        answer = ask_rag(question)

        return render(
            request,
            "main/home.html",
            {
                "question": question,
                "answer": answer,
            },
        )

    except Exception as error:
        return render(
            request,
            "main/home.html",
            {
                "message": f"답변 생성 중 오류가 발생했습니다: {error}",
            },
        )
