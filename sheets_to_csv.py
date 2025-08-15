#!/usr/bin/env python3
"""
Google Sheets to CSV Fetcher
============================
Simple program to fetch data from Google Sheets using service account 
and save it to a CSV file.

Service Account: eri-494@logical-pilot-469015-a8.iam.gserviceaccount.com
Sheet ID: 1dPwooMcTc14nl3Rm5AsEiJfYL0xJE7HXNvQ6YHig6t4
"""

import os
import csv
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleSheetsToCSV:
    def __init__(self):
        # Service account configuration
        self.service_account_file = 'logical-pilot-469015-a8-3b018a70efc4.json'
        self.sheet_id = '1dPwooMcTc14nl3Rm5AsEiJfYL0xJE7HXNvQ6YHig6t4'
        self.range_name = 'Sheet1'
        self.sheets_service = None
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            print("🔐 Authenticating with Google Sheets API...")
            
            if not os.path.exists(self.service_account_file):
                print(f"❌ Service account file not found: {self.service_account_file}")
                return False
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build the service
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            
            print("✅ Successfully authenticated with Google Sheets API")
            print(f"📋 Sheet ID: {self.sheet_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to authenticate with Google Sheets API: {str(e)}")
            return False

    def fetch_sheets_data(self):
        """Fetch data from Google Sheets"""
        try:
            print(f"📖 Fetching data from Google Sheets...")
            
            # Read all data from the sheet
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("❌ No data found in spreadsheet")
                return None
            
            # Extract headers and data rows
            headers = values[0]
            data_rows = values[1:]
            
            print(f"📊 Found {len(data_rows)} data rows")
            print(f"📋 Headers: {headers}")
            
            # Display sample data
            print(f"\n📝 Sample data (first 3 rows):")
            for i, row in enumerate(data_rows[:3], 1):
                # Ensure row has enough columns
                while len(row) < len(headers):
                    row.append('')
                print(f"   Row {i}: {dict(zip(headers, row))}")
            
            return headers, data_rows
            
        except Exception as e:
            print(f"❌ Failed to fetch Google Sheets data: {str(e)}")
            return None

    def save_to_csv(self, headers, data_rows, filename=None):
        """Save data to CSV file"""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"sheets_data_{timestamp}.csv"
            
            print(f"💾 Saving data to CSV file: {filename}")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(headers)
                
                # Write data rows
                for row in data_rows:
                    # Ensure row has enough columns (pad with empty strings if needed)
                    while len(row) < len(headers):
                        row.append('')
                    writer.writerow(row)
            
            print(f"✅ Successfully saved {len(data_rows)} rows to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to save to CSV: {str(e)}")
            return None

    def analyze_data(self, headers, data_rows):
        """Analyze the data and show summary"""
        try:
            print(f"\n📊 DATA ANALYSIS")
            print("=" * 40)
            
            # Find rows that need processing
            answer_col_index = None
            if 'Answer' in headers:
                answer_col_index = headers.index('Answer')
            
            needs_processing = 0
            has_answers = 0
            
            for row in data_rows:
                if answer_col_index is not None and len(row) > answer_col_index:
                    answer = row[answer_col_index].strip()
                    if not answer or answer in ['Not Available', '', 'NaN', 'nan']:
                        needs_processing += 1
                    else:
                        has_answers += 1
                else:
                    needs_processing += 1
            
            print(f"📋 Total rows: {len(data_rows)}")
            print(f"✅ Rows with answers: {has_answers}")
            print(f"📝 Rows needing processing: {needs_processing}")
            
            # Show column information
            print(f"\n📁 Column Information:")
            for i, header in enumerate(headers):
                print(f"   Column {i+1}: {header}")
            
        except Exception as e:
            print(f"❌ Error analyzing data: {str(e)}")

    def run(self, output_filename=None):
        """Main function to fetch data and save to CSV"""
        try:
            print("🚀 GOOGLE SHEETS TO CSV FETCHER")
            print("=" * 40)
            
            # Authenticate
            if not self.authenticate_google_sheets():
                return False
            
            # Fetch data
            result = self.fetch_sheets_data()
            if not result:
                return False
            
            headers, data_rows = result
            
            # Analyze data
            self.analyze_data(headers, data_rows)
            
            # Save to CSV
            csv_filename = self.save_to_csv(headers, data_rows, output_filename)
            if not csv_filename:
                return False
            
            print(f"\n🎉 SUCCESS!")
            print(f"✅ Data fetched from Google Sheets")
            print(f"✅ Saved to: {csv_filename}")
            print(f"📊 Total rows: {len(data_rows)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in main process: {str(e)}")
            return False

def main():
    """Main function"""
    try:
        # Create fetcher instance
        fetcher = GoogleSheetsToCSV()
        
        # Ask user for output filename (optional)
        print("📁 Output file options:")
        print("1. Press Enter for auto-generated filename")
        print("2. Enter custom filename (e.g., 'my_data.csv')")
        
        output_file = input("\n💾 Output filename (or press Enter): ").strip()
        if not output_file:
            output_file = None
        
        # Run the fetcher
        success = fetcher.run(output_file)
        
        if success:
            print("\n✅ Google Sheets data successfully fetched and saved to CSV!")
        else:
            print("\n❌ Failed to fetch and save data!")
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
