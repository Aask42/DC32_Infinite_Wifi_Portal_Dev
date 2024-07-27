import machine
import random
from matrix_functions.matrix_setup import set_up_led_matrix
from matrix_functions.matrix_functions import display_number, scroll_text
import uasyncio


# Define the glider pattern
glider_pattern = [
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1]
]

# Function to add the glider pattern to the grid at a specific position
def add_glider(x, y):
    for dx in range(3):
        for dy in range(3):
            grid[(x + dx) % rows][(y + dy) % cols] = glider_pattern[dx][dy]

#TODO: Move interactive functionality out of here to a higher level for the main program hook
# Configure GPIO 10 as input with a pull-up resistor
button_pin = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP)

def count_neighbors(x, y):
    # Count the number of alive neighbors for a cell at (x, y)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    count = 0
    for dx, dy in directions:
        nx, ny = (x + dx) % rows, (y + dy) % cols
        count += grid[nx][ny]
    return count

def update_grid():
    global grid
    new_grid = [[0] * cols for _ in range(rows)]
    for x in range(rows):
        for y in range(cols):
            neighbors = count_neighbors(x, y)
            if grid[x][y] == 1:
                if neighbors < 2 or neighbors > 3:
                    new_grid[x][y] = 0
                else:
                    new_grid[x][y] = 1
            else:
                if neighbors == 3:
                    new_grid[x][y] = 1
    grid = new_grid

def display_new_grid(led_matrix = None):
    if led_matrix is None:
        print("No valid matrix to display GRID")
        assert ValueError
        
    led_list_x_y = []
    brightness = 100
    for x in range(rows):
        for y in range(cols):
            led_list_x_y.append((x, y, brightness if grid[x][y] == 1 else 0))
    led_matrix.set_led_list(led_list_x_y)
    
async def countdown(count = 5, led_matrix = None):
    await uasyncio.create_task(scroll_text("DC32 INFINITE WIFI PORTAL BADGE"))
    for number in range(count, -1, -1):
        await uasyncio.create_task(display_number(number, led_matrix=led_matrix))
        await uasyncio.sleep(0.5)  # Add a brief pause between numbers

def reset_grid_random():
    global grid
    grid = [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]

def reset_grid_glider():
    global grid
    grid = [[0] * cols for _ in range(rows)]
    add_glider(0, 0)

def move_glider():
    global grid
    # Shift the grid to simulate glider movement
    glider = [[grid[i][j] for j in range(cols)] for i in range(rows)]
    for i in range(rows):
        for j in range(cols):
            grid[i][j] = glider[(i + 1) % rows][(j + 1) % cols]

def is_grid_empty():
    for row in grid:
        if any(cell == 1 for cell in row):
            return False
    return True

def is_static_or_repeating(prev_grids, current_grid):
    for prev_grid in prev_grids:
        if prev_grid == current_grid:
            return True
    return False

async def game_of_life(random_grid=False, delay=0.25, led_matrix=None):
    global rows,cols
    rows = led_matrix.rows
    cols = led_matrix.cols

    await uasyncio.create_task(countdown(2, led_matrix))  # Display countdown before starting
    if random_grid:
        reset_grid_random()
    else:
        reset_grid_glider()
    
    prev_grids = []
    while True:
        # TODO: Move button logic to main.py
        if button_pin.value() == 0:  # Button pressed (GPIO pulled to ground)
            if random_grid:
                reset_grid_random()
            else:
                reset_grid_glider()
                random_grid = True
            await countdown()  # Display countdown after reset
            await uasyncio.sleep(0.1)  # Debounce delay

        display_new_grid(led_matrix=led_matrix)
        prev_grids.append([row[:] for row in grid])  # Store a copy of the current grid
        if len(prev_grids) > 10:  # Limit the history size to the last 10 states
            prev_grids.pop(0)
        
        update_grid()
        
        if random_grid and (is_grid_empty() or is_static_or_repeating(prev_grids, grid)):
            reset_grid_random()  # Restart the grid if it clears or becomes static/repeating in random mode
            await countdown()  # Display countdown before restarting 
        await uasyncio.sleep(delay)

# Call the function to start the simulation with a glider
def run_game_of_life(random_grid = False, led_matrix=set_up_led_matrix()):

    # Set up the LED matrix
    # NOTE This will always spawn a glider first unless otherwise specified
    uasyncio.run(game_of_life(random_grid=random_grid, led_matrix=led_matrix))
    
run_game_of_life()


