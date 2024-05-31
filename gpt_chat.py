import os
import openai
import tiktoken
import json
import tkinter as tk
from tkinter import ttk, Text, filedialog as fd

# ----------------------------------
# déclaration des variables principales
# ----------------------------------

# clé d'api
cle_api = "key"

# paramètres par défaut

# modèle de langage
modele = "text-davinci-003"

# température
temperature = 0

# nom affiché pour l'interlocuteur humain
human_name = "Humain"

# nom affiché pour l'interlocuteur IA
ai_name = "IA"

# maximum (limite) de tokens pour prompt + reponse (4000 est le max possible pour text-davinci-003)
max_tokens = 3000

# optionnel, phrase insérée avant le prompt pour orienter l'ia
pre_prompt = ""

# ----------------------------------
# traitement des tokens
# ----------------------------------

# fonction pour compter les tokens d'un texte
def tokeniser(texte,modele):
    # encodage pour comptage des tokens selon le modele
    encodage = tiktoken.encoding_for_model(modele)
    # comptage
    nb_tokens = len(encodage.encode(texte))
    return nb_tokens

# ----------------------------------
# traitements de l'api
# ----------------------------------

# initialise / authentifie l'api
openai.api_key = cle_api

# fonction de requete
def requete_api(entree,reste_tokens,temperature,modele):
   reponse = openai.Completion.create(model=modele, prompt=entree, temperature=temperature, max_tokens=reste_tokens)
   texte_reponse = reponse["choices"][0]["text"]
   return texte_reponse

# ----------------------------------
# fonctions principales
# ----------------------------------

# fonction de traitement du prompt
def traiteEntree():
    # lecture des paramètres
    params_json = param_store.get('1.0','end')
    params = json.loads(params_json)
    modele = params["settings"][0]["modele"]
    max_tokens = int(params["settings"][1]["max_tokens"])
    temperature = int(params["settings"][2]["temperature"])
    pre_prompt = params["settings"][3]["pre_prompt"]
    human_name = params["settings"][4]["human_name"]
    ai_name = params["settings"][5]["ai_name"]
    # lecture du prompt
    entree = prompt_zone.get('1.0','end')
    # controle que le prompt n'est pas vide
    if (len(entree) < 2):
        label_info.config(text="Le prompt ne peut pas être vide !")
        return
    # controle que le prompt n'est pas trop grand
    nb_tokens_entree = tokeniser(entree,modele)
    if (nb_tokens_entree > max_tokens):
        label_info.config(text="Le prompt dépasse la limite, à réduire...")
        return
    # lecture de l'historique de session actuel
    historique_session = hist_store.get('1.0','end-1c')
    # lecture de l'historique de chat affiche
    hist_zone["state"] = "normal"
    historique_complet = hist_zone.get('1.0','end-1c')
    hist_zone["state"] = "disabled"
    # preparation du prompt final
    prompt_final = historique_session + "\n" + human_name + " : " + entree + "\n" + ai_name + " :"
    # controle qu'il reste des tokens pour la reponse
    nb_tokens_prompt_f = tokeniser(prompt_final,modele)
    reste_tokens = max_tokens-nb_tokens_prompt_f
    if (reste_tokens < 10): 
        # reinitialisation de l'historique de session & prompt final
        if (pre_prompt != ""):
            historique_session = pre_prompt
        else:
            historique_session = ""
        prompt_final = historique_session + "\n" + human_name + " : " + entree + "\n" + ai_name + " :"
        # marquage de la limite de "memoire" dans l'historique de chat
        historique_complet = historique_complet + "\n------------------\nLimite de mémoire : l'IA ignore tout ce qui se situe avant cette ligne \n------------------\n"
        # reinitialisation des tokens 
        nb_tokens_prompt_f2 = tokeniser(prompt_final,modele)
        reste_tokens2 = max_tokens-nb_tokens_prompt_f2
        # envoi a l'api
        reponse = requete_api(prompt_final,reste_tokens2,temperature,modele)
    else:
        # envoi a l'api
        reponse = requete_api(prompt_final,reste_tokens,temperature,modele)
    # insertion de la reponse dans les deux historiques
    historique_session = prompt_final + " " + reponse
    historique_complet = historique_complet + "\n" + human_name + " : " + entree + "\n" + ai_name + " : " + reponse
    # affichage de l'historique de chat (remplace l'existant)
    hist_zone["state"] = "normal"
    hist_zone.delete('1.0','end')
    hist_zone.insert('1.0',historique_complet)
    hist_zone["state"] = "disabled"
    # sauvegarde de l'historique
    hist_store.delete('1.0','end')
    hist_store.insert('1.0',historique_session)
    # effacement du precedent prompt
    prompt_zone.delete('1.0','end')

