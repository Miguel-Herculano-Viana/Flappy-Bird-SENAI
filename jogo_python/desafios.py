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
from cano import VELOCIDADE_DO_CENARIO  # Para a prévia do pulo andar junto com o cenário
from editor import EditorDeCodigo  # O editor onde o visitante digita o código

# BALANCEAMENTO: mude estes números para deixar o jogo mais fácil ou mais difícil
PRIMEIRO_DESAFIO_NO_PAR = 2  # O primeiro desafio aparece no 2º par de canos
MENOR_INTERVALO_ENTRE_DESAFIOS = 2  # Depois de um desafio, o próximo vem entre 2...
MAIOR_INTERVALO_ENTRE_DESAFIOS = 3  # ...e 3 pares de canos
PARES_DE_ESPERA_DO_MESMO_DESAFIO = 4  # COOLDOWN: o mesmo desafio só volta depois de 4 pares
PONTOS_POR_NIVEL = 10  # A cada 10 pontos, o jogo sobe um nível de dificuldade
NIVEL_MAXIMO = 3  # Níveis 0, 1, 2 e 3 (na tela aparecem como 1, 2, 3 e 4)
ABERTURA_NORMAL_NO_FACIL = 80  # Abertura dos canos normais no nível mais fácil...
ABERTURA_NORMAL_NO_DIFICIL = 68  # ...e no mais difícil
SEGUNDOS_NO_EDITOR_NO_FACIL = 20  # Tempo para acertar o código (fora do tutorial) no nível mais fácil...
SEGUNDOS_NO_EDITOR_NO_DIFICIL = 10  # ...e no mais difícil
PONTOS_POR_DESAFIO = 2  # Bônus por resolver um desafio
ESCALA_DO_TEMPO_EDITANDO = 0.15  # Câmera lenta enquanto o editor está aberto
ESCALA_DO_TEMPO_DE_ALERTA = 0.5  # Câmera lenta leve quando o desafio aparece, para dar tempo de apertar ENTER
SEGUNDOS_MOSTRANDO_O_ACERTO = 1.5  # Quanto tempo o "OK!" fica no painel depois de acertar
SEGUNDOS_COMEMORANDO_NO_TUTORIAL = 2.0  # No tutorial, o jogo espera este tempo parado para o visitante ver o resultado
PARES_DE_DURACAO_DOS_EFEITOS = 3  # Gravidade pesada, pulo fraco e canos colados duram 3 pares de canos
DISTANCIA_DOS_CANOS_COLADOS = 45  # Distância entre os pares no desafio dos canos colados (o cano tem 32 de largura: sobra quase nada)
PASSOS_DA_PREVIA_DO_PULO = 24  # Quantos passos de futuro a prévia do pulo calcula
TEMPO_DE_CADA_PASSO_DA_PREVIA = 1 / 30  # Cada passo da prévia vale 1/30 de segundo
FOLGA_PARA_O_CANO_APARECER = 40  # O desafio só "aparece" quando o cano sai 40 pixels de trás do painel

COR_DO_ALERTA = (255, 110, 110)  # Vermelho
COR_DO_ACERTO = (120, 230, 120)  # Verde
COR_DA_DICA = (255, 210, 60)  # Amarelo
COR_DA_PREVIA = (120, 230, 120)  # Verde, para o contorno "fantasma" do resultado
COR_DE_VOLTA_AO_NORMAL = (120, 190, 255)  # Azul


