# Trabalho de Computação Visual — A Cena Reage ao Movimento

**Curso:** Licenciatura em Engenharia de Sistemas de Informação / LESTI (ISE) — Universidade do Algarve  
**Unidade Curricular:** Computação Visual (2026/27)  
**Projeto de Grupo:** Vasco Matos a85234 Daniel Martins a85281  

---

## Tema do Projeto

O projeto teve como base o desenvolvimento de um programa que, atravez de uma camera anexa ao computador, seja verificado movimento numa determinada area, gerando assim uma animação. Essa animação sendo criada em Blender fazendo parte de uma cena de uma explanada.

---

## Tabela das Zonas

| Zona | Objeto Associado | Animação | Quem Modelou |
| :---: | :--- | :--- | :--- |
| **Zona 1**  | **Cadeira** (`zona1_cadeira`) | Rotação/animação em ciclo da cadeira da esplanada (12 FPS) | *Daniel* |
| **Zona 2**  | **Copo** (`zona2_copo`) | Animação do copo de vidro em ciclo (24 FPS) | *Daniel* |
| **Zona 3**  | **Vela** (`zona3_vela`) | Animação da vela com chama/movimento em ciclo (12 FPS) | *Vasco* |
| **Zona 4** | **Saleiro** (`Zona4_Saleiro`) | Animação Saleiro em ciclo (24 FPS) | Daniel |
| **Zona 5**  | **Jarro** (`Zona5_jarro`) | Animação de um jarro em ciclo (24 FPS) | *Vasco* |


> **Nota:**  
> Além dos objetos animados por zona, a cena 3D global inclui a mesa redonda, lugares postos (pratos, garfos, facas), tapete e lâmpada, um saleiro e um jarro de água, na pasta `Blender/` e `Data/`. Estes objetos foram modelados por ambos os membros sendo escolhido os mais adequados para a cena final.

---

## Estrutura do Repositório

```text
TrabalhoComputa-oVisual/
├── Animacoes/
│   └── assets/                     # Sequências de frames PNG em RGBA (fundo transparente)
│       ├── zona1_cadeira/          # Frames de animação da Zona 1
│       ├── zona2_copo/             # Frames de animação da Zona 2
│       ├── zona3_vela/             # Frames de animação da Zona 3
│       ├── zona4_Salgueiro/        # Frames de animação (adicionais)
│       └── zona5_Jarro/            # Frames de animação (adicionais)
├── Blender/                        # Ficheiros originais de modelação (.blend)
│   ├── cadeira_cor.blend
│   ├── Cadeira.blend
│   ├── Copo.blend
│   ├── Faca.blend
│   ├── Garfo.blend
│   ├── Jarro.blend
│   ├── Lampada.blend
│   ├── mesa.blend
│   ├── prato.blend
│   ├── Saleiro.blend
│   ├── Tapete.blend
│   └── vela.blend
├── Data/                           # Cenas e texturas
│   ├── texturas/
│   ├── cena1.blend
│   └── cena1-Tudo.blend
├── src/                            # Código-fonte Python
│   ├── script.py                   # Script principal da aplicação
│   └── teste_camera.py             # Script de teste e calibração do MOG2 com grelha visual
├── .gitattributes
└── README.md                       # Documentação do projeto
```


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

2. **Testar e Calibrar a Câmara com MOG2 (`teste\_camera.py`):**

   Para testar a câmara e visualizar em tempo real os diferentes passos do algoritmo de subtração de fundo (com painéis para o fundo aprendido, máscara bruta com sombras, imagem limpa e resultados com sliders de sensibilidade e área mínima):

```
   python src/teste\_camera.py
   
   ```

   * *Teclas úteis:* Pressiona **`q`** para sair ou **`r`** para reaprender o fundo instantaneamente.

3. **Executar a Aplicação Principal:**
   ```bash
   python src/script.py
   ```

4. **Como utilizar:**

   * O ecrã mostra a imagem da câmara dividida em **5 Zonas** por linhas brancas.
   * Movimenta-te ou coloca objetos nas zonas para ativar as respetivas animações.
   * O fundo adapta-se de forma inteligente a alterações reais do ambiente (como variações na luz do dia ou se alguém deslocar uma cadeira).
   * **Para Terminar:** Pressiona a tecla **`q`** ou fecha a janela.

---


## Explicação Técnica da Solução

