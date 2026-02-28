import asyncio
import logging
import sys
import re
import time
import os
from docx import Document
from datetime import datetime, timedelta, date
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from openpyxl import load_workbook
import pytz
from database.requests import DBRequests
import pandas as pd 
from collections import defaultdict

file_path = 'file.xlsx'
df = pd.read_excel('file.xlsx')
API_TOKEN = '7747630305:AAF-HxD3Syqrlc9Z23l_Nd7Rg59ykCKCLnU' #Вставьте токен
Bot = Bot(token=API_TOKEN,request_timeout=300)
dp = Dispatcher()
awaiting_file = False
ADMIN_ID = 963729102
ADMIN_ID2 = 1624096187
days_mapping = {
    'пн': 'Понедельник',
    'вт': 'Вторник',
    'ср': 'Среда',
    'чт': 'Четверг',
    'пт': 'Пятница',
    'сб': 'Суббота',
    'вс': 'Воскресенье'
}

user_data = defaultdict(dict)

main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Завтра'),KeyboardButton(text='Сегодня'),KeyboardButton(text='Какая неделя')],
    [KeyboardButton(text='Все расписание'),KeyboardButton(text='День недели'),KeyboardButton(text='Cloud')],
    [KeyboardButton(text='Доп. функции'),KeyboardButton(text='Преподаватели')],
    [KeyboardButton(text='Группа'),KeyboardButton(text='Обратная связь')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню...')

dop_panel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Расписание преподавателя'),KeyboardButton(text='Расписание кабинетов')],
    [KeyboardButton(text='Создать титульный лист')],
    [KeyboardButton(text='Назад')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню...')



otmena = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отмена')],
], resize_keyboard=True, input_field_placeholder='Обратная связь...')

admin_panel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='id участников'),KeyboardButton(text='Поменять файл')],
    [KeyboardButton(text='Рассылка'),KeyboardButton(text='Сообщение пользователю')],
    [KeyboardButton(text='Назад')]
    
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню...')

chet_nechet = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Четная'),KeyboardButton(text='Нечетная')],
    [KeyboardButton(text='Общее')],
    [KeyboardButton(text='Назад')]
    
], resize_keyboard=True, input_field_placeholder='Чет или нечет...')

prepod_k= ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Да'),KeyboardButton(text='Нет')],
    [KeyboardButton(text='Назад')]
    
], resize_keyboard=True, input_field_placeholder='Верно?')
nech_days_of_week_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='⬇️ Неч ⬇️')],
    [KeyboardButton(text='Понедельник'),KeyboardButton(text='Вторник')],
    [KeyboardButton(text='Среда'),KeyboardButton(text='Четверг')],
    [KeyboardButton(text='Пятница'),KeyboardButton(text='Суббота')],
    [KeyboardButton(text='Назад')]
], resize_keyboard=True, input_field_placeholder='Выберите день...')


ch_days_of_week_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='⬇️ Чет ⬇️')],
    [KeyboardButton(text='Понедельник'),KeyboardButton(text='Вторник')],
    [KeyboardButton(text='Среда'),KeyboardButton(text='Четверг')],
    [KeyboardButton(text='Пятница'),KeyboardButton(text='Суббота')],
    [KeyboardButton(text='Назад')]
], resize_keyboard=True, input_field_placeholder='Выберите день...')


prep=""
user_ids = []
router = Router(name=__name__)
tasks = {}  
user_groups = {}
ch_spis = {}
register = []
group_list = []
prepod= []
waiting_for_file = 0
waiting_for_group = False
USERS_FILE = "users.txt"
USERS_NEW = "user_new.txt"
day = None
id = 0
sch=0
k1=""
k2=""
group=""
id_pip=1


def save(user,ID):
    info=f"@{user} ID: {ID}"
    lines = []
    with open(USERS_NEW, "r") as file:
        Find=0
        for line in file:
            if str(ID) in line:
                Find=1
                if not(user in line):
                    if ")" in line[-2:]:
                        g=line[-7:]
                        lines.append(info+" "+ g)
                    else:
                        lines.append(info+"\n")
                else:
                    lines.append(line)
            else:
                lines.append(line)
        if Find==0:
            lines.append(info)
    with open(USERS_NEW, "w") as file:
        file.writelines(lines)
    with open(USERS_FILE, "r") as file:
        lines = []
        Find=0
        for line in file:
            if not(str(ID) in line):
                lines.append(line)
            else:
                Find=1
                lines.append(line)
        if Find==0:
            lines.append(str(ID) + "\n")
    with open(USERS_FILE, "w") as file:
        file.writelines(lines)
        


def check_file(ID):
    with open(USERS_NEW, "r") as file:
        for line in file:
            if str(ID) in line:
                if ")" in line[-2:]:
                    grop=(line[-7:])[1:-2]
                    return grop
                else:
                    return "Не введена"

                

class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()
    select_group = State()
    iluz = State()
    obrashenie= State()
    svaz= State()
    Message_from_human= State()
    Message_from_human2= State()
    faind = State()
    kab1=State()
    kab2=State()
    titul1=State()
    titul2=State()
    titul3=State()
    titul4=State()
    titul5=State()
    titul6=State()
    titul7=State()





async def admin_sms(user,idd):
    if idd not in user_ids:
        user_ids.append(idd)
        await Bot.send_message(str(ADMIN_ID), f"Зарегистрирован @{user}\nID: {idd}")


@dp.message(F.text == 'Отмена', StateFilter('*'))
async def process_group(message: types.Message, state: FSMContext):
    await message.answer("Действие отменено",reply_markup=main_keyboard)
    await state.clear()

@dp.message(F.text == 'Создать титульный лист')
async def process_group(message: types.Message, state: FSMContext):
    await message.answer("Чтобы создать титульник, отвечай на вопросы по порядку",reply_markup=otmena)
    await message.answer("Введи название дисциплины:")
    await state.set_state(BroadcastState.titul1)

@dp.message(F.text == 'Cloud')
async def process_group(message: types.Message, state: FSMContext):
    site_id_user = DBRequests().new_human(message.from_user.id)
    await message.answer(f"Твйо Cloud ID: {site_id_user}\n\nВ течении следующих 10 минут ты можешь перекидывать файлы в Telegram через сайт kaicloud.ru, для этого нужен всего лишь ID")

@dp.message(StateFilter(BroadcastState.titul1))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['diccheplina'] = str(message.text)
    await state.clear()
    await state.set_state(BroadcastState.titul2)
    await message.answer("Введи тему работы:")
