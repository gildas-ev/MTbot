from discord import *
from discord.ext import commands
from discord.utils import get

import aiohttp
from bs4 import *
from asyncio import *
from re import compile

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from random import randint

import AnnexePendu
import AnnexeCompteBon
import AopsCore

from traceback import format_exc
from yaml import safe_load

intents = Intents.default()
intents.members = True

description = 'Bot Mathraining.'
bot = commands.Bot(command_prefix='&', description='Bot Mathraining, merci aux génialissimes créateurs !',intents=intents)

#____________________CONSTANTES_______________________________

with open('options.yml', 'r') as options_file : options = safe_load(options_file)

NomsRoles = ["Grand Maitre", "Maitre", "Expert", "Chevronné", "Expérimenté", "Qualifié", "Compétent", "Initié", "Débutant", "Novice"]

colors = {'Novice' : 0x888888, 'Débutant' : 0x08D508, 'Débutante' : 0x08D508, 'Initié' : 0x008800, 'Initiée' : 0x008800,
          'Compétent' : 0x00BBEE, 'Compétente' : 0x00BBEE, 'Qualifié' : 0x0033FF, 'Qualifiée' : 0x0033FF, 'Expérimenté' : 0xDD77FF,
          'Expérimentée' : 0xDD77FF, 'Chevronné' : 0xA000A0, 'Chevronnée' : 0xA000A0, 'Expert' : 0xFFA000, 'Experte' : 0xFFA000,
          'Maître' : 0xFF4400, 'Grand Maître' : 0xCC0000}

nonRattachee = "Cette personne n'est pas rattachée à un compte Mathraining.\nTaper la commande `&help` pour plus d'informations."

#Firefox-headless
wdoptions = webdriver.FirefoxOptions()
wdoptions.add_argument('-headless')

errmsg ="Une erreur a été rencontrée, contactez un Admin ou un Modérateur."
perms="Vous n'avez pas les permissions pour effectuer cette commande."

dernierResolu = [None]*5

##_________________Fonctions_Annexes____________________

async def GetMTScore(idMT: int) :
    async with aclient.get(f"http://mathraining.be/users/{idMT}") as response: text = await response.text()
    soup = BeautifulSoup(text,"lxml")
    try : 
        htmlscore = soup.find_all('td', limit = 5)
        if htmlscore != [] : return int(htmlscore[4].getText().strip())
        else : return 2 #Identifiant non attribué
    except : 
        if htmlscore[1].getText().strip() == "Administrateur" : return 1 #Administrateur
        else : return 0 #Personne n'ayant aucun point

def roleScore(s):
    """Renvoie le role correspondant au score"""
    try:
        if s >= 7500: role = "Grand Maitre"
        elif s >= 5000: role = "Maitre"
        elif s >= 3200: role = "Expert"
        elif s >= 2000: role = "Chevronné"
        elif s >= 1250: role = "Expérimenté"
        elif s >= 750: role = "Qualifié"
        elif s >= 400: role = "Compétent"
        elif s >= 200: role = "Initié"
        elif s >= 70:  role = "Débutant"
        elif s == 2 : role = "Inconnu"
        elif s == 1 : role = "Administrateur"
        else: role = "Novice"
        return role
    except: return -1
    
async def GetDiscordUser(ctx,user) :
    try :
        user1 = get(ctx.guild.members, name=user)
        if user1 == None :
            user2 = bot.get_user(id=int(user[3:-1]))
            if user2 == None : return bot.get_user(id=int(user))
            else : return user2
        else : return user1
    except : return None
    
async def FindUser(user: Member,canal) :
        idMT = 0
        if user == None : return 0
        async for message in canal.history(limit=1000):
            msg = message.content.split()
            e1=[2,3][user.mention[2]=='!']
            e2=[2,3][msg[0][2]=='!']
            if msg[0][e2:-1] == user.mention[e1:-1]:
                idMT = int(msg[1])
                break
        return idMT #0 si n'est pas dans la liste

