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
            requestObject = {}
            self.fetchOrgRecord(requestObject)
        else:
            myOrgUnit = org.list_organizational_units_for_parent(
                ParentId = rootOrgUnit['Roots'][0]['Id'])
            self.envOrgUnitsSelection(myOrgUnit)
            
        return

    # for each account fetch child accounts if available
    def fetchOrgRecord(self, requestObject):
        organizations = org.list_accounts(**requestObject)

        # the result organizations is a dictionary. pick only accounts from them
        for accountRecord in organizations['Accounts']:
            acctInfo = {'Name': accountRecord['Name'], 'ID': accountRecord['Id'], 'Status': accountRecord['Status']}

            # add identified records to all accounts
            self.all_accounts.append(acctInfo)

            #if all accounts are requested, collect accounts by status also
            #if accounts are requested by status then only collect active or suspended account data
            if accountRecord['Status'] != 'SUSPENDED':
                self.active_accounts.append(acctInfo)

            else:
                self.suspended_accounts.append(acctInfo)    

        # when NextToken value exists prep for the next call
        if 'NextToken' in organizations :
            requestObject['NextToken'] = organizations["NextToken"]
            
            #call list accounts with next token - a recursive function
            self.fetchOrgRecord(requestObject)  
            

    def envOrgUnitsSelection(self, myOrgUnit):
        
        for orgUnit in myOrgUnit['OrganizationalUnits']:
            
            if orgUnit['Name'].lower() == self.environment.lower() or 'all' == self.environment.lower():
                #identify all accounts within child org
                self.accountsByOrg(orgUnit)
                
            else:
                # seek the environment through the hierarchy till its found
                childOrgUnit = org.list_organizational_units_for_parent(
                    ParentId = orgUnit['Id'])
                    
                self.envOrgUnitsSelection(childOrgUnit)

    
    def accountsByOrg(self,  orgUnit):
        accounts = org.list_accounts_for_parent(ParentId = orgUnit['Id'])
        for ids in accounts['Accounts']:
            acctInfo = {'Name': ids['Name'], 'ID': ids['Id'], 'Status': ids['Status']}

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