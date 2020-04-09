import discord
import urllib.request
import json
import datetime
import html

replacepairs = [['<b>', '`'], ['</b>', '`']]
noDescription = ['movie', 'image', 'shop']

def naverSearch(id, secret, sctype, query, sort='sim', display=100):
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{sctype}.json?query={encText}&display={display}&sort={sort}"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", id)
    request.add_header("X-Naver-Client-Secret", secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode == 200:
        results = json.load(response)
        for linenum in range(len(results['items'])):
            # 1. Discord Markdown Escape
            results['items'][linenum]['title'] = discord.utils.escape_markdown(results['items'][linenum]['title'], as_needed=True)
            if not sctype in noDescription:
                results['items'][linenum]['description'] = discord.utils.escape_markdown(results['items'][linenum]['description'], as_needed=True)

            # 2. HTML Unescape
            results['items'][linenum]['title'] = html.unescape(results['items'][linenum]['title'])
            if not sctype in noDescription:
                results['items'][linenum]['description'] = html.unescape(results['items'][linenum]['description'])

            # 3. Other Escape
            for replaces in replacepairs:
                results['items'][linenum]['title'] = results['items'][linenum]['title'].replace(replaces[0], replaces[1])
                if not sctype in noDescription:
                    results['items'][linenum]['description'] = results['items'][linenum]['description'].replace(replaces[0], replaces[1])

        return results
    else:
        return rescode

def resultinfoPanel(results, page, perpage, naversort, display=100):
    if results['total'] > display:
        maxdis = f' 중 상위 {display}건'
    else:
        maxdis = ''
    
    if results['total'] < perpage:
        allpage = 0
    else: 
        if maxdis:
            allpage = (display-1)//perpage
        else:
            allpage = (results['total']-1)//perpage
    
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    panel = f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{maxdis}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```"
    return panel

def blogEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 📝 네이버 블로그 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            bloggername = results['items'][page*perpage+pgindex]['bloggername']
            bloggerlink = results['items'][page*perpage+pgindex]['bloggerlink']
            postdate_year = int(results['items'][page*perpage+pgindex]['postdate'][0:4])
            postdate_month = int(results['items'][page*perpage+pgindex]['postdate'][4:6])
            postdate_day = int(results['items'][page*perpage+pgindex]['postdate'][6:8])
            postdate = f'{postdate_year}년 {postdate_month}월 {postdate_day}일'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}\n- *[{bloggername}]({bloggerlink})* / **{postdate}**", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def newsEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 📰 네이버 뉴스 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            originallink = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            pubdateraw = results['items'][page*perpage+pgindex]['pubDate']
            pubdate = datetime.datetime.strptime(pubdateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
            if pubdate.strftime('%p') == 'AM':
                dayweek = '오전'
            elif pubdate.strftime('%p') == 'PM':
                dayweek = '오후'
            hour12 = pubdate.strftime('%I')
            pubdatetext = f'{pubdate.year}년 {pubdate.month}월 {pubdate.day}일 {dayweek} {hour12}시 {pubdate.minute}분'
            embed.add_field(name="ㅤ", value=f"**[{title}]({originallink})**\n{description}\n- **{pubdatetext}**", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def bookEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 📗 네이버 책 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            author = results['items'][page*perpage+pgindex]['author']
            price = results['items'][page*perpage+pgindex]['price']
            discount = results['items'][page*perpage+pgindex]['discount']
            publisher = results['items'][page*perpage+pgindex]['publisher']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            pubdate_year = int(results['items'][page*perpage+pgindex]['pubdate'][0:4])
            pubdate_month = int(results['items'][page*perpage+pgindex]['pubdate'][4:6])
            pubdate_day = int(results['items'][page*perpage+pgindex]['pubdate'][6:8])
            pubdate = f'{pubdate_year}년 {pubdate_month}월 {pubdate_day}일'
            isbn = results['items'][page*perpage+pgindex]['isbn'].split(' ')[1]
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{author} 저 | {publisher} | {pubdate} | ISBN: {isbn}\n**{discount}원**~~`{price}원`~~\n\n{description}", inline=False)
        else:
            break
    embed.set_thumbnail(url=results['items'][page*perpage+pgindex]['image'])
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def encycEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 📚 네이버 백과사전 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
        else:
            break
    embed.set_image(url=results['items'][page*perpage+pgindex]['thumbnail'])
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def movieEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 🎬 네이버 영화 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            subtitle = results['items'][page*perpage+pgindex]['subtitle']
            pubdate = results['items'][page*perpage+pgindex]['pubDate']
            director = results['items'][page*perpage+pgindex]['director'].replace('|', ', ')[:-2]
            actor = results['items'][page*perpage+pgindex]['actor'].replace('|', ', ')[:-2]
            userrating = results['items'][page*perpage+pgindex]['userRating']
            userratingbar = ('★' * round(float(userrating)/2)) + ('☆' * (5-round(float(userrating)/2)))
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})** ({subtitle})\n`{userratingbar} {userrating}`\n감독: {director} | 출연: {actor} | {pubdate}", inline=False)
        else:
            break
    embed.set_image(url=results['items'][page*perpage+pgindex]['image'])
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def cafeEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 ☕ 네이버 카페글 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            cafename = results['items'][page*perpage+pgindex]['cafename']
            cafeurl = results['items'][page*perpage+pgindex]['cafeurl']
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}\n- *[{cafename}]({cafeurl})*", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def kinEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 🎓 네이버 지식iN 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort), inline=False)
    return embed

def webkrEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 🧾 네이버 웹문서 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 30:
        maxpage = results['total']
    else:
        maxpage = 30
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort, display=30), inline=False)
    return embed

def imageEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 🖼 네이버 이미지 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**", inline=False)
        else:
            break
    embed.set_image(url=results['items'][page*perpage+pgindex]['thumbnail'])
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort, display=100), inline=False)
    return embed

def shopEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 🛍 네이버 쇼핑 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            if results['items'][page*perpage+pgindex]['lprice'] == '0':
                lprice = ''
            else:
                lprice = f"**최저가: {results['items'][page*perpage+pgindex]['lprice']}원**"
            mallname = results['items'][page*perpage+pgindex]['mallName']
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{mallname}\n{lprice}", inline=False)
        else:
            break
    embed.set_image(url=results['items'][page*perpage+pgindex]['image'])
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort, display=100), inline=False)
    return embed

def docEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍 📊 네이버 전문자료 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    if results['total'] < 100:
        maxpage = results['total']
    else:
        maxpage = 100
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= maxpage:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
        else:
            break
    embed.add_field(name="ㅤ", value=resultinfoPanel(results, page, perpage, naversort, display=100), inline=False)
    return embed

def shortUrl(clientid, clientsecret, url):
    encText = urllib.parse.quote(url)
    data = "url=" + encText
    url = "https://openapi.naver.com/v1/util/shorturl"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", clientid)
    request.add_header("X-Naver-Client-Secret", clientsecret)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if rescode == 200:
        response_body = response.read()
        result = response_body.decode('utf-8')
        return json.loads(result)
    else:
        return rescode

def shorturlEmbed(jsonresult, color):
    orgurl = jsonresult['result']['orgUrl']
    url = jsonresult['result']['url']
    embed = discord.Embed(title='📇 네이버 URL 단축 결과', description=f'**원본 URL**:\n{orgurl}\n\n**단축 URL**:\n{url}\n\n**QR코드**:', color=color)
    embed.set_image(url=url + '.qr')
    return embed

def detectLangs(clientid, clientsecret, query):
    encQuery = urllib.parse.quote(query)
    data = "query=" + encQuery
    url = "https://openapi.naver.com/v1/papago/detectLangs"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", clientid)
    request.add_header("X-Naver-Client-Secret", clientsecret)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if rescode == 200:
        response_body = response.read()
        result = response_body.decode('utf-8')
        return json.loads(result)
    else:
        return rescode

def detectlangsEmbed(jsonresult, orgtext, color):
    lang = jsonresult['langCode']
    if lang == 'ko': langstr = ':flag_kr: 한국어'
    elif lang == 'ja': langstr = ':flag_jp: 일본어'
    elif lang == 'zh-cn': langstr = ':flag_cn: 중국어 간체'
    elif lang == 'zh-tw': langstr = ':flag_cn: 중국어 번체'
    elif lang == 'hi': langstr = ':flag_in: 힌디어'
    elif lang == 'en': langstr = '영어'
    elif lang == 'es': langstr = ':flag_es: 스페인어'
    elif lang == 'fr': langstr = ':flag_fr: 프랑스어'
    elif lang == 'de': langstr = ':flag_de: 독일어'
    elif lang == 'pt': langstr = ':flag_pt: 포르투갈어'
    elif lang == 'vi': langstr = ':flag_vn: 베트남어'
    elif lang == 'id': langstr = ':flag_id: 인도네시아어'
    elif lang == 'fa': langstr = '페르시아어'
    elif lang == 'ar': langstr = '아랍어'
    elif lang == 'mm': langstr = ':flag_mm: 미얀마어'
    elif lang == 'th': langstr = ':flag_th: 태국어'
    elif lang == 'ru': langstr = ':flag_ru: 러시아어'
    elif lang == 'it': langstr = ':flag_it: 이탈리아어'
    elif lang == 'unk': langstr = '알 수 없음'
    embed = discord.Embed(title='💬 네이버 파파고 언어 감지', description=f'입력한 텍스트:\n```{orgtext}```\n감지된 언어:\n` `\n**{langstr}**', color=color)
    return embed