import tensorflow as tf
import numpy as np
from PIL import Image
import json
import os

model = tf.keras.models.load_model("app/ml/tomato_disease_model.h5")
with open("app/ml/class_names.json") as f:
    class_names = json.load(f)

# Point this at a folder with a few known test images from your dataset
# (any of the Test/<Disease>/ folders you extracted earlier)
test_folder = input("Paste path to a folder of test images: ").strip()

for filename in os.listdir(test_folder)[:10]:
    path = os.path.join(test_folder, filename)
    try:
        img = Image.open(path).convert("RGB").resize((224, 224))
    except Exception:
        continue
    arr = np.expand_dims(np.array(img), axis=0)
    preds = model.predict(arr, verbose=0)[0]
    top_idx = int(np.argmax(preds))
    print(f"{filename}: {class_names[top_idx]} ({preds[top_idx]:.2%})")