async def FindMT(idMT: int, canal) :
        user = 0; test= str(idMT)
        async for message in canal.history(limit=1000):
            msg = message.content.split()
            if msg[1] == test:
                e2=[2,3][msg[0][2]=='!']
                user = int(msg[0][e2:-1])
                break
        return user #0 si n'est pas dans la liste

def Connexion() :
    global driver
    driver = webdriver.Firefox(options=wdoptions)
    driver.get("https://mathraining.be")
    driver.find_element_by_link_text("Connexion").click()
    username = driver.find_element_by_id("tf1")
    username.clear();username.send_keys(options['user'])
    
    password = driver.find_element_by_name("session[password]")
    password.clear();password.send_keys(options['password'])
    
    driver.find_element_by_name("commit").click()    
    
def Deconnexion() :
    driver.find_element_by_xpath("//a[not(contains(text(), 'Théorie')) and not(contains(text(), 'Statistiques')) and not(contains(text(), 'Problèmes')) and @class='dropdown-toggle']").click()
    driver.find_element_by_link_text("Déconnexion").click()
    driver.quit()
    
async def erreur(e,ctx=None,switch=1) :
    err="- "+"[Erreur "+e+'] '+'-'*50+" [Erreur "+e+']'+" -"+'\n'+format_exc()+"- "+"[Erreur "+e+'] '+'-'*50+" [Erreur "+e+']'+" -";print(err)
    err="```diff\n"+err+"```"
    await canalLogsBot.send(err)
    if ctx:
        await ctx.send("**[Erreur "+e+']** '+"`"+errmsg+"`"+" **[Erreur "+e+']**')
        e=Embed()
        if switch == 2 : e.set_image(url=options['AdrienFail'])
        else : e.set_image(url=options['FirmaFail'])
        await ctx.send(embed=e)

##_________________________EVENT_______________________________________

@bot.event
async def on_ready():
    print('------')
    print('Connecté sous')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    global serveur
    global canalInfoBot
    global canalEnAttente
    global canalGeneral
    global canalResolutions
    global canalLogsBot
    global PenduRunner
    PenduRunner = AnnexePendu.Pendu()
    serveur = bot.get_guild(options['IdServeur'])
    canalInfoBot = serveur.get_channel(options['IdInfoBot'])
    canalEnAttente = serveur.get_channel(options['IdEnAttente'])
    canalGeneral = serveur.get_channel(options['IdGeneral'])
    canalResolutions = serveur.get_channel(options['IdResolutions'])
    canalLogsBot = serveur.get_channel(options['IdLogsBot'])
    
    #bot.loop.create_task(background_tasks_mt())
    await bot.change_presence(activity=Game(name="Mathraining | &help"))

@bot.event
async def on_member_join(member):
    fmt = 'Bienvenue '+ member.mention + " ! Pense à lier ton compte Mathraining avec la commande `&ask`. \n" + \
    "Si tu as des problèmes avec cette commande tape `&help` pour en savoir plus sur le bot ou va faire un tour dans <#726480900644143204>. :wink:" 
    await canalGeneral.send(fmt)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
          
@bot.event
async def on_message(message):
    #_____COMMANDE POUR AFFICHER LES PROBLEMES_____    
        
    if '#' in message.content:
        msg = message.content.split()
        for i in msg:
            urlPb = ""
            if i[0]== '#' and i[5:6]=='' and i[4:5]!='' and i[1:5].isdigit() : #On vérifie que le nombre a exactement 4 chiffres
                numeroPb = int(i[1:5])
                with open("Problems.txt", "r") as file:     #On pourrait faire du log(n) si le fichier était trié selon les numéros de pb.
                    for line in file:                       #Mais bon, on a que 153 problèmes, donc c'est pas bien grave !
                        numero, url = map(int, line.split())
                        if numero == numeroPb:
                            urlPb = url; break
            if urlPb:
                aEnvoyer = "Problème " + str(numeroPb) + " : http://www.mathraining.be/problems/" + str(urlPb)
                await message.channel.send(aEnvoyer )
    await bot.process_commands(message)

