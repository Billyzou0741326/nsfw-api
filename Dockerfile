FROM continuumio/miniconda3:4.10.3 AS runtime
RUN conda config --add channels conda-forge && \
    conda install -y tensorflow=2.5.0 tensorflow-hub httpx Pillow Django djangorestframework django-cors-headers gunicorn

FROM runtime
copy . /app/
WORKDIR /app/
ENV MODEL_PATH=/app/nsfw.299x299.h5
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--threads", "24", "main.wsgi"]
