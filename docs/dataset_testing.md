# Авто-тесты

После сбора датасета в нужном для MERA формате, необходимо прогнать пайплайн **авто-тестирования**. Данный пайплайн предоставляет следующий функционал/инструменты:

- Проверка целостности семплов
- Вычисление размеров семплов (высота, ширина)
- Проверка наличия вотермарок в семплах
- Проверка наличия NSFW контента в семплах
- Вычисленеие 'заблюренности' семплов
- Проверка на наличие дубликатов в семплах

**ВАЖНО** 
1) Некоторые процессоры основаны на моделях машинного обучения, поэтому **требуют дополнительной ручной проверки** в случае неуспеха в авто-тестировании. 
2) Инструмент авто-тестирования предназначен только для предварительной проверки датасета перед его дальнейшей обработкой командой MERA и не гарантирует отсутствие ошибок в Вашем датасете после прогона.
2) Для работы пайплайна нужен `python` версии `3.10`.
3) Ниже описаны примеры установки окружения, необходимого для запуска.

## Quickstart

В случае, если Вам необходимо прогнать авто-тесты для сета **изображений**, процесс выглядит так:
```bash
cd {mera_multi_external}/tests/local_run
python3.10 -m venv ./.tests_env
source ./.tests_env/bin/activate
pip3.10 install --upgrade pip
pip3.10 install -r ./base_requirements.txt
python3.10 ./cli_run.py -p {DATASET_PATH}
```
После запуска команды прогонятся прописанные в конфигурации проверки для семплов, в результате чего появятся:
- файл `checkouts_result.csv` с таблицей, указывающей, сколько файлов не прошли проверку и по какому именно критерию
- папка `checkout_data` со списком всех **непрошедших проверку** семплов. Их необходимо отсмотреть **вручную** и убедиться, что с файлами все в порядке / что-то не так
- файл `results.csv` с сырыми результатам проверок.

## Кастомный запуск
Кастомный запуск нужен, например, если вы хотите самостоятельно выбрать набор проверок, или проверить датасет в облкае, не скачивая его локально. 

### Настройка окружения
1) Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2) Настройте `config.yml`

## Настройки `config.yml`

1) Расположите файл `config.yml` по пути `./mera_multi_external/tests/local_run/config.yml`
2) Наполните файл `config.yml` в соответствии с Вашей задачей


