# ruVQA


## Task description

ruVQA is a public question-answering dataset in Russian for two types of images: real photos and abstract illustrations. The questions are divided into 1) simple and 2) complex, categorized by the most frequent types: binary, comparative, how many, where, how, which, what, who. Simple questions require only image-based perception, while complex ones require a step of reasoning. All images in the dataset are classic, from public sources, including real photos and cartoonish abstract images. The dataset is public and serves as a foundational VQA (Visual Question Answering) dataset for the Russian language.

Evaluated skills: Scene understanding, Physical property understanding, Object function understanding, Identity & emotion understanding, Mathematical reasoning, Static counting, Common everyday knowledge, Spatial object relationship, Object-object interaction, Object localization, Object recognition, Living things motion, Object motion, Human body pose recognition


## Motivation

The dataset addresses the classic foundational Visual Question Answering (VQA) task, similar to English datasets [VQA](https://visualqa.org/download.html). For Russian, there is no publicly available baseline VQA dataset to evaluate image-text models. This dataset is designed to test the basic capabilities of models to distinguish objects in various types of images, understand different question types, and generate short answers based on the image. The questions cover key abilities: understanding objects in the image (Fine-grained Perception, single instance), overall image perception (Coarse perception), common sense, and general knowledge. Since the images are sourced from public datasets (COCO dataset, English VQA v2), this should be considered as limitation when interpreting the evaluation. There is a possibility of indirect data leakage through the images in model training data.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `image` [str] — Path to the image file related to the question.
    - `question` [str] — Text of the question.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `question_type` [str] — question types: compare, how much, what, which, where, who, how, binary;
    - `image` — Image metadata.
        - `source` [str] — source of the image: photo or abstract;
    - `complexity` [str] — Complexity of the question: complex / simple


### Data formatting example

```json
{
    "instruction": "Внимательно посмотрите на картинку <image>.\nОтветьте кратко на вопрос. В качестве ответа напишите слово в той же форме, как спрашивается в вопросе, без дополнительных рассуждений, либо цифру, если ответом является число.\nВопрос:{question}\nОтвет:",
    "inputs": {
        "image": "samples/sample1.jpg",
        "question": "Какого цвета комбинезон девушки?"
    },
    "outputs": "Белого",
    "meta": {
        "id": 123,
        "categories": {
            "question_type": "which"
        },
        "image": {
            "source": "photo"
        },
        "complexity": "simple_question"
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Посмотри на изображение <image> и ответь на вопрос по этой картинке. Ответ пиши в той же форме, как спрашивается в вопросе, без дополнительных рассуждений, числа пиши не текстом, а цифрой.

Вопрос:{question}
Ответ:
```


### Dataset creation

The dataset was created using images from the English VQA v2 dataset (which includes data from the COCO dataset). Using the ABC Elementary platform, annotators generated questions and answers for the images from scratch, for each image 3 questions were created and each image was annotated by three annotators. The resulting data was then aggregated and filtered both automatically (to remove long answers, typos, and formatting issues) and manually. The binary question data is balanced across classes.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.
