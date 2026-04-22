from quiz_scraper import QuizScraper

def run_scraper():
    scraper = QuizScraper()
    try:
        scraper.manual_login()
        course_name = input("Course Name: ").strip()
        num_exams = int(input("Number of exams to capture (default 1): ") or "1")
        questions_per_exam = int(input("Questions per exam (default 90): ") or "90")
        debug = input("Enable debug mode? (y/N): ").strip().lower() == 'y'
        
        for i in range(1, num_exams + 1):
            if i > 1:
                input(f"\nNavigate to Exam {i} and press ENTER...")
            scraper.scrape_exam(course_name, i, questions_per_exam, debug_mode=debug)
        
        print("\n" + "="*70)
        print("✅ ALL EXAMS COMPLETED!")
        print("="*70)
        print(f"📁 Data saved in: quiz_screenshots/{course_name.replace(' ', '_')}/")
        print("📄 Check exam_data.json in each exam folder for extracted data")
        print("📸 Screenshots saved as backup")
        print("="*70)
    finally:
        scraper.close()

if __name__ == "__main__":
    print("="*70)
    print("🎓 UDEMY QUIZ SCRAPER")
    print("="*70)
    print("\nThis tool will:")
    print("  1. Extract questions, options, and correct answers from Udemy exams")
    print("  2. Save data to JSON files")
    print("  3. Keep screenshots as backup")
    print("\n" + "="*70 + "\n")
    
    run_scraper()