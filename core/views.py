from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password 
from .models import Utilizador, Produto, Servico, Categoria, Curso, Compras, Mensagem, Suporte, SuporteMensagem

@login_required(login_url='/login/')

def dashboard(request):
    # 1. Estatísticas Básicas
    total_users = Utilizador.objects.count()
    produtos_ativos = Produto.objects.filter(ativo=1).count()
    
    # 2. Processar Transações para o Gráfico e Receita
    # Importante: order_by('data_transacao') para o gráfico seguir a linha do tempo
    todas_compras = Compras.objects.all().order_by('data_transacao')
    
    receita_total = 0
    vendas_por_data = {} # Dicionário temporário: {'21/04': 50.0, '22/04': 30.0}

    for t in todas_compras:
        artigo = None
        if t.id_produto:
            artigo = Produto.objects.filter(id=t.id_produto).first()
        elif t.id_servico:
            artigo = Servico.objects.filter(id=t.id_servico).first()

        if artigo and artigo.preco:
            # Limpeza de preço (converte para número real)
            preco_clean = str(artigo.preco).replace('€', '').replace(' ', '').replace(',', '.')
            try:
                valor = float(preco_clean)
                receita_total += valor
                
                # Agrupar por dia (Formato: Dia/Mês)
                dia_mes = t.data_transacao.strftime('%d/%m')
                vendas_por_data[dia_mes] = vendas_por_data.get(dia_mes, 0) + valor
            except ValueError:
                pass

    # 3. Preparar Listas para o JavaScript
    labels_grafico = list(vendas_por_data.keys())
    valores_grafico = list(vendas_por_data.values())

    # 4. Produtos Recentes (Tabela)
    produtos_recentes = Produto.objects.filter(ativo=1).order_by('-id')[:5]
    for p in produtos_recentes:
        vendedor = Utilizador.objects.filter(id=p.id_utilizador).first()
        p.nome_vendedor = vendedor.nome if vendedor else "Removido"

    # 5. Serviços Recentes (Nova Tabela)
    servicos_recentes = Servico.objects.filter(ativo=1).order_by('-id')[:5]
    for s in servicos_recentes:
        vendedor = Utilizador.objects.filter(id=s.id_utilizador).first()
        s.nome_vendedor = vendedor.nome if vendedor else "Removido"

    contexto = {
        'total_utilizadores': total_users,
        'produtos_ativos': produtos_ativos,
        'total_transacoes': len(todas_compras),
        'receita_total': round(receita_total, 2),
        'produtos_recentes': produtos_recentes,
        'servicos_recentes': servicos_recentes, # <-- Adicionado ao contexto
        # Variáveis do Gráfico
        'labels_grafico': labels_grafico,
        'dados_grafico': valores_grafico,
    }
    
    return render(request, 'core/dashboard.html', contexto)
    
def lista_utilizadores(request):
    
    # O SEGREDO ESTÁ AQUI: Usar .all() para trazer TODOS (ativos e inativos)
    todos_utilizadores = Utilizador.objects.all()
    
    # A LINHA NOVA: Conta o total de utilizadores na base de dados
    total_users = todos_utilizadores.count() 
    
    for aluno in todos_utilizadores:
        # 1. Tratar do Curso
        curso = Curso.objects.filter(id=aluno.id_curso).first()
        aluno.nome_curso = curso.nome if curso else "Curso Desconhecido"
        
        # 2. Tratar da Fotografia
        foto_str = str(aluno.foto_perfil) if aluno.foto_perfil else ""
        
        if foto_str.startswith('http'):
            aluno.foto_url = foto_str
        elif foto_str and not foto_str.startswith('file:///'):
            try:
                aluno.foto_url = aluno.foto_perfil.url
            except:
                aluno.foto_url = None
        else:
            aluno.foto_url = None
    
    contexto = {
        'utilizadores': todos_utilizadores,
        'total_utilizadores': total_users # <-- Não te esqueças de passar a variável para o contexto!
    }
    return render(request, 'core/utilizadores.html', contexto)

