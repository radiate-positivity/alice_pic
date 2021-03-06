from flask import Flask, request
import logging
import json
import os
import requests
import sys
from api import add_im, del_im, start, take_card

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s %(levelname)s %(name)s %(message)s')

sessionStorage = {}

P = {'0': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
K = {'H': '♥', 'S': '♠', 'C': '♣', 'D': '♦'}
V = {'0': '10', 'J': 'В', 'Q': 'Д', 'K': 'K', 'A': 'Т'}

LOSE = '1030494/49669d94682dd7fdced2'
WIN = '1533899/ddeb8459de13000602f7'

mega_cards = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)

def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,
            'game_id': None,
            'point': 0
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Хочешь поиграть в карты?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                    'hide': True
                }
            ]

    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                game_id = start()
                sessionStorage[user_id]['game_id'] = game_id
                sessionStorage[user_id]['game_started'] = True
                # res['response']['text'] = game_id
                play_game(res, req)

            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Хорошо, приходите ещё!'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['game_id'] = None
                sessionStorage[user_id]['point'] = 0
                res['end_session'] = True

            elif 'правила' in req['request']['nlu']['tokens']:
                res['response'][
                    'text'] = 'Вам произвольно выбирается карта из колоды. Количество очков равно номиналу карты. Король, дама, валет оцениваются как 10 очков, а туз как 11. Карты берутся, пока количество набранных очков не равно 21 или более. Если вы набрали ровно 21 очко - вы выиграли, больше - проиграли. Будем играть?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Правила',
                        'hide': True
                    }
                ]
            else:
                res['response']['text'] = 'Так ты хочешь сыграть?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Правила',
                        'hide': True
                    }
                ]
        else:
            if 'да' in req['request']['nlu']['tokens']:
                play_game(res, req)

            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Хорошо, приходите ещё!'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['game_id'] = None
                sessionStorage[user_id]['point'] = 0
                res['end_session'] = True

            elif 'правила' in req['request']['nlu']['tokens']:
                res['response'][
                    'text'] = 'Вам произвольно выбирается карта из колоды. Количество очков равно номиналу карты. Король, дама, валет оцениваются как 10 очков, а туз - 11. Карты берутся, пока количество набранных очков не равно 21 или более. Если вы набрали ровно 21 очко - вы выиграли, больше - проиграли. Продолжим?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Правила',
                        'hide': True
                    }
                ]
            else:
                res['response']['text'] = 'Кажется, я не поняла, что вы хотели сказать. Повторите, пожалуйста.'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Правила',
                        'hide': True
                    }
                ]

def play_game(res, req):
    user_id = req['session']['user_id']
    p, p_o, card = take(sessionStorage[user_id]['game_id'], sessionStorage[user_id]['point'], res)
    sessionStorage[user_id]['point'] = p
    if p == 21:
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card'][
            'title'] = 'Вы вытащили {}, это {} очков. Всего у вас 21 очко! Вы выйграли! Хотите сыграть ещё?'.format(card, p_o)
        res['response']['card']['image_id'] = WIN
        sessionStorage[user_id]['game_started'] = False
        sessionStorage[user_id]['game_id'] = None
        sessionStorage[user_id]['point'] = 0

    elif p > 21:
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card'][
            'title'] = 'Вы вытащили {}, это {}. Всего очков: {}. Вы проиграли :( Хотите сыграть ещё?'.format(card, p_o, p)
        res['response']['card']['image_id'] = LOSE
        sessionStorage[user_id]['game_started'] = False
        sessionStorage[user_id]['game_id'] = None
        sessionStorage[user_id]['point'] = 0

    else:
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card'][
            'title'] = 'Вы вытащили {}, это {}. Всего очков: {}. Берём ещё карту?'.format(card, p_o, p) 
        res['response']['card']['image_id'] = mega_cards[card] 

    res['response']['buttons'] = [
        {
            'title': 'Да',
            'hide': True
        },
        {
            'title': 'Нет',
            'hide': True
        },
        {
            'title': 'Правила',
            'hide': True
        }
    ]
    return

def take(game_id, point, res):
    p_o = None
    card = None
    cards = take_card(game_id)
    card = cards[-1]['code']
    url_card = cards[-1]['image']
    ru_crd = list(card)
    res['response']['text'] = '{}'.format(card)
    if card[0].isdigit() and card[0] != '0':
        p_o = int(card[0])
        point += int(card[0])
    else:
        p_o = P[card[0]]
        point += P[card[0]]
        ru_crd[0] = V[card[0]]
    ru_crd[1] = K[card[1]]
    if ''.join(ru_crd) not in mega_cards:
        mega_cards[''.join(ru_crd)] = add_im(url_card) 
    return point, p_o, ''.join(ru_crd)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)
        
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
