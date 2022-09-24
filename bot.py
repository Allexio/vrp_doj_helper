
# default libraries
from ast import literal_eval # to read history
from datetime import datetime # to get current time
from os import environ # to read bot auth key from env variables
from random import randint # to generate case numbers
from json import load, dump

# custom libraries
import discord # discord library
from discord.commands import Option

# local source files
from bbcode_generators import *

# version info
VERSION = 0.6

# channel where information should be output when someone takes an action
CIVIL_TRIAL_MANAGEMENT_CHANNEL = 1009172034670034974
CRIMINAL_TRIAL_MANAGEMENT_CHANNEL = 1009172034670034974
RECRUITMENT_CHANNEL = 1005113728586498158

# if a request is currently being validated, its number will be here
request_being_validated = 000000
# if a request is currently being rebutted, its number will be here
request_being_rebutted = 000000
# if a judge is currently validating a request, his name will be stored here
validating_judge = ""

bot = discord.Bot()

def load_data() -> dict:
    # case history
    try:
        with open("data/case_history.json", 'r') as file:
            history = load(file)
    except FileNotFoundError:
        print("Case history file not found, creating a new history file")
        with open("data/case_history.json", 'w') as file:
            file.write("{}")
            history = {}
    print("Succesfully loaded " + str(len(history)) + " previous trials.")

    # attorney registry
    try:
        with open("data/attorney_registry.json", 'r') as file:
            attorney_registry = load(file)
    except FileNotFoundError:
        print("Case history file not found, creating a new history file")
        with open("data/attorney_registry.json", 'w') as file:
            file.write("{}")
            attorney_registry = {}
    print("Succesfully loaded " + str(len(attorney_registry)) + " admitted attorneys.")

    # quiz dictionary
    try:
        with open("data/flash_cards.json", 'r') as file:
            flash_cards = load(file)
    except FileNotFoundError:
        print("Case history file not found, creating a new history file")
        with open("data/flash_cards.json", 'w') as file:
            file.write("{}")
            flash_cards = {}
    print("Succesfully loaded " + str(len(flash_cards)) + " flash cards.")

    return history, attorney_registry, flash_cards

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.slash_command(name = "help", description = "Get some help on using the bot")
async def help(ctx):
    await ctx.respond("Hey there and thanks for using the DoJ template creator. You can contact <@108986791696048128> if you need any information regarding this bot.")

@bot.slash_command(name = "email-recruitment", description = "Create a new application response (validation or rejection) email from a bbcode template.")
async def email_recruitment(ctx):
    modal = recruitment_modal(title="Create an application response email")
    await ctx.send_modal(modal)

@bot.slash_command(name = "email", description = "Create a new email from a bbcode template.")
async def email(ctx):
    modal = email_modal(title="Create a standard email")
    await ctx.send_modal(modal)

@bot.slash_command(name = "admit_attorney", description = "Admit a new attorney, letting them then register.")
async def admit_attorney(ctx, attorney: discord.Option(discord.User)):
    
    if attorney.id in attorney_registry:
        await ctx.respond("This attorney is already admitted.", ephemeral=True)
    else:
        attorney_registry[str(attorney.id)] = {} # add a new line in DB
        save_data("registry")
        await attorney.send("Hi,\nYou have been admitted as an attorney. Please use the `/register` command to fully register.\nThank you")
        await ctx.respond("You have registered  <@" + str(attorney.id) + "> as an admitted attorney.", ephemeral=True)

@bot.slash_command(name = "register", description = "Register as an attorney")
async def register(ctx):
    if str(ctx.author.id) in attorney_registry:
        modal = registration_modal(title="Register as an attorney")
        await ctx.send_modal(modal)
    else:
        await ctx.respond("You have not been admitted and therefore can not register.\nPlease contact your superior if you have been told you have passed the bar exam.", ephemeral=True)

@bot.slash_command(name = "defend", description = "Initiate a new trial request or issue a response with pleas.")
async def defend(ctx, request_number: Option(int, "If case is already created, enter case #", required = False, default = '')):
    modal = trial_request_modal(title="Create a trial request")
    await ctx.send_modal(modal)

@bot.slash_command(name = "civil-trial-request", description = "Request the opening of a new civil trial.")
async def civil_trial_request(ctx):
    modal = civil_request_modal(title="Create a civil trial request")
    await ctx.send_modal(modal)

