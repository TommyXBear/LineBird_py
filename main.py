# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 19:29:56 2023

@author: Tommy
"""
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from deta import Deta


#========Auths=========#
LineAccessToken='/hVA+VSB0ufCSCMFq6UGnjAef17MnHKjAAS5a7WWVzuYuVu0tiBhtGnQ2eodiYOnM+nZ2d2yWvEv8tvsNDiY2Fc3B1Eim8x+zrqvAWnFpUwbnyGqe7TTNzeMyzU/FbTxbVFGckqWRLJGiAgKNXb2pAdB04t89/1O/w1cDnyilFU='
LineChannelSecret='da38851eed14106fa4ec8efc7aa1ba9f'
deta = Deta("c08kbe7r_9KdvnQdiTrfaZbTPUAcuogRL8PZhQayX")

#=======Declares=======#
User=deta.Base("Users")
#=======Defines=======#
def FindKeys(UID):#如果Key不在資料庫回傳0,如果有的話回傳dict
    FetchRes=User.fetch()
    temp=[item for item in FetchRes.items if item["key"]==UID]
    if len(temp)==0:
        User.insert({'Hints':list(),'imgURL':list()},UID)
        return [{'Hints': list(), 'imgURL': list(), 'key': '%s'%UID}]
    else:
        return temp
def appendhints(H,U,UID,mes_t):
    mes_t[0]['Hints'].append(str(H));Hints=mes_t[0]['Hints']
    mes_t[0]['imgURL'].append(str(U));URLs=mes_t[0]['imgURL']
    User.update({'Hints':Hints,'imgURL':URLs}, UID)
def decoder(Text):
    temp=Text.split(' ')
    H=temp[1]
    U=temp[2]
    return H,U
def texthandlecat(mes_temp,Text_incoming):
    try:
        ind=[i for i in range(0,len(mes_temp[0]['Hints'])) if mes_temp[0]['Hints'][i] in Text_incoming][0]
    except:
        return 0
    return mes_temp[0]['imgURL'][ind]   
def listall(mes_temp):
    temp=[str(i)+'. %s'%mes_temp[0]['Hints'][i-1] for i in range(1,len(mes_temp[0]['Hints'])+1)]
    return '\n'.join(temp)+'\n(以上編號由建立時間舊到新排序<數字越大越新>)\n若要刪除請用指令: /del 編號'
def delind(del_ind,mes_temp,UID):
    temp=mes_temp[0]['Hints'][del_ind-1]
    mes_temp[0]['Hints'].pop(del_ind-1)
    mes_temp[0]['imgURL'].pop(del_ind-1)
    User.update({'Hints':mes_temp[0]['Hints'],'imgURL':mes_temp[0]['imgURL']}, UID)
    return '%s. %s has been deleted from user database'%(del_ind,temp)
#====App Main======#
app = FastAPI()  # notice that the app instance is called `app`, this is very important.
line_bot_api = LineBotApi(LineAccessToken)
handler = WebhookHandler(LineChannelSecret)
@app.post("/")
async def Main_Event(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
        
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameters")
    return "Process Done"
#======Handler=====#
@handler.add(MessageEvent, message=(TextMessage))
def handling_message(event):
    UINFO= str(event.source)
    UID=UINFO.split()[-1][1:-2]

    if isinstance(event.message, TextMessage):
        mes_temp=FindKeys(UID)
        Text_incoming =event.message.text
        if Text_incoming[0]=='/':#如果是指令
            if Text_incoming[1:5]=='reg ':#登陸圖片
                try:
                    H,U=decoder(Text_incoming)
                    appendhints(H,U,UID,mes_temp)
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text='reg done'))
                except:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text='Failed, pls找銘仁'))
            elif Text_incoming[1:5]=='list':#List 使用者圖片
                lsal=listall(mes_temp)
                try:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=lsal))
                except:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text='Failed, pls找銘仁'))
            elif Text_incoming[1:5]=='del ':
                try:
                    del_ind=int(Text_incoming.split()[1])
                    del_mes=delind(del_ind,mes_temp,UID)
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=del_mes))
                except:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text='Failed, pls找銘仁'))
            else:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=\
                            '指令集:\n/reg 關鍵字 圖片網址 =>登陸關鍵字\n/list=>顯示使用者目前圖片編號\n/del 編號 =>刪除該編號關鍵字'))
        else:#不是指令(使用程序)
            img_url=texthandlecat(mes_temp, Text_incoming)
            if img_url ==0:
                return
            else:
                line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
        
    else:
        return
    
    return

