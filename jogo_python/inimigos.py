# INIMIGOS DO MODO NAVE
# CLASSE Inimigo: o "molde" de toda nave inimiga (vida, XP, animação, piscar ao levar tiro).
# Cada tipo de inimigo é uma classe FILHA que SOBRESCREVE "mover" e "atirar" (POLIMORFISMO).
# CLASSE Chefe: também é um Inimigo, mas tem fases: quanto menos vida, mais trincado o desenho e mais tiros.

import math  # Ferramenta do Python com contas (seno, ângulos)
import random  # Ferramenta do Python para sortear números

import pygame  # Biblioteca de jogos que estamos usando

from imagens import carregar_quadros, carregar_quadros_brancos  # Carrega os sprites do Modo Nave

QUADROS_POR_SEGUNDO_DA_ANIMACAO = 8  # Velocidade da animação das naves
SEGUNDOS_PISCANDO = 0.06  # Quanto tempo o inimigo fica branco depois de levar um tiro
VELOCIDADE_DOS_TIROS_INIMIGOS = 110  # Pixels por segundo


# Vetor de velocidade que vai de "origem" até "alvo".
def mirar(origem, alvo, velocidade):
    direcao = pygame.Vector2(alvo) - pygame.Vector2(origem)
    return direcao.normalize() * velocidade if direcao.length() > 0 else pygame.Vector2(-velocidade, 0)


# Atira "quantidade" balas em leque. "angulo_central" em graus (180 = para a esquerda).
def atirar_em_leque(tiros, origem, quantidade, abertura, angulo_central=180.0, velocidade=VELOCIDADE_DOS_TIROS_INIMIGOS):
    for numero in range(quantidade):
        angulo = angulo_central if quantidade == 1 else angulo_central - abertura / 2 + abertura * numero / (quantidade - 1)
        tiros.add(TiroInimigo(origem, pygame.Vector2(velocidade, 0).rotate(angulo)))  # ".rotate" gira o vetor


class TiroInimigo(pygame.sprite.Sprite):

    def __init__(self, posicao, velocidade):
        super().__init__()
        self.quadros = carregar_quadros("tiro_inimigo", 16)
        self.image = self.quadros[0]
        self.rect = self.image.get_rect(center=(round(posicao[0]), round(posicao[1])))
        self.posicao = pygame.Vector2(posicao)
        self.velocidade = pygame.Vector2(velocidade)
        self.dano = 1  # Quantos corações tira
        self.some_ao_acertar = True  # Um tiro comum some quando acerta o pássaro
        self.idade = 0.0

    def update(self, tempo, area_do_jogo):
        self.idade += tempo
        self.posicao += self.velocidade * tempo
        self.image = self.quadros[int(self.idade * 10) % len(self.quadros)]
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if not area_do_jogo.inflate(40, 40).colliderect(self.rect):  # Saiu da tela
            self.kill()


# EXPLOSÃO: só um efeito visual. Mostra os quadros uma vez e some.
class Explosao(pygame.sprite.Sprite):

    def __init__(self, posicao, nome, largura_do_quadro, tamanho=None, quadros_por_segundo=18):
        super().__init__()
        self.quadros = carregar_quadros(nome, largura_do_quadro)
        if tamanho:  # Explosão maior ou menor que o desenho original
            self.quadros = [pygame.transform.scale(quadro, (round(tamanho), round(tamanho))) for quadro in self.quadros]
        self.quadros_por_segundo = quadros_por_segundo
        self.idade = 0.0
        self.image = self.quadros[0]
        self.rect = self.image.get_rect(center=(round(posicao[0]), round(posicao[1])))

    def update(self, tempo, *argumentos_que_nao_uso):
        self.idade += tempo
        numero_do_quadro = int(self.idade * self.quadros_por_segundo)
        if numero_do_quadro >= len(self.quadros):  # Acabou a animação
            self.kill()
        else:
            self.image = self.quadros[numero_do_quadro]


