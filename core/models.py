from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import uuid

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='categorias/', null=True, blank=True)

    def __str__(self):
        return self.nome

class Curso(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Utilizador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True) 
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True, max_length=254)
    ano = models.IntegerField()
    id_curso = models.IntegerField() 
    password = models.CharField(max_length=128)
    data_registo = models.DateTimeField(auto_now_add=True)
    ativo = models.IntegerField(default=1)
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1. CRIAR CONTA OFICIAL: O Django precisa da password em texto limpo aqui
        if not self.user_id:
            username_gerado = self.email.split('@')[0]
            novo_user = User.objects.create_user(
                username=username_gerado,
                email=self.email,
                password=self.password # Usa o texto normal ("admin123")
            )
            self.user_id = novo_user.id

        # 2. PROTEGER A TUA TABELA: Fazer o Hash da password para a app móvel
        # A condição 'pbkdf2_' impede que a password seja encriptada duas vezes 
        # caso vás editar o curso ou o nome deste aluno mais tarde.
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    titulo = models.CharField(max_length=200)
    id_utilizador = models.IntegerField()
    id_categoria = models.IntegerField() 
    preco = models.CharField(max_length=50)
    local_entrega = models.CharField(max_length=255)
    descricao = models.TextField()
    estado = models.CharField(max_length=50)
    ativo = models.IntegerField(default=1) 
    foto = models.ImageField(upload_to='produtos/', null=True, blank=True)

    def __str__(self):
        return self.titulo

class Servico(models.Model):
    titulo = models.CharField(max_length=200)
    id_utilizador = models.IntegerField()
    id_categoria = models.IntegerField()
    preco = models.CharField(max_length=50)
    formato = models.CharField(max_length=100)
    horario = models.CharField(max_length=100)
    descricao = models.TextField()
    ativo = models.IntegerField(default=1) 
    foto = models.ImageField(upload_to='servicos/', null=True, blank=True)

    def __str__(self):
        return self.titulo

class Avaliacao(models.Model):
    id_utilizador = models.IntegerField()
    id_servico = models.IntegerField()
    estrelas = models.IntegerField() 

    def __str__(self):
        return f"{self.estrelas} estrelas - Serviço {self.id_servico}"

class Favorito(models.Model):
    id_utilizador = models.IntegerField()
    id_servico = models.IntegerField(null=True, blank=True)
    id_produto = models.IntegerField(null=True, blank=True)
    ativo = models.IntegerField(default=1) 

class Compras(models.Model):
    # Identificadores diretos (Sem Foreign Keys)
    id_utilizador = models.IntegerField() 
    id_vendedor = models.IntegerField(null=True, blank=True)
    # Podem ser nulos porque uma transação ou é de um produto, ou de um serviço
    id_produto = models.IntegerField(null=True, blank=True) 
    id_servico = models.IntegerField(null=True, blank=True) 
    
    # Campo preço removido conforme pedido
    
    # Regista automaticamente a data e hora em que a compra é feita
    data_transacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.id_produto:
            return f"Transação: Produto {self.id_produto} (User: {self.id_utilizador})"
        elif self.id_servico:
            return f"Transação: Serviço {self.id_servico} (User: {self.id_utilizador})"
        return f"Transação Desconhecida (User: {self.id_utilizador})"
    
class Mensagem(models.Model):
    # O ID no teu Supabase é um UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificadores da Conversa e do Remetente
    id_conversa = models.UUIDField()
    id_remetente = models.IntegerField()
    
    # Conteúdo e Estado da Mensagem
    texto = models.TextField()
    lida = models.BooleanField(default=False)
    
    # Regista a data automaticamente ao enviar
    data_envio = models.DateTimeField(auto_now_add=True)
    
    # Campo para a moderação (1 = Ativo, 0 = Oculto/Inativo)
    ativo = models.IntegerField(default=1)

    def __str__(self):
        return f"Mensagem {self.id} - Remetente: {self.id_remetente}"
    
class Suporte(models.Model):
    # O ID é criado automaticamente pelo Django, não precisas de o declarar
    email = models.CharField(max_length=255)
    assunto = models.CharField(max_length=255)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    resolvido = models.BooleanField(default=False)

    class Meta:
        # ATENÇÃO: Coloca aqui o nome EXATO que deste à tabela no Supabase.
        # Se na barra do lado esquerdo do Supabase ela se chama "suporte", deixa assim. 
        # Se for "core_suporte", altera aqui!
        db_table = 'core_suporte' 
        
        # Isto diz ao Django para não tentar recriar ou alterar a estrutura da tabela,
        # visto que tu geres isso diretamente no Supabase.
        managed = False 

    def __str__(self):
        return f"Ticket #{self.id} - {self.assunto}"
    
class SuporteMensagem(models.Model):
    ticket_id = models.IntegerField() 
    remetente = models.CharField(max_length=50)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_suporte_mensagens' # O nome exato da tua nova tabela
        managed = False # O Supabase gere a estrutura

    def __str__(self):
        return f"Mensagem de {self.remetente} (Ticket #{self.ticket_id})"