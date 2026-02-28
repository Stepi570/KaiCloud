
import logging
from pathlib import Path
import os
import random
import asyncio
import sys
from aiogram.fsm.storage.memory import MemoryStorage # type: ignore
from aiogram.types import InputFile # type: ignore
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command # type: ignore
from aiogram.types import LabeledPrice # type: ignore
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.fsm.state import State, StatesGroup # type: ignore
from aiogram.filters import Command, CommandStart, StateFilter # type: ignore
from aiogram.types import InputMediaPhoto

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, Message, InlineKeyboardButton, InlineKeyboardMarkup,PreCheckoutQuery,ContentType, CallbackQuery # type: ignore
from config import *
from db import *

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)
name=""
text=""
photo=""
prise=0
id_product=""
buyid={}
bans_keyboard= InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Забанить', callback_data='ban'),
    InlineKeyboardButton(text='Разбанить', callback_data='unban')],
    [InlineKeyboardButton(text='Все баны', callback_data='allbans'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')]
])

main_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📿 Браслеты', callback_data='bracelets')]
])
otmena_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отмена', callback_data='adminpanel')]
])


reviews_inline_keyboard= InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✉️ Оставить отзыв', callback_data='newreviews')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='home')]
])
admin_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📿 Браслеты', callback_data='bracelets')],
    [InlineKeyboardButton(text='🛠️ Админ', callback_data='adminpanel')]
])

admin_panel_keyboard= InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👤 Пользователи', callback_data='allusers'),
    InlineKeyboardButton(text='🚫 Баны', callback_data='adminbans')],
    [InlineKeyboardButton(text='📿 Товары', callback_data='adminproduct'),InlineKeyboardButton(text='🔎 Найти заказ', callback_data='findorder')],
    [InlineKeyboardButton(text='📗 Таблица', callback_data='table')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='home')]
])
class BroadcastState(StatesGroup):
    create_ban=State()
    delete_ban=State()
    one_new_produckt=State()
    two_new_produckt=State()
    three_new_product = State()
    four_new_product = State()
    changename = State()
    changeinfo = State()
    changephoto = State()
    changeprise = State()
    pay=State()
    find=State()
    human=State()
    newreviews=State()
async def create_users_file():
    x=await all_info()
    if x==[]:
        return True
    with open("users.txt","a")as file:
        for i in x:
            file.write(f"{i[0]} ID: {i[1]} Дата регестрации: {i[2]}\n")
    return False


@dp.message(F.text == "/start", StateFilter('*'))
async def process_start(message: types.Message, state: FSMContext): 
    if message.from_user.id == admin:
        await message.answer("Привет! 👋 Добро пожаловать в наш магазин браслетов ✨. Здесь ты найдёшь стильные и уникальные украшения, которые подчеркнут твою индивидуальность. Если у тебя есть вопросы или хочешь что-то заказать — просто напиши! 😊",reply_markup=admin_inline_keyboard)
    else:
        await message.answer("Привет! 👋 Добро пожаловать в наш магазин браслетов ✨. Здесь ты найдёшь стильные и уникальные украшения, которые подчеркнут твою индивидуальность. Если у тебя есть вопросы или хочешь что-то заказать — просто напиши! 😊",reply_markup=main_inline_keyboard)
    if await check_new_people(message.from_user.id,message.from_user.username):
        await bot.send_message(admin,f"Новый пользователь @{message.from_user.username}\nID: {message.from_user.id}")
    await state.clear()

@dp.message(StateFilter(BroadcastState.newreviews),F.text)
async def handle_photo(message: Message, state: FSMContext):
    pass

