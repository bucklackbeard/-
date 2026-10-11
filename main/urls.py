from django.urls import path

from . import views

# 127.0.0.1로 접속하면 home.html 보여줌
# pdf 첨부하면(POST요청) pdf업로드 실행함
# 질문폼 제출하면 질의응답 실행함

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_pdf, name="upload_pdf"),
    path("ask/", views.ask_question, name="ask_question"),
]
