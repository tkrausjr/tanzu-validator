FROM python:3

WORKDIR /usr/src/app
RUN mkdir -p /usr/src/cfg

COPY requirements.txt ./
COPY tz-validate.py /usr/src/app/tz-validate.py

RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install dnsutils -y

CMD [ "python", "./tz-validate.py" ]


