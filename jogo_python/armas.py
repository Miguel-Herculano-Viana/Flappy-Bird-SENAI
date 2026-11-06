# ARMAS DO MODO NAVE
# Cada arma é uma classe FILHA de Arma (HERANÇA). Todas têm DOIS parâmetros que o visitante escolhe no script,
# cada um com uma faixa própria, e um LIMITE COMPARTILHADO: o produto dos dois não pode passar do limite.
# Exemplo: no laser, quantidade x grossura <= 6. Mais raios = raios mais finos.
# Cada arma atira do seu jeito: o método "atirar" é SOBRESCRITO em cada filha (POLIMORFISMO).

import math  # Ferramenta do Python com contas (ângulos, raiz quadrada)
import random  # Ferramenta do Python para sortear números

import pygame  # Biblioteca de jogos que estamos usando

from imagens import carregar_quadros  # Carrega os sprites do Modo Nave
from inimigos import Explosao  # A explosão do míssil
from sprites_das_armas import sprite  # Pixel art das armas e dos tiros

VELOCIDADE_DO_TIRO = 320  # Pixels por segundo dos tiros do pássaro
VELOCIDADE_DO_MISSIL = 150  # Os mísseis são mais lentos, mas fazem curva
CURVA_DE_QUEM_SEGUE = 4.0  # Quão rápido o míssil (e o tiro com tiro.seguir()) vira na direção do alvo
FRACAO_DO_DANO_DA_COPIA = 0.5  # Os tiros criados por dividir e multiplicar têm metade do dano
DANO_DO_MISSIL = 4  # Dano no inimigo atingido em cheio
DANO_DA_EXPLOSAO_DO_MISSIL = 5  # Dano em todos que estiverem dentro do raio da explosão
DANO_DO_LASER_POR_SEGUNDO = 10  # Por pixel de grossura, enquanto o raio encosta no inimigo
DURACAO_DO_LASER = 0.3  # Quanto tempo cada pulso de laser fica aceso
DANO_DO_ESPALHADO = 2  # Dano de cada bala do espalhado
ABERTURA_DO_ESPALHADO = 50  # Ângulo total do leque, em graus
COR_DO_LASER = (90, 230, 255)  # Azul claro
COR_DO_MIOLO_DO_LASER = (240, 255, 255)  # Quase branco


