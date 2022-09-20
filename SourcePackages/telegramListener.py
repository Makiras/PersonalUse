import telebot
from pdlearn import user as pdu
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os
from queue import Queue
from threading import Thread
from flask import Flask, request, render_template, redirect
import pandalearning as pdl
from pdlearn.mydriver import Mydriver
from pdlearn.pluspush import PlusPushHandler
from pdlearn.exp_catch import exception_catcher
from pdlearn.config import cfg_get, get_env_or_cfg
import gc  # 资源回收

pushmode = get_env_or_cfg("addition.Pushmode", "Pushmode", "0")
token = get_env_or_cfg("addition.telegram.bot_token", "AccessToken", "")
master = get_env_or_cfg("addition.telegram.user_id", "Secret", "")
bot = telebot.TeleBot(token)


app = Flask(__name__, template_folder='static')


def authorize(self):
    """
    验证消息人，防止个人信息泄露
    """
    return str(self.from_user.id) == master


@bot.message_handler(commands=['start'], func=authorize)
def send_welcome(message):
    bot.reply_to(message, "已初始化。 /help 获取帮助。")


@bot.message_handler(commands=['help'], func=authorize)
def get_help(message):
    bot.reply_to(message,
                 "/help 获取帮助\n" +
                 "/learn 开始学习\n" +
                 "/list 获取账号列表\n" +
                 "/add 添加新账号\n" +
                 "/update 更新代码\n"
                 "/token 设置Pushplus Token\n")


@bot.message_handler(commands=['learn'], func=authorize)
@exception_catcher(reserve_fun=bot.reply_to, fun_args=("学习崩溃啦",), args_push=True)
def learn(message):
    params = message.text.split(" ")
    if len(params) > 1:
        pdl.start(params[1] if params[1] else None)
    else:
        users = pdl.get_all_user()
        if len(users) <= 1:
            pdl.start(None)
        else:
            markup = InlineKeyboardMarkup()
            boards = []
            for u in users:
                name = u[1]
                uid = u[0]
                boards.append(InlineKeyboardButton(
                    name, callback_data="LEARN_{}".format(uid)))
            boards.append(InlineKeyboardButton(
                "全部", callback_data="LEARN_ALLUSER"))
            markup.add(*boards)
            bot.send_message(message.chat.id, "请选择开始学习的账号：",
                             reply_markup=markup)


@bot.message_handler(commands=['token'], func=authorize)
@exception_catcher(reserve_fun=bot.reply_to, fun_args=("设置Token崩溃啦",), args_push=True)
def set_token(message):
    params = message.text.split(" ")
    if len(params) > 1:
        pdl.start(params[1] if params[1] else None)
    else:
        users = pdl.get_all_user()
        if len(users) <= 1:
            pdl.start(None)
        else:
            markup = InlineKeyboardMarkup()
            boards = []
            for u in users:
                name = u[1]
                uid = u[0]
                boards.append(InlineKeyboardButton(
                    name, callback_data="TOKEN_{}".format(uid)))
            markup.add(*boards)
            bot.send_message(message.chat.id, "请选择添加PushPlus Token的账号：",
                             reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, "开始学习")
    bot.delete_message(call.message.chat.id, call.message.id)

    if call.data.startswith("LEARN_"):
        uid = call.data.split("_")[1]
        if uid == "ALLUSER":
            pdl.start(None)
        else:
            pdl.start(uid)
    elif call.data.startswith("TOKEN_"):
        uid = call.data.split("_")[1]
        bot.send_message(call.message.chat.id, "请输入PushPlus Token：")
        bot.register_next_step_handler(call.message, set_token_step, uid)


def set_token_step(message, uid):
    push_plus_token = message.text
    if len(push_plus_token) < 5:
        pdu.remove_push_plus_token(uid)
    pdu.save_push_plus_token(uid, push_plus_token)
    bot.send_message(message.chat.id, "设置成功")


