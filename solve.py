def read_puzzle(file_path):  #resubby
    """
    read Sudoku puzzle from text file and return it as 2D list
   
    """
    with open(file_path, 'r') as file:
        puzzle=[
            [int(char) for char in line.strip().split() ]
            for line in file if line.strip()
        ]
        return puzzle
    
def print_puzz(puzzle):
    """Print the sudoku puzzle in a readable 9x9 grid."""
    for i in range(len(puzzle)):
        row_str = ''
        for j in range(len(puzzle[i])):
            
            if j > 0 and j % 3 == 0:
                row_str += ''

            row_str += str(puzzle[i][j]) if puzzle[i][j] != 0 else '0'
            row_str += ' '
        
        print(row_str.strip())
  

def possible_values(puzzle,row,col):
    """"
    returns a set of possible values for the cell at (row,col)
    """               
    if puzzle[row][col]!=0:
        return set()
    
    used_num=set(puzzle[row])
    used_num.update(puzzle[i][col] for i in range(9))

    #subgrid values
    start_row, start_col=3*(row//3), 3*(col//3)
    for i in  range(start_row,start_row+3):
        for j in range(start_col,start_col+3):
            used_num.add(puzzle[i][j])

    #values that are not already in use
    return set(range(1,10))-used_num

def naked_single(puzzle):
    """"
    use naked single technique to fill in cells with only one possible value
    """        
    changed=False
    for row in range(9):
        for col in range(9):
            if puzzle[row][col]==0:
                candidates=possible_values(puzzle,row,col)
                if len(candidates)==1:
                    value=candidates.pop()
                    puzzle[row][col]=value
                    changed=True
                    print(f'Naked single: cell ({row+1},{col+1}) can only be {value}')
    return changed    


def hidden_single(puzzle):
    """"
    apply hidden single technique to fill in cells where a  number must appear
    """     
    
    changed=False
    
    #check rows for hidden singles
    for row in range(9):
        for num in range(1,10):
            possible_cells=[]
            for col in range(9):
                if puzzle[row][col]==0:
                    candidates=possible_values(puzzle,row,col)
                    if num in candidates:
                        possible_cells.append((row,col))
            if len(possible_cells)==1:
                r,c=possible_cells[0]
                puzzle[r][c]=num
                changed=True
                print(f"Hidden Single: Row {row + 1} - Number {num} must be in cell ({r + 1}, {c + 1}).")
                
    #check colums for hidden singles
    for col in range(9):
        for num in range(1, 10):
            possible_cells = []
            for row in range(9):
                if puzzle[row][col] == 0:
                    candidates = possible_values(puzzle, row, col)
                    if num in candidates:
                        possible_cells.append((row, col))
            if len(possible_cells) == 1:
                r, c = possible_cells[0]
                puzzle[r][c] = num
                changed = True
                print(f"Hidden Single: Column {col + 1} - Number {num} must be in cell ({r + 1}, {c + 1}).")

    # Check 3x3 subgrids for hidden singles
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            for num in range(1, 10):
                possible_cells = []
                for r in range(box_row, box_row + 3):
                    for c in range(box_col, box_col + 3):
                        if puzzle[r][c] == 0:
                            candidates = possible_values(puzzle, r, c)
                            if num in candidates:
                                possible_cells.append((r, c))
                if len(possible_cells) == 1:
                    r, c = possible_cells[0]
                    puzzle[r][c] = num
                    changed = True
                    print(f"Hidden Single: Box ({box_row // 3 + 1}, {box_col // 3 + 1}) - Number {num} must be in cell ({r + 1}, {c + 1}).")

    return changed  

def write_puzz(puzzle, output_path):
    """Writes the Sudoku puzzle to a file.

   
    """
    with open(output_path, 'w') as f:
        for row in puzzle:
            line = ' '.join(str(num) for num in row)
            f.write(line + '\n')
          
    
    

if __name__ == '__main__':
    file_path = 'puzzle.txt'
    output_path = 'solved_puzzle.txt'
    
    
    puzzle = read_puzzle(file_path)
    print('Original puzzle:')
    print_puzz(puzzle)

    
    print('\nSolving the puzzle with techniques:')
    while True:
        changed = False

        
        if naked_single(puzzle):
            print("Naked Single technique applied:")
            print_puzz(puzzle)
            changed = True

    
        if hidden_single(puzzle):
            print("Hidden Single technique applied:")
            print_puzz(puzzle)
            changed = True

        if not changed:
            break

    
    print("\nSolved Puzzle:")
    print_puzz(puzzle)
    write_puzz(puzzle, output_path)
    print(f'Solution written to {output_path}')
