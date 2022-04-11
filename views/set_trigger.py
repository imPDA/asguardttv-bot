from discord.ui import View, button, Button
from discord import ButtonStyle, Interaction


class Buttons(View):
    def __init__(self):
        super().__init__()
        self.value = None

    @button(label='Confirm', style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    @button(label='Cancel', style=ButtonStyle.grey)
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()

