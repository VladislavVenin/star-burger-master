FROM python:3.13
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/star-burger
COPY . .
RUN apt update \
    && pip3 install -r requirements.txt \
    && pip3 install gunicorn \
    && apt remove -y python3-pip  \
    && apt autoremove --purge -y  \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list
CMD [ "python", "manage.py", "collectstatic", "--noinput" ]
EXPOSE 8000