##_____________________COMMANDES___________________________________

@bot.command(pass_context=True)
async def ask(ctx,idMTnew: int):
    '''Pour pouvoir utiliser le bot: ask @utilisateur idMathraining
    (idMathraining est le nombre dans l'url de votre page de profil sur le site)'''
    pascontent="Nicolas ne va pas être content si vous vous êtes fait un autre compte !! :sweat_smile:"
    contact="Contactez un Admin ou un Modo si vous souhaitez changer de compte."
    user=ctx.message.author
    try:
        msay=await ctx.send("`Chargement en cours ...`")
        idMTold,idMTatt=(await FindUser(user, canalInfoBot)),(await FindUser(user,canalEnAttente))
        if idMTold == 0 and idMTatt == 0 :  
            Score=await GetMTScore(idMTnew)
            UserId,UserIdatt = (await FindMT(idMTnew, canalInfoBot)),(await FindMT(idMTnew,canalEnAttente))
            if UserId != 0 : await msay.edit(content="Ce compte Mathraining appartient déjà à "+str(bot.get_user(UserId))+" !")
            elif UserIdatt != 0: await msay.edit(content="Ce compte Mathraining a déjà été demandé à être relié par "+str(bot.get_user(UserIdatt))+" !")
            elif Score >= 3200 or Score == 1 : await msay.edit(content="Le compte Mathraining renseigné est au moins Expert ou Administrateur, il faut demander à un Admin/Modo du serveur de vous relier !")
            elif Score == 2 : await msay.edit(content="Le compte Mathraining renseigné n'existe pas !")
            else :
                try :
                    Connexion()
                    driver.get("https://www.mathraining.be/discussions/new?qui="+str(idMTnew)) #Sélectionne automatiquement la personne dans les messages.
                    msg="Bonjour !  :-)\n\n Vous avez bien demandé à relier votre compte mathraining avec le compte Discord [b]"+str(user)+"[/b] sur le [url=https://www.mathraining.be/subjects/365?q=0]serveur Mathraining[/url] ?\n Répondez [b]\"Oui\"[/b] (sans aucun ajout) à ce message pour confirmer votre demande, sinon par défaut vous ne serez pas relié. \n Vous devez ensuite taper la commande [b]&verify[/b] sur Discord pour finaliser la demande.\n\n [b]Seul le dernier message de cette conversation sera lu pour confirmer votre demande.[/b] \n[i][u]NB[/u] : Il s'agit d'un message automatique. N'espérez pas communiquer avec ce compte Mathraining.\n[/i]"
                    #supprimé : (A vrai dire, j'ai activé le service sur mon compte pour l'instant. Vous pouvez tout de même me parler ou me signaler un bug ...)
                    m = driver.find_element_by_id("MathInput")
                    m.clear();m.send_keys(msg)
                    driver.find_element_by_name("commit").click()
                    Deconnexion()
                    await canalEnAttente.send(str(user.mention)+ " " + str(idMTnew))
                    await msay.edit(content="Vous venez de recevoir un message privé sur le site. Suivez les instructions demandées.")
                except : await msay.edit(content="Ce service est temporairement indisponible, veuillez réessayer plus tard.\n Vous pouvez toutefois demander à un Admin ou un Modérateur de vous relier manuellement.")
        elif idMTold == idMTnew and idMTold != 0 : await msay.edit(content="Vous êtes déjà relié au bot avec le même id !")
        elif idMTatt == idMTnew and idMTatt !=0 : await msay.edit(content="Vous avez déjà fait une demande avec le même id !")
        elif idMTatt != idMTnew and idMTold ==0 : await msay.edit(content="Vous avez déjà fait une demande avec l'id "+str(idMTatt)+".\n"+pascontent+"\n"+contact)
        else : await msay.edit(content="Vous êtes déjà relié au bot avec l'id "+str(idMTold)+".\n"+pascontent+"\n"+contact)
    except Exception as exc : await erreur('ASK',ctx)

