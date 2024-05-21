from flask import Flask, render_template, jsonify
import os
import requests
import pandas as pd
import json

filename= "aws-ip-ranges.json"
url="https://ip-ranges.amazonaws.com/ip-ranges.json"

app = Flask(__name__)
#Checking if the the server has ip-ranges file stored locally and, if not, download the file for future use.
#In a real-life case, should also add a check step to ensure that the file is up to date and, if it is oudated,
#i.e. the file is older than 7 or 30 days, delete the local file and download the new one

def download_file():
    if os.path.isfile(filename):
        print("Local file found")
    else:
        print("Local file missing. Downloading from url")
        try:
            response = requests.get(url)
            with open(filename, 'wb') as file:
                file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the file: {e}")
            raise

# Homepage
@app.route('/')
def home():
    download_file()
    
    # Read the JSON file
    with open(filename) as file:
        data = json.load(file)
    
    ipv4_prefixes = data.get('prefixes', [])
    ipv6_prefixes = data.get('ipv6_prefixes', [])

# Problem here is that the json file is split into two elements: IPv4 and IPv6 prefixes, which cause for the table.
# Both elements have different title - prefixes vs ipv6_prefixes. Renaming the ipv6_prefixes to just ip_prefixes should
# be the easiest way

    df_ipv4_prefixes = pd.json_normalize(ipv4_prefixes)
    
    #Adding 'type' column to display what ip type are we dealing with (just to be _extra_ clear)
    df_ipv4_prefixes['type'] = 'IPv4'

    df_ipv6_prefixes = pd.json_normalize(ipv6_prefixes)
    
    #Same as for ipv4, setting 'type' to ipv6
    df_ipv6_prefixes['type'] = 'IPv6'

    #Renaming ipv6_prefix so as to have both ipv4 and ipv6 under the same column. 
    df_ipv6_prefixes = df_ipv6_prefixes.rename(columns={'ipv6_prefix': 'ip_prefix'})

    # Combining both elements of the json to one
    df_combined = pd.concat([df_ipv4_prefixes, df_ipv6_prefixes], ignore_index=True)

    #This has got to be the ugliest (or prettiest?) line of code I have seen vvv
    df_combined = df_combined[~df_combined['service'].isin(['S3', 'ROUTE53_HEALTHCHECKS', 'ROUTE53_HEALTHCHECKS_PUBLISHING'])]
    
    
    # Convert DataFrame to HTML table
    table_html = df_combined.to_html(classes='table table-striped table-bordered', index=False)
    
    
    return render_template('index.html', table_html=table_html)

if __name__ == '__main__':
    app.run(debug=True)