### Разбор наполнения конфига
```yaml
storage_params:  # Тут находится информация о местонахождении датсета. Опционально можно проверять данные в s3, указав соответствующие парметры
  # ______ CLOUD S3 PARAMS ______
  # endpoint_url: "{YOUR_S3_CLOUD_ENDPOINT}"
  # access_key: "{ACCESS_KEY_ID}"
  # secret_key: "{SECRET_ACCCESS_KEY}"
  # bucket: "{BUCKET_NAME}"
  # prefix: {PATH_TO_DATASET_FOLDER}
  # result_file_name: {FILE_NAME (без пути, файл загрузится нарпямую в облако в папку с датасетом)}
  # path_csv_key: "{PATH_TO_INPUT_CSV}"  # Можно передавать конкретные семплы посредством передачи .csv файла с полем path, в котором указанны полные ссылки до семплов
  
  # ______ LOCAL PARAMS ______
  prefix: "/Users/example/Desktop/NEW_DATASET/"
  result_file_name: "/Users/example/Desktop/NEW_DATASET/results.csv" 
  path_csv_key: "/Users/example/Desktop/NEW_DATASET/local_run.csv"

map_params:  # В этой вкладке указывается список фильтров. Ниже приведены примеры для разных модальностей. Можно указывать несколько фильтров подряд
  - map_type: "filter"  # тип запускаемого модуля (здесь и далее будут только filters)
    map_name: "blur"  # название запускаемого модуля
    map_modality: "image"  # Название модальности (image, video, audio)
    num_jobs: 1  # Мультитрединг на указанном кол-ве ядер
    count_download_file: 100 # batch_size / параметр, регулирующий, сколько файлов можно скачать из s3 во временную папку
    format: "image" # Тип данных, с которыми будет работать модуль (.zip, .tar, image, video)

#  - map_type: "filter"  # Можно указывать несколько модулей подряд, порядок выполнения сохраняется. Stateful состояние реализовано по батчам.
#    map_name: "meta_extractor"
#    map_modality: "image"
#    num_jobs: 1
#    count_download_file: 100
#    format: "image"

type_get_keys:
  type_pagination: "local_docker"  # "{A}_{B}_{C}"
                                # A <-> [`local`, `s3`]
                                # B <-> [`docker`, None] (Если не указывать параметр `docker`, то необходимо перед запуском собрать окружение для
                                # C <-> [`csv`, `prefix`] (`path_csv_key` в storage_params должен быть указан, если указан `csv`)
                                # конкретного фильтра и активировать его перед запуском скрипта main.py)

                                # Еще примеры:
                                # Если нужно запустить авто-тесты для данных в s3, используя докер, 
                                #     то type_pagination = "s3_docker_prefix" + указанные параметры CLOUD S3 PARAMS
                                # Если нужно запустить авто-тесты для локальных данных, не используя докер и передавая пути до файлов через csv,
                                #     то type_pagination = "local_csv" + указанные параметры LOCAL PARAMS + передан путь `path_csv_key`
                                # Если нужно запустить авто-тесты для локальных данных, через докер и передавая пути до файлов через csv
                                #     то type_pagination = "local_docker_csv" + указанные параметры LOCAL PARAMS + передан путь `path_csv_key`

checkout_params:  # завершающая стадия, результаты работы модулей аггрегируются и раскладываются в необходимую статистику 
  project: mera  # название проекта чекаутов, которые лежат в папке /tests/filters/checkouts/
  checkouts:  # доступные чекауты: 
              # blur -- отсечка по скору заблюренности
              # phash -- поиск дубликатов
              # nsfw -- категоризация nsfw контента
              # watermark -- наличие вотермарки
              # image_resolution -- минимальная сторона == 224, максимальная == 3840
              # corrupted_image -- проверка на битые файлы
              # acl_security (только для s3) -- проверка, что ACL всех данных приватный
              # image_format -- проверка на соответствие формата и модальности (для изображний доступные экстеншны - jpeg, jpg, png)
    - blur  # можно указывать несколько чекаутов, главное, чтобы соответствующий модуль был подключен в `map_params`
#    - phash
#    - image_resolution
#    - corrupted_image
  checkout_result_file: "checkouts_result.csv"  # название файла с результатами чекаутов
  failed_samples_folder: "/Users/example/Desktop/NEW_DATASET/checkout_data" # папка для сохранения "непрошедших" по чекаутам семплов
```

### Пример 1. Запуск кастомных проверок для ИЗОБРАЖЕНИЙ
```yaml
storage_params: 
  prefix: "/Users/example/Desktop/NEW_DATASET/"
  result_file_name: "/Users/example/Desktop/NEW_DATASET/results.csv" 

map_params: 
  - map_type: "filter"  
    map_name: "blur" 
    map_modality: "image"  
    num_jobs: 1 
    count_download_file: 1000
    format: "image" 
  - map_type: "filter"
    map_name: "meta_extractor"
    map_modality: "image"
    num_jobs: 1
    count_download_file: 1000
    format: "image"
  - map_type: "filter"
    map_name: "nsfw"
    map_modality: "image"
    num_jobs: 1
    count_download_file: 100
    format: "image"
  - map_type: "filter"
    map_name: "watermark"
    map_modality: "image"
    num_jobs: 1
    count_download_file: 100
    format: "image"

type_get_keys:
  type_pagination: "local_docker_prefix"  
checkout_params:
  project: mera  
  checkouts:
    - blur  
    - phash
    - image_resolution
    - image_format
    - corrupted_image
    - nsfw
    - watermark

  checkout_result_file: "checkouts_result.csv"
  failed_samples_folder: "/Users/example/Desktop/NEW_DATASET/checkout_data"
```


[//]: # (### Пример 2. Запуск проверок для ВИДЕО)

[//]: # (```yaml)

[//]: # (Добавятся позже)

[//]: # (```)


## Запуск
Кастомный запуск проверок выполняется так:
```bash
cd {mera_multi_external_path}/tests/local_run/
conda create --prefix ./.local_env python=3.10
conda activate ./.local_env
pip install --upgrade pip
pip install pyyaml==6.0.2 docker==7.1.0 boto3==1.35.16 pandas==2.2.2
python ./main.py
```