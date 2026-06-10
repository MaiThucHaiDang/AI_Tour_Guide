import ast, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\AI_Tour_Guide-main\scripts\seed_data.py', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'ARTIFACTS':
                if isinstance(node.value, ast.List):
                    for art_idx, art in enumerate(node.value.elts[:1]):  # first one only
                        if isinstance(art, ast.Dict):
                            name = ''
                            vi_parts = []
                            for k, v in zip(art.keys, art.values):
                                if isinstance(k, ast.Constant) and k.value == 'name_vi':
                                    if isinstance(v, ast.Constant): name = v.value
                                elif isinstance(k, ast.Constant) and k.value == 'history_text_vi':
                                    def get_parts(n, parts):
                                        if isinstance(n, ast.Constant):
                                            parts.append(n.value)
                                        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                                            get_parts(n.left, parts)
                                            get_parts(n.right, parts)
                                        elif isinstance(n, ast.JoinedStr):
                                            for val in n.values:
                                                if isinstance(val, ast.Constant):
                                                    parts.append(val.value)
                                                elif isinstance(val, ast.FormattedValue):
                                                    parts.append(str(getattr(val, 'value', '')))
                                    get_parts(v, vi_parts)
                            
                            total = sum(len(p) for p in vi_parts)
                            print(f'{name}: VI = {total} chars ({len(vi_parts)} string literals)')
                            for i, p in enumerate(vi_parts):
                                preview = p[:80].replace('\n', '\\n')
                                print(f'  [{i+1}] len={len(p):3d}: "{preview}..."')
