"""
filter_duplicates.py
--------------------
Filtra imagens redundantes de um dataset usando Perceptual Hashing (pHash).

Para cada par de imagens com similaridade acima do limiar configurável,
a imagem mais recente na ordem alfabética é descartada. O resultado é
separado em duas pastas: imagens aprovadas e imagens descartadas para
auditoria. Uma matriz de similaridade visual é gerada como saída gráfica.

Uso:
    python filter_duplicates.py

As imagens devem estar na pasta definida em PASTA_ENTRADA.
"""

import os
import shutil

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import imagehash


# ---------------------------------------------------------------------------
# Configurações globais
# ---------------------------------------------------------------------------

PASTA_ENTRADA = "uvas"
PASTA_APROVADAS = "dataset_uvas_final_aprovado"
PASTA_DESCARTADAS = "dataset_uvas_auditoria_pastas"
LIMIAR_SIMILARIDADE = 0.80   # imagens com similaridade >= este valor são descartadas
TAMANHO_HASH = 64            # número de bits da assinatura pHash (padrão: 8x8 = 64 bits)
EXTENSOES_VALIDAS = (".png", ".jpg", ".jpeg")


# ---------------------------------------------------------------------------
# Funções de hashing
# ---------------------------------------------------------------------------

def carregar_hashes(pasta: str, arquivos: list) -> dict:
    """
    Calcula e retorna as assinaturas pHash de todas as imagens da pasta.

    Parâmetros
    ----------
    pasta : str
        Caminho da pasta contendo as imagens.
    arquivos : list
        Lista de nomes de arquivos a processar.

    Retorna
    -------
    dict
        Mapeamento de nome_arquivo -> assinatura pHash.
    """
    hashes = {}
    print(f"Calculando assinaturas pHash para {len(arquivos)} imagens...")

    for arquivo in arquivos:
        caminho = os.path.join(pasta, arquivo)
        try:
            hashes[arquivo] = imagehash.phash(Image.open(caminho))
        except Exception as erro:
            print(f"  [AVISO] Não foi possível processar {arquivo}: {erro}")

    return hashes


def calcular_similaridade(hash_a: imagehash.ImageHash,
                           hash_b: imagehash.ImageHash,
                           bits: int = 64) -> float:
    """
    Calcula a similaridade percentual entre dois hashes pHash.

    A similaridade é calculada como 1 - (distância de Hamming / total de bits).

    Parâmetros
    ----------
    hash_a, hash_b : imagehash.ImageHash
        Assinaturas pHash a comparar.
    bits : int
        Número de bits das assinaturas (padrão 64).

    Retorna
    -------
    float
        Valor entre 0.0 (totalmente diferentes) e 1.0 (idênticas).
    """
    distancia = hash_a - hash_b
    return 1.0 - (distancia / bits)


# ---------------------------------------------------------------------------
# Funções de visualização
# ---------------------------------------------------------------------------

def construir_matriz_similaridade(arquivos: list, hashes: dict,
                                  bits: int = 64) -> np.ndarray:
    """
    Constrói a matriz de similaridade entre todas as imagens do dataset.

    Parâmetros
    ----------
    arquivos : list
        Lista ordenada de nomes de arquivo.
    hashes : dict
        Mapeamento de nome_arquivo -> assinatura pHash.
    bits : int
        Número de bits das assinaturas.

    Retorna
    -------
    np.ndarray
        Matriz quadrada (n x n) com valores de similaridade entre 0 e 1.
    """
    n = len(arquivos)
    matriz = np.zeros((n, n))

    for i, arquivo_i in enumerate(arquivos):
        for j, arquivo_j in enumerate(arquivos):
            matriz[i, j] = calcular_similaridade(hashes[arquivo_i],
                                                  hashes[arquivo_j], bits)
    return matriz


