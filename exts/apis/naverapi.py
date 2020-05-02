import discord
import asyncio
import aiohttp
import datetime
import html.parser
import furl

class Search:
    sectorfmt = {
        'blog': '📝 네이버 블로그',
        'news': '📰 네이버 뉴스',
        'book': '📚 네이버 책',
        'encyc': '📖 네이버 백과사전',
        'cafearticle': '☕ 네이버 카페글',
        'kin': '💬 네이버 지식인',
        'webkr': '📜 네이버 웹문서',
        'image': '🖼 네이버 이미지',
        'shop': '🛍 네이버 쇼핑',
        'doc': '🗃 네이버 전문자료'
    }
    sortfmt = {
        'sim': '정확도순',
        'date': '최신순',
        'asc': '저렴한순',
        'dsc': '비싼순',
        'count': '판매량순'
    }
    reescapes = [['<b>', '<b<'],
                ['</b>', '</b<']]
    unescapes = [['<b<', '`'],
                ['</b<', '`']]

    @staticmethod
    def unescape(s):
        for x, y in Search.reescapes:
            s = s.replace(x, y)
        e = discord.utils.escape_markdown(html.parser.unescape(s))
        for x, y in Search.unescapes:
            e = e.replace(x, y)
        return e

    @staticmethod
    async def search(cid, sec, query, sector, display=100, sort='sim') -> dict:
        params = {
            'query': query,
            'display': display,
            'sort': sort
        }
        async with aiohttp.ClientSession() as s:
            async with s.get('https://openapi.naver.com/v1/search/{}.json'.format(sector), headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}, params=params) as resp:
                rst = await resp.json()
        return rst

    @staticmethod
    def embed(rls, rst, sector, query, page, allpage, color, sort, detailsyn=False):
        embed = discord.Embed(title=Search.sectorfmt[sector] + ' 검색 - `{}`'.format(query), color=color)
        for one in rls:
            title = Search.unescape(one['title'])
            link = one['link']
            desc = Search.unescape(one['description'])
            if sector == 'blog':
                bname = Search.unescape(one['bloggername'])
                blink = one['bloggerlink']
                postdate = datetime.datetime.strptime(one['postdate'], '%Y%m%d')
                postdatestr = postdate.strftime('%Y{} %m{} %d{}').format('년', '월', '일')
                embed.add_field(name='ㅤ', value=f'[**{title}**]({link})\n{desc}\n- [*{bname}*]({blink}), {postdatestr}', inline=False)
            elif sector == 'news':
                pubdate = datetime.datetime.strptime(one['pubDate'], '%a, %d %b %Y %X +0900')
                pubweekday = ['월', '화', '수', '목', '금', '토', '일'][pubdate.weekday()]
                pubdatestr = pubdate.strftime('%Y{} %m{} %d{} {}{} %X').format('년', '월', '일', pubweekday, '요일')
                embed.add_field(name='ㅤ', value=f'[**{title}**]({link})\n{desc}\n- {pubdatestr}', inline=False)
            elif sector == 'book':
                image = furl.furl(one['image']).remove(args=True, fragment=True).url
                author = ', '.join(one['author'].split('|'))
                price = one['price']
                discount = one['discount']
                if discount:
                    pricestr = f'**{discount}원**~~`{price}원`~~'
                else:
                    pricestr = f'**{price}원**'
                publisher = one['publisher']
                isbn = one['isbn']
                pubdate = datetime.datetime.strptime(one['pubdate'], '%Y%m%d')
                pubdatestr = pubdate.strftime('%Y{} %m{} %d{}').format('년', '월', '일')
                embed.add_field(name='ㅤ', value=f'**[{title}]({link})**\n{author} 저 | {publisher} | {pubdate} | ISBN: {isbn}\n{pricestr}\n\n{desc}', inline=False)
        total = rst['total']
        totalstr = ''
        if total < 100:
            totalstr = f'중 {total}건'
        sortstr = Search.sortfmt[sort]
        embed.add_field(name='ㅤ', value=f'```{page+1}/{allpage}페이지, 전체 {total}건, {sortstr} {totalstr}```', inline=False)
        if sector == 'book' and detailsyn:
            embed.set_image(url=image)
        return embed