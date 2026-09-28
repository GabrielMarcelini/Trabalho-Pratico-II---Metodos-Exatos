# Coloração de Grafos, explicada do zero

**TP-II · Programação Linear Inteira · Métodos Exatos**

O que é o problema, como o transformamos em um modelo matemático, o que o solver faz por dentro e como ler os resultados das três instâncias.

---

## 1. Qual é o problema?

Imagine montar o **horário de provas** de uma faculdade. Duas disciplinas que têm algum aluno em comum não podem ter prova no mesmo horário. Queremos usar o menor número de horários possível.

| Termo | Significado | No exemplo |
|---|---|---|
| **Vértice** | uma bolinha | uma disciplina |
| **Aresta** | uma linha entre duas bolinhas | "têm aluno em comum" |
| **Cor** | o rótulo dado a cada bolinha | um horário de prova |

A regra é simples: **duas bolinhas ligadas nunca podem ter a mesma cor**. O objetivo é usar o **menor número de cores**. Esse número mínimo se chama **número cromático**, escrito **χ(G)**.

A nossa instância fácil (**myciel3**, com 11 vértices e 20 arestas) precisa de **4 cores**. Com 3 cores não dá para pintar sem conflito.

---

## 2. Por que é difícil (NP-difícil)?

Não se conhece nenhum algoritmo rápido que encontre a resposta exata para qualquer grafo. Decidir se um grafo pode ser pintado com 3 cores já é **NP-completo**: é um dos 21 problemas clássicos de Karp (1972). A versão que minimiza as cores é, portanto, **NP-difícil**.

Na prática, as combinações explodem. Com 47 vértices e 6 cores, existem 6⁴⁷ formas de pintar o grafo, um número com 37 dígitos. Testar todas é impossível; é por isso que usamos um método mais esperto.

---

## 3. Como viramos isso em matemática

Na **Programação Linear Inteira (PLI)** descrevemos o problema com três coisas:
- **variáveis**: as decisões;
- **função objetivo**: o que queremos minimizar;
- **restrições**: as regras.

Depois um programa chamado **solver** procura a melhor resposta.

### As variáveis são perguntas de sim ou não

- `x[v][c]`: o vértice *v* foi pintado com a cor *c*? (1 = sim, 0 = não)
- `y[c]`: a cor *c* foi usada por alguém? (1 = sim, 0 = não)

### O modelo completo

```
min  Σ_c y_c                               (objetivo: nº de cores usadas)

s.a. Σ_c x_vc = 1         ∀ v ∈ V           (1) uma cor por vértice
     x_uc + x_vc ≤ y_c    ∀ (u,v) ∈ E, ∀ c  (2) vizinhos com cores diferentes
     y_c ≥ y_(c+1)        ∀ c               (3) quebra de simetria
     x, y ∈ {0, 1}
```

| Parte | O que significa |
|---|---|
| **Objetivo** | Contar quantas cores foram "ligadas" e deixar esse número o menor possível. |
| **(1)** | Cada vértice recebe exatamente uma cor. Nenhum fica sem cor, nenhum fica com duas. |
| **(2)** | Vizinhos não compartilham cor: se os dois tivessem a cor *c*, a soma seria 2, o que é proibido. Essa restrição também só permite usar a cor *c* se ela estiver ligada (`y[c] = 1`). |
| **(3)** | Quebra de simetria: só usa a cor 2 se já usou a cor 1, e assim por diante. |
| **{0, 1}** | As variáveis só podem valer 0 ou 1. É isso que torna o problema *inteiro*. |

> **Por que a regra (3)?** Sem ela, "azul, vermelho, verde" e "verde, azul, vermelho" seriam soluções diferentes para o solver, mas no fundo são a mesma. Com 6 cores seriam 720 versões da mesma resposta. A regra corta boa parte dessas repetições.

### Quantas cores oferecemos ao modelo?

Antes de montar o modelo rodamos a heurística **DSATUR**. Ela pinta o grafo rapidamente e de um jeito esperto, mas sem garantia de ser o melhor. Se ela conseguiu com 6 cores, oferecemos só 6 cores ao modelo (`K = 6`), porque sabemos que mais do que isso nunca será necessário. Isso deixa o modelo bem menor.

### O código (PuLP)

```python
# variáveis binárias
x = prob.add_variable_dicts("x", (V, C), cat="Binary")
y = prob.add_variable_dicts("y", C, cat="Binary")
# objetivo: minimizar o nº de cores
prob += lpSum(y[c] for c in C)
# (1) cada vértice recebe uma cor
for v in V:
    prob += lpSum(x[v][c] for c in C) == 1
# (2) vizinhos não compartilham cor
for (u, v) in arestas:
    for c in C:
        prob += x[u][c] + x[v][c] <= y[c]
# (3) quebra de simetria
for c in range(K - 1):
    prob += y[c] >= y[c + 1]
# resolve com branch-and-bound (limite de 300 s)
prob.solve(pulp.HiGHS(timeLimit=300))
```

---

