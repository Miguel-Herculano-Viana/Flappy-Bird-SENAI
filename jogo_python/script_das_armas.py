# VALIDAÇÃO DO SCRIPT DAS ARMAS (Modo Nave)
# O visitante escreve um script de várias linhas que equipa e ajusta as armas, por exemplo:
#     passaro.armas = [blaster, laser]
#     laser.quantidade = 2
#     laser.grossura = 3
#
# SEGURANÇA: assim como no editor.py, o script NUNCA é executado (nada de eval ou exec).
# O módulo "ast" lê o texto e monta uma árvore; nós conferimos cada linha e só aceitamos:
#   passaro.armas = [arma, arma]     (no máximo 2 armas, só as desbloqueadas)
#   arma.parametro = número          (dentro da faixa do parâmetro)
#   comentários (#)
#   e, depois de ganhar PODERES: if / else / for com range, e tiro.poder() (veja poderes.py)
# No fim conferimos o LIMITE COMPARTILHADO de cada arma: parametro1 x parametro2 <= limite.
# Os erros saem como no Python: "linha 3: ValueError: ...".

import ast  # Ferramenta do Python que lê código sem executar

from editor import calcular  # Calcula o valor de um número (ou de uma conta simples) sem executar nada
from poderes import COMPARACOES, CONTAS, MAXIMO_DE_REPETICOES, PODERES, VARIAVEIS, momento_da_regra  # Os poderes e o que eles liberam

MAXIMO_DE_ARMAS_EQUIPADAS = 2
MAXIMO_DE_BLOCOS = 3  # if dentro de for dentro de if... no máximo 3 níveis
MAXIMO_DE_CARACTERES_DO_SCRIPT = 2000  # Para ninguém colar um texto gigante
NOMES_DE_TODAS_AS_ARMAS = ("blaster", "laser", "missil", "espalhado")  # Para avisar "ainda não desbloqueada" em vez de "não existe"


class ErroNoScript(Exception):
    # Um erro com o número da linha, para o editor destacar a linha certa.
    def __init__(self, linha, mensagem):
        super().__init__(mensagem)
        self.linha = linha
        self.mensagem = mensagem


# Confere o script todo. Devolve (configuracao, None) se estiver certo, ou (None, (linha, mensagem)) se tiver erro.
# "armas" é o dicionário nome -> Arma das armas DESBLOQUEADAS; "equipadas" é a lista atual (usada se o script não mudar).
# "liberados" é o conjunto do que os poderes já desbloquearam (ex.: {"quicar", "if", "tiro.acertou"}).
# A configuração é {"armas": [nomes], "valores": {nome_da_arma: {parametro: valor}}, "regras": [(momento, bloco)]}.
def conferir_script(texto, armas, equipadas, liberados=frozenset()):
    try:
        return ler_script(texto, armas, equipadas, liberados), None
    except ErroNoScript as erro:
        return None, (erro.linha, erro.mensagem)