@bot.message_handler(commands=['list'], func=authorize)
@exception_catcher(reserve_fun=bot.reply_to, fun_args=("Chrome 崩溃啦",), args_push=True)
def list(message):
    bot.send_chat_action(master, "typing")
    msg = pdl.get_user_list()
    bot.reply_to(message, msg)


@bot.message_handler(commands=['add'], func=authorize)
@exception_catcher(reserve_fun=bot.reply_to, fun_args=("Chrome 崩溃啦",), args_push=True)
def add(message):
    bot.send_chat_action(master, "typing")
    pdl.add_user()


@bot.message_handler(commands=['update'], func=authorize)
def rep_update(message):
    try:
        shell = "git -C /xuexi/code/TechXueXi pull $Sourcepath $pullbranche "
        params = message.text.split(" ")
        if len(params) > 1:
            shell += params[1]
        msg = os.popen(shell).readlines()[-1]
        if "up to date" in msg:
            bot.send_message(message.chat.id, "当前代码已经是最新的了")
        else:
            os.popen("cp -r /xuexi/code/TechXueXi/SourcePackages/* /xuexi")
            bot.send_message(message.chat.id, "代码更新完成"+msg)
    except Exception as e:
        bot.send_message(message.chat.id, "更新失败："+str(e))


@bot.message_handler(commands=['v'], func=authorize)
def rep_update(message):
    bot.reply_to(message, "当前版本：v0.10.29")


def polling():
    try:
        bot.polling(non_stop=True, timeout=120)
    except Exception as e:
        print("telegtram listener reconnecting...")
    finally:  # 资源回收
        gc.collect()  # 资源回收
        polling()


def update_user(q, uid, token=None):
    if token:
        push = PlusPushHandler(token)
    else:
        push = PlusPushHandler(pdu.get_push_plus_token(uid))
    pdl.get_argv()
    driver_login = Mydriver()
    cookies = driver_login.login(q=q)
    driver_login.quit()
    if not cookies:
        push.fttext("你的上次登录超时，失败了。")
        return
    pdu.save_cookies(cookies)
    uid = pdu.get_userId(cookies)
    if token:
        pdu.save_push_plus_token(uid, token)
    user_fullname = pdu.get_fullname(uid)
    pdu.update_last_user(uid)
    push.fttext("你的上次登录成功了！你的ID是：{}，你的名字是：{}".format(uid, user_fullname))


@app.route("/", methods=['GET'])
def learn_to_win():
    return "Let's Learn to win!"


@app.route("/learn", methods=['GET'])
def learn():
    uid = request.args.get("uid")
    if uid is not None:
        full_name = pdu.get_fullname(uid)
        if full_name == "_":
            return "Bad Request", 400
        q = Queue()
        Thread(target=update_user, args=(q, uid, )).start()
        jump_url = q.get(block=True, timeout=20)
        return redirect(jump_url, code=302)
    else:
        html = render_template(
            "tg_login_jump.html", userAction="注册", hasUid="block", userNames="新注册用户")
        return html, 200


@app.route("/learn", methods=['POST'])
def learn_post():
    token = request.form.get("token")
    if len(token) < 5 or token.startswith("http"):
        return "Bad Request", 400
    else:  # new
        q = Queue()
        Thread(target=update_user, args=(q, -1, token, )).start()
        jump_url = q.get(block=True, timeout=20)
        return jump_url, 200


def run_app():
    app.run(debug=False, threaded=True)


if __name__ == '__main__':
    if os.getenv('Nohead') == "True" and pushmode == "5":
        proxy = cfg_get("addition.telegram.proxy")
        if proxy and cfg_get("addition.telegram.use_proxy", False):
            apihelper.proxy = {'http': proxy, 'https': proxy}
            apihelper.CONNECT_TIMEOUT = 120
            try:
                info = bot.get_me()  # 尝试通过代理获取信息
                info.full_name
            except Exception as e:
                apihelper.proxy = {}
                print("代理请求异常，已关闭代理:"+str(e))
        bot.send_message(master, "学习助手上线啦，快来学习吧")
        Thread(target=run_app).start()
        polling()
