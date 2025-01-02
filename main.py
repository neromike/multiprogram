import pygame
import sys

pygame.init()

# Window dimensions
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Basic Python-like IDE in Pygame")

# Fonts
FONT = pygame.font.SysFont("consolas", 20)
SMALL_FONT = pygame.font.SysFont("consolas", 16)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 128)

# Layout / geometry
EDITOR_X = 20
EDITOR_Y = 20
EDITOR_WIDTH = 550
EDITOR_HEIGHT = 400
OUTPUT_X = 600
OUTPUT_Y = 20
OUTPUT_WIDTH = 380
OUTPUT_HEIGHT = 400

BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
RUN_BUTTON_X = 20
RUN_BUTTON_Y = 450
STEP_BUTTON_X = 140
STEP_BUTTON_Y = 450

# This will store lines of code. Start with an empty list or some sample code:
code_lines = [
    "x = 0",
    "if x < 5:",
    "    print x",
    "    x = x + 1",
    "print x"
]
cursor_pos = [0, 0]  # [line_index, column_index]
scroll_offset = 0  # If code becomes longer than the editor can show

# Output lines
output_lines = []

# Interpreter state
env = {}  # variable environment for the code
current_line = 0  # index of the current line for stepping
stepping_mode = False
running_mode = False
done_executing = True


def interpret_code_all(lines):
    """Interpret all lines at once (reset environment and output)."""
    global env, output_lines, running_mode, done_executing, current_line
    env = {}
    output_lines = []
    done_executing = False
    running_mode = True
    current_line = 0

    # Parse and execute each line with a delay
    while current_line < len(lines):
        # Interpret one line
        new_line = interpret_line(lines, current_line, env)

        # Highlight the current line and refresh the display
        draw_editor()
        draw_output()
        draw_buttons()
        pygame.display.flip()
        pygame.time.delay(500)  # 500 ms delay to highlight the line

        # If interpret_line returns -1, it means stop execution (like a parse error).
        if new_line < 0:
            break

        current_line = new_line

    # Mark execution as done
    done_executing = True
    running_mode = False
    current_line = 0


def interpret_line(lines, line_index, env):
    """Interpret a single line in context of the environment.
       Return the next line index to execute or -1 if error/stop.
    """
    if line_index >= len(lines):
        return -1  # out of range

    line = lines[line_index].rstrip()

    # Check indentation
    # For simplicity, let's consider how many leading spaces there are
    stripped_line = line.lstrip()
    indent_level = len(line) - len(stripped_line)

    # If line is empty or comment, just skip
    if stripped_line == "" or stripped_line.startswith("#"):
        return line_index + 1

    # Very naive parse:
    # 1) Assignment: x = 5
    # 2) Print: print x
    # 3) If statement: if x < 10:
    # 4) Indented lines (we only execute them if the previous if was true)
    #    We'll track if the last if statement was satisfied or not.

    # We need to see if the line is an 'if' or something else.
    if stripped_line.startswith("if "):
        # e.g. if x < 10:
        condition_part = stripped_line[3:].rstrip(":")  # "x < 10"
        condition_part = condition_part.strip()
        result = eval_condition(condition_part, env)  # Evaluate the condition
        # If the condition is false, skip all lines that are more indented
        if not result:
            # Skip lines until we find a line with the same or lower indent_level
            next_line = line_index + 1
            while next_line < len(lines):
                next_stripped = lines[next_line].lstrip()
                next_indent = len(lines[next_line]) - len(next_stripped)
                if next_indent <= indent_level:
                    break
                next_line += 1
            return next_line
        else:
            # Condition is true, just go to next line
            return line_index + 1

    elif stripped_line.startswith("print "):
        # e.g. print x
        expr = stripped_line[len("print "):].strip()
        value = eval_expression(expr, env)
        output_lines.append(str(value))
        return line_index + 1

    elif "=" in stripped_line:
        # Very naive assignment parse: x = 5
        parts = stripped_line.split("=")
        if len(parts) != 2:
            output_lines.append("Error: invalid assignment")
            return -1
        var_name = parts[0].strip()
        expr = parts[1].strip()
        value = eval_expression(expr, env)
        env[var_name] = value
        return line_index + 1
    else:
        # Unrecognized line - skip
        output_lines.append(f"Error: Unrecognized line '{line}'")
        return -1


def eval_condition(condition_part, env):
    """Evaluate a simple boolean expression, e.g. 'x < 5'."""
    # In a real system, you'd parse carefully or use a safe eval approach
    # For demonstration, we'll do a naive 'eval' with a restricted namespace
    try:
        return bool(eval(condition_part, {"__builtins__": {}}, env))
    except Exception as e:
        output_lines.append(f"Error in condition: {e}")
        return False


