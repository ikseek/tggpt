FROM python:3.11
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -e .

CMD [ "python", "-m", "tggpt" ]