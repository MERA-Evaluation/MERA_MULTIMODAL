## Категории метаинформации изображений

Ниже приведена классификация формальных и содержательных характеристик изображений, принятая в MERA Multimodal. Разметка изображений по метаинформации позволяет делать более fine-grained оценки работы моделей с изображениями.

### Происхождение изображения

- `drawing` — нарисованное изображение, в том числе рисунок, изначально сделанный (а не просто доработанный) в цифровых редакторах;
- `tech_drawing` — начерченное изображение, в том числе в программах типа AutoCAD;
- `photo` — фото;
- `screenshot` — скриншот;
- `photoshopped` — смонтированное в графическом редакторе;
- `ai-generated` — сгенерированное;
- `hand-fixed` — доработанное (улучшенное, ухудшенное) вручную;
- `software-fixed` — доработанное (улучшенное, ухудшенное) в графическом редакторе;
- `ai-fixed` — доработанное нейросетями.


### Тип изображения

- `meta_visual` — мета-наглядное, то, что видят приборы или люди при помощи приборов, но то, что человек сам не может увидеть наглядно (спектрограмма, рентгенограмма, МРТ, УЗИ, данные локатора, ИФК-снимок, УФ-снимок, иное мета-наглядное);
- `visual` — наглядное (живопись, графика, фото, скан, рисунок, не относящийся к графике);
- `conditional` — условное (паттерн/орнамент, детская аппликация, тату, абстракция, дорожный знак, оригами);
- `schematic` — схематичное (план, карта, чертёж, блок-схема, схема);
- `systematic` — системное (иерархия, майндмэп, хронологическая таблица, граф, каталог (в том числе скриншот с сайта));
- `graphics` — неизобразительно-информационное (диаграмма, график, инфографика, анонс, реклама, плакат);
- `sign` — знаково-системное (текст/буквы/цифры, ноты, программный код, формулы, числа, брайль, азбука морзе);
- `identic` — идентификационное (штрихкод, QR-код, геометки/координаты, опознавательные знаки (кроме информации из знаково-системного), знаки отличия, гербы и флаги, логотипы, адреса/web-адреса, фирменный стиль, инвентарные и личные номера и коды).


### Содержание изображения

- `subjects` — субъект или группа (речь идет о живых существах: индивидуальный портрет, групповой портрет, бюст);
- `objects` — объект или группа объектов (натюрморт, знак, символ);
- `situation` — ситуация (сцена, последовательность сцен, раскадровка);
- `view` — вид (пейзаж, ландшафт, линия горизонта, панорама);
- `inside` — внутреннее строение (интерьер, разрез, сечение, медицинские снимки из медтех-оборудования, анатомический рисунок, поэтажный или посекционный план);
- `abstraction` — абстракция (фигуры, цвета и пятна);
- `illusion` — иллюзия (слагающийся из объектов текст, слагающийся из объектов иллюзорный объект, невозможные фигуры, нарушения перспективы);
- `riddle` — загадка (ребус, вопросы по картинке, криптограмма);
- `info` — информация (призыв, аналитика, цифры и факты, список, гайд или руководство);
- `mem` — мем (по Докинзу, прочие мемы).


### Сопроводительный контекст

- `footnote` — надписи и подписи (поверх фото, рядом с фото, сноска, выноска, реплика в комиксовом “пузыре”);
- `signature` — идентификаторы (подпись/лого автора/издания, нумерация ("табл. 7", "рис. 9"), идентификаторы автора в соцсетях);
- `draw` — художества (рисунки на полях, пририсованные элементы на изображении);
- `markup` — разметка (стрелки, подчёркивания, обведения, знаки навигации по изображению, перечёркнутость);
- `spots` — пятна (брызги, мазки, отпечатки, потёки);
- `mech_damage` — механические повреждения (потертость, порванность, порезы, склеенность, процарапанность, закаляканность, вырванный или вырезанный элемент, дырки от пуль, обгорелость);
- `no_context` — без сопроводительного контекста.
