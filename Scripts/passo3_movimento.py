import cv2
import time
from pathlib import Path

N_ZONAS = 3
PERSISTENCIA = 0.7   # segundos que a zona fica ativa depois do último movimento
FPS_ANIM = [12, 24, 24]        # velocidade da animação (frames por segundo)
TAMANHO_REL = [0.85, 1.1, 1.1]        # tamanho relativo de cada animação

# Pasta do projeto = uma pasta acima de Scripts/ (funciona de qualquer sítio)
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "Animacoes" / "assets"
PASTAS = ["zona1_cadeira", "zona2_copo", "zona3_vela"]


def carregar(pasta, tamanho):
    """Lê todos os PNGs da pasta (com alfa) e redimensiona para tamanho x tamanho."""
    ficheiros = sorted((ASSETS / pasta).glob("*.png"))
    if not ficheiros:
        raise SystemExit(f"Não encontrei PNGs em: {ASSETS / pasta}")
    frames = []
    for f in ficheiros:
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)   # UNCHANGED = mantém o alfa
        if img is None or img.ndim < 3 or img.shape[2] != 4:
            raise SystemExit(f"Ficheiro sem canal alfa (RGBA): {f}")
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

# Ler um frame só para saber o tamanho da câmara e preparar as animações
ok, frame = cap.read()
if not ok:
    raise SystemExit("Não consegui ler a câmara")
altura, largura = frame.shape[:2]
tamanho = [int(altura * r) for r in TAMANHO_REL]

animacoes = [carregar(p, t) for p, t in zip(PASTAS, tamanho)]

anterior = None
ultimo = [0.0] * N_ZONAS         # última vez que houve movimento em cada zona
inicio = [0.0] * N_ZONAS         # quando a animação de cada zona (re)começou
estava_ativa = [False] * N_ZONAS

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.flip(frame, 1)   # espelhar

    # --- deteção de movimento ---
    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
    if anterior is None:
        anterior = cinza
        continue
    diff = cv2.absdiff(anterior, cinza)
    anterior = cinza
    _, mascara = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    mascara = cv2.dilate(mascara, None, iterations=2)

    agora = time.time()
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contornos:
        if cv2.contourArea(c) < 1500:
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
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Projeto", frame)

    tecla = cv2.waitKey(1) & 0xFF
    fechada = cv2.getWindowProperty("Projeto", cv2.WND_PROP_VISIBLE) < 1
    if tecla == ord("q") or fechada:
        break

cap.release()
cv2.destroyAllWindows()