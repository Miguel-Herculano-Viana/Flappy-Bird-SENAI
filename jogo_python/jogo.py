# ARQUIVO PRINCIPAL DO JOGO: é este que rodamos com "python jogo.py"

import random  # Ferramenta do Python para sortear números
from pathlib import Path  # Ferramenta do Python para montar caminhos de arquivos

import pygame  # Biblioteca de jogos que estamos usando

from avisos import Aviso  # Importa a CLASSE Aviso do arquivo avisos.py
from cano import VELOCIDADE_DO_CENARIO, Cano  # Importa a CLASSE Cano (e a velocidade dos canos) do arquivo cano.py
from chao import Chao  # Importa a CLASSE Chao do arquivo chao.py
from desafios import GerenciadorDeDesafios  # Importa a CLASSE que comanda os desafios de código
from modo_nave import ModoNave  # Importa a CLASSE do Modo Nave (o shooter)
from pos_processamento import PosProcessamento  # Bloom e vinheta
from painel import Painel  # Importa a CLASSE Painel do arquivo painel.py
from passaro import Passaro  # Importa a CLASSE Passaro do arquivo passaro.py
from placar import CAMINHO_DO_ARQUIVO_DO_RECORDE, CAMINHO_DO_ARQUIVO_DO_RECORDE_DA_NAVE, Placar  # Importa a CLASSE Placar (e onde ficam os recordes)

ALTURA_MINIMA_DA_TELA = 256  # O jogo tem pelo menos 256 pixels de altura (a largura e a altura certas dependem do monitor)
ALTURA_DO_CHAO = 32  # Altura da faixa de chão no pé da tela
CAMINHO_DA_IMAGEM_DO_FUNDO = Path(__file__).parent.parent / "src" / "assets" / "fundo.png"  # Céu com nuvens e cidade (144x224); é repetido na largura da tela
QUADROS_POR_SEGUNDO = 60  # Quantas vezes por segundo a tela é redesenhada
POSICAO_HORIZONTAL_DO_PASSARO = 48  # Onde o pássaro fica na horizontal
DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA = 48  # Para a abertura não ficar colada no topo ou no chão
DISTANCIA_ENTRE_OS_CANOS = 100  # Um novo par de canos aparece a cada 100 pixels que o cenário anda
ESCALA_DO_TEMPO_NORMAL = 1.0  # Velocidade normal do jogo (1.0 = tempo real; 0.5 seria metade da velocidade)
MILISSEGUNDOS_DE_ESPERA_PARA_RECOMECAR = 600  # Pausa no fim de jogo, para quem está apertando espaço sem parar conseguir ver o resultado
MARGEM_DO_PAINEL = 8  # Espaço (em pixels do jogo) entre o painel e a borda da tela
PARTE_DA_TELA_DO_PAINEL = 0.4  # O painel ocupa 40% da largura da tela...
LARGURA_MAXIMA_DO_PAINEL = 900  # ...mas, em monitores muito largos, não passa de 900 pixels do monitor
TAMANHO_DA_LETRA_DOS_AVISOS = 7  # Em pixels do jogo (é multiplicado pelo fator de ampliação)
PONTOS_ATE_A_NAVE = 3  # No Modo Nave, depois de passar 3 canos a nave aparece


# Cada modo de jogo tem o seu recorde, então o placar muda conforme o modo escolhido.
def criar_placar(modo):
    arquivo = CAMINHO_DO_ARQUIVO_DO_RECORDE_DA_NAVE if modo == "nave" else CAMINHO_DO_ARQUIVO_DO_RECORDE
    return Placar(area_livre.centerx, arquivo)  # Textos no meio da parte livre da tela