# CORAÇÃO: às vezes um inimigo derrotado solta um. Pegar recupera 1 coração do pássaro.
class Coracao(pygame.sprite.Sprite):

    def __init__(self, posicao):
        super().__init__()
        self.quadros = carregar_quadros("coracao", 16)
        self.image = self.quadros[0]
        self.rect = self.image.get_rect(center=(round(posicao[0]), round(posicao[1])))
        self.posicao = pygame.Vector2(posicao)
        self.idade = 0.0

    def update(self, tempo, area_do_jogo):
        self.idade += tempo
        self.posicao.x -= 25 * tempo  # Vai ficando para trás, devagar
        self.image = self.quadros[int(self.idade * 4) % len(self.quadros)]
        self.rect.center = (round(self.posicao.x), round(self.posicao.y + 3 * math.sin(self.idade * 4)))
        if self.rect.right < 0:
            self.kill()


class Inimigo(pygame.sprite.Sprite):

    # CONSTRUTOR
    #   posicao            -> onde o inimigo nasce (normalmente logo depois da borda direita)
    #   nome_dos_quadros   -> arquivo dos sprites, e "largura_do_quadro" o tamanho de cada quadro
    #   vida, xp           -> quanto aguenta e quanto XP dá ao ser derrotado
    #   explosao           -> (nome do arquivo, largura do quadro) da explosão quando morre
    def __init__(self, posicao, nome_dos_quadros, largura_do_quadro, vida, xp, explosao):
        super().__init__()
        # ATRIBUTOS
        self.nome_dos_quadros = nome_dos_quadros
        self.largura_do_quadro = largura_do_quadro
        self.quadros = carregar_quadros(nome_dos_quadros, largura_do_quadro)
        self.quadros_brancos = carregar_quadros_brancos(nome_dos_quadros, largura_do_quadro)
        self.image = self.quadros[0]
        self.rect = self.image.get_rect(center=(round(posicao[0]), round(posicao[1])))
        self.posicao = pygame.Vector2(posicao)
        self.vida = vida
        self.vida_maxima = vida
        self.xp = xp
        self.explosao = explosao
        self.idade = 0.0  # Há quanto tempo o inimigo existe
        self.segundos_piscando = 0.0
        self.espera_do_tiro = random.uniform(0.5, 1.5)  # Cada um começa a atirar num momento diferente
        self.chance_de_coracao = 0.08  # 8% de chance de soltar um coração

    # MÉTODOS

    def levar_dano(self, dano):
        self.vida -= dano
        self.segundos_piscando = SEGUNDOS_PISCANDO

    def update(self, tempo, passaro, tiros_inimigos, area_do_jogo):
        self.idade += tempo
        self.segundos_piscando -= tempo
        self.mover(tempo, passaro, area_do_jogo)  # POLIMORFISMO: cada inimigo se move do seu jeito
        self.espera_do_tiro -= tempo
        if self.espera_do_tiro <= 0:
            self.espera_do_tiro = self.atirar(passaro, tiros_inimigos)  # Cada um atira do seu jeito e diz quando atira de novo
        quadros = self.quadros_brancos if self.segundos_piscando > 0 else self.quadros
        self.image = quadros[int(self.idade * QUADROS_POR_SEGUNDO_DA_ANIMACAO) % len(quadros)]
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        if self.rect.right < -20:  # Passou do pássaro e saiu pela esquerda: escapou
            self.kill()

    def mover(self, tempo, passaro, area_do_jogo):  # As filhas sobrescrevem
        self.posicao.x -= 50 * tempo

    def atirar(self, passaro, tiros_inimigos):  # As filhas sobrescrevem. Devolve os segundos até o próximo tiro
        return 999

    def ponto_de_tiro(self):  # De onde saem os tiros (o "nariz", do lado esquerdo)
        return (self.rect.left + 4, self.rect.centery)


# BATEDOR: pequeno e rápido, voa em onda. Não atira: o perigo é encostar.
class Batedor(Inimigo):

    def __init__(self, posicao, multiplicador_de_vida=1.0):
        super().__init__(posicao, "inimigo_pequeno", 16, 3 * multiplicador_de_vida, xp=1, explosao=("explosao_pequena", 16))
        self.altura_base = posicao[1]

    def mover(self, tempo, passaro, area_do_jogo):
        self.posicao.x -= 75 * tempo
        self.posicao.y = self.altura_base + 18 * math.sin(self.idade * 4)  # SENO: sobe e desce sem parar, como uma onda


