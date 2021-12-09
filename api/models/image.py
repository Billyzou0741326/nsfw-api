from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Iterable
from tensorflow import keras
from PIL import Image, UnidentifiedImageError
from urllib.parse import urlparse
import io
import json
import httpx


IMG_DIM = 299


class ImageBase:

    @classmethod
    def _prepare_image_from_bytes(cls, img_bytes):
        img_bytes = io.BytesIO(img_bytes)
        img = Image.open(img_bytes, formats=('JPEG', 'PNG'))
        img = img.convert('RGB')
        img = img.resize((IMG_DIM, IMG_DIM), Image.NEAREST)
        img = keras.preprocessing.image.img_to_array(img)
        img /= 255
        return img

    @classmethod
    def prepare(cls, request):
        raise NotImplementedError


class ImageBinary(ImageBase):

    @classmethod
    def prepare(cls, request):
        # 1. Extract filename and fileinfo and Filter out files
        valid = []
        invalid = []
        for n, f in request.FILES.items():
            if f.size > 20 * 1024 * 1024:
                # add to invalid
                invalid.append((n, {'error': 'File too large (>20M)'}))
                continue
            try:
                img = cls._prepare_image_from_bytes(f.read())
                # add to valid
                valid.append((n, img))
            except UnidentifiedImageError:
                # add to invalid
                invalid.append((n, {'error': 'Image format not accepted'}))
                continue
        return tuple(valid), tuple(invalid)


class ImageUrl(ImageBase):

    @classmethod
    def _download_image(cls, url):
        u = urlparse(url)
        scheme = u.scheme if u.scheme == '' else 'http'
        headers = { 'Referer': f'{scheme}://{u.netloc}/' }
        response = httpx.get(url, timeout=10, headers=headers)
        if not response.is_success:
            return b''
        return response.content

    @classmethod
    def _download_images_parallel(cls, urls):
        results = []
        with ThreadPoolExecutor(max_workers=24) as executor:
            future_to_url = {executor.submit(cls._download_image, url): url for url in urls}
            for future in as_completed(future_to_url):
                data = future.result()
                url = future_to_url[future]
                results.append((url, data))
        return tuple(results)

    @classmethod
    def prepare(cls, request):
        valid = []
        invalid = []
        body = json.loads(request.body)
        if not isinstance(body, Iterable):
            return [[], []]
        images = cls._download_images_parallel(body)
        for u, img_bytes in images:
            if len(img_bytes) == 0:
                # add to invalid
                invalid.append((u, {'error': 'Image fetch error'}))
            try:
                img = cls._prepare_image_from_bytes(img_bytes)
                # add to valid
                valid.append((u, img))
            except UnidentifiedImageError:
                # add to invalid
                invalid.append((u, {'error': 'Image format not accepted'}))
                continue
        return tuple(valid), tuple(invalid)
