import discord
from discord import ButtonStyle
from discord.ui import View, Button


class PaginationView(View):
    def __init__(self, pages):
        super().__init__()
        self.page = 0
        self.pages = pages

        self.add_item(Button(label="<", style=ButtonStyle.green, custom_id="prev"))
        self.add_item(Button(label=">", style=ButtonStyle.green, custom_id="next"))

    @discord.ui.button(custom_id="prev")
    async def prev_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(custom_id="next")
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.page < len(self.pages) - 1:
            self.page += 1
            await interaction.response.edit_message(content=self.pages[self.page])
