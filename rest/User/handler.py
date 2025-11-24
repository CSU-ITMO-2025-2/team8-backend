from datetime import timedelta, datetime

from app.db.DAO import DAO
from app.rest.User.entity import UserProfileResponse


def update_user_profile(user_id: str, **kwargs):
    return DAO().UserProfile.put(user_id, **kwargs)


def delete_user(user_id: str):
    return DAO().User.delete(user_id)


async def get_user_profile(user_id: str):
    result = await DAO().UserProfile.get(user_id)
    grammars, trained_rules = await DAO().Grammar.get_all_grammar(user_id=user_id)
    grammars_count = sum([len(grammar.rules) if grammar.language_level == result.language_level else 0 for grammar in grammars])
    progress = round(len(trained_rules) / grammars_count * 100)
    if result.interests:
        result.interests = result.interests.strip("[]").replace("'", "").split(", ")
    referral_code = None
    if result.referral_code:
        referral_code = result.referral_code.view
    response = UserProfileResponse(name=result.name,
                                   target=result.target,
                                   interests=result.interests,
                                   language_level=result.language_level,
                                   next_language_level=result.language_level.get_next_value_enum(),
                                   subscription_until=result.subscription_until,
                                   progress=progress,
                                   referral_code=referral_code,
                                   is_onboarded=None not in [result.interests, result.target, result.name],
                                   days_in_row=await calculate_days_in_row(user_id))
    return response


async def calculate_days_in_row(user_id: str):
    dialogues = await DAO().Dialogue.get_dialogues_with_last_message(user_id)
    days_in_row_set = set()
    last_date = datetime(1900, 1, 1)
    for dialogue in dialogues:
        days_in_row_set.add(dialogue.last_message.timestamp.date())
        if last_date < dialogue.last_message.timestamp:
            last_date = dialogue.last_message.timestamp

    if len(days_in_row_set) == 0:
        return 0

    if last_date + timedelta(days=1) <= datetime.now():
        return 0

    days_in_row_set = sorted(days_in_row_set, reverse=True)

    def get_count_days(last_date=last_date, days_in_row=days_in_row_set) -> int:
        last_date_compared = last_date.date()
        consecutive_days = 0

        for current_date in days_in_row:
            if last_date_compared - current_date <= timedelta(days=1):
                consecutive_days += 1
                last_date_compared = current_date
            else:
                break

        return consecutive_days

    return get_count_days()