1. **Modelação e Renderização 3D (Blender):**

   * Objetos modelados manualmente e exportados em sequências de imagens PNG com canal alfa (RGBA) para garantir transparências limpas.
2. **Deteção de Movimento e Atualização de Fundo (OpenCV - MOG2):**

   * **Subtração de Fundo Adaptativa:** Utilizamos o **`cv2.createBackgroundSubtractorMOG2`** para detetar o fundo e as alterações sobre o mesmo (que representa movimento).
   * **Adaptação Dinâmica:** O fundo está continuamente a atualizar-se de forma automática para refletir situações reais onde as condições de luz mudam gradualmente (ex: luz solar a entrar pela janela) ou se houver alteração de elementos estáticos (ex: mover uma cadeira de sítio). Dispõe também da opção de congelar o fundo ou reiniciá-lo premindo a tecla `r`.
   * **Filtragem Morfológica e Contornos:** Remoção de sombras detetadas pelo MOG2, aplicação de operações de abertura (*morphology open*) para remoção de ruído e dilatação para unir componentes conexos. O centro horizontal (`cx`) da caixa delimitadora (`boundingRect`) determina em qual das zonas o movimento ocorreu.
   * **Composição Alfa (*Alpha Blending*):** Mistura suave píxel a píxel (`alfa \* png + (1 - alfa) \* roi`) para sobrepor as animações na imagem da câmara, complementada por um mecanismo de persistência temporal (`PERSISTENCIA = 0.7s`) para manter a animação fluida após o fim do movimento.

---

### Controlo em Tempo Real (HUD e Sliders)

Durante a execução da aplicação, o ecrã apresenta em tempo real um conjunto de informações (*HUD*) na parte inferior e disponibiliza controlos interativos através de barras de deslize (*sliders*) na janela:

* **Sliders de Controlo:**
  * **Sensibilidade:** Permite ajustar o limiar (`varThreshold`) do algoritmo MOG2. Valores mais baixos tornam a deteção de movimento mais sensível a pequenas alterações, enquanto valores mais altos exigem mudanças maiores para acionar as animações.
  * **Área Mínima (px):** Define o limiar mínimo de píxeis para que um contorno detetado seja considerado válido. Evita que pequenos ruídos na imagem ativem as zonas sem necessidade.
  * **Atualizar Fundo (0/1):** Permite ligar (`1`) ou desligar (`0`) a atualização dinâmica do modelo de fundo do MOG2. Quando desligado, o fundo fica congelado (útil para evitar que alterações temporárias na iluminação afetem o programa); quando ligado, o sistema adapta-se gradualmente ao ambiente.
* **Atalhos e Informação no HUD:**
  * O ecrã indica o estado atual do fundo em tempo real (*"A aprender o fundo..."*, *"Fundo: automático"* ou *"Fundo: congelado"*).
  * Pressionar a tecla **`r`** permite reiniciar instantaneamente o subtrator e forçar uma nova aprendizagem inicial do fundo.
  * Pressionar **`q`** ou fechar a janela encerra a aplicação de forma segura.

---

## Declaração do Uso de IA

Em cumprimento com as regras e diretrizes estabelecidas na ficha de unidade curricular:

- **Ferramentas de IA Utilizadas:** ChatGPT / Claude / Gemini. (foi utilizado os 3 llm principalmente por gastar os tokens gratuitos de cada um)
-1. **Função `sobrepor()` em `src/script.py`:** Auxílio na estruturação matemática do cálculo de mistura dos canais RGBA e tratamento de limites de recorte (*clipping*) nas margens da janela.
2. **Gestão de Persistência Temporal e Controlo de Tempos:** Apoio na lógica de temporização baseada em `time.monotonic()` para gerir o tempo de permanência ativa das animações por zona.
3. **Elaboração da Documentação (`README.md`):** Organização e formatação da estrutura em Markdown para apresentação do projeto.
4. **Integração de MOG2:** Inicialmente foi feito a deteção de movimento atravez de diferença de pixeis. Mais tarde foi decidido alterar para comparação com o fundo. Entao foi utilizado ajuda de IA para fazer essa transição

*Nota:* Em todos os momentos da organização em que foi utilizado IA foi utilizado de forma ética e consciente. Todo o codigo e texto presente foi revisto e alterado manualmente no caso de o necessitar.
Os modelos foram totalmente feitos com as ferramentas utilizadas em aula.