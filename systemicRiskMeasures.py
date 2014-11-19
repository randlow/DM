#pull data

def pulldata(symbols, Start_Date,End_Date,frequency):
    
    import pandas.io.data as pdio
    import numpy as np
    import pandas as pd
    
    Historical_Prices = pdio.get_data_yahoo(symbols,start= Start_Date,end= End_Date) 
    Open=Historical_Prices['Open'].dropna()  
    Close=Historical_Prices['Close'].dropna()
    Low=Historical_Prices['Low'].dropna()
    High=Historical_Prices['High'].dropna()
    Volume=Historical_Prices['Volume'].dropna()
    Adjusted_Close_Prices = Historical_Prices['Adj Close'].dropna()  
    returns = np.log(Adjusted_Close_Prices/Adjusted_Close_Prices.shift(1)).dropna()
    resampled_data=returns.resample(frequency).dropna()
    
    return resampled_data, Open, Close, Low, High, Volume, Adjusted_Close_Prices


##Systemic Risk Measures##

#Journal Article: Kritzman and Li - 2010 - Skulls, Financial Turbulence, and Risk Management
def MahalanobisDist(returns):#define MahalanobisDistance function
    
        
    #stage1: IMPORT LIBRARIES
    import pandas as pd#import pandas    
    import numpy as np#import numpy
    
    #stage2: CALCULATE COVARIANCE MATRIX
    return_covariance= returns.cov() #Generate Covariance Matrix for historical returns
    return_inverse= np.linalg.inv(return_covariance) #Generate Inverse Matrix for historical returns

    #stage3: CALCULATE THE DIFFERENCE BETWEEN THE SAMPLE MEAN AND HISTORICAL DATA
    means= returns.mean()#Calculate historical returns means for each asset
    diff_means= returns.subtract(means) #Calculate difference between historical return means and the historical returns

    #stage4: SPLIT VALUES FROM INDEX DATES
    values=diff_means.values #Split historical returns from Dataframe
    dates= diff_means.index #Split Dataframe from historical returns

    #stage5: BUILD FORMULA
    md = [] #Define Mahalanobis Distance as md
    for i in range(len(values)):
        md.append((np.dot(np.dot(np.transpose(values[i]),return_inverse),values[i])))  #Construct Mahalanobis Distance formula
        
    #stage6: CONVERT LIST Type TO DATAFRAME Type
    md_array= np.array(md) #Translate md List type to md Numpy type
    Mal_Dist=pd.DataFrame(md_array,index=dates,columns=list('R')) #Join Dataframe and Numpy array back together
    MD= Mal_Dist.resample('M')#resample monthly data by average 
    return MD,Mal_Dist #return Mahalanobis Distance data
    
    
