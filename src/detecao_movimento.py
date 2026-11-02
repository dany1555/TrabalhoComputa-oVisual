
import cv2

# Abrir a webcam
camera = cv2.VideoCapture(0)

# Verificar se a webcam abriu corretamente
if not camera.isOpened():
    print("Erro: não foi possível abrir a webcam.")
    exit()

# Guardar o primeiro frame
leitura, frame_anterior = camera.read()

if not leitura:
    print("Erro ao ler a imagem da webcam.")
    camera.release()
    exit()

# Converter o primeiro frame para cinzento
frame_anterior = cv2.cvtColor(frame_anterior, cv2.COLOR_BGR2GRAY)

# Suavizar a imagem
frame_anterior = cv2.GaussianBlur(frame_anterior, (21, 21), 0)

while True:
    # Ler um novo frame da webcam
    leitura, frame = camera.read()

    if not leitura:
        break

    # Converter o frame atual para cinzento
    frame_cinzento = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Suavizar a imagem
    frame_cinzento = cv2.GaussianBlur(
        frame_cinzento, (21, 21), 0
    )

    # Comparar o frame atual com o anterior
    diferenca = cv2.absdiff(frame_anterior, frame_cinzento)

    # Aplicar um limiar para destacar o movimento
    _, limiar = cv2.threshold(
        diferenca, 25, 255, cv2.THRESH_BINARY
    )

    # Aumentar as zonas brancas para juntar regiões próximas
    dilatacao = cv2.dilate(limiar, None, iterations=2)

    # Encontrar os contornos das zonas com movimento
    contornos, _ = cv2.findContours(
        dilatacao,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Analisar cada contorno encontrado
    for contorno in contornos:

        # Ignorar zonas demasiado pequenas
        if cv2.contourArea(contorno) < 1000:
            continue

        # Calcular o retângulo da zona com movimento
        x, y, largura, altura = cv2.boundingRect(contorno)

        # Desenhar o retângulo no vídeo
        cv2.rectangle(
            frame,
            (x, y),
            (x + largura, y + altura),
            (0, 255, 0),
            2
        )

        # Escrever uma mensagem
        cv2.putText(
            frame,
            "Movimento",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # Mostrar o vídeo com os retângulos
    cv2.imshow("Detecao de Movimento", frame)

    # Atualizar o frame anterior
    frame_anterior = frame_cinzento.copy()

    # Sair quando carregar na tecla Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Fechar a webcam e as janelas
camera.release()
cv2.destroyAllWindows()