def lista_produtos(request):
    
    todos_produtos = Produto.objects.all()
    todos_servicos = Servico.objects.all()

    # ADICIONADO: O parâmetro 'tipo' para sabermos onde procurar na tabela de Compras
    def preparar_item(item, tipo):
        categoria = Categoria.objects.filter(id=item.id_categoria).first()
        item.nome_categoria = categoria.nome if categoria else "Sem Categoria"
            
        vendedor = Utilizador.objects.filter(id=item.id_utilizador).first()
        if vendedor:
            item.nome_vendedor = vendedor.nome
            item.id_vendedor = vendedor.id 
        else:
            item.nome_vendedor = "Utilizador Removido"
            item.id_vendedor = "N/A"        
        
        # --- VERIFICAR SE FOI VENDIDO (NOVO) ---
        if tipo == 'produto':
            # Verifica se existe algum registo na tabela Compras com este id_produto
            item.foi_vendido = Compras.objects.filter(id_produto=item.id).exists()
        elif tipo == 'servico':
            # Verifica se existe algum registo na tabela Compras com este id_servico
            item.foi_vendido = Compras.objects.filter(id_servico=item.id).exists()
        else:
            item.foi_vendido = False
            
        # --- LÓGICA DAS IMAGENS ---
        foto_str = str(item.foto) if item.foto else ""
        
        if foto_str.startswith('http'):
            item.foto_url = foto_str
        elif foto_str and not foto_str.startswith('file:///'):
            try:
                item.foto_url = item.foto.url
            except:
                item.foto_url = None
        else:
            item.foto_url = None
            
        return item

    # ADICIONADO: Passamos a palavra 'produto' ou 'servico' para a função
    produtos_finais = [preparar_item(p, 'produto') for p in todos_produtos]
    servicos_finais = [preparar_item(s, 'servico') for s in todos_servicos]

    contexto = {
        'produtos': produtos_finais,
        'servicos': servicos_finais,
        'total_itens': len(produtos_finais) + len(servicos_finais)
    }
    
    return render(request, 'core/produtos.html', contexto)

def editar_aluno(request, id):
    aluno = Utilizador.objects.filter(id=id).first()
    cursos = Curso.objects.all()

    if request.method == 'POST':
        aluno.nome = request.POST.get('nome')
        aluno.email = request.POST.get('email')
        aluno.ano = request.POST.get('ano')
        aluno.id_curso = request.POST.get('id_curso')
        
        if request.POST.get('ativo'):
            aluno.ativo = 1
        else:
            aluno.ativo = 0

        aluno.save()
        return redirect('/utilizadores/') 

    contexto = {
        'aluno': aluno,
        'cursos': cursos,
    }
    return render(request, 'core/editar_aluno.html', contexto)

def editar_produto(request, id):
    produto = Produto.objects.filter(id=id).first()
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        produto.titulo = request.POST.get('titulo')
        produto.descricao = request.POST.get('descricao')
        produto.preco = request.POST.get('preco')
        produto.estado = request.POST.get('estado')
        produto.local_entrega = request.POST.get('local_entrega')
        produto.id_categoria = request.POST.get('id_categoria')
        
        if request.POST.get('ativo'):
            produto.ativo = 1
        else:
            produto.ativo = 0

        produto.save()
        return redirect('/produtos/')

    return render(request, 'core/editar_produto.html', {'produto': produto, 'categorias': categorias})

def editar_servico(request, id):
    servico = Servico.objects.filter(id=id).first()
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        servico.titulo = request.POST.get('titulo')
        servico.descricao = request.POST.get('descricao')
        servico.preco = request.POST.get('preco')
        servico.local_entrega = request.POST.get('local_entrega')
        servico.id_categoria = request.POST.get('id_categoria')
        
        if request.POST.get('ativo'):
            servico.ativo = 1
        else:
            servico.ativo = 0

        servico.save()
        return redirect('/produtos/')

    return render(request, 'core/editar_servico.html', {'servico': servico, 'categorias': categorias})

