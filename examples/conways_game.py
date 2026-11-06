"""
Written by: BadAask
Written for: DC32
Date started: 20240726
Copyright: Do what you want because a pirate is free

Description: This function is exactly what it says: Conway's Game.

    NOTE: This version of Conway's game always starts with a glider,
    and switches to random on reset
    Made for any matrix of X by Y, with an LED driver providing
    set_led_list(led_list_x_y) and clear_leds as functions

Memory notes (2026 update):
    Pre-calculating frames used to store every frame as a full 2D list of
    lists of ints. On the 7x6 matrix that is roughly 330 bytes per frame in
    MicroPython object overhead, so 100 pre-calculated frames cost ~33 KB
    of heap -- a big bite next to WiFi + BLE + MQTT.

    Frames are now bit-packed. One cell is one bit, so a whole 7x6 frame
    is 6 bytes. generate_conway_frames() returns a FrameStore holding all
    frames in ONE bytearray (plus a compact float array of delays):

        100 frames: ~1 KB packed, vs ~33 KB as lists of lists.

    The packed frame int uses the same bit layout as the rest of the
    badge code (bit index = x * cols + y, see
    MatrixManager._convert_frame_to_64bit), so a packed frame drops
    straight into StateManager.add_frame() and plays through the normal
    display path. Playback can walk the store forwards or backwards --
    see FrameStore.pingpong_index() and src/time_sync.py for playing the
    same frame on every badge at the same time.

    The original list-based helpers (update_grid, generate_frame,
    conway_game_next_frame, ...) are unchanged for anything that still
    wants to step the simulation by hand.
"""

import random
from array import array

# Define the glider pattern
glider_pattern = [
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1]
]

# Function to add the glider pattern to the grid at a specific position
def add_glider(x, y, grid, rows, cols):
    for dx in range(3):
        for dy in range(3):
            grid[(x + dx) % rows][(y + dy) % cols] = glider_pattern[dx][dy]

def count_neighbors(x, y, grid, rows, cols):
    # Count the number of alive neighbors for a cell at (x, y)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    count = 0
    for dx, dy in directions:
        nx, ny = (x + dx) % rows, (y + dy) % cols
        count += grid[nx][ny]
    return count

def update_grid(grid, rows, cols, _scratch=None):
    # Compute the next generation. Pass a reusable _scratch grid (same
    # shape) to avoid allocating a fresh 2D list for every generation;
    # every cell of the result is written below, so reuse is safe.
    new_grid = _scratch if _scratch is not None else [[0] * cols for _ in range(rows)]
    for x in range(rows):
        for y in range(cols):
            neighbors = count_neighbors(x, y, grid, rows, cols)
            if grid[x][y] == 1:
                if neighbors < 2 or neighbors > 3:
                    new_grid[x][y] = 0
                else:
                    new_grid[x][y] = 1
            else:
                if neighbors == 3:
                    new_grid[x][y] = 1
                else:
                    new_grid[x][y] = 0
    return new_grid

def generate_frame(grid, rows, cols):
    frame = [[0] * cols for _ in range(rows)]
    delay = 1.0  # Hardcoded delay of 1 second per frame
    for x in range(rows):
        for y in range(cols):
            frame[x][y] = 1 if grid[x][y] == 1 else 0
    return (frame, delay)

def reset_grid_random(rows, cols):
    return [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]

def reset_grid_glider(rows, cols):
    grid = [[0] * cols for _ in range(rows)]
    add_glider(0, 0, grid, rows, cols)
    return grid

def conway_game_init(rows, cols, random_grid=False):
    if random_grid:
        grid = reset_grid_random(rows, cols)
    else:
        grid = reset_grid_glider(rows, cols)
    return grid

def conway_game_next_frame(grid, rows, cols):
    delay = 1.0  # Hardcoded delay of 1 second per frame
    grid = update_grid(grid, rows, cols)
    frame = generate_frame(grid, rows, cols)
    return frame, grid


