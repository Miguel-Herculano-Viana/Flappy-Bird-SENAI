# CLASSE PAINEL
# O painel de código que flutua por cima do jogo, no canto direito. Ele é desenhado direto no monitor,
# na resolução real, por isso o texto fica nítido mesmo com o jogo em pixel art ampliado.
# O visual imita o próprio jogo: vidro azul transparente (dá para ver os canos passando atrás),
# moldura com as cores do cano e barra de título como a "tampa" do cano.
# Em cima fica o editor (quando tem um desafio); embaixo, os MEDIDORES: os atributos do jogo e seus valores.

import re  # Ferramenta do Python para achar padrões em textos (usada para colorir o código)
import textwrap  # Ferramenta do Python que quebra um texto comprido em várias linhas

import pygame  # Biblioteca de jogos que estamos usando

COR_DO_VIDRO = (14, 20, 48)  # Azul-marinho, o "vidro" do painel
TRANSPARENCIA_DO_VIDRO = 205  # 0 = invisível, 255 = opaco (um pouco transparente: os canos aparecem atrás)
COR_DO_CONTORNO = (58, 67, 52)  # O contorno escuro dos canos
COR_DA_MOLDURA = (72, 148, 58)  # O verde do cano
COR_DO_BRILHO = (106, 191, 91)  # O verde claro do brilho do cano
COR_DA_SOMBRA = (39, 81, 32)  # O verde escuro da sombra do cano
COR_DO_TITULO = (255, 255, 255)  # Branco
COR_DE_COMENTARIO = (140, 200, 130)  # Verde claro, como os comentários (#) nos editores de código
COR_DO_NOME = (120, 190, 255)  # Azul, para nomes (canos, abertura...)
COR_DO_NUMERO = (245, 165, 90)  # Laranja, para números
COR_DO_SINAL = (230, 230, 240)  # Branco, para = . e outros sinais
COR_DO_PROMPT = (120, 125, 145)  # Cinza, para o ">>>" do começo da linha
COR_DA_BARRA_DO_MEDIDOR = (106, 191, 91)  # Verde do cano
COR_DA_BARRA_QUE_MUDOU = (255, 200, 60)  # Amarelo, enquanto o valor acabou de mudar
COR_DO_FUNDO_DO_MEDIDOR = (39, 45, 70)  # Azul acinzentado
LINHAS_QUE_CABEM_NO_PAINEL = 28  # O tamanho da letra é escolhido para caber esta quantidade de linhas na altura do painel
VELOCIDADE_DA_ANIMACAO_DO_MEDIDOR = 5.0  # Quão rápido a barra desliza até o valor novo
SEGUNDOS_DE_DESTAQUE = 2.0  # Por quanto tempo um medidor fica amarelo depois de mudar


# CLASSE MEDIDOR: uma linha do painel mostrando um atributo do jogo (ex.: passaro.forca_da_gravidade = 500)
# com uma barra embaixo. Ela é pequena e só o Painel usa, por isso mora no mesmo arquivo.
class Medidor:

    def __init__(self, nome, valor, maximo_da_barra):
        self.nome = nome  # Como o atributo é escrito em código
        self.valor_mostrado = float(valor)  # O valor que aparece agora (desliza até o alvo)
        self.valor_alvo = float(valor)  # O valor de verdade
        self.maximo_da_barra = maximo_da_barra  # Valor que enche a barra inteira
        self.segundos_de_destaque = 0.0  # Maior que zero = acabou de mudar (fica amarelo)

    # Recebe o valor de verdade. Se mudou, a barra começa a deslizar e o medidor fica em destaque.
    def definir(self, valor):
        if valor != self.valor_alvo:
            self.valor_alvo = float(valor)
            self.segundos_de_destaque = SEGUNDOS_DE_DESTAQUE

    def atualizar(self, tempo_real):
        self.valor_mostrado += (self.valor_alvo - self.valor_mostrado) * min(1.0, VELOCIDADE_DA_ANIMACAO_DO_MEDIDOR * tempo_real)  # Desliza até o alvo
        self.segundos_de_destaque = max(0.0, self.segundos_de_destaque - tempo_real)