@bot.command(pass_context=True)
async def verify(ctx,user2: Member = None,idMT2: int = 0):
    """Lie le compte d'un utilisateur au bot (ajoute son id MT dans le canal Info-bot) """
    try: 
        user=ctx.message.author
        idMT=(await FindUser(user,canalEnAttente))
        msay = await ctx.send("`Chargement en cours ...`")
        
        if user2 != None and ("Admin" or "Modo") in [y.name for y in user.roles] :  ##Si admin ou modo ...
            #await bot.add_roles(user, get(user2.server.roles, name = "Vérifié") )
            if (await FindUser(user2,canalInfoBot)) == 0 :
                await canalInfoBot.send(str(user2.mention)+ " " + str(idMT2))
        
                role = roleScore(await GetMTScore(idMT2))
                servRole = get(serveur.roles, name = role)
                await user2.add_roles(servRole)
                
                await canalGeneral.send("Un Administrateur/Modérateur a relié "+str(user2)+" au compte Mathraining d'id "+str(idMT2)+" ! Il obtient le rôle `"+role+"`. :clap:")
                await msay.delete()
            else : await msay.edit(content=str(user2)+ " est déjà lié avec l'id "+str(await FindUser(user2,canalInfoBot))+".")
            
        elif idMT!=0 :                            ##Sinon ignore les autres arguments ...
            try :
                Connexion()
                driver.get("https://www.mathraining.be/discussions/new?qui="+str(idMT))
                
                if driver.find_element_by_xpath("//*[contains(@id, 'normal')]").text[:-20] in ['Oui','oui'] :##Si c'est 'Oui', c'est bon ! (En fait prend le premier avec un id avec 'normal')
                    msg="Vos comptes Discord et Mathraining sont désormais reliés !"
                    m = driver.find_element_by_id("MathInput")
                    m.clear();m.send_keys(msg)
                    driver.find_element_by_name("commit").click()
                    Deconnexion()
                    
                    await canalInfoBot.send(str(user.mention)+ " " + str(idMT))
                    
                    async for message in canalEnAttente.history(limit=1000):
                        msg = message.content.split()
                        e1,e2=[2,3][user.mention[2]=='!'],[2,3][msg[0][2]=='!']
                        if msg[0][e2:-1] == user.mention[e1:-1]: 
                            await message.delete();break
                            
                    role = roleScore(await GetMTScore(idMT))
                    servRole = get(serveur.roles, name = role)
                    await user.add_roles(servRole)
                    
                    await msay.edit(content="La demande de lien a été acceptée par le compte Mathraining ! Vous obtenez le rôle `"+role+"`! :clap:")
                else :
                    msg="Les comptes Discord et Mathraining en question ne seront pas reliés."
                    m = driver.find_element_by_id("MathInput")
                    m.clear();m.send_keys(msg)
                    driver.find_element_by_name("commit").click()
                    Deconnexion()
                    await msay.edit(content="La demande de lien a été refusée par le compte Mathraining.")
            except : await msay.edit(content="Ce service est temporairement indisponible, veuillez réessayer plus tard.\n Vous pouvez toutefois demander à un Admin ou un Modérateur de vous relier manuellement.")
            
        elif (await FindUser(user,canalInfoBot))!=0 : await msay.edit(content="Vous êtes déjà lié avec l'id "+str(await FindUser(user,canalInfoBot))+".")
        else : await msay.edit(content="Vous n'avez fait aucune demande pour lier vos comptes Discord et Mathraining.")
        
    except Exception as exc : await erreur('VERIFY',ctx)

