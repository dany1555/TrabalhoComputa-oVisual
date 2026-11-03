import cv2
import numpy as np
import time
from pathlib import Path

N_ZONAS = 5
PERSISTENCIA = 0.7   # segundos que a zona fica ativa depois do último movimento
FPS_ANIM = [12, 24, 24, 24, 24]               # velocidade da animação (frames por segundo)
TAMANHO_REL = [1.1, 1.1, 1.1, 1.1, 1.1]      # tamanho relativo de cada animação
FRAMES_APRENDIZAGEM = 40   # frames iniciais para o MOG2 aprender o fundo
HISTORY_MOG2 = 500

# Pasta do projeto = uma pasta acima de src/ (funciona de qualquer sítio)
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "Animacoes" / "assets"
PASTAS = ["zona1_cadeira", "zona2_copo", "zona3_vela", "Zona4_Salgueiro", "Zona5_jarro"]

JANELA = "Projeto"
JANELA_CONTROLOS = "Controlos"
RESOLUCAO_CAMERA = (640, 480)
TAMANHO_JANELA_INICIAL = (480, 360)
SLIDER_SENSIBILIDADE = "Sensibilidade"
SLIDER_AREA = "Area minima"
SLIDER_AUTO = "Auto fundo"


def criar_subtrator(limiar):
    return cv2.createBackgroundSubtractorMOG2(
        history=HISTORY_MOG2,
        varThreshold=limiar,
        detectShadows=True
    )


def carregar(pasta, tamanho):
    # Lê todos os PNGs da pasta (com alfa) e redimensiona para tamanho x tamanho.
    ficheiros = sorted((ASSETS / pasta).glob("*.png"))
    if not ficheiros:
        raise SystemExit(f"Não encontrei PNGs em: {ASSETS / pasta}")

    imgs = []
    for f in ficheiros:
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)  # UNCHANGED = mantém o alfa
        if img is None or img.ndim < 3 or img.shape[2] != 4:
            raise SystemExit(f"Ficheiro sem canal alfa (RGBA): {f}")
        imgs.append(img)

    frames = []
    for img in imgs:
        frames.append(cv2.resize(img, (tamanho, tamanho), interpolation=cv2.INTER_AREA))

    print(f"{pasta}: {len(frames)} frames carregados")
    return frames


def sobrepor(fundo, png, x, y):
    # Cola um PNG com alfa sobre o frame; corta o que sair da imagem.
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

cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCAO_CAMERA[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCAO_CAMERA[1])

# Ler um frame só para saber o tamanho da câmara e preparar as animações
ok, frame = cap.read()
if not ok:
    cap.release()
    raise SystemExit("Não consegui ler a câmara")

frame = cv2.flip(frame, 1)
frame = cv2.resize(frame, RESOLUCAO_CAMERA, interpolation=cv2.INTER_AREA)
altura, largura = frame.shape[:2]
tamanho = [int(altura * r) for r in TAMANHO_REL]

try:
    animacoes = [carregar(p, t) for p, t in zip(PASTAS, tamanho)]
except Exception:
    cap.release()
    raise

# Criar a janela redimensionável. Os controlos ficam separados para não
# imporem uma largura mínima à janela da imagem.
cv2.namedWindow(JANELA, cv2.WINDOW_NORMAL)
cv2.namedWindow(JANELA_CONTROLOS, cv2.WINDOW_NORMAL)
cv2.createTrackbar(SLIDER_SENSIBILIDADE, JANELA_CONTROLOS, 50, 200, lambda v: None)
cv2.createTrackbar(SLIDER_AREA, JANELA_CONTROLOS, 1000, 5000, lambda v: None)
cv2.createTrackbar(SLIDER_AUTO, JANELA_CONTROLOS, 1, 1, lambda v: None)
cv2.resizeWindow(JANELA, *TAMANHO_JANELA_INICIAL)
cv2.resizeWindow(JANELA_CONTROLOS, 400, 150)

limiar_atual = 50
subtrator = criar_subtrator(limiar_atual)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

