# CLASSE EDITOR DE SCRIPT
# Um editor de VÁRIAS linhas, com números de linha, para o script das armas do Modo Nave.
#   ENTER          -> roda o script
#   Shift + ENTER  -> cria uma linha nova (com o mesmo recuo; +4 espaços depois de ":")
#   TAB            -> 4 espaços
#   setas, Home, End, Backspace, Delete -> como num editor de texto
# Ele tem o mesmo método "desenhar(monitor, painel, topo)" do EditorDeCodigo, então o Painel desenha
# qualquer um dos dois sem saber qual é (POLIMORFISMO).

import pygame  # Biblioteca de jogos que estamos usando

MAXIMO_DE_CARACTERES = 2000  # Tamanho máximo do script
COR_DO_NUMERO_DA_LINHA = (110, 120, 150)  # Cinza azulado
COR_DO_COMENTARIO = (140, 200, 130)  # Verde claro, como os comentários (#) nos editores
COR_DA_LINHA_COM_ERRO = (110, 30, 40)  # Fundo vermelho escuro na linha do erro
COR_DA_LINHA_DO_CURSOR = (35, 45, 85)  # Fundo da linha onde está o cursor
COR_DO_CURSOR = (255, 255, 255)
COR_DO_ERRO = (255, 110, 110)
COR_DA_DICA = (140, 200, 130)
COR_DO_ACERTO = (120, 230, 120)
COR_DO_DESTAQUE = (255, 210, 60)  # Amarelo: o que o visitante deve digitar e as dicas de erro