# CLASSE PROJÉTIL: um tiro do pássaro. Anda em linha reta, tira vida do primeiro inimigo que encostar e some.
# Os PODERES (poderes.py) mudam os atributos dele: quiques_restantes, seguindo, e criam cópias com "copiar".
class Projetil(pygame.sprite.Sprite):

    def __init__(self, imagem, x, y, velocidade_x, velocidade_y, dano, alcance=None):
        super().__init__()
        self.imagem_original = imagem
        self.image = imagem
        self.rect = imagem.get_rect(center=(round(x), round(y)))
        self.posicao = pygame.Vector2(x, y)  # VETOR: guarda x e y juntos, com casas decimais
        self.velocidade = pygame.Vector2(velocidade_x, velocidade_y)
        self.rapidez = self.velocidade.length()  # O tamanho da velocidade (não muda quando o tiro faz curva)
        self.dano = dano
        self.alcance = alcance  # Distância máxima (None = até sair da tela)
        self.distancia_percorrida = 0.0
        # Atributos dos poderes
        self.numero = 0  # Qual tiro da arma é este (1, 2, 3...): o tiro.numero do script
        self.quiques = 0  # Quantas vezes já quicou
        self.quiques_restantes = 0  # Quantas vezes ainda vai quicar
        self.seguindo = False  # True = faz curva atrás do inimigo mais perto
        self.inimigos = None  # O grupo de inimigos (para seguir e quicar)
        self.ignorar = None  # O inimigo que acabou de acertar (para não acertar de novo logo em seguida)
        self.geracao = 0  # 0 = saiu da arma; 1 = cópia; 2 = cópia da cópia
        self.na_parede = False

    def update(self, tempo, area_do_jogo):
        if self.seguindo and self.inimigos:  # Procura o inimigo mais perto e vira um pouco na direção dele
            alvo = min(self.inimigos, key=lambda inimigo: self.posicao.distance_to(inimigo.rect.center), default=None)
            ate_o_alvo = pygame.Vector2(alvo.rect.center) - self.posicao if alvo else pygame.Vector2()
            if ate_o_alvo.length() > 0:  # (um vetor de tamanho zero não tem direção)
                direcao_desejada = ate_o_alvo.normalize() * self.rapidez  # Para onde ele quer ir
                self.velocidade += (direcao_desejada - self.velocidade) * min(1.0, CURVA_DE_QUEM_SEGUE * tempo)  # Vira aos poucos
        angulo = math.degrees(math.atan2(-self.velocidade.y, self.velocidade.x))  # Ângulo da velocidade (em graus)
        self.image = pygame.transform.rotate(self.imagem_original, angulo) if angulo else self.imagem_original  # O desenho aponta para onde o tiro vai
        passo = self.velocidade * tempo  # Quanto anda neste quadro
        self.posicao += passo
        self.distancia_percorrida += passo.length()  # ".length()" é o tamanho do vetor (o teorema de Pitágoras)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if self.alcance and self.distancia_percorrida > self.alcance:  # Passou do alcance
            self.kill()
        self.na_parede = not area_do_jogo.collidepoint(self.posicao)  # Bateu na borda: o ModoNave roda o evento "parede" e decide se some ou quica

    # Volta para dentro da tela e espelha a velocidade (as cópias criadas na parede já saem para dentro).
    def bater_na_parede(self, area_do_jogo):
        if not area_do_jogo.left <= self.posicao.x <= area_do_jogo.right:
            self.velocidade.x = -self.velocidade.x
        if not area_do_jogo.top <= self.posicao.y <= area_do_jogo.bottom:
            self.velocidade.y = -self.velocidade.y
        self.posicao.x = max(area_do_jogo.left, min(self.posicao.x, area_do_jogo.right))
        self.posicao.y = max(area_do_jogo.top, min(self.posicao.y, area_do_jogo.bottom))
        self.ignorar = None  # Depois da parede, pode acertar o mesmo inimigo de novo

    def depois_da_parede(self):  # Tem quique sobrando: continua (já espelhado). Senão, some.
        if self.quiques_restantes > 0:
            self.quiques_restantes -= 1
            self.quiques += 1
        else:
            self.kill()

    # Chamado quando o projétil encosta em inimigos. Cada tipo de projétil faz o seu (POLIMORFISMO).
    def acertou(self, inimigos_atingidos, todos_os_inimigos, tempo, efeitos):
        alvo = inimigos_atingidos[0]
        alvo.levar_dano(self.dano)  # Tira vida do primeiro
        if self.quiques_restantes > 0:  # Poder QUICAR: em vez de sumir, vai atrás de outro inimigo
            self.quicar(alvo, todos_os_inimigos)
        else:
            self.kill()  # E some

    def quicar(self, alvo, todos_os_inimigos):
        self.quiques_restantes -= 1
        self.quiques += 1
        self.ignorar = alvo
        outros = [inimigo for inimigo in todos_os_inimigos if inimigo is not alvo and inimigo.vida > 0]
        proximo = min(outros, key=lambda inimigo: self.posicao.distance_to(inimigo.rect.center), default=None)
        ate_o_proximo = pygame.Vector2(proximo.rect.center) - self.posicao if proximo else pygame.Vector2()
        if ate_o_proximo.length() > 0:
            self.velocidade = ate_o_proximo.normalize() * self.rapidez
        else:  # Ninguém por perto: quica de volta, meio torto
            self.velocidade = pygame.Vector2(-self.velocidade.x, self.velocidade.y).rotate(random.uniform(-30, 30))

    # Uma cópia deste tiro, virada "angulo" graus e afastada "deslocamento" pixels para o lado.
    def copiar(self, angulo=0, deslocamento=0):
        alcance = max(1, self.alcance - self.distancia_percorrida) if self.alcance else None
        return self.herdar(Projetil(self.imagem_original, self.posicao.x, self.posicao.y, 0, 0, self.dano, alcance), angulo, deslocamento)

    # Poder REPETIR: uma cópia que sai de novo do pássaro ("origem"), reto para a direita. A "vez" afasta uma repetição da outra.
    def repetir(self, origem, vez=1):
        copia = self.copiar()
        copia.posicao = pygame.Vector2(origem) - (10 * vez, 0)
        copia.velocidade = pygame.Vector2(self.rapidez, 0)
        copia.distancia_percorrida = 0.0
        copia.alcance = self.alcance
        copia.ignorar = None
        copia.rect.center = (round(copia.posicao.x), round(copia.posicao.y))
        return copia

    def herdar(self, copia, angulo, deslocamento):
        copia.posicao += self.velocidade.rotate(90).normalize() * deslocamento  # "Para o lado" = 90 graus da direção do tiro
        copia.velocidade = self.velocidade.rotate(angulo)
        copia.rapidez = self.rapidez
        copia.dano = self.dano * FRACAO_DO_DANO_DA_COPIA
        copia.numero, copia.quiques, copia.quiques_restantes = self.numero, self.quiques, self.quiques_restantes
        copia.seguindo, copia.inimigos, copia.ignorar = self.seguindo, self.inimigos, self.ignorar
        copia.geracao = self.geracao + 1
        copia.rect.center = (round(copia.posicao.x), round(copia.posicao.y))
        return copia


