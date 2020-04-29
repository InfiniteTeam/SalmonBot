import discord
import asyncio
import aiohttp

class AddressSearch:
    @staticmethod
    async def search_address(key: str, query, page: int=1, size: int=30):
        headers = {'Authorization': 'KakaoAK {}'.format(key)}
        params = {
            'query': query,
            'page': page,
            'AddressSize': size
        }
        async with aiohttp.ClientSession() as s:
            async with s.get('https://dapi.kakao.com/v2/local/search/address.json', headers=headers, params=params) as resp:
                results = await resp.json()
                return results

    @staticmethod
    def search_address_make_embed(addrs: list, page, allpage, total):
        embed = discord.Embed(title='🗺 주소검색')
        a = list(filter(lambda x: x['address_type'] in ['REGION_ADDR', 'ROAD_ADDR'], addrs))
        desc = ''
        for one in a:
            road_addr = one['road_address']['address_name']
            rname = one['address']['region_3depth_name']
            if one['address']['sub_address_no']:
                rno = one['address']['main_address_no'] + '-' + one['address']['sub_address_no']
            else:
                rno =  one['address']['main_address_no']
            building = one['road_address']['building_name']

            embed.add_field(name='ㅤ', value=f'🔹 **{road_addr}** `({rname} {rno}, {building})`', inline=False)
        totalstr = ''
        if total < 30:
            totalstr = f'중 {total}건'
        embed.add_field(name='ㅤ', value=f'```{page}/{allpage}페이지, 전체 {total}건 {totalstr}```', inline=False)
        return embed