# Cria dois objetos Cano (o de cima e o de baixo) com uma abertura sorteada entre eles.
# "tamanho_da_abertura" é a altura do espaço por onde o pássaro passa.
def criar_par_de_canos(posicao_horizontal, tamanho_da_abertura):
    centro_da_abertura = random.randint(DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA, TOPO_DO_CHAO - DISTANCIA_MINIMA_DA_ABERTURA_ATE_A_BORDA)  # Sorteia a altura da abertura (entre o topo e o chão)
    metade_da_abertura = tamanho_da_abertura // 2  # Metade para cima do centro, metade para baixo
    cano_de_cima = Cano(posicao_horizontal, centro_da_abertura - metade_da_abertura, fica_em_cima=True)  # Nasce na posição pedida (perto da borda direita da tela)
    cano_de_baixo = Cano(posicao_horizontal, centro_da_abertura + metade_da_abertura, fica_em_cima=False)  # Mesmo molde, atributos diferentes
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
tela = pygame.Surface((LARGURA_DA_TELA, ALTURA_DA_TELA))  # O jogo é desenhado nesta imagem pequena e depois ampliado para o monitor
jogo_ampliado = pygame.Surface((LARGURA_DA_TELA * fator_de_ampliacao, ALTURA_DA_TELA * fator_de_ampliacao))  # Onde a imagem ampliada é guardada a cada quadro
area_do_jogo_no_monitor = jogo_ampliado.get_rect()  # O jogo começa no canto de cima do monitor e cobre tudo
pos_processamento = PosProcessamento(tela.get_size(), monitor.get_size())  # Os efeitos aplicados na imagem pronta

# PAINEL flutuando por cima do jogo, no canto direito, acima do chão (o chão passa por baixo dele)
margem_no_monitor = MARGEM_DO_PAINEL * fator_de_ampliacao
largura_do_painel = min(round(monitor.get_width() * PARTE_DA_TELA_DO_PAINEL), LARGURA_MAXIMA_DO_PAINEL)
painel_de_codigo = Painel(pygame.Rect(monitor.get_width() - largura_do_painel - margem_no_monitor, margem_no_monitor,
                                      largura_do_painel, TOPO_DO_CHAO * fator_de_ampliacao - 2 * margem_no_monitor), fator_de_ampliacao)
