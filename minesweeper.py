import pyautogui
import time
import random
import pytesseract
from PIL import Image

time.sleep(2)

#easy
x1, y1 = 728, 449
x2, y2 = 1177, 809

#med
# x1, y1 = 682, 418
# x2, y2 = 1222, 838

#hard

#board = 18x14

cols = 10
rows = 8

    
pyautogui.click(random.randint(900, 1000), random.randint(550, 700))
time.sleep(0.8)

directions = [(-1,-1), (-1,0), (-1,1),
              (0,-1),         (0,1),
              (1,-1), (1,0), (1,1)]

margin = 5

def get_game_array():
    im = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    w, h = im.size
    block_w = w // cols
    block_h = h // rows

    board = [[None for _ in range(cols)] for _ in range(rows)] #from ai

    for r in range(rows):
        for c in range(cols):
            startx = c * block_w
            starty = r * block_h
            endx = (c + 1) * block_w
            endy = (r + 1) * block_h

            block = im.crop((startx + margin, starty + margin, endx - margin, endy - margin))

            # flagged bomb
            pixel_r, pixel_g, pixel_b = block.getpixel((15, 15))
            if 200 <= pixel_r <= 255 and 0 <= pixel_g <= 75 and 0 <= pixel_b <= 50:
                board[r][c] = 9 
                continue
            
            # untouched tile (pot bomb or unknown)
            pixel_r, pixel_g, pixel_b = block.getpixel((5,5))
            if 150 <= pixel_r <= 180 and 200 <= pixel_g <= 230 and 60 <= pixel_b <= 95:
                board[r][c] = -1
                continue

            text = pytesseract.image_to_string(block, config="--psm 10")  #takes hella time
            digits = "".join(ch for ch in text if ch.isdigit()) #idk
            if len(digits) > 1:
                digits = digits[0] #take first digit
            board[r][c] = int(digits) if digits else 0

    # for r in range(rows):
    #     for c in range(cols):
    #         print(board[r][c], end=" ")
    #     print()

    return board, block_w, block_h

def click_tile(r, c, block_w, block_h, right=False):
    click_x = x1 + c * block_w + block_w // 2
    click_y = y1 + r * block_h + block_h // 2
    if right:
        pyautogui.rightClick(click_x, click_y)
    else:
        pyautogui.leftClick(click_x, click_y)

def check_game_over(game_array):
    for r in range(rows):
        for c in range(cols):
            if game_array[r][c] == -1:
                return False

    return True

game_array, block_w, block_h = get_game_array()
changed = True
while changed:

    if check_game_over(game_array):
        print("Game ended")
        break

    changed = False
    new_board = [row[:] for row in game_array]

    for r in range(rows):
        for c in range(cols):
            if new_board[r][c] > 0:
                unknown_neighbors = []
                flagged_bombs = 0
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if new_board[nr][nc] == -1:
                            unknown_neighbors.append((nr, nc))
                        elif new_board[nr][nc] == 9:
                            flagged_bombs += 1
                
                # if number equals remaining unknowns, they must be bombs
                print("Flagging bombs...")
                if new_board[r][c] - flagged_bombs == len(unknown_neighbors) and len(unknown_neighbors) > 0:
                    for nr, nc in unknown_neighbors:
                        if new_board[nr][nc] != 9:
                            new_board[nr][nc] = 9
                            click_tile(nr, nc, block_w, block_h, right=True)
                            changed = True

                # if all bombs are already flagged, the rest are safe
                print("Revealing safe tiles...")
                if flagged_bombs == new_board[r][c] and len(unknown_neighbors) > 0:
                    for nr, nc in unknown_neighbors:
                        # left click only if not already revealed
                        if new_board[nr][nc] == -1:
                            click_tile(nr, nc, block_w, block_h, right=False)
                            changed = True

                
    game_array, block_w, block_h = get_game_array()
    time.sleep(0.8)






