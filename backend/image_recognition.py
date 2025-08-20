import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import os
from PIL import Image
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0 = all logs, 1 = info, 2 = warnings, 3 = errors only

# Load MobileNet model from TF Hub
model = hub.load("https://tfhub.dev/google/tf2-preview/mobilenet_v2/classification/4")

# Download ImageNet labels
labels_path = tf.keras.utils.get_file(
    'ImageNetLabels.txt',
    'https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt'
)
imagenet_labels = np.array(open(labels_path).read().splitlines())

def preprocess_image(image_path):
    img = Image.open(image_path).resize((224, 224))
    img = np.array(img) / 255.0
    img = img[np.newaxis, ...]
    return tf.convert_to_tensor(img, dtype=tf.float32)

def recognize_image(image_path):
    img = preprocess_image(image_path)
    preds = model(img)
    predicted_class = np.argmax(preds[0], axis=-1)
    return imagenet_labels[predicted_class]