@bot.slash_command(name = "prosecute", description = "Initiate a new trial request or issue a rebuttal")
async def trial_request_rebuttal(ctx, request_number: Option(str, "If case is already created, enter case #", required = False, default = '')):
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
    await ctx.respond("Please select what to do with this trial request...", view=validate_view(), ephemeral=True, delete_after=3)

@bot.slash_command(name = "info", description = "Request details of a case or user")
async def request_details(ctx, request_number: Option(int, "If you want information on a case, enter case #", required = False), user: Option(discord.User, "If you want information on a user, please select them", required = False)):
    if request_number == None and user == None:
        await ctx.respond("Please select a case # or a user.", ephemeral=True)
        return
    
    # USER INFO
    if request_number == None:
        user_id = str(user.id)
        if user_id not in attorney_registry:
            await ctx.respond("This user is not currently registered.", ephemeral=True)
            return
        
        cases_handled = 0
        # calculate cases handled
        for case in history:
            if "judge" in case and case["judge"] == user.id:
                cases_handled += 1
            if "prosecutor" in case and case["prosecutor"] == user.id:
                cases_handled += 1
            if "defense" in case and case["defense"] == user.id:
                cases_handled += 1

        embedVar = discord.Embed(title=attorney_registry[user_id]["full_name"])
        embedVar.add_field(name="Phone Number", value=attorney_registry[user_id]["phone"], inline=True)
        embedVar.add_field(name="Timezone", value=attorney_registry[user_id]["timezone"], inline=True)
        embedVar.add_field(name="Cases Handled", value=cases_handled, inline=True)


        if "photo_url" in attorney_registry[user_id]:
            embedVar.set_image(url=attorney_registry[user_id]["photo_url"])
        await ctx.respond(embed=embedVar, ephemeral=True)
        return
    

    # CASE INFO
    request_number = str(request_number) # make sure it is string to be able to call it later.

    if request_number not in history:
        await ctx.respond("This trial request # does not exist", ephemeral=True)
        return

    trial_info = history[request_number]

    if trial_info["state"] == "rejected":
        embed_colour = 0xDC143C
    elif trial_info["state"] == "validated":
        embed_colour = 0x50C878
    else:
        embed_colour = 0x4666FF

    embedVar = discord.Embed(title="Trial request #" + request_number + " details:", description=trial_info["description"])

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
    if "plaintiffs" in trial_info:
        embedVar.add_field(name="Plaintiff", value="<@"+str((trial_info["plaintiff"]))+">", inline=True)
    if "defense" in trial_info:
        embedVar.add_field(name="Defense", value="<@"+str((trial_info["defense"]))+">", inline=True)
    if "judge" in trial_info:
        embedVar.add_field(name="Judge", value="<@"+str((trial_info["judge"]))+">", inline=True)
    if "prosecutor" in trial_info:
        embedVar.add_field(name="Prosecutor", value="<@"+str((trial_info["prosecutor"]))+">", inline=True)


    if type == "criminal":
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
        print("Something fucked up and you got a non normal timestamp to print. Congrats.")
        embedVar.timestamp = trial_info["created_timestamp"]

    await ctx.respond(embed=embedVar, ephemeral=True)

class validate_view(discord.ui.View):
    @discord.ui.button(label="Cancel", row=0, style=discord.ButtonStyle.secondary)
    async def cancel_button_callback(self, validate_trial_request, interaction):
        await interaction.response.send_message("You cancelled the validation request.", ephemeral=True)
        global request_being_validated
        request_being_validated = 0

    @discord.ui.button(label="Reject", row=0, style=discord.ButtonStyle.danger)
    async def reject_button_callback(self, validate_trial_request, interaction):
        global request_being_validated
        history[request_being_validated]["judge"] = interaction.user.id
        history[request_being_validated]["state"] = "rejected"
        save_data("history")
        await interaction.response.send_message("You rejected the trial #" + str(request_being_validated), ephemeral=True)
        if history[request_being_validated]["type"] == "criminal":
            channel = bot.get_channel(CRIMINAL_TRIAL_MANAGEMENT_CHANNEL)
        else:
            channel = bot.get_channel(CIVIL_TRIAL_MANAGEMENT_CHANNEL)
        await channel.send("Judge <@" + str(interaction.user.id) + "> has rejected request #" + str(request_being_validated))
        request_being_validated = 0

    @discord.ui.button(label="Approve", row=0, style=discord.ButtonStyle.success)
    async def accept_button_callback(self, validate_trial_request, interaction):
        global request_being_validated
        history[request_being_validated]["judge"] = interaction.user.id
        history[request_being_validated]["state"] = "validated"
        save_data("history")
        await interaction.response.send_message("You approved the trial #" + str(request_being_validated), ephemeral=True)
        if history[request_being_validated]["type"] == "criminal":
            channel = bot.get_channel(CRIMINAL_TRIAL_MANAGEMENT_CHANNEL)
        else:
            channel = bot.get_channel(CIVIL_TRIAL_MANAGEMENT_CHANNEL)
        await channel.send("Judge <@" + str(interaction.user.id) + "> has approved request #" + str(request_being_validated))
        request_being_validated = 0       
    
