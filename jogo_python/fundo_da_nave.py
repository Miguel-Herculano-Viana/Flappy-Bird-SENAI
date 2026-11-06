# FUNDO DO MODO NAVE: um céu noturno em CAMADAS (paralaxe).
# Cada camada anda numa velocidade: o que está longe anda devagar e o que está perto anda rápido.
# É isso que dá a sensação de profundidade (olhe pela janela de um carro: a montanha quase não se mexe, o poste passa voando).
#   céu (degradê, parado) -> estrelas (duas camadas, piscando) -> planeta -> nebulosa -> cidade longe -> cidade perto

import math  # Ferramenta do Python com contas (seno)
import random  # Ferramenta do Python para sortear números

import pygame  # Biblioteca de jogos que estamos usando

COR_DO_TOPO = (8, 10, 34)  # Azul quase preto
COR_DO_HORIZONTE = (64, 34, 92)  # Roxo
CORES_DA_NEBULOSA = ((150, 60, 200), (40, 140, 200), (200, 70, 130))
COR_DA_CIDADE_LONGE = (40, 30, 78)  # Prédios do fundo: mais escuros e baixos
COR_DA_CIDADE_PERTO = (22, 18, 46)  # Prédios da frente: quase pretos e altos
CORES_DAS_JANELAS = ((255, 220, 120), (255, 190, 90), (150, 230, 255))  # Janelas acesas (claras o bastante para o bloom)
LARGURA_DO_PEDACO_DA_CIDADE = 160  # A cidade é um pedaço desta largura que se repete
QUANTAS_ESTRELAS = 110
VELOCIDADE_DAS_CAMADAS = {"estrelas_longe": 0.08, "estrelas_perto": 0.25, "planeta": 0.04, "nebulosa": 0.4,
                          "cidade_longe": 0.6, "cidade_perto": 1.2}  # Multiplica a velocidade do fundo


class FundoDaNave:

    def __init__(self, area_do_ceu):
        self.largura, self.altura = area_do_ceu.size
        self.deslocamento = 0.0  # Quantos pixels o fundo já andou
        self.tempo = 0.0
        self.ceu = criar_degrade(area_do_ceu.size)
        sorteio = random.Random(7)  # Sempre o mesmo céu (o 7 é a "semente" do sorteio)
        self.estrelas = [(sorteio.uniform(0, self.largura), sorteio.uniform(0, self.altura * 0.8), sorteio.choice(("estrelas_longe", "estrelas_perto")),
                          sorteio.uniform(0, 6.3), sorteio.choice((1, 1, 1, 2))) for _ in range(QUANTAS_ESTRELAS)]  # (x, y, camada, fase do pisca, tamanho)
        self.planeta = criar_planeta(22)
        self.nebulosa = criar_nebulosa(self.largura, self.altura, sorteio)
        self.cidades = {"cidade_longe": criar_cidade(self.largura, sorteio, COR_DA_CIDADE_LONGE, 56, 0.25),
                        "cidade_perto": criar_cidade(self.largura, sorteio, COR_DA_CIDADE_PERTO, 34, 0.12)}

    def atualizar(self, tempo, velocidade):
        self.tempo += tempo
        self.deslocamento += velocidade * tempo

    def posicao_da_camada(self, camada, tamanho):  # Quanto a camada andou, dando a volta a cada "tamanho" pixels
        return (self.deslocamento * VELOCIDADE_DAS_CAMADAS[camada]) % tamanho

    def desenhar(self, tela):
        tela.blit(self.ceu, (0, 0))
        for x, y, camada, fase, tamanho in self.estrelas:
            brilho = 150 + 105 * math.sin(self.tempo * 2 + fase)  # SENO: pisca devagar
            cor = (brilho, brilho, min(255, brilho + 30)) if camada == "estrelas_perto" else (brilho * 0.6,) * 3
            tela.fill(cor, ((x - self.posicao_da_camada(camada, self.largura)) % self.largura, y, tamanho, tamanho))
        x_do_planeta = self.largura * 0.75 - self.posicao_da_camada("planeta", self.largura + 60)
        tela.blit(self.planeta, (x_do_planeta % (self.largura + 60) - 50, self.altura * 0.18))
        x = -self.posicao_da_camada("nebulosa", self.largura)
        tela.blit(self.nebulosa, (x, 0))  # Duas cópias lado a lado: quando uma sai pela esquerda, a outra já está entrando
        tela.blit(self.nebulosa, (x + self.largura, 0))
        for camada, cidade in self.cidades.items():  # Primeiro a de longe, depois a de perto (por cima)
            x = -self.posicao_da_camada(camada, LARGURA_DO_PEDACO_DA_CIDADE)  # Volta a cada pedaço: a emenda não aparece
            tela.blit(cidade, (x, self.altura - cidade.get_height()))