def eval_expression(expr, env):
    """Evaluate a simple numeric/string expression or variable lookup."""
    # Again, naive usage of eval with restricted namespace
    try:
        return eval(expr, {"__builtins__": {}}, env)
    except Exception as e:
        output_lines.append(f"Error in expression: {e}")
        return 0


def step_code(lines):
    """Execute just the current line, then advance."""
    global current_line, env, done_executing
    if done_executing:
        current_line = 0  # Reset current line to the first line
        return

    if current_line < 0 or current_line >= len(lines):
        done_executing = True
        current_line = 0  # Reset current line to the first line
        return

    new_line = interpret_line(lines, current_line, env)
    if new_line < 0:
        done_executing = True
        current_line = 0  # Reset current line to the first line
    else:
        current_line = new_line
        if current_line >= len(lines):
            done_executing = True
            current_line = 0  # Reset current line to the first line


def handle_text_input(event):
    """Handle keyboard input for editing the code in code_lines."""
    global code_lines, cursor_pos

    line_idx, col_idx = cursor_pos
    if event.key == pygame.K_RETURN:
        # Split the current line at the cursor into two
        left_part = code_lines[line_idx][:col_idx]
        right_part = code_lines[line_idx][col_idx:]
        code_lines[line_idx] = left_part
        code_lines.insert(line_idx + 1, right_part)
        cursor_pos = [line_idx + 1, 0]
    elif event.key == pygame.K_BACKSPACE:
        if col_idx > 0:
            # Delete character to the left
            line = code_lines[line_idx]
            code_lines[line_idx] = line[:col_idx - 1] + line[col_idx:]
            cursor_pos[1] = col_idx - 1
        else:
            # If col_idx == 0, merge with previous line
            if line_idx > 0:
                prev_line = code_lines[line_idx - 1]
                current_line = code_lines[line_idx]
                new_col = len(prev_line)
                code_lines[line_idx - 1] = prev_line + current_line
                del code_lines[line_idx]
                cursor_pos = [line_idx - 1, new_col]
    elif event.key == pygame.K_DELETE:
        line = code_lines[line_idx]
        if col_idx < len(line):
            code_lines[line_idx] = line[:col_idx] + line[col_idx + 1:]
        else:
            # Merge with next line if any
            if line_idx < len(code_lines) - 1:
                next_line = code_lines[line_idx + 1]
                code_lines[line_idx] = line + next_line
                del code_lines[line_idx + 1]
    elif event.key == pygame.K_LEFT:
        if col_idx > 0:
            cursor_pos[1] = col_idx - 1
        else:
            if line_idx > 0:
                cursor_pos[0] = line_idx - 1
                cursor_pos[1] = len(code_lines[line_idx - 1])
    elif event.key == pygame.K_RIGHT:
        line_length = len(code_lines[line_idx])
        if col_idx < line_length:
            cursor_pos[1] = col_idx + 1
        else:
            if line_idx < len(code_lines) - 1:
                cursor_pos[0] = line_idx + 1
                cursor_pos[1] = 0
    elif event.key == pygame.K_UP:
        if line_idx > 0:
            cursor_pos[0] = line_idx - 1
            cursor_pos[1] = min(len(code_lines[line_idx - 1]), col_idx)
    elif event.key == pygame.K_DOWN:
        if line_idx < len(code_lines) - 1:
            cursor_pos[0] = line_idx + 1
            cursor_pos[1] = min(len(code_lines[line_idx + 1]), col_idx)
    else:
        # Regular text insertion
        if event.unicode:
            ch = event.unicode
            line = code_lines[line_idx]
            code_lines[line_idx] = line[:col_idx] + ch + line[col_idx:]
            cursor_pos[1] += 1


def handle_mouse_click(mx, my):
    """Move the cursor to the clicked position in the editor."""
    global cursor_pos, scroll_offset

    # Check if the click is within the editor area
    if EDITOR_X <= mx <= EDITOR_X + EDITOR_WIDTH and EDITOR_Y <= my <= EDITOR_Y + EDITOR_HEIGHT:
        line_height = FONT.get_height()

        # Determine the line index based on the vertical position
        clicked_line = (my - EDITOR_Y) // line_height + scroll_offset

        # Clamp the clicked line to valid range
        clicked_line = max(0, min(len(code_lines) - 1, clicked_line))

        # Determine the column index based on the horizontal position
        text_x_offset = mx - EDITOR_X - 5  # Subtract padding
        if text_x_offset < 0:
            text_x_offset = 0

        # Find the column index based on the width of the text
        line_text = code_lines[clicked_line]
        col_idx = 0
        for i in range(len(line_text)):
            char_width = FONT.size(line_text[:i + 1])[0]
            if char_width > text_x_offset:
                break
            col_idx = i + 1  # The cursor should be at this column

        # Update the cursor position
        cursor_pos = [clicked_line, col_idx]


