import os
import json 
import random 
import time
import re

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from collections import defaultdict 
from itertools import chain, groupby
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from networkx.readwrite import json_graph

PYTHONUNBUFFERED=0

app = Flask(__name__)
app.secret_key = 'dasjil91283jklsa'
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/explanations.html", methods=['GET', 'POST'])
def view_graph():

    bar = view_bars()
    text = create_texts()
    start = random.choice(list(session["list_items"]))

    session["start_time"] = time.time()

    return render_template("explanations.html", 
                            graph=json.dumps(session["graph"]),
                            graph_alt=json.dumps(session["graph_company"]),
                            direction=session["control"],
                            list_items=session["list_items"],
                            data=json.dumps(bar),
                            start_data=start,
                            text=json.dumps(text),
                            setting=session["setting"])        

def create_graphs(recruiter=False):
    truth_values = defaultdict(list)
    li = []

    session["label_reverse"] = {"valt onder" : "is overkoepelend over",
                                "vereist diploma" : "is vereist diploma van",
                                "maximaal diploma" : "is maximaal diploma van",
                                "heeft diploma" : "is diploma van",
                                "werkt binnen industrie" : "is huidige industrie van", 
                                "wil werken in industrie" : "is gewilde industrie van",
                                "werkt binnen type" : "is werktype van", 
                                "heeft vaardigheid" : "vaardigheid in bezit van", 
                                "wil type" : "is gewild type van",
                                "heeft vervuld" : "is vervuld door",

                                "is overkoepelend over" : "valt onder",
                                "is vereist diploma van" : "vereist diploma", 
                                "is maximaal diploma van" : "maximaal diploma",
                                "heeft diploma" : "is diploma van",
                                "is huidige industrie van" : "werkt binnen industrie",
                                "is gewilde industrie van" : "wil werken in industrie",
                                "is huidig type van" : "heeft type",
                                "is gewild type van" : "wil type",
                                "vaardigheid in bezit van" : "heeft vaardigheid",
                                "is vervuld door" : "heeft vervuld"}

    for truth in os.listdir("./data/ground_truth"):
        if ".csv" in truth:
            df = pd.read_csv(f"./data/ground_truth/{truth}", header=None)
            li.append(df)
                    
    truths = pd.concat(li, axis=0, ignore_index=True)
    truth_dict = {key1: dict(group[[1, 2]].values) for key1, group in truths.groupby(0)}

    hits = defaultdict(lambda : defaultdict(lambda : defaultdict))
    misses = defaultdict(lambda : defaultdict(lambda : defaultdict))

    for i in os.listdir("./data/hits"):
        if ".json" in i:
            full = json.load(open(f"./data/hits/{i}", encoding="utf-8"))
            for k, v in full.items():
                g = nx.node_link_graph(v)
                
                hits[i.split(".")[0]][k] = g
                
                    
    for i in os.listdir("./data/misses"):
        if ".json" in i:
            full = json.load(open(f"./data/misses/{i}", encoding="utf-8"))
            for k, v in full.items():
                misses[i.split(".")[0]][k] = nx.node_link_graph(v)   

    if recruiter:
        with open("./data/candidate_explanations_updated.json") as f:
            curr_explanations = json.load(f)

        candidate = draw_graph(truth_dict, 
                               curr_explanations, 
                               "candidate", 
                               hits,
                               misses)

        with open("./data/company_explanations_updated.json") as f:
            curr_explanations = json.load(f)

        company = draw_graph(truth_dict, 
                             curr_explanations, 
                             "company", 
                             hits,
                             misses)

        return candidate, company

    else:
        with open(f"./data/{session['direction']}_explanations_updated.json") as f:
            curr_explanations = json.load(f)

        return draw_graph(truth_dict, 
                          curr_explanations, 
                          session['direction'], 
                          hits,
                          misses)



# @app.route("/view_bars.html", methods=['GET', 'POST'])
def view_bars():

    current_json = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))

    for user in session["graph"]:
        for job in session["graph"][user]:

            for i, dic in enumerate(session["graph"][user][job]["full"]["nodes"]):
                if "color" not in dic:
                    session["graph"][user][job]["full"]["nodes"][i]["color"] = "#777777"
                if "node_type" not in dic:
                    session["graph"][user][job]["full"]["nodes"][i]["node_type"] = "overig"

            for i, dic in enumerate(session["graph"][user][job]["simple"]["nodes"]):
                if "color" not in dic:
                    session["graph"][user][job]["simple"]["nodes"][i]["color"] = "#777777"
                if "node_type" not in dic:
                    session["graph"][user][job]["simple"]["nodes"][i]["node_type"] = "overig"


            data = sorted([(i["label"], i["value"], i["color"]) for i in session["graph"][user][job]["full"]["nodes"]], key = lambda x: x[1])
                
            data_simple = [(k, list(v)) for k, v in groupby([(i["node_type"], i["value"], i["color"]) for i in sorted(session["graph"][user][job]["simple"]["nodes"], 
                                                                                                                    key=lambda x: x["node_type"])], 
                                                            key=lambda x: x[0])]
                
            data_simple = sorted([(k, sum(i[1] for i in v), v[0][2]) for k, v in data_simple], key=lambda x: x[1])
            data_simple = sorted([(j[0], (j[1] / max([i[1] for i in data_simple])) * 10, j[2]) for j in data_simple])
            
            data_company = []
            data_company_simple = []

            if "graph_company" in session and session["graph_company"] and job in session["graph_company"]:
                data_company = sorted([(i["label"], i["value"], i["color"]) for i in session["graph_company"][job][user]["full"]["nodes"]], key = lambda x: x[1])
                data_company_simple = [(k, list(v)) for k, v in groupby([(i["node_type"], i["value"], i["color"]) for i in sorted(session["graph_company"][job][user]["full"]["nodes"], 
                                                                                                                                    key=lambda x: x["node_type"])], 
                                                                        key=lambda x: x[0])]
            
                data_company_simple = sorted([(k, sum(i[1] for i in v), v[0][2]) for k, v in data_company_simple], key=lambda x: x[1])
                data_company_simple = sorted([(j[0], (j[1] / max([i[1] for i in data_company_simple])) * 10, j[2]) for j in data_company_simple])
            


                
            if session["control"] == "company":
                data, data_company = data_company, data

            data = [i for i in data if i[0] not in (user, job)]
            data_simple = [i for i in data_simple if i[0] not in (user, job)]
            data_company = [i for i in data_company if i[0] not in (user, job)]
            data_company_simple = [i for i in data_company_simple if i[0] not in (user, job)] 

            current_json[user][job]["full"]["xdata"] = [str(i[0]) for i in data]
            current_json[user][job]["full"]["ydata"] = [str(np.round(i[1], 2)) for i in data]
            current_json[user][job]["full"]["cdata"] = [str(i[2].upper()) for i in data]
            
            current_json[user][job]["simple"]["xdata"] = [str(i[0]) for i in data_simple]
            current_json[user][job]["simple"]["ydata"] = [str(np.round(i[1], 2)) for i in data_simple]
            current_json[user][job]["simple"]["cdata"] = [str(i[2].upper()) for i in data_simple]
            
            current_json[job][user]["full"]["xdata"] = [str(i[0]) for i in data_company]
            current_json[job][user]["full"]["ydata"] = [str(np.round(i[1], 2)) for i in data_company]
            current_json[job][user]["full"]["cdata"] = [str(i[2].upper()) for i in data_company]

            current_json[job][user]["simple"]["xdata"] = [str(i[0]) for i in data_company_simple]
            current_json[job][user]["simple"]["ydata"] = [str(np.round(i[1], 2)) for i in data_company_simple]
            current_json[job][user]["simple"]["cdata"] = [str(i[2].upper()) for i in data_company_simple]

    return dict(current_json)
                
@app.route("/view_texts.html", methods=['GET', 'POST'])
def view_texts():

    session["email"] = request.form["email"]
    session["vakgebied"] = request.form["vakgebied"]
    session["leeftijd"] = request.form["leeftijd"]
    session["geslacht"] = request.form["geslacht"]

    if request.form['button'] == 'Kandidaat':
        session["direction"] = "candidate"   
        session["control"] = "kandidaat"

        session["graph"] = create_graphs()
        session["graph_company"] = None

    elif request.form['button'] == 'Bedrijfsvertegenwoordiger':            
        session["direction"] = "company"
        session["control"] = "bedrijf"

        session["graph"] = create_graphs()
        session["graph_company"] = None

    else:
        session["control"] = "recruiter"
        session["graph"], session["graph_company"] = create_graphs(recruiter=True)

    return render_template("/view_texts.html",
                           direction=session["control"])


@app.route("/debrief.html", methods=['GET', 'POST'])
def debrief():

    if ("debrief_status" in session) and (session["debrief_status"] == "done"):
        with open(f"results/{session['control']}_{session['email'].split('@')[0]}_{time.time()}.txt", "w+") as f:
            f.write(f"""
                    email: {session['email']}
                    vakgebied: {session["vakgebied"]} 
                    leeftijd: {session["leeftijd"]}
                    geslacht: {session["geslacht"]}
                    type: {session["control"]}

                    eerste_setting: {session['first_setting']}
                    eerste_antwoord: {session['first_selection']}
                    eerste_timing: {session['first_time']}

                    tweede_setting: {session["second_setting"]}
                    tweede_antwoord: {list(request.form.keys())[0]}
                    tweede_timing: {time.time() - session["start_time"]}""")
        
        return render_template("done.html")
    else:
        if session["control"] == "kandidaat":   
            session["graph"] = create_graphs()
            session["graph_company"] = None
        elif session["control"] == "bedrijf":
            session["graph"] = create_graphs()
            session["graph_company"] = None
        else:
            session["graph"], session["graph_company"] = create_graphs(recruiter=True)

        session["debrief_status"] = "done"
        session["first_selection"] = list(request.form.keys())[0]
        session["first_time"] = time.time() - session["start_time"]

        return render_template("/display_information.html",
                               direction=session["control"])


_attrs = dict(id='id', source='source', target='target', key='key')
 
# This is stolen from networkx JSON serialization. It basically just changes what certain keys are.
def node_link_data(G, attrs=_attrs):
    
    multigraph = G.is_multigraph()
    id_ = attrs['id']
    source = attrs['source']
    target = attrs['target']
    
    # Allow 'key' to be omitted from attrs if the graph is not a multigraph.
    key = None if not multigraph else attrs['key']
    if len(set([source, target, key])) < 3:
        raise nx.NetworkXError('Attribute names are not unique.')
        
    data = {}
    data['directed'] = G.is_directed()
    data['multigraph'] = multigraph
    data['graph'] = G.graph
    data['nodes'] = [dict(chain(G.nodes[n].items(), [(id_, n), ('label', n)])) for n in G]
    
    if multigraph:
        data['links'] = [
            dict(chain(d.items(),
                       [('from', u), ('to', v), (key, k)]))
            for u, v, k, d in G.edges(keys=True, data=True)]
    
    else:
        data['links'] = [
            dict(chain(d.items(),
                       [('from', u), ('to', v)]))
            for u, v, d in G.edges(data=True)]
                    
    return data

