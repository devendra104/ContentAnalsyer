# ContentAnalsyer

Content Analyser tool helps to identify the variance between pre-upgrade and post-upgrade data.


Pre-requisite:

1: Copy the CLI, API and Templates module data before upgrade and after upgrade in the below files.

    a: preupgrade_cli (text files)
    b: preupgrade_api  (text files)
    c: preupgrade_templates (directory)
    d: postupgrade_templates (directory)

2: Check the config file and update the details according to your use

       a: config.yml
       b: existence_test_data.yml

How to run:

1: Create a virtual python environment.

     virtualenv -p python3.6 contentanalyser_pyenv

2: source contentanalyser_pyenv/bin/activate

3: pip install -r requirements.txt

4: Execute the runner file

    python runner.py

5: Check the generated analysis report in /report directory.

   ![picture](config/xls_report.png)
