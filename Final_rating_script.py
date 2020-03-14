
# coding: utf-8

# In[9]:

from py_files import get_crew_from_api
crew_df = get_crew_from_api.main()

from py_files import get_prestige_from_api
prestige_df = get_prestige_from_api.main(crew_df['CharacterDesignId'].values)

from py_files import get_manual_grades
grades_df = get_manual_grades.main()

from py_files import prep_model_features
from py_files import create_model_sets
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from sqlalchemy import create_engine


# In[7]:

def execute_LR_model(roles, crew_df, grades_df):

    # model features
    feats_df = prep_model_features.main(crew_df)
    
    # make a df to hold the model grades. One column per role, plus CharId
    model_grades_df = pd.DataFrame(data = crew_df['CharacterDesignId'])
    
    for role in roles:
        train_features, train_labels, test_features, test_labels = create_model_sets.main(feats_df, grades_df, role, p=False)
    
        # linear regression model
        Regmodel = LinearRegression()
        # run the model on the training set
        Regmodel.fit(train_features, train_labels)
    
        print("\n The model achieves an R2 value of " + 
              str(Regmodel.score(test_features, test_labels)) + " on the " + role + " test set.")
    
        # add grades to the data frame
        y_pred_all = Regmodel.predict(feats_df.drop(['CharacterDesignId'], axis=1))
        model_grades_df[role + 'Grade'] = np.round_(y_pred_all, 0)
        # model_grades_df[f"{role + 'Grade'}"] = np.round_(y_pred_all, 0)
        
        # print(model_grades_df.head())
        
    # -------------------------- Write to wordpress
    engine = create_engine('mysql://pixelpg4_rigging:PIXs@tt03fl@162.241.219.104/pixelpg4_crew', echo=False)    
    model_grades_df.to_sql('crew_grades', con=engine, if_exists='replace', index = False) 
    engine.dispose()
    
    print('Wrote data to Wordpress db.')
    
    return model_grades_df;


# In[8]:

model_grades_df = execute_LR_model(['Gunner', 'Shielder', 'Engineer', 'Pilot', 'Repairer'], crew_df, grades_df)


# In[ ]:




# In[ ]:



