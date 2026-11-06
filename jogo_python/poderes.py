# PODERES DO MODO NAVE
# Poderes mudam o TIRO: quicar, dividir, seguir, multiplicar e repetir. Sozinhos eles não fazem nada:
# o visitante chama o poder no script, e cada poder também LIBERA uma parte do Python (if, else, for, %...)
# para ele decidir QUANDO o poder acontece. Exemplo:
#     if tiro.acertou:
#         tiro.quicar()
#     if tiro.numero % 3 == 0:
#         tiro.dividir()
#
# Uma REGRA é cada bloco do script que não é "objeto.atributo = valor".
# Cada tiro passa por EVENTOS, e o script pergunta qual está acontecendo:
#   tiro.saiu       -> o tiro acabou de sair da arma
#   tiro.acertou    -> o tiro encostou num inimigo (e inimigo.vida é a vida dele)
#   tiro.na_parede  -> o tiro bateu na borda da tela
# Regra que fala de algum evento roda em TODOS os eventos (a condição escolhe); as outras rodam só quando o tiro sai.
# Exemplo: "if tiro.acertou or tiro.na_parede: tiro.quicar()" quica no inimigo e na parede.
#
# SEGURANÇA: o script NUNCA é executado pelo Python. O script_das_armas.py confere a árvore (ast) e aqui nós
# "andamos" por ela: só sabemos fazer if, for com range e chamar os quatro poderes.

import ast  # Lê código sem executar
import operator  # As contas e comparações (+, %, <, ==...) como funções
from collections import Counter  # Um dicionário que conta (quantas vezes cada poder foi pedido)

import pygame  # Biblioteca de jogos que estamos usando

MAXIMO_DE_QUIQUES = 3  # Cada tiro quica no máximo isso (senão ficaria quicando entre dois inimigos para sempre)
MAXIMO_DE_GERACOES = 2  # Cópia de cópia de cópia não se divide mais
MAXIMO_DE_TIROS = 150  # Nenhum poder cria tiro novo se já tiver isso na tela
MAXIMO_DE_PEDIDOS = 12  # Poderes chamados por tiro, por momento (trava laços dentro de laços)
MAXIMO_DE_REPETICOES = 3  # O maior número do range(...)
ANGULO_DA_DIVISAO = 15  # Graus entre os pedaços do tiro dividido
ESPACO_DAS_COPIAS = 6  # Pixels entre o tiro e as cópias do multiplicar
COR_DO_ICONE = (255, 210, 60)

COMPARACOES = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}
CONTAS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Mod: operator.mod}
EVENTOS = ("tiro.saiu", "tiro.acertou", "tiro.na_parede")
VARIAVEIS = EVENTOS + ("tiro.numero", "tiro.quiques", "passaro.vida", "inimigo.vida")  # O que dá para usar nas condições


class Poder:

    # CONSTRUTOR
    #   nome         -> como se chama no script (tiro.<nome>())
    #   titulo       -> o que aparece na carta
    #   descricao    -> linhas da carta
    #   libera       -> partes do Python que este poder desbloqueia
    #   explicacao   -> o que o professor fala antes do exemplo
    #   exemplo      -> as linhas que o visitante digita no tutorial
    #   resultado    -> o que o professor fala no fim
    #   desenho      -> pontos da linha do ícone (num quadradinho de 16 x 10)
    def __init__(self, nome, titulo, descricao, libera, explicacao, exemplo, resultado, desenho):
        self.nome = nome
        self.titulo = titulo
        self.descricao = descricao
        self.libera = libera
        self.explicacao = explicacao
        self.exemplo = exemplo
        self.resultado = resultado
        self.desenho = desenho

    def rodape_da_carta(self):
        return "Libera: " + ", ".join(self.libera)

    def icone(self):
        imagem = pygame.Surface((16, 10), pygame.SRCALPHA)
        for linha in self.desenho:
            pygame.draw.lines(imagem, COR_DO_ICONE, False, linha)
        return imagem