# ATIRADOR: para no lado direito e atira mirando no pássaro.
class Atirador(Inimigo):

    def __init__(self, posicao, x_de_parada, multiplicador_de_vida=1.0):
        super().__init__(posicao, "inimigo_medio", 16, 8 * multiplicador_de_vida, xp=3, explosao=("explosao_media", 32))
        self.x_de_parada = x_de_parada
        self.altura_base = posicao[1]

    def mover(self, tempo, passaro, area_do_jogo):
        if self.posicao.x > self.x_de_parada:  # Chegando
            self.posicao.x -= 60 * tempo
        else:  # Parado, balançando um pouco; depois de um tempo vai embora
            self.posicao.y = self.altura_base + 10 * math.sin(self.idade * 2)
            if self.idade > 14:
                self.posicao.x -= 40 * tempo

    def atirar(self, passaro, tiros_inimigos):
        tiros_inimigos.add(TiroInimigo(self.ponto_de_tiro(), mirar(self.ponto_de_tiro(), passaro.rect.center, VELOCIDADE_DOS_TIROS_INIMIGOS)))
        return 2.4


# PERSEGUIDOR: pequeno e rápido, igual o Batedor, mas MIRA na altura do pássaro em vez de só ondular.
# Sprite: Kenney "Space Shooter Redux" (CC0), veja src/assets/nave/licencas.
class Perseguidor(Inimigo):

    def __init__(self, posicao, multiplicador_de_vida=1.0):
        super().__init__(posicao, "perseguidor", 16, 4 * multiplicador_de_vida, xp=2, explosao=("explosao_pequena", 16))

    def mover(self, tempo, passaro, area_do_jogo):
        self.posicao.x -= 95 * tempo  # Mais rápido que o Batedor
        self.posicao.y += (passaro.rect.centery - self.posicao.y) * min(1.0, 2.0 * tempo)  # Persegue a altura do pássaro


# METRALHADOR: para no lado direito, igual o Atirador, mas dispara RAJADAS rápidas em vez de um tiro de cada vez.
# Sprite: Kenney "Space Shooter Redux" (CC0), veja src/assets/nave/licencas.
class Metralhador(Inimigo):

    def __init__(self, posicao, x_de_parada, multiplicador_de_vida=1.0):
        super().__init__(posicao, "metralhador", 32, 10 * multiplicador_de_vida, xp=4, explosao=("explosao_media", 32))
        self.x_de_parada = x_de_parada
        self.altura_base = posicao[1]
        self.tiros_que_faltam_na_rajada = 0

    def mover(self, tempo, passaro, area_do_jogo):
        if self.posicao.x > self.x_de_parada:
            self.posicao.x -= 70 * tempo
        else:
            self.posicao.y = self.altura_base + 14 * math.sin(self.idade * 3)
            if self.idade > 12:
                self.posicao.x -= 40 * tempo

    def atirar(self, passaro, tiros_inimigos):
        direcao = mirar(self.ponto_de_tiro(), passaro.rect.center, VELOCIDADE_DOS_TIROS_INIMIGOS)
        tiros_inimigos.add(TiroInimigo(self.ponto_de_tiro(), direcao.rotate(random.uniform(-6, 6))))  # Mira com um pouco de erro
        if self.tiros_que_faltam_na_rajada <= 0:  # Começa (ou recomeça) uma rajada de 3 tiros
            self.tiros_que_faltam_na_rajada = 2
            return 1.6  # Pausa entre rajadas
        self.tiros_que_faltam_na_rajada -= 1
        return 0.22  # Tiros rápidos dentro da mesma rajada


# TANQUE: grande e lento, aguenta muito e atira em leque.
class Tanque(Inimigo):

    def __init__(self, posicao, multiplicador_de_vida=1.0):
        super().__init__(posicao, "inimigo_grande", 32, 25 * multiplicador_de_vida, xp=8, explosao=("explosao_media", 32))
        self.chance_de_coracao = 0.3

    def mover(self, tempo, passaro, area_do_jogo):
        self.posicao.x -= 22 * tempo

    def atirar(self, passaro, tiros_inimigos):
        atirar_em_leque(tiros_inimigos, self.ponto_de_tiro(), 5, 60, velocidade=90)
        return 3.2


