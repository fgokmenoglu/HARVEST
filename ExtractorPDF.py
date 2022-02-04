# ===============================================================================================================
# AUTHOR        : FATIH GOKMENOGLU
# CREATE DATE   : February 3, 2022
# PURPOSE       : Extract data (text) from multiple PDFs and save it in excel in a particular format 
# SPECIAL NOTES : Lines 209-215 (inclusive) are commented out due to concerns regarding OS this code is to be run; 
#                 Line 17 is also commented out since it has no other use purpose
# ================================================================================================================
# Change History:
#
# ================================================================================================================

# Import necessary libraries
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams
from dateutil.parser import parse
import xlsxwriter
# import os
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from io import StringIO

# Define a variable to keep input PDF file information
infile = 'input.pdf'

# Define variables to hold input and output data
inputExtracted = []
outputToWrite = {}

# Find date information within input data
def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

# Find type information within input data
def is_type(string):
    if(string.rstrip('\n') == 'Consumers' or string.rstrip('\n') == 'Lenders'):
        return string
    else:
        return ''

# Find case information within input data
def is_case(string):
    if('● ' in string):
        return string
    else:
        return ''

# Get raw text data
def get_raw_text(filePath):
    resourceManager = PDFResourceManager()
    string = StringIO()
    converter = TextConverter(resourceManager, string)
    pageInterpreter = PDFPageInterpreter(resourceManager, converter)

    file = open(filePath, 'rb')

    for page in PDFPage.get_pages(file, caching=True, check_extractable=True):
        pageInterpreter.process_page(page)

    rawText = string.getvalue()
    # print(rawText)

    converter.close()
    string.close()

    return rawText

# Extract data from a given PDF file
for pageLayout in extract_pages(infile):
    for element in pageLayout:
        if isinstance(element, LTTextContainer):
            # print(element.get_text())
            inputExtracted.append(element.get_text())

# for item in inputExtracted:
#     print(item)

# Define variable to keep track of the number of types and cases
numTypes = 0
numCases = 0

# Loop through data extracted
for text in inputExtracted:
    # Check if date information is found
    if(is_date(text, fuzzy=True)):
        # print(text)
        outputToWrite['date'] = text.rstrip('\n')
    
    # Check if type information is found
    if(is_type(text) != ''):
        # print(text)
        text = text.rstrip('\n')
        outputToWrite['type' + str(numTypes + 1)] = text
        
        numTypes += 1

    # Check if case information and corresponding details are found
    if(is_case(text) != ''):
        # print(text)

        # Find the corresponding details and responsible information for a given case
        index = inputExtracted.index(text)
        details_responsible = inputExtracted[index + 1].rstrip('\n')
        index = details_responsible.find('(')

        # Separate available data into details and responsible respectively
        detailsText = details_responsible[0 : index - 1]
        detailsText = detailsText.replace('\n', '')
        outputToWrite['details' + str(numCases + 1)] = detailsText

        responsibleText = details_responsible[index + 1 : len(details_responsible) - 1]
        outputToWrite['responsible' + str(numCases + 1)] = responsibleText 
        
        # Clear any leading or trailing characters that should not be in output  
        text = text.lstrip('● ')
        text = text.rstrip('\n')

        # Separate available data into case and summary respectively
        index = text.find('-')
        
        caseText = text[0 : index - 1]        
        outputToWrite['case' + str(numCases + 1)] = caseText

        summaryText = text[index + 2 : len(text)]       
        outputToWrite['summary' + str(numCases + 1)] = summaryText

        # Update the number of cases
        numCases += 1       

# print(numTypes)
# print(numCases)

# for item in outputToWrite.items():
#     print(item)

# Get raw text from the given PDF file
typeIndex = []
rawText = get_raw_text(infile)
# print(rawText)

# Check raw text file to find the number of cases corresponding to each type
for ii in range(numTypes):
    typeIndex.append(rawText.find(outputToWrite['type' + str(ii + 1)]))

# for item in typeIndex:
#     print(item)

numCasesPerType = []
numCasesPerType.append(rawText[typeIndex[0] - 1 : typeIndex[1]].count('●'))

for ii in range(len(typeIndex)):
    if (ii + 2) >= len(typeIndex):
        numCasesPerType.append(rawText[typeIndex[ii + 1] : len(rawText)].count('●'))
        break
    else:
        numCasesPerType.append(rawText[typeIndex[ii + 1] : typeIndex[ii + 2]].count('●')) 
        
# for item in numCasesPerType:
#     print(item)

# Open or create xlsx file to output, then add a worksheet
workbook = xlsxwriter.Workbook('output.xlsx')
worksheet = workbook.add_worksheet()

# Adjust header row format
headerFormat = workbook.add_format()
headerFormat.set_font_name('Arial')
headerFormat.set_font_size(14)
headerFormat.set_bold(True)

# Adjust body row format
bodyFormat = workbook.add_format()
bodyFormat.set_font_name('Arial')
bodyFormat.set_font_size(11)
bodyFormat.set_bold(False)

# Add header section
worksheet.write('A1', 'Date', headerFormat)
worksheet.write('B1', 'Type', headerFormat)
worksheet.write('C1', 'Case Name', headerFormat)
worksheet.write('D1', 'Summary', headerFormat)
worksheet.write('E1', 'Details', headerFormat)
worksheet.write('F1', 'Responsible', headerFormat)
worksheet.write('G1', 'Notes', headerFormat)
worksheet.write('H1', 'Reviewed', headerFormat)

# Write data extracted into the corresponding cells
for ii in range(numCases):
    worksheet.write('A' + str(ii + 2), outputToWrite['date'], bodyFormat)
    worksheet.write('C' + str(ii + 2), outputToWrite['case' + str(ii + 1)], bodyFormat)
    worksheet.write('D' + str(ii + 2), outputToWrite['summary' + str(ii + 1)], bodyFormat)
    worksheet.write('E' + str(ii + 2), outputToWrite['details' + str(ii + 1)], bodyFormat)
    worksheet.write('F' + str(ii + 2), outputToWrite['responsible' + str(ii + 1)], bodyFormat)

for ii in range(numTypes):
    for jj in range(numCasesPerType[ii]):
        worksheet.write('B' + str(jj + 2 * ii + 2), outputToWrite['type' + str(ii + 1)], bodyFormat)

# Close the workbook
workbook.close()

# Autofit the column width for available data in output file
# import win32com.client as win32
# excel = win32.gencache.EnsureDispatch('Excel.Application')
# wb = excel.Workbooks.Open(os.path.abspath('output.xlsx'))
# ws = wb.Worksheets("Sheet1")
# ws.Columns.AutoFit()
# wb.Save()
# excel.Application.Quit()