@bot.command(pass_context=True)
async def update(ctx,user: Member = None):
    '''Pour mettre à jour son/ses roles'''
    try:
        if user == None : user = ctx.message.author
        idMT=(await FindUser(user,canalInfoBot))

        if idMT != 0:
            role = roleScore(await GetMTScore(idMT))
            if role == -1: await erreur('ROLESCORE',ctx); return 
            
            roles=user.roles
            for roleMembre in roles:
                if roleMembre.name in NomsRoles and roleMembre.name != role : await user.remove_roles(roleMembre)
            
            if role not in [r.name for r in roles] :
                roles=user.roles; await user.add_roles(get(serveur.roles, name = role))
                if user == ctx.message.author : await ctx.send("Bravo, vous obtenez le rôle `"+role+"`! :clap:")
                else : await ctx.send(str(user)+" obtient désormais le rôle `"+role+"`! :clap:")
            else : await ctx.send("Déjà à jour !")
                
        else: await ctx.send(nonRattachee)
    except Exception as exc : await erreur('UPDATE',ctx)

@bot.command(pass_context=True)
async def info(ctx,user = None):
    """Affiche les stats d'un utilisateur lié"""
    try:
        try : 
            num=int(user)
            if len(user) <= 4 : idMT = num
            else : 
                user = (await GetDiscordUser(ctx,user))
                idMT = (await FindUser(user,canalInfoBot))
        except : 
            if user == None :
                user = ctx.message.author
            else :
                user = (await GetDiscordUser(ctx,user))
            idMT = (await FindUser(user,canalInfoBot))
        if idMT != 0:
            url="http://www.mathraining.be/users/"+str(idMT)
            async with aclient.get(url) as response: text = await response.text()
            soup = BeautifulSoup(text, "lxml")
            try : Infos=list(filter(None,[soup.find_all('td', limit = 39)[i].getText().strip() for i in range(39)]))
            except : 
                if (await GetMTScore(idMT)) == 2 : await ctx.send(content="Le compte Mathraining renseigné n'existe pas !");return
                else : 
                    Infos=list(filter(None,[soup.find_all('td', limit = 3)[i].getText().strip() for i in range(3)]))
                    embed = Embed(title=Infos[0] + " - " + Infos[1], url=url, description="Membre n°"+str(idMT))
                    await ctx.send(embed=embed);return

            embed = Embed(title=Infos[0] + " - " + Infos[1], url=url, description="Membre n°"+str(idMT)+3*' '+"Rang : "+Infos[6]+"  Top  "+Infos[8]+(7-len(Infos[6]+Infos[8]))*' ' +" <:gold:836978754454028338> : "+Infos[9]+" <:silver:836978754433319002> : "+Infos[10]+" <:bronze:836978754467135519> : "+Infos[11]+" <:mh:836978314387259442> : "+Infos[12], color=colors[Infos[1]])
            embed.add_field(name="Score : ", value=Infos[4], inline=True)
            embed.add_field(name="Exercices résolus : ", value=''.join(Infos[14].split()), inline=True)
            embed.add_field(name="Problèmes résolus : ", value=''.join(Infos[16].split()), inline=True)
            for i in range(6): embed.add_field(name=Infos[17+2*i]+' :', value=Infos[18+2*i], inline=True)

            await ctx.send(embed=embed)
            #Penser à rajouter les pays à l'avenir ...
        else: await ctx.send(nonRattachee)
    except Exception as exc : await erreur('INFO',ctx)