@dp.message(StateFilter(BroadcastState.titul2))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['tema'] = str(message.text)
    await state.clear()
    await state.set_state(BroadcastState.titul3)
    await message.answer("Введи тип работы (Лабораторная работа,Практическая работа и тд.):")


@dp.message(StateFilter(BroadcastState.titul3))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['tip'] = str(message.text).upper()
    await state.clear()
    await state.set_state(BroadcastState.titul4)
    await message.answer("Введи нумерацию работы:")

@dp.message(StateFilter(BroadcastState.titul4))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['number'] = str(message.text)
    await state.clear()
    await state.set_state(BroadcastState.titul5)
    await message.answer("Введи номер своей группы:")

@dp.message(StateFilter(BroadcastState.titul5))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['gpyp'] = str(message.text)
    await state.clear()
    await state.set_state(BroadcastState.titul6)
    await message.answer("Введи свое ФИО:")


@dp.message(StateFilter(BroadcastState.titul6))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    user_id = message.from_user.id
    user_data[user_id]['famImaOtch'] = str(message.text)
    await state.clear()
    await state.set_state(BroadcastState.titul7)
    await message.answer("Введи ФИО преподователя:")


@dp.message(StateFilter(BroadcastState.titul7))
async def process_group(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    
    user_id = message.from_user.id
    user_data[user_id]['prepodFIO'] = str(message.text)
    await state.clear()
    
    try:
        doc = Document("title.docx")
        replacements = {
            "TYPE": user_data.get(user_id, {}).get('tip', "не установлено"),
            "number": user_data.get(user_id, {}).get('number', "не установлено"),
            "discipline": user_data.get(user_id, {}).get('diccheplina', "не установлено"),
            "topic": user_data.get(user_id, {}).get('tema', "не установлено"),
            "group": user_data.get(user_id, {}).get('gpyp', "не установлено"),
            "FIO": user_data.get(user_id, {}).get('famImaOtch', "не установлено"),
            "prepod": user_data.get(user_id, {}).get('prepodFIO', "не установлено")
        }

        for paragraph in doc.paragraphs:
            # Работаем с отдельными частями текста (runs)
            for run in paragraph.runs:
                original_text = run.text
                for key, value in replacements.items():
                    if key in original_text:
                        # Заменяем текст с сохранением форматирования
                        run.text = original_text.replace(key, value)
        namemm=user_data.get(user_id, {}).get('famImaOtch', "не установлено")
        doc.save(f"{namemm}.docx")
        await message.answer("Держи свой титульник:",reply_markup=main_keyboard)
        await message.answer_document(types.FSInputFile(f"{namemm}.docx"))
        os.remove(f"{namemm}.docx")
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.clear()
    


@dp.message(F.text == 'Доп. функции')
async def start(message: types.Message, state: FSMContext):
    await message.answer("Выбери пункт меню:",reply_markup=dop_panel)


@dp.message(F.text == 'Расписание кабинетов')
async def start(message: types.Message, state: FSMContext):
    await message.answer("Укажи здание, где находится кабинет:",reply_markup=otmena)
    await state.set_state(BroadcastState.kab1)

@dp.message(StateFilter(BroadcastState.kab1))
async def start(message: types.Message, state: FSMContext):
    global k1
    if not(message.text):
        await message.answer("Давай лучше текстом :/")
        return
    try:
        df = pd.read_excel('file.xlsx')
        df = df.sort_values(by='Время')
    except:
        df['Время'] = pd.to_datetime(df['Время'], format='%H:%M:%S') 
        df = df.sort_values(by='Время')
    k1s=[]
    a=-1
    while True:
        try:
            kabinet = df.iloc[a][df.columns[7]]
            if (str(message.text).lower())[0].isdigit():
                if str(message.text).lower() == (str(kabinet)).lower():
                    k1=(str(kabinet)).rstrip()
                    k1s.append(k1)
                a=a+1
            else:
                if str(message.text).lower() in (str(kabinet)).lower():
                    k1=(str(kabinet)).rstrip()
                    k1s.append(k1)
                a=a+1
        except:
            break
    if k1s==[]:
        await message.answer(f"Не нашел такого здания в расписании")
        return
    await message.answer(f"Твое здание - {k1}")
    await message.answer(f"А теперь введи номер кабинета (например 219 или 219а):")
    await state.clear()
    await state.set_state(BroadcastState.kab2)

@dp.message(StateFilter(BroadcastState.kab2))
async def start(message: types.Message, state: FSMContext):
    global k2
    global k1
    global days_mapping
    if not(message.text):
        await message.answer("Давай лучше текстом :/")
        return
    try:
        df = pd.read_excel('file.xlsx')
        df = df.sort_values(by='Время')
    except:
        df['Время'] = pd.to_datetime(df['Время'], format='%H:%M:%S') 
        df = df.sort_values(by='Время')
    k2s=[]
    a=-1
    while True:
        try:
            kabinet = df.iloc[a][df.columns[6]]
            if (str(message.text).lower())[0].isdigit():
                if str(message.text).lower() == str(kabinet).lower():
                    k2=(str(kabinet)).rstrip()
                    k2s.append(k2)
                    break
                a=a+1
            else:
                if str(message.text).lower() in str(kabinet).lower():
                    k2=(str(kabinet)).rstrip()
                    k2s.append(k2)
                    break
                a=a+1
        except:
            break
    if k2s==[]:
        await message.answer(f"Не нашел такого кабинета в расписании")
        return
    await message.answer(f"Кабинет - {k2}\nЗдание - {k1}")
    await state.clear()
    a=-1
    d=0
    q=0
    R2=""
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
    day = days[d]
    for i in range(6):
        day = days[d]
        while True:
            try:
                kab=(str(df.iloc[a][df.columns[6]]))
                zdanie=str(df.iloc[a][df.columns[7]])
                if k2==kab.rstrip() and k1 in zdanie and (str(df.iloc[a][df.columns[1]])).rstrip() == str(day):
                    time=(str(df.iloc[a][df.columns[2]]))[:5]
                    group222=(str(df.iloc[a][df.columns[0]]))[:4]
                    ch_nech = (df.iloc[a][df.columns[3]])
                    lec_pr= (str(df.iloc[a][df.columns[5]])).rstrip()
                    if {str(ch_nech)} == {'nan'}: 
                        ch_nech = "чет/неч"  
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech:
                            ch_nech="неч"
                        elif "чет" in ch_nech:
                            ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    para=df.iloc[a][df.columns[4]]
                    prepod = df.iloc[a][df.columns[9]]
                    if q==0:
                        R1=f"➤{days_mapping[day]}\n➤{k2}_{k1}\n\n➤<b>{ch_nech}</b>🕘{time}\n<b>{para}</b>({lec_pr})({group222})\n{k2}_{k1}зд.\n{prepod}\n"
                        q=1
                    else:
                        R1=f"➤<b>{ch_nech}</b>🕘{time}\n<b>{para}</b>({lec_pr})({group222})\n{k2}_{k1}зд.\n{prepod}"
                    R2=R2+R1
                    a=a+1
                else:
                    a=a+1
            except:
                break
        q=0
        d=d+1
        a=-1
        try:
            if len(R2) > 4000:
                first_part = R2[:4000]
                second_part = R2[4000:]
                await message.answer(first_part, parse_mode='HTML')
                await message.answer(second_part, parse_mode='HTML')   
            else:
                await message.answer(R2, parse_mode='HTML')   
        except Exception as e:
            vvv=f"➤{days_mapping[day]}\n\nЗанятий нет"
            await message.answer(vvv, parse_mode='HTML') 
        R1=""
        R2=""
    await message.answer("Выбери пункт меню",reply_markup=main_keyboard)


@dp.message(F.text == 'Расписание преподавателя')
async def start(message: types.Message, state: FSMContext):
    await message.answer("Введи ФИО преподавателя:",reply_markup=otmena)
    await state.set_state(BroadcastState.faind)


@dp.message(F.text == "Нет",StateFilter(BroadcastState.faind))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Проверь, правильно ли написано ФИО\nЕсли не помнишь его полностью, попробуй ввести только фамилию, фамилию и имя,отчество и тд. ",reply_markup=otmena)


@dp.message(F.text == "Да",StateFilter(BroadcastState.faind))
async def start(message: types.Message, state: FSMContext):
    global prep
    try:
        df = pd.read_excel('file.xlsx')
        df = df.sort_values(by='Время')
    except:
        df['Время'] = pd.to_datetime(df['Время'], format='%H:%M:%S') 
        df = df.sort_values(by='Время')
    a=-1 #Номера строк
    b=9 #Номера столбцов
    d=0 #номер дня недели
    q=1 #только 1 раз ввести день недели 
    R_3=""
    j=0
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
    day = days[d]
    x = 0 #Только 1 раз ввести и группу и день недели
    number_group = df.iloc[a][df.columns[9]]
    for i in range(6):
        while j == 0:
            try:
                if {str(number_group)} == {str(prep)}:
                    day_k = (df.iloc[a][df.columns[1]])[:2]
                    ch_nech = df.iloc[a][df.columns[3]]
                    global days_mapping
                    if {str(ch_nech)} == {'nan'}: ch_nech = "чет/неч"  
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech:
                            ch_nech="неч"
                        elif "чет" in ch_nech:
                            ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    if {str(day_k)} == {str(day)} :
                        time=(str(df.iloc[a][df.columns[2]]))[:5]
                        para= df.iloc[a][df.columns[4]]
                        lec_pr= df.iloc[a][df.columns[5]]
                        if lec_pr.startswith("л."):
                            lec_pr=lec_pr[:4]  # Оставляем первые 4 символа
                        elif lec_pr.startswith("лек"):
                            lec_pr=lec_pr[:3]  # Оставляем первые 3 символа
                        elif lec_pr.startswith("пр"):
                            lec_pr=lec_pr[:2]  # Оставляем первые 2 символа
                        kab= (str(df.iloc[a][df.columns[6]])).rstrip()
                        group222 = df.iloc[a][df.columns[0]]
                        zdanie= (str(df.iloc[a][df.columns[7]])).rstrip()
                        if x == 0:
                            day_k = days_mapping[day_k]
                            R_1=f"➤{day_k}\n➤{prep}\n\n"
                            x=x+1
                        else:
                            if q==0:
                                day_k = days_mapping[day_k]
                                R_1=f"➤{day_k}\n"
                                q=q+1
                            else:
                                R_1=''
                        R_2=f"{R_1}➤ <b>{ch_nech}</b> 🕘 <b>{time}</b>\n<b>({group222}){para}</b>({lec_pr})\n{kab}_{zdanie}зд."
                        R_3=f"{R_3}\n{R_2}"               
                a=a+1
                number_group = df.iloc[a][df.columns[9]] 
            except IndexError as e:
                print("Конец")
                j=1 
                q=0
                a=-1
        try:
            await message.answer(R_3, parse_mode='HTML')   
        except Exception as e:
            vvv=f"➤{days_mapping[day]}\n\nЗанятий нет"
            await message.answer(vvv, parse_mode='HTML')   
        


        d=d+1
        j=0
        R_3=""
        days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
        try:
            day = days[d]
        except:
            x=x
    user_id = message.from_user.id
    df = pd.read_excel('file.xlsx')
    await state.clear()
    await message.answer("Выбери пункт меню",reply_markup=main_keyboard)



@dp.message(StateFilter(BroadcastState.faind))
async def start(message: types.Message, state: FSMContext):
    xls = pd.ExcelFile(file_path)
    h=[]
    s=0
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    global prep
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Проходим по всем ячейкам в DataFrame
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                # Проверяем, содержит ли ячейка искомый текст
                if message.text.upper() in str(df.iat[row, col]):
                    # Выводим адрес ячейки
                    cell_address = f"{chr(65 + col)}{row + 1}"  # Преобразуем индекс столбца в букву
                    if df.iat[row, col] not in h and s==0:
                        prep=df.iat[row, col]
                        await message.answer(f'Я правильно понял?\nФИО: {prep}',reply_markup=prepod_k)
                        h.append(df.iat[row, col])
                        s=s+1
    if h == []:
        await message.answer("Данный переподователь не найден,попробуй проверить написание ФИО",reply_markup=otmena)

@dp.message(F.text == '/start')
async def start(message: types.Message, state: FSMContext):
    global ADMIN_ID2
    global ADMIN_ID
    if message.from_user.id == ADMIN_ID2:
        await message.answer("Добро пожаловать, матурым-татарка😉!\nРад тебя видеть!💋 Пусть день у тебя пройдет хорошо, твой Степа тебя обожает конечно же!!!", reply_markup=main_keyboard)
    else:
        await message.answer("Добро пожаловать в расписание КИТ! Рад тебя видеть!", reply_markup=main_keyboard)
    user_id = message.from_user.id
    await state.clear()
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)