def draw_graph(truth_dict, curr_explanations, direction, hits, misses):
    # Update setting if needed
    if "setting" not in session:
        session["setting"] = random.choice(["real", "random"])
        session["first_setting"] = session["setting"]
    elif session["setting"] == "real":
        session["setting"] = "random"
        session["second_setting"] = session["setting"]
    else:
        session["setting"] = "real"
        session["second_setting"] = session["setting"]

    CVs = {
        "u4186": {"title": "Naam: Chris de Vries\n\nPersoonlijk Profiel:\nIk ben een enthousiaste financieel assistent met een diploma in economie van ABC Hogeschool. Mijn sterke interesse in financiën en mijn toewijding om financiële processen te begrijpen en te ondersteunen, maken mij een waardevolle aanwinst voor financiële teams. Ik ben vastbesloten om te groeien als financieel professional en mijn bijdrage te leveren aan organisaties.\n\nWerkervaring:\n\n1. Financieel Assistent bij XYZ Finance (2021-heden)\n\t- Als financieel assistent bij XYZ Finance ondersteun ik het team bij verschillende financiële taken. Mijn verantwoordelijkheden omvatten het bijhouden van financiële transacties, het verwerken van facturen en het assisteren bij het opstellen van financiële rapporten.\n\t- Ik werk nauw samen met senior teamleden om financiële gegevens te analyseren en te helpen bij budgetbeheer.\n\n2. Administratief Medewerker bij ABC Retail (2019-2021)\n\t- Als administratief medewerker bij ABC Retail was ik verantwoordelijk voor het verwerken van inkomende bestellingen, het bijhouden van voorraadniveaus en het opstellen van facturen voor klanten.\n\n\t- Mijn nauwkeurigheid en organisatorische vaardigheden waren cruciaal om ervoor te zorgen dat de administratieve processen soepel verliepen.\n\n3. Klantenservicemedewerker bij XYZ Supermarkt (2017-2019)\t- In mijn rol als klantenservicemedewerker bij XYZ Supermarkt stond ik klanten te woord, beantwoordde ik vragen en bood ik ondersteuning bij het afrekenen van aankopen.\n\t- Deze ervaring heeft mijn communicatieve vaardigheden en klantgerichtheid aanzienlijk versterkt.\n\nOpleiding:\nBachelor in Economie aan [Naam van de Hogeschool]\n\nVaardigheden:\n\t- Financiële analyse\t- Boekhouding en financiële rapportage\t- Budgetbeheer\t- Excel en financiële software\t- Communicatieve vaardigheden\n\nHobbies:\nBuiten mijn werk geniet ik van tijd doorbrengen in de natuur, zoals wandelen in het bos en fietsen in de buurt. Ik ben ook een fan van bordspellen en houd van gezellige avonden met vrienden en familie. Het blijven leren en groeien is belangrijk voor mij, dus ik neem graag deel aan online cursussen en workshops om mijn financiële kennis en vaardigheden te verbeteren."},
        "u3033": {"title": "Naam: Sam Appelscha\nErvaringen:\n1. Video Editor bij MediaTech Studios (2018-2019)\n   - Videomontage en bewerking.\n   - Kwaliteitscontrole van video- en audioproducties.\n2. Videoproducer bij Digital Visionaries (2019-2021)\n   - Leiden van videoproductieprojecten.\n   - Samenwerken met het team voor creatieve inhoud.\nOpleiding: Bachelor in Filmproductie aan de Universiteit van Filmstad, Kwalificaties van Effecten- en Futures-industriebeoefenaars\nVaardigheden: Videobewerking, videoproductie, teamwerk"},
        "u3449": {"title": "Naam: Jesse Kusters\nErvaringen:\n1. HR-manager bij Global Enterprises (2018-2019)\n   - Verantwoordelijk voor human resources management.\n   - Coördineren van werving en selectie.\n2. Operationeel Directeur bij Efficiency Solutions (2019-2021)\n   - Leiden van operationele activiteiten.\n   - Toezicht houden op de bedrijfsvoering.\n3. Strategisch Planner bij Future Ventures (2021-heden)\n   - Ontwikkelen van strategische plannen voor groei.\n   - Samenwerken met het leiderschapsteam voor bedrijfsstrategie.\nOpleiding: Bachelor in Bedrijfskunde aan de Universiteit van Zakelijkheid, Master in Strategisch Management aan de Universiteit van Leiderschap\nVaardigheden: HR-management, strategische planning, operationeel beheer"},
        "u2707": {"title": "Naam: Taylor Meijer\nErvaringen:\n1. IT-specialist bij TechGenius (2018-2019)\n   - Ondersteuning bieden bij IT-vraagstukken.\n   - Coördineren van IT-projecten.\n2. Coördinator IT-beheer bij InnovateTech Solutions (2019-2021)\n   - Beheren van IT-infrastructuur.\n   - Samenwerken met teams voor technische oplossingen.\nOpleiding: Bachelor in Informatica aan de Universiteit van TechWorld, Kwalificaties voor Boekhouding\nVaardigheden: IT-beheer, coördinatievermogen, technische oplossingen"},
        "u3961": {"title": "Naam: Noah van der Berg\nErvaringen:\n1. Hoofdingenieur bij Construction Mastermind (2018-2019)\n   - Leiden van bouwprojecten.\n   - Toezicht houden op bouw- en constructiewerkzaamheden.\n2. Projectmanager bij Urban Builders (2019-2021)\n   - Beheren van stedelijke bouwprojecten.\n   - Coördineren van constructieteams.\n3. Bouwcoördinator bij Home Innovations (2021-heden)\n   - Coördineren van renovatieprojecten.\n   - Toezicht houden op kwaliteitscontrole.\nOpleiding: Bachelor in Civiele Techniek aan de Universiteit van Constructopia, Master in Bouwmanagement aan de Universiteit van Urban Planning\nVaardigheden: Bouwmanagement, kwaliteitscontrole, projectcoördinatie"},
        "u2302": {"title": "Naam: Senna de Boer\nErvaringen:\n1. Bedrijfsspecialist bij Business Experts Inc. (2018-2019)\n   - Analyseren van bedrijfsprocessen.\n   - Assisteren bij strategische planning.\n2. Financieel Analist bij Financial Insight Group (2019-2021)\n   - Financiële analyse uitvoeren voor klanten.\n   - Samenwerken aan financiële rapportage.\n3. Marketing Coördinator bij MarketMasters (2021-heden)\n   - Coördineren van marketingcampagnes.\n   - Beheren van klantrelaties.\nOpleiding: Bachelor in Bedrijfskunde aan de Universiteit van Businessville, Kwalificaties van Effecten- en Futures-industriebeoefenaars\nVaardigheden: Bedrijfsanalyse, financiële analyse, marketingcoördinatie"},
        "u2067": {"title": "Naam: Kai Peters\nErvaringen:\n1. Human Resources Manager bij People Power Corp. (2018-2019)\n   - Beheren van HR-activiteiten.\n   - Leiden van personeelsbeheer.\n2. HR Supervisor bij Talent Boosters Ltd. (2019-2021)\n   - Toezicht houden op HR-processen.\n   - Coördineren van training en ontwikkeling.\n3. HR Business Partner bij HR Solutions Inc. (2021-heden)\n   - Samenwerken met bedrijfsleiders voor HR-strategieën.\n   - Adviseren van het leiderschapsteam over personeelszaken.\nOpleiding: Bachelor in Human Resource Management aan de Universiteit van HRville, Master in Organisatieontwikkeling aan de Universiteit van Leiderschap\nVaardigheden: HR-management, strategische planning, training en ontwikkeling"},
        "u1429": {"title": "Naam: Bobby van Dijk\nErvaringen:\n1. Administratief Coördinator bij Office Prodigy (2018-2019)\n   - Coördineren van administratieve processen.\n   - Beheren van kantooractiviteiten.\n2. Documentatie Specialist bij DocuSolutions (2019-2021)\n   - Beheren van documentatieprocessen.\n   - Ondersteunen bij gegevensinvoer en -analyse.\n3. Office Manager bij Office Dynamics (2021-heden)\n   - Beheren van kantoorfaciliteiten en personeel.\n   - Coördineren van evenementen en vergaderingen.\nOpleiding: Bachelor in Bedrijfskunde aan de Universiteit van Businessville, Kwalificaties voor Administratieve Professionals\nVaardigheden: Administratieve coördinatie, documentatiebeheer, kantoorbeheer"},
        "u4171": {"title": "Naam: Robin Boomsma\nErvaringen:\n1. Human Resources Manager bij Nationale Administratieve Zaken Corp. (2018-2019)\n   - Verantwoordelijk voor personeelsbeheer en -coördinatie.\n   - Coördineren van administratieve processen.\n2. Operationeel Supervisor bij Prestatiebeheer Solutions (2019-2021)\n   - Toezicht houden op operationele activiteiten.\n   - Beheren van prestatiebeheerprocessen.\n3. Coördinator van Activiteiten bij Zakelijke Afdeling Experts (2021-heden)\n   - Coördineren van zakelijke evenementen en activiteiten.\n   - Beheren van klantrelaties en ondersteunen bij administratie.\nOpleiding: Bachelor in Human Resource Management, Certificaten in Administratieve Zaken en Inkoop\nVaardigheden: HR-management, administratieve coördinatie, klantrelaties"},
        "u346":  {"title": "Naam: Bowie van den Beek\nErvaringen:\n1. Analist bij Bouwtechniek Experts (2018-2019)\n   - Analyseren van bouwprojecten en technische gegevens.\n   - Coördineren van bouwtechnische processen.\n2. Teamleider bij Veiligheid & Onderwijs Solutions (2019-2021)\n   - Leiden van een team van veiligheidsexperts en trainers.\n   - Coördineren van educatieve programma's.\n3. Communicatie Specialist bij Bouwplaats Services (2021-heden)\n   - Beheren van communicatie op bouwplaatsen.\n   - Ondersteuning bieden bij veiligheidsmaatregelen en administratie.\nOpleiding: Bachelor in Bouwtechniek, Certificaten in Veiligheid en Onderwijs\nVaardigheden: Bouwtechnische analyse, teamleiderschap, communicatie"},
        "u4480": {"title": "Naam: Nova van der Meer\nErvaringen:\n1. Secretaresse bij Kantoor Prodigy (2018-2019)\n   - Coördineren van kantoorprocessen en administratie.\n   - Verantwoordelijk voor klantadvieshotline.\n2. Administratief Supervisor bij Bedrijfsmanagement Solutions (2019-2021)\n   - Toezicht houden op administratieve processen en personeelsbeheer.\n   - Ondersteunen bij het beheer van bedrijfsmiddelen.\n3. Assistentie Manager bij Organisatie Excellence (2021-heden)\n   - Assisteren bij bedrijfsactiviteiten en onderhoud.\n   - Coördineren van evenementplanning en administratie.\nOpleiding: Bachelor in Administratie en Kantoorbeheer, Certificaten in Klantenservice en Archivering\nVaardigheden: Administratieve coördinatie, klantenservice, evenementplanning"},
        "u3092": {"title": "Naam: Isa Michiels\nErvaringen:\n1. Lerarenkwalificatie bij Lerarenopleiding University (2018-2019)\n   - Voltooien van lerarenkwalificatiecursussen.\n   - Lesgeven aan studenten en academische taken uitvoeren.\n2. Teamleider bij Expatriatie Academie (2019-2021)\n   - Leiden van een team van leraren en ondersteunend personeel.\n   - Coördineren van lesgeefactiviteiten en academisch beheer.\n3. Lerarenopleiding bij Algemene Universiteit (2021-heden)\n   - Instrueren en lesgeven aan leraren-in-opleiding.\n   - Beheren van academische programma's en onderwijsontwikkeling.\nOpleiding: Lerarenkwalificatiecertificaat, Certificaten in Lerarenopleiding en Academisch Beheer\nVaardigheden: Lesgeven, teamleiderschap, academisch beheer"},
        "u1049": {"title": "Naam: Puck de Rijke\nErvaringen:\n1. Bankmedewerker bij Nationale Bank (2018-2019)\n   - Klanten adviseren over financiële producten.\n   - Beheren van banktransacties en accounts.\n2. Accountant bij Financiële Experts Inc. (2019-2021)\n   - Verantwoordelijk voor boekhouding en financieel beheer.\n   - Klanten voorzien van financieel advies en ondersteuning.\n3. Lobby Manager bij Financiële Services Ltd. (2021-heden)\n   - Beheren van lobbyactiviteiten en klantrelaties.\n   - Assisteren bij investeringen en financieel beheer.\nOpleiding: Bachelor in Financieel Beheer, Kwalificaties voor Effecten- en Futures-industriebeoefenaars\nVaardigheden: Financieel beheer, boekhouding, klantadvies"},
        "u3499": {"title": "Naam: Bo de Gier\nErvaringen:\n1. Projectmanager bij Projectmanagement Experts (2018-2019)\n   - Leiden van projecten en budgetbeheer.\n   - Coördineren van projectteams en planning.\n2. Coördinator bij Bouw & Inkoop Solutions (2019-2021)\n   - Coördineren van bouw- en inkoopprocessen.\n   - Toezicht houden op contracten en logistiek.\nOpleiding: Bachelor in Bouwmanagement, Certificaten in Projectmanagement en Inkoop\nVaardigheden: Projectmanagement, coördinatie, logistiek"},
        "u4498": {"title": "Naam: Jules Rosmalen\nErvaringen:\n1. Bestandsbeheerder bij Personeelsvoordelen Corp. (2018-2019)\n   - Beheren van bestanden en documenten.\n   - Coördineren van administratieve processen.\n2. Budgetbeheerder bij Administratief Management Solutions (2019-2021)\n   - Verantwoordelijk voor budgetbeheer en financiële rapportage.\n   - Ondersteunen bij bedrijfsactiviteiten en fondsverstrekking.\n3. Coördinator van Activiteiten bij Evenementplanning Experts (2021-heden)\n   - Coördineren van evenementplanning en logistiek.\n   - Ondersteunen bij klantenservice en administratie.\nOpleiding: Bachelor in Administratie en Evenementplanning, Certificaten in Budgetbeheer en Klantenservice\nVaardigheden: Bestandsbeheer, budgetbeheer, evenementplanning"},
        "u3678": {"title": "Naam: Yaniek Bakker\nErvaringen:\n1. Kwaliteitsinspecteur bij Certificering Inc. (2018-2019)\n   - Uitvoeren van kwaliteitsinspecties en certificeringen.\n   - Rapporteren over kwaliteitsbeoordelingen en controles.\n2. Human Resources Specialist bij Personeelszaken Experts (2019-2021)\n   - Beheren van HR-processen en personeelsadministratie.\n   - Coördineren van werving en beoordeling.\n3. Financieel Assistent bij Financiële Beheerproducten Ltd. (2021-heden)\n   - Ondersteunen bij financieel beheer en boekhouding.\n   - Assisteren bij rapportage en controle.\nOpleiding: Bachelor in Kwaliteit en Human Resource Management, Kwalificatiecertificaat voor Boekhouding\nVaardigheden: Kwaliteitsinspectie, HR-beheer, financiële ondersteuning"},
        "u3391": {"title": "Naam: Noël Hoekstra\nErvaringen:\n1. Coördinator van Activiteiten bij Brandweer Experts (2018-2019)\n   - Coördineren van activiteiten en evenementen.\n   - Beheren van brandbestrijdingsfaciliteiten.\n2. Administratief Assistent bij Kantoor Excellentie (2019-2021)\n   - Assisteren bij kantoorprocessen en gegevensbeheer.\n   - Coördineren van vergaderingen en notulen.\n3. Brandwacht bij Veiligheid & Outreach Solutions (2021-heden)\n   - Toezicht houden op brandveiligheid en outreach-activiteiten.\n   - Assisteren bij brandbestrijding en -beheer.\nOpleiding: Bachelor in Administratie en Brandbestrijding, Certificaten in Coördinatie en Veiligheid\nVaardigheden: Coördinatie, gegevensbeheer, brandbestrijding"},
        "u4289": {"title": "Naam: Marijn Baarsma\nErvaringen:\n1. Campus Promotor bij Lerarenkwalificatie University (2018-2019)\n   - Promoten van lerarenkwalificatieprogramma's op de campus.\n   - Coördineren van promotie-evenementen.\n2. Administratief Assistent bij Boekhoudkundige Experts Inc. (2019-2021)\n   - Assisteren bij administratieve taken en gegevensbeheer.\n   - Coördineren van archiefbeheer en documenten.\n3. Coördinator van Producten bij Promotie & Coördinatie Solutions (2021-heden)\n   - Coördineren van productpromotie en marketing.\n   - Ondersteunen bij klantrelaties en coördinatie.\nOpleiding: Bachelor in Buitenlandse Taal en Letterkunde, Rijbewijs C1\nVaardigheden: Promotie, administratie, klantrelaties"},
        "u2905": {"title": "Naam: Silke Jansen\nErvaringen:\n1. Redacteur bij Financiële Kennis Corp. (2018-2019)\n   - Redigeren van financiële documenten en rapporten.\n   - Beheren van financiële kennisbank.\n2. Certified Public Accountant bij Boekhouding & Financiën Experts (2019-2021)\n   - Uitvoeren van boekhoudkundige taken en financieel beheer.\n   - Assisteren bij financiële rapportage en audit.\n3. Teamleider bij Team Financiën (2021-heden)\n   - Leiden van een financieel team.\n   - Coördineren van financiële activiteiten en rapportage.\nOpleiding: Bachelor in Financieel Beheer, Boekhoudkundige Kwalificatie (geannuleerd)\nVaardigheden: Boekhouding, financieel beheer, redactie"},
        "u45":   {"title": "Naam: Dani de Groot\nErvaringen:\n1. Supervisie-Ingenieur bij Gemeentelijke Techniek Corp. (2018-2019)\n   - Toezicht houden op technische projecten en constructie.\n   - Coördineren van bouwprocessen en planning.\n2. Kwaliteitsinspecteur bij Civiele Techniek Inspecties (2019-2021)\n   - Uitvoeren van kwaliteitsinspecties en certificeringen.\n   - Rapporteren over kwaliteitsbeoordelingen en controles.\n3. Projectsupervisor bij Bouwprojecten & Leervermogen Solutions (2021-heden)\n   - Leiden van bouwprojecten en supervisie van teams.\n   - Ondersteunen bij projectbeheer en planning.\nOpleiding: Bachelor in Civiele Techniek, Kwaliteitsinspecteurcertificaat\nVaardigheden: Technische supervisie, kwaliteitsinspectie, projectbeheer"}
    }

    names = {"u4186": "Chris de Vries", "u3033": "Sam Appelscha", "u3449": "Jesse Kusters", "u2707": "Taylor Meijer", "u3961": "Noah van der Berg",
             "u2302": "Senna de Boer", "u2067": "Kai Peters", "u1429": "Bobby van Dijk", "u4171": "Robin Boomsma", "u346":  "Bowie van den Beek",
             "u4480": "Nova van der Meer", "u3092": "Isa Michiels", "u1049": "Puck de Rijke", "u3499": "Bo de Gier", "u4498": "Jules Rosmalen",
             "u3678": "Yaniek Bakker", "u3391": "Noël Hoekstra", "u4289": "Marijn Baarsma", "u2905": "Silke Jansen", "u45": "Dani de Groot",
             "u2006": "Maxime van der Voort"}
    
    listings = {"j127874":"Personeelsassistent, Aydco", "j62302":"HR-administratief specialist, Ahold Delhaize", "j186432":"HR assistent, 043HR", 
                "j66010":"Klerk, Accountantskantoor Frenzel & Weijers", "j203038":"Kantoorbediende/administratief medewerker, BPM Services", 
                "j265360":"Administratief assistent, Cox Techniek", "j105039":"Salarisspecialist, Sunneroo Zonnepanelen", 
                "j169464":"Binnenkomstmedewerker, Hotel Bigarré Maastricht Centrum", "j261177":"Administratief Manager, myenergi", 
                "j15098":"Administratief Specialist, Arvato Maastricht", "j60752":"Medewerker Backoffice/administratieve leiding, Freddomatic", 
                "j211452":"Boekhoudassistent, Huijerjans Adviesgroep", "j120853":"Administratief medewerker, Carwash USA", 
                "j259198":"Verkoopondersteuningsspecialist, Arteaux Art & Design", "j6290":"Headhunting consultant, Staffable Payroll",
                "j184402": "Personeelsassistnet, Majorel", "j83134" : "Ambtenaar, Gemeente Maastricht", "j63991": "Aankoopspecialist, Praxis",
                "j7191" : "Receptionist, Globe Agency", "j138734": "Afdelingsassistent R&D, galactIQ", "j193337": "Uitvoerend manager, Starwash", 
                "j167552": "Administratief medewerker, Esprit Maastricht", "j129341": "HR Bedrijfspartner, Soma Works", "j217795": "Informatiemedewerker, Poirier",
                "j211887": "Assistent, Meijer en Zoons"}    

    terms = {'enterprise': 'ondernemen', 'assistant': 'assistent', 'Recruiter': 'Recruiter', 'teach': 'onderwijzen', 'reception': 'receptie',
             'HR Specialist': 'HR specialist', 'Securities Practitioner Qualification Certificate': 'Kwalificatiecertificaat voor effectenbeoefenaar',
             'dig': 'graven', 'front desk': 'receptie', 'goods': 'goederen', 'leisure': 'recreatie', 'Accounting qualification has been cancelled)': 'Boekhoudkundige kwalificatie (verlopen)',
             'financial assistant': 'financieel assistent', 'communicate': 'communiceren', 'Commercial Specialist': 'Commercieel Specialist', 'Internal auditor': 'Interne auditor',
             'document': 'documentatie', 'Customer Service Specialist': 'Klantenservice specialist', 'transportation': 'vervoer', 'regulations': 'regelgeving', 'Data management': 'Gegevensbeheer',
             'send and receive': 'verzenden en ontvangen', 'headhunting consultant': 'headhunter adviseur', 'Undergraduate': 'Bachelor', 'in stock': 'Bevoorrading',
             'Administrative Commissioner': 'Administratief commissaris', 'secretary': 'secretaris', 'Purchasing Specialist': 'Aankoopspecialist', 'clerk': 'klerk',
             'Accounting Qualification Certificate': 'Certificaat van boekhoudkundige kwalificatie', 'Qualifications for practitioners in the securities and futures industry': 'Kwalificaties voor beoefenaars in de effecten- en futures-industrie',
             'file management': 'bestandsbeheer', 'data operation': 'gegevensbewerking', 'team leader': 'teamleider', 'Documentation': 'Documentatie'}


    reverse = {v: k for k, v in names.items()}

    users = list(set(list(hits.keys()) + list(misses.keys())))

    current_json = defaultdict(lambda : defaultdict(dict))

    setting = session["setting"]

    for node_1 in curr_explanations:
        for node_2 in curr_explanations[node_1].keys(): 
            # truth_value = truth_dict[node_1][node_2]

            # Gather information from the explanation
            sample = curr_explanations[node_1][node_2]["explanation"]

            if not sample:
                continue

            graph = sample[direction][setting]

            # curr_score = np.round(float(sample["full_score"]), 4)
            # full_score = np.round(float(sample[f"{direction}_score"]), 4)

            edges = [(i[0], i[1]) for i in graph]
            weights = {(i[0], i[1]) : i[2] for i in graph}


            # Recover the original graph
            G = {user: {**hits[user], **misses[user]} for user in users}[node_1][node_2].copy()
            G = nx.edge_subgraph(G, edges)
            G = nx.DiGraph(G)

            G.remove_edges_from([(node_1, node_2), (node_2, node_1)])

            if direction == "company":
                node_1, node_2 = node_2, node_1
                # G = G.reverse()

            # Initialize weights
            nx.set_edge_attributes(G, weights, name="weight")
            nx.set_node_attributes(G, {node_1: 10}, "weight")
            nx.set_node_attributes(G, {node: 0 for node in G if node != node_1}, "weight")

            layout = {}
            new_labels = {}

            for node in G:
                if re.match("j[\d]+", node):
                    layout[node] = {"node_type": "Vacatures", "color" : "#2bc253", "shape" : "hexagon"}
                elif re.match("u[\d]+", node):
                    layout[node] = {"node_type": "Kandidaten", "color" : "#f26884"}
                elif re.match("\S{32}", node):
                    new_node = f"j{random.randrange(100000, 250000)}"

                    if node == node_1:
                        node_1 = new_node
                    elif node == node_2:
                        node_2 = new_node

                    G = nx.relabel_nodes(G, {node : new_node})
                    layout[new_node] = {"node_type": "Vacatures", "color" : "#2bc253", "shape" : "hexagon"}
                else:
                    layout[node] = {"node_type": "Vacature types", "color" : "#fcba03", "shape" : "square"}

                if node in CVs:
                    layout[node] = {**layout[node], **CVs[node]}
                    new_labels[node] = names[node]
                elif node in listings:
                    new_labels[node] = listings[node]

            nx.set_node_attributes(G, layout)
                                   
            att_weights = nx.get_edge_attributes(G, "weight")
            att_weights = {k : float(v) for k, v in att_weights.items()}
            
            # Find paths
            paths = list(nx.all_simple_paths(G, node_1, node_2))

            bfs_paths = [list(path) for path in map(nx.utils.pairwise, paths)]
            longest_path = max([len(i) for i in bfs_paths])
            bfs_edges = []

            # Convert path to edges sorted from node_1 to node_2
            for i in range(longest_path):
                for path in bfs_paths:
                    if i < len(path):
                        bfs_edges.append(path[i])

            checked = set()
                        
            # Calculate node and edge weights/sizes
            for edge in bfs_edges:
                if edge in checked or edge == (node_1, node_2) or edge == (node_2, node_1):
                    continue
                else:
                    checked.add(edge)
                
                node_weights = nx.get_node_attributes(G, "weight")

                if edge not in att_weights:
                    edge = (edge[1], edge[0])

                # max_neighbor_weight = max([att_weights[(n, edge[0])] for n in G.neighbors(edge[0])])

                nx.set_node_attributes(G, {edge[1]: float(node_weights[edge[1]]) + float(node_weights[edge[0]]) * att_weights[edge]}, name="weight")
                nx.set_edge_attributes(G, {edge: np.round(att_weights[edge] * float(node_weights[edge[0]]), 3)}, name="value")

                # nx.set_node_attributes(G, {edge[1]: float(node_weights[edge[0]]) * att_weights[edge]}, name="weight")
                # nx.set_edge_attributes(G, {edge: att_weights[edge]}, name="value")

                # nx.set_edge_attributes(G, {edge: max(att_weights[edge], max_neighbor_weight)}, name="value")

                
                # nx.set_edge_attributes(G, {edge: np.mean([node_weights[edge[0]], node_weights[edge[1]]]) * att_weights[edge]}, name="value")

                
            final_weights = nx.get_edge_attributes(G, "value")

            # If company, make sure to reverse the labels
            labels = nx.get_edge_attributes(G, "label")

            if direction == "company":
                labels = {edge: session["label_reverse"][label] for edge, label in labels.items()}
                nx.set_edge_attributes(G, labels, "title")

            nx.set_edge_attributes(G, {edge: f"{labels[edge]}\n" for edge in G.edges()}, name="title") # Waarde: {final_weights[edge]}" for edge in G.edges()}, name="label")
            nx.set_edge_attributes(G, {edge: "" for edge in G.edges()}, name="label")
                
            shortest_paths = nx.all_simple_paths(G, 
                                                node_1, 
                                                node_2)

            # Calculate path weights
            paths = [[(path[i], path[i + 1]) for i in range(len(path) - 1)] for path in list(shortest_paths)]
            path_weights = [(path, sum([att_weights[x, y] for x, y in path])) for path in paths]
            
            # Take the top 3 most important paths
            best_paths = [i[0] for i in sorted(path_weights, key=lambda x: x[1], reverse=True) if i[1] > 0.1][:3]
            G_simple = G.edge_subgraph(set([item for sublist in best_paths for item in sublist]))
            # G = G.edge_subgraph()
            
            nx.set_node_attributes(G, {node: {"value": nx.get_node_attributes(G, "weight")[node]} for node in G})
            nx.set_node_attributes(G, {node: {"id" : i} for i, node in enumerate(G)}) 
            nx.set_node_attributes(G, {edge: {"value": nx.get_edge_attributes(G, "weight")[edge]} for edge in G.edges()})

            for _, _, d in G.edges(data=True):
                for att in ["embedding", "weight"]:
                    d.pop(att, None)

            for _, _, d in G_simple.edges(data=True):
                for att in ["embedding", "weight"]:
                    d.pop(att, None)

            G = nx.relabel_nodes(G, names)
            G = nx.relabel_nodes(G, listings)
            G = nx.relabel_nodes(G, terms)

            G_simple = nx.relabel_nodes(G_simple, names)
            G_simple = nx.relabel_nodes(G_simple, listings)
            G_simple = nx.relabel_nodes(G_simple, terms)

            string = node_link_data(G)
            string["directed"] = "true"
            string["multigraph"] = "false"

            string_simple = node_link_data(G_simple)
            string_simple["directed"] = "true"
            string_simple["multigraph"] = "false"

            current_json[new_labels.get(node_1, node_1)][new_labels.get(node_2, node_2)]["full"] = string
            current_json[new_labels.get(node_1, node_1)][new_labels.get(node_2, node_2)]["simple"] = string_simple

    if direction == "candidate":
        session["list_items"] = ["Personeelsassistent, Aydco", "HR-administratief specialist, Ahold Delhaize", "HR assistent, 043HR", "Klerk, Accountantskantoor Frenzel & Weijers", "Kantoorbediende/administratief medewerker, BPM Services"]
    else:
        session["list_items"] = ["Senna de Boer", "Sam Appelscha", "Chris de Vries", "Taylor Meijer", "Jesse Kusters"]

    return dict(current_json)


