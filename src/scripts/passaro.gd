# CLASSE PASSARO
# Uma classe é um "molde". A cena passaro.tscn é um objeto criado a partir deste molde.
# "extends CharacterBody2D" = HERANÇA: o Passaro herda tudo que um CharacterBody2D já sabe
# fazer (se mover, colidir, ter velocidade) e nós só adicionamos o que é específico dele.
class_name Passaro  # Dá um nome à classe, para outros scripts poderem usar "Passaro"
extends CharacterBody2D  # Classe "mãe" de onde herdamos o movimento e a colisão


# ATRIBUTOS: características do pássaro.
# "@export" faz o valor aparecer no Inspetor do Godot, para ajustar sem mexer no código.
@export var forca_da_gravidade: float = 500.0  # Quanto a gravidade puxa o pássaro para baixo (pixels por segundo²)
@export var forca_do_pulo: float = 160.0  # Velocidade para cima que o pássaro ganha a cada pulo (pixels por segundo)
@export var velocidade_maxima_de_queda: float = 250.0  # Limite de velocidade caindo, para a queda não ficar rápida demais


# MÉTODOS: ações que o pássaro sabe fazer.

# O Godot chama este método sozinho, várias vezes por segundo (a cada quadro de física).
# "tempo_do_quadro" é quantos segundos passaram desde o último quadro.
func _physics_process(tempo_do_quadro: float) -> void:
	aplicar_gravidade(tempo_do_quadro)  # Primeiro a gravidade puxa o pássaro para baixo
	if Input.is_action_just_pressed("pular"):  # Se o jogador apertou Espaço ou clicou neste quadro...
		pular()  # ...o pássaro pula
	move_and_slide()  # Método herdado do CharacterBody2D: move o pássaro usando a "velocity"


# Aumenta a velocidade de queda aos poucos, como a gravidade de verdade.
func aplicar_gravidade(tempo_do_quadro: float) -> void:
	velocity.y += forca_da_gravidade * tempo_do_quadro  # "velocity" é herdada; no Godot, Y positivo é para BAIXO
	velocity.y = min(velocity.y, velocidade_maxima_de_queda)  # Não deixa cair mais rápido que o limite


# Joga o pássaro para cima.
func pular() -> void:
	velocity.y = -forca_do_pulo  # Valor negativo em Y = para CIMA; substitui a queda por um impulso