area_do_ceu = pygame.Rect(0, 0, LARGURA_DA_TELA, TOPO_DO_CHAO)  # Na tela do jogo: tudo acima do chão
area_livre = pygame.Rect(0, 0, painel_de_codigo.retangulo.x // fator_de_ampliacao, TOPO_DO_CHAO)  # A parte do céu que o painel não cobre
area_livre_no_monitor = pygame.Rect(0, 0, painel_de_codigo.retangulo.x, TOPO_DO_CHAO * fator_de_ampliacao)  # A mesma parte, no monitor
POSICAO_INICIAL_DO_PASSARO = (POSICAO_HORIZONTAL_DO_PASSARO, TOPO_DO_CHAO // 2)  # O pássaro começa no meio da altura do céu
fonte_dos_avisos = pygame.font.SysFont("consolas", TAMANHO_DA_LETRA_DOS_AVISOS * fator_de_ampliacao, bold=True)  # Letra dos avisos, proporcional ao tamanho do jogo no monitor
avisos_na_tela = []  # LISTA dos avisos (objetos Aviso) que estão aparecendo agora

# FUNDO: a imagem tem só 144 pixels de largura, então é repetida lado a lado até cobrir a tela,
# com o pé encostado no chão. O que sobra em cima é pintado com a cor do céu (a cor do topo da imagem).
pedaco_do_fundo = pygame.image.load(CAMINHO_DA_IMAGEM_DO_FUNDO).convert()  # Carrega o fundo (sem transparência)
imagem_do_fundo = pygame.Surface((LARGURA_DA_TELA, TOPO_DO_CHAO))
imagem_do_fundo.fill(pedaco_do_fundo.get_at((0, 0)))  # Cor do céu
for esquerda_do_pedaco in range(0, LARGURA_DA_TELA, pedaco_do_fundo.get_width()):  # Um pedaço a cada 144 pixels
    imagem_do_fundo.blit(pedaco_do_fundo, (esquerda_do_pedaco, TOPO_DO_CHAO - pedaco_do_fundo.get_height()))
relogio = pygame.time.Clock()  # Relógio que controla a velocidade do jogo

passaro_do_jogador = Passaro(POSICAO_INICIAL_DO_PASSARO)  # Cria um OBJETO a partir da classe Passaro
modo_escolhido = "desafios"  # Modo de jogo escolhido na tela de início: "desafios" ou "nave"
modo_nave = None  # O OBJETO do Modo Nave (só existe depois que a nave aparece)
placar_do_jogo = criar_placar(modo_escolhido)  # Cria um OBJETO a partir da classe Placar
chao_do_jogo = Chao(LARGURA_DA_TELA, ALTURA_DO_CHAO, TOPO_DO_CHAO)  # Cria um OBJETO a partir da classe Chao
todos_os_canos = pygame.sprite.Group()  # Grupo só com os canos, para testar a batida do pássaro
todos_os_objetos_do_jogo = pygame.sprite.Group(passaro_do_jogador)  # Grupo que atualiza e desenha o pássaro e os canos
gerenciador_de_desafios = GerenciadorDeDesafios(avisos_na_tela, placar_do_jogo, area_do_ceu, area_livre)  # Cria o OBJETO que decide quando aparecem os desafios de código

# O jogo está sempre em UMA destas situações (estados):
#   "inicio"   -> tela de início: o visitante escolhe o modo e o pássaro espera batendo as asas
#   "jogando"  -> a partida de Flappy está acontecendo
#   "nave"     -> Modo Nave: o shooter (quem cuida de tudo é o objeto modo_nave)
#   "fim"      -> o pássaro bateu, a cena congela e aparece o fim de jogo
estado_do_jogo = "inicio"  # Todo jogo começa na tela de início
jogo_esta_rodando = True  # Enquanto for True, a janela continua aberta
momento_em_que_o_jogo_acabou = 0  # Em que milissegundo o jogador perdeu (para contar a pausa antes de recomeçar)
distancia_desde_o_ultimo_cano = 0.0  # Quantos pixels o cenário andou desde o último par de canos
while jogo_esta_rodando:  # LAÇO DO JOGO: cada volta é um quadro
    tempo_do_quadro = relogio.tick(QUADROS_POR_SEGUNDO) / 1000  # Segundos REAIS que passaram desde o último quadro
    if estado_do_jogo == "jogando":  # Durante a partida, os desafios decidem a velocidade (câmera lenta ou pausa no tutorial)
        escala_do_tempo = gerenciador_de_desafios.escala_do_tempo()
    else:
        escala_do_tempo = ESCALA_DO_TEMPO_NORMAL
    tempo_do_jogo = tempo_do_quadro * escala_do_tempo  # Segundos que passaram DENTRO do jogo (em câmera lenta, passa menos tempo)

    for evento in pygame.event.get():  # Verifica tudo que aconteceu (teclas, cliques, fechar a janela, nosso evento)
        if evento.type == pygame.QUIT:  # Clicou no X da janela?
            jogo_esta_rodando = False
        if estado_do_jogo == "nave":  # MODO NAVE: os eventos vão todos para o objeto do modo
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if modo_nave.usa_o_teclado():  # Com o editor aberto, ESC fecha o editor
                    modo_nave.fechar_editor()
                else:  # Senão, sai do jogo
                    jogo_esta_rodando = False
            else:
                modo_nave.tratar_evento(evento)
            continue
        if estado_do_jogo == "inicio" and evento.type == pygame.KEYDOWN and evento.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_1, pygame.K_2):
            if evento.key == pygame.K_1:  # Escolhe o modo de jogo
                modo_escolhido = "desafios"
            elif evento.key == pygame.K_2:
                modo_escolhido = "nave"
            else:  # Setas: troca de um para o outro
                modo_escolhido = "nave" if modo_escolhido == "desafios" else "desafios"
            placar_do_jogo = criar_placar(modo_escolhido)  # Mostra o recorde do modo escolhido
            gerenciador_de_desafios = GerenciadorDeDesafios(avisos_na_tela, placar_do_jogo, area_do_ceu, area_livre)
        # EDITOR ABERTO: o teclado é todo do editor (o espaço vira letra, não pulo). O mouse continua pulando.
        if estado_do_jogo == "jogando" and gerenciador_de_desafios.editor_recebe_teclado() and evento.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:  # ESC fecha o editor (e não o jogo)
                gerenciador_de_desafios.fechar_editor()
            else:
                gerenciador_de_desafios.tratar_evento(evento)  # Letras, apagar, setas, ENTER...
            continue  # "continue" pula o resto do laço e vai para o próximo evento
        apertou_enter = evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER)  # ENTER do teclado ou do teclado numérico
        if apertou_enter and estado_do_jogo == "jogando":  # ENTER abre o editor, se tiver um desafio
            gerenciador_de_desafios.apertou_enter()
        apertou_esc = evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE  # Em tela cheia não tem o X da janela, então o ESC fecha o jogo
        if apertou_esc:  # Apertou ESC (com o editor fechado)?
            jogo_esta_rodando = False  # Então sai do laço e o jogo termina
        apertou_espaco = evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE  # Apertou a barra de espaço?
        clicou_com_botao_esquerdo = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1  # Clicou com o botão esquerdo?
        if apertou_espaco or clicou_com_botao_esquerdo:  # O que espaço ou clique fazem depende do estado do jogo
            if estado_do_jogo == "inicio":  # Na tela de início: começa a partida
                estado_do_jogo = "jogando"  # Muda o estado
                distancia_desde_o_ultimo_cano = 0.0  # Começa a contar a distância para o primeiro par de canos
                passaro_do_jogador.pular()  # A primeira apertada já é um pulo
            elif estado_do_jogo == "jogando":  # Durante a partida: pula
                passaro_do_jogador.pular()  # Chama o MÉTODO pular do objeto
            elif pygame.time.get_ticks() - momento_em_que_o_jogo_acabou >= MILISSEGUNDOS_DE_ESPERA_PARA_RECOMECAR:  # No fim de jogo, e a pausa já passou?
                todos_os_canos.empty()  # Tira todos os canos do grupo dos canos
                todos_os_objetos_do_jogo.empty()  # Esvazia o grupo geral
                passaro_do_jogador = Passaro(POSICAO_INICIAL_DO_PASSARO)  # Cria um pássaro NOVO, com os atributos do começo
                todos_os_objetos_do_jogo.add(passaro_do_jogador)  # Coloca o pássaro novo no grupo geral
                placar_do_jogo = criar_placar(modo_escolhido)  # Cria um placar NOVO: pontos voltam a zero e o recorde é lido do arquivo
                modo_nave = None  # O Modo Nave (se teve) também recomeça do zero
                painel_de_codigo.limpar_medidores()  # Cada modo mostra atributos diferentes no painel
                gerenciador_de_desafios = GerenciadorDeDesafios(avisos_na_tela, placar_do_jogo, area_do_ceu, area_livre)  # Desafios do zero: o próximo visitante vê os tutoriais
                estado_do_jogo = "inicio"  # Volta para a tela de início

    if estado_do_jogo == "inicio":  # Na tela de início, o pássaro só bate as asas, sem cair
        passaro_do_jogador.animar()  # Podemos chamar um método do objeto sozinho, sem o "update" inteiro
        chao_do_jogo.update(tempo_do_jogo)  # O chão já vai andando, como se o pássaro estivesse voando no lugar

    if estado_do_jogo == "jogando":  # Tudo isto só acontece durante a partida; no fim de jogo, a cena fica congelada
        todos_os_objetos_do_jogo.update(tempo_do_jogo)  # POLIMORFISMO: chama o "update" de cada objeto, e cada um faz o seu
        chao_do_jogo.update(tempo_do_jogo)  # O chão fica fora do grupo (ele é desenhado por cima dos canos), então atualizamos ele aqui

        # CANOS POR DISTÂNCIA (e não por relógio): em câmera lenta o cenário anda menos, então os canos também demoram mais para aparecer.
        # Com um relógio de verdade, eles continuariam nascendo no mesmo ritmo e ficariam amontoados.
        distancia_desde_o_ultimo_cano += VELOCIDADE_DO_CENARIO * tempo_do_jogo  # Soma o quanto o cenário andou neste quadro
        distancia_ate_o_proximo_par = gerenciador_de_desafios.distancia_ate_o_proximo_par(DISTANCIA_ENTRE_OS_CANOS)  # Normalmente 90, mas um desafio pode mudar
        if distancia_desde_o_ultimo_cano >= distancia_ate_o_proximo_par:  # Já andou o suficiente para um novo par?
            distancia_desde_o_ultimo_cano -= distancia_ate_o_proximo_par  # Guarda só o que passou da conta
            novos_canos = criar_par_de_canos(LARGURA_DA_TELA - distancia_desde_o_ultimo_cano, gerenciador_de_desafios.abertura_normal())  # Desconta o que passou, para o espaço entre os pares ficar sempre igual; a abertura diminui com o nível
            todos_os_canos.add(novos_canos)  # Coloca no grupo dos canos (para a batida)
            todos_os_objetos_do_jogo.add(novos_canos)  # E no grupo geral (para mover e desenhar)
            if modo_escolhido == "desafios":  # No Modo Nave, o começo é um Flappy normal, sem desafios
                gerenciador_de_desafios.novo_par_criado(novos_canos, passaro_do_jogador)  # Avisa o gerenciador: este par pode virar um desafio

        for cano in todos_os_canos:  # Olha cada cano que está na tela
            cano.animar(tempo_do_quadro)  # Desliza a borda e o deslocamento até o alvo (no tempo REAL, para ver o resultado na hora)
            if cano.vale_ponto and cano.rect.right < passaro_do_jogador.rect.centerx:  # O cano já ficou para trás do pássaro?
                placar_do_jogo.marcar_ponto()  # Ganha um ponto
                cano.vale_ponto = False  # Este cano já foi contado, não vale ponto de novo

        gerenciador_de_desafios.atualizar(tempo_do_quadro, passaro_do_jogador)  # Editor, tutorial, avisos (no tempo REAL)

        passaro_bateu_em_um_cano = pygame.sprite.spritecollideany(passaro_do_jogador, todos_os_canos, pygame.sprite.collide_mask)  # Só conta se os pixels desenhados se tocarem
        passaro_bateu_no_chao = pygame.sprite.collide_mask(passaro_do_jogador, chao_do_jogo)  # Mesmo teste, mas com o chão
        passaro_saiu_da_tela = not tela.get_rect().colliderect(passaro_do_jogador.rect)  # O pássaro subiu e saiu inteiro pelo topo da tela?

        if passaro_bateu_em_um_cano or passaro_bateu_no_chao or passaro_saiu_da_tela:  # Perdeu?
            estado_do_jogo = "fim"  # Congela o jogo e passa a mostrar o fim de jogo
            momento_em_que_o_jogo_acabou = pygame.time.get_ticks()  # Anota a hora, para a pausa antes de recomeçar
            placar_do_jogo.registrar_fim_de_jogo()  # O placar confere e guarda o recorde
        elif modo_escolhido == "nave" and placar_do_jogo.pontos >= PONTOS_ATE_A_NAVE:  # MODO NAVE: chegou a hora da nave aparecer!
            modo_nave = ModoNave(passaro_do_jogador, todos_os_canos, chao_do_jogo, pedaco_do_fundo, area_do_ceu, area_livre, avisos_na_tela, placar_do_jogo)
            painel_de_codigo.limpar_medidores()  # O painel passa a mostrar os atributos do Modo Nave
            estado_do_jogo = "nave"

    if estado_do_jogo == "nave":  # Modo Nave: o objeto do modo cuida de tudo
        modo_nave.atualizar(tempo_do_quadro)
        if modo_nave.acabou:  # O pássaro caiu (ou venceu o chefe final)
            estado_do_jogo = "fim"
            momento_em_que_o_jogo_acabou = pygame.time.get_ticks()
            placar_do_jogo.registrar_fim_de_jogo()

    if modo_nave:  # Modo Nave (jogando ou no fim): ele mesmo desenha o mundo
        modo_nave.desenhar(tela)
    else:
        tela.blit(imagem_do_fundo, (0, 0))  # Desenha o fundo, apagando o quadro anterior
        todos_os_objetos_do_jogo.draw(tela)  # Desenha cada objeto do grupo (usa o "image" e o "rect" deles)
        tela.blit(chao_do_jogo.image, chao_do_jogo.rect)  # O chão é desenhado depois, para tampar a ponta de baixo dos canos
    if estado_do_jogo == "inicio":  # Qual texto mostrar depende do estado
        placar_do_jogo.desenhar_tela_de_inicio(tela, modo_escolhido)  # Título, recorde, escolha do modo e "Aperte ESPAÇO"
    elif estado_do_jogo in ("jogando", "nave"):
        placar_do_jogo.desenhar(tela)  # Só os pontos no topo, na frente dos canos
    else:  # estado "fim"
        placar_do_jogo.desenhar_fim_de_jogo(tela)  # A tela de fim de jogo por cima da cena congelada

    # MEDIDORES: o painel mostra os atributos que o visitante pode mudar com código, sempre com o valor de agora.
    if modo_nave:  # O Modo Nave mostra os atributos dele
        modo_nave.atualizar_medidores(painel_de_codigo)
    else:
        painel_de_codigo.mostrar_valor("canos.abertura", gerenciador_de_desafios.valor_para_o_medidor("canos.abertura", passaro_do_jogador, gerenciador_de_desafios.abertura_normal()), maximo_da_barra=120)
        painel_de_codigo.mostrar_valor("canos.distancia", gerenciador_de_desafios.valor_para_o_medidor("canos.distancia", passaro_do_jogador, DISTANCIA_ENTRE_OS_CANOS), maximo_da_barra=150)
        painel_de_codigo.mostrar_valor("passaro.forca_da_gravidade", passaro_do_jogador.forca_da_gravidade, maximo_da_barra=1000)
        painel_de_codigo.mostrar_valor("passaro.forca_do_pulo", passaro_do_jogador.forca_do_pulo, maximo_da_barra=250)
    painel_de_codigo.atualizar(tempo_do_quadro)  # Anima as barras (no tempo real)
    for aviso in avisos_na_tela:  # Anima os avisos (no tempo real)
        aviso.atualizar(tempo_do_quadro)
    avisos_na_tela[:] = [aviso for aviso in avisos_na_tela if not aviso.acabou()]  # Tira da lista os avisos que já sumiram ("[:]" troca o conteúdo da MESMA lista, que o gerenciador também usa)

    if modo_nave:  # BLOOM só no Modo Nave: no céu escuro, tiros e explosões brilham (no céu claro do Flappy, tudo brilharia)
        pos_processamento.bloom(tela)
    pygame.transform.scale(tela, jogo_ampliado.get_size(), jogo_ampliado)  # Amplia o jogo pequeno (cada pixel vira um quadrado)
    monitor.blit(jogo_ampliado, (0, 0))  # Cobre o monitor inteiro, apagando o quadro anterior
    pos_processamento.aplicar_vinheta(monitor)  # Antes dos textos e do painel, que ficam nítidos por cima
    if estado_do_jogo == "jogando":
        gerenciador_de_desafios.desenhar_no_jogo(monitor, area_do_jogo_no_monitor, fator_de_ampliacao, fonte_dos_avisos)  # Destaque do problema, dica de ENTER, prévia
    if modo_nave:
        modo_nave.desenhar_no_monitor(monitor, fator_de_ampliacao)  # XP, vida do chefe e as cartas (com texto nítido)
    for posicao_na_fila, aviso in enumerate(avisos_na_tela):  # Avisos por cima do jogo, um embaixo do outro, no meio da parte livre
        aviso.desenhar(monitor, area_livre_no_monitor, fonte_dos_avisos, posicao_na_fila)
    if modo_nave:  # No Modo Nave, o painel mostra o script das armas
        editor_visivel = modo_nave.editor_para_mostrar()
        mensagem_do_painel = modo_nave.mensagem_do_painel()
    else:
        editor_visivel = gerenciador_de_desafios.editor_para_mostrar() if estado_do_jogo == "jogando" else None  # O editor só aparece durante a partida
        mensagem_do_painel = gerenciador_de_desafios.mensagem_do_painel() if estado_do_jogo == "jogando" else None  # Ex.: "Aperte ENTER para programar"
    painel_de_codigo.aberto = editor_visivel is not None or mensagem_do_painel is not None  # O painel só aparece quando tem algo para mostrar
    painel_de_codigo.texto_da_aba = "ENTER: código" if modo_nave and modo_nave.etapa == "jogando" else None
    painel_de_codigo.desenhar(monitor, editor_visivel, mensagem_do_painel)  # O painel é desenhado na resolução do monitor, por isso o texto fica nítido
    pygame.display.flip()  # Mostra na tela tudo que foi desenhado

pygame.quit()  # Desliga o pygame