@dp.message(F.text == "Группа")
async def start_grup(message: types.Message, state: FSMContext):
    await message.answer("Введите номер группы:",reply_markup=otmena)
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
    await state.set_state(BroadcastState.select_group)


@dp.message(StateFilter(BroadcastState.select_group))
async def process_group(message: types.Message, state: FSMContext):
    a=1
    if not message.text:
        await message.answer("Лучше введи текстом!")
        return
    global USERS_NEW
    global group
    group_list = []
    while True:
        try:
            number_group = str(df.iloc[a][df.columns[0]])
            if number_group not in group_list:
                group_list.append(number_group)
            a=a+1
        except IndexError as e:
            print("Конец")
            break
    if len(message.text) == 4 and message.text.startswith('4'):
        if message.text in group_list:
            group = message.text
            await message.answer(f"Я запомнил твою группу! Теперь выбери, что именно ты хочешь узнать",reply_markup=main_keyboard)
            await state.clear()
        else:
            await message.answer(f"Данной группы нет в расписании,попробуй еще раз :/")
            return
    else:
        await message.answer(f"Группа введена некоректно, попробуй еще раз :/")
        return
    user_id = message.from_user.id
    e_user_new=f"@{message.from_user.username} ID: {user_id}"
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)

    with open(USERS_NEW, 'r') as file:
        lines = []
        for line in file:
            if str(user_id) in line:
                inf=e_user_new + f" ({group})\n"
                lines.append(inf)
            else:
                lines.append(line)
    with open(USERS_NEW, 'w') as file:
        file.writelines(lines)


                 