# MÍSSIL: um projétil que faz curva atrás do inimigo mais perto e explode, machucando quem estiver em volta.
class ProjetilMissil(Projetil):

    def __init__(self, x, y, raio_da_explosao, velocidade_y):
        super().__init__(carregar_quadros("missil", 16)[0], x, y, VELOCIDADE_DO_MISSIL, velocidade_y, DANO_DO_MISSIL)
        self.rapidez = VELOCIDADE_DO_MISSIL
        self.raio_da_explosao = raio_da_explosao
        self.seguindo = True  # O míssil sempre segue

    def copiar(self, angulo=0, deslocamento=0):
        return self.herdar(ProjetilMissil(self.posicao.x, self.posicao.y, self.raio_da_explosao, 0), angulo, deslocamento)

    # SOBRESCRITA: em vez de só machucar um, explode e machuca todos dentro do raio.
    def acertou(self, inimigos_atingidos, todos_os_inimigos, tempo, efeitos):
        inimigos_atingidos[0].levar_dano(self.dano)
        for inimigo in todos_os_inimigos:
            if self.posicao.distance_to(inimigo.rect.center) <= self.raio_da_explosao + inimigo.rect.width / 2:
                inimigo.levar_dano(DANO_DA_EXPLOSAO_DO_MISSIL)
        efeitos.add(Explosao(self.posicao, "explosao_media", 32, tamanho=self.raio_da_explosao * 2 + 8))
        self.kill()


# RAIO LASER: uma faixa de luz que sai do pássaro até o fim da tela, atravessa tudo e machuca enquanto encosta.
# Com os PODERES: dividir e multiplicar criam raios a mais; ao acertar, os poderes saem numa FAÍSCA (um tiro) do inimigo atingido.
class RaioLaser(pygame.sprite.Sprite):

    def __init__(self, passaro, deslocamento_vertical, grossura, largura_da_tela):
        super().__init__()
        self.passaro = passaro  # O raio acompanha o pássaro
        self.deslocamento_vertical = deslocamento_vertical  # Distância do meio do pássaro (para vários raios lado a lado)
        self.grossura = grossura
        self.largura_da_tela = largura_da_tela
        self.dano_por_segundo = DANO_DO_LASER_POR_SEGUNDO * grossura  # Raio mais grosso machuca mais
        # Atributos dos poderes (os mesmos nomes do Projetil, para os poderes funcionarem nos dois)
        self.numero = 0
        self.quiques = 0
        self.quiques_restantes = 0
        self.seguindo = False
        self.inimigos = None
        self.geracao = 0
        self.ignorar = None
        self.tocados = set()  # Inimigos que este raio já tocou (o evento "acertou" acontece uma vez por inimigo)
        self.idade = 0.0
        self.imagem_cheia = pygame.Surface((largura_da_tela, grossura + 2), pygame.SRCALPHA)
        self.imagem_cheia.fill(COR_DO_LASER)
        self.imagem_cheia.fill(COR_DO_MIOLO_DO_LASER, (0, 1, largura_da_tela, grossura))  # Miolo claro, borda azul
        self.image = self.imagem_cheia
        self.rect = self.image.get_rect()
        self.posicionar()

    def posicionar(self):
        self.rect.midleft = (self.passaro.rect.centerx + 6, self.passaro.rect.centery + self.deslocamento_vertical)

    def update(self, tempo, area_do_jogo):
        self.idade += tempo
        self.posicionar()
        self.image = self.imagem_cheia.copy()
        self.image.set_alpha(round(255 * max(0.0, 1 - self.idade / DURACAO_DO_LASER)))  # Vai apagando
        if self.idade >= DURACAO_DO_LASER:
            self.kill()

    def acertou(self, inimigos_atingidos, todos_os_inimigos, tempo, efeitos):
        for inimigo in inimigos_atingidos:  # Atravessa: machuca todos que encosta, um pouco a cada quadro
            inimigo.levar_dano(self.dano_por_segundo * tempo)

    # Um raio a mais: o ângulo vira distância para o lado (o raio é sempre reto).
    def copiar(self, angulo=0, deslocamento=0):
        copia = RaioLaser(self.passaro, self.deslocamento_vertical + deslocamento + angulo / 3, self.grossura, self.largura_da_tela)
        copia.dano_por_segundo = self.dano_por_segundo * FRACAO_DO_DANO_DA_COPIA
        copia.numero, copia.inimigos, copia.geracao = self.numero, self.inimigos, self.geracao + 1
        return copia

    def repetir(self, origem, vez=1):  # Um pulso novo (o raio já sai do pássaro)
        return self.copiar()

    # FAÍSCA: o tiro que sai do inimigo atingido pelo raio, para os poderes de acerto (quicar, seguir, dividir...).
    def faisca(self, alvo):
        imagem = sprite("tiro_do_blaster")
        faisca = Projetil(imagem, alvo.rect.centerx, alvo.rect.centery, VELOCIDADE_DO_TIRO, 0, self.grossura)
        faisca.numero, faisca.inimigos, faisca.ignorar, faisca.geracao = self.numero, self.inimigos, alvo, self.geracao + 1
        return faisca


