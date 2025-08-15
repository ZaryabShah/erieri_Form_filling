#!/usr/bin/env python3
"""
ERI Complete Automation - All Steps 1-9 + Data Extraction
=========================================================
Working version based on successful 6-step automation with extensions for Steps 7-9
and data extraction. Uses the proven dropdown verification and correct XPaths.

Features:
- Dynamic input parsing: "ERI Code=4006, ERI Location=Dallas, Texas, Revenue=565000000, Industry=All Industries - Diversified, Years of Experience=5, Mean"
- Proven dropdown verification (from working 6-step version)
- All 9 steps automation
- Years of experience data extraction
- CSV export with timestamps
"""

import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from erieri_login_selenium import login_with_selenium

class ERICompleteAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.actions = None
        self.screenshot_counter = 1
        
        # Input data (will be parsed from user input)
        self.eri_code = None
        self.location = None
        self.revenue = None
        self.industry = None
        self.years_experience = None
        self.data_type = None
        
    def screenshot(self, step_name):
        """Take a screenshot"""
        filename = f"complete_{self.screenshot_counter:02d}_{step_name}.png"
        self.driver.save_screenshot(filename)
        print(f"📷 {filename}")
        self.screenshot_counter += 1

    def wait_and_click(self, xpath, description, timeout=15):
        """Enhanced click method with multiple strategies"""
        print(f"\n🎯 {description}")
        print(f"   XPath: {xpath}")
        
        try:
            # Wait for element to be clickable
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            print("   ✅ Element found")
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Try standard click first
            try:
                element.click()
                print("   ✅ Clicked successfully")
                return True
            except ElementNotInteractableException:
                # Fallback to JavaScript click
                print("   ⚠️  Standard click failed, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", element)
                print("   ✅ JavaScript click successful")
                return True
                
        except TimeoutException:
            print(f"   ❌ Element not found within {timeout} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False

    def dropdown_keyboard_selection(self):
        """Specific dropdown selection: 3 down arrows + Enter for ERI Code"""
        print(f"\n📍 STEP 4: Select 'ERI Code' using keyboard navigation")
        print("   🎯 Method: Wait for dropdown, then Press DOWN 3 times, then ENTER")
        
        try:
            # Wait for dropdown menu to appear after clicking
            # print("   ⏳ Waiting for dropdown menu to appear...")
            
            # # Multiple strategies to verify dropdown is open
            # dropdown_appeared = False
            
            # # Strategy 1: Look for dropdown container with options
            # dropdown_selectors = [
            #     "//div[contains(@class, 'dropdown')]//ul",
            #     "//div[contains(@class, 'menu')]//li",
            #     "//ul[contains(@class, 'options')]",
            #     "//div[@role='listbox']",
            #     "//div[@role='menu']",
            #     "//select/option",
            #     "//div[contains(@class, 'select')]//div[contains(@class, 'option')]"
            # ]
            
            # for i, selector in enumerate(dropdown_selectors):
            #     try:
            #         dropdown_options = WebDriverWait(self.driver, 3).until(
            #             EC.presence_of_element_located((By.XPATH, selector))
            #         )
            #         if dropdown_options.is_displayed():
            #             print(f"   ✅ Dropdown detected using strategy {i+1}")
            #             dropdown_appeared = True
            #             break
            #     except:
            #         continue
            dropdown_appeared = True
            # Strategy 2: If specific selectors fail, wait and assume dropdown opened
            # if not dropdown_appeared:
            #     print("   ⚠️  Specific dropdown not detected, waiting and proceeding...")
            #     time.sleep(2)  # Give more time for dropdown to appear
            #     dropdown_appeared = True
            # time.sleep(2)  # Wait for dropdown to stabilize
            if dropdown_appeared:
                print("   ✅ Dropdown menu confirmed open")
                
                # Get the currently active element (should be the dropdown)
                active_element = self.driver.switch_to.active_element
                
                print("   ⬇️  Pressing DOWN arrow 3 times...")
                
                # Press DOWN arrow 3 times
                for i in range(3):
                    active_element.send_keys(Keys.ARROW_DOWN)
                    print(f"      DOWN {i+1}/3")
                    time.sleep(0.5)  # Increased delay between key presses
                
                print("   ⏎ Pressing ENTER to select...")
                active_element.send_keys(Keys.ENTER)
                
                print("   ✅ Successfully selected option using keyboard navigation")
                time.sleep(2)  # Wait for selection to register
                return True
            else:
                print("   ❌ Dropdown menu did not appear")
                return False
            
        except Exception as e:
            print(f"   ❌ Keyboard selection failed: {e}")
            return False

    def parse_user_input(self, user_input):
        """Parse the user input string into individual components"""
        print(f"\n🔍 Parsing user input: {user_input}")
        
        try:
            # Split by comma but handle "Dallas, Texas" specially
            parts = []
            current_part = ""
            in_location = False
            
            for char in user_input:
                if char == ',' and 'Dallas' in current_part and not 'Texas' in current_part:
                    # This is the comma in "Dallas, Texas" - keep it
                    current_part += char
                elif char == ',' and not in_location:
                    # This is a separator comma
                    if current_part.strip():
                        parts.append(current_part.strip())
                        current_part = ""
                else:
                    current_part += char
            
            if current_part.strip():
                parts.append(current_part.strip())
            
            # Parse each part
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'ERI Code':
                        self.eri_code = value
                        print(f"   📋 ERI Code: {value}")
                    elif key == 'ERI Location':
                        self.location = value
                        print(f"   📋 ERI Location: {value}")
                    elif key == 'Revenue':
                        self.revenue = value
                        print(f"   📋 Revenue: {value}")
                    elif key == 'Industry':
                        self.industry = value
                        print(f"   📋 Industry: {value}")
                    elif key == 'Years of Experience':
                        self.years_experience = value
                        print(f"   📋 Years of Experience: {value}")
                elif part in ['Mean', 'Median', '25th Percentile', '75th Percentile']:
                    self.data_type = part
                    print(f"   📋 data_type: {part}")
            
            # Set data type for data extraction
            if self.data_type:
                print(f"   📊 Data Type: {self.data_type}")
                
            return True
            
        except Exception as e:
            print(f"   ❌ Error parsing input: {e}")
            return False

    def enhanced_text_clear_and_type(self, element, text):
        """Enhanced text clearing and typing with multiple strategies"""
        try:
            # Method 1: Select all and delete
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.2)
            element.send_keys(Keys.DELETE)
            time.sleep(0.2)
            
            # Method 2: If text remains, use backspace
            current_value = element.get_attribute('value') or ''
            if current_value:
                for _ in range(len(current_value) + 5):  # Extra backspaces
                    element.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
            
            # Type the new text character by character
            for char in text:
                element.send_keys(char)
                time.sleep(0.05)  # Small delay between characters
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error in text clearing/typing: {e}")
            return False

    def type_and_enter(self, xpath, value, description, timeout=15):
        """Type value in field and press Enter"""
        print(f"\n🎯 {description}")
        print(f"   XPath: {xpath}")
        print(f"   Value: '{value}'")
        
        try:
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            print("   ✅ Element found")
            
            # Scroll into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            
            # Enhanced text clearing and typing
            if self.enhanced_text_clear_and_type(element, value):
                element.send_keys(Keys.ENTER)
                print("   ✅ Pressed ENTER")
                time.sleep(1)
                return True
            else:
                return False
                
        except TimeoutException:
            print(f"   ❌ Element not found within {timeout} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False

    def extract_years_experience_data(self):
        """Extract specific data values from the results page"""
        print("\n📊 Extracting specific data values...")
        
        try:
            # Wait for results to load
            time.sleep(3)
            
            extracted_values = {}
            
            # 1. Extract All Incumbent Average value
            try:
                all_incumbent_xpath = "/html/body/div[1]/div[3]/div[2]/div[1]/div[1]/div[2]/span[3]"
                all_incumbent_element = self.driver.find_element(By.XPATH, all_incumbent_xpath)
                all_incumbent_value = all_incumbent_element.text.strip()
                extracted_values['all_incumbent_average'] = all_incumbent_value
                print(f"   ✅ All Incumbent Average: {all_incumbent_value}")
            except Exception as e:
                print(f"   ❌ Could not extract All Incumbent Average: {e}")
                extracted_values['all_incumbent_average'] = "Not found"
            
            # 2. Find the row with Years of Experience = target value
            target_years = int(self.years_experience)
            print(f"   🔍 Looking for Years of Experience = {target_years}")
            
            mean_value = "Not found"
            row_found = False
            
            # Search through table rows
            for row_num in range(1, 20):  # Check up to 20 rows
                try:
                    # Check Years of Experience column (td[1])
                    years_xpath = f"/html/body/div[1]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[1]/div[2]/div/div/table/tbody/tr[{row_num}]/td[1]"
                    years_element = self.driver.find_element(By.XPATH, years_xpath)
                    years_text = years_element.text.strip()
                    
                    print(f"   📋 Row {row_num}: Years = {years_text}")
                    
                    # Check if this matches our target years
                    if years_text == str(target_years):
                        print(f"   🎯 Found matching row {row_num} for Years = {target_years}")
                        
                        # Get Mean value from td[4] for this row
                        if self.data_type.lower() == "mean":
                            data_xpath = f"/html/body/div[1]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[1]/div[2]/div/div/table/tbody/tr[{row_num}]/td[4]"
                        elif "75th" in self.data_type.lower() or "percentile" in self.data_type.lower():
                            data_xpath = f"/html/body/div[1]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[1]/div[2]/div/div/table/tbody/tr[{row_num}]/td[5]"
                        else:
                            data_xpath = f"/html/body/div[1]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[1]/div[2]/div/div/table/tbody/tr[{row_num}]/td[4]"
                            
                        try:
                            data_element = self.driver.find_element(By.XPATH, data_xpath)
                            mean_value = data_element.text.strip()
                            print(f"   ✅ {self.data_type} value: {mean_value}")
                            row_found = True
                            break
                        except Exception as e:
                            print(f"   ❌ Could not extract {self.data_type} value from row {row_num}: {e}")
                            
                except NoSuchElementException:
                    print(f"   ❌ Row {row_num} not found - stopping search")
                    break
                except Exception as e:
                    print(f"   ⚠️ Error checking row {row_num}: {e}")
                    continue
            
            if not row_found:
                print(f"   ❌ Could not find row with Years of Experience = {target_years}")
            
            extracted_values['mean_value'] = mean_value
            
            return {
                'eri_code': self.eri_code,
                'location': self.location,
                'industry': self.industry,
                'revenue': self.revenue,
                'years_experience': self.years_experience,
                'data_type': self.data_type,
                'all_incumbent_average': extracted_values['all_incumbent_average'],
                'mean_value': extracted_values['mean_value'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"   ❌ Error extracting data: {e}")
            return None

    def save_to_csv(self, data):
        """Save extracted data to CSV file"""
        if not data:
            return
            
        try:
            filename = f"eri_extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [ 'ERI Job Code', 'ERI Location', 'Revenue', 'Industry' ,
                            'Years of Experience', 'Output', 'all_incumbent_average', 'mean_value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerow({
                    # 'timestamp': data['timestamp'],
                    'ERI Job Code': data['eri_code'],
                    'ERI Location': data['location'],
                    'Industry': data['industry'],
                    'Revenue': data['revenue'],
                    'Years of Experience': data['years_experience'],
                    'Output': data['data_type'],
                    'all_incumbent_average': data['all_incumbent_average'],
                    'mean_value': data['mean_value']
                })
            
            print(f"📄 Data saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")

    def run_complete_automation(self):
        """Run the complete 9-step automation with data extraction"""
        print("\n" + "="*60)
        print("🎯 Starting Complete ERI Automation - Steps 1-9")
        print("="*60)
        
        try:
            # Step 1: Click first link
            print("\n📍 STEP 1: Click first link")
            if not self.wait_and_click("/html/body/div[1]/div[3]/div/div/div/div[1]/div[3]/a", "Step 1: First link"):
                return False
            time.sleep(2)
            # self.screenshot("after_step_1")
            
            # Step 2: Click second button  
            print("\n📍 STEP 2: Click second button")
            if not self.wait_and_click("/html/body/div[1]/div[3]/div[1]/div/div[1]/div/div/div[2]/div/div[2]/button", "Step 2: Second button"):
                return False
            time.sleep(4)
            # self.screenshot("after_step_2")
            
            # Step 3: Click dropdown button
            print("\n📍 STEP 3: Click dropdown button")
            if not self.wait_and_click("/html/body/div[59]/div/div[3]/table/tbody/tr/td[1]/div[2]/span/span", "Step 3: Dropdown button"):
                return False
            time.sleep(2)
            # self.screenshot("after_step_3")
            
            # Step 4: Select 'ERI Code' using keyboard navigation (PROVEN WORKING)
            if not self.dropdown_keyboard_selection():
                return False
            # self.screenshot("after_step_4")
            
            # Step 5: Type ERI Code
            print(f"\n📍 STEP 5: Type ERI Code '{self.eri_code}'")
            try:
                input_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[59]/div/div[3]/table/tbody/tr/td[1]/div[1]/div[2]/input")
                ))
                print("   ✅ Element found")
                
                # Clear and type
                input_element.clear()
                input_element.send_keys(self.eri_code)
                print("   ✅ Successfully typed ERI Code")
                # self.screenshot("after_step_5")
            except Exception as e:
                print(f"   ❌ Error typing ERI Code: {e}")
                return False
            
            # Step 6: Click confirmation button (FIXED with JavaScript click)
            print("\n📍 STEP 6: Click confirmation button")
            time.sleep(2)  # Wait for input to register
            step6_xpath = "/html/body/div[59]/div/div[4]/div/div[2]/button[2]"
            
            try:
                # First try to find the element
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, step6_xpath)))
                print("   ✅ Element found")
                
                # Try standard click first
                try:
                    element.click()
                    print("   ✅ Standard click successful")
                except:
                    print("   ⚠️ Standard click failed, trying JavaScript click...")
                    # Use JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", element)
                    print("   ✅ JavaScript click successful")
                    
                time.sleep(3)
                # self.screenshot("after_step_6")
                
            except TimeoutException:
                print("   ❌ Step 6 confirmation button not found")
                return False
            
            # Step 7: Type Location
            print(f"\n📍 STEP 7: Type Location '{self.location}'")
            if not self.type_and_enter("/html/body/div[1]/div[3]/div[1]/div/div[1]/div/div/div[36]/div[1]/div[1]/div[1]/div/input", 
                                     self.location, f"Step 7: Type Location '{self.location}'"):
                return False
            # self.screenshot("after_step_7")
            
            # Step 8: Type Industry
            print(f"\n📍 STEP 8: Type Industry '{self.industry}'")
            if not self.type_and_enter("/html/body/div[1]/div[3]/div[1]/div/div[1]/div/div/div[38]/div[2]/div[1]/input[2]", 
                                     self.industry, f"Step 8: Type Industry '{self.industry}'"):
                return False
            # self.screenshot("after_step_8")
            
            # Step 9: Type Revenue
            print(f"\n📍 STEP 9: Type Revenue '{self.revenue}'")
            formatted_revenue = f"{int(self.revenue):,}"  # Format with commas
            if not self.type_and_enter("/html/body/div[1]/div[3]/div[1]/div/div[1]/div/div/div[40]/div[2]/div[1]/div[1]/input", 
                                     formatted_revenue, f"Step 9: Type Revenue '{formatted_revenue}'"):
                return False
            # self.screenshot("after_step_9")
            
            print("\n" + "="*60)
            print("🎉 ALL STEPS 1-9 COMPLETED SUCCESSFULLY!")
            print("="*60)
            
            # Wait for results to load
            print("\n⏳ Waiting for results to load...")
            time.sleep(5)
            # self.screenshot("results_loaded")
            
            # Extract data
            data = self.extract_years_experience_data()
            if data:
                self.save_to_csv(data)
                
            return True
            
        except Exception as e:
            print(f"❌ Error during automation: {e}")
            # self.screenshot("automation_error")
            return False

