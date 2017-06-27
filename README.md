# highRES
highRES tools

This project folder contains reporting functions and the model setup for highRES (currently it does not have the input file generator functions).

The broad description of how to run highRES is:

1) Create input function (.dd files), all of which are referenced in highRES_data_input.gms
2) Choose model settings and run highRES_2017.gms from a command line. This produces an output sqlite database for each model run
3) Use reporting functions to analyse the sqldatabase. Bulk reporting is possible via write_individual_reports.py
4) Comparison reports can be written via write_comparison_reports.py, but this is very scenario specific, and was written for a specific sensitivity analysis looking at cost, waves, and renewable portfolio standard