def ler_script(texto, armas, equipadas, liberados=frozenset()):
    if len(texto) > MAXIMO_DE_CARACTERES_DO_SCRIPT:
        raise ErroNoScript(1, "SyntaxError: o script está grande demais")
    try:
        arvore = ast.parse(texto)
    except (SyntaxError, ValueError) as erro:
        raise ErroNoScript(getattr(erro, "lineno", 1) or 1, f"SyntaxError: {getattr(erro, 'msg', erro)}\n# O Python não entendeu esta linha. Confira o ponto, o = e os colchetes [ ].")

    configuracao = {"armas": list(equipadas), "valores": {nome: dict(arma.valores) for nome, arma in armas.items()}, "regras": []}
    linha_de_cada_arma = {}  # Em que linha cada arma foi mexida por último (para apontar o erro do limite)
    for comando in arvore.body:  # Cada linha de código (os comentários não aparecem na árvore)
        linha = comando.lineno
        if isinstance(comando, (ast.If, ast.For, ast.Expr)):  # Uma REGRA dos poderes
            conferir_bloco(comando, liberados, set(), 1)
            configuracao["regras"].append((momento_da_regra(comando), comando))
            continue
        if not isinstance(comando, ast.Assign) or len(comando.targets) != 1:
            raise ErroNoScript(linha, "SyntaxError: só valem linhas do tipo objeto.atributo = valor")
        alvo = comando.targets[0]
        if not isinstance(alvo, ast.Attribute) or not isinstance(alvo.value, ast.Name):
            raise ErroNoScript(linha, "SyntaxError: do lado esquerdo do = vai objeto.atributo (ex.: laser.grossura)")
        objeto, atributo = alvo.value.id, alvo.attr

        if objeto == "passaro":  # passaro.armas = [...]
            if atributo != "armas":
                raise ErroNoScript(linha, f"AttributeError: o script não pode mudar 'passaro.{atributo}'\n# Do pássaro, o script só muda passaro.armas")
            configuracao["armas"] = ler_lista_de_armas(comando.value, armas, linha)
            continue

        arma = conferir_nome_da_arma(objeto, armas, linha)
        if atributo not in arma.parametros:
            nomes = " e ".join(arma.parametros)
            raise ErroNoScript(linha, f"AttributeError: '{objeto}' não tem o atributo '{atributo}'\n# Os atributos do {objeto} são {nomes}")
        valor = ler_numero(comando.value, linha)
        if valor != int(valor):
            raise ErroNoScript(linha, f"TypeError: {objeto}.{atributo} precisa ser um número inteiro (sem ponto)")
        minimo, maximo = arma.parametros[atributo]
        if not minimo <= valor <= maximo:
            raise ErroNoScript(linha, f"ValueError: {objeto}.{atributo} deve ficar entre {minimo} e {maximo}")
        configuracao["valores"][objeto][atributo] = int(valor)
        linha_de_cada_arma[objeto] = linha

    # LIMITE COMPARTILHADO: confere depois de ler tudo, com os valores finais
    for nome, arma in armas.items():
        valores = configuracao["valores"][nome]
        primeiro, segundo = arma.nomes_dos_parametros()
        produto = valores[primeiro] * valores[segundo]
        if produto > arma.limite:
            raise ErroNoScript(linha_de_cada_arma.get(nome, 1),
                               f"ValueError: {nome}.{primeiro} x {nome}.{segundo} = {valores[primeiro]} x {valores[segundo]} = {produto}, "
                               f"mas o limite do {nome} é {arma.limite}\n# Diminua um dos dois números.")
    return configuracao


# Lê "[blaster, laser]": uma LISTA com nomes de armas desbloqueadas, sem repetir, no máximo 2.
def ler_lista_de_armas(no, armas, linha):
    if not isinstance(no, ast.List):
        raise ErroNoScript(linha, "TypeError: passaro.armas precisa ser uma lista, ex.: [blaster, laser]")
    nomes = []
    for item in no.elts:  # "elts" são os elementos da lista
        if not isinstance(item, ast.Name):
            raise ErroNoScript(linha, "TypeError: a lista só pode ter nomes de armas, sem aspas (ex.: [blaster, laser])")
        conferir_nome_da_arma(item.id, armas, linha)
        if item.id in nomes:
            raise ErroNoScript(linha, f"ValueError: a arma '{item.id}' está duas vezes na lista")
        nomes.append(item.id)
    if not nomes:
        raise ErroNoScript(linha, "ValueError: equipe pelo menos uma arma")
    if len(nomes) > MAXIMO_DE_ARMAS_EQUIPADAS:
        raise ErroNoScript(linha, f"ValueError: dá para equipar no máximo {MAXIMO_DE_ARMAS_EQUIPADAS} armas ao mesmo tempo")
    return nomes


def conferir_nome_da_arma(nome, armas, linha):
    if nome in armas:
        return armas[nome]
    if nome in NOMES_DE_TODAS_AS_ARMAS:  # Existe, mas o visitante ainda não ganhou
        raise ErroNoScript(linha, f"NameError: name '{nome}' is not defined\n# A arma {nome} ainda não foi desbloqueada. Suba de nível!")
    raise ErroNoScript(linha, f"NameError: name '{nome}' is not defined")


