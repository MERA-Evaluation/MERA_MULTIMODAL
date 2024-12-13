# WEIRD


## Task description

WEIRD is an extended version of a binary classification subtask of the original English [WHOOPS!](https://whoops-benchmark.github.io/) benchmark. The dataset evaluates the ability to detect violations of commonsense. Commonsense violations are situations that contradict the norm of reality. For example, penguins can't fly, children don't drive cars, guests don't set the table for the waiter, etc. "Weird" and "normal" images are equally distributed in the dataset.

Evaluated skills: Weirdness understanding, Common everyday knowledge, Physical property understanding, Object function understanding, Identity & emotion understanding, Other inductive reasoning

Contributors: Elisei Rykov, Vasily Konovalov, Alexander Panchenko


## Motivation

The dataset focuses on the evaluation of the reality check, and is suitable for the evaluation of any AI models that can analyze images. The main capability that this dataset evaluates is the analysis of the visual information and collating it with the common sense. Accuracy is the main evaluation metric. Since the dataset evaluates the basic ability of reality check, it will be interesting for any research as one of the basic stages of the model evaluation pipeline.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `image` [str] — Path to the image file related to the question.
    - `question` [str] — Text of the question.
    - `option_a` [str] — Answer option A.
    - `option_b` [str] — Answer option B.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `categories` — Categorial features characterizing the test example.
        - `commonsense_violation_subgroup` [str] — The synthetically generated subgroup of commonsense violation;
        - `commonsense_violation_group` [str] — Commonsense violation group, obtained manually by combining the subgroups;
    - `caption` [str] — The textual caption used for image generation;
    - `pair_id` [str] — Image pair number;
    - `image` — Image metadata.
        - `synt_source` [list] — Models used for this sample generation;
        - `source` [str] — The source of image


### Data formatting example

```json
{
    "instruction": "Внимательно изучите предложенное изображение.\n<image>.\n Вопрос: {question}. Странные изображения противоречат здравому смыслу, в то время как нормальные ему соответствуют. В качестве ответа укажите только букву A или B без дополнительных рассуждений.\n\nA. {option_a}\nB. {option_b}\nОтвет:",
    "inputs": {
        "image": "samples/image0.jpg",
        "question": "изображение странное или нормальное?",
        "option_a": "странное",
        "option_b": "нормальное"
    },
    "outputs": "A",
    "meta": {
        "id": 0,
        "categories": {
            "commonsense_violation_subgroup": "Object Misplacement",
            "commonsense_violation_group": "Object Function and Misuse"
        },
        "caption": "A plate of spaghetti served on a dinner table with a fork.",
        "pair_id": "v10_47",
        "image": {
            "synt_source": [
                "gpt-4o",
                "dall-e-3"
            ],
            "source": "ai-generated"
        }
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Внимательно изучите предложенное изображение.
<image>.
 Вопрос: {question}. Странные изображения противоречат здравому смыслу, в то время как нормальные ему соответствуют. В качестве ответа укажите только букву A или B без дополнительных рассуждений.

A. {option_a}
B. {option_b}
Ответ:
```


### Dataset creation

The dataset was created based on the original [WHOOPS!](https://whoops-benchmark.github.io/) benchmark, using iterative synthetic generation in the style of [Self-Instruct](https://github.com/yizhongw/self-instruct). Each sample from the WHOOPS! subset for binary classification is a pair consisting of a "weird" and a "normal" image, along with categories of commonsense violations and image descriptions. To extend the original benchmark, we iteratively generated new categories of commonsense violation and image descriptions using GPT-4o with WHOOPS! samples as a few shots. In addition, we used synthetic descriptions to generate images using DALL-E. Next, we manually filtered out bad images and added good images to the pool. Finally, the pool was used to repeat the generation process and extract new few-shots.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `Accuracy`: Accuracy is the proportion of correct model predictions among the total number of cases processed.


### Human baseline

To compare the quality of the model responses and human responses, measurements of human responses were taken using the following methodology.

The human baseline was annotated on the Yandex Tasks platform with an overlap of 5 annotators. 80 control tasks and 10 training tasks were added. Annotators who did not complete at least 80% of the training tasks correctly were not allowed to annotate. Annotators with errors in 5 or more control tasks were excluded from markup. This resulted in a Krippendorff's alpha coefficient of consistency of 0.69 and a human accuracy of 82.22%.

Evaluation results:

- Accuracy – 82.22
