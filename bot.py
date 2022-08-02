import discord

bot = discord.Bot()
client = discord.Client()

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.slash_command(name = "create-trial-request", description = "Create a new trial request from a bbcode template.")
async def trial_request(ctx):
    modal = trial_request_modal(title="Create a trial request")
    await ctx.send_modal(modal)

@bot.slash_command(name = "create-trial-request-rebuttal", description = "Create a new trial request rebuttal from a bbcode template.")
async def trial_request_rebuttal(ctx):
    modal = trial_request_rebuttal_modal(title="Create a trial request rebuttal")
    await ctx.send_modal(modal)


class trial_request_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Full Name(s) of the accused (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Short description of the incident", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Charge(s) (comma-separated)", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Plea(s) (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Evidence required (comma-separated)", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        
        accused = self.children[0].value.split(",")
        description = self.children[1].value
        charges = self.children[2].value.split(",")
        plea = self.children[3].value.split(",")
        evidence = self.children[4].value.split(",")

        if len(plea) != len(charges) and len(plea) > 1:
            await interaction.response.send_message("You need to write the same amount of charges and pleas.", ephemeral=True)
        #channel = client.get_channel(664825085516840963) # channel id here
        #await channel.send('Hello @public defenders, a new trial request has been created !')
        await interaction.response.send_message(accused, ephemeral=True)

class trial_request_rebuttal_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Full Name(s) of the accused (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Charge(s) (comma-separated)" , style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Evidence required (comma-separated)", style=discord.InputTextStyle.long))


    async def callback(self, interaction: discord.Interaction):
        accused = self.children[0].value.split(",")
        charges = self.children[1].value.split(",")
        evidence = self.children[2].value.split(",")
        await interaction.response.send_message("Success: " + accused)
        


def request_bbcode_generator(accused: list, description: str, charges: list, plea: list, evidence: list):
    """bbcode generator for trial request templates"""
    if len(accused) > 1:
        plural = "s"
    else:
        plural = ""

    bbcode = ""

def rebuttal_bbcode_generator(accused: list, evidence: list, plea: list, charges: list):
    """bbcode generator for trial request rebuttal templates"""
    pass

bot.run("")