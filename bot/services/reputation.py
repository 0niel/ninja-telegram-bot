import math
from typing import List
from telegram.utils.helpers import escape_markdown
from bot.models.user import User


def compute_force(rep, force) -> float:
    i_min_size = 0.1
    i_max_size = 8

    size_range = i_max_size-i_min_size

    i_min_count = math.log(0+1)
    i_max_count = math.log(500+1)

    i_count_range = i_max_count-i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if force > 50 and force < 200:
        force_new = force / 70
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 100

    delta = i_min_size + (math.log(force_new + 1) - i_min_count) * \
        (size_range / i_count_range)

    new_force_delta = rep * delta
    new_force_delta = 0 if new_force_delta < 0 else new_force_delta

    return new_force_delta


def compute_rep(rep, force) -> float:
    i_min_size = 0.5
    i_max_size = 15

    size_range = i_max_size-i_min_size

    i_min_count = math.log(0+1)
    i_max_count = math.log(500+1)

    i_count_range = i_max_count-i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if force > 50 and force < 200:
        force_new = force / 20
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 50

    delta = i_min_size+(math.log(force_new+1) - i_min_count) * \
        (size_range / i_count_range)

    return rep * delta


def get_rating(users: List[User]) -> str:
    if len(users) == 0:
        return 'На данный момент нет активных участников для формирования рейтинга'

    medals = {0: '🥇', 1: '🥈', 2: '🥉'}

    lines = []
    for i in range(len(users)):
        medal = ''
        if i in medals:
            medal = medals[i]

        lines.append(str(i+1) + '. {} - {} репутации и {} влияния {}'.format(
            users[i].first_name + ' ' +
            users[i].last_name if users[i].last_name is not None else '',
            users[i].reputation if users[i].reputation >= 0 else f'({users[i].reputation})', users[i].force, medal))

    return '*Рейтинг:*\n' + escape_markdown('\n'.join(lines))
