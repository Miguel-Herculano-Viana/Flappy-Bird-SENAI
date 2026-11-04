# MODO NAVE
# Começa como Flappy Bird. Depois de alguns canos, uma nave aparece, explode os canos e foge para o fundo do céu.
# Aí o jogo vira um SHOOTER HORIZONTAL: o pássaro voa livre (setas ou WASD), atira sozinho e enfrenta ondas de naves e chefes.
# As armas são equipadas e ajustadas com um SCRIPT PYTHON, digitado com o jogo pausado (veja script_das_armas.py).
#
# A CLASSE ModoNave guarda tudo do modo e o jogo.py só repassa para ela os eventos, a atualização e o desenho.
# As ETAPAS do modo (como os "estados" do jogo.py):
#   "chegada"  -> a nave entra pela direita
#   "ataque"   -> a nave explode os canos, um por um
#   "fuga"     -> a nave encolhe e vai para o fundo do céu
#   "editando" -> jogo pausado, o visitante mexe no script das armas
#   "cartas"   -> jogo pausado, o visitante escolhe uma arma nova
#   "jogando"  -> o shooter em si
#   "derrota" / "vitoria" -> o fim (depois de alguns segundos, "acabou" vira True)

import math  # Ferramenta do Python com contas (seno)
import random  # Ferramenta do Python para sortear números
import re  # Ferramenta do Python para achar padrões em textos (usada para atualizar os limites no script)
import textwrap  # Quebra textos compridos em várias linhas (nas cartas)

import pygame  # Biblioteca de jogos que estamos usando

from armas import criar_todas_as_armas  # As quatro armas
from avisos import Aviso  # Pop-ups por cima do jogo
from editor_de_script import EditorDeScript  # O editor de várias linhas
from imagens import carregar_quadros  # Sprites do Modo Nave
from inimigos import Atirador, Batedor, ChefeAmarelo, ChefeVerde, ChefeVermelho, Coracao, Explosao, Tanque  # Os inimigos
from script_das_armas import conferir_script, resumo_do_orcamento  # Validação segura do script

# BALANCEAMENTO: mude estes números para deixar o modo mais fácil ou mais difícil
VELOCIDADE_DO_PASSARO = 130  # Pixels por segundo
VIDAS_DO_PASSARO = 5  # Corações
SEGUNDOS_INVENCIVEL = 2.0  # Depois de levar dano, o pássaro pisca e não leva dano de novo
VELOCIDADE_DO_FUNDO = 20  # O céu rola devagar para dar a sensação de voo
NIVEIS_QUE_DESBLOQUEIAM_ARMAS = (2, 5, 8)  # Nestes níveis o visitante escolhe uma arma nova
SEGUNDOS_ATE_CADA_CHEFE = (75, 165, 270)  # Tempo de jogo (sem contar as lutas) até cada chefe aparecer
INTERVALO_DAS_ONDAS_NO_COMECO = 3.5  # Segundos entre uma onda de inimigos e outra no começo...
INTERVALO_DAS_ONDAS_NO_FIM = 2.0  # ...e perto do chefe final
CUSTO_DE_CADA_INIMIGO = {"batedores": 2, "atirador": 3, "tanque": 6}  # Quanto cada um gasta da "verba de ameaça" de cada onda
SEGUNDOS_DA_CHEGADA = 1.6  # Duração da entrada da nave na cena do começo
SEGUNDOS_ENTRE_CANOS_EXPLODINDO = 0.18
SEGUNDOS_DA_FUGA = 1.6
ESCALA_DA_NAVE_NO_FUNDO = 0.25  # A nave fica com 25% do tamanho no fundo do céu
TRANSPARENCIA_DA_NAVE_NO_FUNDO = 130

COR_DO_ALERTA = (255, 110, 110)  # Vermelho
COR_DO_ACERTO = (120, 230, 120)  # Verde
COR_DA_DICA = (255, 210, 60)  # Amarelo
COR_DE_INFORMACAO = (120, 190, 255)  # Azul
COR_DO_COMENTARIO = (140, 200, 130)  # Verde claro
COR_DO_RAIO_DA_CENA = (255, 240, 150)  # O raio que explode os canos
COR_DO_VIDRO = (14, 20, 48)  # As cartas usam o mesmo visual do painel
COR_DO_CONTORNO = (58, 67, 52)
COR_DA_MOLDURA = (72, 148, 58)
COR_DA_BARRA_DE_VIDA = (230, 70, 70)
COR_DA_BARRA_DE_XP = (120, 190, 255)
COR_DO_FUNDO_DA_BARRA = (39, 45, 70)

CABECALHO_DO_TUTORIAL = "# SCRIPT das armas: mude os números e aperte ENTER."  # Comentários curtos: o editor não quebra linhas de código


class ModoNave:

    # CONSTRUTOR: recebe os objetos do Flappy que já estão na tela (o pássaro, os canos, o chão) e as áreas da tela.
    def __init__(self, passaro, canos, chao, pedaco_do_fundo, area_do_ceu, area_livre, avisos, placar):
        # ATRIBUTOS: o que veio do jogo
        self.passaro = passaro
        self.canos = canos
        self.chao = chao
        self.area_do_ceu = area_do_ceu  # Tela do jogo acima do chão
        self.area_livre = area_livre  # A parte do céu que o painel não cobre
        self.avisos = avisos
        self.placar = placar

        # O fundo que rola: o pedaço de 144 pixels repetido, com um pedaço a mais para não aparecer buraco ao rolar
        self.largura_do_pedaco = pedaco_do_fundo.get_width()
        self.fundo_rolante = pygame.Surface((area_do_ceu.width + self.largura_do_pedaco, area_do_ceu.height))
        self.fundo_rolante.fill(pedaco_do_fundo.get_at((0, 0)))
        for esquerda in range(0, self.fundo_rolante.get_width(), self.largura_do_pedaco):
            self.fundo_rolante.blit(pedaco_do_fundo, (esquerda, area_do_ceu.height - pedaco_do_fundo.get_height()))
        self.deslocamento_do_fundo = 0.0

        # Armas e script
        self.armas = criar_todas_as_armas()  # Dicionário: nome -> Arma
        self.desbloqueadas = ["blaster"]  # LISTA das armas que o visitante já ganhou
        self.equipadas = ["blaster"]  # LISTA das armas que estão atirando (no máximo 2)
        self.script = "\n".join([CABECALHO_DO_TUTORIAL, "# passaro.armas: LISTA das armas equipadas (máx. 2)", "passaro.armas = [blaster]"]
                                + self.armas["blaster"].linhas_do_script())
        self.editor = None  # O editor aberto (ou None)
        self.visualizacao = None  # O mesmo script, só para leitura, mostrado durante a partida
        self.cartas = []  # Nomes das armas oferecidas ao subir de nível
        self.carta_escolhida = 0

        # Grupos de sprites
        self.inimigos = pygame.sprite.Group()
        self.tiros_inimigos = pygame.sprite.Group()
        self.projeteis = pygame.sprite.Group()  # Os tiros do pássaro
        self.efeitos = pygame.sprite.Group()  # Explosões
        self.coracoes = pygame.sprite.Group()

        # Progresso
        self.nivel = 1
        self.xp = 0
        self.vidas = VIDAS_DO_PASSARO
        self.segundos_invencivel = 0.0
        self.relogio_dos_chefes = 0.0  # Só conta quando não tem chefe na tela
        self.espera_da_onda = 2.0
        self.indice_do_proximo_chefe = 0
        self.chefe = None
        self.etapa = "chegada"
        self.tempo_na_etapa = 0.0
        self.tempo_total = 0.0
        self.acabou = False  # Quando vira True, o jogo.py mostra o fim de jogo
        self.venceu = False

        # A nave-mãe da cena do começo (é o mesmo desenho do chefe final)
        self.quadros_da_nave_mae = carregar_quadros("chefe_amarelo_1", 128)
        self.posicao_da_nave_mae = pygame.Vector2(area_do_ceu.right + 70, area_livre.centery)
        self.comeco_da_nave_mae = pygame.Vector2(self.posicao_da_nave_mae)
        self.parada_da_nave_mae = pygame.Vector2(area_livre.right - 80, area_livre.centery)
        self.posicao_no_fundo = pygame.Vector2(area_livre.right * 0.8, 36)
        self.escala_da_nave_mae = 1.0
        self.nave_mae_no_fundo = False
        self.canos_para_explodir = sorted(canos, key=lambda cano: cano.rect.x)  # Da esquerda para a direita
        self.espera_do_proximo_cano = 0.0
        self.raio_da_cena = None  # (ponto, segundos que faltam) do raio que explode um cano

        self.posicao_do_passaro = pygame.Vector2(passaro.rect.center)
        self.altura_do_passaro_na_cena = passaro.rect.centery
        passaro.velocidade_vertical = 0.0  # Acabou a gravidade
        self.fontes = None  # Criadas na primeira vez que desenhar no monitor (dependem do tamanho da tela)
        self.avisos.append(Aviso("NAVE DESCONHECIDA!", COR_DO_ALERTA))

    # ------------------------------------------------------------------ ATUALIZAR

    def atualizar(self, tempo):
        self.tempo_total += tempo
        self.tempo_na_etapa += tempo
        if self.editor:
            self.editor.atualizar(tempo)  # Cursor piscando
        if self.etapa in ("chegada", "ataque", "fuga"):
            self.atualizar_cena(tempo)
        elif self.etapa == "jogando":
            self.atualizar_jogo(tempo)
        elif self.etapa in ("derrota", "vitoria"):
            self.efeitos.update(tempo)
            if self.tempo_na_etapa > (2.5 if self.etapa == "derrota" else 4.0):
                self.acabou = True
        if self.etapa != "derrota":  # O pássaro continua batendo as asas (até no pause, que é mais bonito)
            self.passaro.animar()
            self.passaro.inclinar()
            self.passaro.rect = self.passaro.image.get_rect(center=(round(self.posicao_do_passaro.x), round(self.posicao_do_passaro.y)))

    def mudar_de_etapa(self, etapa):
        self.etapa = etapa
        self.tempo_na_etapa = 0.0

    # A cena do começo: a nave chega, explode os canos e foge para o fundo.
    def atualizar_cena(self, tempo):
        self.posicao_do_passaro.y = self.altura_do_passaro_na_cena + 3 * math.sin(self.tempo_total * 3)  # O pássaro fica parado no ar, assustado
        if self.etapa == "chegada":
            progresso = min(1.0, self.tempo_na_etapa / SEGUNDOS_DA_CHEGADA)
            self.posicao_da_nave_mae = self.comeco_da_nave_mae.lerp(self.parada_da_nave_mae, 1 - (1 - progresso) ** 2)  # Chega freando
            if progresso >= 1:
                self.mudar_de_etapa("ataque")
        elif self.etapa == "ataque":
            self.espera_do_proximo_cano -= tempo
            if self.espera_do_proximo_cano <= 0 and self.canos_para_explodir:  # Explode o próximo cano
                cano = self.canos_para_explodir.pop(0)
                parte_visivel = cano.rect.clip(self.area_do_ceu)
                if parte_visivel.height > 0:
                    self.efeitos.add(Explosao(parte_visivel.center, "explosao_grande", 80, tamanho=56))
                    self.raio_da_cena = (parte_visivel.center, 0.12)
                cano.kill()
                self.espera_do_proximo_cano = SEGUNDOS_ENTRE_CANOS_EXPLODINDO
            if not self.canos_para_explodir and self.espera_do_proximo_cano < -0.5:
                self.avisos.append(Aviso("OS CANOS FORAM DESTRUÍDOS!", COR_DA_DICA))
                self.mudar_de_etapa("fuga")
        elif self.etapa == "fuga":
            progresso = min(1.0, self.tempo_na_etapa / SEGUNDOS_DA_FUGA)
            suave = 1 - (1 - progresso) ** 2
            self.posicao_da_nave_mae = self.parada_da_nave_mae.lerp(self.posicao_no_fundo, suave)
            self.escala_da_nave_mae = 1 - (1 - ESCALA_DA_NAVE_NO_FUNDO) * suave
            if progresso >= 1:
                self.nave_mae_no_fundo = True
                self.avisos.append(Aviso("VOCÊ GANHOU UM BLASTER!", COR_DO_ACERTO, segundos=3.5))
                self.abrir_editor(CABECALHO_DO_TUTORIAL)
        if self.raio_da_cena:
            ponto, segundos = self.raio_da_cena
            self.raio_da_cena = (ponto, segundos - tempo) if segundos > tempo else None
        self.efeitos.update(tempo)

    # O shooter em si.
    def atualizar_jogo(self, tempo):
        if self.chefe is None:
            self.relogio_dos_chefes += tempo

        # MOVIMENTO LIVRE: cada tecla soma ou tira 1 na direção; o vetor é "normalizado" para a diagonal não ser mais rápida
        teclas = pygame.key.get_pressed()
        direcao = pygame.Vector2((teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) - (teclas[pygame.K_LEFT] or teclas[pygame.K_a]),
                                 (teclas[pygame.K_DOWN] or teclas[pygame.K_s]) - (teclas[pygame.K_UP] or teclas[pygame.K_w]))
        if direcao.length() > 0:
            direcao = direcao.normalize()
        self.posicao_do_passaro += direcao * VELOCIDADE_DO_PASSARO * tempo
        self.posicao_do_passaro.x = max(10, min(self.posicao_do_passaro.x, self.area_livre.right - 24))  # Não entra embaixo do painel
        self.posicao_do_passaro.y = max(10, min(self.posicao_do_passaro.y, self.area_do_ceu.bottom - 10))
        self.passaro.velocidade_vertical = direcao.y * VELOCIDADE_DO_PASSARO  # Para o pássaro inclinar quando sobe ou desce
        self.passaro.rect.center = (round(self.posicao_do_passaro.x), round(self.posicao_do_passaro.y))

        self.deslocamento_do_fundo += VELOCIDADE_DO_FUNDO * tempo
        self.chao.update(tempo)
        for nome in self.equipadas:  # POLIMORFISMO: cada arma atira do seu jeito
            self.armas[nome].atualizar(tempo, self.passaro, self.inimigos, self.projeteis, self.area_do_ceu)
        self.diretor_de_ondas(tempo)

        self.inimigos.update(tempo, self.passaro, self.tiros_inimigos, self.area_do_ceu)
        self.tiros_inimigos.update(tempo, self.area_do_ceu)
        self.projeteis.update(tempo, self.area_do_ceu)
        self.efeitos.update(tempo)
        self.coracoes.update(tempo, self.area_do_ceu)

        # COLISÕES: tiros do pássaro x inimigos ("groupcollide" devolve um dicionário: projétil -> lista de inimigos que ele tocou)
        for projetil, atingidos in pygame.sprite.groupcollide(self.projeteis, self.inimigos, False, False).items():
            projetil.acertou(atingidos, self.inimigos, tempo, self.efeitos)  # POLIMORFISMO: tiro, míssil e laser acertam de jeitos diferentes
        for inimigo in list(self.inimigos):
            if inimigo.vida <= 0:
                self.derrotar(inimigo)

        # COLISÕES: pássaro x tiros e naves inimigas (com máscara: só conta se os pixels desenhados se tocarem)
        self.segundos_invencivel -= tempo
        if self.segundos_invencivel <= 0 and self.etapa == "jogando":
            tiros = [tiro for tiro in pygame.sprite.spritecollide(self.passaro, self.tiros_inimigos, False, pygame.sprite.collide_mask) if tiro.dano > 0]
            naves = pygame.sprite.spritecollide(self.passaro, self.inimigos, False, pygame.sprite.collide_mask)
            if tiros or naves:
                for tiro in tiros:
                    if tiro.some_ao_acertar:
                        tiro.kill()
                for nave in naves:
                    nave.levar_dano(5)  # Bater numa nave também machuca ela
                self.machucar_passaro()
        for _ in pygame.sprite.spritecollide(self.passaro, self.coracoes, True):  # Pegou um coração
            if self.vidas < VIDAS_DO_PASSARO:
                self.vidas += 1
                self.avisos.append(Aviso("+1 VIDA", COR_DO_ACERTO, segundos=1.5))

        if self.etapa == "jogando" and self.xp >= self.xp_necessario():
            self.subir_de_nivel()

    # O "DIRETOR": decide quando vem cada onda de inimigos e quando vem cada chefe.
    def diretor_de_ondas(self, tempo):
        if self.chefe:  # Durante a luta com um chefe, não vêm ondas
            return
        if self.indice_do_proximo_chefe < len(SEGUNDOS_ATE_CADA_CHEFE) and self.relogio_dos_chefes >= SEGUNDOS_ATE_CADA_CHEFE[self.indice_do_proximo_chefe]:
            self.chamar_chefe()
            return
        self.espera_da_onda -= tempo
        if self.espera_da_onda <= 0:
            progresso = min(1.0, self.relogio_dos_chefes / SEGUNDOS_ATE_CADA_CHEFE[-1])  # De 0 (começo) até 1 (chefe final)
            self.espera_da_onda = INTERVALO_DAS_ONDAS_NO_COMECO + (INTERVALO_DAS_ONDAS_NO_FIM - INTERVALO_DAS_ONDAS_NO_COMECO) * progresso
            self.criar_onda(verba=2 + self.relogio_dos_chefes / 20 + self.nivel * 0.5)

    # Gasta a "verba de ameaça" sorteando inimigos. Verba maior = onda mais difícil.
    def criar_onda(self, verba):
        multiplicador_de_vida = 1 + self.relogio_dos_chefes / 200  # Com o tempo, os inimigos aguentam mais
        x = self.area_do_ceu.right + 16
        while True:
            opcoes = [tipo for tipo, custo in CUSTO_DE_CADA_INIMIGO.items() if custo <= verba]
            if self.relogio_dos_chefes < 10 and "atirador" in opcoes:  # Bem no começo, só batedores
                opcoes.remove("atirador")
            if self.relogio_dos_chefes < 40 and "tanque" in opcoes:
                opcoes.remove("tanque")
            if not opcoes:
                break
            tipo = random.choice(opcoes)
            verba -= CUSTO_DE_CADA_INIMIGO[tipo]
            y = random.uniform(24, self.area_do_ceu.bottom - 24)
            if tipo == "batedores":  # Uma fila de 3 batedores
                for numero in range(3):
                    self.inimigos.add(Batedor((x + numero * 22, y), multiplicador_de_vida))
            elif tipo == "atirador":
                x_de_parada = random.uniform(self.area_livre.right * 0.55, self.area_livre.right - 20)
                self.inimigos.add(Atirador((x, y), x_de_parada, multiplicador_de_vida))
            else:
                self.inimigos.add(Tanque((x, y), multiplicador_de_vida))
            x += 40

    def chamar_chefe(self):
        numero = self.indice_do_proximo_chefe
        self.indice_do_proximo_chefe += 1
        entrada = (self.area_do_ceu.right + 70, self.area_do_ceu.centery)
        x_de_parada = self.area_livre.right - 75
        if numero == 0:
            self.chefe = ChefeVerde(entrada, x_de_parada)
        elif numero == 1:
            self.chefe = ChefeVermelho(entrada, x_de_parada)
        else:  # O chefe final é a nave-mãe, que sai do fundo do céu
            self.chefe = ChefeAmarelo(entrada, x_de_parada, self.posicao_no_fundo)
            self.nave_mae_no_fundo = False
        self.inimigos.add(self.chefe)
        self.avisos.append(Aviso(f"CUIDADO: {self.chefe.nome}!", COR_DO_ALERTA, segundos=3.0))

    def derrotar(self, inimigo):
        nome_da_explosao, largura = inimigo.explosao
        self.efeitos.add(Explosao(inimigo.rect.center, nome_da_explosao, largura))
        self.xp += inimigo.xp
        self.placar.marcar_ponto(inimigo.xp)
        if random.random() < inimigo.chance_de_coracao:
            self.coracoes.add(Coracao(inimigo.rect.center))
        inimigo.kill()
        if inimigo is self.chefe:
            for _ in range(6):  # Várias explosões espalhadas pelo chefe
                ponto = (inimigo.rect.centerx + random.uniform(-40, 40), inimigo.rect.centery + random.uniform(-25, 25))
                self.efeitos.add(Explosao(ponto, "explosao_grande", 80, tamanho=random.uniform(40, 80), quadros_por_segundo=random.uniform(12, 20)))
            for tiro in self.tiros_inimigos:  # Os tiros do chefe somem junto com ele
                tiro.kill()
            self.avisos.append(Aviso(f"{inimigo.nome} DERROTADO! +{inimigo.xp} XP", COR_DO_ACERTO, segundos=3.0))
            self.chefe = None
            if isinstance(inimigo, ChefeAmarelo):  # "isinstance" pergunta: este objeto é desta classe?
                self.venceu = True
                self.placar.titulo_do_fim = "VOCÊ VENCEU!"
                self.avisos.append(Aviso("VOCÊ SALVOU O CÉU!", COR_DA_DICA, segundos=4.0))
                self.mudar_de_etapa("vitoria")

    def machucar_passaro(self):
        self.vidas -= 1
        self.segundos_invencivel = SEGUNDOS_INVENCIVEL
        self.efeitos.add(Explosao(self.passaro.rect.center, "explosao_pequena", 16))
        if self.vidas <= 0:
            self.efeitos.add(Explosao(self.passaro.rect.center, "explosao_grande", 80, tamanho=64))
            self.avisos.append(Aviso("O PÁSSARO CAIU!", COR_DO_ALERTA, segundos=2.5))
            self.mudar_de_etapa("derrota")

    # ------------------------------------------------------------------ NÍVEIS, CARTAS E SCRIPT

    # Cada nível pede mais XP que o anterior (12, 29, 52, 81, 116...), para o editor não abrir toda hora.
    def xp_necessario(self):
        return 12 + 14 * (self.nivel - 1) + 3 * (self.nivel - 1) ** 2

    def subir_de_nivel(self):
        self.xp -= self.xp_necessario()
        self.nivel += 1
        self.avisos.append(Aviso(f"NÍVEL {self.nivel}!", COR_DA_DICA, segundos=3.0))
        bloqueadas = [nome for nome in self.armas if nome not in self.desbloqueadas]
        if self.nivel in NIVEIS_QUE_DESBLOQUEIAM_ARMAS and bloqueadas:  # Hora de escolher uma arma nova
            self.cartas = random.sample(bloqueadas, min(3, len(bloqueadas)))  # Até 3 armas sorteadas, sem repetir
            self.carta_escolhida = 0
            self.mudar_de_etapa("cartas")
            return
        mudancas = []
        for nome in self.desbloqueadas:  # Os outros níveis aumentam os limites das armas que o visitante já tem
            arma = self.armas[nome]
            antes = arma.limite
            arma.subir_limite()
            mudancas.append(f"{nome} {antes}->{arma.limite}")
            self.script = re.sub(rf"^# Limite do {nome}: .*$", f"# Limite do {nome}: {arma.texto_do_limite()}", self.script, flags=re.MULTILINE)  # Atualiza o comentário no script
        self.avisos.append(Aviso("LIMITES: " + ", ".join(mudancas), COR_DE_INFORMACAO, segundos=4.0))
        self.abrir_editor(f"# NÍVEL {self.nivel}! Limites maiores. Ajuste e dê ENTER.")

    def escolher_carta(self):
        nome = self.cartas[self.carta_escolhida]
        arma = self.armas[nome]
        self.desbloqueadas.append(nome)
        self.cartas = []
        self.script += "\n" + "\n".join([f"# NOVA ARMA: coloque {nome} em passaro.armas"] + arma.linhas_do_script())
        self.avisos.append(Aviso(f"NOVA ARMA: {arma.titulo}!", COR_DO_ACERTO, segundos=3.0))
        self.abrir_editor(f"# NÍVEL {self.nivel}! Nova arma: {nome}. Equipe e dê ENTER.")

    def abrir_editor(self, cabecalho):
        linhas = self.script.split("\n")
        if linhas and linhas[0].startswith("#"):  # A primeira linha é sempre o cabeçalho, que muda a cada vez
            linhas[0] = cabecalho
        else:
            linhas.insert(0, cabecalho)
        self.script = "\n".join(linhas)
        self.editor = EditorDeScript(self.script, self.conferir, self.rodape_do_editor)
        self.editor.linha_do_cursor = next((indice for indice, linha in enumerate(linhas) if not linha.startswith("#")), 0)  # Cursor na primeira linha de código
        self.mudar_de_etapa("editando")
        pygame.key.start_text_input()  # Garante que o pygame manda as letras digitadas (evento TEXTINPUT)

    def armas_desbloqueadas(self):
        return {nome: self.armas[nome] for nome in self.desbloqueadas}

    def conferir(self, texto):
        return conferir_script(texto, self.armas_desbloqueadas(), self.equipadas)

    # Linhas embaixo do editor: a conta de cada limite, ao vivo, verde se cabe e vermelha se passou.
    def rodape_do_editor(self):
        linhas = [("# Limites agora (atualiza enquanto você digita):", COR_DO_COMENTARIO)]
        for _, texto, cabe in resumo_do_orcamento(self.editor.texto(), self.armas_desbloqueadas()):
            linhas.append((("OK  " if cabe else "X   ") + texto, COR_DO_ACERTO if cabe else COR_DO_ALERTA))
        return linhas

    # O script rodou sem erro: as armas passam a usar os valores novos.
    def aplicar(self, configuracao, texto):
        for nome, valores in configuracao["valores"].items():
            self.armas[nome].valores = dict(valores)
        self.equipadas = configuracao["armas"]
        self.script = texto
        for nome in self.equipadas:
            arma = self.armas[nome]
            self.avisos.append(Aviso(f"{nome}: " + ", ".join(f"{parametro} {valor}" for parametro, valor in arma.valores.items()), COR_DO_ACERTO, segundos=3.0))
        self.editor = None
        self.visualizacao = None
        self.mudar_de_etapa("jogando")

    def tratar_evento(self, evento):
        if self.etapa == "editando" and self.editor:
            self.editor.tratar_evento(evento)
            if self.editor.resultado:  # O ENTER rodou o script e deu certo
                self.aplicar(self.editor.resultado, self.editor.texto())
        elif self.etapa == "cartas" and evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.carta_escolhida = (self.carta_escolhida - 1) % len(self.cartas)  # "%": dá a volta (da primeira vai para a última)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.carta_escolhida = (self.carta_escolhida + 1) % len(self.cartas)
            elif evento.key in (pygame.K_1, pygame.K_2, pygame.K_3) and evento.key - pygame.K_1 < len(self.cartas):
                self.carta_escolhida = evento.key - pygame.K_1
                self.escolher_carta()
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.escolher_carta()

    def usa_o_teclado(self):  # True = o ESC não deve fechar o jogo (o modo está usando o teclado)
        return self.etapa in ("editando", "cartas")

    def fechar_editor(self):  # ESC no editor: fecha sem mudar nada (as armas continuam como estavam)
        if self.etapa == "editando":
            self.editor = None
            self.mudar_de_etapa("jogando")

    # ------------------------------------------------------------------ PAINEL

    def editor_para_mostrar(self):
        if self.editor:
            return self.editor
        if not self.nave_mae_no_fundo and self.etapa in ("chegada", "ataque", "fuga"):
            return None
        if self.visualizacao is None:  # Durante a partida: o script só para leitura
            self.visualizacao = EditorDeScript(self.script, somente_leitura=True, rodape=lambda: [
                ("# Este script está controlando suas armas agora.", COR_DO_COMENTARIO),
                ("# Ele abre de novo quando você subir de nível.", COR_DO_COMENTARIO),
                ("# Setas ou WASD: voar. As armas atiram sozinhas.", COR_DO_COMENTARIO)])
        return self.visualizacao

    def mensagem_do_painel(self):
        if self.etapa in ("chegada", "ataque", "fuga"):
            return ["Uma nave desconhecida apareceu!", "Ela está destruindo os canos..."]
        return None

    def atualizar_medidores(self, painel):
        painel.mostrar_valor("passaro.vida", self.vidas, maximo_da_barra=VIDAS_DO_PASSARO)
        painel.mostrar_valor("passaro.xp", int(self.xp), maximo_da_barra=self.xp_necessario())

    # ------------------------------------------------------------------ DESENHAR

    # Desenha o mundo do jogo na tela pequena (pixel art).
    def desenhar(self, tela):
        tela.blit(self.fundo_rolante, (-round(self.deslocamento_do_fundo % self.largura_do_pedaco), 0))
        if self.nave_mae_no_fundo:  # A nave-mãe pequena e meio transparente, esperando no fundo do céu
            imagem = pygame.transform.scale_by(self.quadro_da_nave_mae(), ESCALA_DA_NAVE_NO_FUNDO)
            imagem.set_alpha(TRANSPARENCIA_DA_NAVE_NO_FUNDO)
            tela.blit(imagem, imagem.get_rect(center=(round(self.posicao_no_fundo.x), round(self.posicao_no_fundo.y + 3 * math.sin(self.tempo_total)))))
        self.canos.draw(tela)
        self.coracoes.draw(tela)
        self.inimigos.draw(tela)
        self.projeteis.draw(tela)
        self.tiros_inimigos.draw(tela)
        if self.etapa in ("chegada", "ataque", "fuga") and not self.nave_mae_no_fundo:  # A nave-mãe na cena do começo
            imagem = pygame.transform.scale_by(self.quadro_da_nave_mae(), self.escala_da_nave_mae)
            retangulo = imagem.get_rect(center=(round(self.posicao_da_nave_mae.x), round(self.posicao_da_nave_mae.y)))
            if self.raio_da_cena:  # O raio que acabou de explodir um cano
                pygame.draw.line(tela, COR_DO_RAIO_DA_CENA, (retangulo.left + 6, retangulo.centery), self.raio_da_cena[0], 3)
            tela.blit(imagem, retangulo)
        self.efeitos.draw(tela)
        piscando = self.segundos_invencivel > 0 and int(self.tempo_total * 12) % 2 == 0  # Invencível: aparece e some
        if self.etapa != "derrota" and not piscando:
            tela.blit(self.passaro.image, self.passaro.rect)
        tela.blit(self.chao.image, self.chao.rect)
        coracao = carregar_quadros("coracao", 16)[0]
        for numero in range(self.vidas):  # Corações no canto de cima
            tela.blit(coracao, (4 + numero * 13, 4))

    def quadro_da_nave_mae(self):
        return self.quadros_da_nave_mae[int(self.tempo_total * 8) % len(self.quadros_da_nave_mae)]

    # Desenha na resolução do monitor (texto nítido): XP, barra de vida do chefe e as cartas.
    def desenhar_no_monitor(self, monitor, fator):
        if self.fontes is None:
            self.fontes = {tamanho: pygame.font.SysFont("consolas", tamanho * fator, bold=True) for tamanho in (5, 6, 8)}
        livre = pygame.Rect(0, 0, self.area_livre.right * fator, self.area_livre.bottom * fator)

        # XP e nível, embaixo dos corações
        if self.etapa not in ("chegada", "ataque", "fuga"):
            barra = pygame.Rect(4 * fator, 20 * fator, 80 * fator, 3 * fator)
            pygame.draw.rect(monitor, COR_DO_FUNDO_DA_BARRA, barra)
            pygame.draw.rect(monitor, COR_DA_BARRA_DE_XP, (barra.x, barra.y, round(barra.width * min(1, self.xp / self.xp_necessario())), barra.height))
            pygame.draw.rect(monitor, COR_DO_CONTORNO, barra, width=max(1, fator // 2))
            texto = self.fontes[5].render(f"NÍVEL {self.nivel}   XP {int(self.xp)}/{self.xp_necessario()}", True, (255, 255, 255))
            monitor.blit(texto, (barra.x, barra.bottom + fator))

        # Barra de vida do chefe
        if self.chefe and self.chefe.alive():
            barra = pygame.Rect(0, 0, livre.width * 0.5, 4 * fator)
            barra.midtop = (livre.centerx, 54 * fator)  # Abaixo do número de pontos
            nome = self.fontes[6].render(self.chefe.nome, True, COR_DO_ALERTA)
            monitor.blit(nome, nome.get_rect(midbottom=(barra.centerx, barra.top - fator)))
            pygame.draw.rect(monitor, COR_DO_FUNDO_DA_BARRA, barra)
            pygame.draw.rect(monitor, COR_DA_BARRA_DE_VIDA, (barra.x, barra.y, round(barra.width * max(0, self.chefe.vida) / self.chefe.vida_maxima), barra.height))
            pygame.draw.rect(monitor, COR_DO_CONTORNO, barra, width=max(1, fator // 2))

        if self.etapa == "cartas":
            self.desenhar_cartas(monitor, livre, fator)

    # As cartas de escolha de arma, no visual do painel (vidro azul, moldura de cano).
    def desenhar_cartas(self, monitor, livre, fator):
        escurecer = pygame.Surface(livre.size, pygame.SRCALPHA)
        escurecer.fill((0, 0, 0, 120))
        monitor.blit(escurecer, livre)
        titulo = self.fontes[8].render(f"NÍVEL {self.nivel}! ESCOLHA UMA ARMA NOVA", True, COR_DA_DICA)
        monitor.blit(titulo, titulo.get_rect(midtop=(livre.centerx, livre.height * 0.27)))  # Abaixo dos avisos
        largura, altura = round(livre.width * 0.27), round(livre.height * 0.5)
        espaco = round(livre.width * 0.03)
        esquerda = livre.centerx - (len(self.cartas) * largura + (len(self.cartas) - 1) * espaco) // 2
        for numero, nome in enumerate(self.cartas):
            arma = self.armas[nome]
            escolhida = numero == self.carta_escolhida
            carta = pygame.Rect(esquerda + numero * (largura + espaco), livre.height * 0.34 - (3 * fator if escolhida else 0), largura, altura)  # A escolhida fica um pouco mais alta
            fundo = pygame.Surface(carta.size, pygame.SRCALPHA)
            fundo.fill((*COR_DO_VIDRO, 235))
            monitor.blit(fundo, carta)
            pygame.draw.rect(monitor, COR_DO_CONTORNO, carta, width=fator)
            pygame.draw.rect(monitor, COR_DA_DICA if escolhida else COR_DA_MOLDURA, carta.inflate(-2 * fator, -2 * fator), width=fator)
            y = carta.top + 4 * fator
            texto = self.fontes[8].render(f"{numero + 1}. {arma.titulo}", True, COR_DA_DICA if escolhida else (255, 255, 255))
            monitor.blit(texto, texto.get_rect(midtop=(carta.centerx, y)))
            y += texto.get_height() + 3 * fator
            icone = pygame.transform.scale_by(arma.icone(), fator * 2)
            monitor.blit(icone, icone.get_rect(midtop=(carta.centerx, y)))
            y += icone.get_height() + 4 * fator
            letras_por_linha = (carta.width - 8 * fator) // self.fontes[5].size("a")[0]  # Quantas letras cabem na largura da carta
            linhas = [(parte, (220, 225, 240)) for linha in arma.descricao for parte in textwrap.wrap(linha, letras_por_linha)]
            linhas += [("", None)] + [(parte, COR_DE_INFORMACAO) for parte in textwrap.wrap("Limite: " + arma.texto_do_limite(), letras_por_linha)]
            for linha, cor in linhas:
                if cor:
                    monitor.blit(self.fontes[5].render(linha, True, cor), (carta.left + 4 * fator, y))
                y += self.fontes[5].get_height() + fator
        dica = self.fontes[6].render("<- -> escolhe    ENTER confirma (ou aperte 1, 2, 3)", True, (255, 255, 255))
        monitor.blit(dica, dica.get_rect(midtop=(livre.centerx, livre.height * 0.34 + altura + 6 * fator)))
