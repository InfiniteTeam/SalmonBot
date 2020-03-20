import requests
import json
import discord

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

def search_address(clientsec, query, page, size):
    headers = {'Authorization': 'KakaoAK {}'.format(clientsec)}
    data = {'query': query, 'page': page, 'size': size}
    resp = requests.post('https://dapi.kakao.com/v2/local/search/address.json', headers=headers, data=data)
    resp.raise_for_status()
    result = resp.json()
    return result

def search_addressEmbed(jsonresults, query, page, perpage, color):
    results = jsonresults
    total = results['meta']['total_count']
    embed = discord.Embed(title=f'🗺 주소검색 결과 - {query}', color=color)
    existaddr = False
    for one in results['documents']:
        if one['address_type'] in ['ROAD_ADDR', 'REGION_ADDR']:
            existaddr = True
            oneroad = one['road_address']
            oneregion = one['address']
            if oneregion['sub_address_no']:
                oneaddressno = oneregion['main_address_no'] + '-' + oneregion['sub_address_no']
            else:
                oneaddressno = oneregion['main_address_no']
            onefield = f"{oneroad['zone_no']} **{oneroad['address_name']}** ({oneregion['region_3depth_name']} {oneaddressno}, {oneroad['building_name']})"
            embed.add_field(name='ㅤ', value=onefield, inline=False)
    if total%perpage == 0:
        allpage = total//perpage
    else:
        allpage = total//perpage + 1
    embed.add_field(name='ㅤ', value=f'```{page}/{allpage} 페이지, 총 {total}건```', inline=False)
    if existaddr:
        return embed
    else:
        return None