@bot.command()
async def corrections(ctx,switch=""):
    """Affiche la liste des correcteurs et leurs nombres de corrections"""
    try:
        async with aclient.get("http://www.mathraining.be/correctors") as response: text = await response.text()
        soup = BeautifulSoup(text, "lxml")
        corrections = soup.find_all('td', attrs={"style":u"text-align:center;"})
        correcteurs = soup.find_all('a',{"href":compile(r"/users/.*")})[30:]
        msg=''
        for loop in range(0, len(corrections),2):
            if corrections[loop+1].getText() != "0" or switch == "all":
                n=len(correcteurs[loop//2].getText())
                m=len(corrections[loop].getText())
                msg+='**'+correcteurs[loop//2].getText().strip()+' :** '+(30-n)*' '+corrections[loop].getText() +(7-m)*" " +corrections[loop+1].getText() + "\n"
        embed = Embed(title="Corrections ( ... corrections dont ... les deux dernières semaines) : ", color=0xFF4400,description = msg[0:2047])
        #Petit bug sur les espaces que j'arrive pas à gérer ... + Mettre de plus gros espaces pour économiser les caractères
        #cf. https://emptycharacter.com/ (en fait je crois qu'il y a pas plus gros ...)
        await ctx.send(embed=embed)
    except Exception as exc : await erreur('CORRECTIONS',ctx)

@bot.command()
async def solved(ctx, user: Member, idpb: int):
    """Indique si le problème numéro numPb a été résolu par l'utilisateur"""
    try:
        idMT=(await FindUser(user,canalInfoBot))
        if idMT != 0:
            async with aclient.get(f"http://mathraining.be/users/{idMT}") as resp : response = await resp.text()
            namepb = '#' + str(idpb)
            await ctx.send("Problème"+[" non "," "][namepb in response]+"résolu par l'utilisateur.")
        else: await ctx.send(nonRattachee)
    except Exception as exc : await erreur('SOLVED',ctx)

@bot.command()
async def hi(ctx):
    await ctx.send("Salut ! Comment vas-tu ?")
    
@bot.command(pass_context = True)
async def say(ctx,*args):
    
    if ("Admin" or "Modo") in [y.name for y in serveur.get_member(ctx.message.author.id).roles] :
        msg = ""
        for i in range(len(args)): msg += args[i]+" " #le dernier espace ne va pas être pris en compte sur discord. hm ...
        await canalGeneral.send(msg)
    else : await ctx.send(perms)
    
@bot.command()
async def compte(ctx, tuile: tuple = (-1,-1,-1,-1,-1,-1),trouver: int = -1,sols=1):
    try:
        if (tuile,trouver,sols) == ((-1,-1,-1,-1,-1,-1),-1,1) :
            resultat,tuiles = AnnexeCompteBon.compteBon()
            tirage="Tuiles : " + " ".join(map(str,tuiles)) +  "\nÀ trouver : " + str(resultat)
            embed = Embed( title = "Le compte est bon", color = 0xFF4400 )
            embed.add_field( name = "Tirage", value = tirage, inline = False )
        else:
            tuile2=[];tmp=tuile;i=1 #Tuile est en fait de la forme ('2',',','1','0',',','5',...)
            embed = Embed( title = "Le compte est bon", color = 0xFF4400 )
            while ',' in tmp :
                while tmp[i]!=',' : i+=1
                tuile2+=[int(''.join(tmp[0:i]))];tmp=tmp[i+1:];i=0
            tuile2+=[int(''.join(tmp))] #Ne pas oublier le dernier nombre ...
            if len(tuile)==6 :
                res=AnnexeCompteBon.Solve(trouver,tuile2,sols); msg = ''
                for s in res : msg+=s;msg+='\n'
            #print(msg)
                if msg : embed.add_field( name = "Voici "+str(len(res))+" solution(s) choisie(s) au hasard :", value = msg, inline = False)
                else : embed.add_field( name = "Mince !", value = "Il n'y a pas de solution ...", inline = False)    
            else : embed.add_field( name = "Mince !", value = "Il n'y a pas le bon nombre de tuiles ...", inline = False)    
        await ctx.send(embed=embed)
    except Exception as exc : await erreur('COMPTE',ctx)
     
@bot.command()
async def lettres(ctx):
    try:
        tirage="Tuiles : " + " ".join(AnnexeCompteBon.Lettres())
        embed = Embed( title = "Le mot le plus long", color = 0xFF4400 )
        embed.add_field( name = "Tirage", value = tirage, inline = False)
        await ctx.send(embed=embed)
    except Exception as exc : await erreur('LETTRES',ctx)
          
@bot.command()
async def pendu(ctx, tuile: str = ''):
    try: await AnnexePendu.pendu(ctx, tuile, PenduRunner)
    except Exception as exc : await erreur('PENDU',ctx,2)
    
@bot.command()
async def citation(ctx):
    try:
        async with aclient.get("http://math.furman.edu/~mwoodard/www/data.html") as response: text = await response.text()
        soup = BeautifulSoup(text, "lxml") #Penser à modifier la source soi-même ?
        bout = str(soup.find_all('p')[randint(0,756)]).replace("<br/>", "\n") 
        citation = (BeautifulSoup(bout, "lxml").getText()).split('\n')
        c=''
        for s in citation[1:-2] : c+=(s+'\n')
        c+=citation[-2]
        embed = Embed(title=citation[0], colour=0x964b00, description='_'+c+'_')
        embed.set_author(name="Citations Mathématiques")
        embed.set_footer(text=citation[-1])
        await ctx.send(embed=embed)
    except Exception as exc : await erreur('CITATION',ctx)

@bot.command(pass_context = True)
async def aops(ctx):
    try: await AopsCore.aopscore(bot,ctx)
    except Exception as exc : 
        await erreur('AOPS',ctx)
        try : driver.quit()
        except : return

@bot.command(pass_context = True)
async def oops(ctx):
    await ctx.message.add_reaction('😅')
    
@bot.command(pass_context = True)
async def trivial(ctx):
    await ctx.message.add_reaction('😒')
    
@bot.command(pass_context = True)
async def makeloose(ctx,user:Member = None):
    try :
        author = ctx.message.author
        await (ctx.message).delete()
        if not author == user : await ctx.send(str(user.mention)+" _a perdu ..._")
        else : await ctx.send(str(user.mention)+" _a perdu tout seul ..._")
        await user.send("_42_")
    except :
        try : await (ctx.message).delete();await ctx.send('<:blurryeyes:622399161240649751>')
        except : await ctx.send('<:blurryeyes:622399161240649751>')
    
bot.remove_command('help')
@bot.command(pass_context = True)
async def help(ctx):
    try:
        embed = Embed(title="Mathraining bot", type="rich", description="Préfixe avant les commandes : &. \n [Le code source est disponible.](https://github.com/Firmaprim/MTbot/)", color=0x87CEEB)
        embed.add_field(name="ask idMathraining", value="Pour demander à rattacher votre compte Mathraining." +
        "\n idMathraining est le nombre dans l'url de votre page de profil sur le site.", inline=False)
        embed.add_field(name="verify", value="Pour valider le lien de votre compte Mathraining avec votre compte Discord.", inline=False)
        embed.add_field(name="update", value="Pour mettre à jour son rang.", inline=False)
        embed.add_field(name="info (utilisateur/idMathraining)", value="Donne le score et le rang Mathraining de l'utilisateur Discord ou Mathraining."
        +"\n Les mentions, les surnoms tout comme les id Mathraining fonctionnent.\n Par défaut prend la personne qui a envoyé la commande comme utilisateur.", inline=False)
        embed.add_field(name="corrections (all)", value="Affiche la liste des correcteurs (qui ont corrigé récemment ou pas avec \"all\") et leurs contributions.", inline=False)
        embed.add_field(name="solved utilisateur numPb", value="Indique si le problème numéro numPb a été résolu par l'utilisateur.", inline=False)
        embed.add_field(name="hi", value="Permet d'effectuer un ping avec le bot.", inline=False)
        embed.add_field(name="compte (a,b,c,d,e,f ÀTrouver NbrSolutions)", value="Effectue un tirage de chiffres si aucun argument n'est donné, résout le tirage sinon.", inline=False)
        embed.add_field(name="lettres", value="Effectue un tirage de lettres.", inline=False)
        embed.add_field(name="pendu", value="Pour jouer au pendu.", inline=False)
        embed.add_field(name="citation", value="Affiche une citation mathématique au hasard.\n Source : [Furman University, Mathematical Quotations Server](http://math.furman.edu/~mwoodard/mquot.html)", inline=False)
        embed.add_field(name="aops", value="Permet d'avoir accès aux problèmes AoPS et les afficher.", inline=False)
        embed.add_field(name="help", value="Affiche ce message en MP.", inline=False)

        await (ctx.message.author).send(embed=embed)
    except Exception as exc :
        await erreur('HELP',ctx)
        await ctx.send("Peut-être avez-vous bloqué les messages privés, ce qui empêche le bot de communiquer avec vous.")

##Tâches d'arrière-plan

async def background_tasks_mt():
    debut=0
    numsOld=[0]*4
    await bot.wait_until_ready()
    while not bot.is_closed :
        try:
            #Chiffres remarquables 
            async with aclient.get("http://www.mathraining.be/") as response: text = await response.text()
            soup = BeautifulSoup(text,"lxml")
            info = soup.find_all('td',attrs={"class":u"left"})
            nums=list(map(lambda t : t.getText(),info))
            if debut == 0: print("Le bot vient juste d'être lancé !")
            elif numsOld != nums and (0 in list(map(lambda x: int(x)%100,nums[0:2])) or 0 in list(map(lambda x: int(x)%1000,nums[2:4]))) :
                if nums[0] != numsOld[0] and int(nums[0])%100==0: msg = "Oh ! Il y a maintenant " + nums[0] + " utilisateurs sur Mathraining !🥳\n"
                else: msg = "Il y a " + nums[0] + " utilisateurs sur Mathraining.\n"
                if nums[1] != numsOld[1] and int(nums[1])%100==0: msg += "Oh ! Il y a maintenant " + nums[1] + " problèmes résolus ! 🥳\n"
                else: msg += "Il y a " + nums[1] + " problèmes résolus.\n"
                if nums[2] != numsOld[2] and int(nums[2])%1000==0: msg += "Oh ! Il y a maintenant " + nums[2] + " exercices résolus ! 🥳\n"
                else: msg += "Il y a " + nums[2] + " exercices résolus.\n"
                if nums[3] != numsOld[3] and int(nums[3])%1000==0: msg += "Oh ! Il y a maintenant " + nums[3] + " points distribués ! 🥳"
                else: msg += "Il y a " + nums[3] + " points distribués."
                numsOld=nums
                await canalGeneral.send(msg)
            
            #Résolutions récentes
            async with aclient.get("http://www.mathraining.be/solvedproblems") as response: text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            cible = soup.find_all('tr');level = 1
            for i in range(0, len(cible)):
                td = BeautifulSoup(str(cible[i]), "lxml").find_all('td')
                if len(td) > 3:
                    if (td[3].getText().replace(" ", "")[4]).isdigit() and int(td[3].getText().replace(" ", "")[4]) == level:
                        msg = td[2].getText() + " vient juste de résoudre le problème " + td[3].getText().replace(" ", "").replace("\n", "")
                        if dernierResolu[level-1] != msg:
                            dernierResolu[level-1] = msg
                            if debut != 0: await canalResolutions.send(msg);print(msg)
                        level += 1
                        if level == 6: break
            debut = 1
            await sleep(10)
        except Exception as exc :
            await erreur('BACKGROUND',ctx);continue
#______________________________________________________________

try:
    aclient = aiohttp.ClientSession()
    bot.run(options['token']) #Token MT
except :
    run(aclient.close())
    driver.quit()
finally:
    run(aclient.close())
    driver.quit()