class Desafio:

    # CONSTRUTOR
    #   objeto, atributo     -> o que o visitante muda (ex.: canos.abertura)
    #   minimo, maximo       -> faixa permitida (fora dela dá ValueError e o jogo não muda)
    #   alerta               -> texto do pop-up quando o desafio aparece
    #   explicacao           -> linhas do tutorial, mostradas na primeira vez
    #   pares_de_duracao     -> por quantos pares de canos o desafio dura (depois o jogo volta ao normal)
    #   faixa_no_dificil     -> (mínimo, máximo) no nível mais difícil: a faixa aperta para o jogo não ficar fácil demais
    def __init__(self, objeto, atributo, minimo, maximo, alerta, explicacao, pares_de_duracao, faixa_no_dificil):
        # ATRIBUTOS
        self.objeto = objeto
        self.atributo = atributo
        self.minimo = minimo
        self.maximo = maximo
        self.alerta = alerta
        self.explicacao = explicacao
        self.pares_de_duracao = pares_de_duracao
        self.minimo_no_dificil, self.maximo_no_dificil = faixa_no_dificil  # Separa a dupla em duas variáveis
        self.nivel_de_digitacao = 1  # 1 = só o valor; 2 = atributo e valor; 3 = a linha inteira
        self.pares = []  # Os pares de canos que fazem parte deste desafio (cada par é uma dupla: cano de cima, cano de baixo)
        self.passaro = None  # O pássaro da partida (guardado no começo do desafio)

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

    # MÉTODOS QUE AS CLASSES FILHAS PODEM SOBRESCREVER. Aqui fica o comportamento comum a todos os desafios.

    def comecar(self, passaro, par_de_canos):  # Cria o problema. As filhas chamam este com super() e depois criam o seu problema
        self.passaro = passaro
        self.pares = [par_de_canos]  # O desafio começa no par que acabou de nascer

    def novo_par(self, par_de_canos):  # Nasceu um par enquanto o desafio está ativo: ele entra no desafio se ainda couber
        if len(self.pares) < self.pares_de_duracao:
            self.pares.append(par_de_canos)

    def esta_visivel(self, x_visivel):  # O problema já aparece na tela? "x_visivel": um cano à esquerda deste x já aparece bem
        return True

    def aplicar(self, valor, passaro):  # Usa o valor digitado pelo visitante
        pass

    def terminou(self, passaro):  # O desafio passou quando o ÚLTIMO par dele ficou para trás do pássaro
        ultimo_cano = self.pares[-1][0]
        return len(self.pares) == self.pares_de_duracao and (ultimo_cano.rect.right < passaro.rect.left or not ultimo_cano.alive())

    def desfazer(self, passaro):  # Volta o jogo ao normal. Devolve o texto do aviso (ou None se não tinha nada para desfazer)
        return None

    def valor_atual(self, passaro):  # Valor do atributo agora (para os medidores e os avisos)
        return None

    def distancia_ate_o_proximo_par(self, distancia_normal):  # O desafio pode mudar onde nasce o próximo par
        return distancia_normal

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
        ], pares_de_duracao=1, faixa_no_dificil=(56, 80))
        self.centro = 0.0

    # SOBRESCRITA: fecha o par de canos que acabou de nascer. Os canos deslizam até se encostarem.
    def comecar(self, passaro, par_de_canos):
        super().comecar(passaro, par_de_canos)  # Primeiro, o que todo desafio faz
        cano_de_cima, cano_de_baixo = par_de_canos
        self.centro = (cano_de_cima.borda + cano_de_baixo.borda) / 2  # Meio da abertura
        cano_de_cima.mudar_borda(self.centro)  # As duas bordas vão para o meio...
        cano_de_baixo.mudar_borda(self.centro)  # ...e os canos se fecham

    def esta_visivel(self, x_visivel):
        return self.pares[0][0].rect.x <= x_visivel

    # Abre os canos com a abertura digitada, metade para cima e metade para baixo do meio.
    def aplicar(self, valor, passaro):
        cano_de_cima, cano_de_baixo = self.pares[0]
        cano_de_cima.mudar_borda(self.centro - valor / 2)
        cano_de_baixo.mudar_borda(self.centro + valor / 2)

    def valor_atual(self, passaro):
        cano_de_cima, cano_de_baixo = self.pares[0]
        return round(cano_de_baixo.borda_alvo - cano_de_cima.borda_alvo)  # Distância entre as duas bordas

    def area_do_problema(self):
        cano_de_cima, cano_de_baixo = self.pares[0]
        return cano_de_cima.rect.union(cano_de_baixo.rect)

    # Contorno verde de onde a abertura vai ficar.
    def desenhar_previa(self, monitor, para_o_monitor, valor):
        cano_de_cima = self.pares[0][0]
        abertura = pygame.Rect(cano_de_cima.rect.x, round(self.centro - valor / 2), cano_de_cima.rect.width, round(valor))  # Na tela do jogo
        desenhar_retangulo_transparente(monitor, para_o_monitor(abertura), COR_DA_PREVIA)


