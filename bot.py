from random import randint
import discord
from ast import literal_eval
from datetime import datetime

# channel where information should be output when someone takes an action
OUTPUT_CHANNEL = 1009172034670034974

# if a request is currently being validated, its number will be here
request_being_validated = 000000
# if a request is currently being rebutted, its number will be here
request_being_rebutted = 000000
# if a judge is currently validating a request, his name will be stored here
validating_judge = ""


bot = discord.Bot()

def load_history() -> dict:
    try:
        with open("history.py", 'r') as file:
            history = literal_eval(file.read())
    except FileNotFoundError:
        print("history file not found, creating a new history file")
        with open("history.py", 'w') as file:
            file.write("{}")
            history = {}
    #for request_number in history:
    #    history[request_number]["created_timestamp"] = datetime.fromtimestamp(history[request_number]["created_timestamp"])

    print("Succesfully loaded " + str(len(history)) + " previous trials")
    return history

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.slash_command(name = "create-trial-request", description = "Create a new trial request from a bbcode template.")
async def trial_request(ctx):
    modal = trial_request_modal(title="Create a trial request")
    await ctx.send_modal(modal)

@bot.slash_command(name = "create-trial-request-rebuttal", description = "Create a new trial request rebuttal from a bbcode template.")
async def trial_request_rebuttal(ctx, request_number: int):
    # manage all cases where request should not be rebutted
    if history[request_number]["state"] == "open":
        await ctx.respond("This request has not yet been processed by a judge.", ephemeral=True)
        return
    elif history[request_number]["state"] == "rejected":
        await ctx.respond("This request has been rejected by <@" + str(history[request_number]["judge"]) + "> and therefore can not be rebutted.", ephemeral=True)
        return
    elif history[request_number]["state"] == "rebutted":
        await ctx.respond("This request has been already been rebutted by <@" + str(history[request_number]["prosecutor"]) + "> and therefore can not be processed.", ephemeral=True)
        return

    global request_being_rebutted
    # if another prosecutor is already processing this request
    if request_being_rebutted == request_number:
        await ctx.respond("This request is already being rebutted")
        return
    request_being_rebutted = request_number
    modal = trial_request_rebuttal_modal(title="Create a trial request rebuttal")
    await ctx.send_modal(modal)

@bot.slash_command(name = "validate-trial-request", description = "Accept or reject a trial request as a judge.")
async def validate_trial_request(ctx, request_number: int):
    # first print the details of the ticket
    await request_details(ctx, request_number)
    # check if the request has already been processed
    if history[request_number]["state"] != "open":
        await ctx.respond("This request has already been processed by <@" + str(history[request_number]["judge"]) + "> and can not be validated", ephemeral=True)
        return
    # if not, ask if the user wants to reject or accept it
    global request_being_validated
    request_being_validated = request_number
    await ctx.respond("Please select what to do with this trial request...", view=validate_view(), ephemeral=True)

@bot.slash_command(name = "request-details", description = "Request details of a trial request")
async def request_details(ctx, request_number: int):
    if int(request_number) not in history:
        await ctx.respond("This trial request # does not exist", ephemeral=True)

    trial_info = history[int(request_number)]

    if trial_info["state"] == "rejected":
        embed_colour = 0xDC143C
    elif trial_info["state"] == "validated":
        embed_colour = 0x50C878
    else:
        embed_colour = 0x4666FF

    embedVar = discord.Embed(title="Trial request #" + str(request_number) + " details:", description=trial_info["description"])

    # add corresponding colour
    embedVar.color = embed_colour
    
    # add all the fields
    if len(trial_info["defendants"]) == 1:
        title = "Defendant"
        defendant_string = trial_info["defendants"][0]
    else:
        title = "Defendants"
        defendant_string = ", ".join(trial_info["defendants"])

    embedVar.add_field(name=title, value=defendant_string, inline=True)
    if "defense" in trial_info:
        embedVar.add_field(name="Defense", value="<@"+str((trial_info["defense"]))+">", inline=True)
    if "judge" in trial_info:
        embedVar.add_field(name="Judge", value="<@"+str((trial_info["judge"]))+">", inline=True)
    if "prosecutor" in trial_info:
        embedVar.add_field(name="Prosecutor", value="<@"+str((trial_info["judge"]))+">", inline=True)

    # format charges and pleas together
    charges_and_pleas = ""
    for iterator, charge in enumerate(trial_info["charges"]):
        charges_and_pleas += charge + " -> " + trial_info["pleas"][iterator] + "\n"
    # add them
    embedVar.add_field(name="Charges & Pleas", value=charges_and_pleas, inline=False)
    
    # add the timestamp
    if isinstance(trial_info["created_timestamp"], float):
        embedVar.timestamp = datetime.fromtimestamp(trial_info["created_timestamp"])
    else:
        print("something fucked up and you got a non normal timestamp to print")
        embedVar.timestamp = trial_info["created_timestamp"]

    await ctx.respond(embed=embedVar, ephemeral=True)

