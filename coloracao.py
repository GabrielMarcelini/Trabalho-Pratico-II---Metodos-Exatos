"""
TP-II — Problema de Coloração de Grafos (Graph Coloring Problem)
Modelo de Programação Linear Inteira resolvido com PuLP + HiGHS (método exato: branch-and-bound).

Uso:
    python coloracao.py                       # roda as 3 instâncias do trabalho
    python coloracao.py instancias/X.col 60   # roda uma instância com limite de 60 s
"""
import csv
import json
import os
import sys
import time

import pulp

BASE = os.path.dirname(os.path.abspath(__file__))

# Instâncias do trabalho: (arquivo, dificuldade, χ conhecido na literatura)
INSTANCIAS = [
    ("myciel3.col", "Fácil", 4),
    ("myciel4.col", "Média", 5),
    ("myciel5.col", "Difícil", 6),
]
LIMITE_TEMPO = 300  # segundos


# ---------------------------------------------------------------------------
# 1) Leitura do arquivo DIMACS (.col)
# ---------------------------------------------------------------------------
def ler_dimacs(caminho):
    n, arestas = 0, set()
    with open(caminho) as f:
        for linha in f:
            partes = linha.split()
            if not partes:
                continue
            if partes[0] == "p":                 # p edge <n> <m>
                n = int(partes[2])
            elif partes[0] == "e":               # e <u> <v>
                u, v = int(partes[1]) - 1, int(partes[2]) - 1
                if u != v:
                    arestas.add((min(u, v), max(u, v)))
    return n, sorted(arestas)


# ---------------------------------------------------------------------------
# 2) Heurística DSATUR: dá um limite superior K (quantas cores oferecer ao modelo)
# ---------------------------------------------------------------------------
def dsatur(n, arestas):
    viz = [set() for _ in range(n)]
    for u, v in arestas:
        viz[u].add(v)
        viz[v].add(u)
    cor = [-1] * n
    for _ in range(n):
        # escolhe o vértice com mais cores diferentes na vizinhança (desempate: grau)
        v = max((i for i in range(n) if cor[i] == -1),
                key=lambda i: (len({cor[j] for j in viz[i] if cor[j] != -1}), len(viz[i])))
        usadas = {cor[j] for j in viz[v]}
        cor[v] = next(c for c in range(n) if c not in usadas)
    return max(cor) + 1


# ---------------------------------------------------------------------------
# 3) Modelo de PLI (formulação por atribuição)
# ---------------------------------------------------------------------------
def construir_modelo(n, arestas, K, relaxado=False):
    V, C = range(n), range(K)
    prob = pulp.LpProblem("Coloracao_de_Grafos", pulp.LpMinimize)
    # relaxado=True troca {0,1} por [0,1] -> relaxação linear
    tipo = dict(lowBound=0, upBound=1, cat="Continuous") if relaxado else dict(cat="Binary")

    # x[v][c] = 1 se o vértice v recebe a cor c ; y[c] = 1 se a cor c é usada
    x = prob.add_variable_dicts("x", (V, C), **tipo)
    y = prob.add_variable_dicts("y", C, **tipo)

    # Função objetivo: minimizar o número de cores usadas
    prob += pulp.lpSum(y[c] for c in C)

    # (1) Cada vértice recebe exatamente uma cor
    for v in V:
        prob += pulp.lpSum(x[v][c] for c in C) == 1

    # (2) Vértices vizinhos não podem ter a mesma cor (e só usa cor "ligada")
    for (u, v) in arestas:
        for c in C:
            prob += x[u][c] + x[v][c] <= y[c]

    # (3) Quebra de simetria: a cor c+1 só é usada se a cor c também for
    for c in range(K - 1):
        prob += y[c] >= y[c + 1]

    return prob, x, y


# ---------------------------------------------------------------------------
# 4) Resolução + coleta de métricas
# ---------------------------------------------------------------------------
def resolver(caminho, limite=LIMITE_TEMPO, dificuldade="-", chi=None):
    nome = os.path.basename(caminho).replace(".col", "")
    n, arestas = ler_dimacs(caminho)
    K = dsatur(n, arestas)

    # Relaxação linear (limite inferior "ingênuo")
    relax, _, _ = construir_modelo(n, arestas, K, relaxado=True)
    relax.solve(pulp.HiGHS(msg=False))
    lp_bound = pulp.value(relax.objective)

    prob, x, y = construir_modelo(n, arestas, K)

    # Resolução exata (branch-and-bound do HiGHS)
    t0 = time.perf_counter()
    prob.solve(pulp.HiGHS(msg=False, timeLimit=limite))
    tempo = time.perf_counter() - t0

    info = prob.solverModel.getInfo()
    cores = round(pulp.value(prob.objective))
    limite_inf = info.mip_dual_bound
    h = prob.solverModel
    otimo = h.modelStatusToString(h.getModelStatus()) == "Optimal"
    gap = 0.0 if otimo else (cores - limite_inf) / cores * 100

    # Confere a solução: nenhuma aresta com as duas pontas da mesma cor
    cor = {v: c for v in range(n) for c in range(K) if x[v][c].value() > 0.5}
    assert all(cor[u] != cor[v] for u, v in arestas), "Solução inválida!"

    r = {
        "instancia": nome,
        "dificuldade": dificuldade,
        "vertices": n,
        "arestas": len(arestas),
        "cores_oferecidas_K": K,
        "variaveis": prob.numVariables(),
        "restricoes": prob.numConstraints(),
        "relaxacao_linear": round(lp_bound, 2),
        "limite_inferior": round(limite_inf, 2),
        "cores_encontradas": cores,
        "chi_literatura": chi,
        "status": "Ótimo" if otimo else "Limite de tempo",
        "gap_%": round(gap, 2),
        "nos_bb": info.mip_node_count,
        "tempo_s": round(tempo, 2),
        "coloracao": [cor[v] for v in range(n)],
    }
    return r


def imprimir(r):
    print(f"\n=== {r['instancia']} ({r['dificuldade']}) ===")
    for k, v in r.items():
        if k != "coloracao":
            print(f"  {k:20s}: {v}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        limite = float(sys.argv[2]) if len(sys.argv) > 2 else LIMITE_TEMPO
        imprimir(resolver(sys.argv[1], limite))
        sys.exit()

    resultados = []
    for arquivo, dif, chi in INSTANCIAS:
        r = resolver(os.path.join(BASE, "instancias", arquivo), LIMITE_TEMPO, dif, chi)
        imprimir(r)
        resultados.append(r)

    with open(os.path.join(BASE, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    campos = [k for k in resultados[0] if k != "coloracao"]
    with open(os.path.join(BASE, "resultados.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(resultados)
    print("\nResultados salvos em resultados.csv e resultados.json")
