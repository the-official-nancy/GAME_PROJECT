🐍 Snake: Korean Vocab Edition

A fun twist on the classic Snake game — learn Korean vocabulary while playing!
Built using Python and Pygame, this game challenges you to guide your snake to the correct Korean word that matches an English prompt.

🎮 Features

Classic Snake gameplay with a vocabulary-learning twist

Randomized Korean and English word placements

Score, lives, and level system

Smooth animations and colored HUD display

Built-in default vocabulary + optional custom vocab via CSV

🧠 How to Play

Objective:
Find and eat the Korean word that matches the English word shown at the top.

Controls:

W, A, S, D or Arrow Keys → Move

P → Pause / Resume

R → Restart (after game over)

Esc → Quit

Scoring:

✅ Correct word: +10 points

❌ Wrong word: -5 points and lose 1 life

Levels & Difficulty:

Every 50 points → Level up

Higher levels increase snake speed and distractor words

📦 Installation
1️⃣ Prerequisites

Make sure you have Python 3.8+ installed.

2️⃣ Install dependencies
pip install pygame

3️⃣ Run the game
python Snake_Korean_Vocab_Game.py

🗂 Optional: Custom Vocabulary

You can create your own vocabulary file named vocab.csv in the same folder.

CSV Format:

korean,english
saram,person
sigan,time
bap,rice


If no vocab.csv is found, the game will use a built-in vocabulary list.

🧩 Project Structure
Snake_Korean_Vocab_Game.py   # Main game file
vocab.csv                    # Optional custom vocabulary
README.md                    # Project documentation


🧑‍💻 Author

Your Name
Feel free to improve, remix, or extend this educational Snake game!