FROM continuumio/miniconda3:4.10.3 AS runtime
RUN conda config --add channels conda-forge && \
    conda install -y tensorflow=2.5.0 tensorflow-hub httpx Pillow Django djangorestframework gunicorn

FROM runtime
copy . /app/
WORKDIR /app/
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--threads", "8", "main.wsgi"]
