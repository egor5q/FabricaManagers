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
    
    
@bot.message_handler()
def messages(m):
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
                    text+='У вас здесь ещё нет склада.'
                else:
                    text+='Ваши постройки здесь:\n'
                    text+=buildingslist(user, 'oil')
                    text+='\n'
    
    
def buildingslist(user, recource):
    for ids in user['buildings'][recource]:
        text+=building_ru(ids)+'\n'
    return text
    


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
    
    
def build(x, user):
    count=1
    for ids in user['buildings']:
        if x in ids:
            count+=1
    gentime=10               # В минутах
    amount=10                # Кол-во ресурса
    if x=='stock':
        capacity=1000
        gentime=0
    else:
        capacity=100
    return {x+str(count):{
        'items':{},
        'lvl':1,
        'capacity':capacity,
        'generate_time':gentime,
        'amount':amount
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
    
    
def createuser(user):
    summ=40     # Сколько всего км будет распределено между всеми ресурсными точками
    d_oil=random.randint(0,summ)
    summ-=d_oil
    d_forest=random.randint(0,summ)
    summ-=d_forest
    d_ore=summ
    oil={}
    forest={}
    oil.update(build('stock'))
    oil.update(build('oilfarmer'))
    forest.update(build('stock'))
    forest.update(build('forestcutter'))
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
    
    
    
print('7777')
bot.polling(none_stop=True,timeout=600)

