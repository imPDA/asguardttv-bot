import discord
import os

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if any(substring in message.content.lower() for substring in
           ['пария', 'парайа', 'париа', 'paria', 'парии', 'парию']):
        stuhn_link = "https://cdn.discordapp.com/attachments/953278284098076672/958658012845838346/pariah.png"
        await message.channel.send(stuhn_link)


if __name__ == '__main__':
    client.run(os.environ['TOKEN'])