@dp.message(F.text == "Назад",StateFilter('*'))
async def start(message: types.Message, state: FSMContext):
    await message.answer('Выбери пункт...', reply_markup=main_keyboard)
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
    await state.clear()



@dp.message(F.text == "Все расписание")
async def process_group(message: types.Message, state: FSMContext):
    await message.answer("Выбери четность недели:",reply_markup=chet_nechet)
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)




@dp.message(F.text == "Общее")
async def process_group(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    group = check_file(ID=message.from_user.id)
    if group == "Не введена":
        await message.answer("Для начала введи группу:")
        await state.set_state(BroadcastState.select_group)
        return
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)

    a=-1#Номера строк
    b=0 #Номера столбцов
    d=0 #номер дня недели
    q=1 #только 1 раз ввести день недели 
    R_3=""
    j=0
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
    day = days[d]
    global days_mapping
    x = 0 #Только 1 раз ввести и группу, и день недели
    number_group = df.iloc[a][df.columns[0]]
    for i in range(6):
        while j == 0:
            try:
                if {str(number_group)} == {str(group)}:
                    day_k = (str(df.iloc[a][df.columns[1]]))[:2]
                    ch_nech = str(df.iloc[a][df.columns[3]])
                    if {str(ch_nech)} == {'nan'}:   
                        ch_nech = "чет/неч"
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech: ch_nech="неч"
                        elif "чет" in ch_nech: ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    if {str(day_k)} == {str(day)} :
                        time = (str(df.iloc[a][df.columns[2]]))[:5]
                        para = df.iloc[a][df.columns[4]]
                        lec_pr = df.iloc[a][df.columns[5]]
                        if lec_pr.startswith("л."):lec_pr=lec_pr[:4]
                        elif lec_pr.startswith("лек"):  lec_pr=lec_pr[:3] 
                        elif lec_pr.startswith("пр"):  lec_pr=lec_pr[:2]
                        kab = str(df.iloc[a][df.columns[6]])
                        zdanie = str(df.iloc[a][df.columns[7]])
                        if zdanie.startswith("КСК"):  # Проверяем, начинается ли строка с "КСК"
                            zdanie=zdanie[:3]
                        if kab.startswith("КСК КАИ ОЛИМП"):  # Проверяем, начинается ли строка с "КСК"
                            kab=kab[:13]
                        else:
                            kab=kab[:4]
                        prepod = df.iloc[a][df.columns[9]]
                        if x == 0:
                            day_k = days_mapping[day_k]
                            R_1=f"➤{day_k}\n➤{group}\n➤{ch_nech}\n\n"
                            x=x+1
                        else:
                            if q==0:
                                day_k = days_mapping[day_k]
                                R_1=f"➤{day_k}\n"
                                q=q+1
                            else:
                                R_1=''
                        R_2=f"{R_1}➤ <b>{ch_nech}</b> 🕘 <b>{time}</b>\n<b>{para}</b>({lec_pr})\n{kab}_{zdanie}зд.\n{prepod}"
                        R_3=f"{R_3}\n{R_2}"
                a=a+1
                number_group = df.iloc[a][df.columns[0]] 
            except IndexError as e:
                print("Конец")
                
                j=1 
                q=0
                
                a=-1
        try:
            await message.answer(R_3, parse_mode='HTML')   
        except Exception as e:
            vvv=f"➤{days_mapping[day]}\n\nЗанятий нет"
            await message.answer(vvv, parse_mode='HTML')   
        d=d+1
        j=0
        R_3=""
        days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
        try:
            day = days[d]
        except:
            x=x
    user_id = message.from_user.id
    
    e_user_new=f"@{message.from_user.username} ID: {user_id}"
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)


async def forward_to_admin(user_id: int, message: types.Message):
    """Пересылает сообщение админу с информацией о пользователе"""
    try:
        # Отправляем информацию о пользователе
        user_info = f"Обращение от @{message.from_user.username}\nID: {user_id}\n"
        
        # Пересылаем оригинальное сообщение с сохранением форматирования
        if message.text:
            await Bot.send_message(
                chat_id=str(ADMIN_ID),
                text=user_info + message.text,
                entities=message.entities
            )
        elif message.photo:
            await Bot.send_photo(
                chat_id=str(ADMIN_ID),
                photo=message.photo[-1].file_id,
                caption=user_info + message.caption if message.caption else user_info,
                caption_entities=message.caption_entities
            )
        elif message.video:
            await Bot.send_video(
                chat_id=str(ADMIN_ID),
                video=message.video.file_id,
                caption=user_info + message.caption if message.caption else user_info,
                caption_entities=message.caption_entities
            )
        elif message.document:
            await Bot.send_document(
                chat_id=str(ADMIN_ID),
                document=message.document.file_id,
                caption=user_info + message.caption if message.caption else user_info,
                caption_entities=message.caption_entities
            )
        # Добавьте другие типы медиа по аналогии
        else:
            await Bot.send_message(
                chat_id=str(ADMIN_ID),
                text=user_info + "⚠️ Получен неподдерживаемый тип сообщения"
            )

    except Exception as e:
        logging.error(f"Ошибка пересылки сообщения админу: {e}")

