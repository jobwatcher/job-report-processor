

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

docker compose -f dev-compose.yaml up



docker run -i -t --rm \
    -v "${HOME}/Development/report-processor/src:/report-processor/src" \
    -v "${HOME}/Development/indeedOptimizer/scrapped_data:/report-processor/scrapped_data" \
     report-processor
```

### Build the prod image. 

```shell
docker build -t report-processor-prod --no-cache -f images/prod/Dockerfile .
```


### Run the prod image

This image will need to be rebuilt if anything changes with the code or requirements.

This will monitor the volume for files in the main loop. 

```shell
docker run -i -t --rm \
    -v "${HOME}/Development/indeedOptimizer/scrapped_data:/report-processor/scrapped_data" \
     report-processor-prod
```
#### Running redis "locally" with docker

```shell
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 -e REDIS_ARGS="--requirepass mypassword" redis/redis-stack:latest
```