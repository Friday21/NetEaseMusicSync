#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import os
import base64
import subprocess
import eyed3
from Crypto.Cipher import AES

class NemAPI:
#    用途：本API用于和网易云音乐进行通信
#    方法：get_info_from_nem()是通用方法
#        get_play_list() get_play_list_info() get_music_url() 则是具体实现 

    #   _aes_encrypt() _rsa_encrypt() _create_secret_key()
    #   这三个函数是用于加密传递给网易云音乐的参数的
    #   网易云音乐更新后，把get的参数加密后用post方法传递
    def _aes_encrypt(self,text, sec_key):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(sec_key, 2, '0102030405060708')
        cipher_text = encryptor.encrypt(text)
        cipher_text = base64.b64encode(cipher_text)
        return cipher_text

    def _rsa_encrypt(self,text, pub_key, modulus):
        text = text[::-1]
        rs = int(text.encode('hex'), 16)**int(pub_key, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)

    def _create_secret_key(self,size):
        return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]
    #   以上三个为加密函数


    def get_info_from_nem(self,url,params):
    #   用途：用于和网易云音乐进行通讯，并返回通讯后的json
    #   参数：url str 网易云音乐api的url，params dict {key:value} 就是把之前的url?a=b&c=d转换为{a:d,c:d}
    #   返回：dict api返回的json decode后作为返回值返回

        headers = {
            'Cookie': 'appver=1.5.0.75771;',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
        }
        modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        nonce = '0CoJUm6Qyw8W8jud'
        pub_key = '010001'
        params = json.dumps(params)
        sec_key = self._create_secret_key(16)
        enc_text = self._aes_encrypt(self._aes_encrypt(params, nonce), sec_key)
        enc_sec_key = self._rsa_encrypt(sec_key, pub_key, modulus)
        data = {
            'params': enc_text,
            'encSecKey': enc_sec_key
        }
        req = requests.post(url, headers=headers, data=data)
        return req.json()

    def get_play_list(self,uid):
    #   用途：获取指定用户的所有播放列表，包括创建的和收藏的列表，
    #         可以通过‘userId’是否等于当前user_id来判定是否为用户自己创建的列表
    #   参数：uid str|int 网易云音乐用户的uid
    #   返回：dict api返回的json decode后作为返回值返回

        url = 'http://music.163.com/weapi/user/playlist?csrf_token='
        params = {
            'offset': '0',
            'limit': '9999',
            'uid': str(uid)
        }
        return self.get_info_from_nem(url,params)
        
    def get_play_list_info(self,music_list_id):
    #   用途：获取指定播放列表的所有歌曲
    #   参数：music_list_id str|int 要获取的播放列表的id
    #   返回：dict api返回的json decode后作为返回值返回

        url = 'http://music.163.com/weapi/playlist/detail?csrf_token='
        params = {'id': str(music_list_id)}
        return self.get_info_from_nem(url,params)
        
    def get_music_url(self,music_id):
    #   用途：获取指定歌曲的url下载链接，不过有时间限制，大概5-10分钟后失效
    #   参数：music_id str|int 要获取下载链接的歌曲id
    #   返回：dict api返回的json decode后作为返回值返回

        url = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='
        if type([]) != type(music_id):
            music_id = [music_id]
        params = {
            "ids": str(music_id),
            "br": '320000'
        }
        return self.get_info_from_nem(url,params)


