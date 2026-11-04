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
# No fim conferimos o LIMITE COMPARTILHADO de cada arma: parametro1 x parametro2 <= limite.
# Os erros saem como no Python: "linha 3: ValueError: ...".

import ast  # Ferramenta do Python que lê código sem executar

from editor import calcular  # Calcula o valor de um número (ou de uma conta simples) sem executar nada

MAXIMO_DE_ARMAS_EQUIPADAS = 2
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
# A configuração é {"armas": [nomes], "valores": {nome_da_arma: {parametro: valor}}}.
def conferir_script(texto, armas, equipadas):
    try:
        return ler_script(texto, armas, equipadas), None
    except ErroNoScript as erro:
        return None, (erro.linha, erro.mensagem)


def ler_script(texto, armas, equipadas):
    if len(texto) > MAXIMO_DE_CARACTERES_DO_SCRIPT:
        raise ErroNoScript(1, "SyntaxError: o script está grande demais")
    try:
        arvore = ast.parse(texto)
    except (SyntaxError, ValueError) as erro:
        raise ErroNoScript(getattr(erro, "lineno", 1) or 1, f"SyntaxError: {getattr(erro, 'msg', erro)}\n# O Python não entendeu esta linha. Confira o ponto, o = e os colchetes [ ].")

    configuracao = {"armas": list(equipadas), "valores": {nome: dict(arma.valores) for nome, arma in armas.items()}}
    linha_de_cada_arma = {}  # Em que linha cada arma foi mexida por último (para apontar o erro do limite)
    for comando in arvore.body:  # Cada linha de código (os comentários não aparecem na árvore)
        linha = comando.lineno
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

    resumo = resumo_do_orcamento("laser.quantidade = 3\nlaser.grossura = 3\nblaster.dano = ", desbloqueadas)  # A última linha ainda está sendo digitada
    assert [(nome, ok) for nome, _, ok in resumo] == [("blaster", True), ("laser", False)]
    print("script_das_armas.py: tudo certo!")
