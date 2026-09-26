
import tkinter as tk
from tkinter import messagebox
import time
import random
from PIL import Image, ImageTk
import io
import base64
import os
import shutil

class PuzzleGame:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty
        self.window = tk.Tk()
        self.window.title("Puzzle Game")
        
        # Initialize game state
        self.is_game_complete = False
        self.start_time = None
        self.elapsed_time = 0
