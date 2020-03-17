import requests
import json

def multitag(clientsec, image_url):
    headers = {'Authorization': 'KakaoAK {}'.format(clientsec)}
    data = {'image_url': image_url}
    resp = requests.post('https://kapi.kakao.com/v1/vision/multitag/generate', headers=headers, data=data)
    resp.raise_for_status()
    result = resp.json()['result']
    if len(result['label_kr']) > 0:
        if type(result['label_kr'][0]) != str:
            result['label_kr'] = map(lambda x: str(x.encode("utf-8")), result['label_kr'])
        return result['label_kr']
    else:
        return None

def text_detect(clientsec, image_file):
    headers = {'Authorization': 'KakaoAK {}'.format(clientsec)}
    files = {'files': image_file}
    resp = requests.post('https://kapi.kakao.com/v1/vision/text/detect', headers=headers, files=files)
    resp.raise_for_status()
    result = resp.json()['result']
    if len(result['boxes']) > 0:
        return result['boxes']
    else:
        return None

def text_recognize(clientsec, image_file, boxes):
    headers = {'Authorization': 'KakaoAK {}'.format(clientsec)}
    data = {'boxes': str(boxes)}
    files = {'files': image_file}
    resp = requests.post('https://kapi.kakao.com/v1/vision/text/recognize', headers=headers, data=data, files=files)
    resp.raise_for_status()
    result = resp.json()['result']
    if len(result['recognition_words']) > 0:
        return result['recognition_words']
    else:
        return None