@dp.message(StateFilter(BroadcastState.obrashenie))
async def process_group(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        # Пересылаем сообщение админу
        await forward_to_admin(user_id, message)
        
        # Отправляем подтверждение пользователю
        await message.answer("Спасибо за обратную связь!", reply_markup=main_keyboard)
        
        await admin_sms(user=message.from_user.username,idd=message.from_user.id)
        save(user=message.from_user.username,ID=message.from_user.id)

    except TelegramForbiddenError:
        await message.answer(f"Пользователь {user_id} заблокировал бота.")
    except Exception as e:
        logging.error(f"Ошибка обработки обратной связи: {e}")
    finally:
        await state.clear()

@dp.message(F.text == "Обратная связь")
async def process_group(message: types.Message, state: FSMContext):
    await message.answer(
        "Мы рады услышать тебя! Оставь свои комментарии,вопросы или отзывы, и мы постараемся ответить как можно скорее",
        reply_markup=otmena
    )
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
    await state.set_state(BroadcastState.obrashenie)


@dp.message(F.text == "Нечетная")
@dp.message(F.text == "Четная")
async def process_group(message: types.Message, state: FSMContext):
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
    group = check_file(ID=message.from_user.id)
    if group == "Не введена":
        await message.answer("Для начала введи группу:")
        await state.set_state(BroadcastState.select_group)
        return
    a=-1 #Номера строк
    b=0 #Номера столбцов
    d=0 #номер дня недели
    q=1 #только 1 раз ввести день недели 
    R_3=""
    j=0
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
    day = days[d]
    if message.text == "Четная":
        week_type = "чет"
    else:
        week_type = "неч"
    x = 0 #Только 1 раз ввести и группу и день недели
    number_group = df.iloc[a][df.columns[0]]
    for i in range(6):
        while j == 0:
            try:
                if {str(number_group)} == {str(group)}:
                    day_k = (str(df.iloc[a][df.columns[1]]))[:2]
                    ch_nech = str(df.iloc[a][df.columns[3]])
                    if {ch_nech} == {'nan'}:   
                        ch_nech = "чет/неч"
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech:ch_nech="неч"
                        elif "чет" in ch_nech:ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    spisok_ch_nech="чет/неч"
                    if {str(day_k)} == {str(day)} :
                        if str(ch_nech) == str(week_type) or str(ch_nech) == "чет/неч" or ch_nech not in spisok_ch_nech:
                            time = (str(df.iloc[a][df.columns[2]]))[:5]
                            para = df.iloc[a][df.columns[4]]
                            lec_pr = df.iloc[a][df.columns[5]]
                            if lec_pr.startswith("л."):lec_pr=lec_pr[:4]  
                            elif lec_pr.startswith("лек"):lec_pr=lec_pr[:3] 
                            elif lec_pr.startswith("пр"):lec_pr=lec_pr[:2]
                            kab = df.iloc[a][df.columns[6]]
                            zdanie = str(df.iloc[a][df.columns[7]])
                            if zdanie.startswith("КСК"):  # Проверяем, начинается ли строка с "КСК"
                                zdanie=zdanie[:3]
                            kab=str(kab)
                            if kab.startswith("КСК КАИ ОЛИМП"):  # Проверяем, начинается ли строка с "КСК"
                                kab=kab[:13]
                            else:
                                kab=kab[:4]
                            prepod = df.iloc[a][df.columns[9]]
                            if x == 0:
                                day_k = days_mapping[day_k]
                                R_1=f"➤{day_k}\n➤{group}\n➤{ch_nech}\n\n"
                                x=x+1
                            else:
                                if q==0:
                                    day_k = days_mapping[day_k]
                                    R_1=f"➤{day_k}\n"
                                    q=q+1
                                else:
                                    R_1=''
                            R_2=f"{R_1}➤ <b>{ch_nech}</b> 🕘 <b>{time}</b>\n<b>{para}</b>({lec_pr})\n{kab}_{zdanie}зд.\n{prepod}"
                            R_3=f"{R_3}\n{R_2}"
                a=a+1
                number_group = df.iloc[a][df.columns[0]] 
            except IndexError as e:
                print("Конец")
                print(week_type)
                j=1 
                q=0
                
                a=-1
        try:
            await message.answer(R_3, parse_mode='HTML')   
        except Exception as e:
            vvv=f"➤{days_mapping[day]}\n\nЗанятий нет"
            await message.answer(vvv, parse_mode='HTML')   
        d=d+1
        j=0
        R_3=""
        days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
        try:
            day = days[d]
        except:
            x=x
dn=""
@dp.message(F.text == "⬇️ Неч ⬇️")
@dp.message(F.text == "⬇️ Чет ⬇️")
async def process_group(message: types.Message, state: FSMContext):
    if message.text=="⬇️ Неч ⬇️":
        dn ="чет"
        ch_spis[message.from_user.id] = dn
        dn=ch_spis[message.from_user.id]
        await message.answer(f"Тип недели изменен на Четная ✅",reply_markup=ch_days_of_week_keyboard)
    elif message.text=="⬇️ Чет ⬇️":
        dn ="неч"
        ch_spis[message.from_user.id] = dn
        dn=ch_spis[message.from_user.id]
        await message.answer(f"Тип недели изменен на Нечетная ✅",reply_markup=nech_days_of_week_keyboard)

        


@dp.message(F.text == "День недели")
async def process_group(message: types.Message, state: FSMContext):
    start_date = datetime(2025, 1, 20)
    time_shift = timedelta(hours=3)
    today = datetime.now() + time_shift
    weeks_difference = (today - start_date).days // 7
    if today < start_date:
        week_type = "неделя не определена до 20.01.2025"
    else:
        week_type = "Четная" if weeks_difference % 2 == 0 else "Нечетная"
    if week_type == "Четная":
        await message.answer("Выбери день недели",reply_markup=ch_days_of_week_keyboard)
        dn ="чет"
        ch_spis[message.from_user.id] = dn
        dn=ch_spis[message.from_user.id]
    else:
        await message.answer("Выбери день недели",reply_markup=nech_days_of_week_keyboard)
        dn ="неч"
        ch_spis[message.from_user.id] = dn
        dn=ch_spis[message.from_user.id]
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)