class Painel:

    # CONSTRUTOR: "retangulo" é a posição e o tamanho do painel no monitor.
    # "tamanho_do_pixel" é quantos pixels do monitor valem 1 pixel do jogo (para a moldura ter a mesma "grossura" da pixel art).
    def __init__(self, retangulo, tamanho_do_pixel):
        # ATRIBUTOS
        self.retangulo = retangulo  # Onde o painel fica no monitor
        self.pixel = tamanho_do_pixel
        self.altura_da_linha = retangulo.height // LINHAS_QUE_CABEM_NO_PAINEL  # Altura de cada linha de texto em pixels
        self.fonte = pygame.font.SysFont("consolas", self.altura_da_linha * 3 // 4)  # Fonte "monoespaçada" (todas as letras com a mesma largura), como nos editores
        self.fonte_do_titulo = pygame.font.SysFont("consolas", self.altura_da_linha * 3 // 4, bold=True)
        self.margem = self.altura_da_linha  # Espaço entre a borda do painel e o texto
        self.altura_da_barra_de_titulo = self.altura_da_linha * 3 // 2 // self.pixel * self.pixel  # Arredondada para um número inteiro de "pixels do jogo"
        self.medidores = {}  # Dicionário: nome do atributo -> Medidor
        self.fundo = self.montar_fundo()  # O fundo nunca muda, então é desenhado uma vez só e guardado

    # Monta a imagem do fundo do painel (vidro + moldura + barra de título), com transparência.
    def montar_fundo(self):
        p = self.pixel  # 1 "pixel do jogo", em pixels do monitor
        largura, altura = self.retangulo.size
        fundo = pygame.Surface((largura, altura), pygame.SRCALPHA)  # Imagem transparente do tamanho do painel
        fundo.fill((*COR_DO_VIDRO, TRANSPARENCIA_DO_VIDRO), (p, p, largura - 2 * p, altura - 2 * p))  # O vidro
        pygame.draw.rect(fundo, COR_DO_CONTORNO, (0, 0, largura, altura), width=p)  # Contorno escuro por fora...
        pygame.draw.rect(fundo, COR_DA_MOLDURA, (p, p, largura - 2 * p, altura - 2 * p), width=p)  # ...e moldura verde por dentro

        # Barra de título, desenhada como a tampa do cano: contorno, verde, faixa de brilho em cima, sombra embaixo
        barra = pygame.Rect(0, 0, largura, self.altura_da_barra_de_titulo)
        fundo.fill(COR_DO_CONTORNO, barra)
        fundo.fill(COR_DA_MOLDURA, barra.inflate(-2 * p, -2 * p))
        fundo.fill(COR_DO_BRILHO, (2 * p, 2 * p, largura - 4 * p, p))  # Brilho
        fundo.fill(COR_DA_SOMBRA, (p, barra.bottom - 2 * p, largura - 2 * p, p))  # Sombra
        for coluna in range(3, largura // p // 5):  # Xadrezinho de brilho na esquerda, como na tampa do cano
            for linha in range(3, barra.height // p - 2):
                if (coluna + linha) % 2 == 0:
                    fundo.fill(COR_DO_BRILHO, (largura - coluna * p - 3 * p, linha * p, p, p))

        # Cantos "pixelados": apaga o quadradinho de cada canto, como na pixel art
        for x, y in ((0, 0), (largura - p, 0), (0, altura - p), (largura - p, altura - p)):
            fundo.fill((0, 0, 0, 0), (x, y, p, p))
        return fundo

    # MÉTODOS

    # Mostra (ou atualiza) um atributo do jogo na parte de baixo do painel.
    def mostrar_valor(self, nome, valor, maximo_da_barra):
        if nome not in self.medidores:  # Primeira vez: cria o medidor
            self.medidores[nome] = Medidor(nome, valor, maximo_da_barra)
        self.medidores[nome].definir(valor)

    def atualizar(self, tempo_real):
        for medidor in self.medidores.values():
            medidor.atualizar(tempo_real)

    # Desenha o painel no monitor. Se tiver um "editor" aberto, ele aparece em cima.
    # "mensagem" (uma lista de linhas) troca a explicação normal quando o editor está fechado.
    def desenhar(self, monitor, editor=None, mensagem=None):
        monitor.blit(self.fundo, self.retangulo)  # Vidro, moldura e barra de título
        barra_de_titulo = pygame.Rect(self.retangulo.x, self.retangulo.y, self.retangulo.width, self.altura_da_barra_de_titulo)
        titulo = self.fonte_do_titulo.render("codigo.py", True, COR_DO_TITULO)  # Nome do "arquivo", como numa aba de editor
        sombra = self.fonte_do_titulo.render("codigo.py", True, COR_DA_SOMBRA)
        posicao = titulo.get_rect(midleft=(barra_de_titulo.x + self.margem, barra_de_titulo.centery))
        monitor.blit(sombra, posicao.move(self.pixel // 2, self.pixel // 2))  # Sombra, como no texto do placar
        monitor.blit(titulo, posicao)

        topo_do_conteudo = barra_de_titulo.bottom + self.margem
        if editor:  # Tem um desafio: o editor ocupa a parte de cima
            editor.desenhar(monitor, self, topo_do_conteudo)
        else:  # Sem editor: uma explicação (ou a mensagem recebida)
            linhas = mensagem or ["Voe com ESPAÇO.", "Quando aparecer um desafio, aperte ENTER", "e mude o jogo com código!"]
            y = topo_do_conteudo
            for linha in linhas:
                y = self.escrever_com_quebra(monitor, linha, COR_DE_COMENTARIO, y, prefixo="# ")
        self.desenhar_medidores(monitor)

    # Desenha os medidores no pé do painel: uma linha de código e uma barra para cada atributo.
    def desenhar_medidores(self, monitor):
        espaco_de_cada_medidor = self.altura_da_linha * 2  # Uma linha para o texto, meia para a barra e meia de folga
        y = self.retangulo.bottom - self.margem - len(self.medidores) * espaco_de_cada_medidor  # Começa de baixo para cima, para caber
        self.escrever(monitor, "# Atributos do jogo agora:", COR_DE_COMENTARIO, y - self.altura_da_linha * 3 // 2)
        largura_da_barra = self.retangulo.width - 2 * self.margem
        for medidor in self.medidores.values():
            mudou = medidor.segundos_de_destaque > 0
            self.escrever_colorido(monitor, f"{medidor.nome} = {round(medidor.valor_mostrado)}", self.retangulo.x + self.margem, y)
            if mudou:  # Acabou de mudar: avisa do lado
                largura_do_texto = self.fonte.size(f"{medidor.nome} = {round(medidor.valor_alvo)}  ")[0]
                monitor.blit(self.fonte.render("<- mudou!", True, COR_DA_BARRA_QUE_MUDOU), (self.retangulo.x + self.margem + largura_do_texto, y))
            y_da_barra = y + self.altura_da_linha
            fracao = max(0.0, min(1.0, medidor.valor_mostrado / medidor.maximo_da_barra))  # Quanto da barra está cheia (entre 0 e 1)
            espessura = max(self.pixel * 2, self.altura_da_linha // 4)  # Barra com cantos retos e contorno, no estilo da pixel art
            pygame.draw.rect(monitor, COR_DO_FUNDO_DO_MEDIDOR, (self.retangulo.x + self.margem, y_da_barra, largura_da_barra, espessura))
            pygame.draw.rect(monitor, COR_DA_BARRA_QUE_MUDOU if mudou else COR_DA_BARRA_DO_MEDIDOR, (self.retangulo.x + self.margem, y_da_barra, round(largura_da_barra * fracao), espessura))
            pygame.draw.rect(monitor, COR_DO_CONTORNO, (self.retangulo.x + self.margem, y_da_barra, largura_da_barra, espessura), width=max(1, self.pixel // 2))
            y += espaco_de_cada_medidor

    # MÉTODO AUXILIAR: escreve uma linha de texto alinhada à esquerda, na altura pedida.
    def escrever(self, monitor, texto, cor, distancia_do_topo):
        imagem_do_texto = self.fonte.render(texto, True, cor)  # Transforma o texto em imagem
        monitor.blit(imagem_do_texto, (self.retangulo.x + self.margem, distancia_do_topo))  # Desenha com a margem da esquerda

    # MÉTODO AUXILIAR: escreve um texto que pode não caber numa linha só; ele é quebrado em várias.
    # "prefixo" vai no começo de cada linha (ex.: "# " para todas as linhas de um comentário).
    # Devolve a altura logo abaixo da última linha, para saber onde escrever a próxima coisa.
    def escrever_com_quebra(self, monitor, texto, cor, distancia_do_topo, prefixo=""):
        letras_por_linha = (self.retangulo.width - 2 * self.margem) // self.fonte.size("a")[0]  # Quantas letras cabem na largura
        for linha in textwrap.wrap(texto, letras_por_linha, initial_indent=prefixo, subsequent_indent=prefixo):
            self.escrever(monitor, linha, cor, distancia_do_topo)
            distancia_do_topo += self.altura_da_linha
        return distancia_do_topo

    # MÉTODO AUXILIAR: escreve código com cores diferentes para nomes, números e sinais (como um editor de verdade).
    def escrever_colorido(self, monitor, texto, x, y, so_prompt=False):
        largura_da_letra = self.fonte.size("a")[0]  # Fonte monoespaçada: todas as letras têm esta largura
        for pedaco in re.findall(r"\d+\.?\d*|\w+|\s+|.", texto):  # Separa em números, palavras, espaços e sinais
            if so_prompt:
                cor = COR_DO_PROMPT
            elif pedaco[0].isdigit():
                cor = COR_DO_NUMERO
            elif pedaco[0].isalpha() or pedaco[0] == "_":
                cor = COR_DO_NOME
            else:
                cor = COR_DO_SINAL
            monitor.blit(self.fonte.render(pedaco, True, cor), (x, y))
            x += len(pedaco) * largura_da_letra
