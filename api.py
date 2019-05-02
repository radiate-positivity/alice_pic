import requests


def add_im(url_im):
    headers = {
        'Authorization': 'OAuth <OAuth-AQAAAAAgybA_AAT7o5bkMo-x70LHvAzRp8P6GCM>',
        'Content-Type': 'application/json'
    }

    data = '{ "url": "{}" }'.format(url_im)

    response = requests.post('https://dialogs.yandex.net/api/v1/skills/74ad82e4-64fc-4474-97e6-3237ce9b2501/images',
                             headers=headers, data=data)
    return response['image']['id']


def del_im(id_im):
    headers = {
        'Authorization': 'OAuth <OAuth-AQAAAAAgybA_AAT7o5bkMo-x70LHvAzRp8P6GCM>'
    }
    requests.delete('https://dialogs.yandex.net/api/v1/skills/%3Cидентификатор%20навыка%3E/images/{}'.format(id_im),
                    headers=headers)

def start():
    url = 'https://deckofcardsapi.com/api/deck/new/shuffle/'
    response = requests.get(url)
    json = response.json()
    
    return json['deck_id']

def take_card(deck_id):
    url = 'https://deckofcardsapi.com/api/deck/{}/draw/?count=1'.format(deck_id)
    response = requests.get(url)
    json = response.json()
    
    return json['cards']
