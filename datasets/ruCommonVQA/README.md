# ruCommonVQA


## Task description

ruCommonVQA is a publicly available visual question answering dataset in Russian for two types of images: real-world photos and abstract illustrations. 
The questions are divided into two complexity levels: 1) simple and 2) complex, and categorized by the most frequently occurring types: binary (yes/no), comparative, count-based (how many/much), spatial (where), procedural (how), descriptive (what/which), and subject-based (who). Simple questions can be answered based solely on visual perception of the image, while complex ones require a step of reasoning. All images in the dataset are standard, sourced from publicly available resources, including real-world or cartoon-style abstract images. ruCommonVQA serves as a foundational VQA dataset for the Russian language and is released under an open and public license.

Evaluated skills: Scene understanding, Physical property understanding, Object function understanding, Identity & emotion understanding, Static counting, Common everyday knowledge, Spatial object relationship, Object-object interaction, Human-object interaction, Human-human interaction, Object localization, Object recognition, Living things motion recognition, Object motion recognition

Contributors: Maria Tikhonova, Ulyana Isaeva, Alena Fenogenova


## Motivation

The dataset addresses the classic foundational Visual Question Answering (VQA) task, similar to English datasets such as [VQA](https://visualqa.org/download.html). Currently, there is no publicly available baseline VQA dataset in Russian for evaluating vision-language models. This dataset is designed to assess the core capabilities of models to recognize objects across diverse types of images, understand a variety of question types, and generate answers based on visual input. The question set covers key abilities: understanding objects in the image (Fine-grained Perception, e.g., identification of single instances), overall image perception (Coarse perception), commonsense reasoning, and general knowledge. Images are sourced from public datasets, including [COCO](https://cocodataset.org/) and English-language [VQA v2](https://huggingface.co/datasets/pingzhili/vqa_v2), which should be considered as limitation when interpreting evaluation results. There is a possibility of indirect data leakage through the images in model training data.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model.
    - `image` [str] — Path to the image file related to the question.
    - `question` [str] — Text of the question.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `question_type` [str] — question types: compare, how much, what, which, where, who, how, binary;
    - `image` — Image metadata.
        - `source` [list] — source of the image: photo or abstract;
    - `complexity` [str] — Complexity of the question: complex / simple


### Data formatting example

```json
{
    "instruction": "Внимательно посмотрите на картинку <image>.\nОтветьте кратко на вопрос. В качестве ответа напишите слово в той же форме, как спрашивается в вопросе, без дополнительных рассуждений, либо цифру, если ответом является число.\nВопрос:{question}\nОтвет:",
    "inputs": {
        "image": "samples/image0001.jpg",
        "question": "На фото есть люди?"
    },
    "outputs": "Да",
    "meta": {
        "id": 123,
        "categories": {
            "question_type": "binary"
        },
        "image": {
            "source": [
                "photo"
            ]
        },
        "complexity": "simple"
    }
}
```


### Dataset creation

To construct the dataset, images were sourced from the English-language [VQA v2](https://huggingface.co/datasets/pingzhili/vqa_v2) dataset (which includes data from the [COCO](https://cocodataset.org/) dataset).
Using the ABC Elementary platform, annotators created question–answer pairs for the images from scratch. Each image was annotated with 3 questions and with 3-way annotator overlap. 
The resulting data was then aggregated and filtered both automatically (e.g., removal of overly long answers, typos, formatting issues) and manually. The binary question data was class-balanced.

The second part was created entirely from scratch. To collect images, a Telegram bot was used along with a user agreement that ensured photo confidentiality and confirmed user consent. Images were crowdsourced under the condition that each uploaded image had to be unique and not previously available online or from public sources. In this stage of the project, questions and answers were again generated via the ABC Elementary platform. Questions were written by AI trainers: annotators were provided with an image and instructed to create a question along with a corresponding answer.

## Contributors

Maria Tikhonova, Ulyana Isaeva, Alena Fenogenova


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.82
