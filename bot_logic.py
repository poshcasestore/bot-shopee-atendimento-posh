import datetime
import random
import re
import os

# --- Variáveis Globais (agora para armazenar estados por sessão) ---
# Dicionário para armazenar o estado de cada sessão (conversation_id da Shopee)
# Ex: { 'conversation_id_1': { 'ATENDIMENTO_HUMANO_ATIVO': False, 'MEMORIA_USUARIO': {}, ... },
#       'conversation_id_2': { ... } }
SESSAO_ESTADOS = {}

PEDIDO_ID_COUNTER = 1000 # Contador para gerar IDs de pedido (pode ser global, ou por loja)
FINALIZACAO_ATENDENTE_HUMANO_FRASE = "Estou finalizando meu atendimento por aqui, se precisar de mais alguma coisa é só chamar"

# --- Funções Auxiliares ---

def get_sessao_estado(sessao_id):
    """Retorna o estado da sessão para um dado sessao_id, inicializando se necessário."""
    if sessao_id not in SESSAO_ESTADOS:
        SESSAO_ESTADOS[sessao_id] = {
            'ATENDIMENTO_HUMANO_ATIVO': False,
            'MEMORIA_USUARIO': {},
            'ULTIMA_INTERACAO_ATENDENTE_HUMANO': None,
            'CONVERSA_ENCAMINHADA_HUMANO': False,
            'PRIMEIRA_MENSAGEM_RECEBIDA': False,
        }
    return SESSAO_ESTADOS[sessao_id]

def gerar_id_pedido():
    """Gera um ID de pedido único."""
    global PEDIDO_ID_COUNTER
    data_hora = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    PEDIDO_ID_COUNTER += 1
    return f"{data_hora}-{PEDIDO_ID_COUNTER}"