#Journal Article: Kinlaw and Turkington - 2012 - Correlation Surprise
def Correlation_Surprise(returns):
    
    #Stage1: IMPORT LIBRARIES
    import pandas as pd#import pandas 
    import numpy as np #import numpy
     
         #Step1: CALCULATE TURBULENCE SCORE 
     
    #Stage 1: GENERATE TURBULENCE SCORE
    TS= MahalanobisDist(returns)[1]#calculate Turbulence Score from Mahalanobis Distance Function
    
    
         #Step2: CALCULATE MAGNITUDE SURPRISE   
    
    #Stage1: CALCULATE COVARIANCE MATRIX
    return_covariance= returns.cov() #Generate Covariance Matrix for hisotircal returns
    return_inverse= np.linalg.inv(return_covariance) #Generate Inverse Matrix for historical returns
    
    #stage2: CALCULATE THE DIFFERENCE BETWEEN THE MEAN AND HISTORICAL DATA FOR EACH INDEX
    means= returns.mean() #Calculate historical returns means
    diff_means= returns.subtract(means) #Calculate difference between historical return means and the historical returns
    
    #stage3: SPLIT VALUES FROM INDEX DATES
    values=diff_means.values #Split historical returns data from Dataframe
    dates= diff_means.index #Split Dataframe from historical returns
    
    #Stage4: Create Covariance and BLINDED MATRIX 
    inverse_diagonals=return_inverse.diagonal() #fetch only the matrix variances
    inverse_zeros=np.zeros(return_inverse.shape) #generate zeroed matrix with dynamic sizing properties 
    zeroed_matrix=np.fill_diagonal(inverse_zeros,inverse_diagonals) #combine zeroed matrix and variances to form blinded matrix
    blinded_matrix=inverse_zeros #define blinded matrix
    
    #stage5: BUILD FORMULA
    ms = []                                    #Define Magnitude Surprise as ms                
    for i in range(len(values)):
        ms.append((np.dot(np.dot(np.transpose(values[i]),blinded_matrix),values[i])))       

    #stage6: CONVERT LIST Type TO DATAFRAME Type    
    ms_array= np.array(ms)  #Translate ms List type to ts Numpy type
    Mag_Sur=pd.DataFrame(ms_array,index=dates,columns=list('R')) #Join Dataframe and Numpy array back together
    MS=Mag_Sur.resample('M') #create monthly returns for magnitude surprise
    
        
        #step3:CALCULATE CORRELATION SURPRISE
    #stage1: CALCULATE CORRELATION SURPRISE
    Corre_Sur= TS.divide(Mag_Sur)
    
    Correlation_monthly_trail= Corre_Sur*Mag_Sur
    resample_Correlation_monthly= Correlation_monthly_trail.resample('M',how=sum)
    MS_sum=Mag_Sur.resample('M',how=sum)
    Correlation_Surprise_monthly=resample_Correlation_monthly.divide(MS_sum)
    
    return  Correlation_Surprise_monthly, MS
    



#Journal Article: Kritzman et al. - 2011 - Principal Components as a Measure of Systemic Risk
def Absorption_Ratio(returns):
    
    #stage1: IMPORT LIBRARIES    
    import pandas as pd  #import pandas    
    import numpy as np #import numpys  
    import math as mth #import math
    
    #stage1: GATHER DAILY TRAIL LENGTH
    time_series_of_500days=len(returns)-500 #collect data that is outside of initial 500day window
    
    #stage2: GENERATE ABSORPTION RATIO DATA
    plotting_data=[]#create list titled plot data
        
    for i in range(time_series_of_500days):
    
       
        #stage1: CALCULATE EXPONENTIAL WEIGHTING
        returns_500day= returns[i:i+500]#create 500 day trailing window        
        EWMA_returns=pd.ewma(returns_500day, halflife=250)
    
        #stage2: CALCULATE COVARIANCE MATRIX
        return_covariance= EWMA_returns.cov() #Generate Covariance Matrix over 500 day window
    
        #stage3: CALCULATE EIGENVECTORS AND EIGENVALUES
        ev_values,ev_vector= np.linalg.eig(return_covariance) #generate eigenvalues and vectors over 500 day window 
    
        #Stage4: SORT EIGENVECTORS RESPECTIVE TO THEIR EIGENVALUES
        ev_values_sort_high_to_low = ev_values.argsort()[::-1]                         
        ev_values_sort=ev_values[ev_values_sort_high_to_low] #sort eigenvalues from highest to lowest
        ev_vectors_sorted= ev_vector[:,ev_values_sort_high_to_low] #sort eigenvectors corresponding to sorted eigenvalues
    
        #Stage5: COLLECT 1/5 OF EIGENVALUES
        shape= ev_vectors_sorted.shape[0] #collect shape of ev_vector matrix
        round_down_shape= mth.floor(shape*0.2) #round shape to lowest integer
        ev_vectors= ev_vectors_sorted[:,0:round_down_shape] #collect 1/5th the number of assets in sample
    
        #stage6: CALCULATE ABSORPTION RATIO DATA
        variance_of_ith_eigenvector= np.var(ev_vectors,axis=1).sum()
        #variance_of_ith_eigenvector= ev_vectors.diagonal()#fetch variance of ith eigenvector
        variance_of_jth_asset= EWMA_returns.var().sum() #fetch variance of jth asset
    
        #stage7: CONSTRUCT ABSORPTION RATIO FORMULA     
        numerator= variance_of_ith_eigenvector #calculate the sum to n of variance of ith eigenvector
        denominator= variance_of_jth_asset#calculate the sum to n of variance of jth asset
               
        Absorption_Ratio= numerator/denominator#calculate Absorption ratio
    
        #stage8: Append Data
        plotting_data.append(Absorption_Ratio) #Append Absorption Ratio iterations into plotting_data list
        
    
        #stage9: Plot Data
    plot_array= np.array(plotting_data)#convert plotting_data into array
    dates= returns[500:time_series_of_500days+500].index#gather dates index over 500 day window iterations
    Absorption_Ratio_daily=pd.DataFrame(plot_array,index=dates,columns=list('R'))#merge dates and Absorption ratio returns
    Absorption_Ratio= Absorption_Ratio_daily.resample('M', how=None)#group daily data into monthly data
    return  Absorption_Ratio #print Absorption Ratio
    
    #convert to monthly returns 

