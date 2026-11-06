# CLASSE TUTORIAL DIGITADO
# Um "professor" que escreve no editor sozinho, letra por letra, como se alguém estivesse digitando ao vivo.
# Ele explica com comentários (#) e depois pede para o visitante digitar uma linha de código.
# O visitante digita e aperta ENTER: se a linha estiver certa, o professor continua; se não, ele dá uma dica.
#
# Cada PASSO é um dicionário com:
#   "falar"    -> lista de comentários que o professor digita
#   "conferir" -> (opcional) FUNÇÃO que recebe a linha digitada e diz se está certa (True/False)
#   "exemplo"  -> (opcional) a linha certa, mostrada na dica quando o visitante erra
#   "rodar"    -> (opcional) True = o passo termina quando o visitante aperta ENTER numa linha vazia e o script roda sem erro
#   "recuo"    -> (opcional) espaços que já vêm escritos na linha do visitante (as linhas de dentro de um if ou for)

import pygame  # Biblioteca de jogos que estamos usando

LETRAS_POR_SEGUNDO = 38  # Velocidade da "digitação" do professor
PAUSA_ENTRE_LINHAS = 0.25  # Respiro entre um comentário e outro
PAUSA_DEPOIS_DO_ACERTO = 0.6  # Tempo para o visitante ver que acertou antes do próximo passo


class TutorialDigitado:

    def __init__(self, editor, passos):
        # ATRIBUTOS
        self.editor = editor  # O EditorDeScript onde o professor escreve
        self.passos = passos
        self.indice_do_passo = -1
        self.linhas_para_escrever = []  # Comentários do passo atual que ainda faltam
        self.letras_escritas = 0.0  # Quantas letras da linha atual já apareceram (com casas decimais: anda um pouco a cada quadro)
        self.estado = "pausa"  # "escrevendo", "esperando" (o visitante digita), "pausa" ou "fim"
        self.segundos_de_pausa = 0.3
        self.editor.bloqueado = True  # Enquanto o professor escreve, o visitante não digita
        self.editor.dica = "# (o professor está digitando...)"

    def terminou(self):
        return self.estado == "fim"

    def passo_atual(self):
        return self.passos[self.indice_do_passo]

    def proximo_passo(self):
        self.indice_do_passo += 1
        if self.indice_do_passo >= len(self.passos):  # Acabou: o editor fica livre
            self.estado = "fim"
            self.editor.bloqueado = False
            self.editor.dica = "# ENTER = rodar   Shift+ENTER = nova linha   ESC = fechar"
            return
        self.linhas_para_escrever = list(self.passo_atual()["falar"])
        self.comecar_linha_nova()
        self.estado = "escrevendo"
        self.editor.bloqueado = True
        self.editor.dica = "# (o professor está digitando...)"

    # Abre uma linha nova no fim do script para o professor (ou o visitante) escrever.
    def comecar_linha_nova(self, recuo=""):
        linhas = self.editor.linhas
        if linhas[-1].strip():  # A última linha tem texto: cria outra embaixo
            linhas.append("")
        linhas[-1] = recuo
        self.editor.linha_do_cursor = len(linhas) - 1
        self.editor.coluna_do_cursor = len(recuo)
        self.letras_escritas = 0.0

    def atualizar(self, tempo):
        if self.estado == "pausa":
            self.segundos_de_pausa -= tempo
            if self.segundos_de_pausa <= 0:
                self.proximo_passo()
        elif self.estado == "escrevendo":
            if not self.linhas_para_escrever:  # Terminou de falar: agora é a vez do visitante (ou do próximo passo)
                passo = self.passo_atual()
                if passo.get("conferir") or passo.get("rodar"):
                    self.comecar_linha_nova(passo.get("recuo", ""))
                    self.estado = "esperando"
                    self.editor.bloqueado = False
                    self.editor.dica = "# Aperte ENTER numa linha vazia para RODAR o script." if passo.get("rodar") else "# Sua vez! Digite a linha e aperte ENTER."
                    self.editor.tempo_do_cursor = 0.0
                else:
                    self.estado = "pausa"
                    self.segundos_de_pausa = 0.8
                return
            linha = self.linhas_para_escrever[0]
            self.letras_escritas += LETRAS_POR_SEGUNDO * tempo
            quantas = min(len(linha), int(self.letras_escritas))
            self.editor.linhas[self.editor.linha_do_cursor] = linha[:quantas]  # Mostra só as letras que já "foram digitadas"
            self.editor.coluna_do_cursor = quantas
            self.editor.tempo_do_cursor = 0.0  # Cursor sempre aceso enquanto escreve
            if quantas >= len(linha) and self.letras_escritas >= len(linha) + LETRAS_POR_SEGUNDO * PAUSA_ENTRE_LINHAS:
                self.linhas_para_escrever.pop(0)
                if self.linhas_para_escrever:
                    self.editor.linhas.append("")
                    self.comecar_linha_nova()

    # Os eventos do teclado passam por aqui primeiro. ENTER confere a linha; o resto vai para o editor.
    def tratar_evento(self, evento):
        if self.estado != "esperando":
            return  # Professor escrevendo: o teclado espera
        apertou_enter = evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and not evento.mod & pygame.KMOD_SHIFT
        apagou_no_comeco = evento.type == pygame.KEYDOWN and evento.key == pygame.K_BACKSPACE and self.editor.coluna_do_cursor == 0
        sair_da_linha = evento.type == pygame.KEYDOWN and evento.key in (pygame.K_UP, pygame.K_DOWN)
        if apagou_no_comeco or sair_da_linha:  # Protege as explicações do professor: o visitante fica na linha dele
            return
        if not apertou_enter:
            self.editor.tratar_evento(evento)
            return
        passo = self.passo_atual()
        numero_da_linha = self.editor.linha_do_cursor + 1
        linha = self.editor.linhas[self.editor.linha_do_cursor]
        if passo.get("rodar"):
            if linha.strip():
                self.editor.erro = (numero_da_linha, "# Para RODAR, aperte ENTER numa linha vazia (Shift+ENTER cria uma).")
                return
            self.editor.rodar()  # Confere o script inteiro; se der certo, o Modo Nave aplica
            if self.editor.resultado:
                self.estado = "fim"
            return
        if passo["conferir"](linha):  # Acertou!
            self.editor.erro = None
            self.editor.dica = "# Isso! Linha certa."
            self.editor.bloqueado = True
            self.estado = "pausa"
            self.segundos_de_pausa = PAUSA_DEPOIS_DO_ACERTO
        else:
            self.editor.erro = (numero_da_linha, f"# Ainda não. Digite: {passo['exemplo']}")
