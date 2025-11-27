# RuSLUn


## Task description

RuSLUn (Russian Spoken Language UNderstanding dataset) is a Russian-language dataset for spoken language understanding, designed following the principles of the English [SLURP](https://arxiv.org/pdf/2011.13205) and the multilingual [xSID](https://aclanthology.org/2021.naacl-main.197.pdf), but with consideration for the cultural and linguistic specifics of Russia. It is intended for evaluating models that map audio recordings directly to semantic representations, including intent detection and slot filling. RuSLUn contains a variety of spoken commands and queries that are typical for Russian users and contexts. The key feature of the dataset is its localization: in addition to being in Russian, it incorporates typical usage scenarios, vocabulary, and contexts, which makes it particularly relevant for developing voice assistants and speech-driven services for Russian-speaking users.

Evaluated skills: Speech recognition, Problem decomposition, Common everyday knowledge

Contributors: Zaryana Damashova, Ekaterina Artemova, Ilseyar Alimova


## Motivation

Traditionally, the task of spoken language understanding (SLU) is solved in several stages: first, audio recordings are converted into text using automatic speech recognition (ASR), and then the necessary information is extracted from the text using natural language understanding (NLU) technologies. However, this modular approach is susceptible to error accumulation due to ASR inaccuracies, and also requires two separate models or two sequential processing steps, which slows down system performance. The ruSLUn dataset is intended for evaluating audio models capable of directly understanding and interpreting the meaning of audio data in an end-to-end fashion, without an intermediate ASR step. Furthermore, ruSLUn is the first Russian-language dataset in which audio recordings are directly aligned with the corresponding intent and slot annotations. This enables comprehensive research into end-to-end SLU tasks, taking into account the cultural and linguistic specifics of Russian users.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `audio` [str] — Path to the audio file related to the question.
    - `question` [str] — Text of the question.
    - `annotation` [str] — A list of available intents and slots.
- `outputs` — The correct answer to the question.
    - `intent` [str] — User intent;
    - `slots` [list] — A list of slots in json format, where the key is the slot type and the value is the allocated slot value.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `audio` — Audio metadata.
        - `type` [str] — Audio type — according to the audio classification for MERA datasets.
    - `speaker` [str] — id_gender_age


### Data formatting example

```json
{
    "instruction": "В датасете к задаче идёт такой промпт:\n\nНе обязательно все слоты присутствуют в запросе.\nАудиофайл: <audio>\nВопрос:\n{question}\n\nПрошу решить задачу на основе вышеизложенного и кратко сформулировать ответ.\n\n{annotation}",
    "inputs": {
        "audio": "samples/audio_2.wav",
        "question": "Внимательно послушай <audio> с запросом пользователя, классифицируй к какому намерению (intent) относится запрос пользователя и выдели соответствующие данному намерению все возможные слоты (slots). Слова в слотах должны быть в той же морфологической форме, что и в аудио, цифры должны быть записаны текстом.",
        "annotation": "Список доступных намерений с соответствующими слотами в формате намерение: [список слотов].\nBookRestaurant: [cuisine, datetime, facility, location, party_size_description, party_size_number, restaurant_name, restaurant_type, served_dish, sort]\nSearchScreeningEvent: [datetime, location, movie_name, movie_type, object_location_type, object_type]\nSearchCreativeWork: [object_name, object_type]\nAddToPlaylist: [artist, entity_name, music_item, playlist, reference]\nRateBook: [best_rating, object_name, object_part_of_series_type, object_select, object_type, rating_unit, rating_value]\nPlayMusic: [album, artist, datetime, genre, music_item, playlist, service, sort, track]\nweather/find: [condition_description, condition_temperature, datetime, location, weather/attribute]\nalarm/cancel_alarm: [datetime, reference]\nreminder/set_reminder: [datetime, recurring_datetime, reminder/todo]\nreminder/cancel_reminder: [datetime, reference, reminder/todo]\nreminder/show_reminders: [datetime, reference, reminder/todo]\nalarm/set_alarm: [datetime, recurring_datetime, reference, reminder/todo]\nalarm/show_alarms: [datetime, reference]\nalarm/modify_alarm: [datetime]\nalarm/snooze_alarm: [reference]\nalarm/time_left_on_alarm: []\n\nОтвет должен быть в формате валидного json, по схеме: {\"intent\": \"выбранный из списка intent\", \"slots\": [{\"тип слота\": \"значение слота\"}, {\"тип слота\": \"значение слота\"}, {\"тип слота\": \"значение слота\"}]}. Выведи только валидный JSON без форматирования, комментариев и обратных кавычек."
    },
    "outputs": {
        "intent": "RateBook",
        "slots": [
            {
                "object_name": "доктор живаго"
            },
            {
                "rating_value": "три"
            },
            {
                "best_rating": "шести"
            },
            {
                "rating_unit": "звезд"
            }
        ]
    },
    "meta": {
        "id": 2,
        "audio": {
            "type": "real"
        },
        "speaker": "7_female_33"
    }
}
```


### Dataset creation

The dataset was created in two stages: first, text queries were generated and annotated with intents and slots, then, these queries were recorded as audio.
The annotation scheme was based on the cross-lingual [xSID](https://aclanthology.org/2021.naacl-main.197.pdf) dataset, which includes 16 intent types and 33 slot types. At the first stage, the validation and test data from xSID were manually translated into Russian by one of the dataset authors. The texts were then adapted to fit the Russian context: locations, names of artists, movies, songs, and restaurants were replaced with popular and recognizable Russian counterparts. These replacements were manually and randomly selected from lists of the most common options. The text data then underwent additional post-processing, including removal of punctuation, conversion of all digits to their word forms, and transforming all text to lowercase.
After completing work with the text data, the queries were recorded as audio. Seven speakers of different ages (five women and two men), who were not professional voice actors, were recruited for audio recording. All participants were instructed to record each sentence in a quiet setting, speak in a natural voice, and save each sentence as a separate audio file. Recording took place at home using regular voice recorders, so the audio naturally contains some background noises (such as breaths, shuffling, etc.).
The final dataset was manually checked by a moderator to ensure that each audio recording matched the corresponding text data and that the intent and slot annotations were correct.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Intent Exact Match`: The Intent Exact Match metric computes the average of scores over all examples: score = 1 if the predicted intent exactly matches the ground-truth intent, and 0 otherwise.
- `Slots F1`: Macro-averaged F1 across all examples for slots. For each example, precision is the proportion of predicted slots that are correct, and recall is the proportion of true slots that were predicted. A slot is considered correct if both its type and value match; the F1 for an example is computed from its precision and recall.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Intent Exact Match – 0.91
- Slots F1 – 0.30