#Plotting Systemic Risk Measures
def print_systemic_Risk(systemicRiskMeasure):
    
   import matplotlib.pyplot as plt
    
   #1 MahalanobisDistance
   plt.xticks(rotation=50)  #rotate x axis labels 50 degrees
   plt.xlabel('Year')#label x axis Year
   plt.ylabel('Index')#label y axis Index
   plt.suptitle('Mahalanobis Distance Index Calculated from Yahoo Finance World Indices')#label title of graph Historical Turbulence Index Calculated from Daily Retuns of G20 Countries
   plt.bar(systemicRiskMeasure[0].index,systemicRiskMeasure[0].values, width=2)#graph bar chart of Mahalanobis Distance
   plt.show()    
   
   
   #2Correlation Surprise
   Correlation_Surprise= systemicRiskMeasure[1][0] #gather Correlation surprise array
   Magnitude_Surprise= systemicRiskMeasure[1][1]#gather turbulence score array
   
        #Magnitude Suprise   
   plt.xticks(rotation=50)  #rotate x axis labels 50 degrees
   plt.xlabel('Year')#label x axis Year
   plt.ylabel('Index')#label y axis Index
   plt.suptitle('Magnitude Surprise Index Calculated from Monthly Retuns of Yahoo Finance World Indices')#label title of graph Historical Turbulence Index Calculated from Daily Retuns of G20 Countries
   plt.bar(Magnitude_Surprise.index,Magnitude_Surprise.values, width=2)#graph bar chart of Mahalanobis Distance
   plt.show()
   
       #Correlation_Surprise
   #need to find weighted averaged returns
   plt.xticks(rotation=50)  #rotate x axis labels 50 degrees
   plt.xlabel('Year')#label x axis Year
   plt.ylabel('Index')#label y axis Index
   plt.suptitle('Correlation Surprise Index Calculated from Monthly Retuns of Yahoo Finance World Indices')#label title of graph Historical Turbulence Index Calculated from Daily Retuns of G20 Countries
   plt.bar(Correlation_Surprise.index,Correlation_Surprise.values, width=2)#graph bar chart of Mahalanobis Distance
   plt.show()
   
   
   
   #3Absorption Ratio
   plt.xticks(rotation=50)  #rotate x axis labels 50 degrees
   plt.xlabel('Year')#label x axis Year
   plt.ylabel('Index')#label y axis Index
   plt.suptitle('Absorption Ratio Index Calculated from Monthly Retuns of Yahoo Finance World Indices')#label title of graph Absorption Ratio
   plt.plot(systemicRiskMeasure[2].index,systemicRiskMeasure[2].values)#graph line chart of Absorption Ratio
   plt.show()
   
