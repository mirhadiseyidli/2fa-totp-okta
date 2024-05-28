import asyncio
import json
import logging
import os

from okta.client import Client as OktaClient
from okta import models

class OktaFactorVerifier:
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

    async def verify_factor(self):
        user_name = input("User Email: ")
        self.user, _, user_err = await self.okta_client.get_user(user_name)
        if user_err:
            print("Failed to retrieve user ID:", user_err)
        else:
            # Find Factor ID from our database
            factor_id = self.get_factor_id(user_name)
            # Request the code
            pass_code = input("Please enter the 6 digit code from TOTP device: ")

            verify_factor_request = models.VerifyFactorRequest({
                'passCode': pass_code
            })
            
            # Attempt to verify the TOTP factor
            try:
                verified_factor, _, err = await self.okta_client.verify_factor(
                                                        self.user.id, factor_id, verify_factor_request)
                if err:
                    logging.error("Error during TOTP verification: %s", err)
                    return err
                # Check the verification status from the response
                return verified_factor.factor_result == 'SUCCESS'
            except Exception as e:
                print(f"Exception during TOTP verification: {e}")
                return False
        
async def main():
    # Use configs from JSON file
    config_file = 'config.json'

    enroller = OktaFactorVerifier(config_file)
    config = json.load(open(config_file))

    verified_factor = await enroller.verify_factor()

    if verified_factor == True:
        print("TOTP Successfully verified! You can release the TOTP hardware to the user now!")
    else:
        print("Verification Failed, Please try to setup again!")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())

