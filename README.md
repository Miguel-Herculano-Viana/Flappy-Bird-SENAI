# Flappy-Bird-SENAI
Repositorio de criação de um jogo Flappy Bird para a feira de profissões do SENAI


O jogo é desenvolvido usando a Godot Engine (versão 4.7.2), requerindo a mesma versão ou superior em caso de edição futura

## Versão em Python (Pygame)

A versão em Python fica na pasta `jogo_python/`. Para rodar:

```
pip install -r jogo_python/requirements.txt
python jogo_python/jogo.py
```

O jogo abre em tela cheia. Na tela de início, escolha o modo com as setas (ou 1 / 2) e comece com ESPAÇO:

1. **Desafios de código**: Flappy Bird com desafios que se resolvem escrevendo Python.
2. **Modo Nave**: começa como Flappy Bird e vira um shooter horizontal com armas programadas em Python.

Controles do modo 1:

| Tecla | O que faz |
|---|---|
| ESPAÇO ou clique esquerdo | Pula (o clique pula até com o editor aberto) |
| ENTER | Abre o editor de código quando aparece um desafio; dentro do editor, roda a linha |
| ESC | Fecha o editor; com o editor fechado, sai do jogo |

## Desafios de código

Nesta versão, o principal é **programar o jogo**: no meio da partida aparecem problemas que só se resolvem
escrevendo uma linha de Python no painel ao lado do jogo. Com o editor aberto, o jogo fica em câmera lenta.

| Desafio | O que acontece | Código | Valores permitidos |
|---|---|---|---|
| Canos fechados | Um par de canos se fecha | `canos.abertura = 80` | 56 a 96 |
| Gravidade pesada | O pássaro cai rápido por 3 pares | `passaro.forca_da_gravidade = 450` | 350 a 550 |
| Pulo fraco | O pássaro quase não sobe por 3 pares | `passaro.forca_do_pulo = 170` | 140 a 190 |
| Canos colados | 3 pares chegam quase encostados | `canos.distancia = 110` | 80 a 130 |

- **Tutorial:** na primeira vez de cada desafio, o jogo para e explica o que é objeto, atributo e o sinal `=`.
- **Digitação progressiva:** a cada acerto vem menos código pronto (primeiro só o número, depois o atributo, depois a linha inteira).
- **Erros como no Python:** `SyntaxError`, `NameError`, `AttributeError`, `TypeError`, `ValueError` (fora da faixa)... e o jogo não muda.
- **Efeito temporário:** cada mudança vale só para aquele desafio; depois o jogo volta ao normal (com aviso).
- **Balanceamento:** cooldown por desafio, tempo limite no editor (erros descontam tempo) e, a cada 10 pontos,
  um nível de dificuldade a mais (canos mais estreitos, faixas permitidas menores e menos tempo no editor).
  Todos os números ficam no topo de `jogo_python/desafios.py`.
- **Segurança:** o código digitado nunca é executado (`eval`/`exec`); ele é lido com o módulo `ast` e só o formato
  `objeto.atributo = número` é aceito. Para conferir a validação: `python jogo_python/editor.py`.

## Modo Nave

Depois de 3 canos, uma nave aparece, explode os canos e foge para o fundo do céu. O pássaro ganha uma arma
e o jogo vira um **shooter horizontal**: setas ou WASD movem o pássaro em qualquer direção e as armas atiram sozinhas.
Derrotar inimigos dá XP; ao subir de nível o jogo pausa e o **script das armas** abre no painel:

```python
# SCRIPT das armas: mude os números e aperte ENTER.
# passaro.armas: LISTA das armas equipadas (máx. 2)
passaro.armas = [blaster, laser]
# Limite do blaster: cadencia x dano <= 12
blaster.cadencia = 4
blaster.dano = 3
# Limite do laser: quantidade x grossura <= 6
laser.quantidade = 2
laser.grossura = 3
```

- Cada arma tem dois parâmetros, cada um com uma faixa própria, e um **limite compartilhado**: o produto dos dois não pode passar do limite
  (mais raios de laser = raios mais finos). O painel mostra a conta ao vivo enquanto o visitante digita.
- **Níveis 2, 5 e 8:** o visitante escolhe uma arma nova entre 3 cartas. Só dá para equipar armas desbloqueadas, e no máximo 2 ao mesmo tempo.
- **Outros níveis:** os limites das armas sobem e o script abre para reajustar (ENTER mantém como está; ESC fecha sem mudar).
- Erros aparecem como no Python, com o número da linha (`linha 6: ValueError: ...`), e a arma não muda.
- No editor: ENTER roda o script, Shift+ENTER cria uma linha nova.

| Arma | Parâmetros | Limite (começo, +por nível) | Como atira |
|---|---|---|---|
| `blaster` | `cadencia` 1–10, `dano` 1–10 | `cadencia x dano <= 12` (+3) | tiros retos |
| `laser` | `quantidade` 1–5, `grossura` 1–8 | `quantidade x grossura <= 6` (+2) | pulsos que atravessam tudo |
| `missil` | `quantidade` 1–6, `explosao` 4–24 | `quantidade x explosao <= 24` (+6) | mísseis teleguiados com dano em área |
| `espalhado` | `balas` 1–9, `alcance` 40–200 | `balas x alcance <= 400` (+80) | leque de balas de curto alcance |

Inimigos: batedores (voam em onda), atiradores (miram no pássaro) e tanques (leque de tiros).
Chefes: **Chefe Verde**, **Chefe Vermelho** e a **Nave-Mãe** (a nave do começo, que volta do fundo com um raio gigante).
Cada chefe trinca e fica mais agressivo conforme perde vida. O pássaro tem 5 corações; vencer a Nave-Mãe mostra "VOCÊ VENCEU!".
O Modo Nave tem recorde próprio. Os números de balanceamento ficam no topo de `modo_nave.py`, `armas.py` e `inimigos.py`.

Para conferir a validação do script: `python jogo_python/script_das_armas.py`.

## Créditos

- Sprites do Modo Nave (`src/assets/nave/`), todos CC0, recortados e girados para o shooter horizontal:
  [Space Ship Shooter Pixel Art Assets](https://opengameart.org/content/space-ship-shooter-pixel-art-assets) e
  [Animated Explosions](https://opengameart.org/content/animated-explosions), de ansimuz;
  [SpaceShip Boss Set](https://opengameart.org/content/spaceship-boss-set), de The_Scientist___.
- Cano e fundo (`src/assets/cano.png` e `src/assets/fundo.png`): montados a partir do pacote [Flappy-Bit](https://opengameart.org/content/flappy-bit), de LD, licença [OGA-BY 3.0](https://static.opengameart.org/OGA-BY-3.0.txt).