# fonction pour enregistrer la conversation
def enregistrement(nom_fichier):
    # lecture des paramètres
    params_json = param_store.get('1.0','end')
    params = json.loads(params_json)
    modele = params["settings"][0]["modele"]
    max_tokens = params["settings"][1]["max_tokens"]
    temperature = params["settings"][2]["temperature"]
    pre_prompt = params["settings"][3]["pre_prompt"]
    human_name = params["settings"][4]["human_name"]
    ai_name = params["settings"][5]["ai_name"]
    # lecture de l'historique de session actuel
    historique_session = hist_store.get('1.0','end-1c')
    # lecture de l'historique de chat affiche
    hist_zone["state"] = "normal"
    historique_complet = hist_zone.get('1.0','end-1c')
    hist_zone["state"] = "disabled"
    # ecriture des donnees dans un dictionnaire
    donnees = {
    "settings": [
        {"modele":modele},
        {"max_tokens":max_tokens},
        {"temperature":temperature},
        {"pre_prompt":pre_prompt},
        {"human_name":human_name},
        {"ai_name":ai_name}
        ],
    "hist_store":historique_session,
    "hist_zone":historique_complet
    }
    # export des donnees au format json dans le fichier
    f = open(nom_fichier,"wt")
    json.dump(donnees,f)
    f.close()

# action enregistrer sous (dialogue)
def enregistrerSous():
    # boite de dialogue pour placer et nommer le fichier
    nom_fichier = fd.asksaveasfilename()
    # si annulation
    if (nom_fichier == ""):
        return
    enregistrement(nom_fichier)
    # sauvegarde du nom du fichier
    filename_store.delete('1.0','end')
    filename_store.insert('1.0',nom_fichier)
    # activation du choix enregistrer dans le menu fichier
    menu_fichier.entryconfig("Enregistrer",state="normal")

# action enregistrer (rapide)
def enregistrer():
    # lecture du nom du fichier
    nom_fichier = filename_store.get('1.0','end-1c')
    enregistrement(nom_fichier)

# action exporter
def exporter():
    # boite de dialogue pour placer et nommer le fichier
    fichier = fd.asksaveasfile()
    # si annulation
    if (fichier is None):
        return
    # lecture de l'historique de chat affiche
    hist_zone["state"] = "normal"
    historique_complet = hist_zone.get('1.0','end-1c')
    hist_zone["state"] = "disabled"
    # ecriture dans le fichier
    fichier.write(historique_complet)

# action ouvrir
def ouvrir():
    # si aucun enregistrement : confirmation
    nom_fichier = filename_store.get('1.0','end-1c')
    if (nom_fichier == ""):
        reponse = tk.messagebox.askokcancel(title="Confirmation",message="Ce chat n'a pas été enregistré.\nIl sera perdu si vous en ouvrez un autre.",icon="warning")
        if (reponse is False):
            return
    # boite de dialogue pour ouvrir le fichier
    fichier = fd.askopenfile()
    # si annulation
    if (fichier is None):
        return
    # tentative de lecture
    try:
        donnees = json.load(fichier)
        # lecture des données
        modele = donnees["settings"][0]["modele"]
        max_tokens = donnees["settings"][1]["max_tokens"]
        temperature = donnees["settings"][2]["temperature"]
        pre_prompt = donnees["settings"][3]["pre_prompt"]
        human_name = donnees["settings"][4]["human_name"]
        ai_name = donnees["settings"][5]["ai_name"]
        historique_session = donnees["hist_store"]
        historique_complet = donnees["hist_zone"]
        # sauvegarde des paramètres
        params = {
            "settings": [
                {"modele":modele},
                {"max_tokens":max_tokens},
                {"temperature":temperature},
                {"pre_prompt":pre_prompt},
                {"human_name":human_name},
                {"ai_name":ai_name}
            ]}
        params_json = json.dumps(params)
        param_store.delete('1.0','end')
        param_store.insert('1.0',params_json)
        # affichage de l'historique de chat (remplace l'existant)
        hist_zone["state"] = "normal"
        hist_zone.delete('1.0','end')
        hist_zone.insert('1.0',historique_complet)
        hist_zone["state"] = "disabled"
        # sauvegarde de l'historique
        hist_store.delete('1.0','end')
        hist_store.insert('1.0',historique_session)
        # sauvegarde du nom du fichier
        filename_store.delete('1.0','end')
        filename_store.insert('1.0',fichier.name)
        # activation du choix enregistrer dans le menu fichier
        menu_fichier.entryconfig("Enregistrer",state="normal")
    # message d'erreur si fichier invalide
    except:
        tk.messagebox.showerror(title="Erreur",message="Ce fichier est invalide.\nIl doit s'agir d'un fichier généré par cette application au moment d'un enregistrement (non un export).")


