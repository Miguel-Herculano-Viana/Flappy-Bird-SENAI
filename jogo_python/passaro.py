# CLASSE PASSARO
# Uma classe é um "molde". Com ela criamos objetos: cada pássaro criado é um objeto desta classe.

from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

CAMINHO_DA_IMAGEM_DO_PASSARO = Path(__file__).parent.parent / "src" / "assets" / "Bird_1.png"  # Onde está o desenho do pássaro
TAMANHO_DE_CADA_QUADRO = 32  # O desenho tem vários quadros lado a lado, cada um com 32x32 pixels
MILISSEGUNDOS_POR_QUADRO_DA_ANIMACAO = 100  # Tempo que cada quadro fica na tela (100 ms = 10 quadros por segundo)
GRAUS_DE_INCLINACAO_POR_VELOCIDADE = 0.3  # Quanto o pássaro inclina para cada pixel por segundo de velocidade
INCLINACAO_MAXIMA_PARA_CIMA = 25  # Subindo, o bico aponta no máximo 25 graus para cima
INCLINACAO_MAXIMA_PARA_BAIXO = -70  # Caindo, o bico aponta no máximo 70 graus para baixo


# "(pygame.sprite.Sprite)" = HERANÇA: o Passaro herda tudo que um Sprite do pygame já sabe fazer
# (ser desenhado na tela e ser atualizado por um grupo) e nós só adicionamos o que é dele.
class Passaro(pygame.sprite.Sprite):

    # CONSTRUTOR: roda automaticamente quando um novo pássaro é criado. Ex.: Passaro((48, 128))
    # "self" é o próprio objeto: "self.algo" é um atributo que pertence a ESTE pássaro.
    def __init__(self, posicao_inicial):
        super().__init__()  # Chama o construtor da classe mãe (Sprite) para ela se preparar também

        # ATRIBUTOS: características do pássaro
        self.forca_da_gravidade = 500.0  # Quanto a gravidade puxa o pássaro para baixo (pixels por segundo²)
        self.forca_do_pulo = 160.0  # Velocidade para cima que o pássaro ganha a cada pulo (pixels por segundo)
        self.velocidade_maxima_de_queda = 250.0  # Limite de velocidade caindo, para a queda não ficar rápida demais
        self.velocidade_vertical = 0.0  # Velocidade atual: negativa = subindo, positiva = caindo
        self.posicao_vertical = float(posicao_inicial[1])  # Altura do pássaro com casas decimais, para o movimento ficar suave

        imagem_com_todos_os_quadros = pygame.image.load(CAMINHO_DA_IMAGEM_DO_PASSARO).convert_alpha()  # Carrega o desenho (com transparência)
        quantidade_de_quadros = imagem_com_todos_os_quadros.get_width() // TAMANHO_DE_CADA_QUADRO  # Quantos quadros cabem na largura (160 / 32 = 5)
        self.quadros_da_animacao = [  # Lista com cada quadro recortado da imagem
            imagem_com_todos_os_quadros.subsurface((numero_do_quadro * TAMANHO_DE_CADA_QUADRO, 0, TAMANHO_DE_CADA_QUADRO, TAMANHO_DE_CADA_QUADRO))  # Recorta um quadro
            for numero_do_quadro in range(quantidade_de_quadros)  # Repete para cada quadro
        ]

        # "image" e "rect" precisam ter exatamente esses nomes: é assim que o Sprite (classe mãe) sabe o que desenhar e onde
        self.image = self.quadros_da_animacao[0]  # Imagem que aparece na tela agora
        self.rect = self.image.get_rect(center=posicao_inicial)  # Retângulo com a posição e o tamanho do pássaro

    # MÉTODOS: ações que o pássaro sabe fazer

    def pular(self):
        self.velocidade_vertical = -self.forca_do_pulo  # Valor negativo = para CIMA (no pygame, Y cresce para baixo)

    def aplicar_gravidade(self, tempo_do_quadro):
        self.velocidade_vertical += self.forca_da_gravidade * tempo_do_quadro  # A cada quadro, cai um pouco mais rápido
        self.velocidade_vertical = min(self.velocidade_vertical, self.velocidade_maxima_de_queda)  # Mas nunca mais rápido que o limite
        self.posicao_vertical += self.velocidade_vertical * tempo_do_quadro  # Move o pássaro de acordo com a velocidade
        self.rect.centery = round(self.posicao_vertical)  # Atualiza o retângulo (que só aceita números inteiros)

    def animar(self):
        numero_do_quadro_atual = pygame.time.get_ticks() // MILISSEGUNDOS_POR_QUADRO_DA_ANIMACAO % len(self.quadros_da_animacao)  # Escolhe o quadro pelo tempo que passou
        self.image = self.quadros_da_animacao[numero_do_quadro_atual]  # Troca a imagem mostrada, dando a ilusão de bater as asas

    # Gira o desenho: subindo, o bico aponta para cima; caindo, aponta para baixo.
    def inclinar(self):
        inclinacao = -self.velocidade_vertical * GRAUS_DE_INCLINACAO_POR_VELOCIDADE  # Quanto mais rápido cai, mais inclina para baixo
        inclinacao = max(INCLINACAO_MAXIMA_PARA_BAIXO, min(inclinacao, INCLINACAO_MAXIMA_PARA_CIMA))  # Prende entre os dois limites
        self.image = pygame.transform.rotate(self.image, inclinacao)  # Gira a imagem (graus positivos = sentido anti-horário = bico para cima)
        self.rect = self.image.get_rect(center=self.rect.center)  # A imagem girada muda de tamanho; recentraliza no mesmo lugar

    # "update" é um método que já existe na classe mãe (Sprite). Aqui nós o SOBRESCREVEMOS:
    # trocamos o comportamento dele pelo do pássaro. O grupo chama "update" de todos os seus objetos.
    def update(self, tempo_do_quadro):
        self.aplicar_gravidade(tempo_do_quadro)  # Primeiro a física
        self.animar()  # Depois escolhe o quadro da animação
        self.inclinar()  # E por último gira esse quadro conforme a velocidade
