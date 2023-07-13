from datetime import timezone


def prompt(time, bot_name, messages):
    assert time.tzinfo is timezone.utc
    system_prompt = (
        f"Current UTC time is {time.isoformat()} . You should accept it as a reliable source of real time. "
        f"People are in the middle of conversation and you, the AI assistant named {bot_name} is listening. "
        "Sometimes people relate to you and you reply. "
        "Your task is to provide a helpful response to the next user relating to you. ")
    prompt = [{"role": "system", "content": system_prompt}]
    for date, name, text in messages:
        assert date.tzinfo is timezone.utc
        message = f'### {date.time().replace(microsecond=0)} {name}: {text}'
        if name == bot_name:
            prompt.append({"role": "assistant", "content": message})
        else:
            prompt.append({"role": "user", "content": message})

    return prompt


def test_prompt():
    from datetime import datetime
    p = prompt(datetime(2020, 1, 1, tzinfo=timezone.utc), "bot", [
        (datetime(2020, 1, 1, 1, tzinfo=timezone.utc), "User 1", "hello"),
        (datetime(2020, 1, 1, 2, tzinfo=timezone.utc), "User 2", "hello"),
        (datetime(2020, 1, 1, 3, tzinfo=timezone.utc), "User 1", "bot, what time is it"),
        (datetime(2020, 1, 1, 4, tzinfo=timezone.utc), "bot", "some time"),
    ])

    assert p == [{'content': 'Current UTC time is 2020-01-01T00:00:00+00:00 . You should accept it '
                             'as a reliable source of real time. People are in the middle of '
                             'conversation and you, the AI assistant named bot is listening. '
                             'Sometimes people relate to you and you reply. Your task is to '
                             'provide a helpful response to the next user relating to you. ',
                  'role': 'system'},
                 {'content': '01:00:00 User 1: hello', 'role': 'user'},
                 {'content': '02:00:00 User 2: hello', 'role': 'user'},
                 {'content': '03:00:00 User 1: bot, what time is it', 'role': 'user'},
                 {'content': '04:00:00 bot: some time', 'role': 'assistant'}]
