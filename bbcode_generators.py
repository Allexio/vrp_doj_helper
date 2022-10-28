from datetime import datetime

def criminal_request_bbcode_generator(defendants: list, description: str, request_number: int, charges: list):
    """bbcode generator for trial request templates"""

    # PREPARATION

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


    # START OF BBCODE
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

    if charges:
        # CHARGES section
        bbcode += "\n\n[center][b][u]CHARGES & PLEAS[/u][/b][/center]"
        bbcode += "\nThe Prosecution would like to charge the defendant" + plural + ":[b]" + defendants_list_string + "[/b] with the following:"
        bbcode += "\n[list=1]"
        
        # list out the charges
        for charge in charges:
            bbcode += "\n[*][b] " + charge + "[/b]"
        bbcode += "\n[/list]"

    return bbcode

def civil_request_bbcode_generator(trial_type: str, defendants: list, description: str, request_number: int, plaintiff: str, plaintiff_attorney: str, plaintiff_attorney_phone: int, contract_number=None):
    """bbcode generator for trial request templates"""

    # PREPARATION

    if len(defendants) > 1:
        plural = "s"
        reverse_plural = ""
    else:
        plural = ""
        reverse_plural = "s"

    join_string = "; "
    defendants_list_string = join_string.join(defendants)


    # START OF BBCODE
    # INTRO section -> partly replace with an image?
    bbcode = "[divbox=white]"
    bbcode += "\n[center][size=150][b]DISTRICT COURT OF GREATER LOS SANTOS[/b][/size][/center]"
    bbcode += "\n[center][size=150][b]LOS SANTOS CIVIL COURT DIVISION[/b][/size][/center]"
    bbcode += "\n[list=none][/list]"
    
    bbcode += "\n[divbox=white][float=left][divbox=lightblue]"
    bbcode += "\n[b]" + plaintiff + "[/b][center]v[/center][b][center]" + defendants_list_string + "[/center][/b]"
    bbcode += "\n[/divbox][/float]"
    
    bbcode += "\n[float=right][divbox=lightblue]"
    bbcode += "\n[center]BENCH TRIAL REQUEST[/center]"
    bbcode += "\n[center]#" + str(request_number) + "[/center]"
    bbcode += "\n[/divbox][/float][color=white][list=none].[/list][list=none].[/list][/color][/divbox][font=Courier New]"
    bbcode += "\n\n\nI, attorney [highlight=yellow]" + plaintiff_attorney + "[/highlight], am on this day filing a lawsuit against [highlight=yellow]"+ defendants_list_string + "[/highlight] on behalf of [highlight=yellow]" + plaintiff + "[/highlight] in relation to the following incident."

    # DESCRIPTION section
    bbcode += "\n\n" + description

    if contract_number:
        bbcode += "\n\n\n\nThe contract in question is registered with the government of San Andreas as contract #" + contract_number

    bbcode += "\n\nRespectfully submitted,"
    bbcode += "\n" + plaintiff_attorney
    bbcode += "\n" + plaintiff_attorney
    bbcode += "[/font]"
    return bbcode


def rebuttal_bbcode_generator(defendants: list, evidence: list, plea: list, charges: list):
    """bbcode generator for trial request rebuttal templates"""
    pass

def email_bbcode_generator(recipient: str, office: str, topic="", body="", type="standard"):
    """bbcode generator for emails"""

    # First obtain date in readable format
    current_datetime = datetime.now()
    day_name = current_datetime.strftime("%A")
    day_number = current_datetime.day
    month = current_datetime.strftime("%B")
    year = current_datetime.year

    if type == "recruitment-approval":
        topic = "APPLICATION APPROVAL"
        body = """Thank you for taking the time to apply to a position at the Department of Justice.
Your application was a pleasure to read and we think that you’d be a good fit for this role.

As a next step, [b]we’d like to invite you to an interview at the Department of Justice offices [/b] where you’ll have the chance to further discuss the position and ask any questions you may have.

To this end, we would like it if you could [b]share your upcoming availability[/b] with us so that we may organise the aforementioned interview.
We will attempt to contact you on the phone number you provided during your application at the time(s) you provide.

We hope to hear from you soon."""

    elif type == "recruitment-denial":
        topic = "APPLICATION DENIAL"
        body = """After careful consideration of your application, [b]we have decided to not go forward with the recruitment process at this time[/b].
This being an important legal faction where attention to detail is key, we expect a certain level of professionalism from our applicants.
Unfortunately your application has not met this threshold.

If you are still inclined to join us, we encourage you to send us another application in three weeks."""

    # surrounding boxes
    bbcode = "[divbox=#005A9C][divbox=#e1eeff]"

    # top left logo
    bbcode += "​[img]https://cdn.discordapp.com/attachments/1009172034670034974/1015896612008116274/DOJSeal160.png[/img]"

    # top right details section
    bbcode += "\n[float=right][align=right]"
    bbcode += "\n[b][size=120]San Andreas Department of Justice[/size][/b]"
    bbcode += "\n[size=115]" + office + "[/size]"
    bbcode += "\n[size=110][u]" + topic + "[/u][/size]"
    bbcode += "\n[size=105][i]" + day_name + ", " + month + " "  + str(day_number) + ", "  + str(year) + "[/i][/size]"
    bbcode += "\n[/align][/float]"

    # recipient + body
    bbcode += "\n[list=none]\n" # increment the body so it's not stuck to left border
    bbcode += "\n\n\n\n" + "Dear [b]" + recipient + "[/b],"
    bbcode += "\n\n" + body # add in the body, either generated or custom
    bbcode += "\n\n\n" + "Regards,"
    bbcode += "\n[/list]" # close the increment

    # close the surrounding boxes
    bbcode += "\n[/divbox][/divbox]"

    return bbcode