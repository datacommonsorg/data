import pandas as pd 
import numpy as np
import sys
from xml.etree.ElementTree import parse

def format_mesh_xml(mesh_xml):
    document = parse(mesh_xml)
    dfcols = ['DescriptorId', 'DescriptorName', 'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day', 'QualifierID', 'QualifierName', 'QualifierAbbreviation', 'ConceptID', 'ConceptName', 'TermID', 'TermName']
    df = pd.DataFrame(columns=dfcols)
    for item in document.iterfind('DescriptorRecord'):
        d1 = item.findtext('DescriptorUI')
        elem = item.find(".//DescriptorName") 
        d1_name = elem.findtext("String")
        date_created = item.find(".//DateCreated")
        if not date_created:
            d1_created_year = np.nan
            d1_created_month = np.nan
            d1_created_day = np.nan
        else:
            d1_created_year = date_created.findtext("Year")
            d1_created_month = date_created.findtext("Month")
            d1_created_day = date_created.findtext("Day")
        date_revised = item.find(".//DateRevised")
        if not date_revised:
            d1_revised_year = np.nan
            d1_revised_month = np.nan
            d1_revised_day = np.nan
        else:
            d1_revised_year = date_revised.findtext("Year")
            d1_revised_month = date_revised.findtext("Month")
            d1_revised_day = date_revised.findtext("Day")
        date_established = item.find(".//DateEstablished")
        if not date_established:
            d1_established_year = np.nan
            d1_established_month = np.nan
            d1_established_day = np.nan
        else:
            d1_established_year = date_established.findtext("Year")
            d1_established_month = date_established.findtext("Month")
            d1_established_day = date_established.findtext("Day")
        quantifier_list = item.find(".//AllowableQualifiersList")
        qualID = []
        qual_name = []
        qual_abbr = []
        if not quantifier_list:
            qualID.append(np.nan)
            qual_name.append(np.nan)
            qual_abbr.append(np.nan)
        else:
            l1 = quantifier_list.findall(".//AllowableQualifier")
            for i in range(len(l1)):
                l2 = l1[i].find(".//QualifierReferredTo")
                qualID.append(l2.findtext("QualifierUI"))
                l3 = l2.find(".//QualifierName")
                qual_name.append(l3.findtext("String"))
                qual_abbr.append(l1[i].findtext("Abbreviation"))
        
        concept_list = item.find(".//ConceptList")
        if not concept_list:
            conceptID = np.nan
            conceptName = np.nan
            termUI = np.nan
            termName = np.nan
        else:
            c1 = concept_list.findall(".//Concept")
            conceptID = []
            conceptName = []
            termUI = []
            termName = []
            for i in range(len(c1)):
                conceptID.append(c1[i].findtext("ConceptUI"))
                c2 = c1[i].find(".//ConceptName")
                conceptName.append(c2.findtext("String"))
                c3 = c1[i].find(".//TermList")
                c4 = c3.findall(".//Term")
                subtermUI = []
                subtermName = []
                for j in range(len(c4)):
                    subtermUI.append(c4[j].findtext("TermUI"))
                    subtermName.append(c4[j].findtext("String"))
                termUI.append(subtermUI)
                termName.append(subtermName)
        df = df.append(
            pd.Series([d1, d1_name, d1_created_year, d1_created_month, d1_created_day, d1_revised_year, d1_revised_month, d1_revised_day, d1_established_year, d1_established_month, d1_established_day, qualID, qual_name, qual_abbr, conceptID, conceptName, termUI, termName], index=dfcols),
            ignore_index=True)
    return df

def date_modify(df1):
    df1['DateCreated'] = df1['DateCreated-Year'].astype(str) + "-" + df1['DateCreated-Month'].astype(str) + "-" + df1['DateCreated-Day'].astype(str)
    df1['DateRevised'] = df1['DateRevised-Year'].astype(str) + "-" + df1['DateRevised-Month'].astype(str) + "-" + df1['DateRevised-Day'].astype(str)
    df1['DateEstablished'] = df1['DateEstablished-Year'].astype(str) + "-" + df1['DateEstablished-Month'].astype(str) + "-" + df1['DateEstablished-Day'].astype(str)
    df1 = df1.drop(columns = ['DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day'])
    return df1

def format_descriptor_df(df):
    df_1 = df
    df_1 = date_modify(df_1)
    df_1 = df_1.drop(columns = ['QualifierID', 'QualifierName', 'QualifierAbbreviation', 'ConceptID', 'ConceptName', 'TermID', 'TermName'])
    df_1['Descriptor_dcid'] = 'bio/' + df_1['DescriptorId'].astype(str)
    return df_1

def format_qualifier_df(df):
    df_2 = df
    df_2 = df_2.drop(columns = ['DescriptorName', 'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day', 'ConceptID', 'ConceptName', 'TermID', 'TermName'])
    df_2 = (df_2.set_index('DescriptorId')
              .apply(lambda x: x.apply(pd.Series).stack())
              .reset_index()
              .drop('level_1', 1))
    df_2['Qualifier_dcid'] = 'bio/' + df_2['QualifierId'].astype(str)
    return df_2

def format_concept_df(df):
    df_3 = df
    df_3 = df_3.drop(columns = ['DescriptorName', 'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day', 'QualifierID', 'QualifierName', 'QualifierAbbreviation', 'TermID', 'TermName'])
    df_3 = df_3 = (df_3.set_index('DescriptorId')
              .apply(lambda x: x.apply(pd.Series).stack())
              .reset_index()
              .drop('level_1', 1))
    df_3['Concept_dcid'] = 'bio/' + df_3['ConceptID'].astype(str)
    return df_3

def format_term_df(df):
    df_4 = df
    df_4 = df_4.drop(columns = ['DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day', 'QualifierID', 'QualifierName', 'QualifierAbbreviation', 'DescriptorName', 'DescriptorId'])
    df_4 = df_4.apply(lambda x: x.explode() if x.name in ['ConceptID', 'ConceptName', 'TermID', 'TermName'] else x)
    df_4 = df_4.reset_index(drop=True)
    df_4 = df_4.apply(lambda x: x.explode() if x.name in ['TermID', 'TermName'] else x)
    df_4['Term_dcid'] = 'bio/' + df_4['TermID'].astype(str)
    return df_4

def mesh_wrapper(file_input):
    df = format_mesh_xml(file_input)
    df1 = date_modify(df)
    df1 = format_descriptor_df(df1)
    df2 = format_qualifier_df(df)
    df3 = format_concept_df(df)
    df4 = format_term_df(df)

    df1.to_csv('descriptor_mesh.csv')
    df2.to_csv('qualifier_mesh.csv')
    df3.to_csv('concept_mesh.csv')
    df4.to_csv('term_mesh.csv')

def main():

    file_input = sys.argv[1]


if __name__ == "__main__":
    main()