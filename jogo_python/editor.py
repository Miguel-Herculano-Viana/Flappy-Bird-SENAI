# CLASSE EDITOR DE CÓDIGO
# A caixa onde o visitante digita uma linha de Python para mudar o jogo, por exemplo: canos.abertura = 80
#
# SEGURANÇA: o texto digitado NUNCA é executado (nada de eval ou exec), porque o computador fica aberto ao público.
# Em vez disso, o módulo "ast" do Python lê a linha e monta uma "árvore" dizendo o que cada pedaço é
# (um nome, um ponto, um sinal de igual, um número...). Nós olhamos essa árvore e só aceitamos o formato
# "objeto.atributo = número". Qualquer outra coisa vira uma mensagem de erro, como o Python de verdade faria.

import ast  # Ferramenta do Python que lê código sem executar

import pygame  # Biblioteca de jogos que estamos usando

MAXIMO_DE_CARACTERES = 60  # Tamanho máximo da linha, para ninguém colar um texto gigante
SEGUNDOS_PERDIDOS_POR_ERRO = 2.0  # Cada tentativa errada desconta este tempo do relógio do editor
COR_DA_LACUNA = (55, 60, 85)  # Fundo da parte que o visitante deve digitar
COR_DO_CURSOR = (255, 255, 255)  # Branco
COR_DO_ERRO = (255, 110, 110)  # Vermelho
COR_DO_ACERTO = (120, 230, 120)  # Verde
COR_DA_DICA = (110, 160, 110)  # Verde apagado, como os comentários (#) nos editores
COR_DA_BARRA_DE_TEMPO = (255, 200, 60)  # Amarelo
COR_DO_FUNDO_DA_BARRA = (55, 60, 85)  # Cinza azulado

# Operações de conta que aceitamos no valor (ex.: canos.abertura = 40 * 2). Só com números, nada de nomes ou funções.
OPERACOES_PERMITIDAS = {
    ast.Add: lambda a, b: a + b,  # +
    ast.Sub: lambda a, b: a - b,  # -
    ast.Mult: lambda a, b: a * b,  # *
    ast.Div: lambda a, b: a / b,  # /
    ast.FloorDiv: lambda a, b: a // b,  # //
}


# Confere uma linha de código SEM executar. Devolve (valor, None) se estiver certa, ou (None, mensagem_de_erro).
def conferir_linha(linha, objeto, atributo, minimo, maximo):
    try:
        arvore = ast.parse(linha)  # Lê a linha e monta a árvore (se a escrita estiver errada, dá SyntaxError)
    except (SyntaxError, ValueError) as erro:  # ValueError: alguns textos estranhos (ex.: caracteres invisíveis) dão este erro em vez de SyntaxError
        return None, f"SyntaxError: {getattr(erro, 'msg', erro)}\n# O Python não entendeu a linha. Confira o ponto, o = e o número."

    if len(arvore.body) != 1 or not isinstance(arvore.body[0], ast.Assign) or len(arvore.body[0].targets) != 1:  # Tem que ser UMA atribuição (algo = valor)
        return None, f"SyntaxError: escreva uma atribuição\n# Formato: {objeto}.{atributo} = número"
    alvo = arvore.body[0].targets[0]  # O que está à esquerda do =
    if not isinstance(alvo, ast.Attribute) or not isinstance(alvo.value, ast.Name):  # Tem que ser "nome.nome"
        return None, f"SyntaxError: do lado esquerdo do = vai {objeto}.{atributo}"
    if alvo.value.id != objeto:  # O objeto está escrito certo?
        return None, f"NameError: name '{alvo.value.id}' is not defined\n# O objeto se chama '{objeto}'."
    if alvo.attr != atributo:  # O atributo está escrito certo?
        return None, f"AttributeError: '{objeto}' não tem o atributo '{alvo.attr}'\n# O atributo se chama '{atributo}'."

    try:
        valor = calcular(arvore.body[0].value)  # Calcula o que está à direita do = (só números e contas simples)
    except (TypeError, NameError) as erro:
        return None, f"{type(erro).__name__}: {erro}"  # Mostra o nome do erro (TypeError ou NameError), como o Python faz
    except ZeroDivisionError:
        return None, "ZeroDivisionError: division by zero\n# Não dá para dividir por zero!"

    if not minimo <= valor <= maximo:  # O valor está dentro da faixa permitida?
        return None, f"ValueError: {atributo} deve ficar entre {minimo} e {maximo}"
    return valor, None  # Tudo certo!


