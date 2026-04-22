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
        This gets: question text, all options, correct answers, and explanation.
        """
        q_data = {
            'number': str(q_num),
            'text': "Not Found",
            'options': [],
            'correct_indices': [],
            'explanation': ""
        }
        
        try:
            # 1. Extract Question Number
            for sel in ["div[class*='question-title']", "form[data-testid='mc-quiz-question'] span"]:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for e in els:
                    if "Question" in e.text:
                        q_data['number'] = e.text.replace(':', '').strip()
                        break

            # 2. Extract Question Text
            for sel in ["#question-prompt", "div[class*='mc-quiz-question--question-prompt']"]:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    q_data['text'] = els[0].text.strip()
                    break
            
            # 3. Extract Options and Identify Correct Answers
            # After clicking "Check Answer", Udemy marks correct answers with CSS classes
            for sel in ["li[class*='mc-quiz-question--answer']", "ul[class*='ud-unstyled-list'] li"]:
                found = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if found and found[0].is_displayed():
                    for idx, el in enumerate(found):
                        text = el.text.strip()
                        if not text:
                            continue
                        
                        # Check if this option is marked as correct
                        is_correct = False
                        html = el.get_attribute("outerHTML").lower()
                        
                        # Udemy uses these indicators for correct answers
                        if any(x in html for x in ["correct", "success", "check-circle"]):
                            is_correct = True
                        
                        if is_correct:
                            q_data['correct_indices'].append(idx)
                        
                        q_data['options'].append(
                            Option(text=text, is_correct=is_correct, index=idx)
                        )
                    break
            
            # 4. Extract Explanation (shown after submitting answer)
            explanation_selectors = [
                "div[class*='result-pane--answer-result-pane']",
                "div[class*='domain-pane']",
                "div[data-testid='description']"
            ]
            
            for sel in explanation_selectors:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    q_data['explanation'] = "\n".join([
                        e.text.strip() for e in els if e.is_displayed()
                    ])
                    break
                    
        except Exception as e:
            print(f"⚠️ Extraction Warning: {e}")
        
        return Question(
            question_number=q_data['number'],
            question_text=q_data['text'],
            question_type=q_type,
            options=q_data['options'],
            correct_indices=q_data['correct_indices'],
            explanation=q_data['explanation']
        )

    def scrape_exam(self, course_name: str, exam_number: int, total_questions: int = 90):
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
            
            # Convert Option objects to dicts
            for q in data['questions']:
                q['options'] = [vars(o) for o in q['options']]
            
            json.dump(data, f, indent=2, ensure_ascii=False)