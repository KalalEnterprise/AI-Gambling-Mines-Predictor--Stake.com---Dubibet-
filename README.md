# Dubibet Mines Predictor

A Python tool to assist with predicting safe tiles in the Dubibet Mines game using screen capture, OCR, and statistical analysis.

## Features
- Screen capture and OCR to detect the game board
- Logs tile clicks and outcomes (gem/mine)
- Builds a frequency-based heatmap
- Highlights tiles with the least mine likelihood in a GUI overlay

## Tech Stack
- Python
- PyAutoGUI, Pillow, pytesseract, OpenCV
- Pandas, NumPy
- Tkinter (for overlay UI)

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure Tesseract OCR is installed on your system.
   - Download: https://github.com/tesseract-ocr/tesseract
   - Add Tesseract to your PATH or specify its location in the code if needed.

## Usage
- Run the main script to start the predictor tool.
- The overlay will display suggested safe tiles on top of your browser.

## Disclaimer
This tool is for educational purposes only. Use responsibly.
