import boto3
import os

session = boto3.Session()
org = session.client('organizations')

def lambda_handler(event, context):
    ou = os.environ['orgUnit']
    results = Accounts(ou).active_accounts
    print("Results: {}".format(results))
    return results
    
class Accounts(object):
    
    def __init__(self, environment):
        # Returns only accounts with a status of active.
        self.all_accounts = []

        # Returns only accounts with a status of active.
        self.active_accounts = []
        
        # Returns only the accounts with a status of suspended.
        self.suspended_accounts = []

        self.fetch_accounts(environment)
        return

    def fetch_accounts(self, environment):
        # Specify which you want returned 
        self.environment = environment
        
        rootOrgUnit = org.list_roots()

        if self.environment.lower() == 'all' or self.environment.lower() == 'root':
            self.envOrgUnitsSelection(rootOrgUnit, 'Roots')
        else:
            myOrgUnit = org.list_organizational_units_for_parent(
                ParentId = rootOrgUnit['Roots'][0]['Id'])
            self.envOrgUnitsSelection(myOrgUnit, 'OrganizationalUnits')
            
        return
            
    def accountExists(self, accounts, newAcct):
        exists = False
        for account in accounts:
            if account['Name'] == newAcct['Name'] and account['ID'] == newAcct['ID']:
                exists = True
                break
        return exists
        
    def envOrgUnitsSelection(self, myOrgUnit, key):
        
        for orgUnit in myOrgUnit[key]:
            
            if orgUnit['Name'].lower() == self.environment.lower() or 'all' == self.environment.lower():
                #identify all accounts within child org
                self.accountsByOrg(orgUnit)
                
            else:
                # seek the environment through the hierarchy till its found
                childOrgUnit = org.list_organizational_units_for_parent(
                    ParentId = orgUnit['Id'])
                    
                self.envOrgUnitsSelection(childOrgUnit, 'OrganizationalUnits')

    
    def accountsByOrg(self,  orgUnit):
        accounts = org.list_accounts_for_parent(ParentId = orgUnit['Id'])
        for ids in accounts['Accounts']:
            acctInfo = {'Name': ids['Name'], 'ID': ids['Id'], 'Status': ids['Status']}

            isExisting = self.accountExists(self.active_accounts, acctInfo)
            print("isExisting = {}".format(isExisting))
            # add identified records to all accounts
            if not isExisting:
                
                if 'all' == self.environment.lower():
                    self.all_accounts.append(acctInfo)
                
                #if all accounts are requested, collect accounts by status also
                #if accounts are requested by status then only collect active or suspended account data
                if ids['Status'] != 'SUSPENDED':
                    self.active_accounts.append(acctInfo)
                else:
                    self.suspended_accounts.append(acctInfo)
            
            childOrgUnits = org.list_organizational_units_for_parent(
                    ParentId = orgUnit['Id'])
                    
            for childOrgUnit in childOrgUnits['OrganizationalUnits']:
                self.accountsByOrg(childOrgUnit)
                
    def get_all_accounts(self):
        return self.all_accounts