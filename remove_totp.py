import asyncio
import json
import logging
import os

from okta.client import Client as OktaClient
from okta import models

class OktaFactorRemover:
    def __init__(self, config_file):
        # Load configuration from a JSON file
        with open(config_file, 'r') as file:
            config = json.load(file)
        # Connect to Okta
        self.okta_client = OktaClient({
            'orgUrl': config['org_url'],
            'token': config['token']
        })

    def get_factor_id(self, user_name):
        # Define the file path
        filename = 'user_data.json'
        
        # Read existing data or initialize an empty list
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        # Find the factor_id for the specified user_name
        for entry in existing_data:
            if entry.get('user_name') == user_name:
                return entry.get('factor_id')  # Return the factor_id if found

        return None  # Return None if no matching user_name is found

    async def delete_factor(self):
        self.user_name = input("User Email: ")
        self.user, _, user_err = await self.okta_client.get_user(self.user_name)
        if user_err:
            print("Failed to retrieve user ID:", user_err)
        else:
            # Attempt to verify the TOTP factor
            try:
                factor_id = self.get_factor_id(self.user_name)
                _, err = await self.okta_client.delete_factor(
                                                        self.user.id, factor_id)
                if err:
                    logging.error("Error during TOTP removal: %s", err)
                    return err
                # Check the verification status from the response
                return True
            except Exception as e:
                print(f"Exception during TOTP removal: {e}")
                return False
        
    def remove_user_data(self):
        # Define the file path
        filename = 'user_data.json'
        
        # Read existing data or initialize an empty list
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # Remove data
        filtered_data = []
        for entry in existing_data:
            if entry['user_name'] != self.user_name:
                filtered_data.append(entry)

        existing_data = filtered_data

        # Write updated data back to the file
        with open(filename, 'w') as file:
            json.dump(existing_data, file, indent=4)

        
async def main():
    # Use configs from JSON file
    config_file = 'config.json'

    enroller = OktaFactorRemover(config_file)
    config = json.load(open(config_file))

    deleted_factor = await enroller.delete_factor()
    if deleted_factor == True:
        print("TOTP Successfully removed! You can collect the TOTP hardware from the user now!")
    else:
        print("Removal Failed, Please try again!")
    enroller.remove_user_data()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