@dp.message(StateFilter(BroadcastState.find),F.text)
async def handle_photo(message: Message, state: FSMContext):
    all_info=await all_from_transaction_id(message.text)
    await message.answer(f"ID транзакции: {all_info[0]}\nID человека: {all_info[1]}\nЮзернейм: {all_info[5]}\nТранзакция: {"Подтверждено" if all_info[2]=="paid" else ("Не обработано" if all_info[2]=="created" else "Откланено")}\nСумма: {all_info[3]}₽\nНазвание товара: {all_info[6]}")
    await message.answer("Получается Админка, смотри на нижние пункты ⬇️",reply_markup=admin_panel_keyboard)
    await state.clear()

@dp.message(StateFilter(BroadcastState.pay), F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]  # Берем самую качественную версию
    file_id = photo.file_id
    info_from_zakaz=buyid[message.from_user.id]
    info_from_zakaz=await all_information_from_product(info_from_zakaz)
    id=await new_payment(message.from_user.id,info_from_zakaz[2],buyid[message.from_user.id])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтвердить ✅', callback_data=f'payment_{id}')],
    [InlineKeyboardButton(text='Откланить ❌', callback_data=f'unpayment_{id}')]])
    await bot.send_photo(
    chat_id=admin,  # Используйте вашу переменную с ID админа
    photo=file_id,
    caption=f"Человек оплатил заказ\n"
        f"@{message.from_user.username or 'нет username'}\n"
        f"ID: {message.from_user.id}\n"
        f"Товар: {info_from_zakaz[0]}\n"
        f"Цена: {info_from_zakaz[2]}₽\n\n"
        f"Проверьте оплату и подтвердите если оплата прошла",reply_markup=keyboard)
    await message.answer("✅ Отлино! Ожидаем подтверждения оплаты")
    await state.clear()


@dp.message(F.text,StateFilter(BroadcastState.changename))
async def process_start(message: types.Message, state: FSMContext):
    global id_product
    await change_name(id_product,message.text)
    await message.answer(f"Изменения вступили в силу")
    tovars=await all_product()
    product_list=[]
    for i in tovars:
        product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
    product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
    await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)
    await state.clear()

@dp.message(F.text,StateFilter(BroadcastState.changeinfo))
async def process_start(message: types.Message, state: FSMContext):
    global id_product
    await change_information(id_product,message.text)
    await message.answer(f"Изменения вступили в силу")
    tovars=await all_product()
    product_list=[]
    for i in tovars:
        product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
    product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
    await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)
    await state.clear()

@dp.message(F.text,StateFilter(BroadcastState.changeprise))
async def process_start(message: types.Message, state: FSMContext):
    await state.clear()
    global id_product
    try:
        d=int(message.text)
        if d<0:
            await message.answer("Число не может быть меньше нуля")
            return
    except:
        await message.answer("Неверный формат")
        return
    await change_price(id_product,message.text)
    await message.answer(f"Изменения вступили в силу")
    tovars=await all_product()
    product_list=[]
    for i in tovars:
        product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
    product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
    await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)
    await state.clear()

@dp.message(F.photo,StateFilter(BroadcastState.changephoto))
async def process_start(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    global id_product
    await change_photo(id_product,photo_id)
    await state.clear()
    await message.answer(f"Изменения вступили в силу")
    tovars=await all_product()
    product_list=[]
    for i in tovars:
        product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
    product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
    await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)


@dp.message(F.text,StateFilter(BroadcastState.one_new_produckt))
async def process_start(message: types.Message, state: FSMContext):
    global name
    name=message.text
    await state.clear()
    await message.answer("Отлично!Теперь пришлите описание")
    await state.set_state(BroadcastState.two_new_produckt)

@dp.message(F.text,StateFilter(BroadcastState.two_new_produckt))
async def process_start(message: types.Message, state: FSMContext):
    global text
    text=message.text
    await state.clear()
    await message.answer("Отлично!Теперь пришлите фотографию")
    await state.set_state(BroadcastState.three_new_product)

