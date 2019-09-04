'''
    RTLxl
    ~~~~~

    An XBMC addon for watching RTLxl    
'''
import resources.lib.rtlxl
import sys
if (sys.version_info[0] == 3):
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
    import storageserverdummy as StorageServer  
else:
    # Fall back to Python 2's urllib2
    from urllib import urlencode
    from urlparse import parse_qsl
    try:
        import StorageServer
    except:
        import storageserverdummy as StorageServer

import time
import xbmcplugin, xbmcgui, xbmcaddon

PLUGIN_NAME = 'RTL XL'
PLUGIN_ID = 'plugin.video.rtlxl'

rtlxl = resources.lib.rtlxl.RtlXL()

_url = sys.argv[0]
_handle = int(sys.argv[1])
_cache = StorageServer.StorageServer(PLUGIN_ID, 24) # (Your plugin name, Cache time in hours)
_addon = xbmcaddon.Addon()

# het in elkaar klussen van een url welke weer gebruikt word bij router
def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def setMediaView():
    # juiste skin selecteren alleen voor confluence maar die gebruikik prive nog steeds
    try:
        kodiVersion = xbmc.getInfoLabel('System.BuildVersion').split()[0]
        kodiVersion = kodiVersion.split('.')[0]
        skinTheme = xbmc.getSkinDir().lower()
        if 'onfluence' in skinTheme:
            xbmc.executebuiltin('Container.SetViewMode(504)')
    except:
        pass 

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'keuze':
            show_keuze(params['url'])
            #xbmc.log('url: ' + params['url'], xbmc.LOGERROR)
        elif params['action'] == 'alles':
            show_alles(params['url'])
            #xbmc.log('url: ' + params['url'], xbmc.LOGERROR)
            setMediaView()
        elif params['action'] == 'afleveringen':
            show_afleveringen(params['url'])
            setMediaView()
        elif params['action'] == 'play':
            play_video(params['path'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_overzicht()
        setMediaView()

def list_overzicht():
    xbmcplugin.setPluginCategory(_handle, 'Lijst')
    xbmcplugin.setContent(_handle, 'videos')
    overzicht = _cache.cacheFunction(rtlxl.get_overzicht)
    # Alle mogelijke "begin" "letters"
    for item in overzicht:
        list_item = xbmcgui.ListItem(label=item['label'])
        list_item.setArt(item['art'])
        list_item.setInfo('video', item['video'])
        url = get_url(action='keuze', url=item['url'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def show_keuze(url):
    xbmcplugin.setPluginCategory(_handle, 'Keuze')
    #enable media info viewtype zodat "plot" van een aflevering ook getoond kan worden (indien gewenst)
    xbmcplugin.setContent(_handle, 'videos')
    ##keuze tussel alles of alleen afleveringen (wel fijn bij RTL Nieuws)
    for item in rtlxl.get_categories(url):
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setInfo('video', {
                                'title': item['title'],
                                'mediatype': 'video' })
        url = get_url(action=item['keuze'], url=item['url'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def show_afleveringen(url):
    ##alleen afleveringen weergeven
    videotype = get_videotype(xbmcplugin.getSetting(_handle, "videotype"))
    return show_items(rtlxl.get_items(url, False, videotype), 'Afleveringen')

def show_alles(url):    
    ##alles weergeven
    videotype = get_videotype(xbmcplugin.getSetting(_handle, "videotype"))
    return show_items(rtlxl.get_items(url, True, videotype), 'Alles')

def get_videotype(switchnum):
    if switchnum == '0':
        return 'adaptive'
    if switchnum == '1':
        return 'progressive'
    if switchnum == '2':
        return 'smooth'
    return 'adaptive'

def show_items(opgehaaldeitemsclass, category):
    xbmcplugin.setPluginCategory(_handle, category)
    #enable media info viewtype zodat "plot" van een aflevering ook getoond kan worden (indien gewenst)
    xbmcplugin.setContent(_handle, 'videos')
    ##keuze tussel alles of alleen afleveringen (wel fijn bij RTL Nieuws)
    for item in opgehaaldeitemsclass:
        list_item = xbmcgui.ListItem(label=item['label'])
        list_item.setArt(item['art'])
        list_item.setInfo('video', item['video'])
        list_item.setProperty('IsPlayable', 'true')
        pathparameter = item['path']
        url = get_url(action='play', path=pathparameter)
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

if __name__ == '__main__':
    router(sys.argv[2][1:])