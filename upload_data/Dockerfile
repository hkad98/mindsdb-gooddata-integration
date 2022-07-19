ARG PY_TAG="3.9.9-slim-bullseye"
FROM python:${PY_TAG}

ENV USER_NAME=demo
ENV USER_GROUP=demo

RUN set -x \
 && groupadd ${USER_GROUP} \
 && useradd -m -g ${USER_GROUP} ${USER_NAME} \
 && true

USER ${USER_NAME}
WORKDIR /app
COPY ./upload_data/ /app

RUN set -x \
  && pip3 install --no-cache-dir --user -r requirements.txt \
  && true

LABEL image_name="MindsDB integration with GoodData.CN data image"

CMD ["python3"]
