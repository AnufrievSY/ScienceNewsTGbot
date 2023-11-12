import requests
import bs4
from lxml import html
from tqdm import tqdm
import json
from deep_translator import GoogleTranslator
translator = GoogleTranslator(source='auto', target='ru')


def update():
    main_url = 'https://www.preprints.org'
    req = requests.get(main_url)
    print(f'status | subject_dict.update | {req.status_code}')
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    soup = html.fromstring(str(soup))

    subject_categories = soup.xpath('//*[@id="search_subject_area"]/*/text()')[1:]
    subject_area = soup.xpath('//*[@id="search_subject_area"]/*/@value')[1:]

    subjects_dict = {}
    for index, sa in tqdm(enumerate(subject_area), total=len(subject_categories)):
        subject_area_ural = f'https://www.preprints.org/search?search_subject_area={sa}'
        req = requests.get(subject_area_ural)
        if req.status_code != 200:
            print(
                f'status | subject_dict.update | error with get soup (search_subject_area={sa}/{subject_categories[index]})')
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        soup = html.fromstring(str(soup))
        soup = soup.xpath('//*[@id="search_subject_sub_area"]/*/text()')[1:]
        subjects_dict[subject_categories[index]] = soup
    subjects_dict = {k: [t for t in v if t != 'Other'] for k, v in subjects_dict.items()}
    print('status | subject_dict.update | start translate')
    to_ru = lambda text: translator.translate(text=text)
    subjects_dict_ru = {to_ru(k): [to_ru(t) for t in v] for k, v in tqdm(subjects_dict.items(),
                                                                         total=len(subjects_dict))}
    data = {'original': subjects_dict, 'translate': subjects_dict_ru}
    print('status | subject_dict.update | successfully')

    with open('subjects.json', 'w') as file:
        json.dump(data, file, indent=4)


def get():
    with open('subjects.json', 'r') as file:
        subjects_dict = json.load(file)
    return subjects_dict