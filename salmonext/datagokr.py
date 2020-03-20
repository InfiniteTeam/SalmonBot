import xml.etree.ElementTree as et
import requests
import discord

def searchAddresses(servicekey, query, page, perpage):
    resp = requests.get(f'http://openapi.epost.go.kr/postal/retrieveNewAdressAreaCdSearchAllService/retrieveNewAdressAreaCdSearchAllService/getNewAddressListAreaCdSearchAll?ServiceKey={servicekey}&countPerPage={perpage}&currentPage={page}&srchwrd={query}')
    resp.raise_for_status()
    results = resp.content.decode('utf-8')
    return results

def searchAddressesEmbed(xmlresults, query, page, perpage, color):
    pass

print(search_addresses('eeCC0h6692iNrA1sPg%2FKgsv1kutslrJp3ErAa1UowDC4fqkO3J6ZTY5ErAN8MJfiUe42BMXiqN8a55P6LG%2B%2BGQ%3D%3D', '파호동', 1, 5))