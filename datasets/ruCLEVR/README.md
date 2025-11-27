# ruCLEVR


## Task description

RuCLEVR is a Visual Question Answering (VQA) dataset inspired by the [CLEVR](https://cs.stanford.edu/people/jcjohns/clevr/) methodology and adapted for the Russian language.

RuCLEVR consists of automatically generated images of 3D objects, each characterized by attributes such as shape, size, color, and material, arranged within various scenes to form complex visual environments. The dataset includes questions based on these images, organized into specific families such as querying attributes, comparing attributes, existence, counting, and integer comparison. Each question is formulated using predefined templates to ensure consistency and variety. The set was created from scratch to prevent biases. Questions are designed to assess the models' ability to perform tasks that require accurate visual reasoning by analyzing the attributes and relationships of objects in each scene. Through this structured design, the dataset provides a controlled environment for evaluating the precise reasoning skills of models when presented with visual data.

Evaluated skills: Spatial object relationship, Physical property understanding, Object recognition, Object localization, Spatial object relationship, Static counting

Contributors: Ksenia Biryukova, Daria Chelnokova, Jamilya Erkenova, Artem Chervyakov, Maria Tikhonova


## Motivation

The RuCLEVR dataset was created to evaluate the visual reasoning capabilities of multimodal language models, specifically in the Russian language, where there is a lack of diagnostic datasets for such tasks. It aims to assess models' abilities to reason about shapes, colors, quantities, and spatial relationships in visual scenes, moving beyond simple language understanding to test compositional reasoning. This is crucial for models that are expected to analyze visual data and perform tasks requiring logical inferences about object interactions. The dataset's design, which uses structured question families, ensures that the evaluation is comprehensive and unbiased, focusing on the models' reasoning skills rather than pattern recognition.


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
    - `question_type` [str] — Question type according to possible answers: binary, colors, count, materials, shapes, size.
    - `image` — Image metadata.
        - `synt_source` [list] — Sources used to generate or recreate data for the question, including names of generative models.
        - `type` [list] — Image type — according to the image classification for MERA datasets.


### Data formatting example

```json
{
    "instruction": "Изображение:\n<image>\nНа этом изображении показаны различные геометрические объекты со своей формой, цветом и расположением друг относительно друга.\nВопрос: {question}\nЭтот вопрос касается объектов на изображении. Ответь на вопрос одним словом, употребив начальную форму этого слова, или числом, используя цифры для его записи.\nОтвет:",
    "inputs": {
        "image": "samples/image0007.png",
        "question": "Есть ли еще какие-нибудь предметы такой же формы, как и большой металлический предмет?"
    },
    "outputs": "нет",
    "meta": {
        "id": 7,
        "question_type": "binary",
        "image": {
            "synt_source": [
                "blender"
            ],
            "type": [
                "generated"
            ]
        }
    }
}
```


### Dataset creation

To create RuCLEVR, we used two strategies: 1) generation of the new samples and 2) data augmentation with color replacement. Below, each technique is described in more detail:

**Generation of the New Samples**: We generated new, unique images and corresponding questions from scratch. This process involved a multi-step process to ensure a controlled and comprehensive evaluation of visual reasoning. First, 3D images were automatically generated using Blender, featuring objects with specific attributes such as shape, size, color, and material. These objects were arranged in diverse configurations to create complex scenes. Questions with the corresponding answers were then generated based on predefined templates, which structured the inquiries into families, such as attribute queries and comparisons. To avoid conjunction errors, we stick to the original format and generate questions in English, further translating them into Russian using Google Translator. After generation, we automatically filtered incorrectly translated questions using the [model](https://huggingface.co/RussianNLP/ruRoBERTa-large-rucola) pertained to the linguistic acceptability task. In addition, we checked the dataset for the absence of duplicates. 

**Data Augmentation with Color Replacement**: We also augmented the dataset modifying the images from the validation set of the original CLEVER. Specifically, we developed a [script](https://github.com/erkenovaj/RuCLEVR/tree/main) to systematically replace colors in questions and images according to predefined rules, thereby creating new augmented samples. This process was initially conducted in English to avoid morphological complexities. Once the questions were augmented, they were translated into Russian and verified for grammatical correctness.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.96
