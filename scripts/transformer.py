import csv
from mdutils.mdutils import MdUtils
list_of_strings=[]

counter=0
with open ('fair_eva_results-DT5101.csv',mode ='r') as file:

   csvFile = csv.reader(file)
   
   for lines in csvFile:
              
              counter+=1
              
              clean=[word.replace('\\n','') for word in lines] 
              list_of_strings.extend(lines)

mdFile = MdUtils('fair_eva_results-DT5101.md')

mdFile.new_table(columns=5,rows=(counter),text=list_of_strings )
mdFile.create_md_file()
