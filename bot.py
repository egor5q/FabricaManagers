# -*- coding: utf-8 -*-
import os
import telebot
import time
import random
import threading
from emoji import emojize
from telebot import types
from pymongo import MongoClient
import traceback


token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)


client=MongoClient(os.environ['database'])
db=client.fabricamanagers
users=db.users
world=db.world


try:
    pass

except Exception as e:
    print('Ошибка:\n', traceback.format_exc())
    bot.send_message(441399484, traceback.format_exc())

@bot.message_handler(commands=['start'])
def start(m):
    tutorial=0
    if m.from_user.id==m.chat.id:
        if users.find_one({'id':m.from_user.id})==None:
            users.insert_one(createuser(m.from_user))
            tutorial=1
        user=users.find_one({'id':m.from_user.id})
        if tutorial==1:
            bot.send_message(m.chat.id, 'Добывай ресурсы, строй механизмы на своей фабрике, шпионь, кради ресурсы у других!')
        mainmenu(user)
    

@bot.message_handler(commands=['world_addres'])
def addresourcestoworld(m):
    if m.from_user.id==441399484:
        try:
            resource=m.text.split(' ')[1]
            amount=int(m.text.split(' ')[2])
            try:
                world.update_one({},{'$inc':{resource:amount}})
            except:
                world.update_one({},{'$set':{resource:amount}})
            current=world.find_one({})[resource]
            bot.send_message(m.chat.id, 'Мировой ресурс "'+resource+'" увеличен на '+str(amount)+'! Текущее количество: '+str(current)+'.')
        except Exception as e:
            bot.send_message(441399484, traceback.format_exc())
    
    
@bot.message_handler()
def messages(m):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    if m.from_user.id==m.chat.id:
        try:
            user=users.find_one({'id':m.from_user.id})
            
            if m.text=='🏢Главное меню':
                mainmenu(m.from_user)
                
            if m.text=='❓Обо мне':
                bot.send_message(m.chat.id, aboutme(user))
                
            if m.text=='👷‍♂️Месторождения ресурсов':
                recource_fields(user)
                
            if m.text=='🛢Нефть':
                distance=user['distances']['oil']
                text='Из нефти делается топливо для любых видов техники. Ближайшее месторождение нефти находится в '+str(distance)+' км от вашей фабрики.\n'
                builds=False
                for ids in user['buildings']:
                    if user['buildings'][ids]['place']=='oil':
                        builds=True
                if builds==False:
                    text+='У вас здесь ещё нет строений.\n'
                
                text+='Ваши постройки здесь:\n'
                text+=buildingslist(user, 'oil')
                text+='\n'
                kb.add(types.KeyboardButton('⚒Стройка: нефть'))
                kb.add(types.KeyboardButton('🏢Главное меню'))
                bot.send_message(m.chat.id, text, reply_markup=kb)
                
            if m.text=='⚒Стройка: нефть':
                buildmenu(user, 'oil')
    
    
