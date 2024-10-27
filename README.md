

## Docker Commands

All commands are executed from the same directory as this readme.

### Build the dev image. 

```shell
docker build -t report-processor-dev --no-cache -f images/dev/Dockerfile .
```

### Run the dev image

Restart the container if you change the requirements. 

```shell
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
