# CARREGAR IMAGENS DO MODO NAVE
# Cada arquivo em src/assets/nave é uma FAIXA: vários quadros do mesmo tamanho, lado a lado.
# As imagens ficam guardadas num dicionário depois da primeira vez, para não ler o disco a cada inimigo novo.

from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

PASTA_DAS_IMAGENS = Path(__file__).parent.parent / "src" / "assets" / "nave"  # Onde estão os sprites do Modo Nave
imagens_ja_carregadas = {}  # Dicionário: (nome, largura do quadro, branco?) -> lista de quadros


# Devolve a lista de quadros da faixa "nome.png", cortando a cada "largura_do_quadro" pixels.
def carregar_quadros(nome, largura_do_quadro):
    chave = (nome, largura_do_quadro, False)
    if chave not in imagens_ja_carregadas:  # Primeira vez: lê o arquivo e corta
        faixa = pygame.image.load(PASTA_DAS_IMAGENS / f"{nome}.png").convert_alpha()
        imagens_ja_carregadas[chave] = [
            faixa.subsurface((esquerda, 0, largura_do_quadro, faixa.get_height()))  # Recorta um quadro
            for esquerda in range(0, faixa.get_width(), largura_do_quadro)  # Um a cada "largura_do_quadro" pixels
        ]
    return imagens_ja_carregadas[chave]


# Os mesmos quadros, só que todos brancos (usados para o inimigo "piscar" quando leva um tiro).
def carregar_quadros_brancos(nome, largura_do_quadro):
    chave = (nome, largura_do_quadro, True)
    if chave not in imagens_ja_carregadas:
        imagens_ja_carregadas[chave] = [
            pygame.mask.from_surface(quadro).to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))  # Silhueta branca
            for quadro in carregar_quadros(nome, largura_do_quadro)
        ]
    return imagens_ja_carregadas[chave]
