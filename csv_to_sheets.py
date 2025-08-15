#!/usr/bin/env python3
"""
CSV to Google Sheets Uploader
==============================
Simple program to read data from CSV file and upload it back to Google Sheets 
using service account authentication.

Service Account: eri-494@logical-pilot-469015-a8.iam.gserviceaccount.com
Sheet ID: 1dPwooMcTc14nl3Rm5AsEiJfYL0xJE7HXNvQ6YHig6t4
"""

import os
import csv
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

class CSVToGoogleSheets:
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

    def read_csv_file(self, csv_filename):
        """Read data from CSV file"""
        try:
            print(f"📖 Reading CSV file: {csv_filename}")
            
            if not os.path.exists(csv_filename):
                print(f"❌ CSV file not found: {csv_filename}")
                return None
            
            headers = []
            data_rows = []
            
            with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Read headers
                headers = next(reader)
                print(f"📋 Headers: {headers}")
                
                # Read data rows
                for row in reader:
                    data_rows.append(row)
            
            print(f"📊 Found {len(data_rows)} data rows in CSV")
            
            # Display sample data
            print(f"\n📝 Sample data (first 3 rows):")
            for i, row in enumerate(data_rows[:3], 1):
                row_dict = dict(zip(headers, row))
                print(f"   Row {i}: {row_dict}")
            
            return headers, data_rows
            
        except Exception as e:
            print(f"❌ Failed to read CSV file: {str(e)}")
            return None

    def clear_sheet(self):
        """Clear existing data in the sheet"""
        try:
            print("🗑️ Clearing existing sheet data...")
            
            # Clear all data in the sheet
            body = {
                'values': []
            }
            
            result = self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range=self.range_name,
                body={}
            ).execute()
            
            print(f"✅ Sheet cleared successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to clear sheet: {str(e)}")
            return False

    def upload_to_sheets(self, headers, data_rows, clear_first=True):
        """Upload data to Google Sheets"""
        try:
            print(f"📤 Uploading data to Google Sheets...")
            
            # Option to clear sheet first
            if clear_first:
                if not self.clear_sheet():
                    return False
            
            # Prepare data for upload (headers + data rows)
            all_data = [headers] + data_rows
            
            # Upload data
            body = {
                'values': all_data,
                'majorDimension': 'ROWS'
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=self.range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            print(f"✅ Successfully uploaded data to Google Sheets")
            print(f"📊 Updated {updated_cells} cells")
            print(f"📋 Uploaded {len(data_rows)} data rows + 1 header row")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to upload to Google Sheets: {str(e)}")
            return False

    def update_specific_column(self, csv_filename, column_name, start_row=2):
        """Update only a specific column (useful for updating just the Answer column)"""
        try:
            print(f"🎯 Updating specific column: {column_name}")
            
            # Read CSV data
            result = self.read_csv_file(csv_filename)
            if not result:
                return False
            
            headers, data_rows = result
            
            # Find column index
            if column_name not in headers:
                print(f"❌ Column '{column_name}' not found in CSV headers")
                return False
            
            column_index = headers.index(column_name)
            print(f"📍 Found '{column_name}' at column index {column_index + 1}")
            
            # Extract column data
            column_data = []
            for row in data_rows:
                if len(row) > column_index:
                    column_data.append([row[column_index]])
                else:
                    column_data.append([''])
            
            # Calculate column letter (A=1, B=2, etc.)
            column_letter = chr(ord('A') + column_index)
            range_name = f'Sheet1!{column_letter}{start_row}:{column_letter}{start_row + len(column_data) - 1}'
            
            print(f"📌 Updating range: {range_name}")
            
            # Update the specific column
            body = {
                'values': column_data,
                'majorDimension': 'ROWS'
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            print(f"✅ Successfully updated {column_name} column")
            print(f"📊 Updated {updated_cells} cells")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update column: {str(e)}")
            return False

    def analyze_csv_data(self, headers, data_rows):
        """Analyze CSV data before upload"""
        try:
            print(f"\n📊 CSV DATA ANALYSIS")
            print("=" * 40)
            
            print(f"📋 Total rows: {len(data_rows)}")
            print(f"📁 Total columns: {len(headers)}")
            
            # Show column information
            print(f"\n📁 Column Information:")
            for i, header in enumerate(headers):
                print(f"   Column {i+1} ({chr(ord('A') + i)}): {header}")
            
            # Analyze Answer column if it exists
            if 'Answer' in headers:
                answer_index = headers.index('Answer')
                answer_values = []
                empty_answers = 0
                
                for row in data_rows:
                    if len(row) > answer_index:
                        answer = row[answer_index].strip()
                        if not answer or answer in ['Not Available', '', 'NaN', 'nan']:
                            empty_answers += 1
                        else:
                            answer_values.append(answer)
                    else:
                        empty_answers += 1
                
                print(f"\n💡 Answer Column Analysis:")
                print(f"   ✅ Rows with answers: {len(answer_values)}")
                print(f"   📝 Rows without answers: {empty_answers}")
                if answer_values:
                    print(f"   🔍 Sample answers: {answer_values[:5]}")
            
        except Exception as e:
            print(f"❌ Error analyzing CSV data: {str(e)}")

    def run(self, csv_filename, mode="full", column_name=None):
        """Main function to upload CSV data to Google Sheets"""
        try:
            print("🚀 CSV TO GOOGLE SHEETS UPLOADER")
            print("=" * 40)
            
            # Authenticate
            if not self.authenticate_google_sheets():
                return False
            
            # Read CSV data
            result = self.read_csv_file(csv_filename)
            if not result:
                return False
            
            headers, data_rows = result
            
            # Analyze data
            self.analyze_csv_data(headers, data_rows)
            
            # Upload based on mode
            if mode == "full":
                # Full upload (replace all data)
                print(f"\n🔄 Mode: Full upload (replace all data)")
                success = self.upload_to_sheets(headers, data_rows, clear_first=True)
            elif mode == "column" and column_name:
                # Update specific column only
                print(f"\n🎯 Mode: Update column '{column_name}' only")
                success = self.update_specific_column(csv_filename, column_name)
            else:
                print(f"❌ Invalid mode or missing column name")
                return False
            
            if success:
                print(f"\n🎉 SUCCESS!")
                print(f"✅ CSV data uploaded to Google Sheets")
                print(f"📊 Total rows processed: {len(data_rows)}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"❌ Error in main process: {str(e)}")
            return False

def main():
    """Main function"""
    try:
        # Create uploader instance
        uploader = CSVToGoogleSheets()
        
        print("📁 CSV TO GOOGLE SHEETS UPLOADER")
        print("=" * 40)
        
        # Get CSV filename
        print("\n📂 CSV File Options:")
        print("1. Enter CSV filename")
        print("2. Use latest auto-generated file (sheets_data_*.csv)")
        
        choice = input("\nChoice (1 or 2): ").strip()
        
        csv_filename = None
        if choice == "2":
            # Find latest sheets_data file
            import glob
            files = glob.glob("sheets_data_*.csv")
            if files:
                csv_filename = max(files)  # Get most recent file
                print(f"📋 Using: {csv_filename}")
            else:
                print("❌ No sheets_data_*.csv files found")
                return
        else:
            csv_filename = input("📁 Enter CSV filename: ").strip()
            if not csv_filename:
                csv_filename = "sheets_data_20250815_022100.csv"  # Default to your current file
                print(f"📋 Using default: {csv_filename}")
        
        # Get upload mode
        print(f"\n🔄 Upload Mode Options:")
        print("1. Full upload (replace all data in sheet)")
        print("2. Update specific column only (e.g., just Answer column)")
        
        mode_choice = input("\nMode choice (1 or 2): ").strip()
        
        if mode_choice == "2":
            column_name = input("📋 Enter column name to update (e.g., 'Answer'): ").strip()
            if not column_name:
                column_name = "Answer"
            success = uploader.run(csv_filename, mode="column", column_name=column_name)
        else:
            success = uploader.run(csv_filename, mode="full")
        
        if success:
            print("\n✅ CSV data successfully uploaded to Google Sheets!")
        else:
            print("\n❌ Failed to upload CSV data!")
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
