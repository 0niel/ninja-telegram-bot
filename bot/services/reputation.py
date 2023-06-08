import math

from telegram.helpers import escape_markdown

from bot.models.user import User


def compute_force(rep, force) -> float:
    i_min_size = 0.1
    i_max_size = 8

    size_range = i_max_size - i_min_size

    i_min_count = math.log(0 + 1)
    i_max_count = math.log(500 + 1)

    i_count_range = i_max_count - i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if 50 < force < 200:
        force_new = force / 70
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 100

    delta = i_min_size + (math.log(force_new + 1) - i_min_count) * (size_range / i_count_range)

    new_force_delta = rep * delta
    new_force_delta = max(new_force_delta, 0)

    return new_force_delta


def compute_rep(rep, force) -> float:
    i_min_size = 0.5
    i_max_size = 15

    size_range = i_max_size - i_min_size

    i_min_count = math.log(0 + 1)
    i_max_count = math.log(500 + 1)

    i_count_range = i_max_count - i_min_count

    if i_count_range == 0:
        i_count_range = 1

    if 50 < force < 200:
        force_new = force / 20
    elif force >= 200:
        force_new = force / 10
    else:
        force_new = force / 50

    delta = i_min_size + (math.log(force_new + 1) - i_min_count) * (size_range / i_count_range)

    return rep * delta


def get_rating_by_slice(users_slice: list[tuple["User", int]], user_id: int) -> str:
    lines = []

    if users_slice[0][1] != 1:
        lines.append("**. . .**")

    for user in users_slice:
        force = f"{user[0].force:.3f}"
        reputation = f"{user[0].reputation:.3f}"
        line = escape_markdown(
            f'{str(user[1])}. {f"{user[0].first_name} " + (user[0].last_name if user[0].last_name is not None else "")} - {reputation if user[0].reputation >= 0 else f"({reputation})"} репутации и {force} влияния '
        )

        if user[0].id == user_id:
            line = f"*{line}*"

        lines.append(line)

    lines.append("**. . .**")

    return "*Вы в рейтинге:*\n\n" + "\n".join(lines)