class EditorDeScript:

    # CONSTRUTOR
    #   texto            -> o script que já vem escrito
    #   conferir         -> FUNÇÃO que recebe o texto e devolve (resultado, erro); erro é (linha, mensagem)
    #   rodape           -> FUNÇÃO que devolve linhas extras para mostrar embaixo do código: lista de (texto, cor)
    #   somente_leitura  -> True = só mostra o script, sem cursor (durante a partida)
    def __init__(self, texto, conferir=None, rodape=None, somente_leitura=False):
        # ATRIBUTOS
        self.linhas = texto.split("\n")  # LISTA de textos, um por linha
        self.conferir = conferir
        self.rodape = rodape
        self.somente_leitura = somente_leitura
        self.linha_do_cursor = 0
        self.coluna_do_cursor = 0
        self.primeira_linha_visivel = 0  # Para "rolar" o texto quando o script não cabe
        self.erro = None  # (número da linha, mensagem) do último erro
        self.resultado = None  # O que a função "conferir" devolveu quando deu certo
        self.tempo_do_cursor = 0.0
        self.bloqueado = False  # True = o teclado não escreve (o tutorial está digitando)
        self.valor_aceito = None  # Usado nos desafios do Flappy: o número que o visitante acertou
        self.valor_da_previa = None  # Usado nos desafios do Flappy: o número da linha que está sendo digitada
        self.dica = "# ENTER = rodar   Shift+ENTER = nova linha   ESC = fechar"  # Linha de ajuda embaixo do código (o tutorial troca)

    # MÉTODOS

    def acabou_o_tempo(self):  # O editor do tutorial não tem limite de tempo
        return False

    def texto(self):
        return "\n".join(self.linhas)  # Junta as linhas de volta num texto só

    def atualizar(self, tempo_real):
        self.tempo_do_cursor += tempo_real

    def tratar_evento(self, evento):
        if self.somente_leitura or self.bloqueado:
            return
        linha = self.linhas[self.linha_do_cursor]
        coluna = self.coluna_do_cursor
        if evento.type == pygame.TEXTINPUT:  # Letras, números e sinais
            novo_texto = evento.text[:max(0, MAXIMO_DE_CARACTERES - len(self.texto()))]
            self.linhas[self.linha_do_cursor] = linha[:coluna] + novo_texto + linha[coluna:]
            self.coluna_do_cursor += len(novo_texto)
        elif evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if evento.mod & pygame.KMOD_SHIFT:  # Shift + ENTER: quebra a linha em duas
                    recuo = " " * (len(linha) - len(linha.lstrip()))  # A linha nova começa com os mesmos espaços...
                    if linha[:coluna].rstrip().endswith(":"):  # ...e mais 4 depois de um "if ...:" ou "for ...:"
                        recuo += "    "
                    self.linhas[self.linha_do_cursor] = linha[:coluna]
                    self.linhas.insert(self.linha_do_cursor + 1, recuo + linha[coluna:].lstrip())
                    self.linha_do_cursor += 1
                    self.coluna_do_cursor = len(recuo)
                else:  # ENTER: roda o script
                    self.rodar()
                    return
            elif evento.key == pygame.K_TAB:  # TAB: 4 espaços (o recuo do if e do for)
                self.linhas[self.linha_do_cursor] = linha[:coluna] + "    " + linha[coluna:]
                self.coluna_do_cursor += 4
            elif evento.key == pygame.K_BACKSPACE:
                if coluna > 0:  # Apaga a letra antes do cursor
                    self.linhas[self.linha_do_cursor] = linha[:coluna - 1] + linha[coluna:]
                    self.coluna_do_cursor -= 1
                elif self.linha_do_cursor > 0:  # No começo da linha: junta com a de cima
                    linha_de_cima = self.linhas[self.linha_do_cursor - 1]
                    self.linhas[self.linha_do_cursor - 1] = linha_de_cima + linha
                    del self.linhas[self.linha_do_cursor]  # "del" apaga um item da lista
                    self.linha_do_cursor -= 1
                    self.coluna_do_cursor = len(linha_de_cima)
            elif evento.key == pygame.K_DELETE:
                if coluna < len(linha):  # Apaga a letra depois do cursor
                    self.linhas[self.linha_do_cursor] = linha[:coluna] + linha[coluna + 1:]
                elif self.linha_do_cursor < len(self.linhas) - 1:  # No fim da linha: puxa a de baixo
                    self.linhas[self.linha_do_cursor] = linha + self.linhas.pop(self.linha_do_cursor + 1)
            elif evento.key == pygame.K_LEFT:
                if coluna > 0:
                    self.coluna_do_cursor -= 1
                elif self.linha_do_cursor > 0:  # Do começo da linha, vai para o fim da de cima
                    self.linha_do_cursor -= 1
                    self.coluna_do_cursor = len(self.linhas[self.linha_do_cursor])
            elif evento.key == pygame.K_RIGHT:
                if coluna < len(linha):
                    self.coluna_do_cursor += 1
                elif self.linha_do_cursor < len(self.linhas) - 1:  # Do fim da linha, vai para o começo da de baixo
                    self.linha_do_cursor += 1
                    self.coluna_do_cursor = 0
            elif evento.key == pygame.K_UP:
                self.linha_do_cursor = max(0, self.linha_do_cursor - 1)
            elif evento.key == pygame.K_DOWN:
                self.linha_do_cursor = min(len(self.linhas) - 1, self.linha_do_cursor + 1)
            elif evento.key == pygame.K_HOME:
                self.coluna_do_cursor = 0
            elif evento.key == pygame.K_END:
                self.coluna_do_cursor = len(linha)
            else:
                return
            self.coluna_do_cursor = min(self.coluna_do_cursor, len(self.linhas[self.linha_do_cursor]))  # Linha mais curta: o cursor vai para o fim dela
        else:
            return
        self.tempo_do_cursor = 0.0  # Mexeu: o cursor aparece na hora
        self.erro = None  # O erro antigo não vale mais para o texto novo

    # ENTER: confere o script. Se der erro, leva o cursor até a linha do erro.
    def rodar(self):
        resultado, erro = self.conferir(self.texto())
        if erro:
            self.erro = erro
            self.linha_do_cursor = min(max(0, erro[0] - 1), len(self.linhas) - 1)  # As linhas do Python começam em 1; as da lista, em 0
            self.coluna_do_cursor = min(self.coluna_do_cursor, len(self.linhas[self.linha_do_cursor]))
        else:
            self.erro = None
            self.resultado = resultado

    # Desenha o editor dentro do painel, a partir da altura "topo".
    def desenhar(self, monitor, painel, topo):
        altura = painel.altura_da_linha
        largura_da_letra = painel.fonte.size("a")[0]
        esquerda = painel.retangulo.x + painel.margem
        largura_do_numero = 3 * largura_da_letra  # Espaço para o número da linha
        esquerda_do_codigo = esquerda + largura_do_numero + largura_da_letra

        linhas_de_baixo = self.montar_linhas_de_baixo(painel)  # Erro, dicas e rodapé (já quebradas para caber)
        espaco_para_o_codigo = painel.topo_dos_medidores() - topo - altura * (len(linhas_de_baixo) + 1)
        linhas_que_cabem = max(3, espaco_para_o_codigo // altura)
        if self.linha_do_cursor < self.primeira_linha_visivel:  # ROLAGEM: o cursor sempre fica visível
            self.primeira_linha_visivel = self.linha_do_cursor
        if self.linha_do_cursor >= self.primeira_linha_visivel + linhas_que_cabem:
            self.primeira_linha_visivel = self.linha_do_cursor - linhas_que_cabem + 1

        y = topo
        ultima_visivel = min(len(self.linhas), self.primeira_linha_visivel + linhas_que_cabem)
        for indice in range(self.primeira_linha_visivel, ultima_visivel):
            texto_da_linha = self.linhas[indice]
            largura_da_faixa = painel.retangulo.width - 2 * painel.margem
            if self.erro and indice == self.erro[0] - 1:  # Linha do erro: fundo vermelho
                pygame.draw.rect(monitor, COR_DA_LINHA_COM_ERRO, (esquerda, y - 1, largura_da_faixa, altura))
            elif not self.somente_leitura and indice == self.linha_do_cursor:  # Linha do cursor: fundo um pouco mais claro
                pygame.draw.rect(monitor, COR_DA_LINHA_DO_CURSOR, (esquerda, y - 1, largura_da_faixa, altura))
            numero = painel.fonte.render(str(indice + 1).rjust(2), True, COR_DO_NUMERO_DA_LINHA)  # ".rjust(2)" alinha os números à direita
            monitor.blit(numero, (esquerda, y))
            if texto_da_linha.strip().startswith("#"):  # Comentário: tudo verde
                cor = COR_DO_DESTAQUE if "Digite:" in texto_da_linha else COR_DO_COMENTARIO  # A linha "Digite:" do tutorial em amarelo
                monitor.blit(painel.fonte.render(texto_da_linha, True, cor), (esquerda_do_codigo, y))
            else:
                painel.escrever_colorido(monitor, texto_da_linha, esquerda_do_codigo, y)
            if not self.somente_leitura and indice == self.linha_do_cursor and self.tempo_do_cursor % 1.0 < 0.5:  # Cursor piscando
                pygame.draw.rect(monitor, COR_DO_CURSOR, (esquerda_do_codigo + self.coluna_do_cursor * largura_da_letra, y, 2, altura * 4 // 5))
            y += altura
        if ultima_visivel < len(self.linhas):  # Tem mais linhas abaixo
            monitor.blit(painel.fonte.render("   ...", True, COR_DO_NUMERO_DA_LINHA), (esquerda, y))
        y = topo + linhas_que_cabem * altura + altura // 2

        for texto, cor in linhas_de_baixo:
            monitor.blit(painel.fonte.render(texto, True, cor), (esquerda, y))
            y += altura

    # MÉTODO AUXILIAR: as linhas que ficam embaixo do código (erro ou dica, e o rodapé), já quebradas na largura do painel.
    def montar_linhas_de_baixo(self, painel):
        pedacos = []
        if self.erro:
            for linha_do_erro in self.erro[1].split("\n"):
                if linha_do_erro.startswith("# "):
                    pedacos.append((linha_do_erro, COR_DO_DESTAQUE))
                else:
                    pedacos.append((f"linha {self.erro[0]}: {linha_do_erro}", COR_DO_ERRO))
        elif not self.somente_leitura and self.dica:
            pedacos.append((self.dica, COR_DA_DICA))
        if self.rodape:
            pedacos.extend(self.rodape())
        letras_por_linha = (painel.retangulo.width - 2 * painel.margem) // painel.fonte.size("a")[0]
        linhas = []
        for texto, cor in pedacos:  # Quebra cada texto em várias linhas, se precisar
            prefixo = "# " if texto.startswith("# ") else ""
            for parte in painel.quebrar(texto, letras_por_linha, prefixo):
                linhas.append((parte, cor))
        return linhas
