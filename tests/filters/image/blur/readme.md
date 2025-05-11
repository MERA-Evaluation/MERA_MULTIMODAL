### Filter Blur:
Filter name: blur

Dockerfile: Dockerfile.filter_blur

Docker image dev: swr.ru-moscow-1.hc.sbercloud.ru/sber_devices/rnd_de/depp/filter_blur:dev

Docker image prod: swr.ru-moscow-1.hc.sbercloud.ru/sber_devices/rnd_de/depp/filter_blur:latest


### Способы запуска:

### Локальный запуск через CMD без Docker контейнера
```
python run.py filters/image/blur/run.py --bucket=<bucket name> --endpoint_url=<endpoint_url> --access_key=<s3 access key> --secret_key=<s3 secret key> --prefix=<s3 prefix> --num_jobs=<amount of processes for parallel processing> --count_download_file=<size of batch to download content from s3> --result_file_name=<name of result .csv file> --format=<filter modality: image, video> --is_use_k8s_mount=<is PFS available flag, 0 - if False, 1 - if True> --redis_key_chunk_files=<Optional: uuid of key in Redis that stores paths to samples and other data> --host_redis=<Optional: localhost> --port=<Optional: Redis port> --password=<Optional: Redis password>  
```

### Локальный запуск в Docker контейнере

```
Сборка Docker: docker build . -t swr.ru-moscow-1.hc.sbercloud.ru/sber_devices/rnd_de/depp/filter_blur:dev -f Docker.filter_blur
```

```
Запуск в Docker: docker run -it --rm swr.ru-moscow-1.hc.sbercloud.ru/sber_devices/rnd_de/depp/filter_blur:dev python run.py --bucket=<bucket name> --endpoint_url=<endpoint_url> --access_key=<s3 access key> --secret_key=<s3 secret key> --prefix=<s3 prefix> --num_jobs=<amount of processes for parallel processing> --count_download_file=<size of batch to download content from s3> --result_file_name=<name of result .csv file> --format=<filter modality: image, video> --is_use_k8s_mount=<is PFS available flag, 0 - if False, 1 - if True> --redis_key_chunk_files=<Optional: uuid of key in Redis that stores paths to samples and other data> --host_redis=<Optional: localhost> --port=<Optional: Redis port> --password=<Optional: Redis password>  
```


### Config to run filter in Airflow
```json
{
    "vault_secret": "rnd_de",
    "s3_arguments": [
        "--bucket=rndml-team-mera",
        "--prefix=secret-datasets/public/WEIRD",
        "--format=image"
    ],
    "filter_params": {
        "blur": [
            "--num_jobs=1",
            "--count_download_file=100"
        ]
    },
    "type_get_keys": [
        "--s3_type_pagination=s3_with_redis_key"
    ],
    "count_parallel_tasks": 3
}
```


### Airflow Dev
Validation rules: https://airflow.dev.de.mlrnd.ru/variable/show/4

DAG: https://airflow.dev.de.mlrnd.ru/dags/depp_pipeline__dev__depp/grid

### Airflow Prod
Validation rules: https://airflow.de.mlrnd.ru/variable/show/4

DAG: https://airflow.de.mlrnd.ru/dags/depp_pipeline__depp/grid
