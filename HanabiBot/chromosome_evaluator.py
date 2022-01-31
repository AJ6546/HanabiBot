# A way to evaluate RuleAgentChromosome
# The objective of this class is that it could easily be extended 
# into a genentic algorithm engine to improve chromosomes.
# M. Fairbank. October 2021.
import sys
from turtle import color
from hanabi_learning_environment import rl_env
from rule_agent_chromosome import RuleAgentChromosome
import os, contextlib
import random
import matplotlib.pyplot as plt 

def run(num_episodes, num_players, chromosome, verbose=True):
    """Run episodes."""
    
    environment=rl_env.make('Hanabi-Full', num_players=num_players)
    game_scores = []
    for episode in range(num_episodes):
        observations = environment.reset()
        agents = [RuleAgentChromosome({'players': num_players},chromosome) for _ in range(num_players)]
        done = False
        episode_reward = 0
        while not done:
            for agent_id, agent in enumerate(agents):
                observation = observations['player_observations'][agent_id]
                action = agent.act(observation)
                if observation['current_player'] == agent_id:
                    assert action is not None   
                    current_player_action = action
                    if verbose:
                        print("Player",agent_id,"to play")
                        print("Player",agent_id,"View of cards",observation["observed_hands"])
                        print("Fireworks",observation["fireworks"])
                        print("Player",agent_id,"chose action",action)
                        print()
                else:
                    assert action is None
            # Make an environment step.
            observations, reward, done, unused_info = environment.step(current_player_action)
            if reward<0:
                reward=0 # we're changing the rules so that losing all lives does not result in the score being zeroed.
            episode_reward += reward
            
        if verbose:
            print("Game over.  Fireworks",observation["fireworks"],"Score=",episode_reward)
        game_scores.append(episode_reward)
    return sum(game_scores)/len(game_scores)

def generate_random_number(lower_lmt,upper_lmt):
    return random.randint(lower_lmt,upper_lmt)

