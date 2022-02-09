import functools

def is_admin(func):
    @functools.wraps(func)
    async def oops(client,message):
        is_admin = False
        try:
            user = await message.chat.get_member(message.from_user.id)
            admin_strings = ("creator", "administrator")
            if user.status not in admin_strings:
                is_admin = False
            else:
                is_admin = True

        except ValueError:
            is_admin = True
        if is_admin:
            await func(client,message)
        else:
            await message.reply("Only admins can execute this command!")
    return oops

QUEUE = {}


def add_to_queue(chat_id, title, duration, ytlink, playlink, type, quality, thumb):
    if chat_id in QUEUE:
        chat_queue = QUEUE[chat_id]
        chat_queue.append([title, duration, ytlink, playlink, type, quality, thumb])
        return int(len(chat_queue) - 1)
    else:
        QUEUE[chat_id] = [[title, duration, ytlink, playlink, type, quality, thumb]]


def get_queue(chat_id):
    if chat_id in QUEUE:
        chat_queue = QUEUE[chat_id]
        return chat_queue
    else:
        return 0


def pop_an_item(chat_id):
    if chat_id in QUEUE:
        chat_queue = QUEUE[chat_id]
        chat_queue.pop(0)
        return 1
    else:
        return 0


def clear_queue(chat_id):
    if chat_id in QUEUE:
        QUEUE.pop(chat_id)
        return 1
    else:
        return 0
