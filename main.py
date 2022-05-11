import StellarPlayer
import time
import bs4
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re
import urllib.parse
import urllib.request
import math
import json
import urllib3

mainurl = 'https://www.bugutv.cn'

class bgtvplugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.mainmenu = []
        self.medias = []
        self.maxpage = 0
        self.curpage = 0
        self.acturl = ''
        self.cur_page = ''
        self.firstpage = ''
        self.previouspage = ''
        self.nextpage = ''
        self.lastpage = ''
        self.searchword = ''
        self.xls = []
        self.allmovidesdata = {}
        urllib3.disable_warnings()
    
    def getPageNumber(self,bs):
        selector = bs.select('#rizhuti_v2_module_lastpost_item-2 > div > div.module.posts-wrapper.grid > div.pagination.justify-content-center > span')
        if len(selector) > 0:
            pagetext = selector[0].getText()
            splits = re.split(r'/+',pagetext)
            self.cur_page = '第' + pagetext + '页'
            self.maxpage = int(splits[1])
            self.curpage = int(splits[0])
            return
        selector = bs.select('#main > div.archive.container > div.row > div > div > div.pagination.justify-content-center > span')
        if len(selector) > 0:
            pagetext = selector[0].getText()
            splits = re.split(r'/+',pagetext)
            self.cur_page = '第' + pagetext + '页'
            self.maxpage = int(splits[1])
            self.curpage = int(splits[0])
            return
        self.cur_page = '第1页'
        self.maxpage = 1
        self.curpage = 1
    
    def getMedias(self,bs):
        self.medias = []
        selector = bs.select('#main > div.archive.container > div.row > div > div > div.row.posts-wrapper.scroll > div')
        if len(selector) == 0:
            selector = bs.select('#rizhuti_v2_module_lastpost_item-2 > div > div.module.posts-wrapper.grid > div.row.posts-wrapper.scroll > div')
        if len(selector) > 0:
            for item in selector:
                article = item.select('article')[0]
                movie = article.select('div.entry-media > div > a')[0]
                movieimg = movie.select('img')[0].get('data-src')
                self.medias.append({'title':movie.get('title'),'url':movie.get('href'),'picture':movieimg})
        self.player.updateControlValue('main','mediagrid',self.medias)
                    
    def start(self):
        super().start()
        self.mainmenu = []
        self.acturl = mainurl
        res = requests.get(mainurl,verify=False)
        if res.status_code == 200:
            bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
            selector1 = bs.select('#menu-\%e8\%8f\%9c\%e5\%8d\%95 > li')
            if (selector1):
                for li in selector1:
                    info = li.select('a')[0]
                    self.mainmenu.append({'title':info.getText(),'url':info.get('href')})
            self.getMedias(bs)
            self.getPageNumber(bs)
        
    
    def show(self):
        controls = self.makeLayout()
        self.doModal('main',800,600,'',controls)
    
    def makeLayout(self):
       
        mainmenu_layout = [
            {'type':'link','name':'title','@click':'onMainMenuClick'}
        ]

        mediagrid_layout = [
            [
                {
                    'group': [
                        {'type':'image','name':'picture', '@click':'on_grid_click'},
                        {'type':'label','name':'title','textColor':'#ff7f00','fontSize':15,'height':40, '@click':'on_grid_click'}
                    ],
                    'dir':'vertical'
                }
            ]
        ]
        controls = [
            {'type':'space','height':5},
            {
                'group':[
                    {'type':'edit','name':'search_edit','label':'搜索','width':0.4},
                    {'type':'button','name':'搜索','@click':'onSearch','width':80}
                ],
                'width':1.0,
                'height':30
            },
            {'type':'space','height':10},
            {'type':'grid','name':'menugrid','itemlayout':mainmenu_layout,'value':self.mainmenu,'itemheight':30,'itemwidth':75,'height':30},
            {'type':'grid','name':'mediagrid','itemlayout':mediagrid_layout,'value':self.medias,'separator':True,'itemheight':220,'itemwidth':127},
            {'group':
                [
                    {'type':'space'},
                    {'group':
                        [
                            {'type':'label','name':'cur_page',':value':'cur_page'},
                            {'type':'link','name':'首页','@click':'onClickFirstPage'},
                            {'type':'link','name':'上一页','@click':'onClickFormerPage'},
                            {'type':'link','name':'下一页','@click':'onClickNextPage'},
                            {'type':'link','name':'末页','@click':'onClickLastPage'},
                        ]
                        ,'width':0.45
                    },
                    {'type':'space'}
                ]
                ,'height':30
            },
            {'type':'space','height':5}
        ]
        return controls
    
    def onSearch(self, *args):
        self.loading()
        self.searchword = self.player.getControlValue('main','search_edit')
        if len(self.searchword) > 0:
            searchurl = mainurl + '/?cat=&s=' + self.searchword
            print(searchurl)
            self.onloadpage(searchurl)
        self.loading(True)
    
    def onMainMenuClick(self, page, listControl, item, itemControl):
        self.loading()
        self.firstpage = ''
        self.previouspage = ''
        self.nextpage = ''
        self.lastpage = ''
        self.cur_page = ''
        self.searchword = ''
        self.acturl = self.mainmenu[item]['url']
        self.onloadpage(self.acturl)
        self.loading(True)
    
    def onloadpage(self,pageurl):
        print(pageurl)
        res = requests.get(pageurl,verify=False)
        if res.status_code == 200:
            bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
            self.getMedias(bs)
            self.getPageNumber(bs)
        
    def on_grid_click(self, page, listControl, item, itemControl):
        self.loading()
        mediapageurl = self.medias[item]['url']
        medianame = self.medias[item]['title']
        postid = re.findall(r"www.bugutv.cn/(.+?).html", mediapageurl)
        if len(postid) != 1:
            return
        imgselectstr = '#post-' + postid[0] + ' > div > div.entry-wrapper > div.entry-content.u-text-format.u-clearfix > figure > img'
        infoselectstr = '#post-' + postid[0] + ' > div > div.entry-wrapper > div.entry-content.u-text-format.u-clearfix > p'
        res = requests.get(mediapageurl,verify=False)
        picurl = ''
        infostr = ''
        if res.status_code == 200:
            bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
            picselector = bs.select(imgselectstr)
            if picselector:
                picurl = picselector[0].get('src')
            infoselector = bs.select(infoselectstr)
            textinfo1 = ""
            textinfo2 = ""
            if len(infoselector) > 3:
                textinfo1 = infoselector[0].getText()
                textinfo2 = infoselector[1].getText() + '\n' + infoselector[2].getText()
                textinfo1 = textinfo1.replace('◎','\n')
                textinfo1 = textinfo1[1:]
            magnetarr = []
            for item in infoselector:
                btselector = item.select('a')
                if len(btselector) > 0:
                    if btselector[0].getText().find('magnet:') >= 0:
                        titlestr = item.getText()
                        magneturl = btselector[0].getText()
                        strend = titlestr.find(magneturl)
                        if strend >= 0:
                            titlestr = titlestr[:strend]
                        magnetarr.append({'title':titlestr,'url':magneturl})
            
            magnet_list_layout = {'type':'link','name':'title','@click':'on_magnet_click'}
            controls = [
                {'type':'space','height':5},
                {'group':[
                        {'type':'image','name':'mediapicture', 'value':picurl,'width':0.3},
                        {'type':'label','name':'info1','value':textinfo1,'width':0.7}
                    ],
                    'width':1.0,
                    'height':350
                },
                {'type':'space','height':5},
                {'type':'label','name':'info2','value':textinfo2,'height':180,'textColor':'#556B2F'},
                {'type':'label','name':'xzts','value':'下载地址：','height':20,'textColor':'#ff7f00'},
                {'group':
                    {'type':'grid','name':'magnetlist','itemlayout':magnet_list_layout,'value':magnetarr,'separator':True,'itemheight':30,'itemwidth':700},
                    'height':220
                }
            ]
            self.allmovidesdata[medianame] = magnetarr
            self.loading(True)
            result,control = self.player.doModal(medianame,1000,800,medianame,controls)
        else:
            self.player and self.player.toast('main','获取影片信息失败')
            self.loading(True)


        
    def onClickFirstPage(self, *args):
        if self.acturl == '':
            return
        pageurl = self.acturl
        if len(self.searchword) > 0 and self.acturl == mainurl:
            pageurl = pageurl + '/?cat=&s=' + self.searchword
        self.loading()
        self.onloadpage(pageurl)
        self.loading(True)
        
    def onClickFormerPage(self, *args):
        if self.acturl == '':
            return
        if self.curpage > 1:
            self.curpage = self.curpage - 1
            pageurl = self.acturl + '/page/' + str(self.curpage)
            if len(self.searchword) > 0 and self.acturl == mainurl:
                pageurl = pageurl + '/?cat=&s=' + self.searchword
            self.loading()
            self.onloadpage(pageurl)
            self.loading(True)
    
    def onClickNextPage(self, *args):
        if self.acturl == '':
            return 
        if self.curpage < self.maxpage:
            self.curpage = self.curpage + 1
            pageurl = self.acturl + '/page/' + str(self.curpage)
            if len(self.searchword) > 0 and self.acturl == mainurl:
                pageurl = pageurl + '?cat=&s=' + self.searchword
            self.loading()
            self.onloadpage(pageurl)
            self.loading(True)
        
    def onClickLastPage(self, *args):
        if self.acturl == '':
            return
        self.curpage = self.maxpage
        pageurl = self.acturl + '/page/' + str(self.curpage)
        if len(self.searchword) > 0 and self.acturl == mainurl:
            pageurl = pageurl + '/?cat=&s=' + self.searchword
        self.loading()
        self.onloadpage(pageurl)
        self.loading(True)
        
    def on_magnet_click(self, page, listControl, item, itemControl):
        if len(self.allmovidesdata[page]) > item:
            playurl = self.allmovidesdata[page][item]['url']
            self.player.download(playurl)   
            
    def loading(self, stopLoading = False):
        if hasattr(self.player,'loadingAnimation'):
            self.player.loadingAnimation('main', stop=stopLoading)

def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = bgtvplugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()