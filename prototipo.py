import json
from ibm_watson import NaturalLanguageUnderstandingV1, SpeechToTextV1
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os import path
import pathlib


stt_apikey = "KfNXCEZwBPSwtZQ4nXmrU8cXbp0obbZEpSb9KCjNG25G"
stt_service_url = "https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/078d673b-4a9e-4cfb-95b2-be82eecea53c"

stt_authenticator = IAMAuthenticator(apikey=stt_apikey)

stt_service = SpeechToTextV1(authenticator=stt_authenticator)

stt_service.set_service_url(stt_service_url)

nlu_apikey = "xA0r-1QemCcz72CTOY8nrnk4yNil70emsQ1LSmM3p-w4"
    
nlu_service_url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/4ce8b5a1-f053-41b1-8e66-c564941b4a5d"

nlu_entity_model = "56b64e73-3547-43ac-a203-b746797069ee"

nlu_authenticator = IAMAuthenticator(apikey=nlu_apikey)

nlu_service = NaturalLanguageUnderstandingV1(
    version='2018-03-16',
    authenticator=nlu_authenticator)

nlu_service.set_service_url(nlu_service_url)

stt_model = 'pt-BR_BroadbandModel'

with open('./audio_sample.flac', 'rb') as audio_file:
    stt_results = stt_service.recognize(
            audio=audio_file,
            content_type='audio/flac',
            model=stt_model,
            timestamps=False,
            word_confidence=False).get_result()

# text = "O novo Fiat Toro apresenta um motor incrível! Sem dúvida possui um dos melhores arranques que eu conheço. O design exterior do veículo também é de chamar muita atenção!"
text = "O toro e ARGO é tem o pior lixo horroroso fedido do mal Ar condicionado"

nlu_response = nlu_service.analyze(
    text=text,
    features=Features(entities=EntitiesOptions(model=nlu_entity_model, sentiment=True)),
    language='pt'
).get_result()

lista_carro = [
    "TORO",
    "DUCATO",
    "FIORINO",
    "CRONOS",
    "FIAT 500",
    "MAREA",
    "LINEA",
    "ARGO",
    "RENEGADE"
]

lista_entidade = [
    "SEGURANCA",
	"CONSUMO",
	"DESEMPENHO",
	"MANUTENCAO",
	"CONFORTO",
	"DESIGN",
	"ACESSORIOS"
]

def imprime(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))

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

        # lista = list()
        # for i in value:
        #     if i['mention'] == value['mention']:
        #         lista.append(i)
        # if not lista:
        if not [i for i in negativo if i['mention'] == value['mention']]:
            lista_carros_reclamacoes.append(value['mention'])

pior_valor = 0
for n in negativo:
    if n['sentiment'] <= pior_valor:
        pior_valor = n['sentiment']

piores_notas = list()
for n in negativo:
    if (pior_valor + 0.1) >= n['sentiment']:
        piores_notas.append(n)

entidades_reclamadas = list(set([i['entity'] for i in piores_notas]))

prioridade_entidade = [
    { "SEGURANCA": 7 },
    { "CONSUMO": 6 },
    { "DESEMPENHO": 5 },
    { "MANUTENCAO": 4 },
    { "CONFORTO": 3 },
    { "DESIGN": 2 },
    { "ACESSORIOS": 1 }
]

p = path.join(pathlib.Path().absolute(), 'ranking.json')
with open(p) as json_file:
    json_ranking = json.loads(json_file.read())

ranking = dict()
for p in piores_notas:
    ent = p['entity']
    mention = p['mention']
    if mention not in ranking:
        ranking[mention] = 0
    if ent in json_ranking:
        ranking[mention] += 1
        if mention in json_ranking[ent]:
            ranking[mention] += json_ranking[ent][mention]
        else:
            ranking[mention] += 1
            print("Mention ("+ mention +") not in ranking.")
    else:
        ranking[mention] += 1
        print('Entity ('+ ent +') not in ranking.')
    
v = str()
ranking = {k: v for k, v in sorted(ranking.items(), key=lambda item: item[1], reverse=True)}

response = {
    "recommendation": str(),
    "entities": negativo
}

for v in ranking.keys():
    if v not in lista_carros_reclamacoes:
        response["recommendation"] = v
        break

imprime(response)