class validate_view(discord.ui.View):
    @discord.ui.button(label="Cancel", row=0, style=discord.ButtonStyle.secondary)
    async def cancel_button_callback(self, validate_trial_request, interaction):
        await interaction.response.send_message("You cancelled the validation request.", ephemeral=True)
        request_being_validated = 0

    @discord.ui.button(label="Reject", row=0, style=discord.ButtonStyle.danger)
    async def reject_button_callback(self, validate_trial_request, interaction):
        global request_being_validated
        history[request_being_validated]["judge"] = interaction.user.id
        history[request_being_validated]["state"] = "rejected"
        save_history()
        await interaction.response.send_message("You rejected the trial #" + str(request_being_validated), ephemeral=True)
        channel = bot.get_channel(OUTPUT_CHANNEL)
        await channel.send("Judge <@" + str(interaction.user.id) + "> has rejected request #" + str(request_being_validated))
        request_being_validated = 0

    @discord.ui.button(label="Approve", row=0, style=discord.ButtonStyle.success)
    async def accept_button_callback(self, validate_trial_request, interaction):
        global request_being_validated
        history[request_being_validated]["judge"] = interaction.user.id
        history[request_being_validated]["state"] = "validated"
        save_history()
        await interaction.response.send_message("You approved the trial #" + str(request_being_validated), ephemeral=True)
        channel = bot.get_channel(OUTPUT_CHANNEL)
        await channel.send("Judge <@" + str(interaction.user.id) + "> has approved request #" + str(request_being_validated))
        request_being_validated = 0
        
    
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
        evidence = [i.strip() for i in evidence]

        if len(pleas) != len(charges) and len(pleas) > 1:
            await interaction.response.send_message("You need to write the same amount of charges and pleas.", ephemeral=True)

        # if only one plea was entered, spread it out to all the applicable charges
        if len(charges) > 1 and len(pleas) == 1:
            pleas = [pleas[0]] * len(charges)

        py_timestamp = datetime.now()

        request_number = request_number_generator()

        # save data to history
        history[request_number] = {}
        history[request_number]["description"] = description
        history[request_number]["defendants"] = defendants
        history[request_number]["charges"] = charges
        history[request_number]["pleas"] = pleas
        history[request_number]["evidence"] = evidence
        history[request_number]["state"] = "open"
        history[request_number]["defense"] = interaction.user.id
        history[request_number]["created_timestamp"] = py_timestamp.timestamp()

        save_history()

        channel = bot.get_channel(OUTPUT_CHANNEL)
        await channel.send("Defense attorney <@" + str(interaction.user.id) + "> has created trial request #" + str(request_number))

        bbcode = request_bbcode_generator(defendants, description, charges, pleas, evidence, request_number)
        code_snippet = format_to_code(bbcode)
        request_response = "Created request #" + str(request_number) + "\n" + code_snippet
        await interaction.response.send_message(request_response, ephemeral=True)

class trial_request_rebuttal_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Name(s) of the defendant(s) (comma-separated)", required=False))
        self.add_item(discord.ui.InputText(label="Charge(s) (comma-separated)", required=False, style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Evidence required (comma-separated)", required=False, style=discord.InputTextStyle.long))


    async def callback(self, interaction: discord.Interaction):

        defendants = self.children[0].value.split(",")
        prosecutor_charges = self.children[1].value.split(",")
        prosecutor_charges = [i.strip().capitalize() for i in prosecutor_charges]
        evidence = self.children[2].value.split(",")
        if defendants != [""]:
            history[request_being_rebutted]["defendants"] = defendants
        if prosecutor_charges != [""]:
            # if new charges were added, we need to actually compute which ones are new, and which ones aren't
            old_charges = []
            old_pleas = []
            for iterator, charge in enumerate(history[request_being_rebutted]["charges"]):
                if charge in prosecutor_charges:
                    old_charges.append(charge)
                    old_pleas.append(history[request_being_rebutted]["pleas"][iterator])
                    prosecutor_charges.remove(charge)

            charges = old_charges + prosecutor_charges
            pleas = old_pleas + ["New"]*len(prosecutor_charges)

            history[request_being_rebutted]["charges"] = charges
            history[request_being_rebutted]["pleas"] = pleas
        if evidence != [""]:
            evidence = [i.strip() for i in evidence]

            #remove duplicate evidence
            for evidence_item in evidence:
                if evidence_item in history[request_being_rebutted]["evidence"]:
                    evidence.remove(evidence_item)
            
            
            history[request_being_rebutted]["evidence"].append(evidence)
        
        # Add the prosecutor to the case
        history[request_being_rebutted]["prosecutor"] = interaction.user.id

        # Update the state of the ticket
        history[request_being_rebutted]["state"] = "rebutted"

        channel = bot.get_channel(OUTPUT_CHANNEL)
        await channel.send("Prosecutor <@" + str(interaction.user.id) + "> has responded to request #" + str(request_being_rebutted))

        save_history()

        await interaction.response.send_message("Success: ", ephemeral=True)

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
    bbcode += "\n[center][size=150][b]DISTRICT COURT OF GREATER LOS SANTOS[/b][/size][/center]"
    bbcode += "\n[center][size=150][b]LOS SANTOS CRIMINAL COURT DIVISION[/b][/size][/center]"
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

def save_history():
    """Saves any update to the trial history to a file"""
    with open("history.py", 'w') as file:
        file.write(str(history))

# execution starts here:

# load previously created trials from a file
history = load_history()

# run the bot
bot.run("")