def salvar_heatmap(matriz: np.ndarray, arquivos: list,
                   caminho_saida: str = "matriz_similaridade.png") -> None:
    """
    Gera e salva o heatmap da matriz de similaridade.

    Exibe no máximo 30 rótulos nos eixos para evitar sobreposição.
    O eixo Y cresce de baixo para cima seguindo a convenção cartesiana.

    Parâmetros
    ----------
    matriz : np.ndarray
        Matriz de similaridade gerada por construir_matriz_similaridade.
    arquivos : list
        Lista ordenada de nomes de arquivo (usada como rótulos dos eixos).
    caminho_saida : str
        Caminho do arquivo de imagem a ser salvo.
    """
    n = len(arquivos)
    passo = max(1, n // 30)
    rotulos = [nome if i % passo == 0 else "" for i, nome in enumerate(arquivos)]

    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(
        matriz,
        cmap="YlGnBu",
        xticklabels=rotulos,
        yticklabels=rotulos,
        vmin=0.0,
        vmax=1.0,
    )
    ax.invert_yaxis()
    ax.tick_params(axis="both", which="both", length=0)

    plt.title("Matriz de Similaridade do Dataset (pHash)", pad=20, fontsize=14)
    plt.xlabel("Imagens (ordem crescente →)", labelpad=15, fontsize=12)
    plt.ylabel("Imagens (ordem crescente ↑)", labelpad=15, fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=300)
    plt.close()

    print(f"Matriz de similaridade salva em '{caminho_saida}'.")


# ---------------------------------------------------------------------------
# Função de filtragem
# ---------------------------------------------------------------------------

def filtrar_redundantes(arquivos: list, matriz: np.ndarray,
                         limiar: float) -> tuple:
    """
    Identifica imagens redundantes comparando cada uma com as já aprovadas.

    Uma imagem é considerada redundante se a sua similaridade com qualquer
    imagem já aprovada for maior ou igual ao limiar definido.

    Parâmetros
    ----------
    arquivos : list
        Lista ordenada de nomes de arquivo.
    matriz : np.ndarray
        Matriz de similaridade (n x n).
    limiar : float
        Limiar de similaridade acima do qual a imagem é descartada.

    Retorna
    -------
    tuple
        (aprovadas, descartadas) onde cada elemento é uma lista de dicts
        com as chaves 'arquivo', e opcionalmente 'referencia' e 'similaridade'.
    """
    aprovadas = []
    descartadas = []
    indices_aprovados = []

    for i, arquivo in enumerate(arquivos):
        referencia = None
        similaridade_max = 0.0

        for idx_aprovado in indices_aprovados:
            sim = matriz[i, idx_aprovado]
            if sim >= limiar and sim > similaridade_max:
                similaridade_max = sim
                referencia = arquivos[idx_aprovado]

        if referencia is not None:
            descartadas.append({
                "arquivo": arquivo,
                "referencia": referencia,
                "similaridade": similaridade_max,
            })
        else:
            aprovadas.append({"arquivo": arquivo})
            indices_aprovados.append(i)

    return aprovadas, descartadas


# ---------------------------------------------------------------------------
# Funções de saída
# ---------------------------------------------------------------------------

def copiar_aprovadas(aprovadas: list, pasta_entrada: str,
                     pasta_saida: str) -> None:
    """
    Copia as imagens aprovadas para a pasta de saída.
    """
    os.makedirs(pasta_saida, exist_ok=True)
    for item in aprovadas:
        shutil.copy2(
            os.path.join(pasta_entrada, item["arquivo"]),
            os.path.join(pasta_saida, item["arquivo"]),
        )


def copiar_descartadas_para_auditoria(descartadas: list, pasta_entrada: str,
                                       pasta_saida: str) -> None:
    """
    Copia cada par (referência + descartada) em uma subpasta numerada
    para facilitar a revisão manual dos descartes.

    Estrutura gerada:
        pasta_saida/
            par_0001/
                1_REF_<nome_referencia>.jpg
                2_DESC_(XX%_igual)_<nome_descartada>.jpg
            par_0002/
                ...
    """
    os.makedirs(pasta_saida, exist_ok=True)

    for numero, item in enumerate(descartadas, start=1):
        pasta_par = os.path.join(pasta_saida, f"par_{numero:04d}")
        os.makedirs(pasta_par, exist_ok=True)

        pct = int(item["similaridade"] * 100)
        nome_ref = f"1_REF_{item['referencia']}"
        nome_desc = f"2_DESC_({pct}pct_igual)_{item['arquivo']}"

        shutil.copy2(
            os.path.join(pasta_entrada, item["referencia"]),
            os.path.join(pasta_par, nome_ref),
        )
        shutil.copy2(
            os.path.join(pasta_entrada, item["arquivo"]),
            os.path.join(pasta_par, nome_desc),
        )

        print(f"  par_{numero:04d}: {item['arquivo']} ({pct}% similar a {item['referencia']})")


def imprimir_relatorio(total: int, aprovadas: list, descartadas: list,
                        limiar: float) -> None:
    """
    Exibe um resumo do processo de filtragem no terminal.
    """
    print("\n--- Relatório de filtragem ---")
    print(f"Total analisado : {total} imagens")
    print(f"Aprovadas       : {len(aprovadas)} imagens")
    print(f"Descartadas     : {len(descartadas)} imagens")
    print(f"Limiar utilizado: {limiar * 100:.0f}%")


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    arquivos = sorted([
        f for f in os.listdir(PASTA_ENTRADA)
        if f.lower().endswith(EXTENSOES_VALIDAS)
    ])

    if not arquivos:
        print(f"Nenhuma imagem encontrada em '{PASTA_ENTRADA}'.")
        return

    hashes = carregar_hashes(PASTA_ENTRADA, arquivos)

    print("Construindo matriz de similaridade...")
    matriz = construir_matriz_similaridade(arquivos, hashes, TAMANHO_HASH)
    salvar_heatmap(matriz, arquivos)

    print(f"\nFiltrando imagens com similaridade >= {LIMIAR_SIMILARIDADE * 100:.0f}%...")
    aprovadas, descartadas = filtrar_redundantes(arquivos, matriz, LIMIAR_SIMILARIDADE)

    print("\nCopiando imagens aprovadas...")
    copiar_aprovadas(aprovadas, PASTA_ENTRADA, PASTA_APROVADAS)

    print("\nOrganizando imagens descartadas para auditoria...")
    copiar_descartadas_para_auditoria(descartadas, PASTA_ENTRADA, PASTA_DESCARTADAS)

    imprimir_relatorio(len(arquivos), aprovadas, descartadas, LIMIAR_SIMILARIDADE)


if __name__ == "__main__":
    main()
