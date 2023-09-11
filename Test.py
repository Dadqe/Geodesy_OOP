import json
import calc
from pathlib import Path

# with open(r"Data\Output\DataOutput6.json", 'r', encoding='utf-8') as f:
#     data = json.load(f)


# d = {
#         0: "23°49'18\"",
#         1: "238°29'19\"",
#         2: "204°27'4\"",
#         3: "67°59'56\"",
#         4: "180°31'51\"",
#         5: "82°14'38\"",
#         6: "102°27'54\""
#     }

# with open('ttt.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(d, ensure_ascii=False, indent=4))

new_path = Path('.') / 'pathlib_stuf'
print(new_path.resolve())