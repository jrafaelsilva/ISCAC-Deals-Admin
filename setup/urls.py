"""
URL configuration for setup project.
... (comentários originais do Django omitidos para ficar mais limpo) ...
"""
from django.contrib import admin
from django.urls import path
from core.views import dashboard, lista_utilizadores, lista_produtos, lista_transacoes,chat, editar_aluno, editar_produto, editar_servico, adicionar_aluno, ocultar_mensagem, lista_suporte, detalhe_suporte, login_admin, logout_admin

# 1. ADICIONA ESTES DOIS IMPORTS PARA AS IMAGENS
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='home'),
    path('dashboard/', dashboard, name='dashboard'), 
    path('utilizadores/', lista_utilizadores, name='utilizadores'),
    path('produtos/', lista_produtos, name='produtos'),
    path('transacoes/', lista_transacoes, name='transacoes'),
    path('chat/', chat, name='chat'),
    path('editar_aluno/<int:id>/', editar_aluno, name='editar_aluno'),
    path('editar_produto/<int:id>/', editar_produto, name='editar_produto'),
    path('editar_servico/<int:id>/', editar_servico, name='editar_servico'),
    path('adicionar_aluno/', adicionar_aluno, name='adicionar_aluno'),
    path('ocultar_mensagem/<str:id>/', ocultar_mensagem, name='ocultar_mensagem'),  
    path('suporte/', lista_suporte, name='suporte'),
    path('suporte/<int:id>/', detalhe_suporte, name='detalhe_suporte'),  
    path('login/', login_admin, name='login'),
    path('logout/', logout_admin, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)