<p align="center">
    <img alt="RestlessFunnelBot" width="700vw" src="https://raw.githubusercontent.com/0dminnimda/RestlessFunnelBot/main/docs/_static/logo_fancy_cooked.svg">
</p>

## ✔ Install

Clone the repo, cd into the directory and run

```console
python -m pip install -e .
```

If you want to install optional dependencies for speedups run this instead

```console
python -m pip install -e .[speedups]
```

## ⚙ Setup

To be able to run the bot you need to have api bot tokens

Here are the instructions how to get them:
- [VK](https://ciricc.github.io/articles/how_to_get_group_token_easy.html)  <!-- (https://dev.vk.com/api/access-token/getting-started#%D0%9A%D0%BB%D1%8E%D1%87%20%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D1%81%D0%BE%D0%BE%D0%B1%D1%89%D0%B5%D1%81%D1%82%D0%B2%D0%B0) -->
- [Discord](https://www.writebots.com/discord-bot-token/)  <!-- https://discordpy.readthedocs.io/en/stable/discord.html -->
- [Telegram](https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token)

When you gathered all of the tokens go to `RestlessFunnelBot` directory and create `secrets.py`  
Copy the contents from `secrets.py-template` and replace `...` with your tokens

> ⚠️ **Don't push tokens into public repositories**

## 🚀 Run

It's just as easy as running a command :0

```console
python -m RestlessFunnelBot
```

## 👔 Official bots

> ⚠️ **Those may work right now ... or may not ... or may stop working forever**

- VK: [restlessfunnelbot](https://vk.com/restlessfunnelbot)
- Discord: [invitation link](https://discord.com/api/oauth2/authorize?client_id=1033399831084937327&permissions=84992&scope=bot)
- Telegram: `@RestlessFunnelBot`
