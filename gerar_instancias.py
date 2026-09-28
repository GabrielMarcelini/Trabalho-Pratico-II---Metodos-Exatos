"""
Gera as instâncias clássicas da DIMACS (Graph Coloring Benchmarks) no formato .col.

As instâncias myciel são definidas matematicamente, então podem ser
reconstruídas exatamente (mesmo nº de vértices e arestas das originais em
https://mat.tepper.cmu.edu/COLOR/instances.html).

    myciel3  -> 11 vértices,  20 arestas, χ = 4
    myciel4  -> 23 vértices,  71 arestas, χ = 5
    myciel5  -> 47 vértices, 236 arestas, χ = 6
"""
import os

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instancias")


def mycielski(n_vertices, arestas):
    """Aplica a transformação de Mycielski: aumenta χ em 1 sem criar triângulos."""
    novas = list(arestas)
    for (a, b) in arestas:                 # u_i ligado aos vizinhos de v_i
        novas.append((a, n_vertices + b))
        novas.append((b, n_vertices + a))
    w = 2 * n_vertices                      # vértice extra ligado a todos os u_i
    for i in range(n_vertices):
        novas.append((n_vertices + i, w))
    return 2 * n_vertices + 1, novas


def myciel(k):
    """myciel_k da DIMACS = k-1 transformações de Mycielski a partir de K2."""
    n, arestas = 2, [(0, 1)]
    for _ in range(k - 1):
        n, arestas = mycielski(n, arestas)
    return n, arestas


def salvar_col(nome, n, arestas, comentario):
    os.makedirs(PASTA, exist_ok=True)
    caminho = os.path.join(PASTA, f"{nome}.col")
    with open(caminho, "w") as f:
        f.write(f"c {nome}.col - {comentario}\n")
        f.write(f"p edge {n} {len(arestas)}\n")
        for (u, v) in arestas:
            f.write(f"e {u + 1} {v + 1}\n")     # DIMACS numera a partir de 1
    print(f"{nome:10s} {n:3d} vértices {len(arestas):4d} arestas -> {caminho}")


if __name__ == "__main__":
    for k in (3, 4, 5):
        n, e = myciel(k)
        salvar_col(f"myciel{k}", n, e, "Grafo de Mycielski (sem triangulos, chi alto)")