# action nouveau
def nouveau():
    def validation():
        # lecture / controle du formulaire
        form_ok = False
        modele_selection = modele_list.get()
        if (modele_selection == "efficacité 5 / vitesse 1"):
            modele = "text-davinci-003"
            max_tokens = 4000
        elif (modele_selection == "efficacité 4 / vitesse 2"):
            modele = "text-davinci-002"
            max_tokens = 2000
        elif (modele_selection == "efficacité 3 / vitesse 3"):
            modele = "text-curie-001"
            max_tokens = 2000
        elif (modele_selection == "efficacité 2 / vitesse 4"):
            modele = "text-babbage-001"
            max_tokens = 2000
        elif (modele_selection == "efficacité 1 / vitesse 5"):
            modele = "text-ada-001"
            max_tokens = 2000
        temperature = temp_slider.get()
        pre_prompt = pre_prompt_zone.get('1.0','end-1c')
        form_ok = True
        human_name = human_name_zone.get('1.0','end-1c')
        # controle que l'human name n'est pas vide
        if (len(human_name) < 1):
            tk.messagebox.showerror(title="Erreur",message="Le nom pour l'humain ne peut pas être vide !")
            form_ok = False
        ai_name = ai_name_zone.get('1.0','end-1c')
        # controle que l'ai name n'est pas vide
        if (len(ai_name) < 1):
            tk.messagebox.showerror(title="Erreur",message="Le nom pour l'IA ne peut pas être vide !")
            form_ok = False
        if form_ok == True:
            # sauvegarde des paramètres
            params = {
                "settings": [
                    {"modele":modele},
                    {"max_tokens":max_tokens},
                    {"temperature":temperature},
                    {"pre_prompt":pre_prompt},
                    {"human_name":human_name},
                    {"ai_name":ai_name}
                ]}
            params_json = json.dumps(params)
            param_store.delete('1.0','end')
            param_store.insert('1.0',params_json)
            # suppression de l'historique de chat existant
            hist_zone["state"] = "normal"
            hist_zone.delete('1.0','end')
            hist_zone["state"] = "disabled"
            # suppression de l'historique existant
            hist_store.delete('1.0','end')
            # insertion du pre_prompt si non vide
            if (pre_prompt != ""):
                hist_store.insert('1.0',pre_prompt)
            # fermeture de la fenêtre
            fenetre_creation.destroy()

    # pré-remplissage du pre-prompt avec les exemples
    def select_exemple(event):
        exemple_choix = pr_ex_list.get()
        if (exemple_choix == "apprentissage"):
            pre_prompt_zone.delete('1.0','end')
            pre_prompt_zone.insert('1.0',"Je voudrais apprendre la programmation orientée objet en Python. Vous allez maintenant jouer le rôle de mon professeur. Lorsque l'on vous posera des questions, vous donnerez des exemples concrets et ferez référence à des documentations officielles. Je connais déjà les bases de Python, alors assurez-vous de fournir des comparaisons qui m'aideront à comprendre.")
        elif (exemple_choix == "expertise 1"):
            pre_prompt_zone.delete('1.0','end')
            pre_prompt_zone.insert('1.0',"Je veux que vous agissiez en tant qu'expert en informatique. Je vous fournirai toutes les informations nécessaires concernant mes problèmes techniques, et votre rôle sera de résoudre mon problème. Vous devez utiliser vos connaissances en informatique, en infrastructure de réseau et en sécurité informatique pour résoudre mon problème. Il est utile d'utiliser dans vos réponses un langage intelligent, simple et compréhensible pour des personnes de tous niveaux. Il est utile d'expliquer vos solutions étape par étape et à l'aide de puces. Essayez d'éviter trop de détails techniques, mais utilisez-les si nécessaire. Je veux que vous répondiez avec la solution, pas que vous écriviez des explications.")
        elif (exemple_choix == "expertise 2"):
            pre_prompt_zone.delete('1.0','end')
            pre_prompt_zone.insert('1.0',"Je veux que vous agissiez comme un ingénieur en apprentissage automatique. J'écrirai quelques concepts d'apprentissage automatique et il vous appartiendra de les expliquer en termes faciles à comprendre. Cela pourrait consister à fournir des instructions étape par étape pour construire un modèle, à démontrer diverses techniques à l'aide d'images ou à suggérer des ressources en ligne pour une étude plus approfondie.")
        elif (exemple_choix == "recommandation musique"):
            pre_prompt_zone.delete('1.0','end')
            pre_prompt_zone.insert('1.0',"Je souhaite que vous jouiez le rôle de recommandateur de musiques. Je vous fournirai une musique et vous créerez une liste de lecture de 10 musiques similaires à la musique donnée. Vous fournirez un nom et une description pour la liste de lecture. Ne choisissez pas des musiques qui ont le même nom ou le même artiste. N'écrivez pas d'explications ou d'autres mots, répondez simplement avec le nom de la liste de lecture, la description et les musiques.")
        elif (exemple_choix == "guide temporel"):
            pre_prompt_zone.delete('1.0','end')
            pre_prompt_zone.insert('1.0',"Je vous demande de me servir de guide pour mes voyages dans le temps. Je vous indiquerai la période historique ou l'époque future que je souhaite visiter et vous me suggérerez les meilleurs événements, sites ou personnes à découvrir. N'écrivez pas d'explications, fournissez simplement les suggestions et toutes les informations nécessaires.")
        else:
            pre_prompt_zone.delete('1.0','end')

    # si aucun enregistrement : confirmation
    nom_fichier = filename_store.get('1.0','end-1c')
    if (nom_fichier == ""):
        reponse = tk.messagebox.askokcancel(title="Confirmation",message="Ce chat n'a pas été enregistré.\nIl sera perdu si vous en créez un autre.",icon="warning")
        if (reponse is False):
            return
    # fenêtre de création
    fenetre_creation = tk.Toplevel()
    fenetre_creation.title("Nouveau chat")
    fenetre_creation.geometry('400x600+50+50')
    fenetre_creation.config(bg="black")
    fenetre_creation.iconbitmap("./images/openai.ico")
    label_pres = ttk.Label(fenetre_creation,background="black",foreground="white")
    label_pres.config(text="------------------------------ Paramètres ------------------------------ \n Appuyer directement sur valider pour tout laisser par défaut. \n")
    label_pres.pack()
    # sélection du modèle
    label_modele = ttk.Label(fenetre_creation,text="Modèle de langage",background="black",foreground="white")
    label_modele.pack()
    modele_list = ttk.Combobox(fenetre_creation,state="readonly")
    modele_list["values"] = ("efficacité 5 / vitesse 1","efficacité 4 / vitesse 2","efficacité 3 / vitesse 3","efficacité 2 / vitesse 4","efficacité 1 / vitesse 5")
    modele_list.current(0)
    modele_list.pack()
    # réglage de la température
    label_temp = ttk.Label(fenetre_creation,text="Diversité possible des réponses",background="black",foreground="white")
    label_temp.pack()
    temp_slider = ttk.Scale(fenetre_creation,from_=0,to=2,orient="horizontal")
    temp_slider.pack()
    # pre-prompt
    label_pre_prompt = ttk.Label(fenetre_creation,text="\nTexte à insérer au début du chat",background="black",foreground="white")
    label_pre_prompt.pack()
    pre_prompt_zone = Text(fenetre_creation,height=10,background="black",foreground="white",insertbackground="white")
    pre_prompt_zone.pack()
    label_exemples = ttk.Label(fenetre_creation,text="Pré-remplir avec un exemple :",background="black",foreground="white")
    label_exemples.pack()
    # sélection d'exemple de pre-prompt (avec pré-remplissage)
    pr_ex_list = ttk.Combobox(fenetre_creation,state="readonly")
    pr_ex_list.bind('<<ComboboxSelected>>',select_exemple)
    pr_ex_list["values"] = ("apprentissage","expertise 1","expertise 2","recommandation musique","guide temporel","ami")
    pr_ex_list.pack()
    # nom affiché pour l'interlocuteur humain
    label_human_name = ttk.Label(fenetre_creation,text="\nNom affiché pour l'interlocuteur humain",background="black",foreground="white")
    label_human_name.pack()
    human_name_zone = Text(fenetre_creation,height=1,background="black",foreground="white",insertbackground="white")
    human_name_zone.insert('1.0',human_name)
    human_name_zone.pack()
    # nom affiché pour l'interlocuteur IA
    label_ai_name = ttk.Label(fenetre_creation,text="Nom affiché pour l'interlocuteur IA",background="black",foreground="white")
    label_ai_name.pack()
    ai_name_zone = Text(fenetre_creation,height=1,background="black",foreground="white",insertbackground="white")
    ai_name_zone.insert('1.0',ai_name)
    ai_name_zone.pack()
    # bouton de validation
    valid_btn = tk.Button(fenetre_creation,text="Valider",command=validation)
    valid_btn.pack()

