import ast, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\AI_Tour_Guide-main\scripts\seed_data.py', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

# Find the ARTIFACTS assignment
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'ARTIFACTS':
                if isinstance(node.value, ast.List):
                    artifacts = node.value.elts
                    print(f'Found {len(artifacts)} artifacts\n')
                    
                    all_ok = True
                    for idx, art in enumerate(artifacts, 1):
                        if not isinstance(art, ast.Dict):
                            continue
                        
                        name = ''
                        vi_len = 0
                        en_len = 0
                        
                        for key, value in zip(art.keys, art.values):
                            if isinstance(key, ast.Constant) and key.value == 'name_vi':
                                name = value.value if isinstance(value, ast.Constant) else str(value.s)
                            elif isinstance(key, ast.Constant) and key.value == 'history_text_vi':
                                if isinstance(value, ast.Constant):
                                    vi_len = len(value.value)
                                elif isinstance(value, ast.JoinedStr) or isinstance(value, ast.BinOp):
                                    # Handle string concatenation
                                    # Flatten to get all parts
                                    parts = []
                                    def get_parts(node):
                                        if isinstance(node, ast.Constant):
                                            parts.append(node.value)
                                        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                                            get_parts(node.left)
                                            get_parts(node.right)
                                    get_parts(value)
                                    vi_len = sum(len(p) for p in parts)
                            elif isinstance(key, ast.Constant) and key.value == 'history_text_en':
                                if isinstance(value, ast.Constant):
                                    en_len = len(value.value)
                                elif isinstance(value, ast.BinOp) or isinstance(value, ast.JoinedStr):
                                    parts = []
                                    def get_parts(node):
                                        if isinstance(node, ast.Constant):
                                            parts.append(node.value)
                                        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                                            get_parts(node.left)
                                            get_parts(node.right)
                                    get_parts(value)
                                    en_len = sum(len(p) for p in parts)
                        
                        vi_ok = 1800 <= vi_len <= 3800
                        en_ok = 1800 <= en_len <= 3800
                        if not vi_ok or not en_ok:
                            all_ok = False
                        
                        status = f'VI={vi_len}({"OK" if vi_ok else "OUT"}) EN={en_len}({"OK" if en_ok else "OUT"})'
                        print(f'{idx}. {name[:35]:35s} {status}')
                    
                    print(f'\nAll within bounds: {all_ok}')
                    break
