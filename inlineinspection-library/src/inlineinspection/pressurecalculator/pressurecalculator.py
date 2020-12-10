
""" Headline: Anomaly Processing Inline Inspection pressure caliculation tool 
    Calls:  inlineinspection, inlineinspection.config
    inputs: ILI Feature class(Which is calibrated and imported)
    Description: This tool calculates severity ratios, burst/safe pressures, according to B31G and Modified B31G.  
    Output: The output of this tool estimates burst pressure values for Metal Loss anomalies based on depth, length and pressure.
   """

from logging import exception
import arcpy
import inlineinspection
import os
import datetime as dt
import numpy as np
import math
from inlineinspection import config
import traceback
import sys
import locale
import json
import arcpy.cim
from arcpy import env


class PressureCalculator(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = config.ILI_PC_TOOL_LABEL
        self.description = config.ILI_PC_TOOL_DESC
        self.canRunInBackground = False
        self.category = config.ILI_PC_TOOL_CATAGORY

    def getParameterInfo(self):

        """
                parameters[0]->   in_workspace,
                parameters[1]->   in_nhd_intersections_features              
                """
        
       
        # Input ILI point featuere         
        in_ili_features = arcpy.Parameter(displayName="Input Inline Inspection Point Features",
            name="in_ili_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        in_ili_features.filter.list = ["Point"]
       
        in_pc_length_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Anomaly Length Field", name="in_pc_length_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_length_field.parameterDependencies = [in_ili_features.name]
        in_pc_length_field.value = config.ILI_PC_REQ_FIELDS[0]

        #MaxDepthMeasured' ,'MaxDiameter' ,'MeasuredWallThickness' ,'PipeSmys' ,'PipeMAOP']
        in_pc_MaxDepthMeasured_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Max Depth Measured Field", name="in_pc_MaxDepthMeasured_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_MaxDepthMeasured_field.parameterDependencies = [in_ili_features.name]
        in_pc_MaxDepthMeasured_field.value = config.ILI_PC_REQ_FIELDS[1]

        in_pc_MaxDiameter_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Anomaly Length Field", name="in_pc_MaxDiameter_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_MaxDiameter_field.parameterDependencies = [in_ili_features.name]
        in_pc_MaxDiameter_field.value = config.ILI_PC_REQ_FIELDS[2]

        in_pc_MeasuredWallThickness_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Measured Wall Thickness Field", name="in_pc_MeasuredWallThickness_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_MeasuredWallThickness_field.parameterDependencies = [in_ili_features.name]
        in_pc_MeasuredWallThickness_field.value = config.ILI_PC_REQ_FIELDS[3]

        in_pc_PipeSmys_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Pipe Smys Field", name="in_pc_PipeSmys_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_PipeSmys_field.parameterDependencies = [in_ili_features.name]
        in_pc_PipeSmys_field.value = config.ILI_PC_REQ_FIELDS[4]

        in_pc_PipeMAOP_field = arcpy.Parameter(category =config.ILI_PC_PARAMETER_CATGRY,
            displayName="Pipe MAOP Field", name="in_pc_PipeMAOP_field",
            datatype="Field", parameterType="Required", direction="Input")
        in_pc_PipeMAOP_field.parameterDependencies = [in_ili_features.name]
        in_pc_PipeMAOP_field.value = config.ILI_PC_REQ_FIELDS[5]

               
        parameters = [in_ili_features,in_pc_length_field,in_pc_MaxDepthMeasured_field,in_pc_MaxDiameter_field,in_pc_MeasuredWallThickness_field,
                      in_pc_PipeSmys_field,in_pc_PipeMAOP_field]

        return parameters

    def isLicensed(self):  # optional
        return True

        #return LicenseOperation.is_licensed

    def updateParameters(self, parameters):

        # Populate dependent fields from the input feature classe             
        
        if(parameters[0].value):
            if not parameters[1].value:
               parameters[1].value = config.ILI_PC_REQ_FIELDS[0]
            if not parameters[2].value:
               parameters[2].value = config.ILI_PC_REQ_FIELDS[1]
            if not parameters[3].value:
               parameters[3].value = config.ILI_PC_REQ_FIELDS[2]
            if not parameters[4].value:
               parameters[4].value = config.ILI_PC_REQ_FIELDS[3]
            if not parameters[5].value:
               parameters[5].value = config.ILI_PC_REQ_FIELDS[4]
            if not parameters[6].value:
               parameters[6].value = config.ILI_PC_REQ_FIELDS[5]
            
        else:
            for i in range(1, 7):
                parameters[i].value = None

        return

    def updateMessages(self, parameters):                     
        """ Check the input ILI feature class has the required fields and belongs to project database:       """
        #if parameters[0].valueAsText is not None:
        #    if(arcpy.Exists(parameters[0].value)):
        #        desc = arcpy.Describe(parameters[0])
        #        fc_path = desc.catalogPath                
        #        ili_inputs_fields = inlineinspection.get_field_names(parameters[0].value)
        #        missing_flds = self.get_missing_fields(ili_inputs_fields, config.ILI_PC_REQ_FIELDS)

        #        if len(missing_flds) > 0:
        #            missingflds = inlineinspection.list_to_string(missing_flds)
        #            parameters[0].setErrorMessage("Inline Inspection feature calss does not have required fields: {}. ".format(missingflds))

        return

    def execute(self, parameters, messages):
        inlineinspection.AddMessage("Start Logging.")        
        arcpy.AddMessage("Log file location: " + inlineinspection.GetLogFileLocation())
        inlineinspection.AddMessage("Starting ILI Pressure Calculator process...")

        try:
            # INPUT PARAMETERS for the process           
            #in_workspace = parameters[0].valueAsText
            ili_inputpoint_fc = parameters[0].valueAsText
                       
            if(arcpy.Exists(ili_inputpoint_fc)):                  
                ilicount = int(arcpy.GetCount_management(ili_inputpoint_fc).getOutput(0))  
                inlineinspection.AddMessage("Record count for ILI Pressure Calculator {}".format(ilicount))
                if (ilicount > 0):                     
                    ht_result_flag = False
                    calculateilipressures = CalculateILIPressures()
                    ili_result_flag = calculateilipressures.run(parameters)                 
                else:
                    inlineinspection.AddWarning("There is no records to perform Pressure Caliculation.")
            else:
                    inlineinspection.AddWarning("There is no feature class for Pressure Caliculation.")
            inlineinspection.AddMessage("Finished ILI Pressure Calculator process.")
            return

        except Exception as e:
            tb = sys.exc_info()[2]
            arcpy.AddError("An error occurred on line %i" % tb.tb_lineno)
            arcpy.AddError(str(e))

    def param_changed(self, param, check_value=False):
        changed = param.altered and not param.hasBeenValidated
        if check_value:
            if param.value:
                return changed
            else:
                return False
        else:
            return changed

    def get_missing_fields(self, infields, required_fields):
        '''
        :param infields: list of layer fields
        :param required_fields:  list of required fields
        :return: checks the required fields in the infields and returns missing fields
        '''
        missing_flds = []
        for fld in required_fields:
            if fld.upper() not in infields:
                missing_flds.append(fld)

        return missing_flds


class CalculateILIPressures(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        #self.label = "ILI Pressure Calculator Tool"
        

    def updatedomainvalues(self, inFeatures, fieldName, expression, code_block, field_type):
        try:
            # Set the workspace (to avoid having to type in the full path to the data every time)

            inlineinspection.AddMessage("Calculate Pressure process started for {}".format(fieldName))
            # Process: Add valid material types to the domain
            # use a for loop to cycle through all the domain codes in the dictionary
            arcpy.CalculateField_management(inFeatures, fieldName, expression, 'Python 3', code_block, field_type)
            inlineinspection.AddMessage("  Pressures are calculated, process completed for {}".format(fieldName))

        except Exception as e:
            # If an error occurred, print line number and error message
            tb = sys.exc_info()[2]
            inlineinspection.AddError("   Error in domain creation process for {}".format(domain))
            inlineinspection.AddError("   An error occurred on line %i" % tb.tb_lineno)
            inlineinspection.AddError(str(e))

    def run(self,parameters):
        try:
            # Set the workspace (to avoid having to type in the full path to the data every time)
            #inFeatures = arcpy.GetParameterAsText(0)
            inFeatures=parameters[0].valueAsText
            legthField=parameters[1].valueAsText
            maxDepthMeasure=parameters[2].valueAsText

            maxDiameter=parameters[3].valueAsText
            measuredWallthickness[4].valueAsText

            pipeSmys=parameters[5].valueAsText
            pipeMAOPField=parameters[6].valueAsText

            inlineinspection.AddMessage("Input ILI Feature class {}".format(inFeatures))

            #calculate the first pressure field 1
            fieldName = "AreaOfMetalLoss"
            expression = "(2/3)*(!"+maxDepthMeasure+"!)*(!"+legthField+"!)"
            code_block = ""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

           
            # # calculate the first pressure field 2
            fieldName = "Mod_AreaOfMetalLoss"
            expression = "(.85)*(!"+maxDepthMeasure+"!)*(!"+legthField+"!)"
            code_block =""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            # # calculate the first pressure field 3
            fieldName = "FlowStress"
            expression = "(1.1)*(!"+pipeSmys+"!)"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)
            #
            # # calculate the first pressure field 2
            fieldName = "Mod_FlowStress"
            expression = "(!"+pipeSmys+"!+10000)"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)


            fieldName = "FoliasFactor"
            expression = "folias(!"+legthField+"!, !"+maxDiameter+"!,!"+measuredWallthickness+"!)"
            code_block = """def folias(length, diameter, thickness):
                                if length <(20*diameter*thickness)**(.5):
                                    return math.sqrt((1 + 0.8 * (length**2/(diameter*thickness))))
                                else: 
                                    return 0"""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "Mod_FoliasFactor"
            expression = "modfolias(!"+legthField+"!, !"+maxDiameter+"!,!"+measuredWallthickness+"!)"
            code_block = """def modfolias(length, diameter, thickness):
                                if length**2/(diameter*thickness)<=50:
                                    return math.sqrt((1+(0.6275*(length**2/(diameter*thickness)))-(0.003375*(((length**2)/(diameter*thickness))**2))))
                                elif length**2/(diameter*thickness)>50:
                                    return ((.032)*((length**2)/(diameter*thickness)))+3.3"""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)


            fieldName = "PipeBurstPressure"
            expression = "(!FlowStress!)*((1-(!AreaOfMetalLoss!/(!"+measuredWallthickness+"!*!"+legthField+"!)))/(1-(!AreaOfMetalLoss!/(!"+measuredWallthickness+"!*!"+legthField+"!*!FoliasFactor!))))*((2*!"+measuredWallthickness+"!)/!"+maxDiameter+"!)"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)


            fieldName = "Mod_PipeBurstPressure"
            expression = "(!Mod_FlowStress!)*((1-(!Mod_AreaOfMetalLoss!/(!"+measuredWallthickness+"!*!"+legthField+"!)))/(1-(!Mod_AreaOfMetalLoss!/(!"+measuredWallthickness+"!*!"+legthField+"!*(!Mod_FoliasFactor!)))))*((2*!"+measuredWallthickness+"!)/!"+maxDiameter+"!)"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "CalculatedPressure"
            expression =  "(!PipeBurstPressure!*!"+pipeMAOPField+"!)/(!"+pipeSmys+"!)"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "ReferencePressure"
            expression = "!"+pipeMAOPField+"!"
            code_block = ""
            field_type = 'LONG'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "Safety_Factor"
            expression = "(!PipeBurstPressure!/!"+pipeMAOPField+"!)"
            code_block =""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "PressureReferencedRatio"
            expression = "(!CalculatedPressure!/!ReferencePressure!)"
            code_block =""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "EstimatedRepairFactor"
            expression = "!"+pipeMAOPField+"!/!CalculatedPressure!"
            code_block =""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

            fieldName = "RupturePressureRatio"
            expression = "!PipeBurstPressure!/!"+pipeSmys+"!"
            code_block =""
            field_type = 'DOUBLE'
            self.updatedomainvalues(inFeatures, fieldName, expression, code_block, field_type)

        except Exception as e:
            # If an error occurred, print line number and error message
            tb = sys.exc_info()[2]
            arcpy.AddError("An error occurred on line %i" % tb.tb_lineno)
            arcpy.AddError(str(e))