class email_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Name(s) of the recipient(s)"))
        self.add_item(discord.ui.InputText(label="Topic of the email"))
        self.add_item(discord.ui.InputText(label="Body of the email", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        
        recipient = self.children[0].value
        topic = self.children[1].value
        body = self.children[2].value
        office = interpret_office_name(interaction.user.roles)
        bbcode_email = format_to_code(email_bbcode_generator(recipient, office, topic, body))
        await interaction.response.send_message(bbcode_email, ephemeral=True)

class recruitment_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Name of the candidate"))
        self.add_item(discord.ui.InputText(label="Accept or Reject"))

    async def callback(self, interaction: discord.Interaction):
        office = interpret_office_name(interaction.user.roles)
        candidate = self.children[0].value
        type = self.children[1].value
        if type.lower() in ["validate", "y", "approve", "accept"]:
            type = "recruitment-approval"
            simple_type = " an approval "
        elif type.lower() in ["reject", "n", "deny"]:
            type = "recruitment-denial"
            simple_type = " a rejection "
        else:
            await interaction.response.send_message("Could not understand whether application was denied or accepted.", ephemeral=True)
            return
        
        # generate bbcode
        bbcode_email = format_to_code(email_bbcode_generator(candidate, office, type=type))

        # inform faction management in the recruitment channel
        channel = bot.get_channel(RECRUITMENT_CHANNEL)
        await channel.send("<@" + str(interaction.user.id) + "> has generated" + simple_type + "email for candidate **" + candidate + "**")
        await interaction.response.send_message(bbcode_email, ephemeral=True)

    
class registration_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="First Name"))
        self.add_item(discord.ui.InputText(label="Last Name"))
        self.add_item(discord.ui.InputText(label="Phone number"))
        self.add_item(discord.ui.InputText(label="Timezone in UTC format (ex: UTC+5/UTC-2)"))
        self.add_item(discord.ui.InputText(label="Link to picture", required=False))

    async def callback(self, interaction: discord.Interaction):

        # check phone number is proper format        
        phone = self.children[2].value
        if len(phone) != 6:
            await interaction.response.send_message("You have not provided a valid phone number. Please check and try again.", ephemeral=True)
            return
        
        # check timezone is in proper format
        user_timezone = self.children[3].value
        if user_timezone.startswith("UTC+") or user_timezone.startswith("UTC-"):
            pass
        else:
            await interaction.response.send_message("You have not provided a valid timezone. Please check the provided examples and try again.", ephemeral=True)
            return
        user_id = str(interaction.user.id)

        #TODO: Add private attorney role when a private attorney registers

        attorney_registry[user_id]["full_name"] = self.children[0].value + " " + self.children[1].value
        attorney_registry[user_id]["phone"] = phone
        attorney_registry[user_id]["timezone"] = user_timezone
        attorney_registry[user_id]["photo_url"] = self.children[4].value
        save_data("registry")

        await interaction.response.send_message("You have successfully registered. You can check your info at any time with /info.", ephemeral=True)


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

        request_number = number_generator()

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
        history[request_number]["type"] = "criminal"

        save_data("history")

        channel = bot.get_channel(CRIMINAL_TRIAL_MANAGEMENT_CHANNEL)
        await channel.send("Defense attorney <@" + str(interaction.user.id) + "> has created trial request #" + str(request_number))

        bbcode = request_bbcode_generator(defendants, description, charges, pleas, evidence, request_number)
        code_snippet = format_to_code(bbcode)
        request_response = "Created request #" + str(request_number) + "\n" + code_snippet
        await interaction.response.send_message(request_response, ephemeral=True)


