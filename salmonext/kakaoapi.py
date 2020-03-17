import requests
import json

def multitag(clientsec, image_url=None, file=None):
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