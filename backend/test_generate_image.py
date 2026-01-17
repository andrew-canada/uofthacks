from services import image_generator
import base64, sys

prompt = "A stylish product photo: moody lighting, dark academia, trench coat on model, cinematic"
b64 = image_generator.generate_image_base64(prompt, size='1024x1024')
if not b64:
    print("No image generated (Gemini client missing or API key not set).")
    sys.exit(1)

img_bytes = base64.b64decode(b64)
with open('out_generated.png', 'wb') as f:
    f.write(img_bytes)
print('Wrote out_generated.png')