def create_texts():

# yellow, green, pink

# <span style='background-color: #fcba0344;'></span>
# <span style='background-color: #2bc25344;'></span>
# <span style='background-color: #f2688444;'></span>

    return {
        "Chris de Vries" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5>
                <h6>Chris de Vries. Maastricht, Nederland (<img src='static/location.png' class='textimg'>3.7 KM).<br></h6> 
                <p>Op basis van de informatie die we hebben en de belangrijkheid van de verbanden in het gegevensmodel lijkt Chris de Vries goed te passen bij de functie van Personeelsassistent bij Aydco. Hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries een <span style='background-color: #fcba0344;'>'Kwalificatiecertificaat voor effectenbeoefenaar'</span> wat vrij veel heeft meegewogen in de voorspelling, wat
                aangeeft dat deze vaardigheid van aanzienlijk belang is. Dit suggereert dat Chris beschikt over specifieke vaardigheden die waardevol kunnen zijn in de HR-functie, zoals het omgaan met complexe informatie of regelgeving.</p>
                <p>Daarnaast heeft Chris ervaring als <span style='background-color: #2bc25344;'>'Headhunting consultant' bij 'Staffable Payroll'</span>, opnieuw met een aanzienlijk gewicht. Deze vorige rol is relevant omdat het aangeeft dat Chris 
                bekend is met HR-gerelateerde taken en verantwoordelijkheden, wat van groot belang is voor de functie van Personeelsassistent.</p>
                <p>Tenslotte heeft <span style='background-color: #f2688444;'>Isa Michiels</span>, die eerder als Personeelsassistent bij Aydco heeft gewerkt, vaardigheden in <span style='background-color: #2bc25344;'>onderwijzen</span> 
                met een matig gewicht - een indirecte overeenkomst in skills met Chris. Hoewel dit op het eerste gezicht anders lijkt dan HR, kan het helpen bij het ontwikkelen van medewerkers, wat een belangrijk aspect is van HR-beheer.</p>
                <p>Samengevat suggereren de gewichtige verbanden in het gegevensmodel dat Chris de Vries de benodigde kwalificaties en ervaring heeft om goed te passen bij de functie van Personeelsassistent bij Aydco.</p>""",

                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5>
                <h6>Chris de Vries. Maastricht, Nederland (<img src='static/location.png' class='textimg'>3.7 KM).<br></h6>
                
                <p>Chris de Vries lijkt goed te passen bij de functie van Personeelsassistent bij Aydco, gebaseerd op de belangrijkheid van de verbanden in het AI-model:</p>
                <ul>
                    <li>Chris heeft een <span style='background-color: #fcba0344;'>'Kwalificatiecertificaat voor effectenbeoefenaar'</span> met aanzienlijke relevantie, wat wijst op specifieke vaardigheden.</li>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>'Headhunting consultant' bij 'Staffable Payroll'</span>, met een aanzienlijk gewicht, wat aangeeft dat hij/zij bekend is met HR-gerelateerde taken.</li>
                    <li><span style='background-color: #f2688444;'>Isa Michiels</span>, een vorige Personeelsassistent bij Aydco, heeft indirect overeenkomende vaardigheden met Chris in onderwijzen 
                    met matige relevantie, wat kan helpen bij medewerkersontwikkeling.</li>
                </ul>
                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5>
                <h6>Chris de Vries. Maastricht, Nederland (<img src='static/location.png' class='textimg'>3.7 KM).<br></h6>
                <p>Het lijkt erop dat Chris de Vries goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie die we hebben. Laten we eens kijken naar de connecties die we hebben ontdekt:</p>
                <p>Ten eerste heeft Chris de Vries een <span style='background-color: #fcba0344;'>'Kwalificatiecertificaat voor effectenbeoefenaar'</span>. Deze kwalificatie toont aan dat Chris over specifieke vaardigheden beschikt, 
                wat altijd handig is in HR-gerelateerde functies zoals deze.</p>
                <p>Bovendien heeft Chris ervaring als <span style='background-color: #2bc25344;'>'Headhunting consultant' bij 'Staffable Payroll'</span>. Deze vorige functie is vergelijkbaar met de functie van Personeelsassistent, zij het met
                een andere focus. Dit toont aan dat Chris bekend is met de wereld van personeelszaken en recruitment.</p>
                <p>Tot slot, <span style='background-color: #f2688444;'>Isa Michiels</span>, die eerder heeft gewerkt als Personeelsassistent bij Aydco, heeft vaardigheden in <span style='background-color: #2bc25344;'>onderwijzen</span>. 
                Hoewel dit op het eerste gezicht anders lijkt dan HR, is het belangrijk op te merken dat HR ook betrekking heeft op het begeleiden en ontwikkelen van medewerkers. Deze vaardigheid kan dus waardevol zijn voor het helpen van
                medewerkers bij hun groei en ontwikkeling.</p>
                <p>Al deze verbindingen suggereren dat Chris de Vries de nodige kwalificaties en ervaring heeft om een goede kandidaat te zijn voor de functie van Personeelsassistent bij Aydco.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5>
                <h6>Chris de Vries. Maastricht, Nederland (<img src='static/location.png' class='textimg'>3.7 KM).<br></h6>
                <p>Hier is een beknopte samenvatting van waarom Chris de Vries een goede match lijkt te zijn voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Chris heeft een <span style='background-color: #fcba0344;'>'Kwalificatiecertificaat voor effectenbeoefenaar'</span>, wat wijst op relevante vaardigheden.</li>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>'Headhunting consultant'</span>, wat aantoont dat hij/zij bekend is met personeelszaken.</li>
                    <li><span style='background-color: #f2688444;'>Isa Michiels</span>, een vorige Personeelsassistent bij Aydco, heeft vaardigheden in <span style='background-color: #2bc25344;'>onderwijzen</span>,
                    wat nuttig kan zijn voor medewerkersontwikkeling.</li>
                </ul>"""
            }
        },
        "Senna de Boer" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Senna de Boer</u> en <u>Aydco</u></h5>
                <h6>Senna de Boer. Maastricht, Nederland (<img src='static/location.png' class='textimg'>11.2 KM).<br></h6>
                <p>Het model heeft de volgende relevante connecties aangegeven:</p>
                <p>Senna de Boer heeft eerder gewerkt als <span style='background-color: #2bc25344;'>Afdelingsassistent R&D bij galactIQ</span>. Deze ervaring is van belang omdat het aantoont dat Senna de Boer ervaring heeft
                in een ondersteunende rol, wat overeenkomt met de taken van een Personeelsassistent. Het XAI-model heeft deze connectie als relevant beschouwd voor de match.</p>
                <p>Bovendien heeft Senna de Boer de vaardigheid <span style='background-color: #fcba0344;'>Bevoorrading</span>, wat een belangrijke vaardigheid is in de functie van Personeelsassistent. Dit valt ook te zien aan het feit dat 
                een voormalig Personeelsassistent bij Aydco, <span style='background-color: #f2688444;'>Yaniek Bakker</span>, deze vaardigheid ook heeft. Het hebben van deze vaardigheid is gunstig voor taken zoals voorraadbeheer en organisatie,
                wat vaak deel uitmaakt van de rol. Het model ziet dit als een erg belangrijk verband.</p>
                <p>Verder laat de grafiek zien dat de functie van Personeelsassistent bij Aydco onder de rol van <span style='background-color: #fcba0344;'>assistent</span> valt. Aangezien Senna de Boer eerder heeft gewerkt als
                Afdelingsassistent R&D, suggereert dit dat hij/zij bekend is met ondersteunende taken, wat waardevol is voor de functie van Personeelsassistent.</p>
                <p>De waarden in de grafiek geven aan dat de connecties als relevant worden beschouwd voor deze match. Kortom, de gegevens in de grafiek suggereren dat Senna de Boer zowel de relevante ervaring als vaardigheden 
                heeft om effectief te functioneren als Personeelsassistent bij Aydco, en het XAI-model heeft dit als een sterke match geïdentificeerd op basis van de beschikbare informatie.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Senna de Boer</u> en <u>Aydco</u></h5>
                <h6>Senna de Boer. Maastricht, Nederland (<img src='static/location.png' class='textimg'>11.2 KM).<br></h6>
                <p>Waarom Senna de Boer een goede match is voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Hij/zij bezit, net als voorgaande personeelsassistent van Aydco, de vaardigheid <span style='background-color: #fcba0344;'>Bevoorrading</span>, wat belangrijk is voor taken zoals voorraadbeheer en organisatie in de functie. 
                    Het model ziet dit als een erg belangrijk verband</li>
                    <li>Senna de Boer heeft ervaring als <span style='background-color: #2bc25344;'>Afdelingsassistent R&D bij galactIQ</span>, wat relevant is voor een ondersteunende rol als Personeelsassistent.</li>
                    <li>De functie van Personeelsassistent bij Aydco valt onder de rol van <span style='background-color: #fcba0344;'>assistent</span>, waarin Senna de Boer eerder heeft gewerkt, wat zijn/haar geschiktheid benadrukt.</li>
                </ul>
                <p>Deze verbindingen tonen de geschiktheid van Senna de Boer voor de functie van Personeelsassistent bij Aydco.</p>"""
            },
            "random" : {
                "full" :
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Senna de Boer</u> en <u>Aydco</u></h5>
                <h6>Senna de Boer. Maastricht, Nederland (<img src='static/location.png' class='textimg'>11.2 KM).<br></h6>
                <p>Deze grafiek onthult enkele relevante connecties:</p>
                <p>Ten eerste heeft Senna de Boer eerder gewerkt als <span style='background-color: #2bc25344;'>Afdelingsassistent R&D bij galactIQ</span>. Hoewel de waarde van deze connectie laag lijkt te zijn, duidt het toch op enige 
                ervaring in een ondersteunende rol, wat relevant kan zijn voor de functie van Personeelsassistent.</p>
                <p>Ten tweede bezit Senna de Boer de vaardigheid <span style='background-color: #fcba0344;'>Bevoorrading</span>. Deze vaardigheid is belangrijk in de functie, en het XAI-model beschouwt dit als een belangrijke factor voor de match.</p>
                <p>Ten derde toont de grafiek aan dat de functie van Personeelsassistent bij Aydco valt onder de rol van <span style='background-color: #fcba0344;'>assistent</span>. Senna de Boer heeft eerder gewerkt als 
                <span style='background-color: #2bc25344;'>Afdelingsassistent R&D</span>, wat suggereert dat hij/zij bekend is met ondersteunende taken en verantwoordelijkheden, wat waardevol kan zijn voor de rol van Personeelsassistent.</p>
                <p>Hoewel sommige verbindingswaarden in de grafiek laag lijken, heeft het XAI-model de combinatie van deze connecties als een geschikte match geïdentificeerd. Het model houdt rekening met meerdere factoren en concludeert 
                dat Senna de Boer over de juiste ervaring, vaardigheden en achtergrond beschikt om effectief te zijn in de rol van Personeelsassistent bij Aydco.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Senna de Boer</u> en <u>Aydco</u></h5>
                <h6>Senna de Boer. Maastricht, Nederland (<img src='static/location.png' class='textimg'>11.2 KM).<br></h6>
                <p>Waarom Senna de Boer een goede match is voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Senna de Boer heeft enige ervaring in een ondersteunende rol als <span style='background-color: #2bc25344;'>Afdelingsassistent R&D bij galactIQ</span>.</li>
                    <li>Hij/zij bezit de vaardigheid <span style='background-color: #fcba0344;'>Bevoorrading</span>, wat belangrijk is voor de functie.</li>
                    <li>De functie van Personeelsassistent bij Aydco valt onder de rol van <span style='background-color: #fcba0344;'>assistent</span>, waarin Senna de Boer eerder heeft gewerkt.</li>
                </ul>
                <p>Deze combinatie van factoren maakt Senna de Boer een geschikte match voor de rol van Personeelsassistent bij Aydco.</p>"""
            }
        },
        "Sam Appelscha" : {
            "real" : {
                "full" :
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Sam Appelscha</u> en <u>Aydco</u></h5>
                <h6>Sam Appelscha. Heerlen, Nederland (<img src='static/location.png' class='textimg'>9.5 KM).<br></h6>
                
                <p>Het lijkt erop dat Sam Appelscha goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie 
                die we hebben en de belangrijkheid van de verbanden in het gegevensmodel:</p>
                <p>Allereerst heeft een andere kandidaat, <span style='background-color: #f2688444;'>Jules Rosmalen</span>, ervaring als <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span> en heeft 
                deze ook de functie van Personeelsassistent bij Aydco vervuld, wat aangeeft dat deze persoon de overgang heeft gemaakt naar de HR-gerelateerde functie. Sam Appelscha heeft ook de rol als
                <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span> vervuld, wat suggereert dat hij/zij vergelijkbare taken heeft uitgevoerd als <span style='background-color: #f2688444;'>Jules Rosmalen</span>
                voordat hij/zij de overstap maakte naar Personeelsassistent. Dit is een sterke indicatie van een goede match.</p>
                <p>Bovendien heeft Sam aangegeven te willen werken in de <span style='background-color: #fcba0344;'>vervoer</span> industrie, wat overeenkomt met de gewenste industrie van
                <span style='background-color: #f2688444;'>Bo de Gier</span>, die eerder een functie lijkend op Personeelsassitent heeft vervuld. Dit toont aan dat Sam interesse heeft in de juiste sector voor de functie.</p>
                <p>Samengevat, de overeenkomende sectorvoorkeur en de vergelijkbare loopbaantrajecten van Sam Appelscha en Jules Rosmalen suggereren dat Sam goed zou kunnen passen bij
                de functie van Personeelsassistent bij Aydco.</p>""",
                
                "simple" :
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Sam Appelscha</u> en <u>Aydco</u></h5>
                <h6>Sam Appelscha. Maastricht, Nederland (<img src='static/location.png' class='textimg'>9.5 KM).<br></h6>
                <p>Sam Appelscha lijkt goed te passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie in het gegevensmodel:</p>
                <ul>
                    <li>Sam heeft vergelijkbare ervaring als <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span> met <span style='background-color: #f2688444;'>Jules Rosmalen</span>, 
                    die al eerder de overstap heeft gemaakt naar Personeelsassistent bij Aydco.</li>
                    <li>Sam heeft interesse in de <span style='background-color: #fcba0344;'>vervoersindustrie</span>, wat overeenkomt met de gewenste industrie van <span style='background-color: #f2688444;'>Bo de Gier</span>, 
                    wie eerder een soortgelijke functie heeft vervuld.</li>
                </ul>"""
            },
            "random" : {
                "full" :
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Sam Appelscha</u> en <u>Aydco</u></h5>
                <h6>Sam Appelscha. Maastricht, Nederland (<img src='static/location.png' class='textimg'>9.5 KM).<br></h6>
                <p>Het lijkt erop dat Sam Appelscha goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie in het gegevensmodel en de belangrijkheid van de verbanden:</p>
                <p>Ten eerste heeft Sam aangegeven te willen werken in de <span style='background-color: #fcba0344;'>vervoer</span> industrie, wat enige relevantie heeft. Hoewel dit slechts een lichte indicatie is, kan dit wijzen op
                affiniteit met de juiste sector voor de functie.</p>
                <p>Verder heeft <span style='background-color: #f2688444;'>Jules Rosmalen</span> ervaring als <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span> en heeft deze persoon de rol van 
                Personeelsassistent, Aydco vervuld, met respectievelijk redelijke en aanzienlijke belangrijkheid. Sam Appelscha heeft ook de positie van <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span>
                vervuld, wat suggereert dat hij/zij vergelijkbare taken heeft uitgevoerd als <span style='background-color: #f2688444;'>Jules Rosmalen</span> voordat hij/zij de overstap maakte naar Personeelsassistent. 
                Dit versterkt het idee van een goede match.</p>
                <p>Over het algemeen, hoewel sommige verbanden slechts lichte relevantie hebben, tonen de gewichtige verbanden in het gegevensmodel, zoals de overeenkomstige eerdere functie en
                de gewenste sector, aan dat Sam Appelscha goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco.</p>""",

                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Sam Appelscha</u> en <u>Aydco</u></h5>
                <h6>Sam Appelscha. Maastricht, Nederland (<img src='static/location.png' class='textimg'>9.5 KM).<br></h6>
                                
                <p>Sam Appelscha lijkt goed te passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie in het gegevensmodel:</p>
                <ul>
                    <li>Sam heeft interesse in de <span style='background-color: #fcba0344;'>vervoer</span> industrie, wat enige relevantie heeft voor de functie.</li>
                    <li>Sam heeft vergelijkbare ervaring als <span style='background-color: #2bc25344;'>Ambtenaar bij Gemeente Maastricht</span> als <span style='background-color: #f2688444;'>Jules Rosmalen</span>, 
                    die de overstap heeft gemaakt naar Personeelsassistent bij Aydco.</li>
                </ul>"""
            }
        },
        "Taylor Meijer" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Taylor Meijer</u> en <u>Aydco</u></h5>
                <h6>Taylor Meijer. Heerlen, Nederland (<img src='static/location.png' class='textimg'>19.5 KM).<br></h6>
                <p>Uitleg voor waarom het XAI-model Taylor Meijer heeft aangemerkt als een goede match voor de functie van Personeelsassistent bij Aydco, op basis van de gegevens in de grafiek.</p>
                <p>Taylor Meijer heeft eerder gewerkt als <span style='background-color: #2bc25344;'>Administratief medewerker bij Esprit Maastricht</span>. Deze ervaring is relevant omdat Personeelsassistenten bij Aydco betrokken 
                zijn bij administratieve taken, zoals het beheren van personeelsdossiers en documentverwerking. Het XAI-model heeft deze verbinding als belangrijk aangemerkt voor de match.</p>
                <p>Bovendien heeft Taylor Meijer dezelfde rol als <span style='background-color: #2bc25344;'>uitvoerend manager</span> vervuld als <span style='background-color: #f2688444;'>Nova van der Meer</span>, 
                die op zijn/haar plaats weer de rol van Personeelsassistent by Aydco heeft vervuld in het verleden. Dit suggereert dat Taylor Meijer overeenkomende ervaring heeft opgedaan als voormalig
                Personeelsassistenten, wat erg relevant kan zijn voor de functie.</p>
                <p>Verder laat het model zien dat de functie van Personeelsassistent bij Aydco onder de rol van <span style='background-color: #fcba0344;'>assistent</span> valt. Taylor heeft eerdere ervaring binnen dit gebied,
                wat hem/haar de relevante vaardigheden heeft gegeven voor de nieuwe functie.</p>
                <p>Het model geeft aan dat alle verbindingen als zeer relevant worden beschouwd voor deze match. Kortom, de gegevens in de grafiek duiden erop dat Taylor Meijer de benodigde ervaring en vaardigheden heeft om succesvol te zijn
                als Personeelsassistent bij Aydco, en het XAI-model heeft dit als een mogelijke match geïdentificeerd op basis van de beschikbare informatie.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Taylor Meijer</u> en <u>Aydco</u></h5>
                <h6>Taylor Meijer. Heerlen, Nederland (<img src='static/location.png' class='textimg'>19.5 KM).<br></h6>
                <p>Waarom Taylor Meijer een goede match is voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Taylor Meijer heeft ervaring als <span style='background-color: #2bc25344;'>Administratief medewerker bij Esprit Maastricht</span>, wat relevant is voor administratieve taken in de functie.</li>
                    <li>De grafiek toont aan dat Taylor Meijer dezelfde rol heeft vervuld als <span style='background-color: #f2688444;'>Nova van der Meer</span>, die eerder de Personeelsassistent-functie bij Aydco heeft vervuld, wat wijst op overeenkomende ervaring.</li>
                    <li>De functie van Personeelsassistent bij Aydco valt onder de rol van <span style='background-color: #fcba0344;'>assistent</span>, waarin Taylor Meijer eerdere ervaring heeft opgedaan.</li>
                </ul>
                <p>Deze verbindingen onderstrepen de geschiktheid van Taylor Meijer voor de functie van Personeelsassistent bij Aydco.</p>"""
            },
            "random" : {
                "full" :
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Taylor Meijer</u> en <u>Aydco</u></h5>
                <h6>Taylor Meijer. Heerlen, Nederland (<img src='static/location.png' class='textimg'>19.5 KM).<br></h6>
                <p>Taylor Meijer heeft ervaring als <span style='background-color: #2bc25344;'>Administratief medewerker bij Esprit Maastricht</span>. Deze ervaring is van belang omdat de Personeelsassistent bij Aydco administratieve taken
                moet uitvoeren, zoals het bijhouden van personeelsdossiers en documentverwerking. Het XAI-model heeft vastgesteld dat deze link belangrijk is voor de match.</p>
                <p>Bovendien heeft Taylor Meijer gewerkt met <span style='background-color: #f2688444;'>Nova van der Meer</span>, die eerder de rol van <span style='background-color: #2bc25344;'>Uitvoerend manager bij Starwash</span>
                heeft vervuld. Dit suggereert dat Taylor Meijer mogelijk relevante vaardigheden en kennis heeft opgedaan samen met <span style='background-color: #f2688444;'>Nova van der Meer</span>, wat van pas kan komen in de rol van Personeelsassistent.</p>
                <p>Verder zien we dat de functie van Personeelsassistent, Aydco overkoepelend is over de rol van <span style='background-color: #fcba0344;'>assistent</span>. Dit betekent dat Taylor Meijer de mogelijkheid heeft om een bredere
                impact te hebben en niet beperkt is tot één specifieke taak. Dit kan gunstig zijn in een dynamische rol zoals Personeelsassistent.</p>
                <p>Al met al wijzen de verbindingen in de grafiek erop dat Taylor Meijer relevante ervaring en vaardigheden heeft opgedaan in eerdere functies, wat zijn geschiktheid voor de rol van Personeelsassistent bij Aydco onderstreept.
                Het model heeft dit als een sterke match geïdentificeerd op basis van de beschikbare informatie.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Taylor Meijer</u> en <u>Aydco</u></h5>
                <h6>Taylor Meijer. Heerlen, Nederland (<img src='static/location.png' class='textimg'>19.5 KM).<br></h6>
                <p>Waarom Taylor Meijer een goede match is voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Taylor Meijer heeft ervaring als <span style='background-color: #2bc25344;'>Administratief medewerker bij Esprit Maastricht</span>, wat relevant is voor administratieve taken in de functie.</li>
                    <li>Hij heeft gewerkt met <span style='background-color: #f2688444;'>Nova van der Meer</span>, die eerder <span style='background-color: #2bc25344;'>Uitvoerend manager</span> was, wat wijst op relevante leiderschapskennis.</li>
                    <li>De functie van Personeelsassistent bij Aydco omvat de rol van <span style='background-color: #fcba0344;'>assistent</span>, waardoor Taylor Meijer een brede impact kan hebben.</li>
                </ul>
                <p>Deze verbindingen onderstrepen de geschiktheid van Taylor Meijer voor de functie van Personeelsassistent bij Aydco.</p>"""
            }
        },
        "Jesse Kusters" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Jesse Kusters</u> en <u>Aydco</u></h5>
                <h6>Jesse Kusters. Maastricht, Nederland (<img src='static/location.png' class='textimg'>2.4 KM).<br></h6>
                <p>Het AI-heeft voorspeld dat Jesse Kusters een goede match is voor de positie. De uitleg hiervoor is als volgt:</p>
                <p>Jesse Kusters heeft vaardigheden in <span style='background-color: #fcba0344;'>bestandsbeheer</span>; deze vaardigheid is belangrijk voor de functie van Personeelsassistent, omdat het bijhouden van personeelsdossiers en het verwerken van 
                HR-gerelateerde documenten tot de verantwoordelijkheden van de functie behoren. Het feit dat Jesse Kusters deze vaardigheid heeft, maakt hem/haar geschikt voor deze aspecten van de functie.</p>
                <p>Bovendien heeft Jesse Kusters de vaardigheid van <span style='background-color: #fcba0344;'>Interne auditor</span>, wat een belangrijk onderdeel is van de functie. Dit kan nuttig zijn bij het evalueren van trainingsbehoeften en het 
                helpen handhaven van HR-beleid, zoals vermeld in de functiebeschrijving. Uit de beschikbare data blijkt dat Jesse Kusters deze vaardigheid heeft uitgevoerd, wat betekent dat hij/zij praktische ervaring heeft in dit vakgebied.</p>
                <p>Ten slotte heeft Jesse Kusters een connectie met de functie van Personeelsassistent bij Aydco via <span style='background-color: #f2688444;'>Kai Peters</span> en <span style='background-color: #f2688444;'>Bobby van Dijk</span>,
                waarbij zij soortgelijke functies hebben vervuld. Dit betekent dat er al een bestaande relatie is tussen Jesse Kusters en de functie, wat de kans vergroot dat hij/zij goed in het team zou passen en de vereiste vaardigheden heeft 
                om succesvol te zijn in deze rol.</p>
                <p>Al met al zijn Jesse Kusters' vaardigheden en ervaringen in lijn met de eisen van de functie, en zijn/haar bestaande connecties versterken zijn/haar geschiktheid voor de rol van Personeelsassistent bij Aydco.</p>
                """,
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Jesse Kusters</u> en <u>Aydco</u></h5>
                <h6>Jesse Kusters. Maastricht, Nederland (<img src='static/location.png' class='textimg'>2.4 KM).<br></h6>
                <p>Waarom Jesse Kusters een goede match is voor de functie van Personeelsassistent bij Aydco:</p>
                <ul>
                    <li>Jesse Kusters heeft vaardigheden in <span style='background-color: #fcba0344;'>bestandsbeheer</span>, wat essentieel is voor het bijhouden van personeelsdossiers en documentverwerking in de functie.</li>
                    <li>Jesse bezit de vaardigheid van <span style='background-color: #fcba0344;'>Interne auditor</span>, wat van pas komt bij het evalueren van trainingsbehoeften en het handhaven van HR-beleid.</li>
                    <li>Jesse Kusters heeft bestaande connecties met de functie via <span style='background-color: #f2688444;'>Kai Peters</span> en <span style='background-color: #f2688444;'>Bobby van Dijk</span>, 
                    die soortgelijke rollen eerder hebben vervuld, wat Jesse's geschiktheid versterkt.</li>
                </ul>
                <p>Dit maakt Jesse Kusters een geschikte kandidaat voor de functie van Personeelsassistent bij Aydco.</p>"""
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Jesse Kusters</u> en <u>Aydco</u></h5>
                <h6>Jesse Kusters. Maastricht, Nederland (<img src='static/location.png' class='textimg'>2.4 KM).<br></h6>
                <p>Het lijkt erop dat Jesse Kusters goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie in het gegevensmodel en de belangrijkheid van de verbanden:</p>
                <p>Ten eerste heeft Jesse Kusters vaardigheden op het gebied van <span style='background-color: #fcba0344;'>Interne audit</span>, wat relevant is voor de rol van Personeelsassistent. Deze vaardigheden
                zijn overeenkomend met van <span style='background-color: #f2688444;'>Bobby van Dijk</span>, wat aangeeft dat Jesse in staat is om de benodigde taken uit te voeren.</p>
                <p>Bovendien heeft Jesse Kusters ervaring op het gebied van <span style='background-color: #fcba0344;'>bestandsbeheer</span>, wat relevant kan zijn in een HR-functie waarbij het bijhouden van personeelsdossiers en documentatie essentieel is. 
                Deze vaardigheden zijn overeenkomend met <span style='background-color: #f2688444;'>Robin Boomsma</span>.</p>
                <p>Wat deze match nog sterker maakt, is dat Jesse Kusters eerder heeft gewerkt met <span style='background-color: #f2688444;'>Kai Peters</span>, die de rol van Personeelsassistent heeft vervuld bij Aydco. 
                Dit toont aan dat Jesse al bekend is met iemand binnen het bedrijf, wat een soepele integratie kan bevorderen.</p>
                <p>Al met al, de aanwezigheid van relevante vaardigheden, ervaring en connecties in het gegevensmodel, samen met de belangrijkheid van deze verbanden, suggereert dat Jesse Kusters goed zou
                kunnen passen bij de functie van Personeelsassistent bij Aydco.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Jesse Kusters</u> en <u>Aydco</u></h5>
                <h6>Jesse Kusters. Maastricht, Nederland (<img src='static/location.png' class='textimg'>2.4 KM).<br></h6>
                <p>Jesse Kusters lijkt goed te passen bij de functie van Personeelsassistent bij Aydco op basis van de informatie in het gegevensmodel:</p>
                <ul>
                    <li>Jesse heeft vaardigheden op het gebied van <span style='background-color: #fcba0344;'>Interne audit</span>, net als <span style='background-color: #f2688444;'>Bobby van Dijk</span>, wat relevant is voor de functie.</li>
                    <li>Jesse heeft ervaring op het gebied van <span style='background-color: #fcba0344;'>bestandsbeheer</span>, wat nuttig kan zijn in een HR-rol.</li>
                    <li>Jesse heeft eerder samengewerkt met <span style='background-color: #f2688444;'>Kai Peters</span>, een Personeelsassistent bij Aydco, wat de integratie kan vergemakkelijken.</li>
                </ul>"""
            }
        },
        "HR-administratief specialist, Ahold Delhaize" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Ahold Delhaize</u></h5> 
                <h6>HR-administratief specialist, Ahold Delhaize. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de rol van HR-administratief specialist bij Ahold Delhaize goed zou kunnen passen bij Chris de Vries, en hier is waarom:</p>
                <p>Allereerst heeft Chris de Vries eerder gewerkt als <span style='background-color: #2bc25344;'>HR Bedrijfspartner bij Soma Works</span>. Deze functie deelt enkele overeenkomsten met de beoogde rol van HR-administratief specialist, 
                wat aangeeft dat Chris de relevante vaardigheden en kennis bezit die nodig zijn voor deze functie.</p>
                <p>Daarnaast heeft <span style='background-color: #f2688444;'>Jules Rosmalen</span>, die eerder de positie van HR-administratief specialist bij Ahold Delhaize heeft vervuld, deze rol succesvol uitgeoefend.
                Dit geeft aan dat Ahold Delhaize bekend is met deze functie en dat Jules mogelijk waardevolle inzichten en expertise heeft die Chris kan benutten bij het vervullen van deze rol.</p>
                <p>Bovendien heeft Chris de Vries interesse getoond in het type functie van <span style='background-color: #fcba0344;'>Klantenservice specialist</span>. 
                Hoewel dit op het eerste gezicht misschien niet direct gerelateerd lijkt aan HR-administratie, toont het de veelzijdigheid en bereidheid van Chris om 
                verschillende aspecten van werk te verkennen, wat een positieve eigenschap is in veel functies, inclusief die van HR-administratief specialist.</p>
                <p>In combinatie wijzen deze factoren erop dat Chris de Vries goed in staat zou kunnen zijn om de rol van HR-administratief specialist bij Ahold Delhaize met succes te vervullen, volgens het XAI-model.</p>
                """,
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Ahold Delhaize</u></h5> 
                <h6>HR-administratief specialist, Ahold Delhaize. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de rol van HR-administratief specialist bij Ahold Delhaize goed zou kunnen passen bij Chris de Vries om de volgende redenen:</p>
                <ul>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>HR Bedrijfspartner bij Soma Works</span>, wat relevante vaardigheden oplevert voor de HR-administratief specialist.</li>
                    <li><span style='background-color: #f2688444;'>Jules Rosmalen</span> heeft eerder met succes de functie van HR-administratief specialist bij Ahold Delhaize vervuld, wat duidt op bekendheid binnen het bedrijf.</li>
                    <li>Chris heeft interesse getoond in vergelijkbare functies, zoals <span style='background-color: #fcba0344;'>Klantenservice specialist</span>, wat flexibiliteit en bereidheid tot leren aantoont.</li>
                </ul>
                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Ahold Delhaize</u></h5> 
                <h6>HR-administratief specialist, Ahold Delhaize. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de rol van HR-administratief specialist bij Ahold Delhaize goed zou kunnen passen bij Chris de Vries, en hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>HR Bedrijfspartner bij Soma Works</span>, een functie die vergelijkbaar is met de beoogde rol van HR-administratief specialist. 
                Deze ervaring heeft Chris de nodige vaardigheden en inzichten opgeleverd die waardevol kunnen zijn in de nieuwe functie.</p>
                <p>Bovendien heeft <span style='background-color: #f2688444;'>Jules Rosmalen</span> eerder de functie van HR-administratief specialist bij Ahold Delhaize vervuld. De connectie tussen Chris en
                <span style='background-color: #f2688444;'>Jules Rosmalen</span> in het netwerk suggereert dat Chris waardevolle inzichten en informatie kan halen uit de gedeelde ervaring bij Aydco van Chris en Jules 
                en mogelijk een soepele overgang naar de rol kan maken.</p>
                <p>Daarnaast heeft Chris de Vries aangegeven interesse te hebben in de rol van <span style='background-color: #fcba0344;'>Klantenservice specialist</span>. 
                Hoewel dit misschien niet direct gerelateerd lijkt aan HR-administratie, toont het de bereidheid van Chris om verschillende aspecten van werk
                te verkennen, wat een positieve eigenschap is in veel functies, inclusief die van HR-administratief specialist.</p>
                <p>Kortom, de combinatie van relevante ervaring, organisatorische bekendheid en interesse van Chris de Vries in gerelateerde
                gebieden maakt de rol van HR-administratief specialist bij Ahold Delhaize een goede match volgens het XAI-model.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Ahold Delhaize</u></h5> 
                <h6>HR-administratief specialist, Ahold Delhaize. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de rol van HR-administratief specialist bij Ahold Delhaize goed zou kunnen passen bij Chris de Vries om de volgende redenen:</p>
                <ul>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>HR Bedrijfspartner bij Soma Works</span>, wat vergelijkbare vaardigheden biedt voor de rol.</li>
                    <li><span style='background-color: #f2688444;'>Jules Rosmalen</span>, wie overeenkomende ervaring heeft met Chris, heeft eerder de functie van HR-administratief specialist bij Ahold Delhaize vervuld, wat de organisatorische bekendheid aangeeft.</li>
                    <li>Chris heeft interesse getoond in de rol van <span style='background-color: #fcba0344;'>Klantenservice specialist</span>, wat wijst op een brede bereidheid om verschillende functies te verkennen.</li>
                </ul>"""
            }
        },
        "Personeelsassistent, Aydco" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5> 
                <h6>Personeelsassistent, Aydco. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>De reden waarom het XAI-model denkt dat de functie van Personeelsassistent bij Aydco goed bij Chris de Vries past, is gebaseerd op de connecties in het netwerk. Laat me je uitleggen waarom:</p>
                <p>Chris de Vries heeft eerder gewerkt als <span style='background-color: #2bc25344;'>Headhunting consultant bij Staffable Payroll</span>. Hoewel dit misschien anders lijkt, heeft deze rol bepaalde 
                overeenkomsten en vaardigheden die relevant zijn voor een Personeelsassistent bij Aydco. Het XAI-model heeft opgemerkt dat Chris de Vries vaardigheden heeft ontwikkeld die nuttig zijn in beide functies.</p>
                <p>Daarnaast heeft Chris de Vries een <span style='background-color: #fcba0344;'>Kwalificatiecertificaat voor effectenbeoefenaar</span> behaald. Hoewel dit certificaat niet direct verband houdt met personeelszaken, 
                toont het de bereidheid van Chris om nieuwe vaardigheden te verwerven. Dit vermogen om nieuwe dingen te leren en zich aan te passen is een waardevolle eigenschap in elke functie.</p>
                <p>Ten slotte heeft <span style='background-color: #f2688444;'>Isa Michiels</span> eerder gewerkt als Personeelsassistent bij Aydco, wat aangeeft dat deze functie en organisatie bekend zijn in 
                zijn/haar professionele netwerk. Het XAI-model heeft waarschijnlijk opgemerkt dat Chris de Vries connecties heeft met mensen die relevante ervaring hebben in de rol van Personeelsassistent.</p>
                <p>Al deze factoren, samen met de vaardigheden en ervaring van Chris de Vries, hebben bijgedragen aan de conclusie van het XAI-model dat de functie van Personeelsassistent bij Aydco een goede match zou 
                kunnen zijn voor Chris.</p>
                """,
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5> 
                <h6>Personeelsassistent, Aydco. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
 
                <p>Het XAI-model concludeert dat de functie van Personeelsassistent bij Aydco goed past bij Chris de Vries om de volgende redenen:</p>
                <ul>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>Headhunting consultant bij Staffable Payroll</span>, wat vergelijkbare vaardigheden deelt met de functie van Personeelsassistent.</li>
                    <li>Chris heeft het vermogen getoond om nieuwe vaardigheden te leren, zoals blijkt uit het behalen van het <span style='background-color: #fcba0344;'>Kwalificatiecertificaat voor effectenbeoefenaar</span>.</li>
                    <li><span style='background-color: #f2688444;'>Isa Michiels</span> heeft eerder als Personeelsassistent bij Aydco gewerkt, wat aangeeft dat deze functie bekend is in het professionele netwerk van Chris.</li>
                </ul>

                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen:<br>  <u>Chris de Vries</u> en <u>Aydco</u></h5> 
                <h6>Personeelsassistent, Aydco. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model concludeert dat Chris de Vries goed zou kunnen passen bij de functie van Personeelsassistent bij Aydco op basis van zijn/haar eerdere ervaring en vaardigheden.</p>

                <p>Chris heeft gewerkt als <span style='background-color: #2bc25344;'>Headhunting consultant bij Staffable Payroll</span>, wat betekent dat hij/zij bekend is met het identificeren en selecteren van geschikte kandidaten voor vacatures.
                  Deze ervaring in personeelswerving zou hem/haar goed kunnen voorbereiden op de rol van Personeelsassistent, waarbij het beheren van kandidatendossiers en het coördineren van sollicitatieprocessen belangrijk is.</p>

                <p>Bovendien heeft Chris het <span style='background-color: #fcba0344;'>Kwalificatiecertificaat voor effectenbeoefenaar</span> behaald, wat getuigt van zijn/haar vermogen om complexe vaardigheden te verwerven en toe te passen. Deze 
                toewijding aan het behalen van kwalificaties suggereert een sterke werkethiek en het vermogen om nieuwe kennis snel op te nemen, wat waardevol kan zijn in de veelzijdige rol van een Personeelsassistent.</p>

                <p>Kortom, het XAI-model ziet Chris de Vries als een geschikte kandidaat voor de functie van Personeelsassistent bij Aydco vanwege zijn/haar achtergrond in personeelswerving en zijn/haar vermogen 
                om nieuwe vaardigheden te verwerven. Deze combinatie van ervaring en flexibiliteit zou hem/haar goed kunnen positioneren voor succes in deze rol.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>Aydco</u></h5> 
                <h6>Personeelsassistent, Aydco. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model ziet Chris de Vries als een geschikte kandidaat voor de functie van Personeelsassistent bij Aydco vanwege:</p>
                <ul>
                    <li>zijn/haar ervaring als <span style='background-color: #2bc25344;'>Headhunting consultant</span>, wat wijst op zijn/haar vermogen om geschikte kandidaten te vinden.</li>
                    <li>Het behalen van het <span style='background-color: #fcba0344;'>Kwalificatiecertificaat voor effectenbeoefenaar</span>, wat getuigt van zijn/haar toewijding en leervermogen.</li>
                </ul>
                """
            }
        },
        "HR assistent, 043HR" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>043HR</u></h5> 
                <h6>HR assistent, 043HR. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Ik wil graag uitleggen waarom het XAI-model heeft vastgesteld dat de functie van HR assistent (043HR) goed zou passen bij de kandidaat Chris de Vries. Dit begrijpen we door naar de connecties in de grafiek te kijken.</p>

                <p>Chris de Vries heeft een diploma in economie en heeft gewerkt als <span style='background-color: #2bc25344;'>Salarisspecialist bij Sunneroo Zonnepanelen</span>. In die rol heeft hij/zij ervaring opgedaan met
                financiële taken en administratie, wat nuttige vaardigheden zijn voor een HR assistent.</p>

                <p>De HR assistent-functie vereist vaardigheden zoals communicatie, coördinatie, en het kunnen omgaan met administratieve taken. Chris heeft deze vaardigheden ontwikkeld tijdens zijn/haar werk als administratief medewerker bij Cox Techniek.
                Deze ervaring heeft zijn/haar communicatieve vaardigheden versterkt, wat belangrijk is voor het omgaan met personeelszaken en het onderhouden van personeelsrapporten.</p>

                <p>Daarnaast zien we dat <span style='background-color: #f2688444;'>Noël Hoekstra</span> eerder de rol van HR assistent bij 043HR heeft vervuld, en hij/zijhad ook ervaring als 
                <span style='background-color: #2bc25344;'>Salarisspecialist bij Sunneroo Zonnepanelen</span>. Dit suggereert dat er een verband is tussen de rollen van Salarisspecialist en HR assistent, wat 
                de ervaring van Chris als Salarisspecialist relevant maakt voor de HR-assistentpositie.</p>

                <p>Kortom, de combinatie van Chris' financiële achtergrond en zijn/haar ervaring in administratie en klantenservice maken hem/haar een geschikte kandidaat voor de HR assistent-functie. Het XAI-model heeft deze
                overeenkomsten geïdentificeerd en daarom de match als positief beoordeeld.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br> <u>Chris de Vries</u> en <u>043HR</u></h5> 
                <h6>HR assistent, 043HR. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
               <p>Chris de Vries lijkt goed te passen bij de functie van HR assistent. Dit valt te verklaren door de volgende kenmerken van Chris: 
                <ul>
                    <li>Chris de Vries heeft overeenkomende ervaring met <span style='background-color: #f2688444;'>Noël Hoekstra</span>, die eerder is aangenomen voor de positie.</li>
                    <li>De HR assistent-functie vereist communicatie- en coördinatievaardigheden, die Chris heeft ontwikkeld in eerdere rollen.</li>
                    <li>Chris voldoet aan de educatieve eisen en heeft financiële analytische vaardigheden die passen bij de HR assistent-vacature.</li>
                </ul>
                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen:<br> <u>Chris de Vries</u> en <u>043HR</u></h5> 
                <h6>HR assistent, 043HR. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Natuurlijk, ik zal proberen de match tussen Chris de Vries en de functie van HR assistent bij 043HR op een begrijpelijke manier uit te leggen zonder te verwijzen naar de grafische elementen.</p>

                <p>Chris de Vries heeft ervaring opgedaan als <span style='background-color: #2bc25344;'>Salarisspecialist bij Sunneroo Zonnepanelen</span>, waarbij hij/zij verantwoordelijk was voor financiële en administratieve taken. Dit verleden wijst op vaardigheden 
                die nuttig kunnen zijn in de rol van HR assistent bij 043HR, aangezien financiële gegevens vaak een rol spelen in HR-taken, zoals salarisadministratie en budgetbeheer.</p>

                <p>Bovendien heeft Chris de Vries ook gewerkt als <span style='background-color: #2bc25344;'>Administratief assistent bij Cox Techniek</span>. Deze rol vereist organisatorische en administratieve bekwaamheden, wat belangrijke eigenschappen zijn voor 
                een HR assistent. De ervaring van Chris als Administratief assistent kan hem/haar goed voorbereiden op het efficiënt beheren van HR-gerelateerde documentatie en processen.</p>

                <p><span style='background-color: #f2688444;'>Noël Hoekstra</span>, die in het verleden de rol van HR assistent bij 043HR heeft vervuld, heeft op zijn/haar beurt ervaring als <span style='background-color: #2bc25344;'>Salarisspecialist bij Sunneroo Zonnepanelen</span>. 
                Dit geeft aan dat er enige overlap is tussen de functies van Salarisspecialist en HR assistent, wat suggereert dat de vaardigheden van Chris als Salarisspecialist relevant kunnen zijn voor de HR-assistentfunctie.</p>

                <p>Al met al lijkt het erop dat Chris de Vries over een combinatie van financiële, administratieve en organisatorische vaardigheden beschikt, die goed aansluiten bij de vereisten van de HR assistent 
                functie bij 043HR. Bovendien zijn er overgangen en connecties in zijn/haar arbeidsverleden die suggereren dat hij/zij de benodigde competenties kan hebben ontwikkeld tijdens eerdere functies. Dit maakt hem/haar 
                waarschijnlijk een geschikte kandidaat voor de positie.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen:<br> <u>Chris de Vries</u> en <u>043HR</u></h5> 
                <h6>HR assistent, 043HR. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Chris de Vries lijkt goed te passen bij de functie van HR assistent bij 043HR vanwege:</p>
                <ul>
                <li>Zijn/haar ervaring als <span style='background-color: #2bc25344;'>Salarisspecialist bij Sunneroo Zonnepanelen</span>, wat wijst op financiële en administratieve vaardigheden.</li>
                <li>Zijn/haar eerdere rol als <span style='background-color: #2bc25344;'>Administratief assistent bij Cox Techniek</span>, die organisatorische en administratieve bekwaamheden vereiste.</li>
                <li>De overgangen en connecties in zijn/haar arbeidsverleden, zoals <span style='background-color: #f2688444;'>Noël Hoekstra</span>, die aangeven dat zijn/haar competenties relevant kunnen zijn voor de HR-assistentfunctie.</li>
                </ul>"""
            }
        },        
        "Klerk, Accountantskantoor Frenzel & Weijers" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br><u>Chris de Vries</u> en <u>Accountantskantoor Frenzel & Weijers</u></h5> 
                <h6>Klerk, Accountantskantoor Frenzel & Weijers. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Klerk bij Accountantskantoor Frenzel & Weijers een goede match zou kunnen zijn voor Chris de Vries, en hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries eerdere ervaring als <span style='background-color: #2bc25344;'>Medewerker Backoffice/administratieve leiding bij Freddomatic</span>. 
                Hoewel deze rol anders lijkt, heeft het enkele overeenkomsten in taken en vaardigheden met de functie van Klerk. Deze eerdere ervaring kan waardevolle vaardigheden hebben opgeleverd die relevant zijn voor de nieuwe rol.</p>
                <p>Daarnaast heeft Chris de Vries een <span style='background-color: #fcba0344;'>Boekhoudkundige kwalificatie</span> en <span style='background-color: #fcba0344;'>Kwalificaties voor beoefenaars in de effecten- en futures-industrie</span>.
                Hoewel deze kwalificaties niet direct gerelateerd lijken aan de administratieve rol van een Klerk, tonen ze Chris' bekwaamheid en expertise in financiële en administratieve zaken, wat gunstig kan zijn in deze functie.</p>
                <p>Bovendien heeft <span style='background-color: #f2688444;'>Silke Jansen</span>, die ook deze kwalificaties heeft, ervaring als <span style='background-color: #2bc25344;'>Boekhoudassistent bij Huijerjans Adviesgroep</span>, 
                wat onder de categorie van <span style='background-color: #fcba0344;'>Klerk</span> valt. Dit geeft aan dat er vergelijkbare taken en verantwoordelijkheden zijn tussen deze kwalificaties en de rol van klerk.</p>
                <p>Deze combinatie van eerdere ervaring, kwalificaties en organisatorische overeenkomsten duidt erop dat Chris de Vries goed in staat zou kunnen zijn om de rol van Klerk bij 
                Accountantskantoor Frenzel & Weijers met succes te vervullen, volgens het XAI-model.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen:<br> <u>Chris de Vries</u> en <u>Accountantskantoor Frenzel & Weijers</u></h5> 
                <h6>Klerk, Accountantskantoor Frenzel & Weijers. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Klerk bij Accountantskantoor Frenzel & Weijers een goede match zou kunnen zijn voor Chris de Vries om de volgende redenen:</p>
                <ul>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>Medewerker Backoffice/administratieve leiding bij Freddomatic</span>, wat enkele relevante vaardigheden kan hebben opgeleverd.</li>
                    <li>Chris heeft <span style='background-color: #fcba0344;'>kwalificaties in boekhouding en financiën</span>, wat aantoont dat hij/zij bekwaam is in financiële zaken.</li>
                    <li>Er is overeenkomstige ervaring tussen de functie van Chris en die van <span style='background-color: #f2688444;'>Silke Jansen</span>, wat suggereert dat Chris geschikt zou kunnen zijn voor de rol van Klerk.</li>
                </ul>
                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br><u>Chris de Vries</u> en <u>Accountantskantoor Frenzel & Weijers</u></h5> 
                <h6>Klerk, Accountantskantoor Frenzel & Weijers. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Klerk bij Accountantskantoor Frenzel & Weijers goed zou kunnen passen bij Chris de Vries, en hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>Medewerker Backoffice/administratieve leiding bij Freddomatic</span>. Hoewel deze functie op het eerste gezicht anders lijkt dan die van een Klerk, 
                kunnen er overlappingen zijn in de vereiste organisatorische en administratieve vaardigheden.</p>
                <p>Bovendien heeft Chris de Vries een <span style='background-color: #fcba0344;'>Boekhoudkundige kwalificatie (verlopen)</span> en Kwalificaties voor beoefenaars in de effecten- en futures-industrie. Hoewel deze kwalificaties niet direct lijken
                te passen bij de functie van Klerk, wijzen ze op financiële expertise en vaardigheden die nuttig kunnen zijn in administratieve taken.</p>
                <p>Daarnaast heeft <span style='background-color: #f2688444;'>Silke Jansen</span> ervaring als <span style='background-color: #2bc25344;'>Boekhoudassistent bij Huijerjans Adviesgroep</span>, wat onder dezelfde categorie valt als <span style='background-color: #fcba0344;'>Klerk</span>. Dit duidt op vergelijkbare verantwoordelijkheden
                en taken, wat suggereert dat Chris geschiktheid zou kunnen hebben voor de rol van Klerk.</p>
                <p>Deze combinatie van ervaring en vaardigheden geeft aan dat Chris de Vries de benodigde achtergrond heeft om succesvol te zijn als Klerk bij Accountantskantoor Frenzel & Weijers, volgens het XAI-model.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br><u>Chris de Vries</u> en <u>Accountantskantoor Frenzel & Weijers</u></h5> 
                <h6>Klerk, Accountantskantoor Frenzel & Weijers. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>                         
                <p>Het XAI-model heeft vastgesteld dat de functie van Klerk bij Accountantskantoor Frenzel & Weijers een goede match zou kunnen zijn voor Chris de Vries om de volgende redenen:</p>
                <ul>
                    <li>Chris heeft ervaring als <span style='background-color: #2bc25344;'>Medewerker Backoffice/administratieve leiding bij Freddomatic</span>, wat enkele relevante vaardigheden kan hebben opgeleverd.</li>
                    <li>Chris heeft <span style='background-color: #fcba0344;'>kwalificaties in boekhouding en financiën</span>, wat aantoont dat hij/zij bekwaam is in financiële zaken.</li>
                    <li>Er is vergelijkbare ervaring tussen Chris en <span style='background-color: #f2688444;'>Silke Jansen</span>, wat suggereert dat Chris geschikt zou kunnen zijn voor de rol van Klerk.</li>
                </ul>"""
            }
        },        
        "Kantoorbediende/administratief medewerker, BPM Services" : {
            "real" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen: <br><u>Chris de Vries</u> en <u>BPM Services</u></h5> 
                <h6>Kantoorbediende/administratief medewerker, BPM Services. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Kantoorbediende/administratief medewerker bij BPM Services een goede match zou kunnen zijn voor Chris de Vries, en hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>Administratief assistent bij Cox Techniek</span> en als 
                <span style='background-color: #2bc25344;'>Binnenkomstmedewerker bij Hotel Bigarré Maastricht Centrum</span>. Deze rollen impliceren organisatorische en administratieve vaardigheden, aangezien beide vallen
                onder de categorie <span style='background-color: #fcba0344;'>klerk</span>. Deze ervaring kan relevant zijn voor een Kantoorbediende/administratief medewerker, aangezien dit veel overeenkomsten kan 
                hebben met een functie als <span style='background-color: #fcba0344;'>klerk</span> of <span style='background-color: #fcba0344;'>secretaris</span>.</p>
                <p>Bovendien heeft Chris de Vries gewerkt als <span style='background-color: #2bc25344;'>Personeelsassistent bij Majorel</span>. Dit geeft aan dat hij/zij bekend is met secretariële taken. 
                Daarnaast kunnen de vereiste nauwkeurigheid en efficiëntie in administratieve processen overeenkomsten vertonen.</p>
                <p>Deze combinatie van ervaringen en vaardigheden suggereert dat Chris de Vries de benodigde achtergrond heeft om succesvol te zijn als Kantoorbediende/administratief medewerker bij BPM Services volgens het XAI-model.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen:<br> <u>Chris de Vries</u> en <u>BPM Services</u></h5> 
                <h6>Kantoorbediende/administratief medewerker, BPM Services. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Kantoorbediende/administratief medewerker bij BPM Services een goede match zou kunnen zijn voor Chris de Vries, en hier is waarom:</p>
                <ul>
                    <li>Chris heeft relevante ervaring als <span style='background-color: #2bc25344;'>Administratief assistent</span> en <span style='background-color: #2bc25344;'>Binnenkomstmedewerker</span>, 
                    wat wijst op organisatorische en administratieve vaardigheden die nuttig zijn voor een functie als <span style='background-color: #fcba0344;'>klerk</span>.</li>
                    <li>Zijn/haar rol als <span style='background-color: #f2688444;'>Personeelsassistent</span> geeft aan dat hij/zij bekend is met secretariële taken, wat eveneens relevant kan zijn voor de
                      rol van Kantoorbediende/administratief medewerker.</li>
                </ul>
                <p>Deze combinatie van ervaringen en vaardigheden suggereert dat Chris de Vries de benodigde achtergrond heeft om succesvol te zijn als Kantoorbediende/administratief medewerker bij BPM Services volgens het XAI-model.</p>
                """
            },
            "random" : {
                "full" : 
                """<h5>Geschreven uitleg voor de match tussen:<br> <u>Chris de Vries</u> en <u>BPM Services</u></h5> 
                <h6>Kantoorbediende/administratief medewerker, BPM Services. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Kantoorbediende/administratief medewerker bij BPM Services een goede match zou kunnen zijn voor Chris de Vries, en hier is waarom:</p>
                <p>Ten eerste heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>Administratief assistent bij Cox Techniek</span> en als 
                <span style='background-color: #2bc25344;'>Binnenkomstmedewerker bij Hotel Bigarré Maastricht Centrum</span>. Deze rollen vallen onder de categorie <span style='background-color: #fcba0344;'>klerk</span>.
                Deze ervaring in klerkachtige functies suggereert dat Chris de Vries organisatorische en administratieve vaardigheden heeft ontwikkeld, wat belangrijk is voor een Kantoorbediende/administratief medewerker.</p>
                <p>Bovendien heeft Chris de Vries in deze rollen uitgeblonken, wat blijkt uit zijn/haar succesvolle vervulling van de taken als <span style='background-color: #2bc25344;'>Administratief assistent</span> en 
                <span style='background-color: #2bc25344;'>Binnenkomstmedewerker</span>. Dit wijst op zijn/haar vermogen om in vergelijkbare functies, zoals die van Kantoorbediende/administratief medewerker, succesvol te presteren.</p>
                <p>Daarnaast heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>Personeelsassistent bij Majorel</span>, waar hij/zij waarschijnlijk heeft gewerkt aan taken die verband
                houden met secretariële en administratieve verantwoordelijkheden. Deze ervaring kan naadloos overgaan naar de rol van Kantoorbediende/administratief medewerker, waarbij nauwkeurigheid en efficiëntie van essentieel belang zijn.</p>
                <p>Samengevoegd suggereert deze combinatie van ervaringen en vaardigheden dat Chris de Vries goed zou kunnen passen in de rol van Kantoorbediende/administratief medewerker bij BPM Services, zoals voorgesteld door
                het XAI-model.</p>""",
                
                "simple" : 
                """<h5>Geschreven uitleg voor de match tussen: <br><u>Chris de Vries</u> en <u>BPM Services</u></h5> 
                <h6>Kantoorbediende/administratief medewerker, BPM Services. Maastricht, Nederland (<img src='static/location.png' class='textimg'>8.7 KM).<br></h6>
                <p>Het XAI-model heeft vastgesteld dat de functie van Kantoorbediende/administratief medewerker bij BPM Services een goede match zou kunnen zijn voor Chris de Vries, en hier is waarom:</p>
                <ul>
                    <li>Ten eerste heeft Chris de Vries ervaring als <span style='background-color: #2bc25344;'>Administratief assistent bij Cox Techniek</span> en als 
                    <span style='background-color: #2bc25344;'>Binnenkomstmedewerker bij Hotel Bigarré Maastricht Centrum</span>. 
                    Deze rollen vallen onder de categorie <span style='background-color: #fcba0344;'>klerk</span>, wat impliceert dat hij/zij organisatorische en administratieve vaardigheden heeft ontwikkeld.</li>
                    <li>Chris heeft met succes de taken van <span style='background-color: #2bc25344;'>Administratief assistent</span> en <span style='background-color: #2bc25344;'>Binnenkomstmedewerker</span> vervuld, 
                    wat aantoont dat hij/zij goed presteert in vergelijkbare functies.</li>
                    <li>Bovendien heeft hij/zij ervaring als <span style='background-color: #2bc25344;'>Personeelsassistent bij Majorel</span>, waar hij/zij waarschijnlijk secretariële en administratieve verantwoordelijkheden heeft behandeld,
                    wat relevant is voor de rol van Kantoorbediende/administratief medewerker.</li>
                </ul>
                <p>Deze combinatie van ervaringen en vaardigheden suggereert dat Chris de Vries goed zou kunnen passen in de rol van Kantoorbediende/administratief medewerker bij BPM Services, zoals voorgesteld door het XAI-model.</p>"""
            }
        }
    }

    # Actual rankings:

    ##### Candidate-side (Chris de Vries):
    # BPM Services:
    # "gen_pred": 300.4327392578125,
    # "can_pred": 918.6280517578125,
    # "com_pred": 335.8780822753906,
    # "ground_truth": 3.0,

    # 043HR:
    # "gen_pred": 1000.0,
    # "can_pred": 1940.240966796875,
    # "com_pred": -0.2603781223297119,
    # "ground_truth": 1.0,

    # Frenzel & Weijers:
    # "gen_pred": 464.1255798339844,
    # "can_pred": 1073.6793212890625,
    # "com_pred": 200.44549560546875,
    # "ground_truth": 1.0,

    # Aydco:                 
    # "gen_pred": 396.1236572265625,
    # "can_pred": 945.9556274414062,
    # "com_pred": 198.41517639160156,
    # "ground_truth": 1.0,

    # Ahold:
    # "gen_pred": 0.0,
    # "can_pred": 326.3961181640625,
    # "com_pred": 310.2750549316406,
    # "ground_truth": 0.0,


    ##### Company-side (Aydco):
    # Chris de Vries:
    # "gen_pred": 396.1236572265625,
    # "can_pred": 945.9556274414062,
    # "com_pred": 198.41517639160156,
    # "ground_truth": 2.0,

    # Jesse Kusters:
    # "gen_pred": 184.41041564941406,
    # "can_pred": 426.14898681640625,
    # "com_pred": 77.07267761230469,
    # "ground_truth": 1.0,

    # Taylor Meijer:
    # "gen_pred": 409.93408203125,
    # "can_pred": 782.3716430664062,
    # "com_pred": -0.5987280607223511,
    # "ground_truth": 0.0,

    # Sam Appelscha:
    # "gen_pred": 255.06553649902344,
    # "can_pred": 481.59112548828125,
    # "com_pred": -0.06922134011983871,
    # "ground_truth": 0.0,

    # Senna de Boer:
    # "gen_pred": 0.0,
    # "can_pred": 21.9800968170166,
    # "com_pred": 49.565826416015625,
    # "ground_truth": 0.0,
    
    
if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)