# RealVQA


## Task description

RealVQA is a benchmark for testing the model's ability to conduct visual question-answering (VQA). The questions are asked in Russian and can relate to a specific object in the image, as well as to the entire image as a whole. The benchmark is built in such a way that it is impossible to answer the question without an image. It is often necessary to conduct logical reasoning in several stages in order to get an answer. A key feature of the dataset is the presence of distractors. Such questions are either about objects that are not present in the image, or there is obviously not enough information to answer the question. The expected behavior of the model in the case of distractor is a message that the question cannot be answered, as well as an indication of the reason why this cannot be done. This is how the model's resistance to hallucinations is tested.

Evaluated skills: Spatial object relationship, Object-object interaction, Human-object interaction, Object localization, Object recognition, Object motion recognition, Living things motion recognition, Common everyday knowledge, Common domain knowledge, Style & genre understanding, Scene understanding, Physical property understanding, Object function understanding, Hypothetical reasoning, Cause & effect understanding, Static counting, Mathematical reasoning, Counterfactual robustness, Problem decomposition, Comparative reasoning

Contributors: Ulyana Isaeva, Alexander Kharitonov, Yaroslav Grebniak, Alena Fenogenova


## Motivation

The dataset is designed to evaluate the model's ability to identify cause-effect relationships and apply logical reasoning based on visual input. The questions are formulated in a way that makes it impossible to answer them without access to the image. Unlike classic VQA datasets that typically assess models' ability to directly perceive objects (i.e., coarse perception: recognizing simple shapes and colors), this dataset incorporates the most complex types of perception from the MERA taxonomy (understanding relationships between objects and different types of reasoning in particular). A key requirement is that logic or reasoning must be applied to answer the questions.
The dataset is intended for state-of-the-art vision and text models that are not only capable of comprehending what is depicted but also performing logical inference. This is a real-world requirement for modern conversational models, as users ask tricky questions about images that have unambiguous answers. Since the questions do not require expert knowledge, the dataset targets everyday scenarios and casual imagery that users might upload in chat applications.


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
        - `question_topic` [list] — the main topics of the question (e.g., text_understanding, logic, etc.);
        - `domain` [list] — the domain of the image (e.g., plant, music, sport, interior, etc.);
    - `image` — Image metadata.
        - `source` [list] — Information about the origin of the image — according to the image classification for MERA datasets.
        - `type` [list] — Image type — according to the image classification for MERA datasets.
        - `content` [list] — Image content — according to the image classification for MERA datasets.
        - `context` [list] — Accompanying context present in the image — according to the image classification for MERA datasets.


### Data formatting example

```json
{
    "instruction": "Внимательно посмотрите на картинку <image>.\nОтветьте на заданный вопрос кратко. В качестве ответа на вопрос напишите слово в той же форме, как спрашивается в вопросе, без дополнительных рассуждений.\n\nВопрос:{question}\n\nОтвет:",
    "inputs": {
        "image": "samples/image0165.jpg",
        "question": "Предположительно в какой день недели сделано это фото?"
    },
    "outputs": "в пятницу",
    "meta": {
        "id": 165,
        "categories": {
            "question_topic": [
                "text_understanding"
            ],
            "domain": [
                "tecnology"
            ]
        },
        "image": {
            "source": [
                "photo"
            ],
            "type": [
                "photo",
                "text",
                "inventory_code"
            ],
            "content": [
                "object"
            ],
            "context": [
                "no_context"
            ]
        }
    }
}
```


### Dataset creation

Image collection was carried out via a Telegram bot under a user agreement ensuring non-disclosure of the photos and user consent. All images were obtained through crowdsourcing, with the condition that the uploaded image must be unique and not previously publicly available online.
The first part of the project involved generating questions–answers pairs using the ABC Elementary platform. The questions were written by AI trainers. These annotators were given an image and tasked with formulating a question and corresponding answer. Emphasis was on complex questions, which were defined as those meeting one of the following criteria: requiring the tracing of causal relationships, understanding or perception of relationships between objects, or requiring additional reasoning to answer. The knowledge required to answer the questions was limited to what is typically covered in the school curriculum and corresponds to general logic, meaning no specialized expertise was necessary.
Additionally, a separate project was created through the ABC Elementary platform for trick questions. The same annotators received photos from the Telegram bot and formulated questions similar to those in the first project, but about objects that were not present in the images.
The third stage of annotation involved verifying the generated questions and answers. Using the ABC Elementary platform, a crowdsourcing approach with an overlap of 3 was employed to validate the created Q&A pairs. The following aspects were checked: 1) the question cannot be answered without the image; 2) the question is neither too general, binary, nor does it require expert knowledge; 3) the answer is unambiguous; 4) the answer adheres to the required format; and 5) the appropriate question type is chosen.
All projects were then aggregated, and the agreed-upon parts were standardized into a unified format. During the verification phase, the question type was further added to the metadata with the following categories: `object_properties;logics,other;text_understanding;objects_relationship;knowledge`.
Trick questions comprised 10% of the dataset.


## Evaluation

### Metrics

Metrics for aggregated evaluation of responses:

- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.


### Human baseline

Human baseline is an evaluation of the average human answers to the benchmark questions. The evaluation is carried out using the same metrics as for the models.

For all questions in the dataset, annotator answers were obtained on a crowd-sourcing platform with an overlap of 5. Free-form answers were normalized (case, spaces) for comparison with the reference. The aggregated answer was considered to be the one that was chosen by the majority (majority vote).

Evaluation results:

- Exact match – 0.58