@dp.message(F.photo,StateFilter(BroadcastState.three_new_product))
async def process_start(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    global photo
    photo=photo_id
    await state.clear()
    await message.answer("Отлично!Теперь пришлите цену просто цифрой, например 520")
    await state.set_state(BroadcastState.four_new_product)

@dp.message(F.text,StateFilter(BroadcastState.four_new_product))
async def process_start(message: types.Message, state: FSMContext):
    global prise,name,text,photo
    try:prise=int(message.text)
    except:
        await message.answer("Неверный формат")
        return
    if prise <0:
        await message.answer("Число не может быть меньше нуля")
        return
    await new_product(name,text,photo,prise)
    await state.clear()
    await message.answer(f"Готово товар '{name}' добавлен")
    tovars=await all_product()
    product_list=[]
    for i in tovars:
        product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
    product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
    await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)

@dp.message(F.text,StateFilter(BroadcastState.create_ban))
async def process_start(message: types.Message, state: FSMContext):
    if "_" not in message.text or (message.text).count('_')!=1:
        await message.answer("Не правильный формат")
        return
    x,y=(message.text).split("_")
    if await check_user(x):
        await message.answer("Человека с таким id нет")
        return
    if admin==int(x):
        await message.answer("Нельзя блокировать Админа")
        return
    await new_ban(x,y)
    await message.answer(f"Человек {x} забанен по причине {y}")
    await message.answer("Раздел блокировок людей",reply_markup=bans_keyboard)
    await state.clear()