# CLASSE ARMA: o "molde" de todas as armas.
class Arma:

    # CONSTRUTOR
    #   nome               -> como a arma se chama no script (ex.: "laser")
    #   titulo, descricao  -> o que aparece na carta de escolha
    #   parametros         -> dicionário: nome do parâmetro -> (mínimo, máximo)
    #   valores            -> dicionário: nome do parâmetro -> valor atual
    #   limite             -> o limite compartilhado: parametro1 x parametro2 <= limite
    #   aumento_do_limite  -> quanto o limite sobe a cada nível
    #   intervalo          -> segundos entre um disparo e outro
    def __init__(self, nome, titulo, descricao, parametros, valores, limite, aumento_do_limite, intervalo):
        # ATRIBUTOS
        self.nome = nome
        self.titulo = titulo
        self.descricao = descricao
        self.parametros = parametros
        self.valores = dict(valores)  # "dict(...)" faz uma CÓPIA, para não mexer no dicionário original
        self.limite = limite
        self.aumento_do_limite = aumento_do_limite
        self.intervalo = intervalo
        self.espera = 0.0  # Quanto falta para o próximo disparo
        self.disparos = 0  # Quantas vezes já atirou (vira o tiro.numero do script)

    # MÉTODOS

    def rodape_da_carta(self):
        return "Limite: " + self.texto_do_limite()

    def nomes_dos_parametros(self):
        return list(self.parametros)  # A lista dos nomes (sempre dois)

    # O produto dos dois parâmetros, que precisa ficar abaixo do limite. "valores" pode vir de um script ainda não aplicado.
    def produto(self, valores=None):
        valores = valores or self.valores
        primeiro, segundo = self.nomes_dos_parametros()
        return valores[primeiro] * valores[segundo]

    def texto_do_limite(self):
        primeiro, segundo = self.nomes_dos_parametros()
        return f"{primeiro} x {segundo} <= {self.limite}"

    def subir_limite(self):
        self.limite += self.aumento_do_limite

    # As linhas que entram no script quando a arma é desbloqueada.
    def linhas_do_script(self):
        linhas = [f"# Limite do {self.nome}: {self.texto_do_limite()}"]
        for parametro, valor in self.valores.items():
            linhas.append(f"{self.nome}.{parametro} = {valor}")
        return linhas

    def intervalo_atual(self):  # As filhas podem mudar (o blaster depende da cadência)
        return self.intervalo

    # Chamado a cada quadro: conta o tempo e atira quando chega a hora.
    def atualizar(self, tempo, passaro, inimigos, projeteis, area_do_jogo):
        self.espera -= tempo
        if self.espera <= 0:
            self.espera = max(0.0, self.espera + self.intervalo_atual())  # Começa a contar para o próximo
            self.disparos += 1
            self.atirar(passaro, inimigos, projeteis, area_do_jogo)

    def atirar(self, passaro, inimigos, projeteis, area_do_jogo):  # Cada arma SOBRESCREVE
        pass

    def icone(self):  # O desenho da arma (na carta e na mão do pássaro), em sprites_das_armas.py
        return sprite(self.nome)


