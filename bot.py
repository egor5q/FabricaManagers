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
            bot.send_message(m.chat.id, 'Добывай ресурсы, строй механизмы на своей фабрике, шпионь, кради ресурсы у других, и участвуй в '+
                            'ежедневных битвах роботов!')
        mainmenu(user)
    

@bot.message_handler(commands=['world_addres'])
def addresourcestoworld(m):
    if m.from_user.id==441399484:
        try:
            resource=m.text.split(' ')[1]
            amount=int(m.text.split(' ')[2])
            try:
                world.update_one({},{'$inc':{'res.'+resource:amount}})
            except:
                world.update_one({},{'$set':{'res.'+resource:amount}})
            current=world.find_one({})['res'][resource]
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
                if len(user['buildings']['oil'])>0:
                    builds=True
                if builds==False:
                    text+='У вас здесь ещё нет строений.\n'
                else:
                    text+='Ваши постройки здесь:\n'
                    text+=buildingslist(user, 'oil')
                    text+='\n'
                kb.add(types.KeyboardButton('⚒Стройка: нефть'))
                kb.add(types.KeyboardButton('🏢Главное меню'))
                bot.send_message(m.chat.id, text, reply_markup=kb)
                
            if m.text=='⚒Стройка: нефть':
                buildmenu(user, 'oil')
                
            if m.text=='🚚Транспортировка ресурсов':
                transportmenu(user)
                
        except Exception as e:
            bot.send_message(441399484, traceback.format_exc())
    
    
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
            
        if 'truck' in call.data:
            unit=call.data.split(' ')[1]
            text=unitinfo(user['units'][unit])
            kb.add(types.InlineKeyboardButton(text='Отправить за ресурсами', callback_data='sendto '+unit))
            
    if 'sendto' in call.data:
        unit=call.data.split(' ')[1]
        places=['oil', 'forest', 'ores']
        oil_time=round((user['units'][unit]['speed']/user['distances']['oil'])*2, 2)
        forest_time=round((user['units'][unit]['speed']/user['distances']['forest'])*2, 2)
        ores_time=round((user['units'][unit]['speed']/user['distances']['ores'])*2, 2)
        for ids in places:
            kb.add(types.InlineKeyboardButton(text=fields_ru(ids), callback_data='send '+unit+' '+ids))
        medit('Выберите, куда отправить транспорт. Он заберёт столько ресурсов со склада, сколько уместится.\n'+
                         'Примерное время доставки от точек:\n'+
                        '  Нефть: '+str(oil_time)+' час(ов)\n'+
                        '  Лес: '+str(forest_time)+' час(ов)\n'+
                        '  Руды: '+str(ores_time)+' час(ов)\n', call.message.chat.id, call.message.message_id, reply_markup=kb)
        
    if 'send' in call.data:
        unit=call.data.split(' ')[1]
        to=call.data.split(' ')[2]
        if user['units'][unit]['status']=='free':
            sendto(user, unit, to)
            medit('Транспорт отправлен!', call.message.chat.id, call.message.message_id)
        else:
            medit('Этот транспорт занят!', call.message.chat.id, call.message.message_id)
            
    if 'build' in call.data:
        if 'stock' in call.data:
            resources={}
            place=call.data.split(' ')[2]
            resources.update(addres('wood', 100000))
            resources.update(addres('iron', 40000))
            nores=False
            try:
                for ids in resources:
                    if user['resources'][ids]<resources[ids]:
                        nores=True
            except:
                nores=True
                
            if nores==False:
                b=build(stock, user, place, False, time=21600) 
                for ids in resources:
                    users.update_one({'id':user['id']},{'$inc':{'resources.'+ids:-resources[ids]['amount']}})
                users.update_one({'id':user['id']},{'$set':{'buildings.'+place+'.'+b['name']+str(b['number']):b}})
                medit('Вы начали постройку склада! Стройка закончится примерно через 6 часов.', call.message.chat.id, call.message.message_id)
            else:
                medit('Не хватает ресурсов!', call.message.chat.id, call.message.message_id)
            
    if call.data=='close':
        medit('Меню закрыто.', call.message.chat.id, call.message.message_id, reply_markup=kb)
    
    
