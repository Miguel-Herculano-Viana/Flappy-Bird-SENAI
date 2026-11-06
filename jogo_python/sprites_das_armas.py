# SPRITES DAS ARMAS (pixel art escrita em código)
# Cada desenho é uma LISTA de textos: cada texto é uma linha de pixels e cada letra é uma cor da PALETA.
# O ponto "." é transparente. Mude uma letra e o desenho muda no jogo!

import pygame  # Biblioteca de jogos que estamos usando

PALETA = {
    "K": (24, 26, 40),  # Contorno
    "D": (72, 78, 100),  # Metal escuro
    "G": (140, 150, 175),  # Metal
    "W": (235, 240, 255),  # Brilho
    "C": (90, 230, 255),  # Azul do blaster e do laser
    "R": (220, 60, 60),  # Vermelho
    "O": (255, 150, 40),  # Laranja
    "Y": (255, 235, 120),  # Amarelo
}

DESENHOS = {
    # As armas (aparecem no pássaro e nas cartas)
    "blaster": [
        ".KKKKKKKKK.",
        "KGGWWWWGGCK",
        "KDDDDDDDDCK",
        ".KKKDDKKKK.",
        "...KDDK....",
        "...KKK.....",
    ],
    "laser": [
        "..KKKKKKKKK.",
        ".KGGGGGGGCCK",
        "KDDDDDDDDCWC",
        ".KGGGGGGGCCK",
        "..KKKKKKKKK.",
    ],
    "missil": [
        ".KKKKKKKKK.",
        "KDDDDDDDDDK",
        "KDROOOOOWDK",
        "KDDDDDDDDDK",
        "KDROOOOOWDK",
        "KDDDDDDDDDK",
        ".KKKKKKKKK.",
    ],
    "espalhado": [
        "..KKKKKKKKKK",
        ".KGGGGGGGGOK",
        "KDDDDDDDDDOK",
        "KDDKKKKKKKKK",
        "KKK.........",
    ],
    # Os tiros
    "tiro_do_blaster": [
        "..CCCC..",
        "CCWWWWWW",
        "..CCCC..",
    ],
    "bala_do_espalhado": [
        ".OO.",
        "OYYO",
        "OYYO",
        ".OO.",
    ],
}

sprites_ja_feitos = {}  # Dicionário: nome -> imagem (cada desenho é montado uma vez só)


def sprite(nome):
    if nome not in sprites_ja_feitos:
        linhas = DESENHOS[nome]
        imagem = pygame.Surface((len(linhas[0]), len(linhas)), pygame.SRCALPHA)  # Transparente
        for y, linha in enumerate(linhas):
            for x, letra in enumerate(linha):
                if letra != ".":
                    imagem.set_at((x, y), PALETA[letra])
        sprites_ja_feitos[nome] = imagem
    return sprites_ja_feitos[nome]


# SELF-CHECK: todo desenho é um retângulo e só usa letras da paleta
if __name__ == "__main__":
    for nome, linhas in DESENHOS.items():
        assert len({len(linha) for linha in linhas}) == 1, f"{nome}: linhas de tamanhos diferentes"
        assert set("".join(linhas)) <= set(PALETA) | {"."}, f"{nome}: letra fora da paleta"
    print("sprites_das_armas.py: tudo certo!")