PODERES = {poder.nome: poder for poder in (
    Poder("quicar", "QUICAR", ["Quica no inimigo (vai para outro)", "ou na parede.", f"No máximo {MAXIMO_DE_QUIQUES} quiques por tiro.", "Sozinho não faz nada: use com o if!"],
          ("if", "tiro.acertou", "tiro.na_parede", "tiro.quiques"),
          ["Novo poder: tiro.quicar()", "Sozinho ele não faz nada: VOCÊ decide quando.", "Ele liberou o IF (se): o que fica DENTRO dele",
           "só roda quando a condição é verdadeira.", "tiro.acertou é True quando o tiro acerta alguém."],
          ["if tiro.acertou:", "    tiro.quicar()"],
          ["Agora, quando o tiro acerta, ele quica!", "Teste também: if tiro.na_parede:", "tiro.quiques conta quantas vezes ele já quicou."],
          [[(0, 1), (8, 9), (15, 1)]]),
    Poder("dividir", "DIVIDIR", ["O tiro se divide em 3, num leque.", "Os pedaços têm metade do dano.", "Use com o if e o % !"],
          ("if", "tiro.numero", "%"),
          ["Novo poder: tiro.dividir()", "IF = SE: o de dentro só roda quando é verdade.", "tiro.numero conta os tiros: 1, 2, 3, 4...",
           "O % é o RESTO da divisão: 7 % 3 = 1, 6 % 3 = 0.", "tiro.numero % 3 == 0 é verdade a cada 3 tiros."],
          ["if tiro.numero % 3 == 0:", "    tiro.dividir()"],
          ["Agora, a cada 3 tiros, um se divide!", "Com if tiro.acertou ele se divide no inimigo."],
          [[(0, 5), (7, 5), (15, 0)], [(7, 5), (15, 5)], [(7, 5), (15, 9)]]),
    Poder("seguir", "SEGUIR", ["O tiro faz curva atrás", "do inimigo mais perto.", "Use com o if e o else!"],
          ("if", "else", "passaro.vida", "inimigo.vida"),
          ["Novo poder: tiro.seguir()", "IF = SE. Liberou também o ELSE = SENÃO:", "o que fica dentro do else roda quando o if é falso.",
           "passaro.vida é quantos corações você tem.", "inimigo.vida é a vida de quem o tiro acertou."],
          ["if passaro.vida < 3:", "    tiro.seguir()"],
          ["Agora, com pouca vida, os tiros te ajudam!", "Teste um else: embaixo do if."],
          [[(0, 9), (5, 2), (10, 1), (15, 5)]]),
    Poder("multiplicar", "MULTIPLICAR", ["Cria uma cópia do tiro ao lado.", "As cópias têm metade do dano.", "Use com o for!"],
          ("for",),
          ["Novo poder: tiro.multiplicar()", "Ele liberou o FOR (laço): repete o que", "está dentro. range(2) = 2 vezes."],
          ["for i in range(2):", "    tiro.multiplicar()"],
          ["Cada tiro agora sai com 2 cópias!", f"O range vai até {MAXIMO_DE_REPETICOES}."],
          [[(0, 1), (15, 1)], [(0, 5), (15, 5)], [(0, 9), (15, 9)]]),
    Poder("repetir", "REPETIR", ["Atira de novo, saindo do pássaro.", "A cópia tem metade do dano.", "Na parede? Ao acertar? Você decide!"],
          ("if", "tiro.saiu", "tiro.na_parede"),
          ["Novo poder: tiro.repetir()", "Ele faz o pássaro atirar de novo.", "Liberou tiro.saiu (o tiro acabou de sair)",
           "e tiro.na_parede (o tiro bateu na borda da tela)."],
          ["if tiro.na_parede:", "    tiro.repetir()"],
          ["Agora, todo tiro que bate na borda", "faz o pássaro atirar de novo!"],
          [[(0, 5), (5, 5)], [(8, 5), (13, 5)], [(10, 2), (14, 5), (10, 8)]]),
)}


# A regra fala de algum evento ("sempre": roda em todos, a condição escolhe) ou não ("disparo": só quando o tiro sai)?
def momento_da_regra(comando):
    for no in ast.walk(comando):  # "ast.walk" passa por todos os pedaços da árvore
        if isinstance(no, ast.Attribute) and isinstance(no.value, ast.Name) and f"{no.value.id}.{no.attr}" in EVENTOS:
            return "sempre"
    return "disparo"


