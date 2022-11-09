# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This module provides mapping between Import file and Statistical Variables
of input file.

Below dictionary is used during parsing input file and
generating processed output csv's - SV column.

Dictionary structure:
"<import_name>": {
    "<file_name>": "SV - calculated by reading properties from df",
    ....
}
"""

file_to_sv_mapping = {
    "alcohol_consumption": {
        "hlth_ehis_al1c": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['citizen']"+\
            " + '_' + df['sex']",
        "hlth_ehis_al1u": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['deg_urb']"+\
            " + '_' + df['sex']",
        "hlth_ehis_al1e": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['isced11']"+\
            " + '_' + df['sex']",
        "hlth_ehis_de10": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['isced11']"+\
            " + '_' + df['sex']",
        "hlth_ehis_al1b": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['sex'] + '_'"+\
            " + df['c_birth']",
        "hlth_ehis_al1i": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_AlcoholConsumption' + '_In_Count_Person_' + df['sex'] + '_'"+\
            " + df['quant_inc']",
        "hlth_ehis_al3u": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_BingeDrinking' + '_In_Count_Person_' + df['deg_urb'] + '_'"+\
            " + df['sex']",
        "hlth_ehis_al3e": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_BingeDrinking' + '_In_Count_Person_' + df['isced11'] + '_'"+\
            " + df['sex']",
        "hlth_ehis_de6" : "'Percent_' + df['frequenc_alcohol']"+\
            " + '_BingeDrinking' + '_In_Count_Person_' + df['isced11'] + '_'"+\
            " + df['sex']",
        "hlth_ehis_al3i": "'Percent_' + df['frequenc_alcohol']"+\
            " + '_BingeDrinking' + '_In_Count_Person_' + df['sex'] + '_'"+\
            " + df['quant_inc']",
        "hlth_ehis_al2u": "'Percent_HazardousAlcoholConsumption'"+\
            " + '_In_Count_Person_' + df['deg_urb'] + '_' + df['sex']",
        "hlth_ehis_al2e": "'Percent_HazardousAlcoholConsumption'"+\
            " + '_In_Count_Person_' + df['isced11'] + '_' + df['sex']",
        "hlth_ehis_al2i": "'Percent_HazardousAlcoholConsumption'"+\
            " + '_In_Count_Person_' + df['sex'] + '_' + df['quant_inc']",
    },

    "physical_activity": {
        "hlth_ehis_pe9e": "'Percent_'+df['physact']+'_'" + \
            "+'HealthEnhancingPhysicalActivity_In_Count_Person_'" + \
            "+df['isced11'] + '_' + df['sex']",

        "hlth_ehis_pe9i": "'Percent_' + df['physact'] + '_'" + \
            "+'HealthEnhancingPhysicalActivity' + '_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['quant_inc']",

        "hlth_ehis_pe9u": "'Percent_' + df['physact']" + \
            "+'_HealthEnhancingPhysicalActivity' + '_In_Count_Person_'" + \
            "+df['deg_urb'] + '_' + df['sex']",

        "hlth_ehis_pe1e": "'Percent_' + 'WorkRelatedPhysicalActivity' + '_'" + \
            "+df['levels'] + '_In_Count_Person_' + df['isced11'] + '_'" + \
            "+df['sex']",

        "hlth_ehis_pe1i": "'Percent_' + 'WorkRelatedPhysicalActivity' + '_'" + \
            "+df['levels'] + '_In_Count_Person_' + df['sex'] + '_'" + \
            "+df['quant_inc']",

        "hlth_ehis_pe1u": "'Percent_' + 'WorkRelatedPhysicalActivity_'" \
            "+ df['levels'] + '_In_Count_Person_' + df['deg_urb'] + '_'" + \
            "+df['sex']",

        "hlth_ehis_pe3e": "'Percent_' + df['physact']" + \
            "+'_NonWorkRelatedPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['isced11'] + '_' + df['sex']",

        "hlth_ehis_pe3i": "'Percent_' + df['physact']" + \
            "+'_NonWorkRelatedPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['quant_inc']",

        "hlth_ehis_pe3u" : "'Percent_' + df['physact'] + '_'" + \
            "+'NonWorkRelatedPhysical'+ 'Activity_In_Count_Person_'" + \
            "+df['deg_urb'] + '_'+df['sex']",

        "hlth_ehis_pe2e": "'Percent_' + df['duration'] + '_'" + \
            "+'HealthEnhancingPhysical'+ 'Activity_In_Count_Person_'" + \
            "+df['isced11'] + '_' + df['sex']",

        "hlth_ehis_pe2i": "'Percent_' + df['duration']" + \
            "+'_HealthEnhancingPhysical'+ 'Activity_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['quant_inc']",

        "hlth_ehis_pe2u": "'Percent_' + df['duration']" + \
            "+'_HealthEnhancingPhysicalActivity' + '_In_Count_Person_'" + \
            "+df['deg_urb'] + '_' + df['sex']",

        "hlth_ehis_pe9b": "'Percent_' + df['physact']" + \
            "+'_HealthEnhancingPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['c_birth']",

        "hlth_ehis_pe9c": "'Percent_' + df['physact']" + \
            "+'_HealthEnhancingPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['citizen'] + '_' + df['sex']",

        "hlth_ehis_pe9d": "'Percent_' + df['physact']" + \
            "+'_HealthEnhancingPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['lev_limit']",

        "hlth_ehis_pe2m": "'Percent_' + df['duration']" + \
            "+'_NonWorkRelatedPhysicalActivity'+ '_In_Count_Person_'" + \
            "+df['sex'] + '_' + df['bmi']",

        "hlth_ehis_de9" : "'Percent_' + df['isced11'] + '_PhysicalActivity'" + \
            "+'_In_Count_Person_' + df['sex']",

        "hlth_ehis_pe6e": "'Percent_' + 'AtLeast30MinutesPerDay'" + \
            "+'_WalkingOrCycling_' + 'PhysicalActivity' + '_In_Count_Person_'" + \
            "+'df['isced11'] + '_' + df['sex']'"

    },

    "tobacco_consumption":  {
        "hlth_ehis_sk1b":
        "'Percent'+'_'+df['smoking']+'_'+'TobaccoProducts'"+\
        "+'_In_Count_Person_'+df['sex']+'_'+df['c_birth']",

        "hlth_ehis_sk1c":
            "'Percent'+'_'+df['smoking']+'_'+'TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['citizen']+'_'+df['sex']",

        "hlth_ehis_sk1e":
            "'Percent'+'_'+df['smoking']+'_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_sk1i":
            " 'Percent'+'_'+df['smoking']+'_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']",

        "hlth_ehis_sk1u":
            "'Percent'+'_'+df['smoking']+'_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']",

        "hlth_ehis_sk2i":
            "'Percent_FormerSmoker_Daily_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']",

        "hlth_ehis_sk2e":
            "'Percent_FormerSmoker_Daily_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_sk3e":
            "'Percent_Daily_'+df['smoking']+'_TobaccoSmoking'+'_Cigarettes'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_sk3i":
            "'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'+'_Cigarettes'"+\
            "+'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']",

        "hlth_ehis_sk3u":
            "'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'+'_Cigarettes'"+\
            "+'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']",

        "hlth_ehis_sk4e":
            "'Percent'+'_'+df['frequenc_tobacco']+'_ExposureToTobaccoSmoke'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_sk4u":
            "'Percent'+'_'+df['frequenc_tobacco']+'_ExposureToTobaccoSmoke'"+\
            "+'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']",

        "hlth_ehis_sk5e":
            "'Percent_Daily_TobaccoSmoking_'+df['duration']+'_TobaccoProducts'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_sk6e":
            "'Percent_'+df['frequenc_tobacco']+'_'+'ECigarettes'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",

        "hlth_ehis_de3":
            "'Percent_Daily_TobaccoSmoking'+'_Cigarettes'"+\
            "+'_In_Count_Person_'+df['isced11']+'_'+df['sex']",


        "hlth_ehis_de4":
            "'Percent_Daily_TobaccoSmoking'"+\
            "+'_Cigarettes'+'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']",

        "hlth_ehis_de5":
            "'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'"+\
            "+'_Cigarettes'+'_In_Count_Person_'+df['isced11']+'_'+df['sex']"


    },

    "bmi": {
        "hlth_ehis_bm1e":
            "'Percent_' + df['bmi']"+\
            " + '_In_Count_Person_' + df['isced11']"+\
            "+ '_' + df['sex']",
        "hlth_ehis_de1": "'Percent_' + df['bmi']"+\
                         " + '_In_Count_Person_' + df['isced11']"+\
                         "+ '_' + df['sex']",
        "hlth_ehis_bm1i": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['quant_inc']",
        "hlth_ehis_de2": "'Percent_' + df['bmi']"+\
                         " + '_In_Count_Person_' + df['sex']"+\
                         "+ '_' + df['quant_inc']",
        "hlth_ehis_bm1u": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['deg_urb']"+\
                          "+ '_' + df['sex']",
        "hlth_ehis_bm1b": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['c_birth']",
        "hlth_ehis_bm1c": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['citizen']"+\
                          "+ '_' + df['sex']",
        "hlth_ehis_bm1d": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['lev_limit']",
    },

    "social_environment": {
       "hlth_ehis_ss1e": "'Percent_Receiving' + df['lev_perc']"+\
                         "+'SocialSupport_In_Count_Person_'+ df['isced11']"+\
                         "+'_' + df['sex']",
       "hlth_ehis_ss1u": "'Percent_Receiving' + df['lev_perc']"+\
                         "+'SocialSupport_In_Count_Person_' "+\
                         "+df['deg_urb'] + '_' + df['sex']",
       "hlth_ehis_ss1b": "'Percent_Receiving'+ df['lev_perc']"+\
                         "+'SocialSupport_In_Count_Person_'"+\
                         "+df['sex']+'_'+df['c_birth']",
       "hlth_ehis_ss1c": "'Percent_Receiving' + df['lev_perc']"+\
                         "+'SocialSupport_In_Count_Person_' "+\
                         "+df['citizen'] + '_' + df['sex']",
       "hlth_ehis_ss1d": "'Percent_Receiving' + df['lev_perc']"+\
                         "+'SocialSupport_In_Count_Person_'" +\
                         "+df['sex']+ '_' + df['lev_limit']",
       "hlth_ehis_ic1e": "'Percent_' + 'AtLeastOnceAWeek_' + df['assist']"+\
                         "+'OrAssistance_In_Count_Person_' + df['isced11']"+\
                         "+'_' + df['sex']",
       "hlth_ehis_ic1u": "'Percent_' + 'AtLeastOnceAWeek_' + df['assist']"+\
                         "+'OrAssistance_In_Count_Person_' + df['deg_urb']"+\
                         "+'_' + df['sex']",
   },

    "fruits_vegetables" : {
        "hlth_ehis_fv1b": "'Percent_' + df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] +'_In_Count_Person_'+df['sex']+ '_'+df['c_birth']",
        "hlth_ehis_fv1c": "'Percent_' + df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['citizen'] + '_' + df['sex']",
        "hlth_ehis_fv1d": "'Percent_'+ df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['sex']  + '_' + df['lev_limit']",
        "hlth_ehis_fv1e": "'Percent_'+ df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['isced11'] + '_' + df['sex']",
        "hlth_ehis_fv1i": "'Percent_'+  df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['sex'] + '_' + df['quant_inc']",
        "hlth_ehis_fv1m": "'Percent_'+  df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['sex'] + '_' + df['bmi']",
        "hlth_ehis_fv1u": "'Percent_'+ df['frequenc_fruitsvegetables']"+\
            "+ '_' + df['coicop'] + '_In_Count_Person_' + df['deg_urb']+ '_' + df['sex']",

        "hlth_ehis_fv3b": "'Percent_' + 'Daily_'+df['n_portion']+'_'"+\
            " +'ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['sex']+ '_' + df['c_birth']",
        "hlth_ehis_fv3c": "'Percent_' + 'Daily_'+df['n_portion'] "+\
            " +'_ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['citizen']+ '_' + df['sex']",
        "hlth_ehis_fv3d": "'Percent_' + 'Daily_'+df['n_portion'] "+\
            " +'_ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['sex']+ '_' + df['lev_limit']",
        "hlth_ehis_fv3e": "'Percent_' + 'Daily_'+df['n_portion'] "+\
            " +'_ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['isced11']+ '_' + df['sex']",
        "hlth_ehis_fv3i": "'Percent_' + 'Daily_'+df['n_portion'] "+\
            " +'_ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['sex']+ '_' + df['quant_inc']",
        "hlth_ehis_fv3m": "'Percent_' + 'Daily_'+df['n_portion'] "+\
            " +'_ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['sex']+ '_' + df['bmi']",
        "hlth_ehis_fv3u": "'Percent_' + 'Daily_'+df['n_portion']+'_'"+\
            " +'ConsumptionOfFruitsOrConsumptionOfVegetables_' + 'In_Count_Person_' "+\
           " +  df['deg_urb']+ '_' + df['sex']",

        "hlth_ehis_fv7e": " 'Percent_'+df['frequenc_fruitsvegetables'] +'_'+'ConsumptionOfSugarSweetenedSoftDrinks_' "+\
                "  + 'In_Count_Person_'+df['isced11']+'_'+df['sex']",
        "hlth_ehis_fv7i": " 'Percent_'+df['frequenc_fruitsvegetables'] +'_'+'ConsumptionOfSugarSweetenedSoftDrinks_' "+\
                "  + 'In_Count_Person_'+df['sex']+'_'+df['quant_inc']",
        "hlth_ehis_fv7m": " 'Percent_'+df['frequenc_fruitsvegetables'] +'_'+'ConsumptionOfSugarSweetenedSoftDrinks_' "+\
                "  + 'In_Count_Person_'+df['sex']+'_'+df['bmi']",

       "hlth_ehis_de7": " 'Percent_'+ df['frequenc_fruitsvegetables']+ '_'+'ConsumptionOfFruits_' "+\
               " + 'In_Count_Person_'+ df['isced11']+'_'+ df['sex']",
        "hlth_ehis_de8": " 'Percent_'+ df['frequenc_fruitsvegetables']+ '_'+'ConsumptionOfVegetables_' "+\
               " + 'In_Count_Person_'+ df['isced11']+'_'+ df['sex']",

       "hlth_ehis_fv5e" : " 'Percent_'+ df['frequenc_fruitsvegetables'] + '_' +'ConsumptionOfPureFruitOrConsumptionOfVegetableJuice_' "+\
             " +  'In_Count_Person_' +df['isced11'] +'_' + df['sex']",
    },


}
