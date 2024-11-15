

## Docker Commands

All commands are executed from the same directory as this readme.

### Dependencies 
This project depends on the `search-config` project. 

You can pull or build the dependencies using the guidance here.
### Build dependencies

```shell
git clone git@github.com:ResumeChat/search-config.git
cd search-config
docker build . --file images/dev/Dockerfile --tag ghcr.io/resumechat/search_config
```

### Pull dependencies
Ensure you have the latest official `gh` installed for the token command.

This only needs to be done locally, the build automatically manages authentication.

The commands below will log you in to github with access to read and write packages so you can pull the image from the girhub container repo.

Replace `$USER` with your github username if your current login does now match. 

```shell
gh auth login --scopes repo,packages:write,read:packages
gh auth token | docker login ghcr.io --username $USER --password-stdin
docker pull ghcr.io/resumechat/search_config:latest
```

### Build the dev image. 

Ensure you have the indeed optimizer container locally. You can build it using `docker compose build` from that project directory. 

Once the container is in your local repository you can run docker compose!

```shell
docker compose build 
```

### Run the dev image

Restart the container if you change the requirements. 

```shell
docker compose up --build --watch 
```

### Build the prod image. 

```shell
docker compose build -t report-processor-prod --no-cache
```


### Run the prod image

This image will need to be rebuilt if anything changes with the code or requirements.

This will monitor the volume for files in the main loop. 
Currently this only works to rebuild the image when one of the required files changes.

The container reloads must be done manually when something in the python code changes. 
This can be done with docker desktop, VC Code extension, or the docker cli.


```shell

docker compose up --build --watch
```
#### Running redis "locally" with docker

```shell
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 -e REDIS_ARGS="--requirepass mypassword" redis/redis-stack:latest
```

#### Running a shell with the same version of python as the container

```shell
docker run -it --rm -v ./src:/src python:3.12-bookworm bash
pip install redis pandas sentence-transformers tabulate && pip freeze

docker run -it --rm -v ./src:/src python:3.13-bookworm bash
```


#### Redis stuff

You can view [the redis console here](http://localhost:8002/redis-stack/browser)