def draw_editor():
    """Draw the code editor area with the lines of code and the cursor."""
    pygame.draw.rect(screen, WHITE, (EDITOR_X, EDITOR_Y, EDITOR_WIDTH, EDITOR_HEIGHT))
    pygame.draw.rect(screen, BLACK, (EDITOR_X, EDITOR_Y, EDITOR_WIDTH, EDITOR_HEIGHT), 2)

    line_height = FONT.get_height()
    visible_lines = (EDITOR_HEIGHT // line_height)

    start_index = scroll_offset
    end_index = start_index + visible_lines

    for i, line in enumerate(code_lines[start_index:end_index]):
        actual_i = i + start_index
        text_surf = FONT.render(line, True, BLACK)

        # If we're in stepping mode, highlight the "current_line" if it matches actual_i
        if (stepping_mode and (actual_i == current_line) and not done_executing) or (done_executing and actual_i == 0) or (running_mode and (actual_i == current_line)):
            # Draw a highlight behind the line
            highlight_rect = pygame.Rect(EDITOR_X + 2, EDITOR_Y + i * line_height, EDITOR_WIDTH - 4, line_height)
            pygame.draw.rect(screen, YELLOW, highlight_rect)

        # Render the line text
        screen.blit(text_surf, (EDITOR_X + 5, EDITOR_Y + i * line_height))

    # Draw the cursor
    cursor_line, cursor_col = cursor_pos
    if start_index <= cursor_line < end_index:
        # Cursor is visible
        rel_line = cursor_line - start_index
        cursor_x = EDITOR_X + 5 + FONT.size(code_lines[cursor_line][:cursor_col])[0]
        cursor_y = EDITOR_Y + rel_line * line_height
        pygame.draw.line(screen, RED, (cursor_x, cursor_y), (cursor_x, cursor_y + line_height), 2)


def draw_output():
    """Draw the output area."""
    pygame.draw.rect(screen, WHITE, (OUTPUT_X, OUTPUT_Y, OUTPUT_WIDTH, OUTPUT_HEIGHT))
    pygame.draw.rect(screen, BLACK, (OUTPUT_X, OUTPUT_Y, OUTPUT_WIDTH, OUTPUT_HEIGHT), 2)

    line_height = SMALL_FONT.get_height()
    lines_to_show = min(len(output_lines), OUTPUT_HEIGHT // line_height)
    start_index = max(0, len(output_lines) - lines_to_show)

    for i, line in enumerate(output_lines[start_index:]):
        text_surf = SMALL_FONT.render(line, True, BLACK)
        screen.blit(text_surf, (OUTPUT_X + 5, OUTPUT_Y + i * line_height))


def draw_buttons():
    """Draw the Run and Step buttons."""
    # Run Button
    pygame.draw.rect(screen, GREEN, (RUN_BUTTON_X, RUN_BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT))
    run_text = FONT.render("RUN", True, BLACK)
    screen.blit(run_text, (RUN_BUTTON_X + 20, RUN_BUTTON_Y + 5))

    # Step Button
    pygame.draw.rect(screen, BLUE, (STEP_BUTTON_X, STEP_BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT))
    step_text = FONT.render("STEP", True, BLACK)
    screen.blit(step_text, (STEP_BUTTON_X + 15, STEP_BUTTON_Y + 5))


def main():
    global running, stepping_mode, current_line, done_executing, scroll_offset

    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(30)  # 30 FPS
        screen.fill(GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                handle_text_input(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                handle_mouse_click(mx, my)

                # Check if clicked Run button
                if (RUN_BUTTON_X <= mx <= RUN_BUTTON_X + BUTTON_WIDTH and
                        RUN_BUTTON_Y <= my <= RUN_BUTTON_Y + BUTTON_HEIGHT):
                    # RUN
                    stepping_mode = False
                    interpret_code_all(code_lines)
                    current_line = 0
                # Check if clicked Step button
                elif (STEP_BUTTON_X <= mx <= STEP_BUTTON_X + BUTTON_WIDTH and
                      STEP_BUTTON_Y <= my <= STEP_BUTTON_Y + BUTTON_HEIGHT):
                    # STEP
                    if not stepping_mode:
                        # Initialize stepping
                        stepping_mode = True
                        current_line = 0
                        env.clear()
                        output_lines.clear()
                        done_executing = False
                    step_code(code_lines)
                    if done_executing:
                        current_line = 0  # Reset current line to the first line

            # Mouse wheel for scrolling the editor (optional)
            elif event.type == pygame.MOUSEWHEEL:
                if event.y < 0:
                    # scroll down
                    if scroll_offset < len(code_lines) - 1:
                        scroll_offset += 1
                elif event.y > 0:
                    # scroll up
                    if scroll_offset > 0:
                        scroll_offset -= 1

        # Draw everything
        draw_editor()
        draw_output()
        draw_buttons()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
