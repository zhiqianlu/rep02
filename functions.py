import os
import re


def process_text_files(input_folder: str, output_folder: str) -> list[str]:
    """
    Process all .txt files in the input folder by stripping whitespace from each line,
    renaming the file based on its first line, and saving the result to the output folder.
    The first line of each output file is replaced with the derived filename (including
    the .txt extension) to record the new name inside the file.

    Empty files and files whose first line is empty after stripping are skipped.

    Args:
        input_folder: Path to the folder containing input .txt files.
        output_folder: Path to the folder where processed files will be saved.

    Returns:
        A list of output file paths that were written.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_paths = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(input_folder, filename)

            with open(input_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            lines = [line.strip() for line in lines]

            if not lines or not lines[0]:
                continue

            # Sanitize the first line to prevent path traversal or invalid filenames
            safe_name = re.sub(r'[\\/:*?"<>|]', '_', lines[0])
            # Strip any remaining path components and reject dot-only names
            safe_name = os.path.basename(safe_name).strip('.')
            if not safe_name:
                continue
            new_filename = safe_name + '.txt'
            output_file_path = os.path.join(output_folder, new_filename)

            # Replace the first line with the derived filename to record it inside the file
            lines[0] = new_filename

            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(lines) + '\n')

            output_paths.append(output_file_path)

    return output_paths
