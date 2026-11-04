# DESAFIOS DE CÓDIGO
# No meio da partida aparecem problemas (ex.: os canos fecham) que o visitante resolve escrevendo uma linha de Python.
#
# CLASSE Desafio: o "molde" de todo desafio. Cada desafio de verdade é uma classe FILHA dela (HERANÇA)
# e troca só os métodos que precisa (SOBRESCRITA). O gerenciador chama os mesmos métodos em qualquer desafio,
# sem saber qual é (POLIMORFISMO).
#
# CLASSE GerenciadorDeDesafios: o "diretor". Decide quando um desafio começa, abre o editor, controla
# a câmera lenta e o tutorial, e avisa o visitante de tudo que mudou.

import math  # Ferramenta do Python com contas (usada para fazer o destaque pulsar)
import random  # Ferramenta do Python para sortear números

import pygame  # Biblioteca de jogos que estamos usando

from avisos import Aviso, criar_caixa  # Pop-ups e caixas de texto
from editor import EditorDeCodigo  # O editor onde o visitante digita o código

# BALANCEAMENTO: mude estes números para deixar o jogo mais fácil ou mais difícil
PRIMEIRO_DESAFIO_NO_PAR = 2  # O primeiro desafio aparece no 2º par de canos
MENOR_INTERVALO_ENTRE_DESAFIOS = 2  # Depois de um desafio, o próximo vem entre 2...
MAIOR_INTERVALO_ENTRE_DESAFIOS = 3  # ...e 3 pares de canos
PARES_DE_ESPERA_DO_MESMO_DESAFIO = 4  # COOLDOWN: o mesmo desafio só volta depois de 4 pares
SEGUNDOS_NO_EDITOR = 20  # Tempo para acertar o código (fora do tutorial)
PONTOS_POR_DESAFIO = 2  # Bônus por resolver um desafio
ESCALA_DO_TEMPO_EDITANDO = 0.15  # Câmera lenta enquanto o editor está aberto
ESCALA_DO_TEMPO_DE_ALERTA = 0.5  # Câmera lenta leve quando o desafio aparece, para dar tempo de apertar ENTER
SEGUNDOS_MOSTRANDO_O_ACERTO = 1.5  # Quanto tempo o "OK!" fica no painel depois de acertar
SEGUNDOS_COMEMORANDO_NO_TUTORIAL = 2.0  # No tutorial, o jogo espera este tempo parado para o visitante ver o resultado
X_ONDE_O_CANO_FICA_VISIVEL = 112  # Um cano novo nasce em x = 144 (fora da tela); em 112 ele já aparece bem
AREA_VISIVEL_DO_JOGO = pygame.Rect(0, 0, 144, 224)  # A tela do jogo acima do chão

COR_DO_ALERTA = (255, 110, 110)  # Vermelho
COR_DO_ACERTO = (120, 230, 120)  # Verde
COR_DA_DICA = (255, 210, 60)  # Amarelo
COR_DA_PREVIA = (120, 230, 120)  # Verde, para o contorno "fantasma" do resultado


