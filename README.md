# Trabalho de Computação Visual — A Cena Reage ao Movimento

**Curso:** Licenciatura em Engenharia de Sistemas de Informação / LESTI (ISE) — Universidade do Algarve  
**Unidade Curricular:** Computação Visual (2026/27)  
**Projeto de Grupo:** Vasco Matos a85234 Daniel   

---

## Tema do Projeto

O propjeto teve como base o desenvolvimento de um programa que, atravez de uma camera anexa ao computador, seja verificado movimento numa determinada area, gerando assim uma animação. Essa animação sendo criada em Blender fazendo parte de uma cena de uma explanada.

---

## Tabela das Zonas

| Zona | Objeto Associado | Animação | Quem Modelou |
| :---: | :--- | :--- | :--- |
| **Zona 1** (Esquerda) | **Cadeira** (`zona1_cadeira`) | Rotação/animação em ciclo da cadeira da esplanada (12 FPS) | *Daniel* |
| **Zona 2** (Centro) | **Copo** (`zona2_copo`) | Animação do copo de vidro em ciclo (24 FPS) | *Daniel* |
| **Zona 3** (Direita) | **Vela** (`zona3_vela`) | Animação da vela com chama/movimento em ciclo (24 FPS) | *Vasco* |

> **Nota:**  
> Além dos objetos animados por zona, a cena 3D global inclui a mesa redonda, lugares postos (pratos, garfos, facas), tapete e lâmpada, modelados pelos elementos do grupo e disponibilizados na pasta `Blender/` e `Data/`. Estes objetos foram modelados por ambos os membros sendo escolhido os mais adequados para a cena final.

---

## Estrutura do Repositório

```text
TrabalhoComputa-oVisual/
├── Animacoes/
│   └── assets/                  # Sequências de frames PNG em RGBA (fundo transparente)
│       ├── zona1_cadeira/       # Frames da animação da Zona 1
│       ├── zona2_copo/          # Frames da animação da Zona 2
│       └── zona3_vela/          # Frames da animação da Zona 3
├── Blender/                     # Ficheiros originais de modelação (.blend em Blender 5.2 LTS)
│   ├── cadeira_cor.blend
│   ├── Cadeira.blend
│   ├── Copo.blend
│   ├── Faca.blend
│   ├── Garfo.blend
│   ├── Lampada.blend
│   ├── mesa.blend
│   ├── prato.blend
│   ├── Tapete.blend
│   ├── vela.blend
│   └── vela.blend1
├── Data/                        # Cenas e texturas
│   ├── texturas/
│   ├── cena1.blend
│   └── cena1.blend1
├── src/                         # Código-fonte Python
│   ├── script.py                # Script principal
│   └── teste_camara.py          # Script auxiliar de teste de captura de câmara
├── .gitattributes
└── README.md                    # Documentação do projeto
```

---

## Instruções para Correr

### 1. Pré-requisitos
**Python 3.8+** , juntamente com a biblioteca **OpenCV**.

```bash
pip install opencv-python
```

### 2. Passos de Execução

1. **Clonar / Abrir a pasta do projeto no terminal:**
   ```bash
   cd TrabalhoComputa-oVisual
   ```

2. **Testar a Webcam (Opcional):**  
   Para verificar se a tua câmara/webcam está a funcionar corretamente:
   ```bash
   python src/teste_camara.py
   ```
   * Pressiona a tecla `q` ou fecha a janela com o rato para fechar a aplicação de teste.

3. **Executar a Aplicação Principal:**
   ```bash
   python src/script.py
   ```

4. **Como utilizar:**
   - O ecrã mostrará a imagem da câmara dividida em **3 Zonas** por linhas brancas.
   - Movimenta a mão numa das zonas para ativar a animação do respetivo objeto (`Cadeira` na Zona 1, `Copo` na Zona 2, `Vela` na Zona 3).
   - As caixas delimitadoras a verde (`cv2.rectangle`) identificam a região onde o movimento foi detetado.
   - **Para Terminar:** Pressiona a tecla **`q`** ou fecha a janela de exibição.

---

## Explicação Técnica da Solução

1. **Modelação e Renderização 3D (Blender 5.2 LTS):**
   - Todos os objetos foram modelados manualmente.
   - As animações foram exportadas em sequências de ficheiros PNG com fundo transparente, resolução proporcional em formato RGBA.

2. **Deteção de Movimento e Visão Computacional (OpenCV):**
   - **Captura:** `cv2.VideoCapture(0)` com espelhamento horizontal (`cv2.flip(frame, 1)`) para ser mais intuitivo.
   - **Algoritmo de Movimento:** Diferença absoluta entre frames consecutivos (`cv2.absdiff`), conversão para escala de cinzentos, suavização gaussiana (`cv2.GaussianBlur`), limiarização binária (`cv2.threshold`) e dilatação morfologia (`cv2.dilate`).
   - **Contornos e Zonas:** Cálculo de contornos (`cv2.findContours`) com filtro por área mínima (>1000px). O centro X do vetor delimitador (`boundingRect`) calcula em qual das 3 zonas o movimento ocorreu.
   - **Composição Alfa:** Algoritmo de mistura alfa (*Alpha Blending*) em tempo real que calcula a transparência píxel a píxel (`alfa * png + (1 - alfa) * roi`) sobrepondo a animação frame a frame com persistência temporal.

---

## Declaração do Uso de IA na Escrita de Código

Em cumprimento com as regras e diretrizes estabelecidas na ficha de unidade curricular:

- **Ferramentas de IA Utilizadas:** ChatGPT / Claude / Gemini.
- **Onde foi utilizada:**
  1. **Função `sobrepor()` em `src/script.py`:** Auxílio na lógica matemática de *clipping* e mistura dos canais RGBA (`alfa = png[:, :, 3:4] / 255.0`) para evitar erros de índice nas margens da janela.
  2. **Tratamento de persistência temporal em `src/script.py`:** Estruturação da lógica de temporização (`time.time()`) para manter a animação ativa durante um intervalo configurável (`PERSISTENCIA = 0.7s`) após o fim do movimento.
  3. **Elaboração da documentação em `README.md`:** Formatação em sintaxe Markdown e organização da estrutura do ficheiro de acordo com o guião de avaliação.
- **Garantia de Conformidade:** NENHUM modelo de Aprendizagem Automática ou Redes Neuronais (YOLO, MediaPipe, etc.) foi utilizado na aplicação para deteção de movimento, sendo esta realizada exclusivamente através de técnicas clássicas de processamento de imagem em OpenCV.