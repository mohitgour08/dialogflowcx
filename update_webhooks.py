import zipfile
import os
import shutil
import json
import pandas as pd
import argparse

def update_webhooks(agent_zip, creds_csv, env, output_zip):
    # Temp working folder
    work_dir = 'agent_tmp'
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    # Unzip agent
    with zipfile.ZipFile(agent_zip, 'r') as zip_ref:
        zip_ref.extractall(work_dir)

    # Load webhook credentials for environment
    creds_df = pd.read_csv(creds_csv)
    creds_df = creds_df.fillna('')

    # Process each webhook JSON
    webhooks_path = os.path.join(work_dir, 'webhooks')
    for filename in os.listdir(webhooks_path):
        if filename.endswith('.json'):
            filepath = os.path.join(webhooks_path, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)

            webhook_name = data.get('displayName')
            cred_row = creds_df[creds_df['webhook_name'] == webhook_name]

            if not cred_row.empty:
                row = cred_row.iloc[0]
                print(f"Updating webhook: {webhook_name}")

                # Update URL
                if 'url' in row and row['url']:
                    data['genericWebService']['uri'] = row['url']

                # Update OAuth credentials if present
                if pd.notna(row.get('oauth_client_id', '')) and pd.notna(row.get('oauth_client_secret', '')):
                    data['genericWebService']['authentication'] = {
                        "googleServiceAccount": None,
                        "genericOauth": {
                            "clientId": row['oauth_client_id'],
                            "clientSecret": row['oauth_client_secret']
                        }
                    }
                else:
                    # Remove OAuth if not needed
                    data['genericWebService']['authentication'] = {}

                # Write back updated webhook
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

    # Rezip updated agent
    shutil.make_archive(output_zip.replace('.zip', ''), 'zip', work_dir)

    # Cleanup
    shutil.rmtree(work_dir)

    print(f"✅ Webhooks updated for {env}. Output: {output_zip}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent_zip', required=True, help='Path to exported agent ZIP')
    parser.add_argument('--creds_csv', required=True, help='Path to CSV with webhook credentials')
    parser.add_argument('--env', required=True, help='Target environment name (dev/sit/prod)')
    parser.add_argument('--output_zip', default='agent_updated.zip', help='Output updated agent ZIP file')

    args = parser.parse_args()

    update_webhooks(args.agent_zip, args.creds_csv, args.env, args.output_zip)