# Confere um bloco de regra: if, for, tiro.poder() ou pass. "laco" são os nomes das variáveis dos for em volta.
def conferir_bloco(comando, liberados, laco, profundidade):
    linha = comando.lineno
    if isinstance(comando, ast.Pass):
        return
    if isinstance(comando, ast.Expr):
        chamada = comando.value
        if not (isinstance(chamada, ast.Call) and isinstance(chamada.func, ast.Attribute) and isinstance(chamada.func.value, ast.Name)
                and chamada.func.value.id == "tiro" and chamada.func.attr in PODERES):
            raise ErroNoScript(linha, "SyntaxError: só valem linhas do tipo objeto.atributo = valor" + ("\n# Ou um poder, como tiro.quicar()" if liberados else ""))
        exigir(chamada.func.attr, liberados, linha, f"NameError: o poder tiro.{chamada.func.attr}() ainda não foi desbloqueado\n# Suba de nível para ganhar poderes!")
        if chamada.args or chamada.keywords:
            raise ErroNoScript(linha, f"TypeError: tiro.{chamada.func.attr}() não recebe nada dentro dos parênteses")
        return
    if profundidade > MAXIMO_DE_BLOCOS:
        raise ErroNoScript(linha, f"SyntaxError: no máximo {MAXIMO_DE_BLOCOS} blocos um dentro do outro")
    if isinstance(comando, ast.If):
        exigir("if", liberados, linha)
        if comando.orelse and not (len(comando.orelse) == 1 and isinstance(comando.orelse[0], ast.If)):  # "elif" vira um if dentro do else, e não precisa do else liberado
            exigir("else", liberados, comando.orelse[0].lineno)
        conferir_condicao(comando.test, liberados, laco, linha)
        dentro = comando.body + comando.orelse
    else:  # ast.For
        exigir("for", liberados, linha)
        quantas = comando.iter
        if (not isinstance(comando.target, ast.Name) or comando.orelse or not isinstance(quantas, ast.Call) or not isinstance(quantas.func, ast.Name)
                or quantas.func.id != "range" or len(quantas.args) != 1 or quantas.keywords or not isinstance(quantas.args[0], ast.Constant)):
            raise ErroNoScript(linha, "SyntaxError: o for daqui é sempre assim: for i in range(2):")
        vezes = quantas.args[0].value
        if type(vezes) is not int or not 1 <= vezes <= MAXIMO_DE_REPETICOES:
            raise ErroNoScript(linha, f"ValueError: o número do range deve ficar entre 1 e {MAXIMO_DE_REPETICOES}")
        laco = laco | {comando.target.id}
        dentro = comando.body
    for bloco in dentro:
        conferir_bloco(bloco, liberados, laco, profundidade + 1)


def conferir_condicao(no, liberados, laco, linha):
    if isinstance(no, ast.Constant) and type(no.value) in (int, bool):
        return
    if isinstance(no, ast.Attribute) and isinstance(no.value, ast.Name):
        nome = f"{no.value.id}.{no.attr}"
        if nome not in VARIAVEIS:
            raise ErroNoScript(linha, f"AttributeError: '{nome}' não pode ser usado na condição\n# Dá para usar: " + ", ".join(v for v in VARIAVEIS if v in liberados))
        exigir(nome, liberados, linha)
        return
    if isinstance(no, ast.Name):
        if no.id not in laco:
            raise ErroNoScript(linha, f"NameError: name '{no.id}' is not defined")
        return
    if isinstance(no, ast.Compare) and all(type(operacao) in COMPARACOES for operacao in no.ops):
        for parte in [no.left] + no.comparators:
            conferir_condicao(parte, liberados, laco, linha)
        return
    if isinstance(no, ast.BoolOp):  # and / or
        for parte in no.values:
            conferir_condicao(parte, liberados, laco, linha)
        return
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.Not, ast.USub)):
        conferir_condicao(no.operand, liberados, laco, linha)
        return
    if isinstance(no, ast.BinOp) and type(no.op) in CONTAS:
        if isinstance(no.op, ast.Mod):
            exigir("%", liberados, linha)
        conferir_condicao(no.left, liberados, laco, linha)
        conferir_condicao(no.right, liberados, laco, linha)
        return
    raise ErroNoScript(linha, "TypeError: na condição só valem números, variáveis, contas (+ - * %) e comparações (== != < > <= >=)")


def exigir(palavra, liberados, linha, mensagem=None):
    if palavra not in liberados:
        raise ErroNoScript(linha, mensagem or f"SyntaxError: '{palavra}' ainda não foi desbloqueado\n# Ganhe poderes subindo de nível para liberar o {palavra}.")


def ler_numero(no, linha):
    try:
        return calcular(no)
    except (TypeError, NameError) as erro:
        raise ErroNoScript(linha, f"{type(erro).__name__}: {erro}")
    except ZeroDivisionError:
        raise ErroNoScript(linha, "ZeroDivisionError: division by zero")