# ----------------------------------
# interface graphique
# ----------------------------------

# initialisation de la fenêtre
fenetre = tk.Tk()

# titre
fenetre.title("GPT-3 Chat")

# couleur d'arrière-plan
fenetre.config(bg="black")

# icone
fenetre.iconbitmap("./images/openai.ico")

# dimensions et position
width= int(fenetre.winfo_screenwidth()/1.25)
height= int(fenetre.winfo_screenheight()/1.25)
fenetre.geometry("%dx%d" % (width, height))

# configuration de la grille pour placer les composants
fenetre.rowconfigure(0,weight=5)
fenetre.rowconfigure(1,weight=1)
fenetre.rowconfigure(2,weight=1)
fenetre.rowconfigure(3,weight=1)
fenetre.grid_columnconfigure(0,weight=4)
fenetre.grid_columnconfigure(1,weight=1)

# composants invisibles (pour stocker des données)

# pour l'historique de "session" (remplacé à chaque dépassement de la limite de tokens)
hist_store = Text(fenetre)
# insertion du pre_prompt si non vide
if (pre_prompt != ""):
    hist_store.insert('1.0',pre_prompt)

# pour les paramètres
param_store = Text(fenetre)
# insertion des paramètres par défaut (format json)
params = {
    "settings": [
        {"modele":modele},
        {"max_tokens":max_tokens},
        {"temperature":temperature},
        {"pre_prompt":pre_prompt},
        {"human_name":human_name},
        {"ai_name":ai_name}
    ]}
