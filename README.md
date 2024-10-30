

## Docker Commands

All commands are executed from the same directory as this readme.

### Build the dev image. 

Ensure you have the indeed optimizer container locally. You can build it using `docker compose build` from that project directory. 

Once the container is in your local repository you can run docker compose!

```shell
docker compose -f dev-compose.yaml build 
```

### Run the dev image

Restart the container if you change the requirements. 

```shell
docker compose -f dev-compose.yaml up --build --watch 
```

### Build the prod image. 

```shell
docker compose build -t report-processor-prod --no-cache -f dev-compose.yaml
```


### Run the prod image

This image will need to be rebuilt if anything changes with the code or requirements.

This will monitor the volume for files in the main loop. 
Currently this only works to rebuild the image when one of the required files changes.

The container reloads must be done manually when something in the python code changes. 
This can be done with docker desktop, VC Code extension, or the docker cli.


```shell

docker compose -f dev-compose.yaml up --build --watch
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