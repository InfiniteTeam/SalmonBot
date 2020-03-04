import discord
import urllib.request
import json
import datetime

replacepairs = (['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`'])

def naverSearch(id, secret, sctype, query, sort='sim'):
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{sctype}?query={encText}&display=100&sort={sort}"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", id)
    request.add_header("X-Naver-Client-Secret", secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode == 200:
        results = json.load(response)
        for linenum in range(len(results['items'])):
            for replaces in replacepairs:
                results['items'][linenum]['title'] = results['items'][linenum]['title'].replace(replaces[0], replaces[1])
                if sctype != 'movie':
                    results['items'][linenum]['description'] = results['items'][linenum]['description'].replace(replaces[0], replaces[1])
        return results
    else:
        return rescode

def blogEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍📝 네이버 블로그 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= results['total']:
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
    if results['total'] > 100: max100 = ' 중 상위 100건'
    else: max100 = ''
    if results['total'] < perpage: allpage = 0
    else: 
        if max100: allpage = (100-1)//perpage
        else: allpage = (results['total']-1)//perpage
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
    return embed

def newsEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍📰 네이버 뉴스 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= results['total']:
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
    if results['total'] > 100: max100 = ' 중 상위 100건'
    else: max100 = ''
    if results['total'] < perpage: allpage = 0
    else: 
        if max100: allpage = (100-1)//perpage
        else: allpage = (results['total']-1)//perpage
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
    return embed

def bookEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍📗 네이버 책 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= results['total']:
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
    if results['total'] > 100: max100 = ' 중 상위 100건'
    else: max100 = ''
    if results['total'] < perpage: allpage = 0
    else: 
        if max100: allpage = (100-1)//perpage
        else: allpage = (results['total']-1)//perpage
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
    return embed

def encycEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍📚 네이버 백과사전 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= results['total']:
            title = results['items'][page*perpage+pgindex]['title']
            link = results['items'][page*perpage+pgindex]['link']
            description = results['items'][page*perpage+pgindex]['description']
            if description == '':
                description = '(설명 없음)'
            embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
        else:
            break
    if results['total'] > 100: max100 = ' 중 상위 100건'
    else: max100 = ''
    if results['total'] < perpage: allpage = 0
    else: 
        if max100: allpage = (100-1)//perpage
        else: allpage = (results['total']-1)//perpage
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
    return embed

def movieEmbed(jsonresults, page, perpage, color, query, naversort):
    results = jsonresults
    embed=discord.Embed(title=f'🔍🎬 네이버 영화 검색 결과 - `{query}`', color=color, timestamp=datetime.datetime.utcnow())
    for pgindex in range(perpage):
        if page*perpage+pgindex+1 <= results['total']:
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
    if results['total'] > 100: max100 = ' 중 상위 100건'
    else: max100 = ''
    if results['total'] < perpage: allpage = 0
    else: 
        if max100: allpage = (100-1)//perpage
        else: allpage = (results['total']-1)//perpage
    builddateraw = results['lastBuildDate']
    builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
    if builddate.strftime('%p') == 'AM':
        builddayweek = '오전'
    elif builddate.strftime('%p') == 'PM':
        builddayweek = '오후'
    buildhour12 = builddate.strftime('%I')
    embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {results['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
    return embed