params_json = json.dumps(params)
param_store.insert('1.0',params_json)

# pour le nom du fichier courant (après un premier enregistrement)
filename_store = Text(fenetre)

# composants visibles

# barre de menu
barre_menu = tk.Menu(fenetre)
fenetre.config(menu=barre_menu)
# menu fichier
menu_fichier = tk.Menu(barre_menu,tearoff=0)
menu_fichier.add_command(label="Nouveau chat",command=nouveau)
menu_fichier.add_command(label="Ouvrir...",command=ouvrir)
menu_fichier.add_command(label="Enregistrer",command=enregistrer,state="disabled")
menu_fichier.add_command(label="Enregistrer sous...",command=enregistrerSous)
menu_fichier.add_command(label="Exporter le texte...",command=exporter)
menu_fichier.add_separator()
menu_fichier.add_command(label="Quitter",command=fenetre.destroy)
barre_menu.add_cascade(label="Fichier",menu=menu_fichier)

# conteneur pour la section d'affichage et sa barre de scrolling
fram = tk.Frame(fenetre,borderwidth=2,relief="solid",background="black")
fram.grid(column=0,row=0,sticky=tk.EW)
# section d'affichage de l'historique de chat (complet comme dans chatgpt, non representatif de la "memoire" de l'ia)
hist_zone = Text(fram,height=40,width=170)
hist_zone.config(background="black",foreground="white",font=("Arial",11))
hist_zone.grid(column=0,row=0,sticky=tk.E)
# desactivation de la zone de texte (empeche l'edition)
hist_zone['state'] = 'disabled'
# barre de scrolling
scrolbar = ttk.Scrollbar(fram,orient="vertical")
scrolbar.grid(column=1,row=0,sticky=tk.NS)
hist_zone["yscrollcommand"] = scrolbar.set
scrolbar.config(command=hist_zone.yview)

# zone d'affichage d'info
label_info = ttk.Label(fenetre,text="",background="black",foreground="white")
label_info.grid(column=0,row=1)

# bouton d'envoi du prompt
bouton = tk.Button(fenetre,text="Envoyer",command=traiteEntree)
bouton.grid(column=0,row=2)

# zone de texte multi-ligne pour le prompt
prompt_zone = Text(fenetre,height=8)
prompt_zone.config(background="black",foreground="white",insertbackground="white",font=("Arial",12))
prompt_zone.grid(column=0,row=5,sticky=tk.EW)

# generation de la fenetre
fenetre.mainloop()

