import os
import json
import random
import google.generativeai as genai
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

# ========================================
# 🔐 Gemini API Configuration
# ========================================
# Replace YOUR_API_KEY_HERE with your real key (keep private!)
genai.configure(api_key="")
model = genai.GenerativeModel("models/gemini-flash-latest")

# ========================================
# 📚 Question Bank
# ========================================
QUESTION_BANK = {
    "math": {
        "easy": [
            {"question": "What is 2 + 3?", "answer": "5"},
            {"question": "What is 10 - 6?", "answer": "4"},
        ],
        "medium": [
            {"question": "What is 8 × 7?", "answer": "56"},
            {"question": "What is 45 ÷ 9?", "answer": "5"},
        ],
        "hard": [
            {"question": "What is the square root of 81?", "answer": "9"},
            {"question": "Solve: (3 + 4) × 2", "answer": "14"},
        ],
    },
    "science": {
        "easy": [
            {"question": "What planet do we live on?", "answer": "earth"},
            {"question": "What gas do humans breathe in?", "answer": "oxygen"},
        ],
        "medium": [
            {"question": "What gas do plants release?", "answer": "oxygen"},
            {"question": "What force pulls objects to Earth?", "answer": "gravity"},
        ],
        "hard": [
            {"question": "What is H2O commonly called?", "answer": "water"},
            {"question": "What part of the cell contains DNA?", "answer": "nucleus"},
        ],
    },
}

PROGRESS_FILE = "user_progress.json"

# ========================================
# 🧠 Helper Functions
# ========================================
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as file:
        json.dump(data, file, indent=4)

def get_gemini_feedback(user_answer, correct_answer):
    prompt = f"""
    The student answered: '{user_answer}'
    The correct answer is: '{correct_answer}'
    Give short feedback in a friendly tone. If correct, praise. 
    If wrong, encourage and explain briefly.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def adjust_difficulty(score):
    if score >= 4:
        return "hard"
    elif score >= 2:
        return "medium"
    else:
        return "easy"

# ========================================
# 🧩 Quiz Logic
# ========================================
class QuizBot:
    def __init__(self, username):
        self.username = username
        self.subject = None
        self.difficulty = None
        self.score = 0
        self.question_number = 0
        self.current_question = None
        self.progress_data = load_progress()
        self.in_quiz = False

    def start_quiz(self, subject, difficulty):
        self.subject = subject
        self.difficulty = difficulty
        self.score = 0
        self.question_number = 0
        self.in_quiz = True
        return self.ask_question()

    def ask_question(self):
        if self.question_number >= 5:
            self.in_quiz = False
            accuracy = (self.score / 5) * 100
            self.progress_data[self.username] = {
                "subject": self.subject,
                "score": self.score,
                "accuracy": accuracy
            }
            save_progress(self.progress_data)
            return f"🏁 Quiz finished!\nScore: {self.score}/5 ({accuracy:.1f}%)"
        self.current_question = random.choice(QUESTION_BANK[self.subject][self.difficulty])
        self.question_number += 1
        return f"📖 Question {self.question_number}: {self.current_question['question']}"

    def answer_question(self, user_answer):
        correct = self.current_question["answer"].lower()
        feedback = get_gemini_feedback(user_answer, correct)
        if user_answer.lower() == correct:
            self.score += 1
        self.difficulty = adjust_difficulty(self.score)
        next_q = self.ask_question() if self.in_quiz else ""
        return f"{feedback}\n\n{next_q}"

# ========================================
# 💬 Chatbot UI (Beautiful Tkinter)
# ========================================
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 Educational Quiz Bot")
        self.root.geometry("700x650")
        self.root.config(bg="#EAF0F1")

        # Header
        header = tk.Label(
            root,
            text="🤖 Educational Quiz Bot",
            font=("Poppins", 18, "bold"),
            bg="#4CAF50",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X)

        # Chat Area
        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=80, height=25,
            font=("Poppins", 11), bg="#FFFFFF", fg="#333333"
        )
        self.text_area.pack(pady=10, padx=15)
        self.text_area.config(state=tk.DISABLED)

        # Frame for entry + button
        frame = tk.Frame(root, bg="#EAF0F1")
        frame.pack(pady=10)

        self.entry = tk.Entry(frame, width=55, font=("Poppins", 12))
        self.entry.grid(row=0, column=0, padx=10)
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(
            frame, text="Send", command=self.send_message,
            bg="#4CAF50", fg="white", font=("Poppins", 12, "bold"),
            relief="flat", padx=15, pady=5
        )
        self.send_btn.grid(row=0, column=1)

        # Username setup
        self.username = "Student"
        self.bot = QuizBot(self.username)
        self.display_bot_message("👋 Hi! I'm your AI Tutor.\nType 'start quiz' to begin, or ask me anything!")

    def display_bot_message(self, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"\n🤖 Bot: {message}\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.yview(tk.END)

    def display_user_message(self, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"\n👤 You: {message}")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.yview(tk.END)

    def send_message(self, event=None):
        user_msg = self.entry.get().strip()
        if not user_msg:
            return
        self.display_user_message(user_msg)
        self.entry.delete(0, tk.END)

        bot_reply = self.handle_user_input(user_msg)
        self.display_bot_message(bot_reply)

    def handle_user_input(self, msg):
        msg = msg.lower()

        if self.bot.in_quiz:
            return self.bot.answer_question(msg)

        elif "start quiz" in msg:
            return "Sure! Which subject do you want — Math or Science?"

        elif msg in ["math", "science"]:
            self.bot.subject = msg
            return "Great! Choose difficulty: easy, medium, or hard."

        elif msg in ["easy", "medium", "hard"]:
            if not self.bot.subject:
                return "Please choose a subject first (Math or Science)."
            response = self.bot.start_quiz(self.bot.subject, msg)
            return response

        elif "progress" in msg:
            data = self.bot.progress_data.get(self.bot.username)
            if data:
                return f"📈 Progress — Subject: {data['subject']}, Score: {data['score']}/5 ({data['accuracy']}%)"
            else:
                return "No progress found yet."

        elif msg in ["bye", "exit", "quit"]:
            self.root.quit()

        else:
            response = model.generate_content(msg)
            return response.text.strip()

# ========================================
# 🚀 Run the App
# ========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