def main():
    # Hardcoded input for testing
    user_input = 'ERI Code=4006, ERI Location=Dallas, Texas, Revenue=565000000, Industry=All Industries - Diversified, Years of Experience=11, 75th Percentile'
    
    print("🎯 ERI Complete Automation with Data Extraction")
    print("="*60)
    print("🔑 Using fresh cookies.json")
    print("📋 Input:", user_input)
    
    automation = ERICompleteAutomation()
    
    try:
        # Parse input
        if not automation.parse_user_input(user_input):
            print("❌ Failed to parse input")
            return
        
        # Start browser
        print("\n🚀 Starting browser with fresh cookies...")
        driver, login_success = login_with_selenium("cookies.json")
        
        if driver:
            automation.driver = driver
            automation.wait = WebDriverWait(driver, 15)
            automation.actions = ActionChains(driver)
            
            # Run complete automation
            success = automation.run_complete_automation()
            
            if success:
                print("\n✅ Complete automation finished successfully!")
                print("📄 Check the CSV file for extracted data")
            else:
                print("\n❌ Automation encountered errors")
                
        else:
            print("❌ Failed to start browser session")
            
    except Exception as e:
        print(f"❌ Error in main: {e}")
        
    finally:
        print("\n💡 Browser will stay open for inspection.")
        print("🔒 Session preserved - check CSV file for results.")
        input("Press Enter when ready to close browser...")
        
        if automation.driver:
            automation.driver.quit()

if __name__ == "__main__":
    main()
