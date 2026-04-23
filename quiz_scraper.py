from selenium.webdriver.common.by import By
import time
import random
import re
import json
from pathlib import Path
from datetime import datetime
from base_browser import BaseBrowser
from models import Question, Option

class QuizScraper(BaseBrowser):
    def __init__(self, base_dir="quiz_screenshots"):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def manual_login(self):
        """Guide user through manual login to avoid bot detection"""
        print("\n" + "="*70)
        print("🔐 MANUAL LOGIN")
        print("="*70)
        print("\n1. Browser will open to Udemy")
        print("2. Login with your credentials")
        print("3. Navigate to your first course and first exam start page")
        print("4. STOP at the exam start page (don't click 'Start Quiz' yet)")
        print("5. Return here and press ENTER")
        print("\n" + "="*70)
        
        self.driver.get("https://www.udemy.com/")
        input("\n⏸️  Press ENTER when you're ready at the exam start page...")
        time.sleep(2)

    def _check_and_switch_to_quiz_frame(self):
        """Switch to iframe if quiz is embedded in one"""
        self.driver.switch_to.default_content()
        time.sleep(1)
        
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            try:
                self.driver.switch_to.frame(frame)
                # Check if this iframe contains quiz elements
                if self.driver.find_elements(By.CSS_SELECTOR, "button[data-purpose='start-quiz'], div[class*='question']"):
                    print("  💡 Switched to quiz iframe")
                    return
                self.driver.switch_to.default_content()
            except:
                self.driver.switch_to.default_content()
                continue

    def _debug_page_structure(self):
        """
        Debug helper: Print the DOM structure to help identify correct selectors.
        Call this after clicking 'Check Answer' to see what's available.
        """
        print("\n" + "="*70)
        print("DEBUG: Page Structure After 'Check Answer'")
        print("="*70)
        
        # Check for answer divs with data-purpose="answer"
        print("\n1. Looking for answer containers [div[data-purpose='answer']]:")
        try:
            answer_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-purpose="answer"]')
            print(f"  ✓ Found {len(answer_divs)} answer div(s)")
            
            if len(answer_divs) > 0:
                print("\n  First answer div structure:")
                first = answer_divs[0]
                print(f"    Outer HTML (first 300 chars):")
                print(f"    {first.get_attribute('outerHTML')[:300]}...")
                
                # Check for #answer-text
                try:
                    text_elem = first.find_element(By.CSS_SELECTOR, '#answer-text')
                    print(f"\n    ✓ Found #answer-text: '{text_elem.text}'")
                except:
                    print(f"\n    ✗ #answer-text not found")
                
                # Check for state classes
                class_attr = first.get_attribute("class")
                print(f"    Class attribute: {class_attr}")
                
                # Check child divs
                try:
                    child_divs = first.find_elements(By.CSS_SELECTOR, 'div[class*="answer-"]')
                    print(f"    Found {len(child_divs)} child divs with 'answer-' in class")
                    for i, child in enumerate(child_divs[:3]):  # Show first 3
                        print(f"      Child {i}: {child.get_attribute('class')}")
                except:
                    pass
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Check for explanation containers
        print("\n2. Looking for explanation containers:")
        test_selectors = [
            "#overall-explanation",
            "div[class*='explanation']",
            "div[data-purpose='question-explanation']"
        ]
        for sel in test_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    print(f"  ✓ Found: {sel} ({len(els)} elements)")
                    if els[0].is_displayed():
                        print(f"    Text preview: {els[0].text[:100]}...")
            except:
                pass
        
        print("="*70 + "\n")
        input("Press ENTER to continue...")

    def _detect_required_selections(self) -> int:
        """Detect how many options need to be selected (for multiple choice)"""
        instruction_selectors = [
            "[class*='instruction']",
            "#question-prompt",
            "div[class*='question-viewer']"
        ]
        
        for selector in instruction_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.lower()
                    # Look for "select 2" or "choose 3"
                    match = re.search(r'select (\d+)|choose (\d+)', text)
                    if match:
                        return int(match.group(1) or match.group(2))
                    # "Select all that apply" means all checkboxes
                    if "all that apply" in text:
                        return len(self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"))
            except:
                continue
        
        # Default to 2 for multiple choice if can't detect
        return 2

    def _select_unique_answers(self, count: int):
        """Randomly select answers to trigger the 'Check Answer' reveal"""
        selectors = [
            "input[type='radio']",
            "input[type='checkbox']",
            "label[class*='mc-quiz-answer']",
            "li[class*='mc-quiz-question--answer']"
        ]
        
        options = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if found:
                    options = [o for o in found if o.is_displayed()]
                    if options:
                        break
            except:
                continue
        
        if not options:
            input(f"⚠️  Manual: Select {count} answer(s), then press ENTER...")
            return

        # Randomly select required number of options
        to_select = random.sample(options, min(count, len(options)))
        for option in to_select:
            try:
                self.scroll_to_element(option)
                self.click_element_js(option)
                time.sleep(0.3)
            except:
                continue

    def _extract_question_data(self, q_num: int, q_type: str) -> Question:
        """
        Extract all question data from DOM after 'Check Answer' is clicked.
        Uses exact selectors for Udemy's post-answer state.
        """
        q_data = {
            'number': str(q_num),
            'text': "Not Found",
            'all_options': [],
            'correct_answers': [],
            'user_incorrect_answers': [],
            'correct_indices': [],
            'explanation': ""
        }
        
        try:
            # 1. Extract Question Number
            number_selectors = [
                "div[class*='question-title']",
                "form[data-testid='mc-quiz-question'] span",
                "div[class*='question-number']"
            ]
            for sel in number_selectors:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for e in els:
                    if "Question" in e.text:
                        q_data['number'] = e.text.replace(':', '').strip()
                        break
                if q_data['number'] != str(q_num):
                    break

            # 2. Extract Question Text
            text_selectors = [
                "#question-prompt",
                "div[class*='mc-quiz-question--question-prompt']",
                "div[data-purpose='question-prompt']"
            ]
            for sel in text_selectors:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    q_data['text'] = els[0].text.strip()
                    break
            
            # 3. Extract ALL Options using exact selectors
            # Find all answer containers: div[data-purpose="answer"]
            answer_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-purpose="answer"]')
            
            print(f"  📋 Found {len(answer_divs)} answer divs")
            
            for idx, answer_div in enumerate(answer_divs):
                try:
                    # Get the option text from #answer-text inside this div
                    option_text = ""
                    try:
                        text_elem = answer_div.find_element(By.CSS_SELECTOR, '#answer-text')
                        option_text = text_elem.text.strip()
                    except:
                        # Fallback: try other text selectors
                        try:
                            text_elem = answer_div.find_element(By.CSS_SELECTOR, '[id*="answer-text"]')
                            option_text = text_elem.text.strip()
                        except:
                            option_text = answer_div.text.strip()
                    
                    if not option_text:
                        continue
                    
                    # Determine the state by checking the class attribute
                    # Get the wrapper div inside answer_div that has the state classes
                    state = "skipped"
                    is_correct = False
                    is_user_selected = False
                    
                    # Check the answer_div itself and its children for state classes
                    html_content = answer_div.get_attribute("outerHTML")
                    class_attr = answer_div.get_attribute("class") or ""
                    
                    # Also check immediate child divs for the state classes
                    try:
                        child_divs = answer_div.find_elements(By.CSS_SELECTOR, 'div[class*="answer-"]')
                        for child in child_divs:
                            child_class = child.get_attribute("class") or ""
                            class_attr += " " + child_class
                    except:
                        pass
                    
                    # Determine state based on class names
                    if "answer-correct" in class_attr or "answer-correct" in html_content:
                        state = "correct"
                        is_correct = True
                        q_data['correct_answers'].append(option_text)
                        q_data['correct_indices'].append(idx)
                    elif "answer-incorrect" in class_attr or "answer-incorrect" in html_content:
                        state = "incorrect"
                        is_user_selected = True
                        q_data['user_incorrect_answers'].append(option_text)
                    elif "answer-skipped" in class_attr or "answer-skipped" in html_content:
                        state = "skipped"
                    
                    # Try to extract individual option explanation
                    option_explanation = ""
                    try:
                        # Look for explanation elements within this answer div
                        expl_selectors = [
                            "div[class*='explanation']",
                            "span[class*='explanation']",
                            "div[class*='feedback']",
                            "div[data-purpose='explanation']"
                        ]
                        for expl_sel in expl_selectors:
                            expl_elem = answer_div.find_element(By.CSS_SELECTOR, expl_sel)
                            if expl_elem.is_displayed():
                                option_explanation = expl_elem.text.strip()
                                break
                    except:
                        pass
                    
                    # Create Option object
                    option_obj = Option(
                        text=option_text,
                        is_correct=is_correct,
                        is_user_selected=is_user_selected,
                        index=idx,
                        explanation=option_explanation,
                        state=state
                    )
                    
                    q_data['all_options'].append(option_obj)
                    
                except Exception as e:
                    print(f"  ⚠️ Error processing option {idx}: {e}")
                    continue
            
            # 4. Extract Overall Explanation from #overall-explanation
            explanation_selectors = [
                "#overall-explanation",
                "div[id='overall-explanation']",
                "div[class*='explanation--explanation']",
                "div[data-purpose='question-explanation']",
                "div[class*='quiz-result-panel']"
            ]
            
            for sel in explanation_selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els and els[0].is_displayed():
                        q_data['explanation'] = els[0].text.strip()
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Extraction Error: {e}")
        
        # Debug output to verify extraction
        print(f"  ✓ Question: {q_data['text'][:50]}...")
        print(f"  ✓ All Options: {len(q_data['all_options'])} found")
        print(f"  ✓ Correct Answers: {len(q_data['correct_answers'])} - {q_data['correct_answers']}")
        print(f"  ✓ User Incorrect: {len(q_data['user_incorrect_answers'])} - {q_data['user_incorrect_answers']}")
        print(f"  ✓ Overall Explanation: {'Yes' if q_data['explanation'] else 'No'}")
        
        return Question(
            question_number=q_data['number'],
            question_text=q_data['text'],
            question_type=q_type,
            all_options=q_data['all_options'],
            correct_answers=q_data['correct_answers'],
            user_incorrect_answers=q_data['user_incorrect_answers'],
            options=q_data['all_options'],  # Legacy compatibility
            correct_indices=q_data['correct_indices'],
            explanation=q_data['explanation']
        )

    def scrape_exam(self, course_name: str, exam_number: int, total_questions: int = 90, debug_mode: bool = False):
        """
        Main scraping loop for one exam.
        For each question: select random answer → check → extract data → screenshot → save → next
        """
        # Create directory structure
        exam_dir = self.base_dir / f"{course_name.replace(' ', '_')}" / f"exam_{exam_number}"
        exam_dir.mkdir(parents=True, exist_ok=True)
        
        # Switch to iframe if needed
        self._check_and_switch_to_quiz_frame()
        
        # Click "Start Quiz" button
        self._click_generic_button([
            "//button[contains(., 'Start')]",
            "button[data-purpose='start-quiz']"
        ])
        time.sleep(4)
        
        captured = []
        
        for q_num in range(1, total_questions + 1):
            print(f"\n[{q_num}/{total_questions}] Processing...")
            
            try:
                time.sleep(2)
                
                # Detect question type (single vs multiple choice)
                has_checkboxes = len(self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "input[type='checkbox'], [class*='checkbox']"
                )) > 0
                
                q_type = "multiple_choice" if has_checkboxes else "single_choice"
                
                # Determine how many options to select
                required = self._detect_required_selections() if q_type == "multiple_choice" else 1
                
                # Select random answers (to trigger the reveal)
                self._select_unique_answers(required)
                
                # Click "Check Answer" to reveal correct answers and explanation
                self._click_generic_button([
                    "//button[contains(., 'Check')]",
                    "button[data-purpose='check-answer']"
                ])
                time.sleep(5)  # Wait for explanation to load
                
                # Optional: Debug page structure (only on first question if enabled)
                if debug_mode and q_num == 1:
                    self._debug_page_structure()
                
                # Extract all data from DOM
                question_obj = self._extract_question_data(q_num, q_type)
                
                # Save screenshot as backup
                screenshot_path = exam_dir / f"q{q_num:03d}.png"
                self.driver.save_screenshot(str(screenshot_path))
                question_obj.screenshot_path = str(screenshot_path)
                
                captured.append(question_obj)
                
                # Save progress incrementally (in case of crash)
                self._save_incremental_json(course_name, exam_number, captured, exam_dir)
                
                # Move to next question
                if q_num < total_questions:
                    self._click_generic_button([
                        "//button[contains(., 'Next')]",
                        "button[data-purpose='next-question']"
                    ])
                
            except Exception as e:
                input(f"❌ Error on Q{q_num}: {e}. Resolve manually then ENTER...")
        
        print(f"\n✅ Exam {exam_number} complete! Data saved to {exam_dir}")

    def _click_generic_button(self, selectors):
        """Try multiple selectors to find and click a button"""
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    btn = self.driver.find_element(By.XPATH, selector)
                else:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                if btn.is_displayed():
                    self.scroll_to_element(btn)
                    self.click_element_js(btn)
                    return
            except:
                continue
        
        input(f"⚠️ Button {selectors} not found. Click manually then press ENTER...")

    def _save_incremental_json(self, course: str, exam_num: int, questions: list, exam_dir: Path):
        """Save extracted data to JSON after each question (prevents data loss)"""
        with open(exam_dir / "exam_data.json", 'w', encoding='utf-8') as f:
            data = {
                'course': course,
                'exam_number': exam_num,
                'questions': [vars(q) for q in questions],
                'timestamp': datetime.now().isoformat()
            }
            
            # Convert Option objects to dicts in both 'options' and 'all_options' fields
            for q in data['questions']:
                # Convert all_options
                if 'all_options' in q:
                    q['all_options'] = [vars(o) for o in q['all_options']]
                # Convert options (legacy field)
                if 'options' in q:
                    q['options'] = [vars(o) for o in q['options']]
            
            json.dump(data, f, indent=2, ensure_ascii=False)