# ---------------------------------------------------------------------------
# Bit-packed frames
#
# Bit layout matches the rest of the badge code: the cell at (x, y) is bit
# (x * cols + y) of the frame int. A 7x6 frame is 42 bits = 6 bytes.
# ---------------------------------------------------------------------------

def pack_grid(grid, rows, cols):
    """Pack a 2D 0/1 grid into a single int, one bit per cell."""
    frame_int = 0
    for x in range(rows):
        row = grid[x]
        base = x * cols
        for y in range(cols):
            if row[y]:
                frame_int |= 1 << (base + y)
    return frame_int

def unpack_frame(frame_int, rows, cols):
    """Expand a packed frame int back into a 2D list of 0/1 (old format)."""
    grid = [[0] * cols for _ in range(rows)]
    for x in range(rows):
        base = x * cols
        for y in range(cols):
            grid[x][y] = (frame_int >> (base + y)) & 1
    return grid

def conway_game_next_frame_packed(grid, rows, cols, _scratch=None):
    """Like conway_game_next_frame(), but returns (frame_int, delay, grid)
    with the frame bit-packed instead of a 2D list."""
    delay = 1.0  # Hardcoded delay of 1 second per frame
    grid = update_grid(grid, rows, cols, _scratch)
    return pack_grid(grid, rows, cols), delay, grid


class FrameStore:
    """A sequence of pre-calculated frames, bit-packed into one bytearray.

    Behaves like the old list of (frame, delay) tuples for reading:
        len(store), store[i] -> (frame_int, delay), iteration all work,
    but costs bytes_per_frame + 4 bytes per frame instead of ~330.

    Playback helpers:
        frame_at(i)        packed frame int at index i
        pingpong_index(s)  map an ever-increasing step counter to an index
                           that plays forwards then backwards, forever.
    """

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.bytes_per_frame = (rows * cols + 7) // 8
        self._data = bytearray()
        self._delays = array('f')

    def append(self, frame_int, delay=1.0):
        self._data.extend(frame_int.to_bytes(self.bytes_per_frame, 'little'))
        self._delays.append(delay)

    def __len__(self):
        return len(self._delays)

    def frame_at(self, index):
        start = index * self.bytes_per_frame
        chunk = memoryview(self._data)[start:start + self.bytes_per_frame]
        return int.from_bytes(chunk, 'little')

    def delay_at(self, index):
        return self._delays[index]

    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        return (self.frame_at(index), self.delay_at(index))

    def __iter__(self):
        for i in range(len(self)):
            yield (self.frame_at(i), self.delay_at(i))

    def pingpong_index(self, step):
        """Step 0,1,2,... -> 0,1,...,n-1,n-2,...,1,0,1,... (forwards then
        backwards, no frame shown twice in a row at the turnarounds)."""
        n = len(self)
        if n <= 1:
            return 0
        cycle = 2 * (n - 1)
        pos = step % cycle
        return pos if pos < n else cycle - pos

    def memory_bytes(self):
        """Heap bytes held by the packed frame data and the delay array."""
        return len(self._data) + 4 * len(self._delays)


def generate_conway_frames(rows, cols, random_grid=False, max_frames=10):
    """Pre-calculate max_frames generations of Conway's Game of Life.

    Returns a FrameStore of bit-packed frames (see class notes above).
    The simulation double-buffers two grids, so generating N frames costs
    two grids of heap no matter how large N gets.

    Feed the result to the badge's normal playback path like this:
        for frame_int, delay in generate_conway_frames(7, 6, max_frames=60):
            state_manager.add_frame(frame_int, delay)
    """
    grid = conway_game_init(rows, cols, random_grid)
    scratch = [[0] * cols for _ in range(rows)]
    store = FrameStore(rows, cols)

    for _ in range(max_frames):
        previous = grid
        grid = update_grid(grid, rows, cols, scratch)
        scratch = previous  # old grid becomes the next scratch buffer
        store.append(pack_grid(grid, rows, cols), 1.0)

    return store