@bot.callback_query_handler(func=lambda call:True)
def inline(call):
    user=users.find_one({'id':call.from_user.id})
    kb=types.InlineKeyboardMarkup()
    if 'info' in call.data:
        if 'stock' in call.data:
            text=buildinginfo('stock')
            kb.add(types.InlineKeyboardButton(text='🔨Построить', callback_data='build stock '+call.data.split(' ')[2]))
            kb.add(types.InlineKeyboardButton(text='Закрыть меню', callback_data='close'))
            medit(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
            
    if 'build' in call.data:
        if 'stock' in call.data:
            resources={}
            place=call.data.split(' ')[2]
            resources.update(addres('wood', 100000))
            resources.update(addres('iron', 40000))
            nores=Faslse
            try:
                for ids in resources:
                    if user['resources'][ids]<resources[ids]:
                        nores=True
            except:
                nores=True
                
            if nores==False:
                b=build(stock, user, place, False, time=360) 
                for ids in resources:
                    users.update_one({'id':user['id']},{'$inc':{'resources.'ids:-resources[ids]['amount']}})
                users.update_one({'id':user['id']},{'$set':{'buildings.'+place+'.'+b['name']+str(b['number']):b}})
                medit('Вы начали постройку склада! Стройка закончится примерно через 6 часов.', call.message.chat.id, call.message.message_id)
            else:
                medit('Не хватает ресурсов!', call.message.chat.id, call.message.message_id)
            
    if call.data=='close':
        medit('Меню закрыто.', call.message.chat.id, call.message.message_id, reply_markup=kb)
    
    
def addres(res, amount):
    return {
        res:{'amount':amount
            }
    }
    
def buildinginfo(b):
    text='Неизвестно'
    if b=='stock':
        text='На склад поступают все ресурсы с месторождений. Чтобы ресурсы можно было использовать, их нужно отвезти со '+\
        'склада на вашу главную фабрику. Время перевозки зависит от расстояния между двумя точками.\n\n'
        text+='Характеристики строения:\n'
        text+='Вместимость: 1000 ед. любых ресурсов\n'
        text+='📦Требуемые ресурсы:\n'
        text+='  Доски: 100 000\n'
        text+='  Железо: 40 000\n'
        text+='  ⏰Время: 6ч.\n'
    return text
        
    
    
def buildingslist(user, recource):
    for ids in user['buildings'][recource]:
        text+=building_ru(ids)+'\n'
    return text
    

def buildmenu(user, resource):
    kb=types.InlineKeyboardMarkup()
    str1=[]
    str1.append(types.InlineKeyboardButton(text='Склад', callback_data='info stock '+resource))
    str1.append(types.KeyboardButton(text='Нефтяная вышка', callback_data='info oilfarmer '+resource))
    kb.add(*str1)
    bot.send_message(user['id'], 'Выберите строение для просмотра информации.', reply_markup=kb)
    
    

def recource_fields(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('🛢Нефть'),types.KeyboardButton('🌲Деревья'),types.KeyboardButton('💎Руды'))
    kb.add(types.KeyboardButton('🏢Главное меню'))
    bot.send_message(user['id'], 'Выберите интересующий вас ресурс.', reply_markup=kb)
    
    
    
def aboutme(user):
    text=''
    text+='Имя: '+user['name']+'\n'
    text+='Ресурсы:\n'
    for ids in user['resources']:
        text+=recource_ru(ids)+': '+str(user['resources'][ids]['count'])+'\n'
    text+='\n'
    text+='Рубли: '+str(user['money'])+'\n'
    text+='Уровень главной фабрики: '+str(user['fabricalvl'])+'\n'
    return text
    
    
def build(building, user, place, built, time=None):   # if built==False, time required
    count=1
    for ids in user['buildings'][place]:
        if building in ids:
            count+=1
    gentime=10               # В минутах
    amount=10                # Кол-во ресурса
    if building=='stock':
        capacity=1000
        gentime=0
    else:
        capacity=100
    return {building+str(count):{
        'items':{},
        'lvl':1,
        'capacity':capacity,
        'generate_time':gentime,
        'amount':amount,                 # Генерация ресурса
        'lastgen':None,
        'name':building,
        'number':count,
        'place':place,
        'built':built,
        'buildtime':time,
        'createtime':time.ctime()
    }
               }


def building_ru(x):
    if 'stock' in x:
        return 'Склад'
    if 'oilfarmer' in x:
        return 'Нефтяная вышка'
    if 'forestcutter' in x:
        return 'Автолесоруб'
    
    return 'Неизвестное строение'


def resource_ru(x):
    if x=='oil':
        return 'Нефть'
    return 'Неизвестный ресурс'
    
    
def addresource(building, user):
    error=25             # Погрешность добычи ресурса (в %).
    place=building['place']
    w=world.find_one({})
    if building=='oilfarmer':
        resource='oil'
    elif building=='forestcutter':
        resource='wood'
    amount=building['amount']
    if random.randint(1,100)<=50:
        amount-=amount*random.randint(0, error)
    else:
        amount+=amount*random.randint(0, error)
    if w['resources'][resource]<amount:
        amount=w['resources'][resource]
    stocks=[]
    for ids in user['buildings'][place]:
        bld=user['buildings'][place][ids]
        if bld['name']=='stock':
            stocks.append(bld)
    currentstock=None
    for ids in stocks:
        count=0
        for idss in ids['items']:
            count+=ids['items'][idss]
        if count+amount<=ids['capacity']:
            currentstock=ids['name']+ids['number']
    if currentstock!=None:
        try:
            users.update_one({'id':user['id']},{'$inc':{'buildings.'+place+'.'+currentstock+'.'+'items.'+resource:amount}})
        except:
            users.update_one({'id':user['id']},{'$set':{'buildings.'+place+'.'+currentstock+'.'+'items.'+resource:amount}})
        
    
    
def createuser(user):
    summ=40     # Сколько всего км будет распределено между всеми ресурсными точками
    d_oil=random.randint(0,summ)
    summ-=d_oil
    d_forest=random.randint(0,summ)
    summ-=d_forest
    d_ore=summ
    oil={}
    forest={}
    oil.update(build('stock'), user, 'oil', True)
    oil.update(build('oilfarmer', user, 'oil', True))
    forest.update(build('stock', user, 'forest', True))
    forest.update(build('forestcutter', user, 'forest', True))
    return {
        'id':user.id,
        'name':user.first_name,
        'username':user.username,
        'resources':{},
        'buildings':{
            'oil':oil,
            'forest':forest,
            'ore':{}
        },
        'money':0,
        'fabricalvl':1,
        'distances':{
            'oil':d_oil,
            'forest':d_forest,
            'ore':d_ore
        }
    }
    
    
def mainmenu(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('❓Обо мне'), types.KeyboardButton('👷‍♂️Месторождения ресурсов'))
    bot.send_message(user['id'], '🏡Главное меню.', reply_markup=kb)
 
def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)  