def lista_transacoes(request):
    todas_compras = Compras.objects.all().order_by('-data_transacao')
    lista_final = []

    for t in todas_compras:
        # 1. O COMPRADOR (quem fez a compra -> id_utilizador)
        comprador = Utilizador.objects.filter(id=t.id_utilizador).first()
        t.nome_comprador = comprador.nome if comprador else "Desconhecido"
        
        # 2. O VENDEDOR (quem vendeu -> id_vendedor)
        vendedor = Utilizador.objects.filter(id=t.id_vendedor).first()
        if vendedor:
            t.id_vendedor_venda = vendedor.id
            t.nome_vendedor = vendedor.nome
        else:
            t.id_vendedor_venda = "N/A"
            t.nome_vendedor = "Desconhecido"
            
        # 3. Descobrir os dados do Artigo (Nome e Preço)
        if t.id_produto:
            produto = Produto.objects.filter(id=t.id_produto).first()
            if produto:
                t.artigo = produto.titulo
                t.preco = produto.preco
                t.tipo = "Produto"
            else:
                t.artigo = "Produto Apagado"
                t.preco = 0
                t.tipo = "Produto"
                
        elif t.id_servico:
            servico = Servico.objects.filter(id=t.id_servico).first()
            if servico:
                t.artigo = servico.titulo
                t.preco = servico.preco
                t.tipo = "Serviço"
            else:
                t.artigo = "Serviço Apagado"
                t.preco = 0
                t.tipo = "Serviço"
        else:
            t.artigo = "Desconhecido"
            t.preco = 0
            t.tipo = "N/A"
            
        lista_final.append(t)

    # 4. Cálculo da Receita Segura
    receita_total = 0
    for item in lista_final:
        # Verifica se o artigo tem preço
        if hasattr(item, 'preco') and item.preco:
            # 1º Transformamos o valor numa string de texto
            preco_str = str(item.preco)
            
            # 2º Apagamos os símbolos de Euro e os espaços, e trocamos a vírgula por ponto
            preco_str = preco_str.replace('€', '').replace(' ', '').replace(',', '.')
            
            try:
                # 3º O Python agora consegue converter um texto limpo (ex: "15.00") em número e somar
                receita_total += float(preco_str)
            except ValueError:
                # Se alguém tiver escrito "Grátis" no preço, ele ignora sem dar erro
                pass 

    contexto = {
        'transacoes': lista_final,
        'total_transacoes': len(lista_final),
        'receita_total': round(receita_total, 2)
    }
    return render(request, 'core/transacoes.html', contexto)
def chat(request):
    # 1. Vai buscar todas as mensagens ordenadas da mais recente para a mais antiga
    todas_mensagens = Mensagem.objects.all().order_by('-data_envio')
    
    # 2. Calcular os totais para os teus Cartões de Resumo
    total_mensagens = todas_mensagens.count()
    mensagens_lidas = todas_mensagens.filter(lida=True).count()
    mensagens_inativas = todas_mensagens.filter(ativo=0).count()

    lista_final = []

    # 3. Descobrir quem é o Remetente de cada mensagem
    for m in todas_mensagens:
        remetente = Utilizador.objects.filter(id=m.id_remetente).first()
        
        if remetente:
            m.nome_remetente = remetente.nome
        else:
            m.nome_remetente = "Utilizador Removido"
            
        lista_final.append(m)

    # 4. Enviar os dados todos empacotados para o HTML
    contexto = {
        'mensagens': lista_final,
        'total_mensagens': total_mensagens,
        'mensagens_lidas': mensagens_lidas,
        'mensagens_inativas': mensagens_inativas,
    }
    
    return render(request, 'core/chat.html', contexto)

def login_admin(request):
    # Se o admin já tiver sessão iniciada, manda-o logo para o dashboard
    if request.user.is_authenticated:
        return redirect('/dashboard/') # Confirma se o teu URL é este

    if request.method == 'POST':
        utilizador = request.POST.get('username')
        palavra_passe = request.POST.get('password')
        
        # O Django verifica se o user e password existem e estão corretos
        user = authenticate(request, username=utilizador, password=palavra_passe)
        
        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            # Se errar a password, enviamos uma mensagem de erro
            messages.error(request, 'Utilizador ou palavra-passe incorretos.')

    return render(request, 'core/login.html')

