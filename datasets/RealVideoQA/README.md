# RealVideoQA


## Task description

RealVideoQA is a closed Russian-language question-answering dataset designed for evaluating video-text models (Video-LLMs), comprising questions related to video clips. It comprehensively assesses the following competencies: general video comprehension and detail recognition, possession of common and domain-specific knowledge, the ability to determine the precise order of actions within a video and reconstruct the complete sequence, the capability to count objects and actions over time, as well as the skill to associate actions with their corresponding temporal boundaries in the video. Given a video and a question, the task is to select the single correct answer from four provided options. Correct answers do not require audio track comprehension. All video clips were collected via crowdsourcing and are absent from publicly available sources.

Evaluated skills: Scene understanding, Object recognition, Object motion recognition, Object-object interaction, Human-object interaction, Human-human interaction, Object localization, Spatial object relationship, Temporal object relationship, Physical property understanding, Object function understanding, Common everyday knowledge, Common domain knowledge, Cause & effect understanding, Static counting, Temporal counting, Mathematical reasoning, Temporal media grounding

Contributors: Vildan Saburov


## Motivation

The majority of published benchmarks in video understanding are focused on English, and currently, no publicly available benchmark exists for the Russian language. The RealVideoQA dataset aims to bridge this gap: t enables the evaluation of how effectively video models can address questions requiring video comprehension (the VideoQA task). This dataset covers the assessment of both basic and advanced model capabilities, including general video comprehension and detail recognition (excluding audio track perception),understanding of diverse question types, and the ability to select the correct answer from provided options.

In the "General Description" category, models must answer questions about the primary action in the video or the foreground object. Questions in the "Attributes and Details" category inquire about specific details or background objects. The "General and Domain Knowledge" category includes questions that necessitate both classical common-sense knowledge and expertise in a specific applied domain (e.g., "In what order should the presented dish be prepared?").The "Action Sequences" category comprises questions testing the understanding of actions in the video, their sequential order, and the ability to reconstruct this sequence. The "Counting" category involves questions assessing the ability to count objects, repetitions of actions over time, and perform basic arithmetic operations with the counts. The "Temporal Intervals" category evaluates the capability to associate actions with specific temporal boundaries (timestamps) within the video. Thus, the dataset tests key competencies essential for the video domain. 

Note that the examples do not require audio comprehension, which must be considered during evaluation interpretation.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `inputs` — Input data that forms the task for the model.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
    - `question` [str] — Text of the question.
    - `video` [str] — Path to the video file related to the question.
- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `categories` — Categorial features characterizing the test example.
        - `category` [str] — Question type.
    - `id` [int] — Identification number of the question in the dataset.
    - `video` — Video metadata.
        - `content` [list] — Video content — according to the video classification for MERA datasets.
        - `context` [list] — Accompanying context present in the video — according to the video classification for MERA datasets.
        - `domain` [list] — Video domain (animal, architecture, culture and religion, food, interior, nature, people, sport, tecnology, transport, other).
        - `source` [list] — Information about the origin of the video — according to the video classification for MERA datasets.
        - `type` [list] — Video type — according to the video classification for MERA datasets.
- `outputs` [str] — The correct answer to the question.


### Data formatting example

```json
{
    "inputs": {
        "video": "samples/video184.mp4",
        "question": "Сколько людей на видео прошло вправо?",
        "option_a": "Один.",
        "option_b": "Трое.",
        "option_c": "Двое.",
        "option_d": "Четверо."
    },
    "instruction": "Посмотри <video>. Затем ответь на вопрос \"{question}\", выбрав правильный вариант. Не пиши ничего, кроме буквы.\nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}",
    "outputs": "C",
    "meta": {
        "id": 64,
        "categories": {
            "category": "counting"
        },
        "video": {
            "source": [
                "captured_on_camera"
            ],
            "type": [
                "visual"
            ],
            "content": [
                "subject",
                "action"
            ],
            "context": [
                "sound_context",
                "with_sound"
            ],
            "domain": [
                "people"
            ]
        }
    }
}
```


### Dataset creation

Video clips for the dataset were collected via a Telegram bot using crowdsourcing. Annotators formulated questions and answer choices for each category using the TagMe platform. Each example includes only one correct answer, eliminating ambiguity. Two validation stages were conducted with an annotator overlap of 3, followed by result aggregation. Only examples with unanimous annotator agreement were selected. Post-processing was performed to correct typos. Correct answer options are balanced across classes.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.96
