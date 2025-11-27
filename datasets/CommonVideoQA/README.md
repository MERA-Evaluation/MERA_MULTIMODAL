# CommonVideoQA


## Task description

CommonVideoQA is a public Russian-language question-answering dataset designed for evaluating video-text models (Video-LLMs), comprising questions related to video clips. It comprehensively assesses the following competencies: general video comprehension and detail recognition, possession of common and domain-specific knowledge, ability to determine the precise order of actions within a video and reconstruct the complete sequence, capability to count objects and actions over time, as well as the skill to associate actions with corresponding temporal boundaries in the video. Given an input video and a question, the task requires selecting the single correct answer from four provided options. Correct answers do not require audio track comprehension. All video clips are sourced from open public repositories.

Evaluated skills: Scene understanding, Object recognition, Object motion recognition, Object-object interaction, Human-object interaction, Human-human interaction, Object localization, Spatial object relationship, Temporal object relationship, Physical property understanding, Object function understanding, Common everyday knowledge, Common domain knowledge, Cause & effect understanding, Static counting, Temporal counting, Mathematical reasoning, Temporal media grounding

Contributors: Vildan Saburov


## Motivation

Most published benchmarks in video understanding focus on English-language content, and currently no Russian-language benchmark is available in the public domain. The CommonVideoQA dataset aims to bridge this gap: it enables the evaluation of how effectively video models can address questions requiring video comprehension (the VideoQA task). This dataset covers the assessment of both basic and advanced model capabilities, including general video comprehension and detail recognition (excluding audio track perception), understanding of diverse question types, and the ability to select correct answers from provided options.

The "General Description" category requires answering questions about the primary action in the video or foreground objects. Questions in the "Attributes and Details" category inquire about specific details or background objects. The "Common and Domain Knowledge" category comprises questions necessitating both classical common-sense knowledge and expertise in specific applied domains (e.g., "In what order should the presented dish be prepared?"). The "Action Sequences" category includes questions testing the understanding of actions in the video, their sequential order, and the ability to reconstruct this sequence. The "Counting" category involves questions assessing the capability to count objects, repetitions of actions over time, and perform basic arithmetic operations with the counts. The "Temporal Intervals" category evaluates the ability to associate actions with temporal boundaries (video timestamps) during which these actions occur. Thus, the dataset evaluates key competencies essential for the video domain.

The dataset comprises video scenes spanning the following domains: "kitchens" (encompassing household activities), "sport" (involving training sessions or competitions), "flora and fauna" (featuring landscapes, wildlife, or plants), "tools" (demonstrating the use of various implements or auxiliary items), and "hobbies" (covering a range of personal pursuits). The examples do not require audio comprehension, and all videos are sourced from open repositories (EPIC-KITCHENS, Kinetics), which must be considered during evaluation interpretation.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `video` [str] — Path to the video file related to the question.
    - `question` [str] — Text of the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `video` — Video metadata.
        - `source` [list] — Information about the origin of the video — according to the video classification for MERA datasets.
        - `type` [list] — Video type — according to the video classification for MERA datasets.
        - `content` [list] — Video content — according to the video classification for MERA datasets.
        - `context` [list] — Accompanying context present in the video — according to the video classification for MERA datasets.
        - `domain` [list] — Video domain.
    - `categories` — Categorial features characterizing the test example.
        - `category` [str] — Question type.


### Data formatting example

```json
{
    "instruction": "Вопрос: {question} \nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}\nДля данных вопроса и вариантов ответа тебе необходимо выбрать верный ответ, отвечай только буквой правильного варианта. Для этого посмотри видео  <video>. Какой твой выбор?",
    "inputs": {
        "video": "samples/video632.mp4",
        "question": "Сколько всего тарелок и тарелочек (не глубоких мисок и не пиал) у героя этого видео?",
        "option_a": "Пятнадцать.",
        "option_b": "Тринадцать.",
        "option_c": "Двенадцать.",
        "option_d": "Шестнадцать."
    },
    "outputs": "A",
    "meta": {
        "id": 604,
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
                "object",
                "situation",
                "inside"
            ],
            "context": [
                "sound_context",
                "with_sound"
            ],
            "domain": [
                "kitchens"
            ]
        }
    }
}
```


### Dataset creation

Video clips for the dataset were sourced from the EPIC-KITCHENS-100 and Kinetics-600 datasets. Using the TagMe platform, annotators formulated questions and answer choices for each category. Each example includes only one correct answer, eliminating ambiguity. Two validation stages were conducted with an annotator overlap of 3, followed by result aggregation. Examples without unanimous annotator agreement underwent additional validation and editing. Post-processing was performed to correct typos. Correct answer options are balanced across classes.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.96
