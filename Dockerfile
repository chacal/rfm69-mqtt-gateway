FROM balenalib/raspberrypi3-alpine-python:3-build as builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip3 install --install-option="--prefix=/install" -r /requirements.txt


FROM balenalib/raspberrypi3-alpine-python:3-run
COPY --from=builder /install /usr/local

RUN mkdir /app
COPY *.py /app/

CMD [ "python3", "-u", "/app/main.py" ]