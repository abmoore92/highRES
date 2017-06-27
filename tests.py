
import unittest
import pandas as pd
import numpy as np
import os
import sys
file_dir = os.getcwd()
sys.path.append(file_dir)

from reporting import clean

class TestReporting(unittest.TestCase):

    def setUp(self):
        pass

    def testClean_lessthan(self):
        df = pd.DataFrame(data=np.arange(10**7) / 10**6, columns=['r'])
        self.assertLess(clean(df,'r')['r'].sum(),df['r'].sum())

    # check that the function does not change the input dataframe
    def testClean_originalUnchanged(self):
        df = pd.DataFrame(data=np.arange(10**7) / 10**6, columns=['r'])
        df_copy = df.copy()
        df_copy_clean = clean(df_copy,'r')
        self.assertTrue(df.equals(df_copy))


if __name__ == '__main__':
    unittest.main()


