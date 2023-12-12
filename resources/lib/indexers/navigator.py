# -*- coding: utf-8 -*-

'''
    PPCRN Addon
    Copyright (C) 2023 heg, vargalex

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, locale, base64
from bs4 import BeautifulSoup
import requests
import urllib.parse
import resolveurl as urlresolver
from resources.lib.modules.utils import py2_decode, py2_encode
import html

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

import platform
import xml.etree.ElementTree as ET

os_info = platform.platform()
kodi_version = xbmc.getInfoLabel('System.BuildVersion')

current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(current_directory)))
addon_xml_path = os.path.join(parent_directory, "addon.xml")

tree = ET.parse(addon_xml_path)
root = tree.getroot()
version = root.attrib.get("version")

xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info}', xbmc.LOGINFO)

base_url = 'https://ppcrn.eu'

headers = {
    'authority': 'ppcrn.eu',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        self.addDirectoryItem("Sorozatok", "only_series", '', 'DefaultFolder.png')
        self.addDirectoryItem("Kategóriák", "categories", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", "search", '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self):
        page = requests.get(f"{base_url}/index.php", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        category_div = soup.find('div', class_='header__dropdown-menu-inside')
        category_links = category_div.find_all('a')

        for link in category_links:
            category_link = link['href']
            category_link = f'{base_url}{category_link}'
            category_name = link.find('div').text
            
            enc_link = urllib.parse.quote(category_link, safe=':/')
            
            self.addDirectoryItem(f"{category_name}", f'series_items&url={enc_link}', '', 'DefaultFolder.png')

        self.endDirectory()

    def getSeriesItems(self, url, img_url, hun_title, content, card_rate):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        movies = soup.find_all('a', class_='card__play')
        
        for movie in movies:
            link = movie['href']
            series_card_link = f'{base_url}{link}'
            
            hun_title = movie['title']
            img = movie.find('img')['style'].split("'")[1]
            img_url = f'{base_url}{img}'
        
            card_rate_element = movie.find('div', class_='card__rate')
            card_rate = card_rate_element.text.strip() if card_rate_element else 'N/A'
        
            if card_rate != 'N/A':
                self.addDirectoryItem(f'[B]{hun_title} | [COLOR yellow]{card_rate}[/COLOR][/B]', f'extract_series&url={series_card_link}&img_url={img_url}&hun_title={hun_title}&content={content}&card_rate={card_rate}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            next_page_link = soup.find('div', class_='paginator__item--next').parent['href']
            next_page_url = f'{base_url}{next_page_link}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getSeriesItems | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def extractSeriesItems(self, url, img_url, hun_title, content, card_rate):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        content = soup.find('div', class_='card__description_in').text.strip()
        seasons_container = soup.find('div', class_='f100mb30')
        season_links = seasons_container.find_all('a')
        
        season_data = []
        
        for season_link in season_links:
            evad_title = season_link['title']
            evad_link = 'https://ppcrn.eu' + season_link['href']

            self.addDirectoryItem(f'[B] {evad_title} | [COLOR yellow]{card_rate}[/COLOR][/B]', f'extract_episodes&url={evad_link}&img_url={img_url}&hun_title={hun_title}&content={content}&card_rate={card_rate}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
    
        self.endDirectory('movies')

    def getSeasonProviders(self, url, img_url, hun_title, content, ep_title):
        import base64
        import requests
        import re
        
        html_soup_2 = requests.get(url, headers=headers)
        soup_2 = BeautifulSoup(html_soup_2.text, 'html.parser')

        card_description_div = soup_2.find('div', class_='card__description').find('div', class_='card__description_in')
        content = card_description_div.get_text(strip=True)
        
        link = re.findall(r'href=\"(.*?)\"\s.*\s.*[lL]inkek [mM]egtekintése', str(soup_2))[0].strip()
        link = re.sub(r'amp;', r'', link)
        
        link_3 = f'{base_url}{link}'
        
        import requests
        
        response_3 = requests.get(link_3, headers=headers)
        soup_3 = BeautifulSoup(response_3.text, 'html.parser')
        
        try:
            table = soup_3.find('table', attrs={'align': 'center'})
            
            all_data = []
            
            def extract_data(main_title, rows):
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) == 3:
                        quality = columns[0].get_text(strip=True)
                        channel = columns[1].get_text(strip=True)
                        link_element = columns[2].find('a')
                        if link_element:
                            link = link_element['href']
            
                            if re.search(r"url=(.*)&m", link):
                                decoded_url = None
                                base64_part = link.split('url=')[1].split('&m=')[0]
                                decoded_url = base64.b64decode(base64_part).decode('utf-8')
                                all_data.append({'main_title': main_title, 'quality': quality, 'channel': channel, 'decoded_url': decoded_url})
            
            magyar_szinkron_header = table.find('th', string='MAGYAR SZINKRON')
            if magyar_szinkron_header:
                magyar_szinkron_rows = magyar_szinkron_header.find_next('tr').find_all_next('tr')
                extract_data('MAGYAR SZINKRON', magyar_szinkron_rows)
            
            magyar_felirat_header = table.find('th', string='MAGYAR FELIRAT')
            if magyar_felirat_header:
                magyar_felirat_rows = magyar_felirat_header.find_next('tr').find_all_next('tr')
                extract_data('MAGYAR FELIRAT', magyar_felirat_rows)
            
            egyeb_header = table.find('th', string='EGYÉB')
            if egyeb_header:
                egyeb_rows = egyeb_header.find_next('tr').find_all_next('tr')
                extract_data('EGYÉB', egyeb_rows)
            
            for entry in all_data:
            
                extr_main_title = entry['main_title']
                if extr_main_title == 'MAGYAR SZINKRON':
                    extr_main_title = 'Szinkronos'
                if extr_main_title == 'MAGYAR FELIRAT':
                    extr_main_title = 'Feliratos'                    

                extr_quality = entry['quality']
                extr_channel = entry['channel']
                extr_decoded_url = entry['decoded_url']
                
                ep_title = re.sub(r'None', r'', str(ep_title))

                self.addDirectoryItem(f'[B][COLOR lightblue]{extr_quality}[/COLOR] | [COLOR orange]{extr_main_title}[/COLOR] | [COLOR red]{extr_channel}[/COLOR] | {ep_title} - {hun_title}[/B]', f'playmovie&url={extr_decoded_url}&img_url={img_url}&hun_title={hun_title}&content={content}&ep_title={ep_title}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': ep_title, 'plot': content})
        
        
        except (UnboundLocalError, AttributeError):
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getSeasonProviders | name: No video sources found', xbmc.LOGINFO)
            notification = xbmcgui.Dialog()
            notification.notification("PPCRN", "Törölt tartalom", time=5000)                
        
        self.endDirectory('series')

    def getOnlySeries(self):
        page = requests.get(f"{base_url}/index.php/uj-sorozatok", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        container = soup.find('div', class_='container_tab')
        cards = container.find_all('a', class_='card__play')
        
        for card in cards:
            link = card.get('href', 'N/A')
            card_link = f'{base_url}{link}'
        
            img = card.find('img')['style'].split("url('")[1].split("')")[0] if card.find('img') else 'N/A'
            img_url = f'{base_url}{img}'
        
            card_rate_element = card.find_next('div', class_='card__rate')
            card_rate = card_rate_element.text.strip() if card_rate_element else 'N/A'
        
            title_element = card.find_previous('h3', class_='card__title')
            title_before_play = title_element.text.strip() if title_element else 'N/A'
            hun_title = card['title']
            
            self.addDirectoryItem(f'[B]{hun_title} | [COLOR yellow]{card_rate}[/COLOR][/B]', f'extract_episodes&url={card_link}&img_url={img_url}&hun_title={hun_title}&card_rate={card_rate}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title})
        
        try:
            next_page_link = soup.find('div', class_='paginator__item--next').parent['href']
            next_page_url = f'{base_url}{next_page_link}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'season_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlySeries | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')      

    def extractEpisodes(self, url, img_url, hun_title, content, ep_title):
        soup_2 = requests.get(url, headers=headers)
        soup2 = BeautifulSoup(soup_2.text, 'html.parser')

        card_description_div = soup2.find('div', class_='card__description').find('div', class_='card__description_in')
        content = card_description_div.get_text(strip=True)        
        
        import re
        cut_url = re.findall(r'/evad/(.*)', url)[0].strip()
        
        html = requests.get(f'{base_url}/js/episodes.php?season_url={cut_url}', headers=headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        
        episodes = soup.find_all('a')
        
        for episode in episodes:
            episode_title = episode['title']
            episode_link = episode['href']
            
            ep_link = f'{base_url}{episode_link}'
            ep_title = f'{episode_title} - {hun_title}'

            self.addDirectoryItem(f'[B]{episode_title} - {hun_title}[/B]', f'get_season_providers&url={quote_plus(ep_link)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': ep_title, 'plot': content})

        self.endDirectory('series')

    def getSeasonItems(self, url, img_url, hun_title, content, card_rate):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        container = soup.find('div', class_='container_tab')
        
        cards = container.find_all('a', class_='card__play')
        
        for card in cards:
            link = card.get('href', 'N/A')
            card_link = f'{base_url}{link}'
        
            img = card.find('img')['style'].split("url('")[1].split("')")[0] if card.find('img') else 'N/A'
            img_url = f'{base_url}{img}'
        
            card_rate_element = card.find_next('div', class_='card__rate')
            card_rate = card_rate_element.text.strip() if card_rate_element else 'N/A'
        
            title_element = card.find_previous('h3', class_='card__title')
            title_before_play = title_element.text.strip() if title_element else 'N/A'
            hun_title = card['title']
            
            self.addDirectoryItem(f'[B]{hun_title} | [COLOR yellow]{card_rate}[/COLOR][/B]', f'extract_episodes&url={card_link}&img_url={img_url}&hun_title={hun_title}&content={content}&card_rate={card_rate}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            next_page_link = soup.find('div', class_='paginator__item--next').parent['href']
            next_page_url = f'{base_url}{next_page_link}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'season_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlySeries | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def playMovie(self, url):
        try:
            direct_url = urlresolver.resolve(url)
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | playMovie | direct_url: {direct_url}', xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=direct_url)
            if 'm3u8' in direct_url:
                from inputstreamhelper import Helper
                is_helper = Helper('hls')
                if is_helper.check_inputstream():
                    play_item.setProperty('inputstream', 'inputstream.adaptive')  # compatible with recent builds Kodi 19 API
                    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
        except:
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | playMovie | name: No video sources found', xbmc.LOGINFO)
            notification = xbmcgui.Dialog()
            notification.notification("PPCRN", "Törölt tartalom", time=5000)

    def extrSearches(self, url, img_url, hun_title):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        card_play_links = soup.find_all('a', class_='card__play')
        
        for link in card_play_links:
            hun_title = link['title']
            
            img_url = base_url + link.find('img')['style'].split("'")[1]
            link_url = base_url + link['href']
            
            self.addDirectoryItem(f'[B]{hun_title}[/B]', f'get_season_providers&url={link_url}&img_url={img_url}&hun_title={hun_title}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title})
        
        try:
            next_page_link = soup.find('div', class_='paginator__item--next').parent['href']
            next_page_url = f'{base_url}{next_page_link}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'extr_search&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'PPCRN | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlySeries | next_page_url | csak egy oldal található', xbmc.LOGINFO)        
        
        
        self.endDirectory('movies')
    
    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                url_p = f"{base_url}/index.php/kereses/{item}"
                
                self.addDirectoryItem(item, f'extr_search&url={url_p}', '', 'DefaultFolder.png')

            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write(f"{search_text}\n")
            file.close()
            url_x = f"{base_url}/index.php/kereses/{search_text}"

            self.extrSearches(url_x, 1, 1)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)