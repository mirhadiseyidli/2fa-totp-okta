import asyncio
import json
import logging
import os
import subprocess

from okta.client import Client as OktaClient
from okta import models

class OktaFactorEnroller:
    def __init__(self, config_file):
        # Load configuration from a JSON file
        with open(config_file, 'r') as file:
            config = json.load(file)
        # Connect to Okta
        self.okta_client = OktaClient({
            'orgUrl': config['org_url'],
            'token': config['token']
        })
    
    async def enroll_factor(self, factor_profile_id):
        # Create a Shared Secret
        shared_secret = subprocess.run(f"openssl rand -hex 20",
                                shell=True, stdout=subprocess.PIPE, text=True)
        # Get User ID by Email
        self.user_name = input("User Email: ")
        self.user, _, user_err = await self.okta_client.get_user(self.user_name)
        if user_err:
            print("Failed to retrieve user ID:", user_err)
        else:
            # Configure TOTP Factor
            totp_factor = models.CustomHotpUserFactor({
                'factorProfileId': factor_profile_id,
                "provider": "CUSTOM",
                'profile': models.CustomHotpUserFactorProfile({
                    'sharedSecret': shared_secret.stdout.strip()
                })
            })

            try:
                enrolled_factor, _, err = await self.okta_client.enroll_factor(
                                    self.user.id, totp_factor, {"activate": "true"})
                if err:
                    logging.error("Error enrolling factor: %s", err)
                    return None, None, err
                else:
                    return enrolled_factor, shared_secret.stdout.strip(), None
            except Exception as e:
                logging.error("An exception occurred: %s", e)
                return None, str(e)
        
    async def verify_factor(self, pass_code, factor_id):
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
        
    def update_user_data(self, factor_id):
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

        # Update or append data
        found = False
        for entry in existing_data:
            if entry['user_name'] == self.user_name:
                entry['factor_id'] = factor_id  # Update the factor_id
                found = True
                break
        if not found:
            existing_data.append({'user_name': self.user_name, 'factor_id': factor_id})

        # Write updated data back to the file
        with open(filename, 'w') as file:
            json.dump(existing_data, file, indent=4)

async def main():
    # Use configs from JSON file
    config_file = 'config.json'

    enroller = OktaFactorEnroller(config_file)
    config = json.load(open(config_file))
    factor_profile_id = config['factor_profile_id']
    
    enrolled_factor, shared_secret, error = await enroller.enroll_factor(factor_profile_id)
    if error:
        print("Failed to enroll factor:", error)
        return
    else:
        if enrolled_factor is not None:
            enroller.update_user_data(enrolled_factor.id)
        print(f"\nSuccessfully enrolled the custom TOTP factor!\n"
              f"Please burn this Shared Secret into the TOTP device: {shared_secret}\n"
               "To verify TOTP, please submit the 6-digit number from your TOTP device below\n"
               f"If you fail and would love to re-verify, use the Factor ID: {enrolled_factor.id}")

        totp_passcode = input("Please enter the 6 digit code from TOTP device: ")
        verified_factor = await enroller.verify_factor(totp_passcode, enrolled_factor.id)

        if verified_factor == True:
            print("TOTP Successfully verified! You can release the TOTP hardware to the user now!")
        else:
            print("Verification Failed, Please try to setup again!")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
