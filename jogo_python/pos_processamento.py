# PÓS-PROCESSAMENTO: efeitos aplicados na imagem PRONTA, depois que tudo foi desenhado.
#   BLOOM   -> o que é muito claro (tiros, laser, explosões, estrelas) ganha um brilho que "vaza" em volta.
#              Como funciona: 1) fica só com a parte clara (tira um pouco de cada cor), 2) diminui a imagem
#              e aumenta de novo (isso BORRA), 3) SOMA o borrão por cima da imagem original.
#   VINHETA -> as bordas da tela ficam mais escuras, puxando o olho para o meio.

import numpy  # Contas com muitos números de uma vez (usado para montar a vinheta, uma vez só)
import pygame  # Biblioteca de jogos que estamos usando

LIMIAR_DO_BLOOM = 150  # Só brilha o que passar disto (0 a 255). Menor = mais coisas brilham
FORCA_DO_BLOOM = 200  # Quanto do brilho é somado (0 a 255)
ESCURIDAO_DA_VINHETA = 140  # Quão escuros ficam os cantos (0 a 255)
COMECO_DA_VINHETA = 0.55  # A partir de que distância do meio (0 = meio, 1 = canto) começa a escurecer


class PosProcessamento:

    def __init__(self, tamanho_do_jogo, tamanho_do_monitor):
        largura, altura = tamanho_do_jogo
        self.tamanho_do_jogo = tamanho_do_jogo
        self.borroes = [(max(1, largura // 4), max(1, altura // 4)), (max(1, largura // 8), max(1, altura // 8))]  # Um brilho perto e um mais espalhado
        self.vinheta = criar_vinheta(tamanho_do_monitor)

    # Aplica o bloom na tela pequena do jogo (antes de ampliar: o brilho fica com cara de pixel art).
    def bloom(self, tela):
        claro = tela.copy()
        claro.fill((LIMIAR_DO_BLOOM,) * 3, special_flags=pygame.BLEND_RGB_SUB)  # Tira o limiar: o que era escuro vira preto
        claro.fill((FORCA_DO_BLOOM,) * 3, special_flags=pygame.BLEND_RGB_MULT)  # Ajusta a força
        pequeno = claro
        for tamanho in self.borroes:  # Cada vez menor = mais borrado
            pequeno = pygame.transform.smoothscale(pequeno, tamanho)
            tela.blit(pygame.transform.smoothscale(pequeno, self.tamanho_do_jogo), (0, 0), special_flags=pygame.BLEND_RGB_ADD)  # SOMA a luz

    def aplicar_vinheta(self, monitor):
        monitor.blit(self.vinheta, (0, 0))


# Uma imagem preta com transparência que aumenta do meio para as bordas (em forma de elipse).
def criar_vinheta(tamanho):
    largura, altura = tamanho
    x = numpy.linspace(-1, 1, largura)[:, None]  # -1 na borda esquerda, 1 na direita
    y = numpy.linspace(-1, 1, altura)[None, :]
    distancia = numpy.sqrt(x ** 2 + y ** 2) / numpy.sqrt(2)  # 0 no meio, 1 no canto
    forca = numpy.clip((distancia - COMECO_DA_VINHETA) / (1 - COMECO_DA_VINHETA), 0, 1) ** 2  # Suave no começo
    vinheta = pygame.Surface(tamanho, pygame.SRCALPHA)
    vinheta.fill((0, 0, 0, 255))
    pygame.surfarray.pixels_alpha(vinheta)[:] = (forca * ESCURIDAO_DA_VINHETA).astype(numpy.uint8)
    return vinheta
