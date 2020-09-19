from flask import Blueprint, jsonify, request, current_app
import json
from ibm_watson import NaturalLanguageUnderstandingV1, SpeechToTextV1
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os import path
import pathlib

bp_desafio = Blueprint('bp_desafio', __name__)

stt_model = 'pt-BR_BroadbandModel'
stt_apikey = "KfNXCEZwBPSwtZQ4nXmrU8cXbp0obbZEpSb9KCjNG25G"
stt_service_url = "https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/078d673b-4a9e-4cfb-95b2-be82eecea53c"

nlu_apikey = "xA0r-1QemCcz72CTOY8nrnk4yNil70emsQ1LSmM3p-w4"
nlu_service_url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/4ce8b5a1-f053-41b1-8e66-c564941b4a5d"
nlu_entity_model = "56b64e73-3547-43ac-a203-b746797069ee"

lista_de_carros = [
    "FIAT 500",
    "MAREA",
    "ARGO",
    "LINEA",
    "CRONOS",
    "FIORINO",
    "TORO",
    "DUCATO",
    "RENEGADE"
]

@bp_desafio.route('/texto', methods=['POST'])
def texto():
    texto = str()
    for v in request.form:
        texto = request.form[v]
        break
    return jsonify(get_response(texto)), 200

@bp_desafio.route('/audio', methods=['POST'])
def audio():
    for v in request.files:
        audio = request.files[v]
        break
    stt_authenticator = IAMAuthenticator(apikey=stt_apikey)
    stt_service = SpeechToTextV1(authenticator=stt_authenticator)
    stt_service.set_service_url(stt_service_url)

    stt_results = stt_service.recognize(
            audio=audio,
            content_type='audio/flac',
            model=stt_model,
            timestamps=False,
            word_confidence=False).get_result()
    texto = str()
    for i in stt_results['results']:
        for j in i['alternatives']:
            texto = j['transcript']
            break
        break
    return jsonify(get_response(texto)), 200

def get_response(text):
    print(text)
    nlu_authenticator = IAMAuthenticator(apikey=nlu_apikey)

    nlu_service = NaturalLanguageUnderstandingV1(
        version='2018-03-16',
        authenticator=nlu_authenticator)

    nlu_service.set_service_url(nlu_service_url)

    nlu_response = nlu_service.analyze(
        text=text,
        features=Features(entities=EntitiesOptions(model=nlu_entity_model, sentiment=True)),
        language='pt'
    ).get_result()

    negativo = list()
    lista_carros_reclamacoes = list()
    for ent in nlu_response['entities']:
        if ent['sentiment']['score'] < 0:
            value = {
                "entity": ent['type'].upper(),
                "sentiment": ent['sentiment']['score'],
                "mention": ent['text'].upper()
            }
            negativo.append(value)
            lista_carros_reclamacoes.append(value['mention'])
    lista_carros_reclamacoes = list(set(lista_carros_reclamacoes))

    pior_valor = 0
    for n in negativo:
        if n['sentiment'] <= pior_valor:
            pior_valor = n['sentiment']

    piores_notas = list()
    for n in negativo:
        if (pior_valor + 0.1) >= n['sentiment']:
            piores_notas.append(n)

    p = path.join(pathlib.Path().absolute(), 'ranking.json')
    with open(p) as json_file:
        json_ranking = json.loads(json_file.read())

    ranking = dict()
    for i in lista_de_carros:
        if i not in ranking:
            ranking[i] = 0
    for p in piores_notas:
        ent = p['entity']
        mention = p['mention']
        if ent in json_ranking:
            for j in json_ranking[ent]:
                ranking[j] += json_ranking[ent][j]
                if mention not in json_ranking[ent]:
                    print("Mention ("+ mention +") not in ranking.")
        else:
            for i in lista_de_carros:
                ranking[i] += 1
            print('Entity ('+ ent +') not in ranking.')
        
    ranking = {k: v for k, v in sorted(ranking.items(), key=lambda item: item[1], reverse=True)}

    response = {
        "recommendation": str(),
        "entities": negativo
    }
    if negativo:
        for v in ranking.keys():
            if v not in lista_carros_reclamacoes:
                response["recommendation"] = v
                break

    return response