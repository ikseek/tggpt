from itertools import groupby


def prompt(bot_name, messages):
    last_user, last_message = messages[-1].split(": ", 1)
    system_prompt = (
        f"People are in the middle of conversation and the AI assistant named {bot_name} is listening. "
        "Sometimes people relate to the AI assistant and he answers. "
        "The conversation history is provided in triple quotes. "
        "The user named {last_user} asks you a question. "
        "Your task is to provide helpful answer to that question only. "
        '"""{history}"""')
    system = system_prompt.format(bot_name=bot_name, history="\n".join(messages[:-1]), last_user=last_user)
    prompt = [{"role": "system", "content": system}, {"role": "user", "content": last_message}]

    return prompt


def test_prompt():
    p = prompt("bot", ["User 1: hello", "User 2: hello", "User 1: bot, what time is it?"])

    assert p == [{'content': 'People are in the middle of conversation and the AI assistant '
                             'named bot is listening. Sometimes people relate to the AI '
                             'assistant and he answers. The conversation text is provided in '
                             'triple quotes. Your task is to provide a helpful answer to the '
                             'next user relating to you."""User 1: hello\n'
                             'User 2: hello"""',
                  'role': 'system'},
                 {'content': 'User 1: bot, what time is it?', 'role': 'user'}]
