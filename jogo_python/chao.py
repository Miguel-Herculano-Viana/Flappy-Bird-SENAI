# CLASSE CHAO
# O chão no pé da tela. Se o pássaro encostar nele, perde.

import pygame  # Biblioteca de jogos que estamos usando

from cano import VELOCIDADE_DO_CENARIO  # O chão anda na mesma velocidade dos canos, senão os canos pareceriam "escorregar"

COR_DA_TERRA = (222, 216, 149)  # Bege, a cor da terra
COR_DA_GRAMA_CLARA = (115, 191, 46)  # Verde claro, a faixa de grama em cima da terra
COR_DA_GRAMA_ESCURA = (84, 150, 32)  # Verde escuro, as listras da grama (são elas que mostram o chão andando)
ALTURA_DA_GRAMA = 6  # Grossura da faixa de grama em pixels
LARGURA_DE_CADA_LISTRA = 8  # Cada listra tem 4 pixels escuros e 4 claros, e o desenho se repete a cada 8 pixels


# HERANÇA: o Chao também "é um" Sprite do pygame.
class Chao(pygame.sprite.Sprite):

    # CONSTRUTOR: recebe o tamanho do chão e a altura da tela onde ele começa
    def __init__(self, largura, altura, posicao_do_topo):
        super().__init__()  # Chama o construtor da classe mãe (Sprite)

        # ATRIBUTOS
        self.velocidade_horizontal = VELOCIDADE_DO_CENARIO  # Quantos pixels por segundo o chão anda para a esquerda
        self.posicao_horizontal = 0.0  # Posição com casas decimais, para o movimento ficar suave

        # O TRUQUE DO CHÃO INFINITO: a imagem é uma listra mais larga que a tela.
        # O chão anda uma listra para a esquerda e volta para o começo. Como as listras são
        # todas iguais, ninguém percebe o "pulo" e parece que o chão nunca acaba.
        largura_da_imagem = largura + LARGURA_DE_CADA_LISTRA  # Uma listra a mais, para não aparecer buraco na direita
        self.image = pygame.Surface((largura_da_imagem, altura))  # Cria uma imagem vazia do tamanho do chão
        self.image.fill(COR_DA_TERRA)  # Pinta tudo de terra
        self.image.fill(COR_DA_GRAMA_CLARA, (0, 0, largura_da_imagem, ALTURA_DA_GRAMA))  # Pinta uma faixa de grama em cima
        for inicio_da_listra in range(0, largura_da_imagem, LARGURA_DE_CADA_LISTRA):  # A cada 8 pixels...
            self.image.fill(COR_DA_GRAMA_ESCURA, (inicio_da_listra, 0, LARGURA_DE_CADA_LISTRA // 2, ALTURA_DA_GRAMA))  # ...pinta uma listra escura
        self.rect = self.image.get_rect(topleft=(0, posicao_do_topo))  # Posiciona o chão no pé da tela

    # SOBRESCRITA: o chão também tem o seu próprio "update"
    def update(self, tempo_do_quadro):
        self.posicao_horizontal -= self.velocidade_horizontal * tempo_do_quadro  # Anda para a esquerda
        if self.posicao_horizontal <= -LARGURA_DE_CADA_LISTRA:  # Já andou uma listra inteira?
            self.posicao_horizontal += LARGURA_DE_CADA_LISTRA  # Volta uma listra para trás (o truque do chão infinito)
        self.rect.x = round(self.posicao_horizontal)  # Atualiza o retângulo (que só aceita números inteiros)