# Um desafio que estraga um atributo do PÁSSARO por alguns pares de canos (gravidade pesada, pulo fraco).
# Repare que é UMA classe só, usada duas vezes com dados diferentes (veja o GerenciadorDeDesafios).
class DesafioDoPassaro(Desafio):

    # "valor_ruim" é o valor que o atributo recebe quando o desafio começa (ex.: gravidade 800).
    def __init__(self, atributo, valor_ruim, minimo, maximo, faixa_no_dificil, alerta, explicacao):
        super().__init__("passaro", atributo, minimo, maximo, alerta, explicacao, PARES_DE_DURACAO_DOS_EFEITOS, faixa_no_dificil)
        self.valor_ruim = valor_ruim
        self.valor_normal = None  # Guardado no começo, para voltar ao normal no fim

    # getattr e setattr leem e mudam um atributo pelo NOME (um texto). É o que o editor "faria" com o código digitado.
    def comecar(self, passaro, par_de_canos):
        super().comecar(passaro, par_de_canos)
        self.valor_normal = getattr(passaro, self.atributo)  # Ex.: lê passaro.forca_da_gravidade
        setattr(passaro, self.atributo, self.valor_ruim)  # Ex.: passaro.forca_da_gravidade = 800

    def aplicar(self, valor, passaro):
        setattr(passaro, self.atributo, valor)  # Aqui o código do visitante vira realidade

    def desfazer(self, passaro):
        setattr(passaro, self.atributo, self.valor_normal)
        return f"{self.atributo} voltou ao normal: {round(self.valor_normal)}"

    def valor_atual(self, passaro):
        return round(getattr(passaro, self.atributo))

    def area_do_problema(self):
        return self.passaro.rect.inflate(-14, -14)  # O desenho do pássaro tem bastante sobra transparente em volta

    # PRÉVIA: desenha pontinhos mostrando o caminho de um pulo com o valor que está sendo digitado.
    # É a mesma conta que o pássaro faz (passaro.py), só que feita de antemão, alguns quadros no futuro.
    def desenhar_previa(self, monitor, para_o_monitor, valor):
        gravidade = valor if self.atributo == "forca_da_gravidade" else self.passaro.forca_da_gravidade
        pulo = valor if self.atributo == "forca_do_pulo" else self.passaro.forca_do_pulo
        x, y = float(self.passaro.rect.centerx), self.passaro.posicao_vertical
        velocidade = -pulo  # Começa com um pulo
        for passo in range(PASSOS_DA_PREVIA_DO_PULO):
            velocidade = min(velocidade + gravidade * TEMPO_DE_CADA_PASSO_DA_PREVIA, self.passaro.velocidade_maxima_de_queda)
            y += velocidade * TEMPO_DE_CADA_PASSO_DA_PREVIA
            x += VELOCIDADE_DO_CENARIO * TEMPO_DE_CADA_PASSO_DA_PREVIA  # O cenário anda; em relação a ele, o pássaro vai para a direita
            if passo % 2 == 0:  # Um pontinho a cada dois passos
                ponto = para_o_monitor(pygame.Rect(round(x), round(y), 1, 1))
                pygame.draw.circle(monitor, COR_DA_PREVIA, ponto.center, max(3, ponto.width // 2))


# CANOS COLADOS: uma "onda" de pares nasce quase encostada. O visitante muda a distância e eles se afastam.
class DesafioCanosColados(Desafio):

    def __init__(self):
        super().__init__("canos", "distancia", 80, 130, "CANOS COLADOS!", [
            "Os canos vieram colados! Não dá para passar entre eles.",
            "'distancia' é o ATRIBUTO com o espaço entre um par de canos e o próximo.",
            "Quanto MAIOR o número, mais espaço para voar.",
            "Digite um número e aperte ENTER.",
        ], pares_de_duracao=PARES_DE_DURACAO_DOS_EFEITOS, faixa_no_dificil=(80, 110))
        self.valor_aceito = None  # A distância digitada (None enquanto o visitante não acertar)
        self.ja_nasceu_o_par_depois_da_onda = False

    def comecar(self, passaro, par_de_canos):
        super().comecar(passaro, par_de_canos)
        self.valor_aceito = None
        self.ja_nasceu_o_par_depois_da_onda = False

    # Cada par novo da onda já nasce empurrado para o lugar certo, se o visitante já tiver acertado.
    def novo_par(self, par_de_canos):
        if len(self.pares) >= self.pares_de_duracao:  # A onda já está completa: este é o primeiro par normal depois dela
            self.ja_nasceu_o_par_depois_da_onda = True
        super().novo_par(par_de_canos)
        if self.valor_aceito is not None:
            self.aplicar(self.valor_aceito, self.passaro)

    # Enquanto a onda nasce, os pares vêm colados. Depois dela, o próximo par respeita o empurrão do último.
    def distancia_ate_o_proximo_par(self, distancia_normal):
        if len(self.pares) < self.pares_de_duracao:
            return DISTANCIA_DOS_CANOS_COLADOS
        if not self.ja_nasceu_o_par_depois_da_onda:
            return distancia_normal + self.pares[-1][0].deslocamento_alvo  # Para o par seguinte não nascer em cima do último da onda
        return distancia_normal

    def esta_visivel(self, x_visivel):  # O problema aparece quando o 2º par (o primeiro colado) aparece
        return len(self.pares) >= 2 and self.pares[1][0].rect.x <= x_visivel

    # Empurra cada par da onda para a direita, para que fiquem a "valor" pixels um do outro (deslizando).
    def aplicar(self, valor, passaro):
        self.valor_aceito = valor
        for posicao_na_onda, (cano_de_cima, cano_de_baixo) in enumerate(self.pares):
            empurrao = posicao_na_onda * (valor - DISTANCIA_DOS_CANOS_COLADOS)  # O 1º não anda, o 2º anda um pouco, o 3º anda o dobro
            cano_de_cima.mudar_deslocamento(empurrao)
            cano_de_baixo.mudar_deslocamento(empurrao)

    def desfazer(self, passaro):
        return "canos.distancia voltou ao normal"

    def valor_atual(self, passaro):
        return self.valor_aceito if self.valor_aceito is not None else DISTANCIA_DOS_CANOS_COLADOS

    def area_do_problema(self):
        area = self.pares[0][0].rect.union(self.pares[0][1].rect)
        for cano_de_cima, cano_de_baixo in self.pares[1:]:
            area = area.union(cano_de_cima.rect).union(cano_de_baixo.rect)
        return area

    # Contornos verdes de onde cada par da onda vai ficar.
    def desenhar_previa(self, monitor, para_o_monitor, valor):
        for posicao_na_onda, (cano_de_cima, _) in enumerate(self.pares):
            x_final = cano_de_cima.posicao_horizontal + posicao_na_onda * (valor - DISTANCIA_DOS_CANOS_COLADOS)
            lugar = pygame.Rect(round(x_final), 0, cano_de_cima.rect.width, cano_de_cima.rect.height * 2)  # Da altura da tela toda (o que passar é recortado)
            desenhar_retangulo_transparente(monitor, para_o_monitor(lugar), COR_DA_PREVIA)


class GerenciadorDeDesafios:

    # CONSTRUTOR: recebe a lista de avisos (para mostrar pop-ups) e o placar (para dar o bônus).
    #   area_do_ceu  -> retângulo da tela do jogo acima do chão
    #   area_livre   -> a parte do céu que o painel não cobre (onde ficam as dicas)
    # Cada partida cria um gerenciador novo, então cada visitante vê os tutoriais desde o começo.
    def __init__(self, avisos, placar, area_do_ceu, area_livre):
        # ATRIBUTOS
        self.avisos = avisos
        self.placar = placar
        self.area_do_ceu = area_do_ceu
        self.area_livre = area_livre
        self.desafios = [  # Na ordem em que aparecem pela primeira vez
            DesafioCanosFechados(),
            DesafioDoPassaro("forca_da_gravidade", 800, 350, 550, (420, 550), "GRAVIDADE PESADA!", [
                "A gravidade ficou pesada! O pássaro cai rápido demais.",
                "'passaro' é um OBJETO e 'forca_da_gravidade' é um ATRIBUTO dele.",
                "Quanto MENOR o número, mais devagar o pássaro cai.",
                "Digite um número e aperte ENTER.",
            ]),
            DesafioDoPassaro("forca_do_pulo", 110, 140, 190, (140, 175), "PULO FRACO!", [
                "O pulo ficou fraco! O pássaro quase não sobe.",
                "'forca_do_pulo' é o ATRIBUTO com a força de cada pulo.",
                "Quanto MAIOR o número, mais alto o pássaro pula.",
                "Digite um número e aperte ENTER.",
            ]),
            DesafioCanosColados(),
        ]
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
        self.nivel_anunciado = 0  # Último nível de dificuldade avisado ao visitante

    # MÉTODOS

    # Chamado pelo jogo cada vez que nasce um par de canos. É aqui que um desafio novo pode começar.
    def novo_par_criado(self, par_de_canos, passaro):
        for desafio in self.pares_de_espera:  # Cada par novo diminui o cooldown de todos
            self.pares_de_espera[desafio] -= 1
        if self.desafio_ativo:  # Já tem um desafio acontecendo: o par pode fazer parte dele
            self.desafio_ativo.novo_par(par_de_canos)
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
        if self.nivel_de_dificuldade() > self.nivel_anunciado:  # Subiu de nível: avisa (deixar claro que algo mudou)
            self.nivel_anunciado = self.nivel_de_dificuldade()
            self.avisos.append(Aviso(f"NÍVEL {self.nivel_anunciado + 1}: O JOGO APERTOU!", COR_DA_DICA, segundos=3.5))
        desafio = self.desafio_ativo
        if desafio is None:
            return

        if not self.ja_alertou and desafio.esta_visivel(self.area_livre.right - FOLGA_PARA_O_CANO_APARECER):  # O problema acabou de aparecer (saiu de trás do painel)
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
        texto_do_aviso = desafio.desfazer(passaro)  # POLIMORFISMO: cada desafio desfaz o seu efeito
        if texto_do_aviso:
            self.avisos.append(Aviso(texto_do_aviso, COR_DE_VOLTA_AO_NORMAL))
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
                desafio.objeto, desafio.atributo,
                self.misturar(desafio.minimo, desafio.minimo_no_dificil), self.misturar(desafio.maximo, desafio.maximo_no_dificil),  # A faixa aperta com o nível
                desafio.codigo_pronto(),
                desafio.explicacao if no_tutorial else desafio.dica(),
                None if no_tutorial else self.misturar(SEGUNDOS_NO_EDITOR_NO_FACIL, SEGUNDOS_NO_EDITOR_NO_DIFICIL),  # No tutorial não tem limite de tempo
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

    # Onde nasce o próximo par de canos: normalmente na distância de sempre, mas um desafio pode mudar.
    def distancia_ate_o_proximo_par(self, distancia_normal):
        if self.desafio_ativo:
            return self.desafio_ativo.distancia_ate_o_proximo_par(distancia_normal)
        return distancia_normal

    # DIFICULDADE ADAPTATIVA: o nível sobe com os pontos (0 a 9 pontos = nível 0, 10 a 19 = nível 1...).
    def nivel_de_dificuldade(self):
        return min(NIVEL_MAXIMO, self.placar.pontos // PONTOS_POR_NIVEL)

    # Escolhe um valor entre o do nível fácil e o do difícil, de acordo com o nível atual.
    # Ex.: misturar(80, 68) dá 80 no nível 0, 76 no 1, 72 no 2 e 68 no 3.
    def misturar(self, valor_no_facil, valor_no_dificil):
        return round(valor_no_facil + (valor_no_dificil - valor_no_facil) * self.nivel_de_dificuldade() / NIVEL_MAXIMO)

    def abertura_normal(self):  # Abertura dos canos que não são desafio
        return self.misturar(ABERTURA_NORMAL_NO_FACIL, ABERTURA_NORMAL_NO_DIFICIL)

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
            ceu_no_monitor = para_o_monitor(self.area_do_ceu)  # Destaques e prévias ficam só no céu (não passam por cima do chão)
            if area_do_problema:  # Contorno amarelo pulsando em volta do problema
                pulso = (math.sin(self.tempo_total * 8) + 1) / 2  # Vai e volta entre 0 e 1, umas 1,3 vezes por segundo
                monitor.set_clip(ceu_no_monitor)
                pygame.draw.rect(monitor, COR_DA_DICA, para_o_monitor(area_do_problema.clip(self.area_do_ceu)).inflate(8, 8), width=2 + round(4 * pulso), border_radius=6)
                monitor.set_clip(None)

            if self.editor_aberto and self.editor.valor_da_previa is not None:  # Prévia ao vivo do que o visitante está digitando
                monitor.set_clip(ceu_no_monitor)
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
                    livre_no_monitor = para_o_monitor(self.area_livre)
                    monitor.blit(caixa, caixa.get_rect(midbottom=(livre_no_monitor.centerx, livre_no_monitor.bottom - 16 * fator_de_ampliacao)))  # No meio da parte livre, acima do chão


# MÉTODO AUXILIAR: um retângulo verde transparente com borda (para as prévias).
def desenhar_retangulo_transparente(monitor, retangulo, cor):
    camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)  # Imagem com transparência do tamanho do retângulo
    camada.fill((*cor, 70))  # Preenchimento quase transparente
    pygame.draw.rect(camada, cor, camada.get_rect(), width=3)  # Borda bem visível
    monitor.blit(camada, retangulo)
