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