@dp.message(F.text,StateFilter(BroadcastState.delete_ban))
async def process_start(message: types.Message, state: FSMContext):
    if await check_ban(message.text):
        await message.answer("Такой человек не забанен")
        return
    await delete_people_from_ban(message.text)
    await message.answer(f"Человек {message.text} разбанен")
    await message.answer("Раздел блокировок людей",reply_markup=bans_keyboard)
    await state.clear()

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not await check_ban(callback_query.message.chat.id):
        await bot.send_message(callback_query.message.chat.id,"🚫 Вы были заблокированны")
        return
    global id_product
    if "_" in (callback_query.data):
        x,y=(callback_query.data).split("_")
    else:
        x=callback_query.data
    if x=='adminpanel':
        await callback_query.message.edit_text("Получается Админка, смотри на нижние пункты ⬇️",reply_markup=admin_panel_keyboard)
        await bot.answer_callback_query(callback_query.id)
        await state.clear()
    elif x=="allusers":
        try:
            await bot.send_message(admin,"Колличество пользователей "+str(await count_people()))
            if await create_users_file():
                await  bot.send_message(admin,"Пользователей нет")
                await bot.answer_callback_query(callback_query.id)
                return
            await bot.send_document(admin,types.FSInputFile("users.txt"))
            os.remove("users.txt")
        except Exception as e:
            await bot.send_message(admin,f"Ошибка {e}")
        await bot.answer_callback_query(callback_query.id)
    elif x=="home":
        if callback_query.from_user.id == admin:
            await callback_query.message.edit_text("Привет! 👋 Добро пожаловать в наш магазин браслетов ✨. Здесь ты найдёшь стильные и уникальные украшения, которые подчеркнут твою индивидуальность. Если у тебя есть вопросы или хочешь что-то заказать — просто напиши! 😊",reply_markup=admin_inline_keyboard)
        else:
            await callback_query.message.edit_text("Привет! 👋 Добро пожаловать в наш магазин браслетов ✨. Здесь ты найдёшь стильные и уникальные украшения, которые подчеркнут твою индивидуальность. Если у тебя есть вопросы или хочешь что-то заказать — просто напиши! 😊",reply_markup=main_inline_keyboard)
        await bot.answer_callback_query(callback_query.id)
    elif x=="adminbans":
        await callback_query.message.edit_text("Раздел блокировок людей",reply_markup=bans_keyboard)
        await bot.answer_callback_query(callback_query.id)
    elif x=="ban":
        await callback_query.message.edit_text("Пожалуйста, введите ID человека и через символ '_' укажите причину бана (она будет видна только вам).\nНапример: 123456789_Спам",reply_markup=otmena_keyboard)
        await state.set_state(BroadcastState.create_ban)
    elif x=="unban":
        await callback_query.message.edit_text("Пожалуйста, введите ID человека которого нужно разбанить",reply_markup=otmena_keyboard)
        await state.set_state(BroadcastState.delete_ban)
    elif x=="allbans":
        bans=await all_bans()
        if bans==[]:
            await bot.send_message(admin,"Вы никого не забанили")
            await bot.answer_callback_query(callback_query.id)
            return
        info_of_bans=[]
        for i in bans:
            info_of_bans.append(f"ID {i[0]} Причина: {i[1]}")
        await bot.send_message(admin,"\n".join(info_of_bans))
        await bot.answer_callback_query(callback_query.id)
    elif x=="adminproduct":
        tovars=await all_product()
        product_list=[]
        for i in tovars:
            product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
        product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
        product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
        try:
            await callback_query.message.edit_text("Выбери товар или добавь новый",reply_markup=product_keyboard)
            await bot.answer_callback_query(callback_query.id)
        except:
            await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)
            await bot.answer_callback_query(callback_query.id)
    elif x=="createnewpost":
        await callback_query.message.edit_text("Товар будет состоять из названия,описания,фотографии и цены.Сначала пришлите название",reply_markup=otmena_keyboard)
        await bot.answer_callback_query(callback_query.id)
        await state.set_state(BroadcastState.one_new_produckt)
    elif x=="bracelets":
        tovars=await all_product()
        if tovars==[]:
            await bot.send_message(callback_query.message.chat.id,"Товаров пока нет 😞")
            await bot.answer_callback_query(callback_query.id)
            return
        keyboard=[]
        for i in tovars:
            keyboard.append([InlineKeyboardButton(text=f'{i[0]}', callback_data=f'prod_{i[1]}')])
        keyboard.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='home')])
        product_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback_query.message.edit_text("Выбери те браслеты котоые тебе приглянулись",reply_markup=product_keyboard)
        except:
            await callback_query.message.delete()
            await bot.send_message(callback_query.message.chat.id,"Выбери те браслеты котоые тебе приглянулись",reply_markup=product_keyboard)
    elif x=="prod":
        tovar=await all_information_from_product(y)
        keyboard= InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='💲 Купить', callback_data=f'buy_{y}')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='bracelets')]
        ])
        await bot.edit_message_media(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        media=InputMediaPhoto(
            media=tovar[3],
            caption=f"{tovar[0]}\n\n{(tovar[1]).replace('<>','\n')}\n\nЦена: {tovar[2]}₽"),
        reply_markup=keyboard)
    elif x=="edit":
        tovar=await all_information_from_product(y)
        keyboard= InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Редактировать название', callback_data=f'changename_{y}')],
            [InlineKeyboardButton(text='Редактировать описание', callback_data=f'changeinfo_{y}')],
            [InlineKeyboardButton(text='Редактировать фотографию', callback_data=f'changephoto_{y}')],
            [InlineKeyboardButton(text='Редактировать цену', callback_data=f'changeprise_{y}')],
            [InlineKeyboardButton(text='Удалить товар', callback_data=f'delete_{y}')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='adminproduct')]
        ])
        await bot.edit_message_media(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        media=InputMediaPhoto(
            media=tovar[3],
            caption=f"{tovar[0]}\n\n{(tovar[1]).replace('<>','\n')}\n\nЦена: {tovar[2]}₽"),
        reply_markup=keyboard)
    elif x=="changename":
        await state.set_state(BroadcastState.changename)
        await callback_query.message.delete()
        await bot.send_message(admin,f"Введи новое имя товара",reply_markup=otmena_keyboard)
        
        id_product=y
    elif x=="changeinfo":
        await state.set_state(BroadcastState.changeinfo)
        await callback_query.message.delete()
        await bot.send_message(admin,f"Введи новое описание товара",reply_markup=otmena_keyboard)
        id_product=y
    elif x=="changephoto":
        await state.set_state(BroadcastState.changephoto)
        await callback_query.message.delete()
        await bot.send_message(admin,f"Пришли новое фото товара",reply_markup=otmena_keyboard)
        id_product=y
    elif x=="changeprise":
        await state.set_state(BroadcastState.changeprise)
        await callback_query.message.delete()
        await bot.send_message(admin,f"Введи новую цену товара просто цифраи например 520",reply_markup=otmena_keyboard)
        id_product=y
    elif x=="delete":
        await callback_query.message.delete()
        await delete_product(y)
        await bot.send_message(admin,f"Товар был удален")
        tovars=await all_product()
        product_list=[]
        for i in tovars:
            product_list.append([InlineKeyboardButton(text=i[0], callback_data=f'edit_{i[1]}')])
        product_list.append([InlineKeyboardButton(text='➕ Добавить товар', callback_data='createnewpost'),InlineKeyboardButton(text='⬅️ Назад', callback_data='adminpanel')])
        product_keyboard = InlineKeyboardMarkup(inline_keyboard=product_list)
        await bot.send_message(admin,"Выбери товар или добавь новый",reply_markup=product_keyboard)
        await bot.answer_callback_query(callback_query.id)
    elif x=="buy":
        tovar=await all_information_from_product(y)
        await callback_query.message.delete()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data=f'prod_{y}')]])
        buyid[callback_query.message.chat.id]=y
        await bot.send_message(callback_query.message.chat.id,f"Оплата товара '{tovar[0]}'\n\nРеквизиты:\n{details}\n\nСумма:{tovar[2]}₽\n\nПосле оплаты товара пришлите в чат скриншот/чек. Обязательно в виде фотографии",reply_markup=keyboard)
        await state.set_state(BroadcastState.pay)
    elif x=="payment":
        i=await update_payment_and_id(y)
        await callback_query.message.delete()
        await bot.send_message(admin,"✅ Оплата подтверждена")
        await bot.send_message(chat_id=i,text=f"🎉 Оплата прошла успешно\nНомер заказа: <code>{y}</code>\nОтправьте ваш номер заказа администратору {admin_username}",parse_mode="HTML")
    elif x=="unpayment":
        i=await un_update_payment_and_id(y)
        await callback_query.message.delete()
        await bot.send_message(admin,"❌ Оплата откланена")
        await bot.send_message(chat_id=i,text=f"❌ Оплата была откланена",parse_mode="HTML")
    elif x=="findorder":
        await callback_query.message.edit_text("Введите номер транзакции:",reply_markup=otmena_keyboard)
        await state.set_state(BroadcastState.find)
    elif x=="table":
        table=await all_payment()
        if table==[]:
            await bot.send_message(admin,f'Пока не было транзакций')
            return
        df = pd.DataFrame(table, columns=['Товар', 'Цена', 'ID Транзакци', 'Статус транзакции', 'User_ID', 'Username'])
        df.to_excel('payments.xlsx', index=False)
        await bot.send_document(admin,document=types.FSInputFile('payments.xlsx'))
        await bot.send_message(admin,f"Статус оплаты:\ndenied - Отклонен\npaid - Подтвержден\ncreated - Неопределен")
        os.remove('payments.xlsx')
        await bot.answer_callback_query(callback_query.id)
    elif x=="reviews":
        await callback_query.message.edit_text("Выберите пункт:",reply_markup=reviews_inline_keyboard)
    elif x=="newreviews":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data=f'reviews')]])
        await callback_query.message.edit_text("Введите отзыв:",reply_markup=keyboard)
        await state.set_state(BroadcastState.newreviews)



async def main():
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nБот успешно выключен')
