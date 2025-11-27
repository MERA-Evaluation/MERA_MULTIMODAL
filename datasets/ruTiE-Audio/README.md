# ruTiE-Audio


## Task description

ruTiE-Audio is an emulation of the Turing test in audio format. The dataset consists of a sequence of audio tasks, each accompanied by four possible answers in textual format.

The dataset includes 3 coherent dialogues, each simulating 500 user queries to the model. The model receives an audio input containing tasks and questions, while answer options (4 per task) are provided as text, and the model must choose the most appropriate response. Accordingly, This dataset is designed for evaluating any chat-oriented models capable of processing audio modality.

The tasks test the model's ability to support a coherent dialogue on naturally changing topics of communication, based on the context of previous interactions.

This dataset is based on the text dataset of the same name from the first release of the MERA benchmark. In addition to ruTiE-Audio, it is presented in two more versions: textual and visual (textual questions about images that are answered in text).

Acknowledgements for providing and processing voices (voiceover of the material): Ulyana Isaeva, Anna Lobanova, Andrey Bikin, Andrey Yevlampiev, Alexander Sautin, Anton Yemelyanov, Olga Vedenina, Maria Tikhonova

Evaluated skills: Speech recognition, Speaker diarization, Temporal object relationship, Human-human interaction, Human-object interaction, Object recognition, Common everyday knowledge, Common domain knowledge, Topic understanding, Scene understanding, Analogical reasoning, Temporal counting, Mathematical reasoning

Contributors: Denis Shevelev, Artem Chervyakov, Alena Fenogenova, Sergey Markov (the author of the idea)


## Motivation

This dataset targets models with a large context window (ideally capable of handling dialogue history up to 499 prior turns), but can also be used for models with a smaller context window (as few as 15 questions).  

The test has a complex task. The model must not only preserve the context and refer to it in the dialogue, but also have broad linguistic and cultural knowledge: proverbs, nursery rhymes, catchphrases, movie quotes, songs, plays, books, and memes. Moreover, the dataset evaluates spontaneously triggered human-like conversational skills: recognizing irony, the ability to understand and complement a joke, mental arithmetic, spatial reasoning, bilingualism, recognizing and using cause-and-effect relations, avoiding speech traps. Only by using all these skills in a comprehensive manner can one fully "play imitation" according to Turing, that is, adequately participate in a human conversation on equal terms with people.

Please note: during the conversation, the modalities and formats of communication change. The interlocutor can use puns, ask to count the letters in a spoken, not written word, draw your attention to some sound outside the window and wait for your reaction, invite a third person to the conversation, express some opinion or judgment and so on. Therefore, not all prompts are formatted as direct questions. Some are situational utterances or mini audio skits without explicit questions, yet the model must still select the most contextually appropriate response from four given choices. ruTiE-Audio offers 4 answer options for each question.

The test checks the model's ability
- to retain context
- to support (at the everyday level) a dialogue on any of the main topics (as defined in MERA domains)
- to recognize and categorize core task types, without which it is impossible to solve the problems of emulating the Turing test (including basic mathematics, ethics, linguistic games, common knowledge, etc.)
- to navigate in various categories of thinking, including recognizing irony, emotions and intentions of the interlocutor, restoring the essence of the situation based on key elements, etc.

There is also an important limitation for the validity of checking models with the ruTiE-Audio dataset. Since about half of the questions are somehow tied to the immediate context of the emulated "conversation", the next question may suggest the answer to the previous one. So you cannot give the model several tasks from the dialogue at once. Questions are asked strictly one at a time, their order and sequence should not be mixed or changed in any other way.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `audio` [str] — Path to the audio file related to the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `type` [str] — Thematic domain of the dataset.
    - `unified_category` [str] — Unified category by type of thinking.
    - `nonunified_category` [str] — Nonunified categorization by type of thinking audio/visual modality.
    - `turing_imitation` [str] — Turing test emulation category tested by the question.
    - `short_context` [int] — Indicator of the need for the last 1-2 questions to answer the current question.
    - `long_context` [int] — Indicator of the need for the last more than 1-2 questions to answer the current question.
    - `audio` — Audio metadata.
        - `type` [str] — Audio type — according to the audio classification for MERA datasets.


### Data formatting example

```json
{
    "instruction": "С вами ведут диалог посредством аудиофайлов/аудиосообщений. Освежите в памяти контекст предыдущей беседы: <context>. Внимательно прослушайте аудио, если оно есть: <audio>. Прочитайте варианты предлагаемых реакций на прослушанное вами аудио и (или) на контекст предыдущей части диалога, затем выберите наиболее правильный вариант ответной реакции, указав только буквы наиболее правильного варианта без дополнительных пояснений.\nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}\nОтвет:",
    "inputs": {
        "audio": "samples/audio0001.wav",
        "option_a": "Завалинка",
        "option_b": "Валидол",
        "option_c": "Валентина",
        "option_d": "Валентин"
    },
    "outputs": "D",
    "meta": {
        "id": 1,
        "type": "Вводная категория",
        "turing_imitation": "language’n’audio_structure",
        "unified_category": "trap",
        "nonunified_category": "Опознание ситуации",
        "short_context": 0,
        "long_context": 0,
        "audio": {
            "type": "real"
        }
    }
}
```


### Dataset creation

The dataset was manually collected by internal experts and then validated. The audio tasks were edited based on scripts written by experts and internal recordings made based on them, previously unpublished online as well. Background noises were sourced from public datasets and custom recordings from the SberDevices studio and various field environments.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, answers from annotators on a crowd-sourcing platform with an overlap of 5 were obtained. The aggregated answer was considered to be the one chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.45