def salvar_personalizacao_nome_txt(nome_gravado, pedido_id, modelo_celular):
    """
    Salva os detalhes de UMA ÚNICA personalização de nome em um arquivo .txt
    na pasta Nomes_Personalizar, com o nome do arquivo formatado como NomeGravado_IDdoPedido.txt.
    """
    diretorio = "Nomes_Personalizar"
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

    # Remove caracteres inválidos do nome do arquivo
    nome_arquivo_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_gravado)
    filename = os.path.join(diretorio, f"{nome_arquivo_limpo}_{pedido_id}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"ID_Pedido: {pedido_id}\n")
        f.write(f"Nome Gravado: {nome_gravado}\n")
        f.write(f"Modelo do Celular: {modelo_celular}\n")
    return filename

def salvar_personalizacao_foto_txt(modelo_tema, nome_arquivo_foto, pedido_id):
    """
    Salva os detalhes de UMA ÚNICA personalização de foto em um arquivo .txt
    na pasta Fotos_Personalizar, com o nome do arquivo formatado como ModeloTema_IDdoPedido.txt.
    """
    diretorio = "Fotos_Personalizar"
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

    # Remove caracteres inválidos do nome do arquivo
    nome_arquivo_limpo = re.sub(r'[\\/*?:"<>|]', "", modelo_tema)
    filename = os.path.join(diretorio, f"{nome_arquivo_limpo}_{pedido_id}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"ID_Pedido: {pedido_id}\n")
        f.write(f"Modelo/Tema: {modelo_tema}\n")
        f.write(f"Nome do Arquivo da Foto: {nome_arquivo_foto}\n")
    return filename

def carregar_regras_loja(filepath="RegrasLoja_v2.txt"):
    """Carrega as regras da loja de um arquivo de texto."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado. Por favor, verifique o caminho.")
        # Retorna um conteúdo mínimo para evitar erros, mas o ideal é que o arquivo exista.
        return """
✔ SAUDACAO_INICIAL
RESPOSTA: Olá! Tudo bem? Eu sou sua assistente virtual. Para eu te ajudar, digite o numero da opção desejada:

✔ MENU_PRINCIPAL
RESPOSTA: Olá! Eu sou sua assistente virtual. Como posso te auxiliar hoje?
1 - Personalizar capinha com nome
2 - Personalizar capinha com foto
3 - Quero consutar se tem capinha para meu modelo de celular ou com algum tema de desenho especifico
4 - Solicitar Devolução/Reembolso
5 - Outras Informações/Dúvidas
6 - Sair do Antendimento

✔ PEDIDO_NOME_JA_ENVIADO
RESPOSTA: Seu pedido de personalização com nome já foi registrado. Para alterar um nome já enviado, é necessário falar com um atendente humano. Se deseja prosseguir com o atendimento humano, digite "Falar com atendimento humano". Caso contrário, por favor, escolha outra opção do menu principal.
"""

REGRAS_LOJA = carregar_regras_loja()

def get_resposta_regra(chave):
    """Extrai a resposta de uma chave específica do REGRAS_LOJA."""
    # Ajuste para garantir que não capture "Frases-exemplo para treinamento:" se existir
    padrao = re.compile(rf"✔ {re.escape(chave)}\n(?:Frases-exemplo para treinamento:.*?\n)?RESPOSTA:\n(.*?)(?=\n----------------------------------------------------------------------|\Z)", re.DOTALL)
    match = padrao.search(REGRAS_LOJA)
    if match:
        return match.group(1).strip()
    return "Desculpe, não encontrei informações sobre isso no momento. Por favor, digite 'Falar com atendimento humano' para obter ajuda."

def exibir_saudacao_inicial():
    """Retorna a saudação inicial."""
    return get_resposta_regra("SAUDACAO_INICIAL")

def exibir_menu_principal():
    """Exibe o menu principal de opções."""
    return get_resposta_regra("MENU_PRINCIPAL")

def exibir_submenu_duvidas():
    """Exibe o submenu de dúvidas e informações."""
    return get_resposta_regra("SUBMENU_DUVIDAS")

# --- Funções de Processamento de Fluxos ---

def processar_personalizacao_nome(sessao_id, user_input):
    """Gerencia o fluxo de personalização de capinha com nome."""
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']

    user_input_lower = user_input.lower().strip()

    if user_input_lower == 'voltar':
        sessao['MEMORIA_USUARIO'] = {} # Limpa a memória da sessão
        return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

    estado = MEMORIA_USUARIO.get('personalizacao_nome_estado', 'inicio')

    if estado == 'inicio':
        MEMORIA_USUARIO['personalizacao_nome_estado'] = 'aguardando_quantidade'
        MEMORIA_USUARIO['detalhes_personalizacao_nome'] = []
        # Resetar a flag de pedido concluído ao iniciar um novo fluxo
        MEMORIA_USUARIO['personalizacao_nome_concluida_recentemente'] = False
        return "Certo! Quantas capinhas você gostaria de personalizar com nome? (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_quantidade':
        try:
            quantidade = int(user_input)
            if quantidade <= 0:
                return "Por favor, digite um número válido de capinhas (maior que zero). (Ou digite 'Voltar' para o menu principal)"
            MEMORIA_USUARIO['quantidade_capinhas_nome'] = quantidade
            MEMORIA_USUARIO['capinha_atual_nome'] = 1
            MEMORIA_USUARIO['personalizacao_nome_estado'] = 'aguardando_modelo_nome'
            return (f"Ok! Para a Capinha {MEMORIA_USUARIO['capinha_atual_nome']}: "
                    "Qual o **modelo do celular ou estampa** e o **nome** que você gostaria de gravar? Lembre-se de separar por vírgula. "
                    "(Exemplos: 'iPhone 13, Alex', 'Capa verde, José', 'Estampa BS-056, João') (Ou digite 'Voltar' para o menu principal)")
        except ValueError:
            return "Por favor, digite um número válido. (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_modelo_nome':
        # Espera "modelo, nome"
        partes = [p.strip() for p in user_input.split(',', 1)]
        if len(partes) < 2:
            return ("Por favor, digite o modelo do celular ou estampa e o nome separados por vírgula. "
                    "(Exemplos: 'iPhone 13, Alex', 'Capa verde, José', 'Estampa BS-056, João') (Ou digite 'Voltar' para o menu principal)")

        modelo = partes[0]
        # Remove a palavra "nome" se ela estiver no início do nome gravado
        nome_gravado = re.sub(r'^(nome\s*)', '', partes[1], flags=re.IGNORECASE).strip()

        if len(nome_gravado) > 20 or not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nome_gravado):
            # Armazena o modelo e o nome inválido para possível correção
            MEMORIA_USUARIO['modelo_para_correcao'] = modelo
            MEMORIA_USUARIO['nome_para_correcao'] = nome_gravado
            MEMORIA_USUARIO['personalizacao_nome_estado'] = 'aguardando_correcao_nome'
            return (f"Para que sua capinha com o nome '{nome_gravado}' fique perfeita, "
                    "diga um nome menor, até 20 caracteres, sem símbolos ou emojis. "
                    "Ou digite 'Voltar' para o menu principal.")

        MEMORIA_USUARIO['detalhes_personalizacao_nome'].append({'modelo': modelo, 'nome': nome_gravado})
        MEMORIA_USUARIO['capinha_atual_nome'] += 1

        if MEMORIA_USUARIO['capinha_atual_nome'] <= MEMORIA_USUARIO['quantidade_capinhas_nome']:
            return (f"Certo! Para a Capinha {MEMORIA_USUARIO['capinha_atual_nome']}: "
                    "Qual o **modelo do celular ou estampa** e o **nome** que você gostaria de gravar? Lembre-se de separar por vírgula. "
                    "(Exemplos: 'Samsung S21, Maria', 'Capa azul, Pedro', 'Estampa BS-057, Ana') (Ou digite 'Voltar' para o menu principal)")
        else:
            MEMORIA_USUARIO['personalizacao_nome_estado'] = 'confirmacao_final'
            detalhes_str = "\n".join([f"- Modelo: {d['modelo']}, Nome: {d['nome']}" for d in MEMORIA_USUARIO['detalhes_personalizacao_nome']])
            return (f"Perfeito! Suas personalizações são:\n{detalhes_str}\n"
                    "Está tudo correto? (Sim/Não) (Ou digite 'Voltar' para o menu principal)")

    elif estado == 'aguardando_correcao_nome':
        # O usuário está corrigindo o nome de uma capinha específica
        if user_input_lower == 'voltar':
            sessao['MEMORIA_USUARIO'] = {}
            return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

        novo_nome = re.sub(r'^(nome\s*)', '', user_input, flags=re.IGNORECASE).strip() # Assume que o usuário está dando apenas o novo nome

        if len(novo_nome) > 20 or not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', novo_nome):
            return (f"Ainda não consegui entender o nome. Por favor, diga um nome menor, até 20 caracteres, "
                    "sem símbolos ou emojis. (Ou digite 'Voltar' para o menu principal)")

        # Pega o modelo que estava sendo corrigido (do item que causou o erro)
        modelo_corrigido = MEMORIA_USUARIO.get('modelo_para_correcao', 'Modelo Desconhecido')

        # Se o erro ocorreu ao adicionar um novo item, remove o inválido e adiciona o corrigido
        if 'nome_para_correcao' in MEMORIA_USUARIO:
            MEMORIA_USUARIO['detalhes_personalizacao_nome'].append({'modelo': modelo_corrigido, 'nome': novo_nome})
            # Não incrementa capinha_atual_nome aqui, pois já foi incrementado antes do erro
            # e o erro impediu a transição de estado.
            # Apenas limpa os dados de correção e volta ao fluxo normal.
            del MEMORIA_USUARIO['modelo_para_correcao']
            del MEMORIA_USUARIO['nome_para_correcao']

            if MEMORIA_USUARIO['capinha_atual_nome'] <= MEMORIA_USUARIO['quantidade_capinhas_nome']:
                MEMORIA_USUARIO['personalizacao_nome_estado'] = 'aguardando_modelo_nome'
                return (f"Certo! Para a Capinha {MEMORIA_USUARIO['capinha_atual_nome']}: "
                        "Qual o **modelo do celular ou estampa** e o **nome** que você gostaria de gravar? Lembre-se de separar por vírgula. "
                        "(Exemplos: 'Samsung S21, Maria', 'Capa azul, Pedro', 'Estampa BS-057, Ana') (Ou digite 'Voltar' para o menu principal)")
            else:
                MEMORIA_USUARIO['personalizacao_nome_estado'] = 'confirmacao_final'
                detalhes_str = "\n".join([f"- Modelo: {d['modelo']}, Nome: {d['nome']}" for d in MEMORIA_USUARIO['detalhes_personalizacao_nome']])
                return (f"Perfeito! Suas personalizações são:\n{detalhes_str}\n"
                        "Está tudo correto? (Sim/Não) (Ou digite 'Voltar' para o menu principal)")
        else:
            # Este caso não deveria ser atingido se o fluxo for sempre de adicionar um novo item
            # e depois corrigir. Mas como fallback, se não houver 'nome_para_correcao',
            # o bot não sabe qual item corrigir.
            return "Desculpe, não consegui aplicar a correção. Por favor, tente novamente ou digite 'Voltar'."

    elif estado == 'confirmacao_final':
        if user_input_lower == 'sim':
            pedido_id = gerar_id_pedido()
            # Loop para salvar cada capinha em um arquivo separado
            for item in MEMORIA_USUARIO['detalhes_personalizacao_nome']:
                salvar_personalizacao_nome_txt(item['nome'], pedido_id, item['modelo'])

            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória após a conclusão do fluxo
            sessao['MEMORIA_USUARIO']['personalizacao_nome_concluida_recentemente'] = True # Marca que um pedido foi concluído
            sessao['MEMORIA_USUARIO']['last_action_completed'] = 'personalizacao_nome_concluida' # Novo estado para gerenciar as opções pós-confirmação
            return (f"Ótimo! Seu pedido de personalização com nome (ID: {pedido_id}) foi registrado e será processado. "
                    "Em breve você receberá mais informações. "
                    "O que você gostaria de fazer agora?\n"
                    "1 - Voltar ao menu principal\n"
                    "2 - Sair do atendimento")
        elif user_input_lower == 'não' or user_input_lower == 'nao':
            MEMORIA_USUARIO['personalizacao_nome_estado'] = 'aguardando_correcao_final'
            detalhes_str = "\n".join([f"- Capinha {i+1}: Modelo: {d['modelo']}, Nome: {d['nome']}" for i, d in enumerate(MEMORIA_USUARIO['detalhes_personalizacao_nome'])])
            return (f"Ah, entendi! O que você gostaria de corrigir?\n"
                    f"Suas personalizações atuais são:\n{detalhes_str}\n"
                    "Por favor, diga o número da capinha e o novo nome. (Ex: Capinha 1, Novo Nome) "
                    "Ou digite 'Voltar' para o menu principal para recomeçar.")
        else:
            return "Por favor, responda 'Sim' ou 'Não'. (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_correcao_final':
        if user_input_lower == 'voltar':
            sessao['MEMORIA_USUARIO'] = {}
            return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

        # Tenta extrair o número da capinha e o nome
        match_capinha_nome = re.match(r'^(?:capinha\s*(\d+),\s*)?(.*)$', user_input_lower, re.IGNORECASE)

        capinha_idx = -1
        novo_nome = ""

        if match_capinha_nome:
            capinha_num_str = match_capinha_nome.group(1)
            nome_input = match_capinha_nome.group(2)
            novo_nome = re.sub(r'^(nome\s*)', '', nome_input, flags=re.IGNORECASE).strip()

            if capinha_num_str:
                capinha_idx = int(capinha_num_str) - 1
            elif len(MEMORIA_USUARIO['detalhes_personalizacao_nome']) == 1:
                # Se só há uma capinha, assume que a correção é para ela
                capinha_idx = 0
            else:
                # Se há múltiplas capinhas e o número não foi especificado
                return ("Desculpe, não consegui identificar para qual capinha é o novo nome. "
                        "Por favor, diga o número da capinha e o novo nome. "
                        "(Exemplos: 'Capinha 1, Novo Nome') "
                        "Ou digite 'Voltar' para o menu principal.")
        else:
            # Se não houver match, pode ser apenas um nome, mas precisamos do índice
            # Aqui, se o usuário digitou apenas um nome, e há apenas uma capinha, aplica a ela.
            if len(MEMORIA_USUARIO['detalhes_personalizacao_nome']) == 1:
                capinha_idx = 0
                novo_nome = re.sub(r'^(nome\s*)', '', user_input, flags=re.IGNORECASE).strip()
            else:
                return ("Desculpe, não consegui identificar para qual capinha é o novo nome. "
                        "Por favor, diga o número da capinha e o novo nome. "
                        "(Exemplos: 'Capinha 1, Novo Nome') "
                        "Ou digite 'Voltar' para o menu principal.")

        if not (0 <= capinha_idx < len(MEMORIA_USUARIO['detalhes_personalizacao_nome'])):
            return "Número de capinha inválido. Por favor, digite um número de capinha existente. (Ou digite 'Voltar' para o menu principal)"

        if len(novo_nome) > 20 or not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', novo_nome):
            return (f"O nome '{novo_nome}' é inválido. Por favor, diga um nome menor, até 20 caracteres, "
                    "sem símbolos ou emojis. (Ou digite 'Voltar' para o menu principal)")

        MEMORIA_USUARIO['detalhes_personalizacao_nome'][capinha_idx]['nome'] = novo_nome
        MEMORIA_USUARIO['personalizacao_nome_estado'] = 'confirmacao_final' # Volta para a confirmação
        detalhes_str = "\n".join([f"- Modelo: {d['modelo']}, Nome: {d['nome']}" for d in MEMORIA_USUARIO['detalhes_personalizacao_nome']])
        return (f"Nome da Capinha {capinha_idx+1} atualizado para '{novo_nome}'.\n"
                f"Suas personalizações são:\n{detalhes_str}\n"
                "Está tudo correto agora? (Sim/Não) (Ou digite 'Voltar' para o menu principal)")

    return "Desculpe, não entendi. Por favor, digite 'Voltar' para o menu principal."

def processar_personalizacao_foto(sessao_id, user_input):
    """Gerencia o fluxo de personalização de capinha com foto."""
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']

    user_input_lower = user_input.lower().strip()

    if user_input_lower == 'voltar':
        sessao['MEMORIA_USUARIO'] = {}
        return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

    estado = MEMORIA_USUARIO.get('personalizacao_foto_estado', 'inicio')

    if estado == 'inicio':
        MEMORIA_USUARIO['personalizacao_foto_estado'] = 'aguardando_quantidade'
        MEMORIA_USUARIO['detalhes_personalizacao_foto'] = []
        return "Certo! Quantas capinhas você gostaria de personalizar com foto? (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_quantidade':
        try:
            quantidade = int(user_input)
            if quantidade <= 0:
                return "Por favor, digite um número válido de capinhas (maior que zero). (Ou digite 'Voltar' para o menu principal)"
            MEMORIA_USUARIO['quantidade_capinhas_foto'] = quantidade
            MEMORIA_USUARIO['capinha_atual_foto'] = 1
            MEMORIA_USUARIO['personalizacao_foto_estado'] = 'aguardando_modelo_foto'
            return (f"Ok! Para a Capinha {MEMORIA_USUARIO['capinha_atual_foto']}: "
                    "Qual o modelo do celular ou tema da capinha? (Ex: iPhone 13, Tema Flores) (Ou digite 'Voltar' para o menu principal)")
        except ValueError:
            return "Por favor, digite um número válido. (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_modelo_foto':
        modelo_tema = user_input.strip()
        if not modelo_tema:
            return ("Por favor, digite o modelo do celular ou tema da capinha. "
                    "(Ex: iPhone 13, Tema Flores) (Ou digite 'Voltar' para o menu principal)")

        # Armazena o modelo/tema temporariamente para a capinha atual
        MEMORIA_USUARIO['modelo_tema_atual_foto'] = modelo_tema
        MEMORIA_USUARIO['personalizacao_foto_estado'] = 'aguardando_upload_foto'
        return (f"Certo, para a Capinha {MEMORIA_USUARIO['capinha_atual_foto']} ({modelo_tema}): "
                "Agora, por favor, envie a foto que você gostaria de usar. "
                "(Você pode digitar o nome do arquivo da foto, ex: minha_foto.jpg) (Ou digite 'Voltar' para o menu principal)")

    elif estado == 'aguardando_upload_foto':
        nome_arquivo_foto = user_input.strip()
        # Validação para reconhecer se é um "envio de imagem" (simulado por nome de arquivo)
        if not re.search(r'\.(jpg|jpeg|png|gif)$', nome_arquivo_foto, re.IGNORECASE):
            return ("Não consegui identificar um arquivo de imagem. Por favor, envie a foto "
                    "digitando o nome do arquivo (ex: minha_foto.jpg, foto_do_pet.png). "
                    "(Ou digite 'Voltar' para o menu principal)")

        modelo_tema = MEMORIA_USUARIO.pop('modelo_tema_atual_foto') # Pega o modelo/tema salvo
        MEMORIA_USUARIO['detalhes_personalizacao_foto'].append({'tema': modelo_tema, 'nome_arquivo_foto': nome_arquivo_foto})
        MEMORIA_USUARIO['capinha_atual_foto'] += 1

        if MEMORIA_USUARIO['capinha_atual_foto'] <= MEMORIA_USUARIO['quantidade_capinhas_foto']:
            MEMORIA_USUARIO['personalizacao_foto_estado'] = 'aguardando_modelo_foto'
            return (f"Ótimo! Foto recebida para a Capinha {MEMORIA_USUARIO['capinha_atual_foto']-1}. "
                    f"Agora, para a Capinha {MEMORIA_USUARIO['capinha_atual_foto']}: "
                    "Qual o modelo do celular ou tema da capinha? (Ex: Samsung S21, Outro Tema) (Ou digite 'Voltar' para o menu principal)")
        else:
            MEMORIA_USUARIO['personalizacao_foto_estado'] = 'confirmacao_final'
            detalhes_str = "\n".join([f"- Capinha {i+1}: Modelo/Tema: {d['tema']}, Foto: {d['nome_arquivo_foto']}" for i, d in enumerate(MEMORIA_USUARIO['detalhes_personalizacao_foto'])])
            return (f"Perfeito! Suas personalizações com foto são:\n{detalhes_str}\n"
                    "Está tudo correto? (Sim/Não) (Ou digite 'Voltar' para o menu principal)")

    elif estado == 'confirmacao_final':
        if user_input_lower == 'sim':
            pedido_id = gerar_id_pedido()
            # Loop para salvar cada capinha em um arquivo separado
            for item in MEMORIA_USUARIO['detalhes_personalizacao_foto']:
                salvar_personalizacao_foto_txt(item['tema'], item['nome_arquivo_foto'], pedido_id)

            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória após a conclusão
            sessao['MEMORIA_USUARIO']['last_action_completed'] = 'personalizacao_foto_concluida' # Novo estado para gerenciar as opções pós-confirmação
            return (f"Ótimo! Seu pedido de personalização com foto (ID: {pedido_id}) foi registrado e será processado. "
                    "Caso haja alguma irregularidade na foto, um atendente humano entrará em contato para resolver. "
                    "O que você gostaria de fazer agora?\n"
                    "1 - Voltar ao menu principal\n"
                    "2 - Sair do atendimento")
        elif user_input_lower == 'não' or user_input_lower == 'nao':
            MEMORIA_USUARIO['personalizacao_foto_estado'] = 'aguardando_correcao_final'
            detalhes_str = "\n".join([f"- Capinha {i+1}: Modelo/Tema: {d['tema']}, Foto: {d['nome_arquivo_foto']}" for i, d in enumerate(MEMORIA_USUARIO['detalhes_personalizacao_foto'])])
            return (f"Ah, entendi! O que você gostaria de corrigir?\n"
                    f"Suas personalizações atuais são:\n{detalhes_str}\n"
                    "Por favor, diga o número da capinha, o novo modelo/tema e o nome do arquivo da foto. "
                    "(Ex: Capinha 1, iPhone 13, nova_foto.jpg) "
                    "Ou digite 'Voltar' para o menu principal para recomeçar.")
        else:
            return "Por favor, responda 'Sim' ou 'Não'. (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_correcao_final':
        if user_input_lower == 'voltar':
            sessao['MEMORIA_USUARIO'] = {}
            return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

        partes = [p.strip() for p in user_input.split(',', 2)] # Divide em até 3 partes
        if len(partes) < 3 or not partes[0].lower().startswith('capinha'):
            return ("Formato inválido. Por favor, diga o número da capinha, o novo modelo/tema e o nome do arquivo da foto. "
                    "(Ex: Capinha 1, iPhone 13, nova_foto.jpg) (Ou digite 'Voltar' para o menu principal)")

        try:
            capinha_idx = int(partes[0].lower().replace('capinha', '').strip()) - 1
            novo_modelo_tema = partes[1]
            novo_nome_arquivo_foto = partes[2]

            if not (0 <= capinha_idx < len(MEMORIA_USUARIO['detalhes_personalizacao_foto'])):
                return "Número de capinha inválido. Por favor, digite um número de capinha existente. (Ou digite 'Voltar' para o menu principal)"

            if not re.search(r'\.(jpg|jpeg|png|gif)$', novo_nome_arquivo_foto, re.IGNORECASE):
                return ("Nome de arquivo de foto inválido. Por favor, certifique-se de que termina com .jpg, .jpeg, .png ou .gif. "
                        "(Ou digite 'Voltar' para o menu principal)")

            MEMORIA_USUARIO['detalhes_personalizacao_foto'][capinha_idx]['tema'] = novo_modelo_tema
            MEMORIA_USUARIO['detalhes_personalizacao_foto'][capinha_idx]['nome_arquivo_foto'] = novo_nome_arquivo_foto
            MEMORIA_USUARIO['personalizacao_foto_estado'] = 'confirmacao_final' # Volta para a confirmação
            detalhes_str = "\n".join([f"- Capinha {i+1}: Modelo/Tema: {d['tema']}, Foto: {d['nome_arquivo_foto']}" for i, d in enumerate(MEMORIA_USUARIO['detalhes_personalizacao_foto'])])
            return (f"Capinha {capinha_idx+1} atualizada para Modelo/Tema: '{novo_modelo_tema}', Foto: '{novo_nome_arquivo_foto}'.\n"
                    f"Suas personalizações são:\n{detalhes_str}\n"
                    "Está tudo correto agora? (Sim/Não) (Ou digite 'Voltar' para o menu principal)")

        except ValueError:
            return "Número de capinha inválido. Por favor, digite 'Capinha X, Modelo/Tema, Nome_Arquivo_Foto'. (Ou digite 'Voltar' para o menu principal)"

    return "Desculpe, não entendi. Por favor, digite 'Voltar' para o menu principal."

def processar_consulta_capinha(sessao_id, user_input):
    """Gerencia o fluxo de consulta de capinhas."""
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']

    user_input_lower = user_input.lower().strip()

    if user_input_lower == 'voltar':
        sessao['MEMORIA_USUARIO'] = {}
        return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

    estado = MEMORIA_USUARIO.get('consulta_capinha_estado', 'inicio')

    if estado == 'inicio':
        MEMORIA_USUARIO['consulta_capinha_estado'] = 'aguardando_modelo_tema'
        return ("Certo! Qual o modelo de celular ou tema de desenho específico que você gostaria de consultar? "
                "(Ou digite 'Voltar' para o menu principal)")

    elif estado == 'aguardando_modelo_tema':
        # Aqui, em um sistema real, você faria uma consulta ao banco de dados.
        # Por enquanto, vamos simular o encaminhamento para o humano.
        modelo_tema_consultado = user_input
        MEMORIA_USUARIO['modelo_tema_consultado'] = modelo_tema_consultado

        # Encaminha para atendimento humano
        sessao['ATENDIMENTO_HUMANO_ATIVO'] = True
        sessao['CONVERSA_ENCAMINHADA_HUMANO'] = True
        MEMORIA_USUARIO['consulta_capinha_estado'] = 'encaminhado_humano' # Marca o estado para não responder mais
        return get_resposta_regra("TRANSFERENCIA_OFERECER")

    elif estado == 'encaminhado_humano':
        # Se o usuário ainda está nesse estado, significa que o humano está ativo.
        # O bot não deve responder, a menos que o usuário cancele o atendimento humano.
        return None # O bot fica em silêncio, esperando o humano ou o cancelamento

    return "Desculpe, não entendi. Por favor, digite 'Voltar' para o menu principal."

def processar_devolucao_reembolso(sessao_id, user_input):
    """Processa a solicitação de devolução/reembolso."""
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']
    # A limpeza da memória e o retorno ao menu principal/saída serão tratados na assistente_virtual_bot
    # para permitir que 'last_flow_options' seja lido.
    return (get_resposta_regra("ERRO_LOJA_SCRIPT") + "\n" +
            "O que você gostaria de fazer agora?\n"
            "1 - Voltar ao menu principal\n"
            "2 - Sair do atendimento")

def processar_duvidas_informacoes(sessao_id, user_input):
    """Gerencia o fluxo do submenu de dúvidas e informações."""
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']

    user_input_lower = user_input.lower().strip()

    if user_input_lower == 'voltar':
        sessao['MEMORIA_USUARIO'] = {}
        return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()

    estado = MEMORIA_USUARIO.get('duvidas_estado', 'inicio')

    if estado == 'inicio':
        MEMORIA_USUARIO['duvidas_estado'] = 'aguardando_opcao_submenu'
        return exibir_submenu_duvidas() + " (Ou digite 'Voltar' para o menu principal)"

    elif estado == 'aguardando_opcao_submenu':
        if user_input_lower == '1':
            resposta = get_resposta_regra("LOGISTICA_ATRASO")
        elif user_input_lower == '2':
            resposta = get_resposta_regra("COMPRA_INCORRETA")
        elif user_input_lower == '3':
            resposta = get_resposta_regra("PAGAMENTO_COMPLETO")
        elif user_input_lower == '4':
            resposta = get_resposta_regra("APROVACAO_VER_CAPINHA")
        elif user_input_lower == '5':
            resposta = get_resposta_regra("IMAGENS_ILUSTRATIVAS")
        elif user_input_lower == '6':
            resposta = get_resposta_regra("MODELO_DESCONHECIDO")
        elif user_input_lower == '7':
            resposta = get_resposta_regra("ALTERAR_FONTE_LETRA")
        elif user_input_lower == '8':
            resposta = get_resposta_regra("CAPINHA_PROTECAO")
        elif user_input_lower == '9':
            resposta = get_resposta_regra("CAPINHA_AMARELA")
        elif user_input_lower == '10':
            resposta = get_resposta_regra("CUPOM_DESCONTO")
        elif user_input_lower == '11': # Voltar ao menu principal
            sessao['MEMORIA_USUARIO'] = {}
            return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()
        elif user_input_lower == '12': # Falar com atendimento Humano
            sessao['ATENDIMENTO_HUMANO_ATIVO'] = True
            sessao['CONVERSA_ENCAMINHADA_HUMANO'] = True
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória para o atendente humano
            return get_resposta_regra("TRANSFERENCIA_OFERECER")
        else:
            return get_resposta_regra("RESPOSTA_FORA_MENU") + "\n" + exibir_menu_principal()

        MEMORIA_USUARIO['duvidas_estado'] = 'apos_resposta_duvida'
        return (resposta + "\n\nO que você gostaria de fazer agora?\n"
                "1 - Voltar ao menu principal\n"
                "2 - Fazer outra pergunta (voltar ao submenu de dúvidas)\n"
                "3 - Sair do atendimento")

    elif estado == 'apos_resposta_duvida':
        if user_input_lower == '1': # Voltar ao menu principal
            sessao['MEMORIA_USUARIO'] = {}
            return "Entendido. Voltando ao menu principal.\n" + exibir_menu_principal()
        elif user_input_lower == '2': # Fazer outra pergunta (voltar ao submenu de dúvidas)
            MEMORIA_USUARIO['duvidas_estado'] = 'aguardando_opcao_submenu'
            return exibir_submenu_duvidas() + " (Ou digite 'Voltar' para o menu principal)"
        elif user_input_lower == '3': # Sair do atendimento
            sessao['MEMORIA_USUARIO'] = {}
            return get_resposta_regra("SAIR_ATENDIMENTO")
        else:
            return ("Desculpe, não entendi sua escolha. Por favor, selecione uma das opções numeradas:\n"
                    "1 - Voltar ao menu principal\n"
                    "2 - Fazer outra pergunta (voltar ao submenu de dúvidas)\n"
                    "3 - Sair do atendimento")

    return "Desculpe, não entendi. Por favor, digite 'Voltar' para o menu principal."

def processar_mensagem_shopee(sessao_id, user_input):
    """
    Função principal para processar mensagens da Shopee, gerenciando o estado da sessão.
    Retorna a resposta do bot e um booleano indicando se a conversa foi encaminhada para humano.
    """
    sessao = get_sessao_estado(sessao_id)
    MEMORIA_USUARIO = sessao['MEMORIA_USUARIO']
    ATENDIMENTO_HUMANO_ATIVO = sessao['ATENDIMENTO_HUMANO_ATIVO']
    ULTIMA_INTERACAO_ATENDENTE_HUMANO = sessao['ULTIMA_INTERACAO_ATENDENTE_HUMANO']
    CONVERSA_ENCAMINHADA_HUMANO = sessao['CONVERSA_ENCAMINHADA_HUMANO']
    PRIMEIRA_MENSAGEM_RECEBIDA = sessao['PRIMEIRA_MENSAGEM_RECEBIDA']

    user_input_lower = user_input.lower().strip()
    resposta_bot = None
    encaminhado_humano_final = False # Flag para retornar se a conversa foi encaminhada

    # --- Lógica de Início de Conversa ---
    if not PRIMEIRA_MENSAGEM_RECEBIDA:
        sessao['PRIMEIRA_MENSAGEM_RECEBIDA'] = True
        resposta_bot = exibir_saudacao_inicial() + "\n" + exibir_menu_principal()
        return resposta_bot, encaminhado_humano_final

    # --- Lógica de Atendimento Humano ---
    if ATENDIMENTO_HUMANO_ATIVO:
        # Se o atendente humano enviou a frase de finalização
        if user_input.strip() == FINALIZACAO_ATENDENTE_HUMANO_FRASE:
            sessao['ATENDIMENTO_HUMANO_ATIVO'] = False
            sessao['CONVERSA_ENCAMINHADA_HUMANO'] = False
            sessao['ULTIMA_INTERACAO_ATENDENTE_HUMANO'] = datetime.datetime.now() # Marca o tempo da finalização
            return None, False # A assistente não responde, apenas desativa o modo humano

        # Se o cliente quer cancelar o atendimento humano
        if user_input_lower == 'cancelar atendimento humano':
            sessao['ATENDIMENTO_HUMANO_ATIVO'] = False
            sessao['CONVERSA_ENCAMINHADA_HUMANO'] = False
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória para recomeçar com a assistente
            resposta_bot = get_resposta_regra("CANCELAR_ATENDIMENTO_HUMANO") + "\n" + exibir_menu_principal()
            return resposta_bot, False

        # Se a conversa foi encaminhada e o atendente humano ainda não finalizou,
        # a assistente fica em modo de espera total, não respondendo proativamente.
        # O bot não deve responder nada aqui, pois o atendente está no controle.
        if CONVERSA_ENCAMINHADA_HUMANO:
            # Não responde, pois o humano está no controle.
            # Se a Shopee exige uma resposta 200 OK, o server.py já faz isso.
            # O bot_logic não precisa gerar uma resposta de texto aqui.
            return None, True # Retorna True para indicar que ainda está encaminhado

    # --- Retomada da Assistente Virtual após 24h de inatividade do atendente humano ---
    # Esta lógica só se aplica se o atendimento humano foi finalizado (ULTIMA_INTERACAO_ATENDENTE_HUMANO não é None)
    # E se o atendente NÃO enviou a frase de finalização.
    if ULTIMA_INTERACAO_ATENDENTE_HUMANO and not ATENDIMENTO_HUMANO_ATIVO:
        if (datetime.datetime.now() - ULTIMA_INTERACAO_ATENDENTE_HUMANO).total_seconds() > 24 * 3600: # 24 horas
            sessao['ULTIMA_INTERACAO_ATENDENTE_HUMANO'] = None # Reseta o timer
            # A assistente está pronta para responder normalmente na próxima interação do usuário.
        else:
            # Se ainda não passou 24h desde a última interação do atendente (sem a frase de finalização),
            # e o atendimento humano não foi cancelado, a assistente ainda não retoma proativamente.
            # Ela só responderá se o usuário iniciar uma nova conversa ou opção do menu.
            pass

    # --- Detecção de Intenção para Atendimento Humano (fora de um fluxo específico) ---
    if user_input_lower == 'falar com atendimento humano' or user_input_lower == 'falar com atendente':
        sessao['ATENDIMENTO_HUMANO_ATIVO'] = True
        sessao['CONVERSA_ENCAMINHADA_HUMANO'] = True # Marca que a conversa foi encaminhada
        sessao['MEMORIA_USUARIO'] = {} # Limpa a memória para o atendente humano
        resposta_bot = get_resposta_regra("TRANSFERENCIA_OFERECER")
        encaminhado_humano_final = True
        return resposta_bot, encaminhado_humano_final

    # --- Processamento de Opções Pós-Conclusão de Fluxo (Novo) ---
    # Este bloco deve vir ANTES do processamento de fluxos ativos e do menu principal
    if MEMORIA_USUARIO.get('last_action_completed') == 'personalizacao_nome_concluida':
        if user_input_lower == '1': # Voltar ao menu principal
            sessao['MEMORIA_USUARIO'] = {} # Limpa toda a memória para um novo início
            resposta_bot = exibir_menu_principal()
        elif user_input_lower == '2': # Sair do atendimento
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória
            resposta_bot = get_resposta_regra("SAIR_ATENDIMENTO")
        else:
            # Se o usuário digitou algo diferente de 1 ou 2, reexibe as opções
            resposta_bot = ("Desculpe, não entendi sua escolha. Por favor, selecione uma das opções numeradas:\n"
                    "1 - Voltar ao menu principal\n"
                    "2 - Sair do atendimento")
        return resposta_bot, encaminhado_humano_final

    if MEMORIA_USUARIO.get('last_action_completed') == 'personalizacao_foto_concluida':
        if user_input_lower == '1': # Voltar ao menu principal
            sessao['MEMORIA_USUARIO'] = {} # Limpa toda a memória para um novo início
            resposta_bot = exibir_menu_principal()
        elif user_input_lower == '2': # Sair do atendimento
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória
            resposta_bot = get_resposta_regra("SAIR_ATENDIMENTO")
        else:
            # Se o usuário digitou algo diferente de 1 ou 2, reexibe as opções
            resposta_bot = ("Desculpe, não entendi sua escolha. Por favor, selecione uma das opções numeradas:\n"
                    "1 - Voltar ao menu principal\n"
                    "2 - Sair do atendimento")
        return resposta_bot, encaminhado_humano_final

    # --- Processamento de Fluxos Ativos ---
    # Se o estado 'last_flow_options' está definido e o input é '1' ou '2',
    # significa que o usuário está respondendo às opções de "Voltar ao menu principal" ou "Sair"
    # após um fluxo como Devolução/Reembolso.
    if MEMORIA_USUARIO.get('last_flow_options') == 'devolucao_reembolso':
        if user_input_lower == '1':
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória para garantir um novo início
            resposta_bot = exibir_menu_principal()
        elif user_input_lower == '2':
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória
            resposta_bot = get_resposta_regra("SAIR_ATENDIMENTO")
        else:
            resposta_bot = processar_devolucao_reembolso(sessao_id, user_input) # Reprocessa para exibir as opções novamente
        return resposta_bot, encaminhado_humano_final

    if 'personalizacao_nome_estado' in MEMORIA_USUARIO:
        resposta_bot = processar_personalizacao_nome(sessao_id, user_input)
    elif 'personalizacao_foto_estado' in MEMORIA_USUARIO:
        resposta_bot = processar_personalizacao_foto(sessao_id, user_input)
    elif 'consulta_capinha_estado' in MEMORIA_USUARIO:
        resposta_bot = processar_consulta_capinha(sessao_id, user_input)
        if sessao['CONVERSA_ENCAMINHADA_HUMANO']: # Verifica se a consulta encaminhou para humano
            encaminhado_humano_final = True
    elif 'duvidas_estado' in MEMORIA_USUARIO:
        resposta_bot = processar_duvidas_informacoes(sessao_id, user_input)
    else:
        # --- Processa as opções do menu principal ---
        if user_input_lower == '1':
            # Trava para reenvio de nome (Novo)
            if MEMORIA_USUARIO.get('personalizacao_nome_concluida_recentemente'):
                resposta_bot = get_resposta_regra("PEDIDO_NOME_JA_ENVIADO")
            else:
                resposta_bot = processar_personalizacao_nome(sessao_id, user_input)
        elif user_input_lower == '2':
            resposta_bot = processar_personalizacao_foto(sessao_id, user_input)
        elif user_input_lower == '3':
            resposta_bot = processar_consulta_capinha(sessao_id, user_input)
            if sessao['CONVERSA_ENCAMINHADA_HUMANO']:
                encaminhado_humano_final = True
        elif user_input_lower == '4':
            # Define o last_flow_options ANTES de chamar a função
            MEMORIA_USUARIO['last_flow_options'] = 'devolucao_reembolso'
            resposta_bot = processar_devolucao_reembolso(sessao_id, user_input)
        elif user_input_lower == '5':
            resposta_bot = processar_duvidas_informacoes(sessao_id, user_input)
        elif user_input_lower == '6' or user_input_lower == 'sair':
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória ao sair
            resposta_bot = get_resposta_regra("SAIR_ATENDIMENTO")
        elif user_input_lower == 'menu' or user_input_lower == 'menu principal':
            resposta_bot = exibir_menu_principal()
        elif user_input_lower == 'olá' or user_input_lower == 'oi' or user_input_lower == 'tudo bem':
            # Se for uma saudação e já passou da primeira mensagem, apenas exibe o menu
            resposta_bot = exibir_menu_principal()
        elif user_input_lower == 'obrigado' or user_input_lower == 'obrigada':
            resposta_bot = "De nada, Alex! Fico feliz em ajudar. Você gostaria de fazer mais alguma coisa ou tem alguma outra dúvida?"
        elif "reembolso" in user_input_lower or "devolução" in user_input_lower or "dinheiro de volta" in user_input_lower:
            # Define o last_flow_options ANTES de chamar a função
            MEMORIA_USUARIO['last_flow_options'] = 'devolucao_reembolso'
            resposta_bot = processar_devolucao_reembolso(sessao_id, user_input)
        elif "prazo de envio" in user_input_lower or "recebimento do pedido" in user_input_lower:
            resposta_bot = get_resposta_regra("LOGISTICA_ATRASO") + "\n" + exibir_menu_principal()
        elif "comprei errado" in user_input_lower or "preciso alterar" in user_input_lower:
            resposta_bot = get_resposta_regra("COMPRA_INCORRETA") + "\n" + exibir_menu_principal()
        elif "formas de pagamento" in user_input_lower or "pagamento" in user_input_lower:
            resposta_bot = get_resposta_regra("PAGAMENTO_COMPLETO") + "\n" + exibir_menu_principal()
        elif "ver minha capinha" in user_input_lower or "aprovar antes do envio" in user_input_lower:
            resposta_bot = get_resposta_regra("APROVACAO_VER_CAPINHA") + "\n" + exibir_menu_principal()
        elif "imagens do anuncio" in user_input_lower or "diferentes do meu modelo" in user_input_lower:
            resposta_bot = get_resposta_regra("IMAGENS_ILUSTRATIVAS") + "\n" + exibir_menu_principal()
        elif "não sei meu modelo de celular" in user_input_lower or "nao sei meu modelo" in user_input_lower:
            resposta_bot = get_resposta_regra("MODELO_DESCONHECIDO") + "\n" + exibir_menu_principal()
        elif "mudar o tipo de letra" in user_input_lower or "alterar fonte" in user_input_lower:
            resposta_bot = get_resposta_regra("ALTERAR_FONTE_LETRA") + "\n" + exibir_menu_principal()
        elif "capinha possui proteção" in user_input_lower or "proteção da capinha" in user_input_lower:
            resposta_bot = get_resposta_regra("CAPINHA_PROTECAO") + "\n" + exibir_menu_principal()
        elif "capinha amarela" in user_input_lower or "amarela com o tempo" in user_input_lower:
            resposta_bot = get_resposta_regra("CAPINHA_AMARELA") + "\n" + exibir_menu_principal()
        elif "cupom de desconto" in user_input_lower or "promoção" in user_input_lower:
            resposta_bot = get_resposta_regra("CUPOM_DESCONTO") + "\n" + exibir_menu_principal()
        else:
            # Se não for uma opção do menu e não houver fluxo ativo, exibe a mensagem de fora do menu
            # e o menu principal.
            sessao['MEMORIA_USUARIO'] = {} # Limpa a memória para garantir que o menu principal seja exibido
            resposta_bot = get_resposta_regra("RESPOSTA_FORA_MENU") + "\n" + exibir_menu_principal()

    # Atualiza o estado da sessão com as flags de atendimento humano
    sessao['ATENDIMENTO_HUMANO_ATIVO'] = ATENDIMENTO_HUMANO_ATIVO
    sessao['ULTIMA_INTERACAO_ATENDENTE_HUMANO'] = ULTIMA_INTERACAO_ATENDENTE_HUMANO
    sessao['CONVERSA_ENCAMINHADA_HUMANO'] = CONVERSA_ENCAMINHADA_HUMANO

    return resposta_bot, encaminhado_humano_final

# --- Simulação de Interação (para testes) ---
if __name__ == "__main__":
    # A assistente não imprime nada no início, espera a primeira mensagem do usuário
    print("Inicie a conversa...")
    test_sessao_id = "test_user_123" # Usar um ID de sessão fixo para testes locais
    while True:
        user_input = input("Você: ")
        if user_input.lower() == 'sair':
            response, _ = processar_mensagem_shopee(test_sessao_id, user_input)
            if response:
                print(f"Assistente Virtual: {response}")
            break
        response, _ = processar_mensagem_shopee(test_sessao_id, user_input)
        if response is not None: # A assistente só responde se não estiver em modo de espera total
            print(f"Assistente Virtual: {response}")
            if "Tenha um ótimo dia!" in response:
                break
