from threading import Lock, Thread, Semaphore
from PIL import Image
from tensorflow import keras
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import time
import os
import io
from .image import IMG_DIM


MODEL_PATH = os.getenv('MODEL_PATH', default='mobilenet_v2_140_224')


def load_model():
    if MODEL_PATH is None or not os.path.exists(MODEL_PATH):
        raise ValueError("environment variable MODEL_PATH must be the valid directory of a saved model to load.")
    model = tf.keras.models.load_model(MODEL_PATH, custom_objects={'KerasLayer': hub.KerasLayer}, compile=False)
    return model


class NSFWModel:

    class inner:
        model_lock = Lock()
        wait_sem = Semaphore(value=1)
        model = None
        loading = False

    @staticmethod
    def is_ready():
        with NSFWModel.inner.model_lock:
            return NSFWModel.inner.model is not None

    @staticmethod
    def _load_model():
        should_load = False
        # Semaphore: wait lock
        # Lock: sync lock
        with NSFWModel.inner.model_lock:
            if NSFWModel.inner.model == None and not NSFWModel.inner.loading:
                should_load = NSFWModel.inner.loading = True
        if should_load:
            with NSFWModel.inner.wait_sem:
                model = load_model()
                with NSFWModel.inner.model_lock:
                    NSFWModel.inner.loading = False
                    NSFWModel.inner.model = model
                    return model
        with NSFWModel.inner.model_lock:
            return NSFWModel.inner.model

    @staticmethod
    def prepare_image_from_file(img_path):
        img = keras.preprocessing.image.load_img(img_path, (IMG_DIM, IMG_DIM))
        img = keras.preprocessing.image.img_to_array(img)
        return img

    @staticmethod
    def predict(img_list: list):
        categories = ['drawings', 'hentai', 'neutral', 'porn', 'sexy']
        m = NSFWModel._load_model()
        img_list = np.asarray(img_list)
        predictions = m.predict(img_list)
        results = []
        for i, prediction in enumerate(predictions):
            single_probs = {}
            for j, pred in enumerate(prediction):
                single_probs[categories[j]] = float(pred)
            results.append(single_probs)
        return results
