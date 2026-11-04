# CLASSE CANO
# Cada cano na tela é um OBJETO desta classe. O par de canos (cima e baixo) são dois objetos
# criados com o MESMO molde, só que com atributos diferentes.

from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

CAMINHO_DA_IMAGEM_DO_CANO = Path(__file__).parent.parent / "src" / "assets" / "cano.png"  # Desenho do cano (32x256, com a "tampa" em cima)
VELOCIDADE_DO_CENARIO = 50.0  # Quantos pixels por segundo os canos (e o chão) andam para a esquerda (devagar: o foco é programar, não desviar)
VELOCIDADE_DA_ANIMACAO = 8.0  # Quão rápido o cano desliza até a posição nova (maior = mais rápido; 8 leva uns 0,4 segundo)


# HERANÇA: assim como o Passaro, o Cano também "é um" Sprite do pygame.
class Cano(pygame.sprite.Sprite):

    # ATRIBUTO DE CLASSE: pertence à classe, e não a um cano só. Todos os canos usam a MESMA imagem,
    # então carregamos o arquivo uma vez só, em vez de ler o disco a cada cano novo.
    imagem_original = None

    # CONSTRUTOR: "borda_da_abertura" é a altura onde o cano termina e começa o espaço para o pássaro passar.
    # "fica_em_cima" diz se este é o cano de cima (True) ou o de baixo (False).
    def __init__(self, posicao_horizontal, borda_da_abertura, fica_em_cima):
        super().__init__()  # Chama o construtor da classe mãe (Sprite)

        # ATRIBUTOS
        self.velocidade_horizontal = VELOCIDADE_DO_CENARIO  # Quantos pixels por segundo o cano anda para a esquerda
        self.posicao_horizontal = float(posicao_horizontal)  # Posição com casas decimais, para o movimento ficar suave
        self.vale_ponto = fica_em_cima  # Só o cano de cima vale ponto, assim cada PAR de canos conta 1 ponto só
        self.fica_em_cima = fica_em_cima  # Guardamos para saber para que lado a borda empurra o cano
        self.borda = float(borda_da_abertura)  # Altura atual da borda (com casas decimais, para a animação ficar suave)
        self.borda_alvo = self.borda  # Altura para onde a borda está indo; quando é igual à atual, o cano está parado
        self.deslocamento = 0.0  # Quantos pixels o cano está empurrado para a direita (usado para afastar os canos)
        self.deslocamento_alvo = 0.0  # Para onde o deslocamento está indo

        if Cano.imagem_original is None:  # Primeiro cano do jogo? Então ainda não carregamos a imagem
            Cano.imagem_original = pygame.image.load(CAMINHO_DA_IMAGEM_DO_CANO).convert_alpha()  # Carrega o desenho (com transparência)
        if fica_em_cima:  # Cano de cima: pendurado, termina na borda da abertura
            self.image = pygame.transform.flip(Cano.imagem_original, False, True)  # Vira de cabeça para baixo, para a tampa ficar virada para a abertura
        else:  # Cano de baixo: começa na borda da abertura e vai até o chão
            self.image = Cano.imagem_original  # Usa a imagem do jeito que ela é
        self.rect = self.image.get_rect()  # Retângulo do tamanho da imagem; a posição certa vem logo abaixo
        self.posicionar()  # Coloca o retângulo no lugar

    # MÉTODOS

    # Pede para a borda ir até uma altura nova. O cano não pula para lá: ele desliza aos poucos (veja "animar").
    def mudar_borda(self, nova_borda):
        self.borda_alvo = float(nova_borda)  # Só troca o destino; a animação faz o resto

    # Pede para o cano se afastar (ou se aproximar) na horizontal, também deslizando.
    def mudar_deslocamento(self, novo_deslocamento):
        self.deslocamento_alvo = float(novo_deslocamento)  # Só troca o destino; a animação faz o resto

    # ANIMAÇÃO: a cada quadro, anda uma parte do caminho que falta até o alvo. Perto do alvo anda pouco,
    # longe anda muito, e por isso o movimento começa rápido e termina suave.
    # Recebe o tempo REAL (e não o do jogo) para a animação aparecer na hora, mesmo em câmera lenta.
    def animar(self, tempo_real):
        parte_do_caminho = min(1.0, VELOCIDADE_DA_ANIMACAO * tempo_real)  # Que fração do caminho andar neste quadro (no máximo tudo)
        self.borda += (self.borda_alvo - self.borda) * parte_do_caminho  # Aproxima a borda do alvo
        self.deslocamento += (self.deslocamento_alvo - self.deslocamento) * parte_do_caminho  # Aproxima o deslocamento do alvo
        self.posicionar()  # Move o retângulo para a posição nova

    # MÉTODO AUXILIAR: põe o retângulo (que só aceita números inteiros) na posição atual do cano.
    def posicionar(self):
        self.rect.x = round(self.posicao_horizontal + self.deslocamento)  # Posição na horizontal, mais o empurrão para a direita
        if self.fica_em_cima:  # O cano de cima termina na borda...
            self.rect.bottom = round(self.borda)  # ...então a parte de BAIXO dele fica na borda
        else:  # O cano de baixo começa na borda...
            self.rect.top = round(self.borda)  # ...então a parte de CIMA dele fica na borda

    # SOBRESCRITA: o Passaro e o Cano têm um "update", mas cada um faz uma coisa diferente.
    # O grupo chama "update" de todos sem saber quem é quem. Isso se chama POLIMORFISMO.
    def update(self, tempo_do_quadro):
        self.posicao_horizontal -= self.velocidade_horizontal * tempo_do_quadro  # Anda para a esquerda
        self.posicionar()  # Atualiza o retângulo
        if self.rect.right < 0:  # Se o cano saiu inteiro pela esquerda da tela...
            self.kill()  # ...remove ele de todos os grupos. "kill" é um método HERDADO do Sprite