def criar_degrade(tamanho):
    largura, altura = tamanho
    imagem = pygame.Surface(tamanho)
    for y in range(altura):  # Uma linha de cada cor, misturando o topo com o horizonte
        mistura = y / max(1, altura - 1)
        imagem.fill([round(a + (b - a) * mistura) for a, b in zip(COR_DO_TOPO, COR_DO_HORIZONTE)], (0, y, largura, 1))
    return imagem


def criar_planeta(raio):
    imagem = pygame.Surface((raio * 2 + 8, raio * 2 + 8), pygame.SRCALPHA)
    centro = (raio + 4, raio + 4)
    pygame.draw.circle(imagem, (120, 90, 200, 40), centro, raio + 4)  # Atmosfera
    pygame.draw.circle(imagem, (90, 70, 160), centro, raio)
    pygame.draw.circle(imagem, (150, 120, 220), (centro[0] - 5, centro[1] - 5), raio - 6)  # Lado iluminado
    pygame.draw.circle(imagem, (90, 70, 160), (centro[0] + 4, centro[1] + 4), raio - 6)  # Sombra
    pygame.draw.ellipse(imagem, (200, 180, 255), (2, centro[1] - 2, raio * 2 + 4, 5), 1)  # Anel
    return imagem


# Nuvens de cor feitas com muitos círculos quase transparentes. Os que passam da borda são desenhados também do outro lado,
# para a imagem "emendar" quando repete.
def criar_nebulosa(largura, altura, sorteio):
    imagem = pygame.Surface((largura, altura), pygame.SRCALPHA)
    for _ in range(14):
        cor = sorteio.choice(CORES_DA_NEBULOSA)
        cx, cy = sorteio.uniform(0, largura), sorteio.uniform(altura * 0.1, altura * 0.7)
        for _ in range(10):
            raio = sorteio.uniform(10, 34)
            x, y = cx + sorteio.uniform(-30, 30), cy + sorteio.uniform(-12, 12)
            bolha = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(bolha, (*cor, 10), (raio, raio), raio)
            for deslocamento in (-largura, 0, largura):
                imagem.blit(bolha, (x - raio + deslocamento, y - raio))
    return imagem


# Um pedaço de cidade: prédios sorteados com janelas acesas. Depois ele é repetido na largura (com um pedaço a mais para rolar).
def criar_cidade(largura, sorteio, cor, altura_maxima, chance_de_janela):
    pedaco = pygame.Surface((LARGURA_DO_PEDACO_DA_CIDADE, altura_maxima), pygame.SRCALPHA)
    x = 0
    while x < LARGURA_DO_PEDACO_DA_CIDADE:
        largura_do_predio = min(sorteio.randint(8, 18), LARGURA_DO_PEDACO_DA_CIDADE - x)
        altura = sorteio.randint(altura_maxima // 3, altura_maxima)
        pedaco.fill(cor, (x, altura_maxima - altura, largura_do_predio, altura))
        for janela_y in range(altura_maxima - altura + 3, altura_maxima - 2, 4):  # Janelas a cada 4 pixels
            for janela_x in range(x + 2, x + largura_do_predio - 2, 3):
                if sorteio.random() < chance_de_janela:
                    pedaco.fill(sorteio.choice(CORES_DAS_JANELAS), (janela_x, janela_y, 1, 2))
        x += largura_do_predio + sorteio.randint(0, 3)  # Às vezes um espacinho entre os prédios
    vezes = -(-largura // LARGURA_DO_PEDACO_DA_CIDADE) + 1  # Arredonda para cima, e mais um
    cidade = pygame.Surface((vezes * LARGURA_DO_PEDACO_DA_CIDADE, altura_maxima), pygame.SRCALPHA)
    for numero in range(vezes):
        cidade.blit(pedaco, (numero * LARGURA_DO_PEDACO_DA_CIDADE, 0))
    return cidade
