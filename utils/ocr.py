import easyocr


reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def extract_text_from_image(image_path):

    result = reader.readtext(
        image_path,
        detail=0
    )

    return " ".join(result)