class NemAutoDownloader:
#    用途：把我收藏的音乐自动同步到计算机指定目录
#    变量：user_id str 用户id; music_dir str 本地文件夹目录
#    流程：
#        1.获取网络数据，生成云端列表[[mane,url],...]
#        2.获取本地数据，生成本地列表[name,...]
#        3.对比生成最终下载列表[[mane,url],...]
#        4.下载
#        5.整理
#    依赖：os, subprocess, eyed3

    user_id = '126887679' #我的用户ID
    music_dir = '/home/gaoyuan/Music'
    nem_api = NemAPI()
    
    def __init__(self,userid='',music_dir=''):
        if not userid == '':
            self.userid = userid
        if not music_dir == '':
            self.music_dir = music_dir

    def get_play_list(self,user_id):
    #   用途：获取指定用户（user_id）创建的播放列表，不含收藏的
    #   参数：user_id str/int
    #   返回：list [list_id,list_id,...] 

        play_list_id = []
        json = self.nem_api.get_play_list(user_id)
        for play_list in json['playlist']:
            if play_list['userId'] == int(user_id):
                play_list_id.append(play_list['id'])
        return play_list_id
        
    def get_song_list(self,play_list):
    #   用途：获取指定播放列表（play_list）中的歌曲
    #   参数：play_list list [list_id,list_id,...]
    #   返回：list [{name:XX,id:XX,singer:XX},{...},...]

        song_list = []
        for play_list_id in play_list:
            json = self.nem_api.get_play_list_info(play_list_id)['result']['tracks']
            for track in json:
                singers = []
                for singer in track['artists']:
                    singers.append(singer['name'])
                song_list.append({'name':track['name'],'id':track['id'],'singer':'&'.join(singers)})
        return song_list
        
    # -2-
    def get_local_song_list(self): 
    #   用途：获取本地（music_dir）歌曲列表
    #   参数：music_dir str 本地目录
    #   返回：list [song1,song2,...]

        local_song_list = []
        for lists in os.listdir(self.music_dir): 
            path = os.path.join(self.music_dir, lists) 
            if not os.path.isdir(path): 
                local_song_list.append(lists.split(".")[0])
        return local_song_list
        
    # -3-
    def get_download_list(self,local_music_list,song_list):
    #   用途：使用网络列表（song_list）减去本地列表（local_music_list）以确定要下载的列表
    #   参数：song_list list; local_music_list list
    #   返回：list [song1,song2,...]

        download_list = []
        for song_id in song_list:
            if not str(song_id['id']) in local_music_list:
                download_list.append(song_id)
        return download_list
        
    def get_song_url_list(self,song_list):
    #   用途：将歌曲id转换为下载链接，注意下载链接有时间限制，约为5～10分钟
    #   参数：song_list list
    #   返回：list [{id:XX,url:XX},{...},...]

        song_id_list = []
        song_url_list = []
        for song in song_list:
            song_id_list.append(song['id'])
        json = self.nem_api.get_music_url(song_id_list)['data']
        for track in json:
            song_url_list.append({'id':track['id'],'url':track['url']})
        return song_url_list
            
    # -4-
    def download_music(self,download_list):
    #   用途：下载音乐到指定目录（music_dir）
    #   参数：download_list list [{id:XX,url:XX},{...},...]
    #   返回：int 错误数量 0为没有错误

        i = 0
        errors = 0
        total = len(download_list)
        for song in download_list:
            i = i + 1
            print '    @+++>Downloading %s of %s...'%(str(i),str(total))
            if not song['url'] == None:
                song_name = self.music_dir+'/'+str(song['id'])+song['url'][-4:]
                state = subprocess.call('wget -O %s %s'%(song_name,song['url']),shell=True)
                if not state == 0:
                    errors = errors + 1
                    print '    @--->%Cannot download [%s] because of ...somgthing,delete broken music file'%(state,str(song['name']))
                    os.unlink(song_name)
                    pass #此处应有‘下载失败的log’
            else:
                print '    @--->Cannot download [%s] because of copyright'%(str(song['id']))
                pass #此处应有‘此歌曲由于版权原因无法下载的log’
        return errors
        
    # -5-
    def change_mp3_tag(self,song_list):
    #   用途：修改下载的mp3文件的Tag
    #   参数：song_list list [{id:XX,name:XX,singer:XX},{...},...]
    #   返回：boole 是否成功完成所有操作

        for song in song_list:
            mp3 = self.music_dir+'/'+str(song['id'])+'.mp3'
            if os.path.exists(mp3):
                try:
                    audiofile = eyed3.load(mp3)
                    audiofile.initTag()
                    audiofile.tag.title = song['name']
                    audiofile.tag.artist = song['singer']
                    audiofile.tag.save()
                    del audiofile
                    print mp3,'<==>',song['name'],'<==>',song['singer']
                except:
                    print '@--->An error occured while change the tag.Please re-run as fix mode(fix=True)'
                    return False
        return True

    def auto_download(self,fix_mode=False):
    #   用途：主程序，自动下载收藏的歌曲
    #   参数：
    #   返回： 

    #1
        print '@+++>stage 1 =>getting online list'
        play_list = self.get_play_list(self.user_id)
        song_list = self.get_song_list(play_list)
        print '@--->stage 1 =>have %s list(s) and %s song(s) online'%(str(len(play_list)),str(len(song_list)))
    #2
        print '@+++>stage 2 =>getting local list'
        local_music_list = self.get_local_song_list()
        print '@--->stage 2 =>have %s song(s) at local'%(str(len(local_music_list)))
    #3
        print '@+++>stage 3 =>making download list'
        song_to_down_list = self.get_download_list(local_music_list,song_list)
        download_list = self.get_song_url_list(song_to_down_list)
        print '@--->stage 3 =>have %s song(s) to download'%(str(len(download_list)))
    #4    
        print '@+++>stage 4 =>starting download'
        errors = self.download_music(download_list)
        if errors == 0:
            print '@--->stage 4 =>finished download,no error'        
        else:
            print '@--->stage 4 =>finished download, found %s errors,please re-run this script'%(errors)
     #5
        print '@+++>stage 5 =>write song title to mp3 tag'
        if fix_mode:
            self.change_mp3_tag(song_list)
        else:
            self.change_mp3_tag(song_to_down_list)
        print '@--->stage 5 =>ALL DONE !'       










if __name__=="__main__":
    nem_auto_downloader = NemAutoDownloader()
    nem_auto_downloader.auto_download()