class Desafio:

    # CONSTRUTOR
    #   objeto, atributo     -> o que o visitante muda (ex.: canos.abertura)
    #   minimo, maximo       -> faixa permitida (fora dela dá ValueError e o jogo não muda)
    #   alerta               -> texto do pop-up quando o desafio aparece
    #   explicacao           -> linhas do tutorial, mostradas na primeira vez
    def __init__(self, objeto, atributo, minimo, maximo, alerta, explicacao):
        # ATRIBUTOS
        self.objeto = objeto
        self.atributo = atributo
        self.minimo = minimo
        self.maximo = maximo
        self.alerta = alerta
        self.explicacao = explicacao
        self.nivel_de_digitacao = 1  # 1 = só o valor; 2 = atributo e valor; 3 = a linha inteira

    # Quanto da linha já vem escrito, de acordo com o nível. A cada acerto, vem menos pronto.
    def codigo_pronto(self):
        if self.nivel_de_digitacao == 1:
            return f"{self.objeto}.{self.atributo} = "  # Falta só o número
        if self.nivel_de_digitacao == 2:
            return f"{self.objeto}."  # Falta o atributo e o número
        return ""  # Falta tudo

    # Dica curta (fora do tutorial), de acordo com o nível.
    def dica(self):
        if self.nivel_de_digitacao == 1:
            return [self.alerta.capitalize(), f"Complete o valor de {self.atributo}."]
        if self.nivel_de_digitacao == 2:
            return [self.alerta.capitalize(), f"Escreva o atributo e o valor: {self.atributo} = número"]
        return [self.alerta.capitalize(), f"Escreva a linha inteira: {self.objeto}.{self.atributo} = número"]

    # MÉTODOS QUE CADA DESAFIO SOBRESCREVE (aqui eles não fazem nada; as classes filhas fazem o trabalho)

    def comecar(self, passaro, par_de_canos):  # Cria o problema (ex.: fecha os canos)
        pass

    def esta_visivel(self):  # O problema já aparece na tela? (só então o alerta e o tutorial aparecem)
        return True

    def aplicar(self, valor, passaro):  # Usa o valor digitado pelo visitante
        pass

    def terminou(self, passaro):  # O desafio já passou?
        return True

    def desfazer(self, passaro):  # Volta o jogo ao normal quando o desafio acaba
        pass

    def valor_atual(self, passaro):  # Valor do atributo agora (para os medidores e os avisos)
        return None

    def area_do_problema(self):  # Retângulo (na tela do jogo) que pisca para mostrar onde está o problema
        return None

    def desenhar_previa(self, monitor, para_o_monitor, valor):  # Mostra como ficaria com o valor que está sendo digitado
        pass


# HERANÇA: os canos fechados "são um" Desafio, com o comportamento próprio deles.
class DesafioCanosFechados(Desafio):

    def __init__(self):
        super().__init__("canos", "abertura", 56, 96, "OS CANOS FECHARAM!", [
            "Os canos fecharam! Vamos abrir com código.",
            "'canos' é um OBJETO do jogo e 'abertura' é um ATRIBUTO dele.",
            "O sinal = guarda um valor novo no atributo.",
            "Digite um número e aperte ENTER.",
        ])
        self.cano_de_cima = None
        self.cano_de_baixo = None
        self.centro = 0.0

    # SOBRESCRITA: fecha o par de canos que acabou de nascer. Os canos deslizam até se encostarem.
    def comecar(self, passaro, par_de_canos):
        self.cano_de_cima, self.cano_de_baixo = par_de_canos
        self.centro = (self.cano_de_cima.borda + self.cano_de_baixo.borda) / 2  # Meio da abertura
        self.cano_de_cima.mudar_borda(self.centro)  # As duas bordas vão para o meio...
        self.cano_de_baixo.mudar_borda(self.centro)  # ...e os canos se fecham

    def esta_visivel(self):
        return self.cano_de_cima.rect.x <= X_ONDE_O_CANO_FICA_VISIVEL

    # Abre os canos com a abertura digitada, metade para cima e metade para baixo do meio.
    def aplicar(self, valor, passaro):
        self.cano_de_cima.mudar_borda(self.centro - valor / 2)
        self.cano_de_baixo.mudar_borda(self.centro + valor / 2)

    def terminou(self, passaro):
        return self.cano_de_cima.rect.right < passaro.rect.left or not self.cano_de_cima.alive()  # O par ficou para trás (ou saiu do jogo)

    def valor_atual(self, passaro):
        return round(self.cano_de_baixo.borda_alvo - self.cano_de_cima.borda_alvo)  # Distância entre as duas bordas

    def area_do_problema(self):
        return self.cano_de_cima.rect.union(self.cano_de_baixo.rect).clip(AREA_VISIVEL_DO_JOGO)  # Só a parte que aparece na tela

    # Contorno verde de onde a abertura vai ficar.
    def desenhar_previa(self, monitor, para_o_monitor, valor):
        abertura = pygame.Rect(self.cano_de_cima.rect.x, round(self.centro - valor / 2), self.cano_de_cima.rect.width, round(valor))  # Na tela do jogo
        desenhar_retangulo_transparente(monitor, para_o_monitor(abertura), COR_DA_PREVIA)