# RAIO DO CHEFE FINAL: uma faixa que vai da boca do chefe até a borda esquerda. Não some ao acertar.
class RaioDoChefe(pygame.sprite.Sprite):

    def __init__(self, chefe, duracao):
        super().__init__()
        self.chefe = chefe
        self.duracao = duracao
        self.idade = 0.0
        self.dano = 1
        self.some_ao_acertar = False
        pedaco = carregar_quadros("raio_do_chefe", 49)[0]
        largura = max(pedaco.get_width(), chefe.rect.left + 10)
        self.image = pygame.Surface((largura, pedaco.get_height()), pygame.SRCALPHA)
        for esquerda in range(0, largura, pedaco.get_width()):  # O pedaço do raio repetido até cobrir a largura
            self.image.blit(pedaco, (esquerda, 0))
        self.rect = self.image.get_rect()

    def update(self, tempo, area_do_jogo):
        self.idade += tempo
        self.rect.midright = (self.chefe.rect.left + 12, self.chefe.rect.centery)  # Sai da boca do chefe
        if self.idade >= self.duracao or not self.chefe.alive():
            self.kill()


# CARGA DO RAIO: o aviso piscando antes do raio sair. Só visual (dano zero).
class CargaDoRaio(pygame.sprite.Sprite):

    def __init__(self, chefe, duracao):
        super().__init__()
        self.chefe = chefe
        self.duracao = duracao
        self.idade = 0.0
        self.dano = 0
        self.some_ao_acertar = False
        self.quadros = carregar_quadros("carga_do_raio", 74)
        self.image = self.quadros[0]
        self.rect = self.image.get_rect()

    def update(self, tempo, area_do_jogo):
        self.idade += tempo
        self.image = self.quadros[int(self.idade * 12) % len(self.quadros)]
        self.rect = self.image.get_rect(midright=(self.chefe.rect.left + 12, self.chefe.rect.centery))
        if self.idade >= self.duracao or not self.chefe.alive():
            self.kill()


class Chefe(Inimigo):

    # "nome_base" é o começo do nome dos arquivos (ex.: "chefe_verde" -> chefe_verde_1, _2 e _3, um por fase).
    def __init__(self, posicao, nome, nome_base, largura_do_quadro, vida, xp, x_de_parada):
        super().__init__(posicao, f"{nome_base}_1", largura_do_quadro, vida, xp, explosao=("explosao_grande", 80))
        self.nome = nome  # Aparece na barra de vida
        self.nome_base = nome_base
        self.x_de_parada = x_de_parada
        self.altura_base = posicao[1]
        self.fase = 1
        self.chegou = False  # Enquanto entra na tela, não leva dano
        self.chance_de_coracao = 1.0  # Chefe sempre solta um coração

    # SOBRESCRITA: só leva dano depois de chegar.
    def levar_dano(self, dano):
        if self.chegou:
            super().levar_dano(dano)

    def update(self, tempo, passaro, tiros_inimigos, area_do_jogo):
        fase_pela_vida = 1 if self.vida > self.vida_maxima * 2 / 3 else 2 if self.vida > self.vida_maxima / 3 else 3
        if fase_pela_vida != self.fase:  # Mudou de fase: troca o desenho para o mais trincado
            self.fase = fase_pela_vida
            self.quadros = carregar_quadros(f"{self.nome_base}_{self.fase}", self.largura_do_quadro)
            self.quadros_brancos = carregar_quadros_brancos(f"{self.nome_base}_{self.fase}", self.largura_do_quadro)
        super().update(tempo, passaro, tiros_inimigos, area_do_jogo)

    def mover(self, tempo, passaro, area_do_jogo):
        if self.posicao.x > self.x_de_parada:  # Entrando (rápido, porque ele vem de trás do painel)
            self.posicao.x -= 90 * tempo
        else:
            self.chegou = True
            amplitude = area_do_jogo.height / 2 - self.rect.height / 2 - 12  # Sobe e desce por quase toda a altura do céu
            self.posicao.y = area_do_jogo.centery + amplitude * math.sin(self.idade * (0.5 + 0.15 * self.fase))

    def atirar(self, passaro, tiros_inimigos):
        if not self.chegou:
            return 0.5
        return self.padrao_de_tiro(passaro, tiros_inimigos)

    def padrao_de_tiro(self, passaro, tiros_inimigos):  # Cada chefe SOBRESCREVE
        return 1.0


