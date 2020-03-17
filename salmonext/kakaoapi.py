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
        print("이미지를 대표하는 태그는 \"{}\"입니다.".format(','.join(result['label_kr'])))
    else:
        return None

multitag(clientsec="b42fcb711139457fe5445f970d830286", image_url="https://t1.daumcdn.net/alvolo/_vision/openapi/r2/images/thumbnail_demo1.jpg")