@dp.message((F.text).lower() == "iluz")
async def process_group(message: types.Message, state: FSMContext):
        global ADMIN_ID2
        global ADMIN_ID
        if message.from_user.id == ADMIN_ID or message.from_user.id == ADMIN_ID2:
            await message.answer("Добро пожаловать в ADMIN панель",reply_markup=admin_panel)

@dp.message(F.text == 'Сообщение пользователю')
async def start(message: types.Message, state: FSMContext):
    global ADMIN_ID2
    global ADMIN_ID
    if message.from_user.id == ADMIN_ID or message.from_user.id == ADMIN_ID2:
        await message.answer("Введи ID пользователя")
        await state.set_state(BroadcastState.Message_from_human)

@dp.message(StateFilter(BroadcastState.Message_from_human))
async def start(message: types.Message, state: FSMContext):
    global id_pip
    id_pip=message.text
    await message.answer("Введи текст который хочешь отправить пользователю")
    await state.clear()
    await state.set_state(BroadcastState.Message_from_human2)

@dp.message(StateFilter(BroadcastState.Message_from_human2))
async def start(message: types.Message, state: FSMContext):
    try:
        await Bot.send_message(id_pip, f"Сообщение от Администратора:\n{message.text}")
        await message.answer("Сообщение отправленно")
        await state.clear()
    except:
        await message.answer("Ошибка")
        await state.clear()

