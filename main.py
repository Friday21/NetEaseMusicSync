#!/usr/bin/python
# -*- coding: utf-8 -*-

#流程：
#1.获取网络数据，生成云端列表[[mane,url],...]
#2.获取本地数据，生成本地列表[name,...]
#3.对比生成最终下载列表[[mane,url],...]
#4.下载
#5.整理
# -0-
import nemapi #1,3
import os #2,4
import subprocess #4
import eyed3

from pprint import pprint
userid = '126887679' #我的用户ID
musicdir = '/home/gaoyuan/Music'

# -1-
def getplaylist(userid):
    playlistid = []
    json = nemapi.getplaylist(userid)
    for playlist in json['playlist']:
        if playlist['userId'] == int(userid):
            playlistid.append(playlist['id'])
    return playlistid
    
def getsonglist(playlist):
    songlist = []
    for playlistid in playlist:
        json = nemapi.getplaylistinfo(playlistid)['result']['tracks']
        for track in json:
            singers = []
            for singer in track['artists']:
                singers.append(singer['name'])
            songlist.append({'name':track['name'],'id':track['id'],'singer':'&'.join(singers)})
    return songlist
    
# -2-
def getlocalsonglist(musicdir): 
    localsonglist = []
    for lists in os.listdir(musicdir): 
        path = os.path.join(musicdir, lists) 
        if not os.path.isdir(path): 
            localsonglist.append(lists.split(".")[0])
    return localsonglist
    
# -3-
def getdownloadlist(locallist,songlist):
    downloadlist = []
    for songid in songlist:
        if not str(songid['id']) in locallist:
            downloadlist.append(songid)
    return downloadlist
    
def getsongurllist(songlist):
    songidlist = []
    songurllist = []
    for song in songlist:
        songidlist.append(song['id'])
    json = nemapi.getmusicurl(songidlist)['data']
    for track in json:
        songurllist.append({'name':track['id'],'url':track['url']})
    return songurllist
        
# -4-
def download(downloadlist):
    i = 0
    errors = 0
    total = len(downloadlist)
    for song in downloadlist:
        i = i + 1
        print '    @+++>Downloading %s of %s...'%(str(i),str(total))
        if not song['url'] == None:
            songname = musicdir+'/'+str(song['name'])+song['url'][-4:]
            state = subprocess.call('wget -O %s %s'%(songname,song['url']),shell=True)
            if not state == 0:
                errors = errors + 1
                print '    @--->%Cannot download [%s] because of ...somgthing,delete broken music file'%(state,str(song['name']))
                os.unlink(songname)
                pass #此处应有‘下载失败的log’
        else:
            print '    @--->Cannot download [%s] because of copyright'%(str(song['name']))
            pass #此处应有‘此歌曲由于版权原因无法下载的log’
    return errors
    
# -5-
def changemp3tag(songlist):
    for song in songlist:
        mp3 = musicdir+'/'+str(song['id'])+'.mp3'
        if os.path.exists(mp3):
            audiofile = eyed3.load(mp3)
            audiofile.initTag()
            audiofile.tag.title = song['name']
            audiofile.tag.artist = song['singer']
            audiofile.tag.save()
            del audiofile
            print mp3,'<==>',song['name'],'<==>',song['singer']
    

# -main-
if __name__ == "__main__":
#1
    print '@+++>stage 1 =>getting online list'
    playlist = getplaylist(userid)
    songlist = getsonglist(playlist)
    print '@--->stage 1 =>have %s list(s) and %s song(s) online'%(str(len(playlist)),str(len(songlist)))
#2
    print '@+++>stage 2 =>getting local list'
    locallist = getlocalsonglist(musicdir)
    print '@--->stage 2 =>have %s song(s) at local'%(str(len(locallist)))
#3
    print '@+++>stage 3 =>making download list'
    songtodownlist = getdownloadlist(locallist,songlist)
    downloadlist = getsongurllist(songtodownlist)
    print '@--->stage 3 =>have %s song(s) to download'%(str(len(downloadlist)))
#4    
    print '@+++>stage 4 =>starting download'
    errors = download(downloadlist)
    if errors == 0:
        print '@--->stage 4 =>finished download,no error'        
    else:
        print '@--->stage 4 =>finished download, found %s errors,please re-run this script'%(errors)
 #5
    print '@+++>stage 5 =>write song title to mp3 tag'
    changemp3tag(songtodownlist)#如果要重新设置所有mp3的tag修改参数为songlist即可
    print '@--->stage 5 =>ALL DONE !'
    
    
    
    
    
    
    
    
    
