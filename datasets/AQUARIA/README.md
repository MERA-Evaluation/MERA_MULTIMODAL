# AQUARIA


## Task description

The dataset includes multiple-choice questions that test complex audio comprehension, including speech, non-verbal sounds, and music. The tasks in the dataset require not only the recognition of speech but also the analysis of the entire auditory situation and the interactions among its components. The audio tracks used in AQUARIA were created specifically for this dataset.

The dataset contains 9 types of tasks:
- Audio scene classification
- Audio captioning (matching audio with its textual description)
- Audio comparison (finding differences between two audio)
- Audio sequence analysis
- Emotion recognition (recognition of emotions and subjective characteristics of a speaker)
- Sound QA (questions related to analysis of non-verbal signals)
- Speaker characterization (recognition of objective characteristics of a speaker)
- Music QA (questions requiring analysis of music and related knowledge)
- Music characterization (recognition of objective characteristics of music)

Evaluated skills: Speaker diarization, Temporal object relationship, Object-object interaction, Human-object interaction, Human-human interaction, Object recognition, Object motion recognition, Living things motion recognition, Speech recognition, Common everyday knowledge, Common domain knowledge, Speech emotion recognition, Music emotion recognition, Style & genre understanding, Scene understanding, Physical property understanding, Identity & emotion understanding, Cause & effect understanding, Temporal counting, Comparative reasoning

Contributors: Ulyana Isaeva


## Motivation

The methodology for evaluating large audio-language models (LALMs), as well as the models themselves, is a fairly recent area of research. Compared to benchmarks in the vision-language domain, there are significantly fewer comprehensive benchmarks available for evaluating audio-language models. Examples of such benchmarks include [AIR-Bench (02.2024)](https://arxiv.org/abs/2402.07729), [AudioBench (06.2024)](https://arxiv.org/abs/2406.16020), and [MMAU (10.2024)](https://arxiv.org/abs/2410.19168v1). Audio understanding tasks are generally classified into three categories: speech analysis, non-verbal signal analysis, and music analysis.

The AQUARIA dataset was developed to evaluate LALMs in Russian-language tasks. The model needs to be able to process audio because answering questions requires analyzing the associated audio track. The dataset contains 9 question types, which vary both by task category and by the model abilities they test. The dataset assesses three skill categories for audio-language models: perception, knowledge, and reasoning.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `audio_1` [str] — Path to the audio file related to the question.
    - `audio_2` [str] — Path to the second audio file related to the question (if the question is related to two audio files, else field is not used).
    - `question` [str] — Text of the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `task_type` [str] — Task type (see section Task description).


### Data formatting example

```json
{
    "instruction": "Задание содержит две аудиозаписи и вопрос к ним с четырьмя вариантами ответа: A, B, C, D. Из них только один правильный. Прослушайте аудио: <audio_1>, <audio_2>. Прочитайте вопрос к аудиозаписям и напишите букву правильного ответа: {question}\nA) {option_a}\nB) {option_b}\nC) {option_c}\nD) {option_d}\n\nОтвет:",
    "inputs": {
        "question": "В чём различие двух предложенных аудиозаписей?",
        "audio_1": "samples/audio194.wav",
        "audio_2": "samples/audio195.wav",
        "option_a": "На первой записи отпирают дверь, на второй она была отперта",
        "option_b": "На первой записи дверь скрипит, на второй нет",
        "option_c": "На первой записи в квартиру входит женщина, на второй — мужчина",
        "option_d": "На первой записи человек заходит в открытую дверь, а на второй отпирает замок"
    },
    "outputs": "B",
    "meta": {
        "id": 173,
        "categories": {
            "task_type": "Audio comparison"
        }
    }
}
```


### Dataset creation

Based on an analysis of existing benchmarks for testing language models with audio interfaces, we have developed 9 types of tasks that evaluate various groups of skills for these models. For each task type, experts created scenarios with dialogues, background sounds, and music, along with corresponding questions tailored to different task formulations. All scenarios were recorded using professional studio recording equipment, with voluntary use of dataset contributors' voices. For some of the Music QA and Music characterization questions, the music tracks were created using generative models (including suno.com).


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, answers from annotators on a crowd-sourcing platform with an overlap of 5 were obtained. The aggregated answer was considered to be the one chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.98
