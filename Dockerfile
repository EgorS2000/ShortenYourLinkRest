FROM python:3.8

COPY requirements.txt /code

RUN pip install -r requirements.txt

COPY . /code

WORKDIR /code

CMD ["python", "app.py"]
