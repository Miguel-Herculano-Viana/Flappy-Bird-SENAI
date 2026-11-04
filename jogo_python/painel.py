# CLASSE PAINEL
# O painel de código que fica ao lado do jogo. Ele é desenhado direto no monitor, na resolução real,
# por isso o texto fica nítido mesmo com o jogo em pixel art ampliado.

import pygame  # Biblioteca de jogos que estamos usando

COR_DO_FUNDO_DO_PAINEL = (30, 32, 44)  # Cinza azulado escuro, como um editor de código
COR_DA_BARRA_DE_TITULO = (44, 47, 64)  # Um pouco mais claro, para a barra de cima
COR_DO_TITULO = (200, 204, 220)  # Cinza claro
COR_DE_COMENTARIO = (110, 160, 110)  # Verde, como os comentários (#) nos editores de código
LINHAS_QUE_CABEM_NO_PAINEL = 30  # O tamanho da letra é escolhido para caber esta quantidade de linhas na altura do painel


class Painel:

    # CONSTRUTOR: "retangulo" é a posição e o tamanho do painel no monitor
    def __init__(self, retangulo):
        # ATRIBUTOS
        self.retangulo = retangulo  # Onde o painel fica no monitor
        self.altura_da_linha = retangulo.height // LINHAS_QUE_CABEM_NO_PAINEL  # Altura de cada linha de texto em pixels
        self.fonte = pygame.font.SysFont("consolas", self.altura_da_linha * 3 // 4)  # Fonte "monoespaçada" (todas as letras com a mesma largura), como nos editores
        self.margem = self.altura_da_linha  # Espaço entre a borda do painel e o texto

    # Desenha o painel no monitor.
    def desenhar(self, monitor):
        pygame.draw.rect(monitor, COR_DO_FUNDO_DO_PAINEL, self.retangulo, border_radius=self.margem // 2)  # Fundo com cantos arredondados
        barra_de_titulo = pygame.Rect(self.retangulo.x, self.retangulo.y, self.retangulo.width, self.altura_da_linha * 3 // 2)  # Faixa no topo
        pygame.draw.rect(monitor, COR_DA_BARRA_DE_TITULO, barra_de_titulo, border_top_left_radius=self.margem // 2, border_top_right_radius=self.margem // 2)  # Só os cantos de cima arredondados
        self.escrever(monitor, "codigo.py", COR_DO_TITULO, barra_de_titulo.centery - self.altura_da_linha // 2)  # Nome do "arquivo", como numa aba de editor
        self.escrever(monitor, "# Os desafios de código aparecem aqui", COR_DE_COMENTARIO, barra_de_titulo.bottom + self.margem)  # Painel ainda vazio

    # MÉTODO AUXILIAR: escreve uma linha de texto alinhada à esquerda, na altura pedida.
    def escrever(self, monitor, texto, cor, distancia_do_topo):
        imagem_do_texto = self.fonte.render(texto, True, cor)  # Transforma o texto em imagem
        monitor.blit(imagem_do_texto, (self.retangulo.x + self.margem, distancia_do_topo))  # Desenha com a margem da esquerda