class GerenciadorDeDesafios:

    # CONSTRUTOR: recebe a lista de avisos (para mostrar pop-ups) e o placar (para dar o bônus).
    # Cada partida cria um gerenciador novo, então cada visitante vê os tutoriais desde o começo.
    def __init__(self, avisos, placar):
        # ATRIBUTOS
        self.avisos = avisos
        self.placar = placar
        self.desafios = [DesafioCanosFechados()]  # Na ordem em que aparecem pela primeira vez
        self.desafios_com_tutorial_visto = []  # Desafios que já apareceram nesta partida
        self.pares_de_espera = {}  # COOLDOWN: desafio -> quantos pares faltam para ele poder voltar
        self.pares_ate_o_proximo_desafio = PRIMEIRO_DESAFIO_NO_PAR
        self.desafio_ativo = None  # O desafio que está acontecendo agora (ou None)
        self.editor = None  # O editor do desafio ativo (continua o mesmo se o visitante fechar e abrir de novo)
        self.editor_aberto = False
        self.ja_alertou = False  # O alerta do desafio ativo já apareceu?
        self.resolvido = False  # O visitante já acertou o código do desafio ativo?
        self.valor_antes = None  # Valor do atributo antes do visitante mudar (para o aviso "0 -> 80")
        self.segundos_mostrando_o_acerto = 0.0
        # TUTORIAL (só na primeira vez de cada desafio):
        #   None          -> sem tutorial
        #   "esperando"   -> o desafio começou, mas o problema ainda não apareceu na tela
        #   "mostrando"   -> jogo parado, mostrando o problema e pedindo ENTER
        #   "editando"    -> jogo parado, visitante digitando (sem limite de tempo)
        #   "comemorando" -> jogo parado um instante, mostrando o resultado
        self.etapa_do_tutorial = None
        self.tempo_total = 0.0  # Relógio para as animações (piscar e pulsar)

    # MÉTODOS

    # Chamado pelo jogo cada vez que nasce um par de canos. É aqui que um desafio novo pode começar.
    def novo_par_criado(self, par_de_canos, passaro):
        for desafio in self.pares_de_espera:  # Cada par novo diminui o cooldown de todos
            self.pares_de_espera[desafio] -= 1
        if self.desafio_ativo:  # Já tem um desafio acontecendo
            return
        self.pares_ate_o_proximo_desafio -= 1
        if self.pares_ate_o_proximo_desafio > 0:  # Ainda não é a hora
            return
        disponiveis = [desafio for desafio in self.desafios if self.pares_de_espera.get(desafio, 0) <= 0]  # Os que não estão em cooldown
        if not disponiveis:  # Todos em cooldown: tenta de novo no próximo par
            return
        nunca_vistos = [desafio for desafio in disponiveis if desafio not in self.desafios_com_tutorial_visto]
        desafio = nunca_vistos[0] if nunca_vistos else random.choice(disponiveis)  # Primeiro os novos (na ordem), depois sorteio
        self.comecar(desafio, par_de_canos, passaro)

    def comecar(self, desafio, par_de_canos, passaro):
        desafio.comecar(passaro, par_de_canos)  # POLIMORFISMO: cada desafio cria o seu problema
        self.desafio_ativo = desafio
        self.editor = None
        self.editor_aberto = False
        self.ja_alertou = False
        self.resolvido = False
        self.valor_antes = desafio.valor_atual(passaro)
        self.etapa_do_tutorial = "esperando" if desafio not in self.desafios_com_tutorial_visto else None

    # Chamado a cada quadro com o tempo REAL.
    def atualizar(self, tempo_real, passaro):
        self.tempo_total += tempo_real
        desafio = self.desafio_ativo
        if desafio is None:
            return

        if not self.ja_alertou and desafio.esta_visivel():  # O problema acabou de aparecer na tela
            self.ja_alertou = True
            self.avisos.append(Aviso(desafio.alerta, COR_DO_ALERTA))
            if self.etapa_do_tutorial == "esperando":
                self.etapa_do_tutorial = "mostrando"  # Para o jogo e explica

        if self.editor:
            self.editor.atualizar(tempo_real)
            if self.editor.valor_aceito is not None and not self.resolvido:  # Acabou de acertar!
                self.resolver(passaro)
            elif self.editor_aberto and self.editor.acabou_o_tempo():  # O tempo do editor acabou
                self.editor_aberto = False
                self.avisos.append(Aviso("TEMPO ESGOTADO!", COR_DO_ALERTA))

        if self.resolvido:  # Depois de acertar, o "OK!" fica um tempo no painel
            self.segundos_mostrando_o_acerto -= tempo_real
            if self.segundos_mostrando_o_acerto <= 0:
                self.editor_aberto = False
                if self.etapa_do_tutorial == "comemorando":
                    self.etapa_do_tutorial = None  # Fim do tutorial: o jogo volta

        if desafio.terminou(passaro):
            self.terminar(passaro)

    # O visitante acertou o código: muda o jogo e comemora.
    def resolver(self, passaro):
        desafio = self.desafio_ativo
        valor = self.editor.valor_aceito
        desafio.aplicar(valor, passaro)  # POLIMORFISMO: cada desafio usa o valor do seu jeito
        self.resolvido = True
        self.avisos.append(Aviso(f"{desafio.atributo}: {self.valor_antes} -> {valor}", COR_DO_ACERTO))
        self.avisos.append(Aviso(f"+{PONTOS_POR_DESAFIO} pontos!", COR_DA_DICA))
        self.placar.marcar_ponto(PONTOS_POR_DESAFIO)
        desafio.nivel_de_digitacao = min(3, desafio.nivel_de_digitacao + 1)  # Da próxima vez, vem menos código pronto
        if self.etapa_do_tutorial == "editando":
            self.etapa_do_tutorial = "comemorando"
            self.segundos_mostrando_o_acerto = SEGUNDOS_COMEMORANDO_NO_TUTORIAL
            self.avisos.append(Aviso("VOCÊ PROGRAMOU O JOGO!", COR_DO_ACERTO, segundos=SEGUNDOS_COMEMORANDO_NO_TUTORIAL + 1))
        else:
            self.segundos_mostrando_o_acerto = SEGUNDOS_MOSTRANDO_O_ACERTO

    # O desafio passou: desfaz o efeito, liga o cooldown e marca quando vem o próximo.
    def terminar(self, passaro):
        desafio = self.desafio_ativo
        desafio.desfazer(passaro)
        self.pares_de_espera[desafio] = PARES_DE_ESPERA_DO_MESMO_DESAFIO
        if desafio not in self.desafios_com_tutorial_visto:
            self.desafios_com_tutorial_visto.append(desafio)
        self.desafio_ativo = None
        self.editor = None
        self.editor_aberto = False
        self.etapa_do_tutorial = None
        self.pares_ate_o_proximo_desafio = random.randint(MENOR_INTERVALO_ENTRE_DESAFIOS, MAIOR_INTERVALO_ENTRE_DESAFIOS)

    # ENTER (com o editor fechado): abre o editor, se tiver um desafio esperando.
    def apertou_enter(self):
        desafio = self.desafio_ativo
        if desafio is None or not self.ja_alertou or self.resolvido:  # Nada para programar agora
            return
        if self.editor and self.editor.acabou_o_tempo():  # Já gastou o tempo deste desafio
            self.avisos.append(Aviso("SEM TEMPO! DESVIE COMO PUDER", COR_DO_ALERTA))
            return
        if self.editor is None:  # Primeira vez neste desafio: cria o editor
            no_tutorial = self.etapa_do_tutorial == "mostrando"
            self.editor = EditorDeCodigo(
                desafio.objeto, desafio.atributo, desafio.minimo, desafio.maximo, desafio.codigo_pronto(),
                desafio.explicacao if no_tutorial else desafio.dica(),
                None if no_tutorial else SEGUNDOS_NO_EDITOR,  # No tutorial não tem limite de tempo
            )
        self.editor_aberto = True
        if self.etapa_do_tutorial == "mostrando":
            self.etapa_do_tutorial = "editando"
        pygame.key.start_text_input()  # Garante que o pygame vai mandar as letras digitadas (evento TEXTINPUT)

    # ESC com o editor aberto: fecha sem perder o que foi digitado (o tempo restante continua o mesmo).
    def fechar_editor(self):
        if not self.resolvido:
            self.editor_aberto = False
            if self.etapa_do_tutorial == "editando":
                self.etapa_do_tutorial = "mostrando"

    # O teclado vai para o editor só enquanto ele está aberto E o visitante ainda não acertou.
    # Depois do acerto o "OK!" continua aparecendo, mas o espaço já volta a fazer o pássaro pular.
    def editor_recebe_teclado(self):
        return self.editor_aberto and not self.resolvido

    def editor_para_mostrar(self):  # O editor que o painel deve desenhar (ou None)
        return self.editor if self.editor_aberto else None

    # Linhas que o painel mostra quando o editor está fechado (None = a explicação normal).
    def mensagem_do_painel(self):
        desafio = self.desafio_ativo
        if desafio is None or not self.ja_alertou or self.resolvido or self.editor_aberto:
            return None
        if self.editor and self.editor.acabou_o_tempo():
            return [f"{desafio.alerta.capitalize()}", "O tempo do editor acabou. Desvie como puder!"]
        return [f"{desafio.alerta.capitalize()}", "Aperte ENTER para abrir o editor e programar.", "(ESC fecha o editor)"]

    def tratar_evento(self, evento):
        if self.editor and not self.resolvido:
            self.editor.tratar_evento(evento)

    # A câmera lenta (e a pausa) dependem do que está acontecendo.
    def escala_do_tempo(self):
        if self.etapa_do_tutorial in ("mostrando", "editando", "comemorando"):
            return 0.0  # Tutorial: jogo parado
        if self.desafio_ativo and self.ja_alertou and not self.resolvido:
            return ESCALA_DO_TEMPO_EDITANDO if self.editor_aberto else ESCALA_DO_TEMPO_DE_ALERTA
        return 1.0

    # O valor que o medidor do painel deve mostrar: durante o desafio, o valor do desafio; fora dele, o normal.
    def valor_para_o_medidor(self, nome_no_codigo, passaro, valor_normal):
        desafio = self.desafio_ativo
        if desafio and f"{desafio.objeto}.{desafio.atributo}" == nome_no_codigo:
            return desafio.valor_atual(passaro)
        return valor_normal

    # Desenha por cima do jogo (no monitor): o destaque piscando, a dica de ENTER e a prévia do resultado.
    def desenhar_no_jogo(self, monitor, area_do_jogo, fator_de_ampliacao, fonte):
        desafio = self.desafio_ativo
        if desafio is None or not self.ja_alertou:
            return

        def para_o_monitor(retangulo):  # Converte um retângulo da tela do jogo (144x256) para o monitor
            return pygame.Rect(area_do_jogo.x + retangulo.x * fator_de_ampliacao, area_do_jogo.y + retangulo.y * fator_de_ampliacao,
                               retangulo.width * fator_de_ampliacao, retangulo.height * fator_de_ampliacao)

        if not self.resolvido:
            area_do_problema = desafio.area_do_problema()
            if area_do_problema:  # Contorno amarelo pulsando em volta do problema
                pulso = (math.sin(self.tempo_total * 8) + 1) / 2  # Vai e volta entre 0 e 1, umas 1,3 vezes por segundo
                monitor.set_clip(area_do_jogo)
                pygame.draw.rect(monitor, COR_DA_DICA, para_o_monitor(area_do_problema).inflate(8, 8), width=2 + round(4 * pulso), border_radius=6)
                monitor.set_clip(None)

            if self.editor_aberto and self.editor.valor_da_previa is not None:  # Prévia ao vivo do que o visitante está digitando
                monitor.set_clip(area_do_jogo)
                desafio.desenhar_previa(monitor, para_o_monitor, self.editor.valor_da_previa)
                monitor.set_clip(None)

            if not self.editor_aberto:  # Dica de ENTER no pé do jogo (no tutorial ela não pisca)
                if self.editor and self.editor.acabou_o_tempo():
                    texto, cor = "SEM TEMPO! DESVIE!", COR_DO_ALERTA
                elif self.etapa_do_tutorial == "mostrando":
                    texto, cor = "Aperte ENTER para programar!", COR_DA_DICA
                else:
                    texto, cor = "ENTER = programar", COR_DA_DICA
                if self.etapa_do_tutorial == "mostrando" or self.tempo_total % 0.8 < 0.55:
                    caixa = criar_caixa(texto, cor, fonte)
                    monitor.blit(caixa, caixa.get_rect(midbottom=(area_do_jogo.centerx, area_do_jogo.bottom - 40 * fator_de_ampliacao)))


# MÉTODO AUXILIAR: um retângulo verde transparente com borda (para as prévias).
def desenhar_retangulo_transparente(monitor, retangulo, cor):
    camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)  # Imagem com transparência do tamanho do retângulo
    camada.fill((*cor, 70))  # Preenchimento quase transparente
    pygame.draw.rect(camada, cor, camada.get_rect(), width=3)  # Borda bem visível
    monitor.blit(camada, retangulo)
