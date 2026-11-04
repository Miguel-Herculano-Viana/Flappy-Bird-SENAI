# CLASSE PLACAR
# Guarda os pontos e o recorde do jogador e sabe se desenhar na tela.
# Repare que ela NÃO herda de ninguém: nem toda classe precisa de uma classe mãe.

from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

CAMINHO_DO_ARQUIVO_DO_RECORDE = Path(__file__).parent / "recorde.txt"  # Arquivo onde o recorde fica guardado, mesmo fechando o jogo
TAMANHO_DA_FONTE_GRANDE = 28  # Tamanho das letras dos pontos e do "FIM DE JOGO"
TAMANHO_DA_FONTE_PEQUENA = 20  # Tamanho das letras das outras frases
COR_DO_TEXTO = (255, 255, 255)  # Branco
COR_DO_DESTAQUE = (255, 220, 0)  # Amarelo, para o "NOVO RECORDE!"
COR_DA_SOMBRA = (0, 0, 0)  # Preto, desenhado atrás do texto para ele aparecer bem em cima do céu
DISTANCIA_DO_TOPO_DA_TELA = 16  # Quantos pixels abaixo do topo os pontos ficam durante a partida


class Placar:

    # CONSTRUTOR: todo placar novo começa com zero pontos e lê o recorde guardado no arquivo
    def __init__(self):
        # ATRIBUTOS
        self.pontos = 0  # Quantos canos o jogador já passou nesta partida
        self.bateu_o_recorde = False  # Vira True se esta partida passar o recorde
        self.fonte_grande = pygame.font.Font(None, TAMANHO_DA_FONTE_GRANDE)  # Fonte das letras grandes ("None" = fonte padrão do pygame)
        self.fonte_pequena = pygame.font.Font(None, TAMANHO_DA_FONTE_PEQUENA)  # Fonte das letras pequenas
        if CAMINHO_DO_ARQUIVO_DO_RECORDE.exists():  # Já existe um recorde guardado?
            self.recorde = int(CAMINHO_DO_ARQUIVO_DO_RECORDE.read_text())  # Lê o número que está no arquivo
        else:  # Primeira vez que o jogo roda neste computador
            self.recorde = 0  # Ainda não tem recorde

    # MÉTODOS

    # "quantidade=1" é um PARÂMETRO COM VALOR PADRÃO: se ninguém disser quantos pontos, vale 1.
    def marcar_ponto(self, quantidade=1):
        self.pontos += quantidade  # Soma os pontos

    # Chamado quando o jogador perde: se fez mais pontos que o recorde, guarda o novo recorde.
    def registrar_fim_de_jogo(self):
        if self.pontos > self.recorde:  # Passou o recorde?
            self.recorde = self.pontos  # O recorde agora é a pontuação desta partida
            self.bateu_o_recorde = True  # Marca que bateu, para mostrar na tela
            CAMINHO_DO_ARQUIVO_DO_RECORDE.write_text(str(self.recorde))  # Grava no arquivo, para não perder ao fechar o jogo

    # Desenha só os pontos no topo da tela, durante a partida.
    def desenhar(self, tela):
        self.desenhar_texto_com_sombra(tela, str(self.pontos), self.fonte_grande, COR_DO_TEXTO, DISTANCIA_DO_TOPO_DA_TELA)  # Número dos pontos

    # Desenha a tela de início, antes da primeira batida de asas.
    def desenhar_tela_de_inicio(self, tela):
        self.desenhar_texto_com_sombra(tela, "FLAPPY BIRD", self.fonte_grande, COR_DO_TEXTO, 40)  # Título
        self.desenhar_texto_com_sombra(tela, f"Recorde: {self.recorde}", self.fonte_pequena, COR_DO_DESTAQUE, 68)  # O desafio: bater este número
        self.desenhar_texto_com_sombra(tela, "Aperte ESPAÇO", self.fonte_pequena, COR_DO_TEXTO, 176)  # Como começar

    # Desenha a tela de fim de jogo, com os pontos e o recorde.
    def desenhar_fim_de_jogo(self, tela):
        self.desenhar_texto_com_sombra(tela, "FIM DE JOGO", self.fonte_grande, COR_DO_TEXTO, 64)  # Título
        self.desenhar_texto_com_sombra(tela, f"Pontos: {self.pontos}", self.fonte_pequena, COR_DO_TEXTO, 100)  # Pontos desta partida
        self.desenhar_texto_com_sombra(tela, f"Recorde: {self.recorde}", self.fonte_pequena, COR_DO_TEXTO, 118)  # Melhor pontuação até hoje
        if self.bateu_o_recorde:  # Só aparece se esta partida bateu o recorde
            self.desenhar_texto_com_sombra(tela, "NOVO RECORDE!", self.fonte_pequena, COR_DO_DESTAQUE, 136)  # Comemoração em amarelo
        self.desenhar_texto_com_sombra(tela, "Aperte ESPAÇO", self.fonte_pequena, COR_DO_TEXTO, 176)  # Como jogar de novo

    # MÉTODO AUXILIAR: usado pelos outros métodos para não repetir o mesmo código várias vezes.
    def desenhar_texto_com_sombra(self, tela, texto, fonte, cor, distancia_do_topo):
        imagem_da_sombra = fonte.render(texto, True, COR_DA_SOMBRA)  # Transforma o texto em uma imagem preta
        imagem_do_texto = fonte.render(texto, True, cor)  # E em uma imagem colorida
        posicao_do_texto = imagem_do_texto.get_rect(midtop=(tela.get_width() // 2, distancia_do_topo))  # Centralizado na horizontal
        tela.blit(imagem_da_sombra, posicao_do_texto.move(1, 1))  # Desenha a sombra 1 pixel para baixo e para a direita
        tela.blit(imagem_do_texto, posicao_do_texto)  # Desenha o texto por cima