def adicionar_aluno(request):
    if request.method == 'POST':
        # 1. Apanhar os dados
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        password_texto = request.POST.get('password') # Password normal
        id_curso = request.POST.get('curso')
        ano = request.POST.get('ano')
        ativo = 1 if request.POST.get('ativo') == 'on' else 0

        # 2. Encriptar a password (Hash)
        password_hash = make_password(password_texto)

        # 3. Gravar na base de dados
        novo_aluno = Utilizador(
            nome=nome,
            email=email,
            password=password_hash, # <-- Agora guarda o hash de segurança!
            id_curso=id_curso,
            ano=ano,
            ativo=ativo
        )
        novo_aluno.save()

        return redirect('utilizadores')

    cursos = Curso.objects.all()
    contexto = {
        'cursos': cursos
    }
    return render(request, 'core/adicionar_aluno.html', contexto)

def ocultar_mensagem(request, id):
    # Procura a mensagem na base de dados
    mensagem = Mensagem.objects.filter(id=id).first()
    
    if mensagem:
        # Se for 1 muda para 0, se for 0 muda para 1 (efeito interruptor)
        mensagem.ativo = 0 if mensagem.ativo == 1 else 1
        mensagem.save()
        
    # Redireciona de volta para a página do chat (confirma se o nome no urls.py é 'chat')
    return redirect('chat')
from django.shortcuts import render, redirect

def lista_suporte(request):
    # Vai buscar todos os tickets, ordenados pelos mais recentes primeiro
    tickets = Suporte.objects.all().order_by('-data_envio')
    
    # Calcular métricas para os cartões
    total = tickets.count()
    pendentes = tickets.filter(resolvido=False).count()
    resolvidos = tickets.filter(resolvido=True).count()
    
    contexto = {
        'tickets': tickets,
        'total': total,
        'pendentes': pendentes,
        'resolvidos': resolvidos
    }
    return render(request, 'core/suporte.html', contexto)

def lista_suporte(request):
    # Vai buscar todos os tickets à tabela do Supabase
    tickets = Suporte.objects.all().order_by('-data_envio')
    
    # Cálculos para os cartões de estatísticas
    contexto = {
        'tickets': tickets,
        'total': tickets.count(),
        'pendentes': tickets.filter(resolvido=False).count(),
        'resolvidos': tickets.filter(resolvido=True).count()
    }
    return render(request, 'core/suporte.html', contexto)

def detalhe_suporte(request, id):
    # 1. Carregar o ticket e as mensagens
    ticket = Suporte.objects.filter(id=id).first()
    mensagens = SuporteMensagem.objects.filter(ticket_id=id).order_by('data_envio')
    
    if request.method == 'POST':
        # 2. Se a ação foi "Enviar Mensagem"
        if 'enviar_mensagem' in request.POST:
            texto = request.POST.get('nova_mensagem')
            if texto:
                nova_msg = SuporteMensagem(
                    ticket_id=id,
                    remetente='admin',
                    mensagem=texto
                )
                nova_msg.save()
            # Redireciona para a PRÓPRIA página para veres a mensagem a aparecer no chat
            return redirect('detalhe_suporte', id=id)

        # 3. Se a ação foi "Guardar Estado" (Resolver)
        elif 'resolver_ticket' in request.POST:
            estado_resolvido = True if request.POST.get('resolvido') == 'on' else False
            ticket.resolvido = estado_resolvido
            ticket.save()
            # Redireciona para a lista principal de suporte
            return redirect('suporte') 
        
    contexto = {
        'ticket': ticket,
        'mensagens': mensagens
    }
    return render(request, 'core/detalhe_suporte.html', contexto)
def logout_admin(request):
    logout(request)
    return redirect('/login/')