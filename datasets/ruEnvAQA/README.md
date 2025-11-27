# ruEnvAQA


## Task description

ruEnvAQA is a dataset of multiple-choice and binary-choice questions in Russian. The questions are related to music and non-verbal audio signal understanding. The dataset is based on questions from English-language datasets [Clotho-AQA](https://arxiv.org/abs/2204.09634) and [MUSIC-AVQA](https://arxiv.org/abs/2203.14072v2). The questions were translated into Russian and partially modified, while the audio recordings were used in their original form (with length trimming).

The dataset includes 8 types of questions:

- Original question types from MUSIC-AVQA (approximately half of the questions test expert knowledge about rare instrument sounds, while the rest test general knowledge):
    - `Music instrument counting`: "How many musical instruments are playing in the recording?";
    - `Single music instrument detection`: "Is <instrument_X> playing in the recording?";
    - `Double music instrument detection`: "Is it true that both <instrument_X> and <instrument_Y> are playing in the recording?";
    - `Music instrument comparison (louder)`: "Is it true that <instrument_X> is playing louder than <instrument_Y> in the recording?";
    - `Music instrument comparison (longer)`: "Is it true that <instrument_X> is playing for a longer duration than <instrument_Y> in the recording?";

- Classes assigned during the editing of CLOTHO-AQA questions (general knowledge questions):
    - `Audio scene classification` is about understanding the audio scene as a whole, logical inference from multiple details (determining the location or circumstances where the audio was recorded);
    - `Audio captioning` questions are about understanding specific details of an audio fragment, the order and quantity of events;
    - `Sound QA with reasoning` questions test audio comprehension with simple reasoning, requiring not only perception of audio signal details but also a step of logical reasoning.

Evaluated skills: Scene understanding, Physical property understanding, Object function understanding, Temporal counting, Comparative reasoning, Object-object interaction, Object recognition, Object motion recognition, Common everyday knowledge, Common domain knowledge

Contributors: Ulyana Isaeva


## Motivation

The methodology for evaluating large audio language models (LALMs), as well as the models themselves, is a relatively new phenomenon. Compared to the vision-language domain, there are fewer large benchmarks that combine diverse tasks for the evaluation of LALM skills. Examples of such benchmarks include [AIR-Bench (02.2024)](https://arxiv.org/abs/2402.07729), [AudioBench (06.2024)](https://arxiv.org/abs/2406.16020), and [MMAU (10.2024)](https://arxiv.org/abs/2410.19168v1). Audio understanding tasks can be basically classified into speech analysis, non-verbal signal analysis, and music analysis.

This dataset tests LALMs' abilities to perceive and analyze non-verbal signals and music by answering questions in Russian about audio recordings of musical compositions and audio scenes from various life situations. The tests include questions of three types:
- **Questions on literal perception of audio events** (`Audio captioning` and music questions) test models' ability to match sequences of events captured in audio, their quantity and duration with their textual description. For example, "How many times did the ball bounce on the floor?" or "Is there a violin playing in the recording?".
- **Questions on audio scene classification** (`Audio scene classification`) test models' ability to conduct inductive reasoning, specifically to determine the location and circumstances of audio recording based on event details. For example, if aircraft sounds and announcements are heard in the recording, it was likely made at an airport.
- **Questions with additional reasoning** (`Sound QA with reasoning`) require additional logical operations with general world knowledge to derive the answer, beyond basic audio information perception. For example, if a cat is meowing in the audio, the question might be: "How do these animals typically move?".


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `question` [str] — Text of the question.
    - `audio` [str] — Path to the audio file related to the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `task_type` [str] — Task type according to the task classification in the dataset.
        - `source_dataset` [str] — A dataset that the audio and the question originate from.
        - `knowledge` [str] — The knowledge level required to answer the question.


### Data formatting example

```json
{
    "instruction": "Прослушайте аудиозапись.<audio> Прочитайте вопрос к аудио, оцените варианты ответа на вопрос и выберите один правильный. Дайте ответ буквой без дополнительных пояснений.\n\nВопрос: {question}\nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}\n\nОтвет:",
    "inputs": {
        "question": "В каком месте с наибольшей вероятностью сделана запись?",
        "audio": "samples/audio024.wav",
        "option_a": "в аэропорту",
        "option_b": "на причале",
        "option_c": "на железнодорожном вокзале",
        "option_d": "на автобусном вокзале"
    },
    "outputs": "C",
    "meta": {
        "id": 24,
        "categories": {
            "task_type": "Audio scene classification",
            "source_dataset": "CLOTHO-AQA",
            "knowledge": "common"
        }
    }
}
```


### Dataset creation

The dataset is compiled from audio files and questions in equal proportions from two English-language datasets, separately covering the domains of music and non-verbal signals. Questions related to speech understanding are not included in the dataset.


### Questions from Clotho-AQA Dataset

The [Clotho-AQA](https://arxiv.org/abs/2204.09634) dataset contains questions about audio with non-verbal signals and minor speech elements, with questions focusing only on non-verbal signals and occasionally on external characteristics of speech, such as volume or speaker gender.

Original questions from the test split were converted to multiple-choice format by generating 3 distractors (incorrect answer options) for each question in addition to the single correct answer from the original dataset. The distractors were generated in English using [Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct).

Questions, correct answers, and distractors were translated into Russian using [DeepL API](https://www.deepl.com/products/api). Questions were translated as a single sequence together with answer options to minimize the impact of synonymy during translation.

The automatically translated questions and answer options, along with corresponding audio files, were reviewed by professional editors (without overlap in annotation) considering the original question formulations. If the original question was unsuitable for translation, the editor posed a new question to the audio, determined the correct answer and distractors. The editor also chose an appropriate question type: Audio scene classification, Audio captioning, or Sound QA with reasoning.


### Questions from MUSIC-AVQA

The [MUSIC-AVQA](https://gewu-lab.github.io/MUSIC-AVQA/) dataset consists of video recordings of musical performances and three groups of questions:
- questions about the audio component of the video, not requiring visual component analysis;
- questions about the visual content, not requiring understanding of the accompanying audio;
- questions about audio-visual content, relating simultaneously to both audio and visual parts of the video.

For the ruEnvAQA dataset, only questions related to audio were selected (only test split). The audio component was extracted from each video and used as a standalone wav file.

The selected questions were constructed using templates filled with musical instrument names (22 different instruments):
- "How many musical instruments are playing in the recording?";
- "Is <instrument_X> playing in the recording?";
- "Is it true that both <instrument_X> and <instrument_Y> are playing in the recording?";
- "Is it true that <instrument_X> is playing louder than <instrument_Y> in the recording?";
- "Is it true that <instrument_X> is playing for a longer duration than <instrument_Y> in the recording?";

Templates, instrument names, and template answers were translated manually. Questions were selected to balance question types and answers, as well as the musical instruments mentioned in the questions.

The original dataset questions were converted to binary questions. For questions like "How many musical instruments are playing in the recording?", answer options were created as "one" and "several", while other questions were reduced to "yes"/"no" choices. Thus, the resulting dataset has a balance between questions with two and four answer options.


### Question Validation and Audio Processing

Pre-selected questions from both datasets underwent validation by crowdsource annotators with 3-fold overlap. Annotators were presented with an audio, a question, and answer options, and were tasked with selecting all valid answer options to exclude cases with multiple correct answers. Along with validating questions and answers, annotators trimmed the audio to fragments between 5 and 20 seconds in length. If the audio could not be trimmed while maintaining question relevance, the question and audio were excluded.

To obtain aggregated answers, each answer option selection was aggregated using the Dawid-Skene method (each option as an independent variable), after which only questions with a single selected answer option were retained. Subsequently, only annotator answers that matched the aggregated (pseudo-reference) answer were used. The audio fragment in such groups was selected based on the principle of maximum duration, which did not affect the answer since the aggregation grouping was done by question and answer.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, answers from annotators on a crowd-sourcing platform with an overlap of 5 were obtained. The aggregated answer was considered to be the one chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.95