async def send_message_to_user(user_id, message):
    """Отправляет сообщение пользователю с сохранением форматирования и поддерживает различные типы сообщений."""
    try:
        # Для текстовых сообщений с сущностями (жирный, курсив и т.д.)
        if message.text:
            await Bot.send_message(
                chat_id=user_id,
                text=message.text,
                entities=message.entities
            )
        
        # Фото с подписью и сущностями подписи
        elif message.photo:
            await Bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
        
        # Видео
        elif message.video:
            await Bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
        
        # Голосовые сообщения
        elif message.voice:
            await Bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id
            )
        
        # Документы
        elif message.document:
            await Bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
        
        # Аудио
        elif message.audio:
            await Bot.send_audio(
                chat_id=user_id,
                audio=message.audio.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
        
        # Стикеры
        elif message.sticker:
            await Bot.send_sticker(
                chat_id=user_id,
                sticker=message.sticker.file_id
            )
        
        # Анимации (GIF)
        elif message.animation:
            await Bot.send_animation(
                chat_id=user_id,
                animation=message.animation.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
        
        # Локация
        elif message.location:
            await Bot.send_location(
                chat_id=user_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )
        
        # Контакты
        elif message.contact:
            await Bot.send_contact(
                chat_id=user_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name
            )
        
        # Опросы
        elif message.poll:
            await Bot.send_poll(
                chat_id=user_id,
                question=message.poll.question,
                options=[opt.text for opt in message.poll.options],
                is_anonymous=message.poll.is_anonymous,
                type=message.poll.type
            )
        
        # Неподдерживаемые типы
        else:
            await Bot.send_message(
                chat_id=user_id,
                text='Данный тип сообщений не поддерживается'
            )

    except TelegramForbiddenError:
        await message.answer(f"Пользователь {user_id} заблокировал бота.")
    except TelegramBadRequest as e:
        await message.answer(f"Ошибка отправки пользователю {user_id}")
    except Exception as e:
        await message.answer(f"Неизвестная ошибка при отправке пользователю {user_id}")


async def broadcast_message(message: types.Message, state: FSMContext, bot_message):
    """Рассылает сообщение всем пользователям"""
    await message.answer("Начинаю рассылку...")
    with open("users.txt","r") as file:
        lines = file.readlines()
    for user_id in lines:
        await send_message_to_user(user_id, bot_message)
        await asyncio.sleep(0.2)  # Задержка что бы не заблочили бота
    await message.answer("Рассылка завершена!")


@dp.message(F.text == "Рассылка")
async def start_broadcast_handler(message: types.Message, state: FSMContext):
    """Обработчик команды /send_broadcast"""
    if message.from_user.id != ADMIN_ID:
        print("return")
    await message.answer("Отправьте мне сообщение, которое вы хотите разослать пользователям:")
    await state.set_state(BroadcastState.waiting_for_message)  # Переключаем бота в состояние ожидания сообщения для рассылки
@dp.message(StateFilter(BroadcastState.waiting_for_message))
async def get_broadcast_message_handler(message: types.Message, state: FSMContext):
    """Получение сообщения для рассылки"""
    if message.from_user.id != ADMIN_ID:
        print("return")
    await state.update_data(message_to_broadcast=message)  # Сохраняем сообщение
    await message.answer(
        f"Вы хотите отправить следующее сообщение пользователям:\n{message.text if message.text else 'Фото или другой тип сообщения'}\n\nНажмите /confirm для подтверждения или отправьте другое сообщение, чтобы изменить")
    await state.set_state(BroadcastState.waiting_for_confirmation)  # Переключаем бота в состояние ожидания подтверждения


@dp.message(Command("confirm"), StateFilter(BroadcastState.waiting_for_confirmation))
async def confirm_broadcast_handler(message: types.Message, state: FSMContext):
    """Обработка подтверждения рассылки"""
    if message.from_user.id != ADMIN_ID:
        print("return")
    data = await state.get_data()
    message_to_broadcast = data.get("message_to_broadcast")
    await broadcast_message(message, state, message_to_broadcast)  # Вызываем функцию рассылки
    await state.clear()  # Очищаем состояние

@dp.message(lambda message: message.text == "Поменять файл")
async def process_change_file(message: types.Message, state: FSMContext):
    global ADMIN_ID2
    global ADMIN_ID
    if message.from_user.id == ADMIN_ID or message.from_user.id == ADMIN_ID2:
        global waiting_for_file
        if not waiting_for_file:
            waiting_for_file = 1
            await message.reply("Пожалуйста, отправьте файл.")
            await state.set_state(BroadcastState.iluz)
        else:
            await message.reply("Вы уже находитесь в процессе изменения файла. Пожалуйста, отправьте файл.")


@dp.message(F.content_type.in_({'document', 'file', 'video', 'video_note', 'audio'}),StateFilter(BroadcastState.iluz))
async def handle_file(message: types.Message, state: FSMContext):
    global ADMIN_ID2
    global ADMIN_ID
    if message.from_user.id == ADMIN_ID or message.from_user.id == ADMIN_ID2:
        global waiting_for_file
        global file_path
        global df

        if waiting_for_file == 1:
            # Получаем документ
            document = message.document  
            file_id = document.file_id

            # Получаем файл
            file = await Bot.get_file(file_id)

            # Создаем имя файла с указанным путем
            file_path = 'file.xlsx'  # Указываем путь для сохранения файла

            # Загружаем файл
            await Bot.download_file(file.file_path, file_path)

            # Предполагаем, что файл Excel корректный и загружаем его
            try:
                df = pd.read_excel(file_path)
                await message.reply("Файл успешно сохранён как 'file.xlsx'.")
                waiting_for_file = 0
                await state.clear()
            except Exception as e:
                await message.reply(f"Ошибка при чтении файла: {e}")
                waiting_for_file = 0
                await state.clear()

@dp.message(F.text == "id участников")
async def process_group(message: types.Message, state: FSMContext):
    global ADMIN_ID
    global ADMIN_ID2
    await message.answer_document(types.FSInputFile("user_new.txt"))
    await message.answer_document(types.FSInputFile("users.txt"))
            
                

@dp.message(F.text == "Преподаватели")
async def process_group(message: types.Message, state: FSMContext):
    group = check_file(ID=message.from_user.id)
    if group == "Не введена":
        await message.answer("Для начала введи группу:")
        await state.set_state(BroadcastState.select_group)
        return
    a=-1 #Номера строк
    b=0 #Номера 
    Type_spis=[]
    prepod_spis=[]
    para_spis=[]
    anser=f"➤Преподаватели\n"
    Rw_spis=[]
    h=[] #тест
    while True:
        try:
            number_group = df.iloc[a][df.columns[0]]
            if {str(number_group)} == {str(group)}:
                para = df.iloc[a][df.columns[4]]
                type = df.iloc[a][df.columns[5]]
                if type.startswith("л."):
                    type=type[:4]  # Оставляем первые 4 символа
                elif type.startswith("лек"):
                    type=type[:3]  # Оставляем первые 3 символа
                elif type.startswith("пр"):
                    type=type[:2]  
                para_spis.append(para)
                b=b+4
                prepod = df.iloc[a][df.columns[9]]
                prepod = ' '.join(word.capitalize() for word in prepod.lower().split())
                Rw=f"▎• <b>{para}({type})</b>\n   {prepod}\n"
                if str(Rw) not in Rw_spis:
                    Rw_spis.append(str(Rw))
                    Rw=str(Rw)
                    h.append(Rw)
            a=a+1
        except IndexError as e:
            print("Конец")
            break 
    sorted_h = sorted(h, key=lambda x: x[1:])
    sorted_h = [anser] + sorted_h
    first_sorted_h = sorted_h[:25]
    second_sorted_h = sorted_h[25:]
    first_sorted_h = '\n'.join(first_sorted_h)
    second_sorted_h = '\n'.join(second_sorted_h)
    await message.answer(first_sorted_h, parse_mode='HTML')
    await message.answer(second_sorted_h, parse_mode='HTML')
@dp.message(F.text == "Какая неделя")
async def process_group(message: types.Message, state: FSMContext):
    start_date = datetime(2025, 1, 20)
    time_shift = timedelta(hours=3)
    today = datetime.now() + time_shift
    weeks_difference = (today - start_date).days // 7
    if today < start_date:
        week_type = "неделя не определена до 20.01.2025"
    else:
        week_type = "Четная" if weeks_difference % 2 == 0 else "Нечетная"
    await message.answer(week_type)
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)


@dp.message(F.text == "Завтра")
@dp.message(F.text == "Сегодня")
async def process_group(message: types.Message, state: FSMContext):
    group = check_file(ID=message.from_user.id)
    if group == "Не введена":
        await message.answer("Для начала введи группу:")
        await state.set_state(BroadcastState.select_group)
        return
    if message.text == "Сегодня":
        dayss=0
    elif message.text == "Завтра":
        dayss=1
    tomorrow = datetime.now() + timedelta(days=dayss)
    tomorrow_str = tomorrow.strftime('%d.%m')
    a=-1 #Номера строк
    b=0 #Номера столбцов
    d=0 #номер дня недели
    q=1 #только 1 раз ввести день недели 
    R_3=""
    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz)
    tomorrow = today + timedelta(0)
    day_of_week = tomorrow.weekday()
    
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    t_day = days[day_of_week]
    tomorrow = today + timedelta(dayss)
    day_of_week = tomorrow.weekday()
    
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    day = days[day_of_week]
    if day == "вс":
        await message.answer("Выходной получается")
    else:
        number_group = df.iloc[a][df.columns[1]]
        start_date = datetime(2025, 1, 20)
        time_shift = timedelta(hours=3)
        today = datetime.now() + time_shift
        weeks_difference = (today - start_date).days // 7
        if today < start_date:
            week_type = "неделя не определена до 20.01.2025"
        else:
            week_type = "чет" if weeks_difference % 2 == 0 else "неч"
        x = 0
        a=0
        b=0
        if message.text == "Завтра" and t_day == "вс":
            if week_type == "чет":
                week_type = "неч"
            else:
                week_type = "чет"
        number_group = df.iloc[a][df.columns[0]]

        while True:
            try:
                if {str(number_group)} == {str(group)}:
                    day_k = str(df.iloc[a][df.columns[1]])
                    day_k=day_k[:2]
                    ch_nech = df.iloc[a][df.columns[3]]
                    ch_nech=str(ch_nech)
                    global days_mapping
                    if {ch_nech} == {'nan'}:   
                        ch_nech = "чет/неч"
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech:
                            ch_nech="неч"
                        elif "чет" in ch_nech:
                            ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    spisok_ch_nech="чет/неч"
                    if {str(day_k)} == {str(day)} :
                        if str(ch_nech) == str(week_type) or str(ch_nech) == "чет/неч" or ch_nech not in spisok_ch_nech:
                            time = (str(df.iloc[a][df.columns[2]]))[:5]
                            time=str(time)
                            para = df.iloc[a][df.columns[4]]
                            lec_pr = df.iloc[a][df.columns[5]]
                            if lec_pr.startswith("л."):
                                lec_pr=lec_pr[:4]  # Оставляем первые 4 символа
                            elif lec_pr.startswith("лек"):
                                lec_pr=lec_pr[:3]  # Оставляем первые 3 символа
                            elif lec_pr.startswith("пр"):
                                lec_pr=lec_pr[:2]  # Оставляем первые 2 символа
                            kab = df.iloc[a][df.columns[6]]
                            zdanie = df.iloc[a][df.columns[7]]
                            zdanie=str(zdanie)
                            if zdanie.startswith("КСК"):  # Проверяем, начинается ли строка с "КСК"
                                zdanie=zdanie[:3]
                            kab=str(kab)
                            if kab.startswith("КСК КАИ ОЛИМП"):  # Проверяем, начинается ли строка с "КСК"
                                kab=kab[:13]
                            else:
                                kab=kab[:4]
                            b=b+2
                            prepod = df.iloc[a][df.columns[9]]
                            if x == 0:
                                day_k = days_mapping[day_k]
                                R_1=f"➤{day_k}\n➤{group}\n➤{week_type}\n\n"
                                x=x+1
                            else:
                                if q==0:
                                    day_k = days_mapping[day_k]
                                    R_1=f"➤{day_k}"
                                else:
                                    R_1=''
                            if tomorrow_str not in ch_nech and "." in ch_nech:
                                a=a+1
                                number_group = df.iloc[a][df.columns[0]]
                                continue

                            R_2=f"{R_1}➤ <b>{ch_nech}</b> 🕘 <b>{time}</b>\n<b>{para}</b>({lec_pr})\n{kab}_{zdanie}зд.\n{prepod}"
                            R_3=f"{R_3}\n{R_2}"
                a=a+1
                number_group = df.iloc[a][df.columns[0]] 
            except IndexError as e:
                break 
                x = 0
        try:
            tomorrow = datetime.now() + timedelta(days=dayss)
            tomorrow_str = tomorrow.strftime('%d.%m.%Y')
            await message.answer(f"Расписание на {tomorrow_str}\n"+R_3, parse_mode='HTML')   
        except Exception as e:
            vvv=f"➤{days_mapping[day]}\n\nЗанятий нет"
            
            await message.answer(vvv, parse_mode='HTML')
        user_id = message.from_user.id
        await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)


