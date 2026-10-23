import cv2

cap = cv2.VideoCapture(0)
anterior = None

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # 1) cinzento + desfocar (menos ruído)
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cinza = cv2.GaussianBlur(cinza, (21, 21), 0)

    # no primeiro frame ainda não há "anterior" para comparar
    if anterior is None:
        anterior = cinza
        continue

    # 2) diferença entre o frame anterior e o atual
    diff = cv2.absdiff(anterior, cinza)
    anterior = cinza

    # 3) limiar: o que mudou muito fica branco, o resto preto
    _, mascara = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    # 4) dilatar: junta pedaços brancos próximos numa mancha só
    mascara = cv2.dilate(mascara, None, iterations=2)

    # 5) encontrar as manchas e desenhar uma caixa em cada
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contornos:
        if cv2.contourArea(c) < 1500:   # ignora manchas pequenas (ruído)
            continue
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Movimento", frame)
    cv2.imshow("Mascara", mascara)   # só para perceberes o que o programa "vê"

    tecla = cv2.waitKey(1) & 0xFF
    fechada = cv2.getWindowProperty("Movimento", cv2.WND_PROP_VISIBLE) < 1
    if tecla == ord("q") or fechada:
        break

cap.release()
cv2.destroyAllWindows()