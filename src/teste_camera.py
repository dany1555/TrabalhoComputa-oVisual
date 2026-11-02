import cv2
import numpy as np

LARGURA_PAINEL = 320   # largura de cada painel na grelha (reduz se o ecrã for pequeno)
JANELA = "Visualizacao MOG2"


def criar_subtrator(limiar):
    return cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=limiar, detectShadows=True)


def painel(img, titulo): # definir função para redimensionar e adicionar título
    """Redimensiona para a largura do painel, garante 3 canais e escreve o título."""
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    h, w = img.shape[:2]
    img = cv2.resize(img, (LARGURA_PAINEL, int(h * LARGURA_PAINEL / w)))
    cv2.rectangle(img, (0, 0), (img.shape[1], 28), (0, 0, 0), -1)
    cv2.putText(img, titulo, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def mascara_bruta_colorida(m):
    """MOG2 devolve 0 (fundo), 127 (sombra) ou 255 (movimento). Damos uma cor a cada."""
    out = np.zeros((*m.shape, 3), dtype="uint8")
    out[m == 127] = (255, 120, 0)     # sombra  -> azul
    out[m == 255] = (255, 255, 255)   # movimento -> branco
    return out


def painel_legenda(altura, largura): # os valores a frente sao a cor do texto
    img = np.zeros((altura, largura, 3), dtype="uint8")
    linhas = [
        ("LEGENDA", (255, 255, 255)),
        ("", None),
        ("Preto  = fundo (ignorado)", (180, 180, 180)),
        ("Azul   = sombra (descartada)", (255, 120, 0)),
        ("Branco = movimento", (255, 255, 255)),
        ("Verde  = movimento aceite", (0, 255, 0)),
        ("", None),
        ("q = sair", (0, 255, 255)),
        ("r = reaprender fundo", (0, 255, 255)),
    ]
    y = 35
    for texto, cor in linhas: # cola o texto na imagem, se houver texto
        if texto:
            cv2.putText(img, texto, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1, cv2.LINE_AA)
        y += 24
    return img


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Não foi possível abrir a câmara")

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

cv2.namedWindow(JANELA)
cv2.createTrackbar("Sensibilidade (menor = mais sensivel)", JANELA, 50, 200, lambda v: None)
cv2.createTrackbar("Area minima", JANELA, 1000, 5000, lambda v: None)

limiar_atual = 50
subtrator = criar_subtrator(limiar_atual)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)

    # ler sliders (varThreshold mínimo 1)
    limiar = max(cv2.getTrackbarPos("Sensibilidade (menor = mais sensivel)", JANELA), 1)
    area_min = cv2.getTrackbarPos("Area minima", JANELA)
    if limiar != limiar_atual:
        subtrator.setVarThreshold(limiar)
        limiar_atual = limiar

    # pipeline (igual ao script original)
    bruta = subtrator.apply(frame)                                   # 0 / 127 / 255
    _, sem_sombras = cv2.threshold(bruta, 250, 255, cv2.THRESH_BINARY)
    aberta = cv2.morphologyEx(sem_sombras, cv2.MORPH_OPEN, kernel)   # tira ruído
    final = cv2.dilate(aberta, kernel, iterations=2)                 # une bocados

    # fundo que o MOG2 aprendeu
    fundo = subtrator.getBackgroundImage()
    if fundo is None:
        fundo = np.zeros_like(frame)

    # resultado: fundo escurecido, movimento a cores + contornos aceites
    resultado = (frame * 0.2).astype("uint8")
    resultado[final > 0] = frame[final > 0]
    contornos, _ = cv2.findContours(final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    n_aceites = 0
    for c in contornos:
        if cv2.contourArea(c) < area_min:
            continue
        n_aceites += 1
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(resultado, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.drawContours(resultado, [c], -1, (0, 255, 0), 1)

    # montar a grelha 2x3
    p1 = painel(frame, "1. Camara")
    p2 = painel(fundo, "2. Fundo aprendido")
    p3 = painel(mascara_bruta_colorida(bruta), "3. MOG2 bruto (sombras a azul)")
    p4 = painel(sem_sombras, "4. Sem sombras (threshold 250)")
    p5 = painel(final, "5. Limpo (open + dilate)")
    p6 = painel(resultado, f"6. Resultado - {n_aceites} objeto(s)")

    altura_painel = p1.shape[0]
    p7 = painel_legenda(altura_painel, LARGURA_PAINEL)

    vazio = np.zeros_like(p1)
    linha1 = np.hstack([p1, p2, p3, p7])
    linha2 = np.hstack([p4, p5, p6, vazio])
    cv2.imshow(JANELA, np.vstack([linha1, linha2]))

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord("q") or cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:
        break
    if tecla == ord("r"):
        subtrator = criar_subtrator(limiar_atual)

cap.release()
cv2.destroyAllWindows()