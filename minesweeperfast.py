import pyautogui
import time
import random
import pytesseract
from PIL import Image

time.sleep(2)

# easy
x1, y1 = 728, 449
x2, y2 = 1178, 809
cols = 10
rows = 8

# med
# x1, y1 = 682, 419
# x2, y2 = 1222, 839
# cols = 18
# rows = 14

#hard





    
pyautogui.click(random.randint(900, 1000), random.randint(550, 700))
time.sleep(0.8)

directions = [(-1,-1), (-1,0), (-1,1),
              (0,-1),         (0,1),
              (1,-1), (1,0), (1,1)]

 # untouched green tile
tile_color = {
    (162, 209, 73),
    (170, 215, 81)
}    
flag_color = (242, 54, 7)   

color_to_num = {
    (229, 194, 159): 0,
    (215, 184, 153): 0,
    (25, 118, 210): 1,      # blue 1
    (56, 142, 60): 2,      # green 2
    (211, 47, 47): 3,      # red 3
    (123, 31, 162): 4,
    (128, 0, 0): 5,
    (0, 128, 128): 6,
    (0, 0, 0): 7,
    (128, 128, 128): 8,
}

tile_size = (x2 - x1) // cols
center = tile_size // 2

def get_game_array():
    board = [[None for _ in range(cols)] for _ in range(rows)]

    offset_ratio = 10 / 45  

    offset = int(tile_size * offset_ratio)


    for r in range(rows):
        for c in range(cols):


            px = x1 + c * tile_size + center
            py = y1 + r * tile_size + center

            sample_points = [
                (px, py - offset),          # main loc
                (px, py - offset - 1),      # slightly above
                (px, py - offset + 1),      # slightly below
            ]

            colors = [pyautogui.pixel(x, y) for x, y in sample_points]


            #flagged bomb
            if any(color == flag_color for color in colors):
                board[r][c] = 9
                continue

            # untouched tile
            if any(color in tile_color for color in colors):
                board[r][c] = -1
                continue

            # number
            found = None
            for color in colors:
                if color in color_to_num:
                    found = color_to_num[color]
                    break

            board[r][c] = found if found is not None else 0

    for r in range(rows):
        for c in range(cols):
            print(board[r][c], end=" ")
        print()

    return board

def click_tile(r, c, right=False):
    click_x = x1 + c * tile_size + center
    click_y = y1 + r * tile_size + center
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

game_array = get_game_array()
changed = True
while changed:

    if check_game_over(game_array):
        print("Game ended")
        time.sleep(4)
        pyautogui.click(943, 714) # click "Play Again"
        time.sleep(0.8)
        pyautogui.click(random.randint(900, 1000), random.randint(550, 700))
        


    # changed = False
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
                            click_tile(nr, nc, right=True)
                            # changed = True

                # if all bombs are already flagged, the rest are safe
                print("Revealing safe tiles...")
                if flagged_bombs == new_board[r][c] and len(unknown_neighbors) > 0:
                    for nr, nc in unknown_neighbors:
                        # left click only if not already revealed
                        if new_board[nr][nc] == -1:
                            click_tile(nr, nc, right=False)
                            # changed = True

                
    game_array = get_game_array()
    # input()
    # time.sleep(0.8)






