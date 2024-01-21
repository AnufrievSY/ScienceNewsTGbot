import requests
import bs4
from lxml import html
from tqdm import tqdm
import json
import time
import pandas as pd
from deep_translator import GoogleTranslator
translator = GoogleTranslator(source='auto', target='ru')


def update():
    topics_df = pd.DataFrame(columns=['original', 'translate', 'type'])

    main_url = 'https://www.preprints.org'
    req = requests.get(main_url)
    print(f'status | subject_dict.update | get main topics: {req.status_code}')
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    soup = html.fromstring(str(soup))
    subject_categories = soup.xpath('//*[@id="search_subject_area"]/*/text()')[1:]
    subject_area = soup.xpath('//*[@id="search_subject_area"]/*/@value')[1:]

    print(f'status | subject_dict.update | get sub topics:')
    time.sleep(0.5)
    for index, (sa, sc) in tqdm(enumerate(zip(subject_area, subject_categories)), total=len(subject_area)):
        topics_df.loc[sa] = [sc, '', 'main']
        subject_area_ural = f'https://www.preprints.org/search?search_subject_area={sa}'
        req = requests.get(subject_area_ural)
        if req.status_code != 200:
            print(
                f'status | subject_dict.update | ',
                f'error with get soup (search_subject_area={sa}/{subject_categories[index]})')
            break
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        soup = html.fromstring(str(soup))
        sub_subject_name = soup.xpath('//*[@id="search_subject_sub_area"]/*/text()')[1:2]
        sub_subject_area = soup.xpath('//*[@id="search_subject_sub_area"]/*/@value')[1:2]
        topics_df = pd.concat([topics_df,
                               pd.DataFrame({'original': sub_subject_name,
                                             'translate': '',
                                             'type': 'sub'},
                                            index=sub_subject_area)],
                              ignore_index=False).drop_duplicates()

    time.sleep(0.5)
    print(f'status | subject_dict.update | translate topics')
    time.sleep(0.5)
    topics_df.translate = [translator.translate(text=text) for text in tqdm(topics_df.original)]

    topics_df.to_json('topics.json')
def load():
    with open('topics.json', 'r') as file:
        subjects_dict = json.load(file)
    return pd.DataFrame(subjects_dict)

df = load()

for i in df.loc[df.type == 'main', 'translate'].items():
    print(i)
