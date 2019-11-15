
# Gitlab CLI tool
Using the Gitlab UI for our daily tasks is a bit of a pain as it does not keep filters, and does not support batch actions.
Easy-to-use CLI that we can use in our terminal.

## Contents

1. [Initial Setup Instructions](#initial-setup-instructions)
1. [Running Gitlab CLI](#running-gitlab-cli)
1. [Usage](#usage)

## Initial Setup Instructions

### Credentials to Gitlab
You should store credentials in `~/.gitlab-cli/secrets.txt` <br/>
You need to supply secrets.txt with correct credentials.
Example of credentials
```bash
SERVER=https://gitlab.companyname.com
TOKEN=kHsHaskj_213asd
TRIGGER_TOKEN=asdkj21290381029asdasd
PROJECT_ID=234
```

## Running Gitlab CLI

### 1. Using docker

#### 1.1 Pull docker image <br/> 
You can find image here `https://hub.docker.com/r/gastrofixgmbh/gitlabcli` <br/>
Docker pull command: `docker pull gastrofixgmbh/gitlabcli`
#### 1.2 Run docker container and map your local secrets.txt <br/> 
```docker run -it --rm --volume=$HOME/.gitlab-cli:/root/.gitlab-cli gastrofixgmbh/gitlabcli```

### 2. Running locally
#### 2.1 Setup Python Virtual Environment
```buildoutcfg
python3 -m venv venv
. venv/bin/activate
pip3 install .
```
#### 2.2 Run script
```python gitlab_cli_tool/run.py```


## Usage
#### Listing all runners
You can list all runners or filter them with --name or --tag <br/>
`runners list`
```
NAME      TAGS             PROJECT           ACTIVE JOBS  STATUS
--------  ---------------  --------------  -------------  --------
qa-01.02  ios13, qa-01.02  dummy-project         4          online
qa-01.03  ios13, qa-01.03  dummy-project         4          online
qa-01.04  atf, qa-01.04    dummy-project         0          online
qa-02.01  atf, qa-02.01    dummy-project         0          paused
...
```
#### Listing all runners filtered by names
You can add multiple names. It works like OR. The name filter works like `icontains` so eg `qa-03`
will look for qa-03.01 , qa-03.02 etc. <br/>
`runners list --name qa-03 qa-04` 
```
NAME      TAGS           PROJECT           ACTIVE JOBS  STATUS
--------  -------------  --------------  -------------  --------
qa-03.01  atf, qa-03.01  dummy-project         0           online
qa-03.02  atf, qa-03.02  dummy-project         0           online
qa-04.01  atf, qa-04.01  dummy-project         0           online
qa-04.03  atf, qa-04.03  dummy-project         0           online
...
```
#### Listing all runners filtered by tags
You can add multiple tags. It works like OR.  <br/>
`runners list --tag atf linux` 
```
NAME                 TAGS                             PROJECT             ACTIVE JOBS  STATUS
-------------------  -------------------------------  ----------------  -------------  -------------
qa-01.04             atf, qa-01.04                    dummy-project           2         online
qa-02.01             atf, qa-02.01                    dummy-project           0         paused
ci-k8s-linux-0       build, linux, k8s                dummy-project           0         not_connected
ci-k8s-linux-0       build, linux, k8s                dummy-project           0         not_connected
...
```

#### Pause runners
Pausing works the same as listing when it comes to filtering by names and tags. You have to filter by names or tags. <br/>
 `runners pause` will not work. <br/>
`runners pause --name qa-01 ` will pause runners 
```
Runner id: 262 is paused
Runner id: 263 is paused
Runner id: 264 is paused
NAME      TAGS             PROJECT            ACTIVE JOBS  STATUS
--------  ---------------  ---------------  -------------  --------
qa-01.02  ios13, qa-01.02  dummy-project          4         paused
qa-01.03  ios13, qa-01.03  dummy-project          4         paused
qa-01.04  atf, qa-01.04    dummy-project          4         paused
```
#### Resume runners
Resuming works the same as listing when it comes to filtering by names and tags. You have to filter by names or tags. <br/>
 `runners resume` will not work. <br/>
`runners resume --name qa-01 ` will resume runners
```
Runner id: 262 is resumed
Runner id: 263 is resumed
Runner id: 264 is resumed
NAME      TAGS             PROJECT             ACTIVE JOBS  STATUS
--------  ---------------  ----------------  -------------  --------
qa-01.02  ios13, qa-01.02  dummy-project           4        online
qa-01.03  ios13, qa-01.03  dummy-project           4        online
qa-01.04  atf, qa-01.04    dummy-project           4        online
```

#### Trigger a pipeline by branch name
Trigger a pipeline command <br/>
`pipeline run --branch master` 
```
Pipeline for branch master has been triggered
https://gitlab.acme.com/smth/dummy-project/pipelines/XXXX
```
It is possible to trigger a pipeline with variables with format `name=value` <br/>
`pipeline run --branch master --variables VAR1=true VAR2=3.12` 
```
Pipeline for branch master has been triggered
https://gitlab.acme.com/smth/dummy-project/pipelines/XXXX
```
#### Running tests
Use pytest inside docker container to run all or some tests, examples:

``` bash
# runs all tests
pytest tests
```