class civil_request_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Name(s) of the plaintiff(s) (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Name(s) of the defendant(s) (comma-separated)"))
        self.add_item(discord.ui.InputText(label="Type (tort/contract)"))
        self.add_item(discord.ui.InputText(label="Short description", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Evidence (comma-separated)", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        
        plaintiffs = self.children[0].value.split(",")
        defendants = self.children[1].value.split(",")
        type = self.children[2].value.lower()
        description = self.children[3].value
        evidence = self.children[4].value.split(",")

        # clean up type and reject non-standard types
        if type == "t" or "tort" in type:
            type = "Tort"
        elif type == "c" or "contract" in type:
            type = "Contract Dispute"
        else:
            await interaction.response.send_message("This type of civil trial does not exist, please select a proper type either \"contract\" or \"tort\".", ephemeral=True)

        # clean up lists
        defendants = [i.strip() for i in defendants]
        plaintiffs = [i.strip() for i in plaintiffs]
        evidence = [i.strip() for i in evidence]

        py_timestamp = datetime.now()

        request_number = number_generator()

        # save data to history
        history[request_number] = {}
        history[request_number]["defendants"] = defendants
        history[request_number]["type"] = type
        history[request_number]["description"] = description
        history[request_number]["evidence"] = evidence
        history[request_number]["state"] = "open"
        history[request_number]["plaintiffs"] = plaintiffs
        history[request_number]["created_timestamp"] = py_timestamp.timestamp()

        save_data("history")

        channel = bot.get_channel(CIVIL_TRIAL_MANAGEMENT_CHANNEL)
        await channel.send("Attorney <@" + str(interaction.user.id) + "> has created civil trial request #" + str(request_number))

        bbcode = civil_request_bbcode_generator(plaintiffs, defendants, description, type, evidence, request_number)
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

        # Save history to file
        save_data("history")

        # Get channel
        channel = bot.get_channel(CRIMINAL_TRIAL_MANAGEMENT_CHANNEL)

        # Get trial start time
        trial_time = int(datetime.now().timestamp()+900)
        await channel.send("<@" + str(interaction.user.id) + ">, <@" + str(history[request_being_rebutted]["defense"]) + ">, <@" + str(history[request_being_rebutted]["judge"]) + "> a trial you are participating in (#" + str(request_being_rebutted) + ") will start <t:" + str(trial_time) + ":R>")

        

        await interaction.response.send_message("You have succesfully responded to request #" + str(request_being_rebutted), ephemeral=True)


def interpret_office_name(user_roles: list):
    """Takes a user's roles and returns the closest matching office name"""

    user_role_names = []
    for role in user_roles:
        user_role_names.append(role.name)

    if "District Attorney" in user_role_names or "Assistant District Attorney" in user_role_names:
        office = "Office of the District Attorney"
    elif "Attorney General" in user_role_names:
        office = "Office of the Attorney General"
    elif "Chief Public Defender" in user_role_names or "Assistant Chief Public Defender" in user_role_names:
        office = "Office of Public Defence"
    elif "Judge" in user_role_names or "Magistrate" in user_role_names:
        office = "Office of the Court of San Andreas"
    elif "Office of Public Defense" in user_role_names:
        office = "Office of Public Defence"
    elif "Office of the District Attorney" in user_role_names:
        office = "Office of the District Attorney"
    else:
        office = "Unknown Office"

    return office

def format_to_code(bbcode: str):
    discord_code_snippet = "```html\n" + bbcode + "\n```"
    return discord_code_snippet

def number_generator():
    """Generates a unique 6 digit number"""
    # pick a random 6 digit number
    unique_request_number = randint(100000, 999999)
    # as long as the randomly generated number has already been generated before
    while unique_request_number in history:
        # generate a new one
        unique_request_number = randint(100000, 999999)
    # make it a string because json can only have strings as keys
    unique_request_number = str(unique_request_number)
    return unique_request_number

def save_data(data_to_save):
    """Saves any update to the trial history to a file"""
    if data_to_save == "history":
        with open("data/case_history.json", 'w') as file:
            dump(history, file)
    elif data_to_save == "registry":
        with open("data/attorney_registry.json", 'w') as file:
            dump(attorney_registry, file)
    elif data_to_save == "flash_cards":
        with open("data/flash_cards.json", 'w') as file:
            dump(flash_cards, file)

# execution starts here:

# load previously created trials from a file
history, attorney_registry, flash_cards = load_data()

try:
    # run the bot
    bot.run(environ['DOJ_BOT'])
except KeyError:
    print("FATAL: Could not find the 'DOJ_BOT' environment variable, please make sure that the environment variable has been properly set and try again.")