def sendto(user, unit, to):
    users.update_one({'id':user['id']},{'$set':{'units.'+unit+'.status':'busy'}})
    timee=round((user['units'][unit]['speed']/user['distances'][to])*2, 2)
    timee=timee*3600
    inv=[]
    count=0
    for ids in user['buildings'][to]:
        building=user['buildings'][to][ids]
        if building['name']=='stock':
            for ids in building['items']:
                c=building['items'][ids]
                if count+c>user['units'][unit]['capacity']:
                    c=user['units'][unit]['capacity']-count
                    if c!=0:
                        inv.append({ids:c})
                        count+=c
                        users.update_one({'id':user['id']},{'$inc':{'buildings.'+to+'.'+building['name']+building['number']+'.items.'+ids:-c}})
    users.update_one({'id':user['id']},{'$set':{'units.'+unit+'.deliver_time':time.time()+timee}})
    users.update_one({'id':user['id']},{'$set':{'units.'+unit+'.inventory':inv}})
    
        
    
    
    
def transportmenu(user):
    text='Здесь находится весь ваш свободный транспорт. Он нужен для того, чтобы перевозить ресурсы со складов на главную фабрику. Нажмите кнопку '+\
    'для просмотра информации.'
    alltransport=[]
    kb=types.InlineKeyboardMarkup()
    for ids in user['units']:
        unit=user['units'][ids]
        if unit['type']=='transport' and unit['status']=='free':
            alltransport.append(unit)
    for ids in alltransport:
        kb.add(types.InlineKeyboardButton(text=units_ru(ids['name']), callback_data='info '+unit['name']+unit['number']))
    kb.add(types.InlineKeyboardButton(text='Закрыть меню', callback_data='close'))
    bot.send_message(user['id'], text, reply_markup=kb)
    
                                            
                                             
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
        
    
def unitinfo(unit):
    text=unit['name']+':\n'
    if unit['type']=='transport':
        text+='Скорость: '+str(unit['speed'])+' км/ч\n'
        text+='Вместимость: '+str(unit['capacity'])+'\n'
    return text
    
    
def buildingslist(user, recource):
    text=''
    for ids in user['buildings'][recource]:
        text+=building_ru(ids)+'\n'
    return text
    

def buildmenu(user, resource):
    kb=types.InlineKeyboardMarkup()
    str1=[]
    str1.append(types.InlineKeyboardButton(text='Склад', callback_data='info stock '+resource))
    str1.append(types.InlineKeyboardButton(text='Нефтяная вышка', callback_data='info oilfarmer '+resource))
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
    
  
def createunit(user, unit):
    speed=60            # km/h
    typee=None
    if unit=='truck':
        typee='transport'
    count=1
    try:
        for ids in user['units']:
            if unit in ids:
                count+=1
    except:
        pass
    return {unit+str(count):{
        'name':unit,
        'speed':speed,
        'capacity':1000,
        'type':typee,
        'number':count,
        'status':'free',
        'inventory':[],
        'deliver_time':None    # Время, когда ресурсы из inventory попадут на общий склад.
    }
           }


def build(building, user, place, built, time=None):   # if built==False, time required
    count=1
    try:
        for ids in user['buildings'][place]:
            if building in ids:
                count+=1
    except:
        pass
    gentime=600               # В секундах
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
        'amount':amount,                 # Добываемое кол-во ресурса
        'nextgen':None,                  # Время следующей добычи ресурса (в unix)
        'name':building,
        'number':count,
        'place':place,
        'built':built,
        'buildtime':time                 # unix - когда строение будет построено
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
    
                                              
def units_ru(unit):
    if unit=='truck':
        return 'Грузовик'
    return 'Неизвестный юнит'
                                              
                                              
def places_ru(x):
    if x=='oil':
        return 'Нефть'
    if x=='forest':
        return 'Лес'
    if x=='ores':
        return 'Шахта'
    return 'Неизвестное место'
        
                                              
    
