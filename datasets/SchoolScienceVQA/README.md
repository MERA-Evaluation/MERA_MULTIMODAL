# SchoolScienceVQA


## Task description

**SchoolScienceVQA** is a Russian-language multimodal dataset inspired by [ScienceQA](https://scienceqa.github.io/index.html#home). It evaluates the reasoning capabilities of AI models in a multimodal setting using multiple-choice questions across scientific subjects such as physics, biology, chemistry, economics, history, and earth science. Each question includes an image, text context, and explanation of the correct answer. These components provide a basis for assessing reasoning chains.

Evaluated skills: Expert domain knowledge, Scheme recognition, Text recognition (OCR), Static counting, Problem decomposition, Comparative reasoning, Physical property understanding, Mathematical reasoning

Contributors: Maria Tikhonova, Yulia Lyakh


## Motivation

SchoolScienceVQA is designed to benchmark AI systems in educational and scientific reasoning tasks requiring both visual and textual understanding. It supports the following use cases:

- **Multimodal Model Evaluation**: The dataset requires joint processing of images and text. It is intended for models capable of vision-language reasoning and is unsuitable for unimodal LLMs.

- **Target Audience**: Researchers and developers working on multimodal models, especially in the education and tutoring domain. Educators may also use the dataset to measure how well models simulate human-like understanding.

- **Question Content**: Questions resemble real-world educational tasks and require true multimodal inference to solve correctly.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `image` [str] — Path to the image file related to the question.
    - `context` [str] — A supportive context used along with the image to solve the task.
    - `question` [str] — Text of the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
    - `option_c` [str] — Answer option C.
    - `option_d` [str] — Answer option D.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `domain` [str] — Scientific domain of the sample.
        - `question_difficulty` [int] — Question difficulty.
    - `image` — Image metadata.
        - `type` [list] — Image type — according to the image classification for MERA datasets.
        - `source` [list] — Information about the origin of the image — according to the image classification for MERA datasets.


### Data formatting example

```json
{
    "instruction": "Дано: вопрос с четырьмя вариантами ответа, изображение и, возможно, пояснение к нему. По имеющейся информации ответь на вопрос. В качестве ответа напиши букву правильного ответа без дополнительных пояснений (A, B, C или D).\nИзображение: <image>.\nПояснение: {context}\nВопрос: {question}\nA. {option_a}\nB. {option_b}\nC. {option_c}\nD. {option_d}\nОтвет: ",
    "inputs": {
        "image": "samples/image0760.jpg",
        "context": "",
        "question": "На каком из перечисленных геологических образований вероятность сохранения изображенного на фото покрова на вершинах в течение всего года самая низкая?",
        "option_a": "Аконкагуа, Аргентина",
        "option_b": "Монблан, Франция",
        "option_c": "Килиманджаро, Танзания",
        "option_d": "Денали, США"
    },
    "outputs": "C",
    "meta": {
        "id": 760,
        "image": {
            "type": [
                "visual"
            ],
            "source": [
                "photo"
            ]
        },
        "categories": {
            "domain": "earth_science",
            "question_difficulty": 3
        }
    }
}
```


### Dataset creation

SchoolScienceVQA was developed from scratch based on the methodology of [ScienceQA](https://scienceqa.github.io/index.html#home), adapted for Russian cultural and educational context. Domains were adjusted to align with the Russian school curriculum.

Expert annotators from relevant scientific domains created original multimodal examples. Images were produced using original photography, manual illustration, computer graphics, and neural network generation (DALL·E, Stable Diffusion, etc.). All images are novel and not reused from existing datasets. Metadata includes image generation method to support transparency and bias mitigation.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

These tasks were presented to two groups: one consisting of untrained participants (overlap 5) and the other of domain experts (overlap 3). The aggregated answer was considered to be the one chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.48

- Exact match (expert) – 0.82
