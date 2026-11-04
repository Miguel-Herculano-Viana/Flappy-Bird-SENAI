# CLASSE AVISO
# Um pop-up que aparece por cima do jogo dizendo o que mudou (ex.: "abertura: 0 -> 80").
# Ele entra deslizando de cima, fica um tempo na tela e some aos poucos.
# É desenhado na resolução do monitor (e não na do jogo), por isso o texto fica nítido.

import pygame  # Biblioteca de jogos que estamos usando

SEGUNDOS_NA_TELA = 2.5  # Quanto tempo cada aviso fica visível
SEGUNDOS_PARA_ENTRAR = 0.3  # Duração da animação de entrada (deslizando de cima)
SEGUNDOS_PARA_SUMIR = 0.5  # Duração da animação de saída (ficando transparente)
COR_DO_FUNDO_DO_AVISO = (20, 22, 34)  # Fundo escuro, para o texto aparecer em cima do céu
TRANSPARENCIA_DO_FUNDO = 210  # 0 = invisível, 255 = opaco
DISTANCIA_DO_TOPO = 0.12  # O primeiro aviso fica a 12% da altura do jogo, abaixo dos pontos


class Aviso:

    # CONSTRUTOR: o texto e a cor do aviso. "segundos" muda quanto tempo ele fica na tela.
    def __init__(self, texto, cor, segundos=SEGUNDOS_NA_TELA):
        # ATRIBUTOS
        self.texto = texto
        self.cor = cor
        self.segundos_na_tela = segundos
        self.idade = 0.0  # Há quantos segundos o aviso apareceu

    # MÉTODOS

    # Chamado a cada quadro com o tempo REAL (os avisos não ficam lentos na câmera lenta).
    def atualizar(self, tempo_real):
        self.idade += tempo_real

    def acabou(self):
        return self.idade >= self.segundos_na_tela

    # Desenha o aviso dentro da área do jogo no monitor. "posicao_na_fila" empilha vários avisos um embaixo do outro.
    def desenhar(self, monitor, area_do_jogo, fonte, posicao_na_fila):
        imagem_do_texto = fonte.render(self.texto, True, self.cor)  # Transforma o texto em imagem
        margem = fonte.get_height() // 3  # Espaço entre o texto e a borda da caixa
        caixa = pygame.Surface((imagem_do_texto.get_width() + 2 * margem, imagem_do_texto.get_height() + 2 * margem), pygame.SRCALPHA)  # Caixa com transparência
        pygame.draw.rect(caixa, (*COR_DO_FUNDO_DO_AVISO, TRANSPARENCIA_DO_FUNDO), caixa.get_rect(), border_radius=margem)  # Fundo escuro arredondado
        pygame.draw.rect(caixa, self.cor, caixa.get_rect(), width=max(2, margem // 4), border_radius=margem)  # Borda na cor do aviso
        caixa.blit(imagem_do_texto, (margem, margem))  # Texto dentro da caixa

        # ENTRADA: nos primeiros instantes, a caixa desce de cima. "1 - (1 - x)²" começa rápido e freia no fim.
        progresso_da_entrada = min(1.0, self.idade / SEGUNDOS_PARA_ENTRAR)  # Vai de 0 até 1
        suavizado = 1 - (1 - progresso_da_entrada) ** 2  # Mesma faixa (0 a 1), mas freando no fim
        altura_final = area_do_jogo.top + area_do_jogo.height * DISTANCIA_DO_TOPO + posicao_na_fila * (caixa.get_height() + margem)  # Onde a caixa vai parar
        altura_atual = area_do_jogo.top - caixa.get_height() + (altura_final - area_do_jogo.top + caixa.get_height()) * suavizado  # Começa escondida acima do jogo

        # SAÍDA: no fim, a caixa vai ficando transparente.
        tempo_que_falta = self.segundos_na_tela - self.idade
        caixa.set_alpha(round(255 * max(0.0, min(1.0, tempo_que_falta / SEGUNDOS_PARA_SUMIR))))  # 255 = opaco, 0 = invisível

        posicao = caixa.get_rect(midtop=(area_do_jogo.centerx, round(altura_atual)))  # Centralizado na horizontal
        recorte_anterior = monitor.get_clip()  # Guarda o recorte atual do monitor
        monitor.set_clip(area_do_jogo)  # Só desenha dentro da área do jogo (na entrada, a parte de cima fica escondida)
        monitor.blit(caixa, posicao)
        monitor.set_clip(recorte_anterior)  # Volta o recorte como estava