# RECURSÃO: para calcular "40 * 2 + 1", a função calcula cada pedaço chamando a si mesma.
def calcular(no):
    if isinstance(no, ast.Constant) and type(no.value) in (int, float):  # Um número sozinho (True/False não contam)
        return no.value
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.USub):  # Um número negativo, como -5
        return -calcular(no.operand)
    if isinstance(no, ast.BinOp) and type(no.op) in OPERACOES_PERMITIDAS:  # Uma conta, como 40 * 2
        return OPERACOES_PERMITIDAS[type(no.op)](calcular(no.left), calcular(no.right))
    if isinstance(no, ast.Name):  # Um nome solto, como "abc": o Python procuraria uma variável com esse nome
        raise NameError(f"name '{no.id}' is not defined\n# Para o valor, escreva só o número (ex.: 80).")
    if isinstance(no, ast.Constant) and isinstance(no.value, str):  # Um texto entre aspas
        raise TypeError("o valor precisa ser um número, não um texto\n# Tire as aspas.")
    raise TypeError("use só números (e contas como + - * /)")


class EditorDeCodigo:

    # CONSTRUTOR
    #   objeto, atributo   -> o que o visitante deve mudar (ex.: "canos", "abertura")
    #   minimo, maximo     -> faixa de valores permitida
    #   codigo_pronto      -> o começo da linha que já vem escrito (ex.: "canos.abertura = ")
    #   comentarios        -> linhas de explicação mostradas acima do código
    #   segundos           -> tempo que o visitante tem para acertar
    def __init__(self, objeto, atributo, minimo, maximo, codigo_pronto, comentarios, segundos):
        # ATRIBUTOS
        self.objeto = objeto
        self.atributo = atributo
        self.minimo = minimo
        self.maximo = maximo
        self.codigo_pronto = codigo_pronto  # Parte que o visitante não precisa digitar
        self.comentarios = comentarios  # Explicações (cada item é uma linha)
        self.texto_digitado = ""  # O que o visitante já digitou
        self.posicao_do_cursor = 0  # Em que letra do texto digitado o cursor está
        self.segundos_restantes = segundos  # Relógio do editor
        self.segundos_totais = segundos  # Guardado para desenhar a barra de tempo
        self.mensagem_de_erro = None  # Último erro (ou None se não tem)
        self.valor_aceito = None  # Vira o número digitado quando o visitante acerta
        self.valor_da_previa = None  # Valor da linha que está sendo digitada, se ela já estiver certa (para mostrar uma prévia)
        self.tempo_do_cursor = 0.0  # Conta o tempo para o cursor piscar

    # MÉTODOS

    # A linha inteira, juntando a parte pronta com a parte digitada.
    def linha_completa(self):
        return self.codigo_pronto + self.texto_digitado

    # Recebe as teclas. TEXTINPUT traz as letras já prontas (com acento e no teclado brasileiro);
    # KEYDOWN traz as teclas especiais, como apagar e as setas.
    def tratar_evento(self, evento):
        if evento.type == pygame.TEXTINPUT:  # Digitou uma letra, número ou sinal
            espaco_livre = MAXIMO_DE_CARACTERES - len(self.linha_completa())  # Quantas letras ainda cabem
            novo_texto = evento.text[:max(0, espaco_livre)]  # Corta o que não couber
            self.texto_digitado = self.texto_digitado[:self.posicao_do_cursor] + novo_texto + self.texto_digitado[self.posicao_do_cursor:]  # Insere onde está o cursor
            self.posicao_do_cursor += len(novo_texto)  # O cursor anda junto
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_BACKSPACE and self.posicao_do_cursor > 0:  # Apaga a letra antes do cursor
                self.texto_digitado = self.texto_digitado[:self.posicao_do_cursor - 1] + self.texto_digitado[self.posicao_do_cursor:]
                self.posicao_do_cursor -= 1
            elif evento.key == pygame.K_DELETE:  # Apaga a letra depois do cursor
                self.texto_digitado = self.texto_digitado[:self.posicao_do_cursor] + self.texto_digitado[self.posicao_do_cursor + 1:]
            elif evento.key == pygame.K_LEFT:  # Cursor para a esquerda
                self.posicao_do_cursor = max(0, self.posicao_do_cursor - 1)
            elif evento.key == pygame.K_RIGHT:  # Cursor para a direita
                self.posicao_do_cursor = min(len(self.texto_digitado), self.posicao_do_cursor + 1)
            elif evento.key == pygame.K_HOME:  # Cursor para o começo
                self.posicao_do_cursor = 0
            elif evento.key == pygame.K_END:  # Cursor para o fim
                self.posicao_do_cursor = len(self.texto_digitado)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):  # ENTER roda a linha
                self.rodar()
                return
            else:
                return  # Outra tecla: nada mudou
        else:
            return  # Não é teclado: nada mudou
        self.tempo_do_cursor = 0.0  # Mexeu no texto: o cursor aparece na hora (não some no meio de uma piscada)
        self.valor_da_previa, _ = conferir_linha(self.linha_completa(), self.objeto, self.atributo, self.minimo, self.maximo)  # Prévia ao vivo

    # O visitante apertou ENTER: confere a linha.
    def rodar(self):
        valor, erro = conferir_linha(self.linha_completa(), self.objeto, self.atributo, self.minimo, self.maximo)
        if erro:  # Errou: mostra o erro e perde um pouco de tempo
            self.mensagem_de_erro = erro
            self.segundos_restantes -= SEGUNDOS_PERDIDOS_POR_ERRO
        else:  # Acertou!
            self.mensagem_de_erro = None
            self.valor_aceito = valor

    # Chamado a cada quadro com o tempo REAL (a câmera lenta não deixa o relógio do editor mais lento).
    def atualizar(self, tempo_real):
        self.tempo_do_cursor += tempo_real
        if self.valor_aceito is None:  # Depois de acertar, o relógio para
            self.segundos_restantes -= tempo_real

    def acabou_o_tempo(self):
        return self.segundos_restantes <= 0 and self.valor_aceito is None

    # Desenha o editor dentro do painel, começando na altura "topo". Usa a fonte e o tamanho de linha do painel.
    def desenhar(self, monitor, painel, topo):
        altura = painel.altura_da_linha
        largura_da_letra = painel.fonte.size("a")[0]  # Fonte monoespaçada: todas as letras têm esta largura
        esquerda = painel.retangulo.x + painel.margem
        y = topo

        for comentario in self.comentarios:  # Explicações do desafio
            painel.escrever(monitor, "# " + comentario, COR_DA_DICA, y)
            y += altura
        y += altura // 2

        # Linha de código: ">>> " + parte pronta + parte digitada (com fundo destacado) + cursor
        x_da_lacuna = esquerda + len(">>> " + self.codigo_pronto) * largura_da_letra
        largura_da_lacuna = max(len(self.texto_digitado) + 1, 4) * largura_da_letra  # Sempre um pouco mais larga que o texto
        pygame.draw.rect(monitor, COR_DA_LACUNA, (x_da_lacuna - 2, y - 2, largura_da_lacuna + 4, altura), border_radius=4)
        painel.escrever_colorido(monitor, ">>> ", esquerda, y, so_prompt=True)  # O ">>>" do Python, em cinza
        painel.escrever_colorido(monitor, self.linha_completa(), esquerda + 4 * largura_da_letra, y)  # O código, colorido
        if self.valor_aceito is None and self.tempo_do_cursor % 1.0 < 0.5:  # Cursor pisca: meio segundo aceso, meio apagado
            x_do_cursor = x_da_lacuna + self.posicao_do_cursor * largura_da_letra
            pygame.draw.rect(monitor, COR_DO_CURSOR, (x_do_cursor, y, 2, altura * 4 // 5))
        y += altura * 3 // 2

        if self.valor_aceito is not None:  # Acertou
            painel.escrever(monitor, f"OK! {self.objeto}.{self.atributo} agora vale {self.valor_aceito}", COR_DO_ACERTO, y)
        elif self.mensagem_de_erro:  # Errou: mostra o erro (pode ter mais de uma linha)
            for linha_do_erro in self.mensagem_de_erro.split("\n"):
                painel.escrever(monitor, linha_do_erro, COR_DA_DICA if linha_do_erro.startswith("#") else COR_DO_ERRO, y)
                y += altura
        else:
            painel.escrever(monitor, f"# valores permitidos: de {self.minimo} a {self.maximo}. Aperte ENTER para rodar.", COR_DA_DICA, y)
        y = max(y + altura, topo + altura * (len(self.comentarios) + 6))

        # Barra de tempo: encolhe conforme o tempo passa
        largura_total = painel.retangulo.width - 2 * painel.margem
        fracao = max(0.0, self.segundos_restantes / self.segundos_totais)
        pygame.draw.rect(monitor, COR_DO_FUNDO_DA_BARRA, (esquerda, y, largura_total, altura // 3), border_radius=4)
        pygame.draw.rect(monitor, COR_DA_BARRA_DE_TEMPO, (esquerda, y, round(largura_total * fracao), altura // 3), border_radius=4)


# SELF-CHECK: rode "python editor.py" para conferir se a validação aceita e recusa as linhas certas.
if __name__ == "__main__":
    def conferir(linha):
        return conferir_linha(linha, "canos", "abertura", 56, 96)

    assert conferir("canos.abertura = 80") == (80, None)  # Linha certa
    assert conferir("canos.abertura=80")[0] == 80  # Sem espaços também vale
    assert conferir("canos.abertura = 40 * 2")[0] == 80  # Conta simples
    assert conferir("canos.abertura = 80.5")[0] == 80.5  # Número com vírgula (ponto, em Python)
    assert conferir("canos.abertura = ")[1].startswith("SyntaxError")  # Faltou o número
    assert conferir("canos.abertura == 80")[1].startswith("SyntaxError")  # Comparação no lugar de atribuição
    assert conferir("canos.abretura = 80")[1].startswith("AttributeError")  # Atributo escrito errado
    assert conferir("cano.abertura = 80")[1].startswith("NameError")  # Objeto escrito errado
    assert conferir("canos.abertura = 200")[1].startswith("ValueError")  # Fora da faixa (acima)
    assert conferir("canos.abertura = -80")[1].startswith("ValueError")  # Fora da faixa (negativo)
    assert conferir("canos.abertura = '80'")[1].startswith("TypeError")  # Texto no lugar de número
    assert conferir("canos.abertura = True")[1].startswith("TypeError")  # True não é um número aqui
    assert conferir("canos.abertura = abc")[1].startswith("NameError")  # Nome solto no lugar do número
    assert conferir("canos.abertura = 80 / 0")[1].startswith("ZeroDivisionError")  # Divisão por zero
    assert conferir("canos.abertura = 9 ** 9 ** 9")[1].startswith("TypeError")  # Potência não é permitida (evita contas gigantes)
    assert conferir("canos.abertura = __import__('os').system('dir')")[1].startswith("TypeError")  # Tentativa de rodar comando: recusada
    assert conferir("import os")[1].startswith("SyntaxError")  # Qualquer coisa que não seja atribuição: recusada
    assert conferir("canos.abertura = 80; import os")[1].startswith("SyntaxError")  # Duas linhas em uma: recusada

    # Digitação: letras entram no cursor, apagar e setas funcionam, ENTER confere.
    editor = EditorDeCodigo("canos", "abertura", 56, 96, "canos.abertura = ", [], 10)
    editor.tratar_evento(pygame.event.Event(pygame.TEXTINPUT, text="8"))
    editor.tratar_evento(pygame.event.Event(pygame.TEXTINPUT, text="5"))
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
    editor.tratar_evento(pygame.event.Event(pygame.TEXTINPUT, text="0"))
    assert editor.linha_completa() == "canos.abertura = 80" and editor.valor_da_previa == 80
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_HOME))
    editor.tratar_evento(pygame.event.Event(pygame.TEXTINPUT, text="1"))  # Vira "180": fora da faixa
    assert editor.valor_da_previa is None
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert editor.valor_aceito is None and editor.mensagem_de_erro.startswith("ValueError") and editor.segundos_restantes == 8  # Errou: perdeu 2 s
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))  # Volta o cursor para antes do "1"...
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DELETE))  # ...e apaga ele
    editor.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert editor.valor_aceito == 80 and editor.mensagem_de_erro is None
    editor.atualizar(100)  # Depois de acertar, o tempo não acaba
    assert not editor.acabou_o_tempo()
    print("editor.py: tudo certo!")
