FROM python:3.7-alpine3.9
COPY . /gitlab-cli-tool
WORKDIR /gitlab-cli-tool
RUN apk update && apk add --update libffi-dev gcc musl-dev make openssl-dev bash
RUN pip3 install -r requirements.txt
CMD [ "python", "gitlab_cli_tool/run.py" ]