class ChefeVerde(Chefe):

    def __init__(self, posicao, x_de_parada):
        super().__init__(posicao, "CHEFE VERDE", "chefe_verde", 96, vida=250, xp=30, x_de_parada=x_de_parada)

    def padrao_de_tiro(self, passaro, tiros_inimigos):
        mira = mirar(self.ponto_de_tiro(), passaro.rect.center, 1)  # Só a direção
        angulo = math.degrees(math.atan2(mira.y, mira.x))
        atirar_em_leque(tiros_inimigos, self.ponto_de_tiro(), 3, 16, angulo, 120)  # Rajada mirada de 3
        if self.fase >= 2:
            atirar_em_leque(tiros_inimigos, self.ponto_de_tiro(), 5, 80, 180, 80)  # Mais um leque largo e lento
        return 1.6 if self.fase == 1 else 1.3 if self.fase == 2 else 0.9


class ChefeVermelho(Chefe):

    def __init__(self, posicao, x_de_parada):
        super().__init__(posicao, "CHEFE VERMELHO", "chefe_vermelho", 96, vida=450, xp=50, x_de_parada=x_de_parada)
        self.giro = 0.0

    def padrao_de_tiro(self, passaro, tiros_inimigos):
        self.giro += 17  # Cada anel sai um pouco girado: forma uma espiral
        atirar_em_leque(tiros_inimigos, self.rect.center, 10 + 2 * self.fase, 360 - 360 / (10 + 2 * self.fase), self.giro, 85)  # Anel em volta
        if self.fase >= 2:
            tiros_inimigos.add(TiroInimigo(self.ponto_de_tiro(), mirar(self.ponto_de_tiro(), passaro.rect.center, 140)))
        return 1.9 if self.fase == 1 else 1.5 if self.fase == 2 else 1.1


# CHEFE FINAL: a nave que explodiu os canos no começo. Ela volta do fundo do céu crescendo.
class ChefeAmarelo(Chefe):

    def __init__(self, posicao, x_de_parada, posicao_no_fundo):
        super().__init__(posicao, "NAVE-MÃE", "chefe_amarelo", 128, vida=800, xp=100, x_de_parada=x_de_parada)
        self.posicao_no_fundo = pygame.Vector2(posicao_no_fundo)
        self.posicao_de_chegada = pygame.Vector2(x_de_parada, posicao[1])
        self.posicao = pygame.Vector2(posicao_no_fundo)
        self.segundos_ate_o_raio = 6.0
        self.duracao_da_chegada = 2.5
        self.raio_pendente = False  # True entre a carga (o aviso) e o raio de verdade

    def update(self, tempo, passaro, tiros_inimigos, area_do_jogo):
        super().update(tempo, passaro, tiros_inimigos, area_do_jogo)
        if not self.chegou:  # Chegando do fundo: começa pequena e cresce
            progresso = min(1.0, self.idade / self.duracao_da_chegada)
            escala = 0.25 + 0.75 * progresso
            self.image = pygame.transform.scale_by(self.image, escala)
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def mover(self, tempo, passaro, area_do_jogo):
        if not self.chegou:
            progresso = min(1.0, self.idade / self.duracao_da_chegada)
            self.posicao = self.posicao_no_fundo.lerp(self.posicao_de_chegada, progresso)  # "lerp": um ponto entre os dois
            if progresso >= 1:
                self.chegou = True
                self.idade = 0.0
        else:
            super().mover(tempo, passaro, area_do_jogo)

    def padrao_de_tiro(self, passaro, tiros_inimigos):
        if self.fase >= 2:  # A partir da fase 2: o raio gigante, com aviso antes
            self.segundos_ate_o_raio -= 1
            if self.segundos_ate_o_raio <= 0:
                self.segundos_ate_o_raio = 6 if self.fase == 2 else 4
                tiros_inimigos.add(CargaDoRaio(self, 1.2))
                self.raio_pendente = True
                return 1.2
        if self.raio_pendente:  # Acabou a carga: solta o raio
            self.raio_pendente = False
            tiros_inimigos.add(RaioDoChefe(self, 1.2))
            return 1.4
        atirar_em_leque(tiros_inimigos, self.ponto_de_tiro(), 7, 90, 180, 95)  # Leque de 7
        if self.fase == 3:
            tiros_inimigos.add(TiroInimigo(self.ponto_de_tiro(), mirar(self.ponto_de_tiro(), passaro.rect.center, 150)))
        return 1.0
