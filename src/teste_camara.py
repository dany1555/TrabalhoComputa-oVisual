import cv2

cap = cv2.VideoCapture(0)

while True:
    ok, frame = cap.read()
    if not ok:
        print("Não consegui ler a câmara")
        break

    cv2.imshow("Teste", frame)

    # sai se carregares em q OU se fechares a janela com o X
    tecla = cv2.waitKey(1) & 0xFF
    janela_fechada = cv2.getWindowProperty("Teste", cv2.WND_PROP_VISIBLE) < 1
    if tecla == ord("q") or janela_fechada:
        break

cap.release()
cv2.destroyAllWindows()