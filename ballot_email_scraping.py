import os
import pandas as pd
import numpy as np
import nltk
import re
#from nltk.stem import PorterStemmer
#from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.decomposition import LatentDirichletAllocation as LDA
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
#import seaborn as sns
#from matplotlib import pyplot as plt
import pdfplumber as plum

os.chdir("/Users/garmo/Desktop/Ballot Analysis/Ballots")





folders = os.listdir()
print(folders)

def getallballots(directory = "/Users/garmo/Desktop/Ballot Analysis/Ballots"):
    os.chdir(directory)
    
    folders = os.listdir()
    
    ballot_files = {}
    
    
    for i in folders:
        os.chdir(str(directory + "/" + i))
        ballot_files.update({i:os.listdir()})
        
    os.chdir(directory)
    return ballot_files
        
    
ballot_files = getallballots()


def get_ballot_as_str(ballot):
    ballot_concat = ""
    num_pages = len(ballot.pages)
    
    for i in list(range(num_pages)):
        ballot_concat = ballot_concat + ballot.pages[i].extract_text()
        
    return ballot_concat




        
        


def break_ballot_by_round(ballot, remove_expressions_lst = None, remove_footer_expression = None, remove_header = None):
    """
    Break up each ballot at each point where the expression Round: \d occurs
    
    remove_expressions_lst is a list of additional expressions to remove based on email format
    and may be different between tournaments
    
    """
    ballot = ballot.lower()
    if remove_expressions_lst != None:
        
        for exp in remove_expressions_lst:
            ballot = re.sub(exp,"",ballot)
    
    if remove_footer_expression != None:
        ballot = re.split(remove_footer_expression,ballot)[0]
        
    ballot = re.split("round\: \d",ballot)
    
    
    if remove_header == 1 and type(ballot) == list:
        return ballot[1:len(ballot)]
    
    else:
    
        return ballot

def get_name_from_ballot(ballot):
    name = re.findall("ballots for \w+\s?\w*",ballot)[0]
    
    name = re.sub("ballots for ","",name)
    
    return name





def scrape_ballot(ballot_file_name, remove_expressions_lst = None, remove_footer_expression = None, remove_header = None):
    
    ballot = plum.open(ballot_file_name)
    ballot = get_ballot_as_str(ballot)
    ballot = ballot.lower()
    ballot_split = break_ballot_by_round(ballot, remove_expressions_lst, remove_footer_expression, remove_header)
    columns = ["Name","Tournament","Division","Event Type","Event","Round","Side","Pos","Rank","Rate","Win","Judge","Feedback","RFD","Source Text"]
    ballots_df = pd.DataFrame(columns=columns)
    
    
    for rd in ballot_split:
    
        judge = re.findall("judge\:\s.+ ",rd)[0]
        judge = re.sub("judge: ","",judge)
        judge = judge.rstrip()
        
        if len(re.findall("rank:\s*\d+",rd)) > 0:
            rank = re.findall("rank:\s*\d+",rd)[0]
            rank = re.findall("\d+",rank)[0]
        
        else:
            rank = None
            
        if len(re.findall("rate:\s*\d+",rd)) > 0:
            rate = re.findall("rate:\s*\d+",rd)[0]
            rate = re.findall("\d+",rate)[0]
        else:
            rate = None
            
        if len(re.findall("decision:\s*l\w*",rd)) > 0:
            win = 0    
        elif len(re.findall("decision:\s*w\w*",rd)) > 0:
            win = 1
        else:
            win = None
        
            
        feedback = re.sub("\n"," ",rd)
        feedback = re.findall("feedback.+",feedback)
        
        if (type(feedback) == list) and (len(feedback) > 0):
            feedback = feedback[0]  
        else:
            feedback = None
            
            
        rfd = re.findall("reason for decision.+",feedback)
        if len(rfd) > 0:
            rfd = rfd[0]
        else:
            rfd = None
            
        
        if len(re.findall("side: \w+",rd)) > 0:
            side = re.findall("side: \w+",rd)
            side = re.sub("side: ","",side[0])
            
        else:
            side = None
            
        try:
            pos = re.findall("pos:.+",rd)[0]
            pos = re.sub("pos: ","",pos)
        except:
            pos = None
            
        event = None
        event_type = None
        name = None
        tournament = None
        division = None
        round_ = None
        
        new_row = {
            "Name":name,
            "Tournament":tournament,
            "Division":division,
            "Event Type":event_type,
            "Event":event,
            "Round":round_,
            "Side":side,
            "Pos":pos,
            "Rank":rank,
            "Rate":rate,
            "Win":win,
            "Judge":judge,
            "Feedback":feedback,
            "RFD":rfd}
        
        ballots_df = ballots_df.append(new_row, ignore_index=True)
    
        
    name = get_name_from_ballot(ballot)
    
    events = re.findall("- .+ \w+\s*\w+\s*\w* round: \d+",ballot)
    events = [e.strip() for e in events]
    events = [re.sub("\sround.+","",e) for e in events]
    events = [re.sub("\- \w\. \w+ ","",e) for e in events]
    
    divisions = re.findall("-.+ \w+\s*\w+\s*\w* round: \d+",ballot)
    divisions = [re.findall("\- \w\.\s\w+",d) for d in divisions]
    divisions = [re.sub("\- \w\.\s","",d[0]) for d in divisions]
    
    
    tournament = re.findall("- .+ ballots",ballot)[0]
    tournament = re.sub("\-|ballots","",tournament).strip()
    
    rounds = re.findall("round: \d+",ballot)
    rounds = [re.sub("round: ","",r) for r in rounds]
    
    ballots_df["Name"] = name
    ballots_df["Tournament"] = tournament
    ballots_df["Event"] = pd.Series(events)
    ballots_df["Round"] = pd.Series(rounds)
    ballots_df["Division"] = pd.Series(divisions)
    ballots_df["Source Text"] = ballot
    
    if name == None:
        ballots_df["Name"] = re.findall("\w+ .* \w+ \-")
        

    return ballots_df


master = pd.DataFrame()

for tournament in ballot_files.keys():
    for ballot_name in ballot_files[tournament]:
    
        ballot = tournament + "/" + ballot_name
        df = scrape_ballot(ballot, remove_expressions_lst = ["https\:.+"], remove_footer_expression = "unsubscribe", remove_header = 1)
    
        master = master.append(df)
        
        print(ballot)


master.loc[((master.Side.isnull()) & np.invert(master.Pos.isnull())),"Side"] = master.loc[((master.Side.isnull()) & np.invert(master.Pos.isnull())),"Pos"]


master["Round"] = master["Round"].astype(int)
master_grp = master.groupby(["Name","Tournament","Event"])
master_sort = master.sort_values(["Name","Tournament","Event"])

x = master_grp.agg({"Round":[max]})



y = master_sort["Name"] + "|" + master_sort["Tournament"] + "|" + master_sort["Event"]
y = y.unique()
y = [re.split("\|",i) for i in y]

df = pd.DataFrame(columns = ["Name","Tournament","Event"])
for i in y:
    name = i[0]
    tournament = i[1]
    event = i[2]
    df = df.append({"Name":name,
                    "Tournament":tournament,
                    "Event":event},ignore_index=True)
df["Last Prelim"] = list(x.iloc[:,0])

df = df.sort_values(["Name","Tournament","Event"])
df2 = df.groupby(["Tournament","Event"])["Max Round"].min()

master1 = pd.merge(master, df,  how='left', on= ["Name","Tournament","Event"])
master1["Break"] = 0

master2 = master1[["Round","Max Round"]]
