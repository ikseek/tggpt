from itertools import groupby


def prompt(bot_name, messages):
    system_prompt = (
        f"People are in the middle of conversation and you, the AI assistant named {bot_name} is listening. "
        "Sometimes people relate to you and you reply. "
        "Your task is to provide a helpful response to the next user relating to you. ")
    prompt = [{"role": "system", "content": system_prompt}]
    for m in messages:
        if m.startswith(bot_name):
            prompt.append({"role": "assistant", "content": m})
        else:
            prompt.append({"role": "user", "content": m})

    return prompt


def test_prompt():
    p = prompt("bot", ["User 1: hello", "User 2: hello", "User 1: bot, what time is it?"])

    assert p == [{'content': 'People are in the middle of conversation and you, the AI '
                             'assistant named bot is listening. Sometimes people relate to you '
                             'and you reply. Your task is to provide a helpful response to the '
                             'next user relating to you. ',
                  'role': 'system'},
                 {'content': 'User 1: hello', 'role': 'user'},
                 {'content': 'User 2: hello', 'role': 'user'},
                 {'content': 'User 1: bot, what time is it?', 'role': 'user'}]
