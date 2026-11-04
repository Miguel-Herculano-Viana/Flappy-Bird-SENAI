# ARQUIVO PRINCIPAL DO JOGO: é este que rodamos com "python jogo.py"

import random  # Ferramenta do Python para sortear números
from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

from cano import Cano  # Importa a CLASSE Cano do arquivo cano.py
from chao import Chao  # Importa a CLASSE Chao do arquivo chao.py
from passaro import Passaro  # Importa a CLASSE Passaro do arquivo passaro.py
from placar import Placar  # Importa a CLASSE Placar do arquivo placar.py

ALTURA_MINIMA_DA_TELA = 256  # O jogo tem pelo menos 256 pixels de altura (a largura e a altura certas dependem do monitor)
ALTURA_DO_CHAO = 32  # Altura da faixa de chão no pé da tela
CAMINHO_DA_IMAGEM_DO_FUNDO = Path(__file__).parent.parent / "src" / "assets" / "fundo.png"  # Céu com nuvens e cidade (144x224); é repetido na largura da tela
QUADROS_POR_SEGUNDO = 60  # Quantas vezes por segundo a tela é redesenhada
POSICAO_HORIZONTAL_DO_PASSARO = 48  # Onde o pássaro fica na horizontal (a altura inicial é o meio do céu, calculada depois)
TAMANHO_DA_ABERTURA_ENTRE_OS_CANOS = 64  # Altura do espaço por onde o pássaro passa
DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA = 48  # Para a abertura não ficar colada no topo ou no chão
MILISSEGUNDOS_CANOS = 1500  # Um novo par de canos aparece a cada 1,5 segundo
MILISSEGUNDOS_DE_ESPERA_PARA_RECOMECAR = 600  # Pausa no fim de jogo, para quem está apertando espaço sem parar conseguir ver o resultado


# Cria dois objetos Cano (o de cima e o de baixo) com uma abertura sorteada entre eles.
def criar_par_de_canos():
    centro_da_abertura = random.randint(DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA, TOPO_DO_CHAO - DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA)  # Sorteia a altura da abertura (entre o topo e o chão)
    metade_da_abertura = TAMANHO_DA_ABERTURA_ENTRE_OS_CANOS // 2  # Metade para cima do centro, metade para baixo
    cano_de_cima = Cano(LARGURA_DA_TELA, centro_da_abertura - metade_da_abertura, fica_em_cima=True)  # Nasce logo depois da borda direita da tela
    cano_de_baixo = Cano(LARGURA_DA_TELA, centro_da_abertura + metade_da_abertura, fica_em_cima=False)  # Mesmo molde, atributos diferentes
    return cano_de_cima, cano_de_baixo  # Devolve os dois objetos criados


pygame.init()  # Liga o pygame
monitor = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Tela cheia, no tamanho real do monitor ("0, 0" = use o tamanho do monitor)
pygame.display.set_caption("Flappy Bird SENAI")  # Título da janela