def timecheck():
    t=threading.Timer(60, timecheck)
    t.start()
    x=time.ctime()
    x=x.split(" ")
    month=0
    year=0
    ind=0
    num=0
    for ids in x:
       for idss in ids:
          if idss==':':
             tru=ids
             ind=num
       num+=1
    day=x[ind-1]
    month=x[1]
    year=x[ind+1]
    x=tru 
    x=x.split(":")  
    minute=int(x[1])    # минуты
    hour=int(x[0])+3  # часы (+3, потому что heroku в Великобритании)
    z=time.ctime()
    z=z.split(' ')
    u=users.find({})
    for ids in u:
        cuser=users.find_one({'id':ids['id']})
        for idss in cuser['buildings']:
            for idsss in cuser['buildings'][idss]:
                building=cuser['buildings'][idss][idsss]
                if building['built']==True:
                    settime=building['lastgen']
                    a=settime.split(" ")
                    ind=0
                    num=0
                    for idss in a:
                    for idsss in idss:
                        if idsss==':':
                            trua=idss
                            ind=num
                    num+=1
                    cday=a[ind-1]
                    cmonth=a[1]
                    cyear=a[ind+1]
                    a=trua
                    a=a.split(":")  
                    chour=int(a[0])+3
                    cminute=int(a[1])
                    
                    if minute-cminute>=building['generate_time']:
                        addresource(building, cuser)
                        
                    elif hour-chour>=1:
                        if minute+(60-cminute)>=building['generate_time']:
                            addresource(building, cuser)
                            
                    elif cday!=day or cmonth!=month or cyear!=year:
                        addresource(building, cuser)
    

    
    
print('7777')
bot.polling(none_stop=True,timeout=600)