class Blaster(Arma):

    def __init__(self):
        super().__init__("blaster", "BLASTER", ["Tiros retos e rápidos.", "Mais cadência = mais tiros por segundo.", "Mais dano = tiros mais fortes."],
                         {"cadencia": (1, 10), "dano": (1, 10)}, {"cadencia": 4, "dano": 3}, limite=12, aumento_do_limite=3, intervalo=0.25)

    def intervalo_atual(self):
        return 1 / self.valores["cadencia"]  # Cadência 4 = um tiro a cada 1/4 de segundo

    def atirar(self, passaro, inimigos, projeteis, area_do_jogo):
        imagem = sprite("tiro_do_blaster")
        projeteis.add(Projetil(imagem, passaro.rect.centerx + 8, passaro.rect.centery, VELOCIDADE_DO_TIRO, 0, self.valores["dano"]))


class Laser(Arma):

    def __init__(self):
        super().__init__("laser", "LASER", ["Raios que atravessam tudo.", "Mais quantidade = mais raios.", "Mais grossura = raios mais fortes."],
                         {"quantidade": (1, 5), "grossura": (1, 8)}, {"quantidade": 2, "grossura": 3}, limite=6, aumento_do_limite=2, intervalo=1.0)

    def atirar(self, passaro, inimigos, projeteis, area_do_jogo):
        quantidade, grossura = self.valores["quantidade"], self.valores["grossura"]
        espaco = grossura + 4  # Distância entre um raio e outro
        for numero in range(quantidade):
            deslocamento = (numero - (quantidade - 1) / 2) * espaco  # Os raios ficam centralizados no pássaro
            projeteis.add(RaioLaser(passaro, deslocamento, grossura, area_do_jogo.width))


class Missil(Arma):

    def __init__(self):
        super().__init__("missil", "MÍSSIL", ["Mísseis que perseguem o inimigo.", "Mais quantidade = mais mísseis.", "Mais explosao = explosão maior."],
                         {"quantidade": (1, 6), "explosao": (4, 24)}, {"quantidade": 2, "explosao": 12}, limite=24, aumento_do_limite=6, intervalo=1.5)

    def atirar(self, passaro, inimigos, projeteis, area_do_jogo):
        quantidade = self.valores["quantidade"]
        for numero in range(quantidade):
            velocidade_y = (numero - (quantidade - 1) / 2) * 60  # Saem abertos em leque e depois fazem curva
            missil = ProjetilMissil(passaro.rect.centerx, passaro.rect.centery, self.valores["explosao"], velocidade_y)
            missil.inimigos = inimigos
            projeteis.add(missil)


class Espalhado(Arma):

    def __init__(self):
        super().__init__("espalhado", "ESPALHADO", ["Um leque de balas de perto.", "Mais balas = leque mais cheio.", "Mais alcance = balas vão mais longe."],
                         {"balas": (1, 9), "alcance": (40, 200)}, {"balas": 4, "alcance": 100}, limite=400, aumento_do_limite=80, intervalo=0.7)

    def atirar(self, passaro, inimigos, projeteis, area_do_jogo):
        balas = self.valores["balas"]
        imagem = sprite("bala_do_espalhado")
        for numero in range(balas):
            angulo = 0 if balas == 1 else math.radians(-ABERTURA_DO_ESPALHADO / 2 + ABERTURA_DO_ESPALHADO * numero / (balas - 1))  # Do ângulo de cima até o de baixo
            projeteis.add(Projetil(imagem, passaro.rect.centerx + 6, passaro.rect.centery,
                                   VELOCIDADE_DO_TIRO * math.cos(angulo), VELOCIDADE_DO_TIRO * math.sin(angulo), DANO_DO_ESPALHADO, alcance=self.valores["alcance"]))


# Cria uma arma de cada tipo. Dicionário: nome no script -> objeto Arma.
def criar_todas_as_armas():
    return {arma.nome: arma for arma in (Blaster(), Laser(), Missil(), Espalhado())}
