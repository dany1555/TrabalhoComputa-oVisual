import cv2
import numpy as np
import time
from pathlib import Path

N_ZONAS = 5
PERSISTENCIA = 0.7   # segundos que a zona fica ativa depois do último movimento
FPS_ANIM = [12, 24, 24, 24, 24]               # velocidade da animação (frames por segundo)
TAMANHO_REL = [1.1, 1.1, 1.1, 1.1, 1.1]      # tamanho relativo de cada animação
RECORTAR = [False, False, False, False, False] # True = tira as margens transparentes dos PNGs
FRAMES_APRENDIZAGEM = 40   # frames iniciais para o MOG2 aprender o fundo

# Pasta do projeto = uma pasta acima de src/ (funciona de qualquer sítio)
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "Animacoes" / "assets"
PASTAS = ["zona1_cadeira", "zona2_copo", "zona3_vela", "Zona4_Salgueiro", "Zona5_jarro"]


def carregar(pasta, tamanho, recortar=False):
    """Lê todos os PNGs da pasta (com alfa) e redimensiona para tamanho x tamanho."""
    ficheiros = sorted((ASSETS / pasta).glob("*.png"))
    if not ficheiros:
        raise SystemExit(f"Não encontrei PNGs em: {ASSETS / pasta}")
    imgs = []
    for f in ficheiros:
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)   # UNCHANGED = mantém o alfa
        if img is None or img.ndim < 3 or img.shape[2] != 4:
            raise SystemExit(f"Ficheiro sem canal alfa (RGBA): {f}")
        imgs.append(img)

    if recortar:
        # corta as margens transparentes (a mesma caixa em todos os frames)
        alfa_max = np.max([im[:, :, 3] for im in imgs], axis=0)
        ys, xs = np.where(alfa_max > 10)
        if len(xs):
            imgs = [im[ys.min():ys.max() + 1, xs.min():xs.max() + 1] for im in imgs]

    frames = []
    for img in imgs:
        if recortar:
            # mantém as proporções e centra numa tela quadrada transparente
            h, w = img.shape[:2]
            esc = tamanho / max(h, w)
            nw, nh = max(int(w * esc), 1), max(int(h * esc), 1)
            peq = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
            tela = np.zeros((tamanho, tamanho, 4), dtype="uint8")
            oy, ox = (tamanho - nh) // 2, (tamanho - nw) // 2
            tela[oy:oy + nh, ox:ox + nw] = peq
            frames.append(tela)
        else:
            frames.append(cv2.resize(img, (tamanho, tamanho), interpolation=cv2.INTER_AREA))
    print(f"{pasta}: {len(frames)} frames carregados")
    return frames


def sobrepor(fundo, png, x, y):
    """Cola um PNG com alfa sobre o frame; corta o que sair da imagem."""
    H, W = fundo.shape[:2]
    h, w = png.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    png = png[y0 - y:y1 - y, x0 - x:x1 - x]
    roi = fundo[y0:y1, x0:x1]
    alfa = png[:, :, 3:4] / 255.0
    roi[:] = (alfa * png[:, :, :3] + (1 - alfa) * roi).astype("uint8")


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Não foi possível abrir a câmara")

# Ler um frame só para saber o tamanho da câmara e preparar as animações
ok, frame = cap.read()
if not ok:
    raise SystemExit("Não consegui ler a câmara")
frame = cv2.flip(frame, 1)
altura, largura = frame.shape[:2]
tamanho = [int(altura * r) for r in TAMANHO_REL]

animacoes = [carregar(p, t, r) for p, t, r in zip(PASTAS, tamanho, RECORTAR)]

# Subtração de fundo MOG2: aprende o fundo e devolve o que é "novo" na imagem.
# detectShadows=True marca as sombras a 127 (removidas mais abaixo).
subtrator = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

ultimo = [0.0] * N_ZONAS         # última vez que houve movimento em cada zona
inicio = [0.0] * N_ZONAS         # quando a animação de cada zona (re)começou
estava_ativa = [False] * N_ZONAS
n_frames = 0

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.flip(frame, 1)   # espelhar
    n_frames += 1
    agora = time.time()

    # --- deteção de movimento (subtração de fundo MOG2) ---
    mascara = subtrator.apply(frame)
    _, mascara = cv2.threshold(mascara, 250, 255, cv2.THRESH_BINARY)   # remove sombras (127)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)        # remove ruído
    mascara = cv2.dilate(mascara, kernel, iterations=2)

    aprendendo = n_frames < FRAMES_APRENDIZAGEM
    if not aprendendo:
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            if cv2.contourArea(c) < 1000:
                continue
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cx = x + w // 2
            zona = min(cx * N_ZONAS // largura, N_ZONAS - 1)
            ultimo[zona] = agora

    # --- animações das zonas ativas ---
    for z in range(N_ZONAS):
        ativa = (agora - ultimo[z]) < PERSISTENCIA
        if ativa and not estava_ativa[z]:
            inicio[z] = agora            # animação recomeça do frame 1
        estava_ativa[z] = ativa

        if ativa:
            anim = animacoes[z]
            t = tamanho[z]
            i = int((agora - inicio[z]) * FPS_ANIM[z]) % len(anim)
            x0 = z * largura // N_ZONAS
            x1 = (z + 1) * largura // N_ZONAS
            px = x0 + (x1 - x0 - t) // 2                # centrar na zona
            py = (altura - t) // 2
            sobrepor(frame, anim[i], px, py)

    # --- linhas divisórias e nomes das zonas ---
    for z in range(N_ZONAS):
        x0 = z * largura // N_ZONAS
        if z > 0:
            cv2.line(frame, (x0, 0), (x0, altura), (255, 255, 255), 2)
        cv2.putText(frame, f"Zona {z + 1}", (x0 + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if aprendendo:
        cv2.putText(frame, "A aprender o fundo...", (10, altura - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Projeto", frame)
    # cv2.imshow("Mascara MOG2", mascara)   # descomenta para ver a máscara

    tecla = cv2.waitKey(1) & 0xFF
    fechada = cv2.getWindowProperty("Projeto", cv2.WND_PROP_VISIBLE) < 1
    if tecla == ord("q") or fechada:
        break

cap.release()
cv2.destroyAllWindows()