# Roda as regras de um momento ("disparo", "acerto" ou "parede") e devolve quantas vezes cada poder foi pedido (ex.: {"quicar": 1}).
def executar_regras(regras, momento, variaveis):
    variaveis = dict(variaveis, **{"tiro.saiu": momento == "disparo", "tiro.acertou": momento == "acerto", "tiro.na_parede": momento == "parede"})
    pedidos = Counter()
    for quando, comando in regras:
        if quando in ("sempre", momento):
            executar(comando, dict(variaveis), pedidos)
    return pedidos


def executar(comando, variaveis, pedidos):
    if sum(pedidos.values()) >= MAXIMO_DE_PEDIDOS:
        return
    if isinstance(comando, ast.If):
        for dentro in (comando.body if avaliar(comando.test, variaveis) else comando.orelse):
            executar(dentro, variaveis, pedidos)
    elif isinstance(comando, ast.For):  # Já conferido: "for nome in range(número)"
        for valor in range(comando.iter.args[0].value):
            variaveis[comando.target.id] = valor
            for dentro in comando.body:
                executar(dentro, variaveis, pedidos)
    elif isinstance(comando, ast.Expr):  # Já conferido: "tiro.poder()"
        pedidos[comando.value.func.attr] += 1


# Calcula uma condição já conferida (só números, variáveis liberadas, contas e comparações).
def avaliar(no, variaveis):
    if isinstance(no, ast.Constant):
        return no.value
    if isinstance(no, ast.Attribute):
        return variaveis[f"{no.value.id}.{no.attr}"]
    if isinstance(no, ast.Name):  # A variável do for
        return variaveis[no.id]
    if isinstance(no, ast.Compare):  # Também vale "1 < x < 5"
        esquerda = avaliar(no.left, variaveis)
        for operacao, lado in zip(no.ops, no.comparators):
            direita = avaliar(lado, variaveis)
            if not COMPARACOES[type(operacao)](esquerda, direita):
                return False
            esquerda = direita
        return True
    if isinstance(no, ast.BoolOp):
        valores = (avaliar(valor, variaveis) for valor in no.values)
        return all(valores) if isinstance(no.op, ast.And) else any(valores)
    if isinstance(no, ast.UnaryOp):
        valor = avaliar(no.operand, variaveis)
        return not valor if isinstance(no.op, ast.Not) else -valor
    esquerda, direita = avaliar(no.left, variaveis), avaliar(no.right, variaveis)
    if isinstance(no.op, ast.Mod) and direita == 0:  # "x % 0" daria erro: vale 0
        return 0
    return CONTAS[type(no.op)](esquerda, direita)


# Faz os poderes pedidos acontecerem no tiro (um Projetil ou um RaioLaser: os dois sabem "copiar" e "repetir").
# "origem" é o pássaro (de onde sai o repetir); "ignorar" é o inimigo que acabou de ser acertado (as cópias passam por ele).
def aplicar_poderes(tiro, pedidos, projeteis, origem, ignorar=None):
    tiro.quiques_restantes = min(MAXIMO_DE_QUIQUES - tiro.quiques, tiro.quiques_restantes + pedidos["quicar"])
    if pedidos["seguir"]:
        tiro.seguindo = True
    if tiro.geracao >= MAXIMO_DE_GERACOES:
        return
    copias = []
    for numero in range(1, pedidos["dividir"] + 1):  # Cada dividir abre o leque mais um pouco
        copias += [tiro.copiar(angulo=lado * ANGULO_DA_DIVISAO * numero) for lado in (-1, 1)]
    for numero in range(1, pedidos["multiplicar"] + 1):  # Cópias lado a lado: uma em cima, uma embaixo, mais longe...
        copias.append(tiro.copiar(deslocamento=(numero + 1) // 2 * ESPACO_DAS_COPIAS * (-1) ** numero))
    copias += [tiro.repetir(origem, numero) for numero in range(1, pedidos["repetir"] + 1)]
    for copia in copias:
        if len(projeteis) >= MAXIMO_DE_TIROS:
            break
        copia.ignorar = ignorar or copia.ignorar
        projeteis.add(copia)
