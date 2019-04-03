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
    
    
    
    
    
    
def aboutme(user):
    text=''
    text+='Имя: '+user['name']+'\n'
    text+='Ресурсы:\n'
    for ids in user['resources']:
        text+=recource_ru(ids)+': '+str(user['resources'][ids]['count'])+'\n'
    text+='Рубли: '+str(user['money'])+'\n'
    text+='Уровень главной фабрики: '+str(user['fabricalvl'])+'\n'
    return text
    
    
    
def resource_ru(x):
    if x=='oil':
        return 'Нефть'
    return 'Неизвестный ресурс'
    
    
def createuser(user):
    return {
        'id':user.id,
        'name':user.first_name,
        'username':user.username,
        'resources':{},
        'buildings':{},
        'money':0,
        'fabricalvl':1
    }
    
    
def mainmenu(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('❓Обо мне'), types.KeyboardButton('👷‍♂️Месторождения ресурсов'))
    bot.send_message(user['id'], '🏡Главное меню.', reply_markup=kb)
    
    
    
print('7777')
bot.polling(none_stop=True,timeout=600)

