import json
import re
from datetime import datetime
import time
from operator import itemgetter, attrgetter
'''
    resources.lib.leesrtlxl
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching RTLxl

    # low
	# http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az/output=xml
	# http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=a2t/fmt=progressive/ak=216992/output=xml/pg=1/
	# http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/pg=1/output=xml/ak=283771/sk=301653
	# http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/uuid=6937d7bb-bf40-4f51-9590-c2c8131bccc7/output=xml/
    # http://pg.us.rtl.nl//rtlxl/network/a2t/progressive/components/videorecorder/28/283771/301653/6937d7bb-bf40-4f51-9590-c2c8131bccc7.ssm/6937d7bb-bf40-4f51-9590-c2c8131bccc7.mp4

    ## deze met a2t omdat deze geen drm doet!
    http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az
    http://www.rtl.nl/system/s4m/vfd/version=2/d=pc/output=json/fun=az/fmt=smooth
    http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1
    http://www.rtl.nl/system/s4m/vfd/version=2/uuid=1b10429e-7dd9-3506-b558-0a3de42bae1e/fmt=adaptive/output=json/

    ## nieuwe api rtlxl
    https://xlapi.rtl.nl/version=2/fun=az/model=svod
    https://xlapi.rtl.nl/version=1/fun=progclasses/ak=426250
    https://xlapi.rtl.nl/version=1/fun=progeps/ak=426250/model=svod/pg=1/sk=426308/sz=6

'''
import sys
if (sys.version_info[0] == 3):
    # For Python 3.0 and later
    from urllib.request import urlopen, Request
else:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, Request


class RtlXL:
    def __gettextitem(self, element, elementnaam):
        el = element.find(elementnaam)
        if el is None:
            return ''
        return el.text

    def __value_of_dict(self, dic, key):
        if key in dic:
            return dic[key]
        return ''

    def get_overzicht(self):
        req = self.__set_request_headers(
            'http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az')
        response = urlopen(req)
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        rtlitemlist = list()
        poster_base_url = json_data['meta']['poster_base_url']
        for serie in json_data['abstracts']:
            item = {'label': serie['name'], 
                    'url': serie['itemsurl'],
                    'art': {    'thumb': poster_base_url + serie['coverurl'],
                                'icon':  poster_base_url + serie['coverurl'],
                                'fanart': poster_base_url + serie['coverurl']
                            },
                    'video': {
                        'title': serie['name'],
                        'plot': self.__value_of_dict(serie, 'synopsis'),
                        'studio': self.__value_of_dict(serie, 'station'),
                        'mediatype': 'video'
                    }
            }
            rtlitemlist.append(item)
        return sorted(rtlitemlist, key=lambda x: x['label'], reverse=False)

    def __items(self, url, alles, videotype):
        req = self.__set_request_headers(url)
        response = urlopen(req)
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        rtlitemlist = list()
        cover_base_url = json_data['meta']['cover_base_url']
        for material in json_data['material']:
            rtlitem = { 'label': material['title'],
                        'uuid': material['uuid'],
                        'videotype': videotype,
                        #'path': self.movie_trans(material['uuid'], videotype),
                        'classname': material['classname'],
                        'art': {    'thumb': cover_base_url + material['image'],
                                    'icon':  cover_base_url + material['image'],
                                    'fanart': cover_base_url + material['image']
                                },
                        'video': {
                            'title': 'zie hier onder, word gezet.',
                            'date': datetime.fromtimestamp(int(material['original_date'])).strftime("%d-%m-%Y"),
                            'aired': datetime.fromtimestamp(int(material['original_date'])).strftime("%Y-%m-%d"),
                            'premiered': datetime.fromtimestamp(int(material['display_date'])).strftime("%Y-%m-%d"),
                            'plot': self.__value_of_dict(material, 'synopsis'),
                            'studio': self.__value_of_dict(material, 'station'),
                            'year': datetime.fromtimestamp(int(material['original_date'])).strftime("%Y"),
                            'genre': '',
                            'mediatype': 'video'
                        }
            }
            for episode in json_data['episodes']:
                if episode['key'] == material['episode_key']:
                    if material['classname'] == 'uitzending':
                        rtlitem['label'] = episode['name'] # uitzendinggen hebben hier beter naam.
                    if alles:
                        rtlitem['label'] = rtlitem['label'] + ' ('+material['classname']+')'
                # opzoeken juiste aflevering info
                if episode['key'] == material['episode_key']:
                    # als we gernes hebben
                    if 'genre' in episode:
                        # we halen nu keys op welke bij aflevering horen
                        genreskeys = episode['genre'].split(",")
                        genres = list()
                        for key in genreskeys:
                            for genresjson in json_data['genres']:
                                # match op key van genre in aflevering en genre beschrijving
                                if genresjson['key'] == key:
                                    # toevoegen naam aan lijst
                                    genres.append(genresjson['name'])
                        # komma gescheiden weer opslaan in het item
                        # set ontdubbeld
                        rtlitem['video']['genre'] = ', '.join(list(set(genres)))
            rtlitem['video']['title'] = rtlitem['label']
            if material['episode_key']:
                rtlitemlist.append(rtlitem)
        return rtlitemlist

    def __is_uitzending(self, item):
        return item['classname'] == 'uitzending'

    def get_categories(self, url):
        items = self.__items(url, True, 'adaptive')
        aantaluitzendingen = [
            item for item in items if self.__is_uitzending(item)]
        terug = list()
        terug.append({
            'keuze': 'afleveringen',
            'selected': True,
            # aantal uitzendingen
            'title': 'uitzendingen: (' + str(len(aantaluitzendingen)) + ')',
            'url': url,  # url met alle items
        })
        terug.append({
            'keuze': 'alles',
            'selected': False,
            'title': 'alles: (' + str(len(items)) + ')',  # aantal alles
            'url': url,  # url met alle items
        })
        return terug

    def __set_request_headers(self, url):
        req = Request(url)
        # req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
        req.add_header(
            'User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36')
        req.add_header(
            'Accept-Encoding', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')
        # req.add_header('Accept-Encoding', 'utf-8')
        return req

    def movie_trans(self, uuid, videotype):
        url = 'http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/uuid=' + \
            uuid + '/fmt=' + videotype + '/output=json/'
        if videotype == 'progressive':
            url = 'http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fun=abstract/uuid=' + \
                uuid + '/fmt=' + videotype + '/output=json/'
        req = self.__set_request_headers(url)
        response = urlopen(req)
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        if json_data['meta']['nr_of_videos_total'] == 0:
            return ''
        movie = json_data['meta']['videohost'] + \
            json_data['material'][0]['videopath']
        #referer en user-agent als header meesturen (anders werkt het niet meer)
        return movie + '|Referer='+movie+'&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'

    def get_items(self, url, alles, videotype):
        items = self.__items(url, alles, videotype)
        if (alles):
            return items
        return [item for item in items if self.__is_uitzending(item)]