@dp.message(lambda message: message.text in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'])
async def process_group(message: types.Message, state: FSMContext):
    group = check_file(ID=message.from_user.id)
    if group == "Не введена":
        await message.answer("Для начала введи группу:")
        await state.set_state(BroadcastState.select_group)
        return
    global day
    global days_mapping
    # Обновляем переменную day в зависимости от нажатой кнопки
    if message.text == 'Понедельник':
        day = 'пн'
    elif message.text == 'Вторник':
        day = 'вт'
    elif message.text == 'Среда':
        day = 'ср'
    elif message.text == 'Четверг':
        day = 'чт'
    elif message.text == 'Пятница':
        day = 'пт'
    elif message.text == 'Суббота':
        day = 'сб'
    a = 0
    b = 0
    a=-1 #Номера строк
    d=0 #номер дня недели
    q=1 #только 1 раз ввести день недели 
    R_3=""
    x = 0
    a=-1
    dn = ch_spis.get(message.from_user.id, "Не введена")
    if dn == "Не введена":
        await message.answer("Ошибка нажми /start")

    number_group = df.iloc[a][df.columns[0]]
    while True:
            try:
                if {str(number_group)} == {str(group)}:
                    day_k = (str(df.iloc[a][df.columns[1]]))[:2]
                    ch_nech = str(df.iloc[a][df.columns[3]])
                    if {str(ch_nech)} == {'nan'}:   
                        ch_nech = "чет/неч"
                    if ch_nech != "чет/неч":
                        if "неч" in ch_nech:
                            ch_nech="неч"
                        elif "чет" in ch_nech:
                            ch_nech="чет"
                        else: ch_nech=ch_nech.strip()
                    spisok_ch_nech="чет/неч"
                    if {str(day_k)} == {str(day)} :
                        if ch_nech == dn or ch_nech == "чет/неч" or ch_nech not in spisok_ch_nech:
                            time = (str(df.iloc[a][df.columns[2]]))[:5]
                            para = df.iloc[a][df.columns[4]]
                            lec_pr = df.iloc[a][df.columns[5]]
                            if lec_pr.startswith("л."):
                                lec_pr=lec_pr[:4]  # Оставляем первые 4 символа
                            elif lec_pr.startswith("лек"):
                                lec_pr=lec_pr[:3]  # Оставляем первые 3 символа
                            elif lec_pr.startswith("пр"):
                                lec_pr=lec_pr[:2]  # Оставляем первые 2 символа
                            kab = df.iloc[a][df.columns[6]]
                            zdanie = str(df.iloc[a][df.columns[7]])
                            if zdanie.startswith("КСК"):  # Проверяем, начинается ли строка с "КСК"
                                zdanie=zdanie[:3]
                            kab=str(kab)
                            if kab.startswith("КСК КАИ ОЛИМП"):  # Проверяем, начинается ли строка с "КСК"
                                kab=kab[:13]
                            else:
                                kab=kab[:4]
                            prepod = df.iloc[a][df.columns[9]]
                            if x == 0:
                                day_k = days_mapping[day_k]
                                R_1=f"➤{day_k}\n➤{group}\n➤{dn}\n\n"
                                x=x+1
                            else:
                                if q==0:
                                    day_k = days_mapping[day_k]
                                    R_1=f"➤{day_k}"
                                else:
                                    R_1=''
                            R_2=f"{R_1}➤ <b>{ch_nech}</b> 🕘 <b>{time}</b>\n<b>{para}</b>({lec_pr})\n{kab}_{zdanie}зд.\n{prepod}"
                            R_3=f"{R_3}\n{R_2}"
                a=a+1
                number_group = df.iloc[a][df.columns[0]] 
            except IndexError as e:
                print("Конец")
                print(dn)
                break 
                x = 0
    await message.answer(R_3, parse_mode='HTML')
    user_id = message.from_user.id
    e_user_new=f"@{message.from_user.username} ID: {user_id}"
    
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)

@dp.message()
async def process_group(message: types.Message):
    await message.answer("Не понимаю тебя, напиши /start")
    user_id = message.from_user.id
    global group
    await admin_sms(user=message.from_user.username,idd=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
    save(user=message.from_user.username,ID=message.from_user.id)
   
async def main():
    await dp.start_polling(Bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        print ('Бот выключен')