# RESUMO AO VIVO: para cada arma desbloqueada, o produto dos parâmetros e o limite, mesmo com o script incompleto.
# Lê linha por linha, ignorando as que ainda estão com erro (o visitante pode estar no meio da digitação).
# Devolve uma lista de (nome, texto, esta_dentro_do_limite).
def resumo_do_orcamento(texto, armas):
    valores = {nome: dict(arma.valores) for nome, arma in armas.items()}
    for linha_de_texto in texto.split("\n"):
        try:
            comando = ast.parse(linha_de_texto.strip()).body[0]
            alvo = comando.targets[0]
            nome, atributo = alvo.value.id, alvo.attr
            if nome in valores and atributo in valores[nome]:
                valores[nome][atributo] = calcular(comando.value)
        except Exception:  # Linha incompleta, comentário, ou qualquer outra coisa: só pula
            continue
    resumo = []
    for nome, arma in armas.items():
        primeiro, segundo = arma.nomes_dos_parametros()
        produto = valores[nome][primeiro] * valores[nome][segundo]
        resumo.append((nome, f"{nome}: {primeiro} x {segundo} = {valores[nome][primeiro]:g} x {valores[nome][segundo]:g} = {produto:g} / limite {arma.limite}", produto <= arma.limite))
    return resumo


