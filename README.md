# TP-II — Problema de Coloração de Grafos (PLI com Métodos Exatos)

Modelagem do **Problema de Coloração de Grafos** como Programação Linear Inteira em Python (**PuLP**),
resolvido de forma exata com o solver **HiGHS** (branch-and-bound + planos de corte).

## Problema

Dado um grafo G = (V, E), atribuir uma cor a cada vértice de forma que vértices adjacentes
tenham cores diferentes, usando o menor número de cores possível (o número cromático χ(G)).
Decidir se G é k-colorível é NP-completo para k ≥ 3 (Karp, 1972), então a otimização é NP-difícil.

## Modelo (formulação por atribuição)

- `x[v][c] = 1` se o vértice v recebe a cor c
- `y[c] = 1` se a cor c é usada
- K = nº de cores oferecidas (limite superior dado pela heurística DSATUR)

```
min  Σ_c y_c
s.a. Σ_c x_vc = 1               ∀ v ∈ V              (uma cor por vértice)
     x_uc + x_vc ≤ y_c          ∀ (u,v) ∈ E, ∀ c     (vizinhos com cores diferentes)
     y_c ≥ y_{c+1}              ∀ c                  (quebra de simetria)
     x, y ∈ {0,1}
```

## Estrutura

```
TP2-Coloracao-de-Grafos/
├── instancias/
│   ├── myciel3.col      # Fácil   — 11 vértices,  20 arestas, χ = 4
│   ├── myciel4.col      # Média   — 23 vértices,  71 arestas, χ = 5
│   └── myciel5.col      # Difícil — 47 vértices, 236 arestas, χ = 6
├── gerar_instancias.py  # reconstrói as instâncias DIMACS (formato .col)
├── coloracao.py         # leitor DIMACS + DSATUR + modelo PLI + métricas
├── resultados.csv       # tabela comparativa
├── resultados.json      # resultados completos (inclui a coloração de cada vértice)
├── saida_execucao.txt   # log da execução
├── slides.html          # apresentação (abrir no navegador)
└── requirements.txt
```

## Como executar

```bash
pip install -r requirements.txt
python gerar_instancias.py        # opcional: os .col já estão na pasta
python coloracao.py               # roda as 3 instâncias (limite de 300 s cada)
python coloracao.py instancias/myciel4.col 60   # uma instância com limite de 60 s
```

As instâncias são do benchmark DIMACS de coloração
(<https://mat.tepper.cmu.edu/COLOR/instances.html>). Como os grafos de Mycielski têm definição
matemática, `gerar_instancias.py` os reconstrói com o mesmo número de vértices e arestas das originais.

## Resultados (HiGHS, limite de 300 s)

| Nível | Instância | V | E | Variáveis | Restrições | Relax. LP | Lim. inf. | Cores | Gap | Nós B&B | Tempo | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fácil | myciel3 | 11 | 20 | 48 | 94 | 2.0 | 4.0 | 4 | 0.0% | 93 | 0.08 s | Ótimo |
| Média | myciel4 | 23 | 71 | 120 | 382 | 2.0 | 5.0 | 5 | 0.0% | 21990 | 12.03 s | Ótimo |
| Difícil | myciel5 | 47 | 236 | 288 | 1468 | 2.0 | 4.0 | 6 | 33.33% | 157269 | 300.03 s | Limite de tempo |

A relaxação linear dá limite 2 nas três instâncias, enquanto o ótimo é 4, 5 e 6. Na myciel5 o solver
encontra a coloração ótima (6 cores), mas não prova a otimalidade em 300 s (limite inferior = 4).

## Apresentação

Abra `slides.html` no navegador. Teclas: **← →** navegar, **N** mostra as notas do apresentador
(roteiro de fala de cada slide), **F** tela cheia. Os slides indicam qual integrante apresenta
cada parte (~7 min no total).
