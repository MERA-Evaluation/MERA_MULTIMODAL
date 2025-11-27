# ruTiE-Image


## Task description

ruTiE-Image is a multimodal emulation of the Turing test, which is an unchangeable sequence of question-answer tasks with the ability to choose an answer. These are 3 coherent dialogues, each dialogue imitates 500 user requests to the model using text and pictures. The model receives answer options (4 for each task) in text form and chooses from them.

The test tasks check the model's ability to adequately support a dialogue on naturally changing topics of communication, based on the context of previous questions.

The dataset is based on the text dataset of the same name from the first release of the MERA benchmark. In addition to ruTiE-Image, a similar dataset is presented in 2 more versions: monomodal ruTiE-Txt and multimodal ruTie-Audio (questions are submitted to the input in audio format, the model responds with text).

Evaluated skills: Object recognition, Object recognition, Human-human interaction, Human-object interaction, Object recognition, Common everyday knowledge, Common domain knowledge, Topic understanding, Scene understanding, Analogical reasoning, Static counting, Mathematical reasoning

Contributors: Denis Shevelev, Artem Chervyakov, Alena Fenogenova, Sergey Markov (the author of the idea)


## Motivation

The dataset is designed to analyze models with a large context window (with a context depth of up to 499 questions), but can also be used for models with a smaller context window with a depth of 15 questions.

The test has a complex task. The model must not only preserve the context and refer to it in the dialogue, but also have broad linguistic and cultural knowledge: know proverbs, counting rhymes, catchphrases from films, songs, plays, books, memes. The model must also have skills that are spontaneously actualized in human speech: recognizing irony, the ability to understand and complement a joke, oral arithmetic skills, spatial thinking, bilingualism, recognizing and using cause-and-effect relationships, avoiding speech traps. Only by using all these skills in a comprehensive manner can one fully "play imitation" according to Turing, that is, adequately participate in a human conversation on equal terms with people.

Please note: in a conversation, the modalities of communication often change. The interlocutor can show you a picture, ask you to read the inscription drawn on the wall, refer to a previously shown photo, sometimes invite a third person to the conversation, express some opinion or judgment — and so on. Therefore, the design of a separate task in the ruTiE-Image dialogue is not always designed as a question — it can be designed as a replica-sentence, to which the model needs to choose an adequate reaction. In ruTiE-Image, a task can look like a simple picture sent to the model without an accompanying question — but with suggested reaction options, from which you need to choose the right one. The dataset offers 4 answer options for each question.

The test checks the model's ability
- to retain context,
- to support (at the everyday level) a dialogue on any of the main subject areas (see the MERA benchmark areas)
- to understand the main classes of problems, without which it is impossible to solve the problems of emulating the Turing test (including the simplest mathematics, ethics, linguistic games, general worldview, etc.)
- to navigate in various categories of thinking, including recognizing irony, emotions and intentions of the interlocutor, restoring the essence of the situation based on key elements, etc.

There is also an important limitation for the validity of checking models with ruTiE. Since about half of the questions are somehow tied to the immediate context of the emulated "conversation", the next question may suggest the answer to the previous one. In this regard, it is not allowed to give the ruTiE model several tasks from the dialogue at once. Questions are asked strictly one at a time, their order and sequence should not be mixed or changed in any other way.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `image` [str] — Path to the image file related to the question.
    - `question` [str] — Text of the question.
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
    - `image` — Image metadata.
        - `type` [str] — Image type — according to the image classification for MERA datasets.


### Data formatting example

```json
{
    "instruction": "Вам придётся запоминать контекст\n<context> беседы, которую с вами ведут текстом и картинками. В каждом задании сопоставьте картинку <image>, если она есть, и текст вопроса, если он есть, с контекстом предыдущей беседы - и выберите наиболее верный вариант ответа. Выведите одну букву, которая его обозначает. Вопрос:\n{question}\nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}\nОтвет:",
    "inputs": {
        "image": "samples/image0001.png",
        "question": "Привет! Я буду звать тебя Ада, а чтобы узнать, как меня зовут, взгляни на картинку и ответь, кто покрасил их в розовый цвет, - а потом возьми три первых буквы этого слова. Так как меня звать?",
        "option_a": "Худ",
        "option_b": "Сол",
        "option_c": "Мал",
        "option_d": "Зак"
    },
    "outputs": "Б",
    "meta": {
        "id": 1,
        "type": "Вводная категория",
        "unified_category": "trap",
        "nonunified_category": "Опознание ситуации",
        "turing_imitation": "algorithmic_transformations",
        "short_context": 0,
        "long_context": 0,
        "image": {
            "type": "real"
        }
    }
}
```


### Dataset creation

The dataset was manually collected by internal experts and then verified. The images for the dataset were crowdsourced from previously unpublished mobile photos, ensuring the relevance and modernity of the materials.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, answers from annotators on a crowd-sourcing platform with an overlap of 5 were obtained. The aggregated answer was considered to be the one chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.55