# SELF-CHECK: rode "python script_das_armas.py" para conferir se a validação aceita e recusa os scripts certos.
if __name__ == "__main__":
    from armas import criar_todas_as_armas

    todas = criar_todas_as_armas()
    desbloqueadas = {nome: todas[nome] for nome in ("blaster", "laser")}

    def conferir(texto):
        return conferir_script(texto, desbloqueadas, ["blaster"])

    configuracao, erro = conferir("passaro.armas = [blaster, laser]\nlaser.quantidade = 3\nlaser.grossura = 2\nblaster.cadencia = 6\nblaster.dano = 2")
    assert erro is None and configuracao["armas"] == ["blaster", "laser"] and configuracao["valores"]["laser"] == {"quantidade": 3, "grossura": 2}
    assert conferir("# só um comentário")[1] is None  # Script sem mudanças também vale
    assert conferir("laser.quantidade = 2 * 3 - 4")[0]["valores"]["laser"]["quantidade"] == 2  # Conta simples

    def erro_de(texto):
        return conferir(texto)[1]

    assert erro_de("passaro.armas = [blaster]\nlaser.quantidade = 3\nlaser.grossura = 3")[0] == 3  # O erro do limite aponta a última linha que mexeu no laser
    assert erro_de("laser.quantidade = 3\nlaser.grossura = 3")[0] == 2 and "limite do laser é 6" in erro_de("laser.quantidade = 3\nlaser.grossura = 3")[1]  # 9 > 6: passa do limite, aponta a linha 2
    assert erro_de("laser.grossura = 9")[1].startswith("ValueError")  # Fora da faixa do parâmetro
    assert erro_de("laser.grossura = 2.5")[1].startswith("TypeError")  # Precisa ser inteiro
    assert erro_de("laser.cor = 3")[1].startswith("AttributeError")  # Parâmetro que não existe
    assert erro_de("passaro.vida = 99")[1].startswith("AttributeError")  # Não dá para se dar vida infinita
    assert erro_de("passaro.armas = [missil]")[1].startswith("NameError") and "desbloqueada" in erro_de("passaro.armas = [missil]")[1]  # Arma bloqueada
    assert erro_de("passaro.armas = [canhao]")[1].startswith("NameError")  # Arma que não existe
    assert erro_de("passaro.armas = [blaster, laser, blaster]")[1].startswith("ValueError")  # Repetida
    assert erro_de("passaro.armas = []")[1].startswith("ValueError")  # Lista vazia
    assert erro_de("passaro.armas = 'laser'")[1].startswith("TypeError")  # Não é lista
    assert erro_de("passaro.armas = ['laser']")[1].startswith("TypeError")  # Texto dentro da lista
    assert erro_de("blaster.dano = 3\nlaser.grossura == 2")[0] == 2  # Erro na linha 2
    assert erro_de("blaster.dano = 3\nlaser.grossura = ")[0] == 2 and erro_de("blaster.dano = 3\nlaser.grossura = ")[1].startswith("SyntaxError")  # Linha incompleta
    assert erro_de("import os")[1].startswith("SyntaxError")  # Tentativas de rodar outra coisa: recusadas
    assert erro_de("__import__('os').system('dir')")[1].startswith("SyntaxError")
    assert erro_de("blaster.dano = __import__('os').getpid()")[1].startswith("TypeError")
    assert erro_de("print('oi')")[1].startswith("SyntaxError")
    assert erro_de("x = 3")[1].startswith("SyntaxError")
    assert erro_de("blaster.dano = 9 ** 9 ** 9")[1].startswith("TypeError")  # Potência não é permitida
    assert erro_de("a" * 3000)[1].startswith("SyntaxError")  # Grande demais

    # PODERES: regras com if / for, e o que ainda não foi desbloqueado
    from poderes import executar_regras
    tudo = set(PODERES) | {palavra for poder in PODERES.values() for palavra in poder.libera}
    script = "if tiro.acertou:\n    tiro.quicar()\nif tiro.numero % 3 == 0:\n    tiro.dividir()\nelse:\n    for i in range(2):\n        tiro.multiplicar()"
    configuracao, erro = conferir_script(script, desbloqueadas, ["blaster"], tudo)
    assert erro is None and [momento for momento, _ in configuracao["regras"]] == ["sempre", "disparo"]
    regras = configuracao["regras"]
    def variaveis(numero):
        return {"tiro.numero": numero, "tiro.quiques": 0, "passaro.vida": 5, "inimigo.vida": 0}
    assert executar_regras(regras, "disparo", variaveis(6)) == {"dividir": 1}
    assert executar_regras(regras, "disparo", variaveis(7)) == {"multiplicar": 2}
    assert executar_regras(regras, "acerto", variaveis(7)) == {"quicar": 1}
    assert executar_regras(regras, "parede", variaveis(7)) == {}  # A regra do acerto não roda na parede
    eventos, _ = conferir_script("if tiro.acertou or tiro.na_parede:\n    tiro.quicar()\nif tiro.saiu:\n    tiro.repetir()", desbloqueadas, ["blaster"], tudo)
    assert executar_regras(eventos["regras"], "parede", variaveis(1)) == {"quicar": 1}
    assert executar_regras(eventos["regras"], "disparo", variaveis(1)) == {"repetir": 1}
    assert erro_de("if tiro.acertou:\n    tiro.quicar()")[1].startswith("SyntaxError")  # Sem poderes, o if está bloqueado
    so_quicar = {"quicar", "if", "tiro.acertou", "tiro.quiques"}
    assert conferir_script("if tiro.acertou and tiro.quiques < 2:\n    tiro.quicar()", desbloqueadas, ["blaster"], so_quicar)[1] is None
    def erro_com_quicar(texto):
        return conferir_script(texto, desbloqueadas, ["blaster"], so_quicar)[1]
    assert erro_com_quicar("if tiro.numero % 3 == 0:\n    tiro.quicar()")[1].startswith("SyntaxError")  # tiro.numero ainda bloqueado
    assert erro_com_quicar("if tiro.acertou:\n    tiro.dividir()")[0] == 2  # Poder bloqueado, erro na linha 2
    assert erro_com_quicar("if tiro.acertou:\n    tiro.quicar()\nelse:\n    tiro.quicar()")[1].startswith("SyntaxError")  # else bloqueado
    assert erro_com_quicar("if tiro.acertou:\n    x = 3")[1].startswith("SyntaxError")  # Dentro do if, só poderes
    assert erro_com_quicar("if tiro.acertou:\n    tiro.quicar(99)")[1].startswith("TypeError")
    assert erro_com_quicar("if __import__('os'):\n    tiro.quicar()")[1].startswith("TypeError")
    assert erro_com_quicar("if tiro.vida:\n    tiro.quicar()")[1].startswith("AttributeError")
    assert conferir_script("for i in range(9):\n    tiro.multiplicar()", desbloqueadas, ["blaster"], tudo)[1][1].startswith("ValueError")  # range grande demais
    assert conferir_script("for i in lista:\n    tiro.multiplicar()", desbloqueadas, ["blaster"], tudo)[1][1].startswith("SyntaxError")
    fundo = "for a in range(3):\n for b in range(3):\n  for c in range(3):\n   for d in range(3):\n    tiro.multiplicar()"
    assert conferir_script(fundo, desbloqueadas, ["blaster"], tudo)[1][1].startswith("SyntaxError")  # Blocos demais

    resumo = resumo_do_orcamento("laser.quantidade = 3\nlaser.grossura = 3\nblaster.dano = ", desbloqueadas)  # A última linha ainda está sendo digitada
    assert [(nome, ok) for nome, _, ok in resumo] == [("blaster", True), ("laser", False)]
    print("script_das_armas.py: tudo certo!")
