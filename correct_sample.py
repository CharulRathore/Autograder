from collections import deque
# given the position of the knight on the board, this helper 
# function returns all the possible locations for the knight
# kr and kc can run from 0 - n-1
# there are 8 positions that a knight can move
def knight_positions(n, kr, kc):
    possible_positions = []
    # knight moves in a L shape, 2 steps in either direction and 
    # then 1 step in either direction
    for r in [-2, 2]:
        for c in [-1, 1]:
            row_pos = kr + r
            col_pos = kc + c
            possible_positions.append((row_pos, col_pos))
    for r in [-1, 1]:
        for c in [-2, 2]:
            row_pos = kr + r
            col_pos = kc + c
            possible_positions.append((row_pos, col_pos))
    # now these positions can be out of bounds, if so don't
    # include in final list
    possible_positions = is_bounded(n, possible_positions)
    return possible_positions

def is_bounded(n, positions):
    valid_positions = []
    for position in positions:
        row, col = position
        row_bound = 0 <= row < n
        col_bound = 0 <= col < n
        if row_bound and col_bound:
            valid_positions.append((row, col))
    return valid_positions

def knight_attack(n, kr, kc, pr, pc):
    visited = set()
    n = bfs(n, kr, kc, pr, pc, visited)
    return n

# return shortest path from knight position to pawn
def bfs(n, kr, kc, pr, pc, visited):
    q = deque()
    moves = 0
    q.append((kr, kc, moves))
    pawn_location = (pr, pc)
    while q:
        cur_row, cur_col, move = q.popleft()
        cur_pos = (cur_row, cur_col)
        # print("current position ", cur_pos, "moves = ", move)
        if cur_pos in visited:
            continue
        visited.add(cur_pos)
        if cur_pos == pawn_location:
            return move
        for position in knight_positions(n, cur_row, cur_col):
            r, c = position
            q.append((r, c, move+1))
    return None