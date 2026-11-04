# CLASSE CANO
# Cada cano na tela é um OBJETO desta classe. O par de canos (cima e baixo) são dois objetos
# criados com o MESMO molde, só que com atributos diferentes.

from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

CAMINHO_DA_IMAGEM_DO_CANO = Path(__file__).parent.parent / "src" / "assets" / "cano.png"  # Desenho do cano (32x256, com a "tampa" em cima)
VELOCIDADE_DO_CENARIO = 60.0  # Quantos pixels por segundo os canos (e o chão) andam para a esquerda


# HERANÇA: assim como o Passaro, o Cano também "é um" Sprite do pygame.
class Cano(pygame.sprite.Sprite):

    # CONSTRUTOR: "borda_da_abertura" é a altura onde o cano termina e começa o espaço para o pássaro passar.
    # "fica_em_cima" diz se este é o cano de cima (True) ou o de baixo (False).
    def __init__(self, posicao_horizontal, borda_da_abertura, fica_em_cima):
        super().__init__()  # Chama o construtor da classe mãe (Sprite)

        # ATRIBUTOS
        self.velocidade_horizontal = VELOCIDADE_DO_CENARIO  # Quantos pixels por segundo o cano anda para a esquerda
        self.posicao_horizontal = float(posicao_horizontal)  # Posição com casas decimais, para o movimento ficar suave
        self.vale_ponto = fica_em_cima  # Só o cano de cima vale ponto, assim cada PAR de canos conta 1 ponto só

        self.image = pygame.image.load(CAMINHO_DA_IMAGEM_DO_CANO).convert_alpha()  # Carrega o desenho (com transparência)
        if fica_em_cima:  # Cano de cima: pendurado, termina na borda da abertura
            self.image = pygame.transform.flip(self.image, False, True)  # Vira de cabeça para baixo, para a tampa ficar virada para a abertura
            self.rect = self.image.get_rect(bottomleft=(posicao_horizontal, borda_da_abertura))  # A parte de BAIXO dele fica na borda
        else:  # Cano de baixo: começa na borda da abertura e vai até o chão
            self.rect = self.image.get_rect(topleft=(posicao_horizontal, borda_da_abertura))  # A parte de CIMA dele fica na borda

    # SOBRESCRITA: o Passaro e o Cano têm um "update", mas cada um faz uma coisa diferente.
    # O grupo chama "update" de todos sem saber quem é quem. Isso se chama POLIMORFISMO.
    def update(self, tempo_do_quadro):
        self.posicao_horizontal -= self.velocidade_horizontal * tempo_do_quadro  # Anda para a esquerda
        self.rect.x = round(self.posicao_horizontal)  # Atualiza o retângulo (que só aceita números inteiros)
        if self.rect.right < 0:  # Se o cano saiu inteiro pela esquerda da tela...
            self.kill()  # ...remove ele de todos os grupos. "kill" é um método HERDADO do Sprite