if __name__=="__main__":
    num_players=4
    chromosome=[1, 11, 2, 7, 5, 8, 6]
    best_fitness=0
    best_chromosome=None
    up=[10,20,30,40,50] # Upper limit of range for each path
    ignored=[0,0,0,0,0] # Number of times each path has been ignored
    total_games=0
    times_scored_higher_13=0
    percent_score_higher_than_13=0
    chromosomes_with_score_higher_than_13=[]
    chromosomes_with_score_lower_than_10=[]
    fitness=[]

    file1=open("logger.txt","r+")
    logger=file1.read()
    '''If logger.txt is not empty we split up the string and fill in values for 
    best_chromosome, best_fitness, total_games, total_scored_higher_13 and percent_scored_higher_than_13'''
    if logger != "":
        logged_values=logger.split("| ")
        logged_chromosome=logged_values[0].split(", ")
        logged_up=logged_values[1].split(", ")
        logged_ignored=logged_values[2].split(", ")
            
        chromosome.clear()
        up.clear()
        ignored.clear()
        for value in logged_chromosome:
            chromosome.append(int(value))
        for value in logged_up:
            up.append(int(value))
        for value in logged_ignored:
            ignored.append(int(value))
        best_chromosome=chromosome.copy()
        best_fitness=float(logged_values[3])
        total_games=int(logged_values[4])
        times_scored_higher_13=int(logged_values[5])
        percent_score_higher_than_13=float(logged_values[6])

    file1.truncate(0)
    file1.close()

    '''If best_chromosome_logger.txt is not empty we append chromosomes
    from it to chromosomes_with_score_higher_than_13'''
    file2=open("best_chromosome_logger.txt","r+")
    logged_best_chromosomes = file2.read()
    if logged_best_chromosomes !="":
        temp_chromosome=[]
        logged_values=[x for x in logged_best_chromosomes.split("| ") if x !=""]
        for crm in logged_values:
            temp_chromosome=crm.split(", ")
            temp=[]
            for value in temp_chromosome:    
                temp.append(int(value))
            chromosomes_with_score_higher_than_13.append(temp)
    file2.close()       
        
    '''If worst_chromosome_logger.txt is not empty we append chromosomes
    from it to chromosomes_with_score_lower_than_10'''
    file3=open("worst_chromosome_logger.txt","r+")
    logged_worst_chromosomes = file3.read()
    if logged_worst_chromosomes !="":
        temp_chromosome=[]
        logged_values=[x for x in logged_worst_chromosomes.split("| ") if x !=""]
        for crm in logged_values:
            temp_chromosome=crm.split(", ")
            temp=[]
            for value in temp_chromosome:    
                temp.append(int(value))
            chromosomes_with_score_lower_than_10.append(temp)
    file3.close()
    
    '''Updating the list fitness with logged values'''
    file4=open("fitness.txt","r+")
    logged_fitness = file4.read()
    if logged_fitness !="":
        logged_values=[x for x in logged_fitness.split("| ") if x !=""]
        for fit in logged_values:
            fitness.append(float(fit))
    file4.close()

    print("Best Chromosome: ",chromosome," up: ", up, " ignored: ", ignored, 'best_fitness: ',best_fitness,'Total games: ',total_games,
    "Times Scored Greater than 13: ",times_scored_higher_13,"Percentage of games scored higher than 13: ",percent_score_higher_than_13)
    path=0
    for i in range(1,2): # Range set to 1,2 to play game only once
        total_games+=1 

        #Setting chromosome with best chromosome
        if best_chromosome is not None:
            chromosome=best_chromosome.copy()
        random_number = generate_random_number(1, up[4])
            
        #1 Delete - pop an element at random position
        if random_number in range(1,up[0]) and len(chromosome)>=4:
            pos=generate_random_number(0, len(chromosome)-1)
            chromosome.pop(pos)
            path=1
            print("Run: ",i," Delete: ",chromosome,"Path: ",path)
        #2 Insert - insert an element to a random position
        elif random_number in range(up[0]+1,up[1])  and len(chromosome)<8:
            pos=generate_random_number(0, len(chromosome))
            if set(chromosome) != set([x for x in range(0,12)]):
                insert_chrom = random.choice([x for x in range(0,12) if x not in chromosome])
                chromosome.insert(pos,insert_chrom)
            path=2
            print("Run: ",i," Insert: ",chromosome,"Path: ",path)
        #3 Choose a New Chromosome from best chomosomes
        elif random_number in range(up[1]+1,up[2]):
            chromosome.clear()
            chromosome = list(chromosomes_with_score_higher_than_13[generate_random_number(0,len(chromosomes_with_score_higher_than_13)-1)]).copy()
            path=3
            print("Run: ",i," New Chromesome: ",chromosome,"Path: ",path)
        #4 Splice of 2 randomly chosen best chromosomes
        elif random_number in range(up[2]+1,up[3]):
            chrom1=set(chromosomes_with_score_higher_than_13[generate_random_number(0,len(chromosomes_with_score_higher_than_13)-1)])
            chrom2=set(chromosomes_with_score_higher_than_13[generate_random_number(0,len(chromosomes_with_score_higher_than_13)-1)])
            chrom1_not_2 = list(chrom1-chrom2)
            chrom_12=chrom1_not_2+list(chrom2)
            len_diff=8-len(chrom_12)            

            for k in range(len_diff):
                x = generate_random_number(0,len(chrom_12)-1)
                chrom_12.pop(x)
            chromosome=chrom_12.copy()
            path=4
            print("Run: ",i," Splice: ",chromosome,"Path: ",path)
        #5 Swap the positions of 2 elements in the chromosome
        else:
            pos1=generate_random_number(0, len(chromosome)-1)
            pos2=generate_random_number(0, len(chromosome)-1)
            chromosome[pos1],chromosome[pos2]=chromosome[pos2],chromosome[pos1]
            path=5
            print("Run: ",i," Swap: ",chromosome,"Pos1: ",pos1,"Pos2: ",pos2,"Path: ",path)

        #Always have 5 and 6 to avoid exception 
        if 5 not in chromosome:
            chromosome.append(5)
        if 6 not in chromosome:
            chromosome.append(6)
            
        # If chromosome is not in best chromosme replace chromosome
        if len(chromosomes_with_score_higher_than_13)> 100:
            fit_chromosome=False
            for k in chromosomes_with_score_higher_than_13:
                if set(chromosome).issubset(set(k)):
                    fit_chromosome=True
            if fit_chromosome==False:
                chromosome.clear()
                chromosome = list(chromosomes_with_score_higher_than_13[generate_random_number(0,len(chromosomes_with_score_higher_than_13)-1)]).copy()
                print("Chromosome not subset of best chromosmes\nUpadating Chromosme: ", chromosome)

        # If chromosome is in Worst chromosme list replace chromosome
        if len(chromosomes_with_score_lower_than_10)>1 and chromosome in chromosomes_with_score_lower_than_10:
            chromosome.clear()
            chromosome = chromosomes_with_score_higher_than_13[generate_random_number(0,len(chromosomes_with_score_higher_than_13)-1)]
            print("Chromosme in worst chromosomes\nUpadating Chromosme: ", chromosome) 

        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull):
                result=run(25,num_players,chromosome,False)
        print("Result: ",result)
        fitness.append(result)
        # Loggin the Best and Worst Chromosomes
        if result>=13:
            times_scored_higher_13+=1
            chromosomes_with_score_higher_than_13.append(chromosome)
        if result<10:
            chromosomes_with_score_lower_than_10.append(chromosome)

        if best_fitness<result:
            best_fitness=result
            best_chromosome=chromosome
            # Increasing probability of rewarding paths
            for x in range(1,6):
                if (x==path and x<=4 and up[x-1]+2<up[x]) or (x==path and x==5):
                    up[x-1]+=2
        elif result<best_fitness:
            # decreasing probability of punishing paths
            for x in  range(1,6):
                if (x==path and x<=4 and up[x-1]-2>up[x]) or (x==path and x==0):
                    up[x-1]-=2             
        # Increasing probability of ignored paths
        for k in range(len(ignored)):
            if k!=path-1:
                ignored[k]+=1
            if (ignored[k]%10==0 and (k+1 <=4) and up[k]+1<up[k+1]) or (ignored[k]%10==0 and k==4):
                up[k]+=1

    # Logging values to logger.txt
    file1=open("logger.txt","r+")
    for k in range(len(best_chromosome)):
        if k !=len(best_chromosome)-1:
            file1.write(str(best_chromosome[k])+", ")
        else:
            file1.write(str(best_chromosome[k])+"| ")
    for k in range(len(up)):
        if k !=len(up)-1:
            file1.write(str(up[k])+", ")
        else:
            file1.write(str(up[k])+"| ")
    for k in range(len(ignored)):
        if k !=len(ignored)-1:
            file1.write(str(ignored[k])+", ")
        else:
            file1.write(str(ignored[k])+"| ")

    file1.write(str(best_fitness)+"| "+str(total_games)+"| "+str(times_scored_higher_13)+"| "+str(round((times_scored_higher_13*100)/total_games,2))+"| ")
    file1.close()

    # Logging values from chromosomes_with_score_higher_than_13 to best_chromosome_logger.txt
    file2=open("best_chromosome_logger.txt","r+")
    if chromosomes_with_score_higher_than_13:
        for crm in chromosomes_with_score_higher_than_13:
            for k in range(len(crm)):
                if k !=len(crm)-1:
                    file2.write(str(crm[k])+", ")
                else:
                    file2.write(str(crm[k])+"| ")
    file2.close()

    # Logging values from chromosomes_with_score_lower_than_10 to worst_chromosome_logger.txt
    file3=open("worst_chromosome_logger.txt","r+")
    if chromosomes_with_score_lower_than_10:
        for crm in chromosomes_with_score_lower_than_10:
            for k in range(len(crm)):
                if k !=len(crm)-1:
                    file3.write(str(crm[k])+", ")
                else:
                    file3.write(str(crm[k])+"| ")
    file3.close()

    #Logging in fitness values
    file4 = open("fitness.txt","r+")
    if fitness:
        for fit in fitness:
            file4.write(str(fit)+"| ")
    file4.close()
    print("\nBest chromosome",best_chromosome,"Best Fitness",best_fitness,"\n")
    print("Current chromosome",chromosome,"Fitness",result,"\n")

    '''Using scatter plot to display score against number of games played'''
    fig = plt.figure(figsize=(50,30))
    plt.scatter(list([x for x in range(1,total_games+1)]), fitness, color='red')
    #plt.plot(list([x for x in range(1,total_games+1)]), fitness, color='blue')
    plt.title('Games Played vs Score', fontsize=20)
    plt.xlabel('Games Played', fontsize=20)
    plt.ylabel('Score', fontsize=20)
    plt.show()
    fig.savefig('Score Graph')
        


