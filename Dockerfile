
FROM python:3.7-alpine3.9
RUN apk update && apk add --update libffi-dev gcc musl-dev make openssl-dev bash
COPY requirements.txt /gitlab-cli-tool/requirements.txt
WORKDIR /gitlab-cli-tool
RUN pip3 install -r requirements.txt
COPY . /gitlab-cli-tool
CMD [ "python", "-m", "gitlab_cli_tool.run" ]

