import cv2

def get_qr_code_image(qr_code):
    img = cv2.imread(qr_code)
    cv2.imshow('a', img)
    cv2.waitKey(0) 

    return cv2.QRCodeDetector().detectAndDecode(img)

val, pts, st_code = get_qr_code_image(r"qr_code/chunk_1.png")
print('#'*20, type(val), len(val))
print(val)