ultimo = [0.0] * N_ZONAS         # última vez que houve movimento em cada zona
inicio = [0.0] * N_ZONAS         # quando a animação de cada zona (re)começou
estava_ativa = [False] * N_ZONAS
n_frames = 0

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1) # espelhar horizontalmente para ser mais intuitivo
        frame = cv2.resize(frame, RESOLUCAO_CAMERA, interpolation=cv2.INTER_AREA)
        n_frames += 1
        agora = time.monotonic()

        # Ler os controlos. O varThreshold mais baixo torna a deteção mais sensível.
        limiar = max(cv2.getTrackbarPos(SLIDER_SENSIBILIDADE, JANELA_CONTROLOS), 1)
        area_min = cv2.getTrackbarPos(SLIDER_AREA, JANELA_CONTROLOS)
        auto_fundo = cv2.getTrackbarPos(SLIDER_AUTO, JANELA_CONTROLOS) == 1

        if limiar != limiar_atual:
            subtrator.setVarThreshold(limiar)
            limiar_atual = limiar

        # Nos primeiros frames, o MOG2 aprende continuamente para inicializar o fundo.
        aprendendo = n_frames <= FRAMES_APRENDIZAGEM
        if aprendendo:
            mascara = subtrator.apply(frame)
        else:
            if auto_fundo:
                mascara = subtrator.apply(frame)
            else:
                mascara = subtrator.apply(frame, learningRate=0)

        # Remover sombras e limpar ruído da máscara.
        _, mascara = cv2.threshold(mascara, 250, 255, cv2.THRESH_BINARY)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
        mascara = cv2.dilate(mascara, kernel, iterations=2)

        if not aprendendo: # não desenhar contornos durante a aprendizagem do fundo
            contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contornos:
                if cv2.contourArea(c) < area_min:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cx = x + w // 2
                zona = min(cx * N_ZONAS // largura, N_ZONAS - 1)
                ultimo[zona] = agora

        # animações das zonas ativas
        for z in range(N_ZONAS):
            ativa = (agora - ultimo[z]) < PERSISTENCIA
            if ativa and not estava_ativa[z]:
                inicio[z] = agora  # animação recomeça do frame 1
            estava_ativa[z] = ativa

            if ativa:
                anim = animacoes[z]
                t = tamanho[z]
                i = int((agora - inicio[z]) * FPS_ANIM[z]) % len(anim)
                x0 = z * largura // N_ZONAS
                x1 = (z + 1) * largura // N_ZONAS
                px = x0 + (x1 - x0 - t) // 2
                py = (altura - t) // 2
                sobrepor(frame, anim[i], px, py)

        # linhas divisórias, nomes das zonas e estado dos controlos
        for z in range(N_ZONAS):
            x0 = z * largura // N_ZONAS
            if z > 0:
                cv2.line(frame, (x0, 0), (x0, altura), (255, 255, 255), 2)
            cv2.putText(frame, f"Zona {z + 1}", (x0 + 10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if aprendendo:
            estado_fundo = "A aprender o fundo..."
        elif auto_fundo:
            estado_fundo = "Fundo: automatico"
        else:
            estado_fundo = "Fundo: congelado"

        cv2.putText(frame, estado_fundo, (10, altura - 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        cv2.putText(frame, f"Sensibilidade: {limiar} | Area minima: {area_min} px",
                    (10, altura - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Apresentar a imagem à escala da janela evita que os 640 px da câmara
        # imponham uma largura mínima e permite redimensioná-la horizontalmente.
        _, _, janela_largura, janela_altura = cv2.getWindowImageRect(JANELA)
        display_largura = max(janela_largura, 1)
        display_altura = max(janela_altura, 1)
        frame_display = cv2.resize(
            frame,
            (display_largura, display_altura),
            interpolation=cv2.INTER_AREA
        )
        cv2.imshow(JANELA, frame_display)

        tecla = cv2.waitKey(1) & 0xFF
        fechada = cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1
        if tecla == ord("q") or fechada:
            break

        # 'r' reinicia o modelo e volta a fazer a aprendizagem inicial do fundo.
        if tecla == ord("r"):
            subtrator = criar_subtrator(limiar_atual)
            n_frames = 0
            ultimo = [0.0] * N_ZONAS
            inicio = [0.0] * N_ZONAS
            estava_ativa = [False] * N_ZONAS

finally:
    cap.release()
    cv2.destroyAllWindows()