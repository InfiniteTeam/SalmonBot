import xml.etree.ElementTree as et
import requests
import discord

def resultinfoPanel(total, page, perpage, display=50):
    if total > display:
        maxdis = f' 중 상위 {display}건'
    else:
        maxdis = ''
    
    if total < perpage:
        allpage = 0
    else: 
        if maxdis:
            allpage = (display-1)//perpage
        else:
            allpage = (total-1)//perpage
    
    panel = f"```{page+1}/{allpage+1} 페이지, 총 {total}건{maxdis}```"
    return panel

def searchAddresses(servicekey, query, page, perpage):
    resp = requests.get(f'http://openapi.epost.go.kr/postal/retrieveNewAdressAreaCdSearchAllService/retrieveNewAdressAreaCdSearchAllService/getNewAddressListAreaCdSearchAll?ServiceKey={servicekey}&countPerPage={perpage}&currentPage={page}&srchwrd={query}')
    resp.raise_for_status()
    results = resp.content.decode('utf-8')
    return results

def searchAddressesHeader(xmlresults):
    root = et.fromstring(xmlresults)
    if root.find('cmmMsgHeader').find('totalCount') == None:
        totalCount = None
    else:
        totalraw = root.find('cmmMsgHeader').find('totalCount').text
        if type(totalraw) == str:
            totalCount = int(totalraw)
        elif totalraw == None:
            totalCount = None
    successYN = root.find('cmmMsgHeader').find('successYN').text
    if successYN == 'Y':
        successYN = True
    elif successYN == 'N':
        successYN = False
    return {'totalCount': totalCount, 'successYN': successYN}

def searchAddressesEmbed(xmlresults, query, page, perpage, color):
    embed = discord.Embed(title=f'🗺 주소 검색 결과 - {query}', color=color)
    header = searchAddressesHeader(xmlresults)
    root = et.fromstring(xmlresults)
    total = header['totalCount']
    if total < 50:
        maxpage = total
    else:
        maxpage = 50
    for pgindex in range(perpage):
        if page*perpage+pgindex < maxpage:
            one = root.findall('newAddressListAreaCdSearchAll')[page*perpage+pgindex]
            lnmAdres = one.find('lnmAdres').text
            rnAdres = one.find('rnAdres').text
            zipNo = one.find('zipNo').text
            embed.add_field(name='ㅤ', value=f'**{zipNo}** {lnmAdres}\n- `{rnAdres}`', inline=False)
        else:
            break
    embed.add_field(name='ㅤ', value=resultinfoPanel(total, page, perpage, display=50), inline=False)
    return embed

def corona19Masks_byaddr(address):
    data = {'address': address}
    resp = requests.get('https://8oi9s0nnth.apigw.ntruss.com/corona19-masks/v1/storesByAddr/json', data=data)
    resp.raise_for_status()
    results = resp.json()
    return results

def corona19Masks_Embed(jsonresults, page, perpage, storesby='address', color=0x3DB7CC):
    results = jsonresults
    total = results['count']
    if storesby == 'address':
        embed = discord.Embed(title='🧪 공적 마스크 판매처 검색 - 주소 기준', color=color)
    for pgindex in range(perpage):
        if page*perpage+pgindex < total:
            one = results['stores'][page*perpage+pgindex]
            addr = one['addr']
            code = one['code']
            created_at = one['created_at']
            name = one['name']
            remain_stat = one['remain_stat']
            if remain_stat == 'plenty':
                remain_cir = '🟢'
                remain_str = '충분히 많음(100개 이상)'
            elif remain_stat == 'some':
                remain_cir = '🟡'
                remain_str = '약간 (30~99개)'
            elif remain_stat == 'few':
                remain_cir = '🔴'
                remain_str = '아주 적음 (2~29개)'
            elif remain_stat == 'empty':
                remain_cir = '⚪'
                remain_str = '없음 (1개 이하)'
            elif remain_stat == 'break':
                remain_cir = '⛔'
                remain_str = '판매 중지'
            stock_at = one['stock_at']
            storetype = one['type']
            if storetype == '01':
                storetype_str = '🏥 약국'
            elif storetype == '02':
                storetype_str = '📫 우체국'
            elif storetype == '03':
                storetype_str = '🍀 농협 하나로마트'
            embed.add_field(name='ㅤ', value=f'{remain_cir}  **{name}** `({addr})`\n🔹 재고: **{remain_str}**\n🔹 판매처 유형: {storetype_str}\n🔹 기준시간: `{created_at}`\n🔹 이 판매분이 입고된 시간: `{stock_at}`', inline=False)
        else:
            break
    embed.add_field(name='ㅤ', value=resultinfoPanel(total, page, perpage, display=total), inline=False)
    return embed