## 4. O que o solver faz por dentro

Usamos o **HiGHS**, um solver gratuito chamado pelo PuLP no Python. Ele usa o **Branch-and-Bound**, o método exato pedido no trabalho. São três ideias:

1. **Relaxação linear.** Primeiro ele finge que as variáveis podem valer números "quebrados", como 0,5. Esse problema é fácil de resolver e dá um **limite inferior**: "com certeza precisa de pelo menos tantas cores".
2. **Branch (ramificar).** Se a resposta veio com valores quebrados, ele divide o problema em dois casos, por exemplo "o vértice 5 é azul" e "o vértice 5 não é azul", e resolve cada um. Isso forma uma árvore; cada caso é um **nó**.
3. **Bound (podar).** Se um galho não tem como ser melhor que a solução já encontrada, ele é descartado sem ser explorado.

```
                 [Relaxação: ≥ 2 cores]
                  /                  \
     [vértice 5 é azul]       [vértice 5 não é azul]
        /         \               /            \
  continua…   achou 6 cores   podado ✕      continua…
```

Durante a busca o solver guarda dois números:
- **Melhor solução encontrada** (limite superior): "já achei uma pintura com 6 cores".
- **Limite inferior** (a prova): "tenho certeza de que precisa de pelo menos 4".

Quando os dois se encontram, está **provado que a solução é ótima**. A distância entre eles é o **gap**.

---

## 5. Como ler os nossos resultados

As três instâncias são da família **Mycielski**, do benchmark **DIMACS**. Cada uma é construída a partir da anterior, então a dificuldade cresce de forma controlada. O limite de tempo foi de 300 segundos.

| Instância | Vértices | Arestas | Relaxação | Cores | Provou ≥ | Gap | Nós | Tempo | Status |
|---|---|---|---|---|---|---|---|---|---|
| myciel3 · fácil | 11 | 20 | 2 | 4 | 4 | 0% | 93 | 0,08 s | ✅ Ótimo |
| myciel4 · média | 23 | 71 | 2 | 5 | 5 | 0% | 21.990 | 12 s | ✅ Ótimo |
| myciel5 · difícil | 47 | 236 | 2 | 6 | 4 | 33% | 157.269 | 300 s | ⏱️ Limite de tempo |

Visualmente, numa escala de 0 a 7 cores (`R` = relaxação, `L` = limite inferior provado, `S` = solução encontrada):

```
myciel3   0 ─── R ─────── L=S ────────────     ótimo provado
myciel4   0 ─── R ───────────── L=S ──────     ótimo provado
myciel5   0 ─── R ─────── L ░░░░░░░░ S ───     gap: falta provar de 4 a 6
          0  1  2  3  4  5  6  7
```

> **A conclusão principal:** achar uma boa solução é fácil (o DSATUR já acha 6 cores na hora). O caro é **provar que não existe solução melhor**. Na myciel5 o solver tem a resposta certa, mas em 5 minutos só consegue provar que são necessárias pelo menos 4 cores.

### Por que a difícil não fecha?

- **Relaxação fraca.** Com valores quebrados, o solver dá "meia cor" para cada vértice e o limite começa em 2, enquanto a resposta é 6. A árvore precisa fechar esse buraco sozinha.
- **Grafos de Mycielski são traiçoeiros.** Eles não têm triângulos, mas mesmo assim precisam de muitas cores. Normalmente o solver usaria grupos de vértices todos ligados entre si (cliques) para provar o limite, e aqui eles não existem.
- **Simetria.** Mesmo com a regra (3), sobram muitas pinturas equivalentes para ele examinar.

---

## 6. Perguntas que o professor pode fazer

**Por que o problema é NP-difícil?**
Decidir se um grafo pode ser pintado com 3 cores é NP-completo (Karp, 1972). Minimizar o número de cores é pelo menos tão difícil quanto isso.

**A relaxação linear já é inteira?**
Não. Ela dá 2 nas três instâncias, enquanto o ótimo é 4, 5 e 6. É exatamente isso que torna possível ter uma instância difícil.

**O que é o gap?**
A diferença entre a melhor solução encontrada e o limite inferior provado, em porcentagem. Na myciel5: (6 − 4) / 6 = 33%. Gap 0% significa ótimo provado.

**O que são os "nós"?**
Cada subproblema que o Branch-and-Bound analisou na árvore. Mais nós significa mais trabalho: 93 na fácil, 157 mil na difícil.

**Para que serve a heurística DSATUR?**
Ela dá rapidamente uma coloração boa. Usamos o número de cores dela como K, a quantidade de cores oferecidas ao modelo, o que reduz o tamanho do modelo.

**Como dava para melhorar?**
Com formulações mais fortes, como a de representantes ou a de conjuntos independentes com geração de colunas, que têm uma relaxação linear bem melhor. Um solver comercial, como o Gurobi, e mais tempo também ajudariam.

---

*Código: Python + PuLP, solver HiGHS. Instâncias: benchmark DIMACS de coloração de grafos (myciel3, myciel4, myciel5).*
