## Function to grab the manual grades for each role from the Wordpress database

## inputs: none
## outputs: manual_grades  (dataframe with one row per crew, crewId and grades for each 8 roles in columns)

from sqlalchemy import create_engine
import pandas as pd


# ----- Get data from wordpress -------------------------------------------------
def main():
    engine = create_engine('mysql://pixelpg4_rigging:PIXs@tt03fl@162.241.219.104/pixelpg4_crew', echo=False)
    manual_grades = pd.read_sql('select * from crew_input', engine)
    # ^^ retrieves data frame of DesignId, GunnerInput, ShielderInput, etc
    engine.dispose()
   
    print('retrieved manual grades from wordpress')
    return manual_grades;   



if __name__== "__main__":
    main()