# AMPLIAÇÃO POR UM NÚMERO INTEIRO: cada pixel do jogo vira um quadrado de "fator x fator" pixels no monitor.
# Com um número quebrado (ex.: 4,2) uns pixels ficariam maiores que outros e a pixel art ficaria torta.
fator_de_ampliacao = max(1, monitor.get_height() // ALTURA_MINIMA_DA_TELA)  # Ex.: 1080 // 256 = 4
# O TAMANHO DA TELA DO JOGO sai do monitor: o jogo ampliado cobre o monitor inteiro, sem faixas pretas.
# "-(-a // b)" é a divisão arredondando para CIMA (para não sobrar nenhuma faixinha sem desenho).
LARGURA_DA_TELA = -(-monitor.get_width() // fator_de_ampliacao)  # Ex.: 1920 / 4 = 480
ALTURA_DA_TELA = -(-monitor.get_height() // fator_de_ampliacao)  # Ex.: 1080 / 4 = 270
TOPO_DO_CHAO = ALTURA_DA_TELA - ALTURA_DO_CHAO  # Altura da tela onde o chão começa
POSICAO_INICIAL_DO_PASSARO = (POSICAO_HORIZONTAL_DO_PASSARO, TOPO_DO_CHAO // 2)  # Onde o pássaro aparece no começo do jogo: no meio do céu
tela = pygame.Surface((LARGURA_DA_TELA, ALTURA_DA_TELA))  # O jogo é desenhado nesta imagem pequena e depois ampliado para o monitor
jogo_ampliado = pygame.Surface((LARGURA_DA_TELA * fator_de_ampliacao, ALTURA_DA_TELA * fator_de_ampliacao))  # Onde a imagem ampliada é guardada a cada quadro

# FUNDO: a imagem tem só 144 pixels de largura, então é repetida lado a lado até cobrir a tela,
# com o pé encostado no chão. O que sobra em cima é pintado com a cor do céu (a cor do topo da imagem).
pedaco_do_fundo = pygame.image.load(CAMINHO_DA_IMAGEM_DO_FUNDO).convert()  # Carrega o fundo (sem transparência)
imagem_do_fundo = pygame.Surface((LARGURA_DA_TELA, TOPO_DO_CHAO))
imagem_do_fundo.fill(pedaco_do_fundo.get_at((0, 0)))  # Cor do céu
for esquerda_do_pedaco in range(0, LARGURA_DA_TELA, pedaco_do_fundo.get_width()):  # Um pedaço a cada 144 pixels
    imagem_do_fundo.blit(pedaco_do_fundo, (esquerda_do_pedaco, TOPO_DO_CHAO - pedaco_do_fundo.get_height()))
relogio = pygame.time.Clock()  # Relógio que controla a velocidade do jogo

EVENTO_DE_CRIAR_CANOS = pygame.event.custom_type()  # Cria um tipo de evento nosso, como se fosse uma "tecla" que o próprio jogo aperta

passaro_do_jogador = Passaro(POSICAO_INICIAL_DO_PASSARO)  # Cria um OBJETO a partir da classe Passaro
placar_do_jogo = Placar()  # Cria um OBJETO a partir da classe Placar
chao_do_jogo = Chao(LARGURA_DA_TELA, ALTURA_DO_CHAO, TOPO_DO_CHAO)  # Cria um OBJETO a partir da classe Chao
todos_os_canos = pygame.sprite.Group()  # Grupo só com os canos, para testar a batida do pássaro
todos_os_objetos_do_jogo = pygame.sprite.Group(passaro_do_jogador)  # Grupo que atualiza e desenha o pássaro e os canos

# O jogo está sempre em UMA destas três situações (estados):
#   "inicio"   -> tela de início, o pássaro fica parado batendo as asas esperando o jogador
#   "jogando"  -> a partida está acontecendo
#   "fim"      -> o pássaro bateu, a cena congela e aparece o fim de jogo
estado_do_jogo = "inicio"  # Todo jogo começa na tela de início
jogo_esta_rodando = True  # Enquanto for True, a janela continua aberta
momento_em_que_o_jogo_acabou = 0  # Em que milissegundo o jogador perdeu (para contar a pausa antes de recomeçar)
while jogo_esta_rodando:  # LAÇO DO JOGO: cada volta é um quadro
    tempo_do_quadro = relogio.tick(QUADROS_POR_SEGUNDO) / 1000  # Segundos que passaram desde o último quadro

    for evento in pygame.event.get():  # Verifica tudo que aconteceu (teclas, cliques, fechar a janela, nosso evento)
        apertou_esc = evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE  # Em tela cheia não tem o X da janela, então o ESC fecha o jogo
        if evento.type == pygame.QUIT or apertou_esc:  # Fechou a janela ou apertou ESC?
            jogo_esta_rodando = False  # Então sai do laço e o jogo termina
        if evento.type == EVENTO_DE_CRIAR_CANOS and estado_do_jogo == "jogando":  # Chegou a hora de um novo par de canos (e estamos jogando)?
            novos_canos = criar_par_de_canos()  # Cria os dois objetos Cano
            todos_os_canos.add(novos_canos)  # Coloca no grupo dos canos (para a batida)
            todos_os_objetos_do_jogo.add(novos_canos)  # E no grupo geral (para mover e desenhar)
        apertou_espaco = evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE  # Apertou a barra de espaço?
        clicou_com_botao_esquerdo = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1  # Clicou com o botão esquerdo?
        if apertou_espaco or clicou_com_botao_esquerdo:  # O que espaço ou clique fazem depende do estado do jogo
            if estado_do_jogo == "inicio":  # Na tela de início: começa a partida
                estado_do_jogo = "jogando"  # Muda o estado
                pygame.time.set_timer(EVENTO_DE_CRIAR_CANOS, MILISSEGUNDOS_CANOS)  # Liga a criação de canos, contando a partir de agora
                passaro_do_jogador.pular()  # A primeira apertada já é um pulo
            elif estado_do_jogo == "jogando":  # Durante a partida: pula
                passaro_do_jogador.pular()  # Chama o MÉTODO pular do objeto
            elif pygame.time.get_ticks() - momento_em_que_o_jogo_acabou >= MILISSEGUNDOS_DE_ESPERA_PARA_RECOMECAR:  # No fim de jogo, e a pausa já passou?
                todos_os_canos.empty()  # Tira todos os canos do grupo dos canos
                todos_os_objetos_do_jogo.empty()  # Esvazia o grupo geral
                passaro_do_jogador = Passaro(POSICAO_INICIAL_DO_PASSARO)  # Cria um pássaro NOVO, com os atributos do começo
                todos_os_objetos_do_jogo.add(passaro_do_jogador)  # Coloca o pássaro novo no grupo geral
                placar_do_jogo = Placar()  # Cria um placar NOVO: pontos voltam a zero e o recorde é lido do arquivo
                estado_do_jogo = "inicio"  # Volta para a tela de início

    if estado_do_jogo == "inicio":  # Na tela de início, o pássaro só bate as asas, sem cair
        passaro_do_jogador.animar()  # Podemos chamar um método do objeto sozinho, sem o "update" inteiro
        chao_do_jogo.update(tempo_do_quadro)  # O chão já vai andando, como se o pássaro estivesse voando no lugar

    if estado_do_jogo == "jogando":  # Tudo isto só acontece durante a partida; no fim de jogo, a cena fica congelada
        todos_os_objetos_do_jogo.update(tempo_do_quadro)  # POLIMORFISMO: chama o "update" de cada objeto, e cada um faz o seu
        chao_do_jogo.update(tempo_do_quadro)  # O chão fica fora do grupo (ele é desenhado por cima dos canos), então atualizamos ele aqui

        for cano in todos_os_canos:  # Olha cada cano que está na tela
            if cano.vale_ponto and cano.rect.right < passaro_do_jogador.rect.centerx:  # O cano já ficou para trás do pássaro?
                placar_do_jogo.marcar_ponto()  # Ganha um ponto
                cano.vale_ponto = False  # Este cano já foi contado, não vale ponto de novo

        passaro_bateu_em_um_cano = pygame.sprite.spritecollideany(passaro_do_jogador, todos_os_canos, pygame.sprite.collide_mask)  # Só conta se os pixels desenhados se tocarem
        passaro_bateu_no_chao = pygame.sprite.collide_mask(passaro_do_jogador, chao_do_jogo)  # Mesmo teste, mas com o chão
        passaro_saiu_da_tela = not tela.get_rect().colliderect(passaro_do_jogador.rect)  # O pássaro subiu e saiu inteiro pelo topo da tela?

        if passaro_bateu_em_um_cano or passaro_bateu_no_chao or passaro_saiu_da_tela:  # Perdeu?
            estado_do_jogo = "fim"  # Congela o jogo e passa a mostrar o fim de jogo
            momento_em_que_o_jogo_acabou = pygame.time.get_ticks()  # Anota a hora, para a pausa antes de recomeçar
            placar_do_jogo.registrar_fim_de_jogo()  # O placar confere e guarda o recorde

    tela.blit(imagem_do_fundo, (0, 0))  # Desenha o fundo, apagando o quadro anterior
    todos_os_objetos_do_jogo.draw(tela)  # Desenha cada objeto do grupo (usa o "image" e o "rect" deles)
    tela.blit(chao_do_jogo.image, chao_do_jogo.rect)  # O chão é desenhado depois, para tampar a ponta de baixo dos canos
    if estado_do_jogo == "inicio":  # Qual texto mostrar depende do estado
        placar_do_jogo.desenhar_tela_de_inicio(tela)  # Título, recorde e "Aperte ESPAÇO"
    elif estado_do_jogo == "jogando":
        placar_do_jogo.desenhar(tela)  # Só os pontos no topo, na frente dos canos
    else:  # estado "fim"
        placar_do_jogo.desenhar_fim_de_jogo(tela)  # A tela de fim de jogo por cima da cena congelada
    pygame.transform.scale(tela, jogo_ampliado.get_size(), jogo_ampliado)  # Amplia o jogo pequeno (cada pixel vira um quadrado)
    monitor.blit(jogo_ampliado, (0, 0))  # Cobre o monitor inteiro, apagando o quadro anterior
    pygame.display.flip()  # Mostra na tela tudo que foi desenhado

pygame.quit()  # Desliga o pygame
