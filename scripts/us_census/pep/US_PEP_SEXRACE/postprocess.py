'''
Script to read all
the generated csv for
National, State and County
and generate final csv, MCF, TMCF file
'''

import pandas as pd


csvlist = ["Nationals_Result_1900_1959.csv",
    "Nationals_Result_1960_1979.csv","Nationals_Result_1990_2000.csv",
    "Nationals_Result_2000_2010.csv","Nationals_Result_2010_2020.csv",
    "State_Result_2000_2010.csv",
    "County_Result_2000_2009.csv", "County_Result_2010_2020.csv"]

csvlist1 = ["Nationals_Result_1980_1990.csv","State_Result_1970_1979.csv",
    "State_Result_1980_1990.csv","State_Result_1990_2000.csv",
    "County_Result_1970_1979.csv", "County_Result_1980_1989.csv",
    "County_Result_1990_2000.csv",]

csvlist2 = ["State_Result_2010_2020.csv"]

df1=pd.DataFrame()
df3=pd.DataFrame()
df5=pd.DataFrame()

for i in csvlist:
    df=pd.read_csv(i,header=0)
    for col in df.columns:
        df[col]=df[col].astype("str")
    df1=pd.concat([df,df1],ignore_index=True)

df1['Year']=df1['Year'].astype(float).astype(int)
df1.drop(columns=['Unnamed: 0'],inplace=True)
df1['geo_ID']=df1['geo_ID'].str.strip()
df1.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)
print(df1.columns)
df1.to_csv("postprocess.csv",index=False)
sv_list1=df1.columns.to_list()

for i in csvlist1:
    df2=pd.read_csv(i,header=0)
    for col in df2.columns:
        df2[col]=df2[col].astype("str")
    df3=pd.concat([df2,df3],ignore_index=True)

df3['Year']=df3['Year'].astype(float).astype(int)
df3.drop(columns=['Unnamed: 0'],inplace=True)
df3['geo_ID']=df3['geo_ID'].str.strip()
df3.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)
print(df3.columns)
df3.to_csv("postprocess_aggregate.csv",index=False)
sv_list2=df3.columns.to_list()
print(df3)

for i in csvlist2:
    df4=pd.read_csv(i,header=0)
    for col in df4.columns:
        df4[col]=df4[col].astype("str")
    df5=pd.concat([df4,df5],ignore_index=True)

df5['Year']=df5['Year'].astype(float).astype(int)
#df5.drop(columns=['Unnamed: 0'],inplace=True)
df5['geo_ID']=df5['geo_ID'].str.strip()
df5.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)
print(df5.columns)
df5.to_csv("postprocess_aggregate_state_2010_2020.csv",index=False)
sv_list3=df5.columns.to_list()

print(sv_list1)
print(sv_list2)
print(sv_list3)
# flag=1
# _generate_mcf(sv_list1,flag)
# _generate_tmcf(sv_list1,flag)

# flag=2
# # df1=pd.read_csv("postprocess_aggregate.csv"))
# # #df1.drop(columns=["Unnamed: 0"],inplace=True)
# _generate_mcf(sv_list2,flag)
# _generate_tmcf(sv_list2,flag)

def _generate_mcf(sv_list: list,flag1: int) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template
    Arguments:
        df_cols (list) : List of DataFrame Columns
    Returns:
        None
    """
    mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""

    final_mcf_template = ""
    for sv in sv_list:



        #print(sv)
        if "Total" in sv:
            continue
        if "Year" in sv:
            continue
        if "geo_ID" in sv:
            continue
        gender = ''
        race = ''
        sv_prop = sv.split("_")
        for prop in sv_prop:
            #print(prop)

            if prop in ["Count","Person"]:
                continue
            if "Male" in prop or "Female" in prop:
                gender = "gender: dcs:" + prop
            else:
                race = "race: dcs:" + prop + "\n"
        final_mcf_template += mcf_template.format(sv, race,
                                                    gender) + "\n"
    # Writing Genereated MCF to local path.
    #self.mcf_file_path = "mcf_file.mcf"
    if flag1 == 1:
        with open("Sex_Race.mcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    elif flag1 == 2:
        with open("Sex_Race_aggregate.mcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    else:
        with open("Sex_Race_aggregate_state_2010_2020.mcf",\
             'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

def _generate_tmcf( df_cols: list, flag2: int) -> None:

    """
            This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template
    Arguments:
        df_cols (list) : List of DataFrame Columns
    Returns:
        None
    """

    tmcf_template = """Node: E:postprocess->E{}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{}
measurementMethod: dcs:{}
observationAbout: C:postprocess->geo_ID
observationDate: C:postprocess->Year
observationPeriod: \"P1Y\"
value: C:postprocess->{} 

"""
    j = 0
    measure = ""
    tmcf = ""
    for cols in df_cols:
        if "Year" in cols:
            continue
        if "geo_ID" in cols:
            continue
        if flag2 == 1:
            measure = "CensusPEPSurvey"
        elif flag2 == 2:
            if cols == "Count_Person_Male":
                measure = "dcAggregate/CensusPEPSurvey"
            elif cols == "Count_Person_Female":
                measure = "dcAggregate/CensusPEPSurvey"
            else:
                measure = "CensusPEPSurvey"
        else:
            measure = "dcAggregate/CensusPEPSurvey"
        tmcf = tmcf + tmcf_template.format(j, cols, measure, cols) + "\n"
        j = j + 1
    # Writing Genereated TMCF to local path.
    if flag2 == 1:
        with open("Sex_Race.tmcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    elif flag2 == 2:
        with open("Sex_Race_aggregate.tmcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    else:
        with open("Sex_Race_aggregate_state_2010_2020.tmcf"\
                , 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))

flag=1
_generate_mcf(sv_list1,flag)
_generate_tmcf(sv_list1,flag)

flag=2
_generate_mcf(sv_list2,flag)
_generate_tmcf(sv_list2,flag)

flag=3
_generate_mcf(sv_list3,flag)
_generate_tmcf(sv_list3,flag)
