# CLASSE PAINEL
# O painel de código que fica ao lado do jogo. Ele é desenhado direto no monitor, na resolução real,
# por isso o texto fica nítido mesmo com o jogo em pixel art ampliado.
# Em cima fica o editor (quando tem um desafio); embaixo, os MEDIDORES: os atributos do jogo e seus valores.

import re  # Ferramenta do Python para achar padrões em textos (usada para colorir o código)

import pygame  # Biblioteca de jogos que estamos usando

COR_DO_FUNDO_DO_PAINEL = (30, 32, 44)  # Cinza azulado escuro, como um editor de código
COR_DA_BARRA_DE_TITULO = (44, 47, 64)  # Um pouco mais claro, para a barra de cima
COR_DO_TITULO = (200, 204, 220)  # Cinza claro
COR_DE_COMENTARIO = (110, 160, 110)  # Verde, como os comentários (#) nos editores de código
COR_DO_NOME = (120, 190, 255)  # Azul, para nomes (canos, abertura...)
COR_DO_NUMERO = (245, 165, 90)  # Laranja, para números
COR_DO_SINAL = (230, 230, 240)  # Branco, para = . e outros sinais
COR_DO_PROMPT = (120, 125, 145)  # Cinza, para o ">>>" do começo da linha
COR_DA_BARRA_DO_MEDIDOR = (120, 190, 255)  # Azul
COR_DA_BARRA_QUE_MUDOU = (255, 200, 60)  # Amarelo, enquanto o valor acabou de mudar
COR_DO_FUNDO_DO_MEDIDOR = (55, 60, 85)  # Cinza azulado
LINHAS_QUE_CABEM_NO_PAINEL = 30  # O tamanho da letra é escolhido para caber esta quantidade de linhas na altura do painel
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

    # CONSTRUTOR: "retangulo" é a posição e o tamanho do painel no monitor
    def __init__(self, retangulo):
        # ATRIBUTOS
        self.retangulo = retangulo  # Onde o painel fica no monitor
        self.altura_da_linha = retangulo.height // LINHAS_QUE_CABEM_NO_PAINEL  # Altura de cada linha de texto em pixels
        self.fonte = pygame.font.SysFont("consolas", self.altura_da_linha * 3 // 4)  # Fonte "monoespaçada" (todas as letras com a mesma largura), como nos editores
        self.margem = self.altura_da_linha  # Espaço entre a borda do painel e o texto
        self.medidores = {}  # Dicionário: nome do atributo -> Medidor

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
        pygame.draw.rect(monitor, COR_DO_FUNDO_DO_PAINEL, self.retangulo, border_radius=self.margem // 2)  # Fundo com cantos arredondados
        barra_de_titulo = pygame.Rect(self.retangulo.x, self.retangulo.y, self.retangulo.width, self.altura_da_linha * 3 // 2)  # Faixa no topo
        pygame.draw.rect(monitor, COR_DA_BARRA_DE_TITULO, barra_de_titulo, border_top_left_radius=self.margem // 2, border_top_right_radius=self.margem // 2)  # Só os cantos de cima arredondados
        self.escrever(monitor, "codigo.py", COR_DO_TITULO, barra_de_titulo.centery - self.altura_da_linha // 2)  # Nome do "arquivo", como numa aba de editor

        topo_do_conteudo = barra_de_titulo.bottom + self.margem
        if editor:  # Tem um desafio: o editor ocupa a parte de cima
            editor.desenhar(monitor, self, topo_do_conteudo)
        else:  # Sem editor: uma explicação (ou a mensagem recebida)
            linhas = mensagem or ["Voe com ESPAÇO.", "Quando aparecer um desafio, aperte ENTER", "e mude o jogo com código!"]
            for numero_da_linha, linha in enumerate(linhas):
                self.escrever(monitor, "# " + linha, COR_DE_COMENTARIO, topo_do_conteudo + numero_da_linha * self.altura_da_linha)
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
            pygame.draw.rect(monitor, COR_DO_FUNDO_DO_MEDIDOR, (self.retangulo.x + self.margem, y_da_barra, largura_da_barra, self.altura_da_linha // 4), border_radius=3)
            pygame.draw.rect(monitor, COR_DA_BARRA_QUE_MUDOU if mudou else COR_DA_BARRA_DO_MEDIDOR, (self.retangulo.x + self.margem, y_da_barra, round(largura_da_barra * fracao), self.altura_da_linha // 4), border_radius=3)
            y += espaco_de_cada_medidor

    # MÉTODO AUXILIAR: escreve uma linha de texto alinhada à esquerda, na altura pedida.
    def escrever(self, monitor, texto, cor, distancia_do_topo):
        imagem_do_texto = self.fonte.render(texto, True, cor)  # Transforma o texto em imagem
        monitor.blit(imagem_do_texto, (self.retangulo.x + self.margem, distancia_do_topo))  # Desenha com a margem da esquerda

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
