from audioop import reverse
from random import randint
import discord
from json import load
from ast import literal_eval

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

@bot.slash_command(name = "request-details", description = "Request details of a trial request")
async def trial_request_rebuttal(ctx, request_number):
    trial_details = history[int(request_number)]
    await ctx.respond(str(trial_details), ephemeral=True)

class trial_request_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Name(s) of the defendant(s) (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Short description of the incident", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Charge(s) (comma-separated)", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Plea(s) (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Evidence required (comma-separated)", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        
        defendants = self.children[0].value.split(",")
        description = self.children[1].value
        charges = self.children[2].value.split(",")
        pleas = self.children[3].value.split(",")
        evidence = self.children[4].value.split(",")

        # clean up lists
        defendants = [i.strip() for i in defendants]
        charges = [i.strip().capitalize() for i in charges]
        pleas = [i.strip().capitalize() for i in pleas]
        evidence = [i.strip().capitalize() for i in evidence]

        if len(pleas) != len(charges) and len(pleas) > 1:
            await interaction.response.send_message("You need to write the same amount of charges and pleas.", ephemeral=True)

        request_number = request_number_generator()
        write_to_history(defendants, description, charges, pleas, evidence, request_number)

        bbcode = request_bbcode_generator(defendants, description, charges, pleas, evidence, request_number)
        code_snippet = format_to_code(bbcode)
        request_response = "Created request #" + str(request_number) + "\n" + code_snippet
        await interaction.response.send_message(request_response, ephemeral=True)

class trial_request_rebuttal_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Full Name(s) of the defendant(s) (comma-separated)", required=False))
        self.add_item(discord.ui.InputText(label="Charge(s) (comma-separated)", required=False, style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Evidence required (comma-separated)", required=False, style=discord.InputTextStyle.long))


    async def callback(self, interaction: discord.Interaction):
        defendants = self.children[0].value.split(",")
        charges = self.children[1].value.split(",")
        evidence = self.children[2].value.split(",")
        await interaction.response.send_message("Success: " + defendants)

def request_bbcode_generator(defendants: list, description: str, charges: list, pleas: list, evidence: list, request_number: int):
    """bbcode generator for trial request templates"""
    
    if len(defendants) > 1:
        plural = "s"
        reverse_plural = ""
    else:
        plural = ""
        reverse_plural = "s"
    
    if len(charges) > 1:
        charge_plural = "s"
    else:
        charge_plural = ""
    


    join_string = "; "
    defendants_list_string = join_string.join(defendants)
    # INTRO section -> partly replace with an image?
    bbcode = "[divbox=lightblue]"
    bbcode += "\n[center][size=150][b]LOS SANTOS DISTRICT COURT[/b][/size][/center]"
    bbcode += "\n[center][size=150][b]DISTRICT OF THE CITY OF LOS SANTOS[/b][/size][/center]"
    bbcode += "\n[list=none][/list]"
    
    bbcode += "\n[divbox=lightblue][float=left][divbox=gold]"
    bbcode += "\n[b]THE STATE OF SAN ANDREAS[/b][list=none][/list][center]v[/center][list=none][/list][b][center]" + defendants_list_string + "[/center][/b]"
    bbcode += "\n[/divbox][/float]"
    
    bbcode += "\n[float=right][divbox=gold]"
    bbcode += "\n[center]BENCH TRIAL REQUEST[/center]"
    bbcode += "\n[center]#" + str(request_number) + "[/center]"
    bbcode += "\n[/divbox]"
    
    bbcode += "\n[/float][color=white][list=none].[/list][list=none].[/list][list=none].[/list][list=none].[/list][/color][/divbox]"

    # DESCRIPTION section
    bbcode += "\n\n[center][b][u]DESCRIPTION[/u][/b][/center]"
    bbcode += "\n" + description

    # CHARGES and PLEAS section
    bbcode += "\n\n[center][b][u]CHARGES & PLEAS[/u][/b][/center]"

    bbcode += "\n[b]" + defendants_list_string + "[/b], claim" + reverse_plural + " defense for the following charge" + charge_plural +  ":"
    bbcode += "\n[list=1]"

    # if only one plea was entered, spread it out to all the applicable charges
    if len(charges) > 1 and len(pleas) == 1:
        pleas = [pleas[0]] * len(charges)

    # list out the charges and pleas
    
    for iterator, charge in enumerate(charges):
        bbcode += "\n[*]For the charge of [b]" + charge + "[/b], the defendant" + plural + " plead" + reverse_plural + " [b][u]" + pleas[iterator] + "[/u][/b]"
    bbcode += "\n[/list]"


    # EVIDENCE section
    bbcode += "\n\n[center][b][u]EVIDENCE[/u][/b][/center]"
    bbcode += "\n[list=0]"

    # list out required evidence
    evidence_increment = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    for iterator, evidence_item in enumerate(evidence):
        bbcode += "\n[*]Exhibit " + evidence_increment[iterator] + ": " + evidence_item

    bbcode += "\n[/list]"
    return bbcode

def rebuttal_bbcode_generator(defendants: list, evidence: list, plea: list, charges: list):
    """bbcode generator for trial request rebuttal templates"""
    pass

def format_to_code(bbcode: str):
    discord_code_snippet = "```html\n" + bbcode + "\n```"
    return discord_code_snippet

def request_number_generator():
    """Generates a unique 6 digit number"""
    # pick a random 6 digit number
    unique_request_number = randint(100000, 999999)
    # as long as the randomly generated number has already been generated before
    while unique_request_number in history:
        # generate a new one
        unique_request_number = randint(100000, 999999)
    return unique_request_number

def write_to_history(defendants: list, description: str, charges: list, pleas: list, evidence: list, request_number: int):
    history[request_number] = {}
    history[request_number]["defendants"] = defendants
    history[request_number]["description"] = description
    history[request_number]["charges"] = charges
    history[request_number]["pleas"] = pleas
    history[request_number]["evidence"] = evidence

    with open("history.py", 'w') as file:
        file.write(str(history))

def load_history():
    with open("history.py", 'r') as file:
        history = literal_eval(file.read())
    print("Succesfully loaded " + str(len(history)) + " previous trials")
    return history


history = load_history()
bot.run("")