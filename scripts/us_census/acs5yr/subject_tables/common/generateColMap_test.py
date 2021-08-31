"""Tests for generateColMap."""
import unittest
import json
import generateColMap

class generColMapTest(unittest.TestCase):
  def example_usage(self):
    specPath = './testdata/colMapInputs/spec.json'
    columnFile = './testdata/colMapInputs/columns.txt'
    expectedOut = './testdata/colMapInputs/expected.json'

    ## load the files
    specDict = json.load(open(specPath, 'r'))
    columnList = open(columnFile, 'r').read().split('\n')
    expectedMap = json.load(open(expectedOut, 'r'))

    #create the column map for the inputs
    generatedMap = generateColMap.generateColMap(specPath, columnFile)

    #validate
    self.assertEqual(expectedMap, generatedMap)

if __name__ == '__main__':
  unittest.main()