def addresource(building, user):
    error=25             # Погрешность добычи ресурса (в %).
    place=building['place']
    w=world.find_one({})
    if building['name']=='oilfarmer':
        resource='oil'
    elif building['name']=='forestcutter':
        resource='wood'
    amount=building['amount']
    if random.randint(1,100)<=50:
        amount-=amount*(random.randint(0, error)/100)
    else:
        amount+=amount*(random.randint(0, error)/100)
    try:
        if w['res'][resource]<amount:
            amount=w['resources'][resource]
    except:
        return False
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
            currentstock=ids['name']+str(ids['number'])
    if currentstock!=None:
        try:
            users.update_one({'id':user['id']},{'$inc':{'buildings.'+place+'.'+currentstock+'.'+'items.'+resource:amount}})
        except:
            users.update_one({'id':user['id']},{'$set':{'buildings.'+place+'.'+currentstock+'.'+'items.'+resource:amount}})
        users.update_one({'id':user['id']},{'$set':{'buildings.'+place+'.'+building['name']+str(building['number'])+'.nextgen':int(time.time())+building['generate_time']}})
        world.update_one({},{'$inc':{'res.'+resource:-amount}})
        
    
    
def createuser(user):
    summ=80     # Сколько всего км будет распределено между всеми ресурсными точками
    d_ore=random.randint(1,summ)
    summ-=d_ore
    d_forest=random.randint(1,summ)
    summ-=d_forest
    d_oil=summ
    oil={}
    forest={}
    oil.update(build('stock', user, 'oil', True))
    oil.update(build('oilfarmer', user, 'oil', True))
    forest.update(build('stock', user, 'forest', True))
    forest.update(build('forestcutter', user, 'forest', True))
    units={}
    units.update(createunit(user, 'truck'))
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
        'units':units,
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
    kb.add(types.KeyboardButton('❓Обо мне'), types.KeyboardButton('👷‍♂️Месторождения ресурсов'), types.KeyboardButton('🚚Транспортировка ресурсов'))
    try:
        bot.send_message(user['id'], '🏡Главное меню.', reply_markup=kb)
    except:
        bot.send_message(user.id, '🏡Главное меню.', reply_markup=kb)
 
def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)  

def finishbuild(user, building):
    path='buildings.'+building['place']+'.'+building['name']+building['number']
    users.update_one({'id':user['id']},{'$set':{path+'.built':True, path+'.buildtime':None}})
    bot.send_message(user['id'], 'Строение "'+building_ru(building['name'])+'": стройка завершена!')

def finishdelivery(user, unit):
    allres={}
    for ids in unit['inventory']:
        for idss in ids:
            try:
                users.update_one({'id':user['id']},{'$inc':{'resources.'+idss:ids[idss]}})
            except:
                users.update_one({'id':user['id']},{'$set':{'resources.'+idss:ids[idss]}})
            try:
                allres[idss]+=ids[idss]
            except:
                allres.update({
                    idss:ids[idss]
                })
    users.update_one({'id':user['id']},{'$set':{'units.'+unit['name']+unit['number']+'.inventory':[]}})
    users.update_one({'id':user['id']},{'$set':{'units.'+unit['name']+unit['number']+'.status':'free'}})
    return allres
            

def timecheck():
    t=threading.Timer(60, timecheck)
    t.start()
    timee=int(time.time())
    u=users.find({})
    for ids in u:
        cuser=users.find_one({'id':ids['id']})
        for idss in cuser['buildings']:
            for idsss in cuser['buildings'][idss]:
                building=cuser['buildings'][idss][idsss]
                if building['built']==True:
                    ctime=building['nextgen']
                    if ctime!=None:
                        if timee>=ctime:
                            addresource(building, cuser)
                    else:
                        addresource(building, cuser)
                        
                else:
                    ctime=building['buildtime']
                    if timee>=ctime:
                        finishbuild(cuser, building)
                    
        for idss in cuser['units']:
            unit=cuser['units'][idss]
            if unit['type']=='transport':
                ctime=unit['deliver_time']
                if ctime!=None:
                    if timee>=ctime:
                        text=''
                        resources=finishdelivery(cuser, unit)
                        for ids in resources:
                            text+=resource_ru(ids)+': '+str(resources[ids])+'\n'
                        bot.send_message(cuser['id'], 'Ваш транспорт приехал! Полученные ресурсы:\n'+text)
                        
  
    
timecheck()
    
print('7777')
bot.polling(none_stop=True,timeout=600)

