# Grape Frame Extractor

Ferramentas para pré-processamento de datasets de vinhedo: extração estruturada de frames de vídeo e filtragem de imagens redundantes por *Perceptual Hashing* (pHash).

Desenvolvido como parte do Trabalho de Conclusão de Curso em Engenharia de Computação no IFMG *Campus* Bambuí.

## Estrutura do repositório

```
grape-frame-extractor/
├── extract_frames.py       # Extração de frames dos vídeos
├── filter_duplicates.py    # Filtragem de redundância por pHash
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Extração de frames (`extract_frames.py`)

### Como funciona

O algoritmo divide cada vídeo em janelas temporais correspondentes a 4 janelas por segundo. Para cada janela, seleciona o frame mais adequado com base em dois critérios:

1. **Nitidez** — medida pela variância do operador Laplaciano aplicado ao frame em escala de cinza. Frames mais nítidos produzem maior variância.
2. **Luminosidade** — medida pela intensidade média dos pixels. Frames com luminosidade abaixo do limiar configurável são descartados como candidatos principais.

**Critério de seleção:**
- Se houver frames com luminosidade adequada na janela, seleciona o mais nítido entre eles.
- Se todos os frames da janela estiverem abaixo do limiar de luminosidade, seleciona o mais nítido do lote independentemente da iluminação (*fallback*).

Esse critério garante exatamente um frame por janela, independentemente das condições do vídeo.

### Uso

Coloque os arquivos de vídeo na pasta raiz do projeto com os nomes `video1.mp4` até `video7.mp4` e execute:

```bash
python extract_frames.py
```

### Configurações

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `FRAMES_POR_SEGUNDO` | `4` | Número de janelas por segundo |
| `LIMIAR_LUMINOSIDADE` | `40.0` | Luminosidade mínima (0–255) para considerar um frame bem iluminado |
| `PASTA_SAIDA_BASE` | `dataset_uvas_estruturado` | Pasta raiz de saída |

### Estrutura de saída

```
dataset_uvas_estruturado/
├── video1/
│   ├── frame_000000_orig_000000.jpg
│   ├── frame_000001_orig_000015.jpg
│   └── ...
├── video2/
│   └── ...
└── ...
```

O nome de cada arquivo indica o índice do frame no conjunto extraído (`frame_XXXXXX`) e o índice do frame original no vídeo (`orig_XXXXXX`).

---

## Filtragem de redundância por pHash (`filter_duplicates.py`)

Após a extração, imagens visualmente semelhantes são identificadas e removidas utilizando *Perceptual Hashing* (pHash). O método calcula uma assinatura binária de 64 bits para cada imagem via Transformada Discreta de Cosseno (DCT) e mede a similaridade entre pares pela Distância de Hamming normalizada.

### Como funciona

Para cada imagem, o algoritmo a compara com todas as imagens já aprovadas. Se a similaridade com qualquer aprovada for maior ou igual ao limiar configurável, a imagem é descartada. Caso contrário, é aceita e passa a integrar o conjunto de referência.

### Uso

```bash
python filter_duplicates.py
```

As imagens a filtrar devem estar na pasta definida em `PASTA_ENTRADA`.

### Configurações

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `PASTA_ENTRADA` | `uvas` | Pasta com as imagens a filtrar |
| `PASTA_APROVADAS` | `dataset_uvas_final_aprovado` | Pasta de saída das imagens únicas |
| `PASTA_DESCARTADAS` | `dataset_uvas_auditoria_pastas` | Pasta de auditoria dos descartes |
| `LIMIAR_SIMILARIDADE` | `0.80` | Similaridade mínima para descartar (0.0–1.0) |

### Estrutura de saída

```
dataset_uvas_final_aprovado/
│   imagem_001.jpg
│   imagem_003.jpg
│   ...

dataset_uvas_auditoria_pastas/
├── par_0001/
│   ├── 1_REF_imagem_001.jpg
│   └── 2_DESC_(83%_igual)_imagem_002.jpg
├── par_0002/
│   └── ...
└── ...
```

Cada subpasta de auditoria contém o par (referência + descartada) para revisão manual. O percentual de similaridade é indicado no nome do arquivo descartado.

Uma matriz de similaridade visual é salva em `matriz_similaridade.png`.

---

## Requisitos

- Python 3.8 ou superior
- OpenCV
- NumPy
- Pillow
- imagehash
- matplotlib
- seaborn

Instalação das dependências:

```bash
pip install -r requirements.txt
```

---

## Projeto relacionado

Este repositório faz parte de um *pipeline* maior que inclui:

- Anotação do *dataset* na plataforma Roboflow
- Treinamento de modelo de segmentação de instâncias baseado na família YOLO
- Algoritmo de estimativa quantitativa de produção de uvas

## Autor

Hugo César Leal  
Engenharia de Computação — IFMG *Campus* Bambuí  
Orientador: Prof. Dr. Ciniro Aparecido Leite Nametala  
Coorientador: Prof. Dr. João Carlos Sampaio Maldonado Costa Mendes (UPB, Portugal)
